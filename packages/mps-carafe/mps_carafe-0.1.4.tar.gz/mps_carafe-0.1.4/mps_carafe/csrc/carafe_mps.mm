// MPS CARAFE - Metal implementation of CARAFE for content-aware upsampling
// Used in Mask R-CNN, FPN, and other detection/segmentation networks

#include <torch/extension.h>
#include <ATen/mps/MPSStream.h>
#include <ATen/native/mps/OperationUtils.h>
#include <Metal/Metal.h>
#include <Foundation/Foundation.h>

static id<MTLDevice> g_device = nil;
static id<MTLLibrary> g_library = nil;
static id<MTLComputePipelineState> g_carafe_forward_fp32 = nil;
static id<MTLComputePipelineState> g_carafe_forward_fp16 = nil;
static id<MTLComputePipelineState> g_carafe_forward_bf16 = nil;
static id<MTLComputePipelineState> g_carafe_backward_features_fp32 = nil;
static id<MTLComputePipelineState> g_carafe_backward_masks_fp32 = nil;

static const char* METAL_SHADER = R"(
#include <metal_stdlib>
using namespace metal;

// Atomic float add using compare-and-swap (works on all Metal versions)
// This is the standard workaround when atomic_float is not available
inline void atomic_add_float(device atomic_uint* addr, float value) {
    uint expected = atomic_load_explicit(addr, memory_order_relaxed);
    float current_val = as_type<float>(expected);
    float new_val = current_val + value;
    uint new_bits = as_type<uint>(new_val);

    while (!atomic_compare_exchange_weak_explicit(
        addr, &expected, new_bits,
        memory_order_relaxed, memory_order_relaxed)) {
        current_val = as_type<float>(expected);
        new_val = current_val + value;
        new_bits = as_type<uint>(new_val);
    }
}

// CARAFE forward kernel - FP32
kernel void carafe_forward_fp32(
    device const float* features [[buffer(0)]],
    device const float* masks [[buffer(1)]],
    device float* output [[buffer(2)]],
    constant int& batch [[buffer(3)]],
    constant int& channels [[buffer(4)]],
    constant int& in_height [[buffer(5)]],
    constant int& in_width [[buffer(6)]],
    constant int& out_height [[buffer(7)]],
    constant int& out_width [[buffer(8)]],
    constant int& kernel_size [[buffer(9)]],
    constant int& group_size [[buffer(10)]],
    constant int& scale_factor [[buffer(11)]],
    uint3 gid [[thread_position_in_grid]]
) {
    int ow = gid.x;
    int oh = gid.y;
    int bc = gid.z;

    int b = bc / channels;
    int c = bc % channels;

    if (ow >= out_width || oh >= out_height || b >= batch) return;

    int group_channels = channels / group_size;
    int g = c / group_channels;

    int ih = oh / scale_factor;
    int iw = ow / scale_factor;

    int k_half = kernel_size / 2;
    float sum = 0.0f;

    for (int ky = 0; ky < kernel_size; ky++) {
        for (int kx = 0; kx < kernel_size; kx++) {
            int iy = ih + ky - k_half;
            int ix = iw + kx - k_half;

            float feat_val = 0.0f;
            if (iy >= 0 && iy < in_height && ix >= 0 && ix < in_width) {
                feat_val = features[b * channels * in_height * in_width +
                                   c * in_height * in_width +
                                   iy * in_width + ix];
            }

            int mask_c = g * kernel_size * kernel_size + ky * kernel_size + kx;
            float mask_val = masks[b * group_size * kernel_size * kernel_size * out_height * out_width +
                                   mask_c * out_height * out_width +
                                   oh * out_width + ow];

            sum += feat_val * mask_val;
        }
    }

    output[b * channels * out_height * out_width +
           c * out_height * out_width +
           oh * out_width + ow] = sum;
}

// CARAFE forward kernel - FP16
kernel void carafe_forward_fp16(
    device const half* features [[buffer(0)]],
    device const half* masks [[buffer(1)]],
    device half* output [[buffer(2)]],
    constant int& batch [[buffer(3)]],
    constant int& channels [[buffer(4)]],
    constant int& in_height [[buffer(5)]],
    constant int& in_width [[buffer(6)]],
    constant int& out_height [[buffer(7)]],
    constant int& out_width [[buffer(8)]],
    constant int& kernel_size [[buffer(9)]],
    constant int& group_size [[buffer(10)]],
    constant int& scale_factor [[buffer(11)]],
    uint3 gid [[thread_position_in_grid]]
) {
    int ow = gid.x;
    int oh = gid.y;
    int bc = gid.z;

    int b = bc / channels;
    int c = bc % channels;

    if (ow >= out_width || oh >= out_height || b >= batch) return;

    int group_channels = channels / group_size;
    int g = c / group_channels;

    int ih = oh / scale_factor;
    int iw = ow / scale_factor;

    int k_half = kernel_size / 2;
    float sum = 0.0f;

    for (int ky = 0; ky < kernel_size; ky++) {
        for (int kx = 0; kx < kernel_size; kx++) {
            int iy = ih + ky - k_half;
            int ix = iw + kx - k_half;

            float feat_val = 0.0f;
            if (iy >= 0 && iy < in_height && ix >= 0 && ix < in_width) {
                feat_val = float(features[b * channels * in_height * in_width +
                                         c * in_height * in_width +
                                         iy * in_width + ix]);
            }

            int mask_c = g * kernel_size * kernel_size + ky * kernel_size + kx;
            float mask_val = float(masks[b * group_size * kernel_size * kernel_size * out_height * out_width +
                                        mask_c * out_height * out_width +
                                        oh * out_width + ow]);

            sum += feat_val * mask_val;
        }
    }

    output[b * channels * out_height * out_width +
           c * out_height * out_width +
           oh * out_width + ow] = half(sum);
}

// CARAFE forward kernel - BF16 (native bfloat16 support)
kernel void carafe_forward_bf16(
    device const bfloat* features [[buffer(0)]],
    device const bfloat* masks [[buffer(1)]],
    device bfloat* output [[buffer(2)]],
    constant int& batch [[buffer(3)]],
    constant int& channels [[buffer(4)]],
    constant int& in_height [[buffer(5)]],
    constant int& in_width [[buffer(6)]],
    constant int& out_height [[buffer(7)]],
    constant int& out_width [[buffer(8)]],
    constant int& kernel_size [[buffer(9)]],
    constant int& group_size [[buffer(10)]],
    constant int& scale_factor [[buffer(11)]],
    uint3 gid [[thread_position_in_grid]]
) {
    int ow = gid.x;
    int oh = gid.y;
    int bc = gid.z;

    int b = bc / channels;
    int c = bc % channels;

    if (ow >= out_width || oh >= out_height || b >= batch) return;

    int group_channels = channels / group_size;
    int g = c / group_channels;

    int ih = oh / scale_factor;
    int iw = ow / scale_factor;

    int k_half = kernel_size / 2;
    float sum = 0.0f;

    for (int ky = 0; ky < kernel_size; ky++) {
        for (int kx = 0; kx < kernel_size; kx++) {
            int iy = ih + ky - k_half;
            int ix = iw + kx - k_half;

            float feat_val = 0.0f;
            if (iy >= 0 && iy < in_height && ix >= 0 && ix < in_width) {
                feat_val = float(features[b * channels * in_height * in_width +
                                         c * in_height * in_width +
                                         iy * in_width + ix]);
            }

            int mask_c = g * kernel_size * kernel_size + ky * kernel_size + kx;
            float mask_val = float(masks[b * group_size * kernel_size * kernel_size * out_height * out_width +
                                        mask_c * out_height * out_width +
                                        oh * out_width + ow]);

            sum += feat_val * mask_val;
        }
    }

    output[b * channels * out_height * out_width +
           c * out_height * out_width +
           oh * out_width + ow] = bfloat(sum);
}

// Backward for features - scatter gradients from output to input
// Note: Uses atomic_float, no atomic_half/atomic_bfloat in Metal, so backward always FP32
kernel void carafe_backward_features_fp32(
    device const float* grad_output [[buffer(0)]],
    device const float* masks [[buffer(1)]],
    device atomic_uint* grad_features [[buffer(2)]],
    constant int& batch [[buffer(3)]],
    constant int& channels [[buffer(4)]],
    constant int& in_height [[buffer(5)]],
    constant int& in_width [[buffer(6)]],
    constant int& out_height [[buffer(7)]],
    constant int& out_width [[buffer(8)]],
    constant int& kernel_size [[buffer(9)]],
    constant int& group_size [[buffer(10)]],
    constant int& scale_factor [[buffer(11)]],
    uint3 gid [[thread_position_in_grid]]
) {
    int ow = gid.x;
    int oh = gid.y;
    int bc = gid.z;

    int b = bc / channels;
    int c = bc % channels;

    if (ow >= out_width || oh >= out_height || b >= batch) return;

    int group_channels = channels / group_size;
    int g = c / group_channels;

    int ih = oh / scale_factor;
    int iw = ow / scale_factor;

    int k_half = kernel_size / 2;

    float grad_out_val = grad_output[b * channels * out_height * out_width +
                                     c * out_height * out_width +
                                     oh * out_width + ow];

    for (int ky = 0; ky < kernel_size; ky++) {
        for (int kx = 0; kx < kernel_size; kx++) {
            int iy = ih + ky - k_half;
            int ix = iw + kx - k_half;

            if (iy >= 0 && iy < in_height && ix >= 0 && ix < in_width) {
                int mask_c = g * kernel_size * kernel_size + ky * kernel_size + kx;
                float mask_val = masks[b * group_size * kernel_size * kernel_size * out_height * out_width +
                                      mask_c * out_height * out_width +
                                      oh * out_width + ow];

                int feat_idx = b * channels * in_height * in_width +
                              c * in_height * in_width +
                              iy * in_width + ix;
                atomic_add_float(&grad_features[feat_idx], grad_out_val * mask_val);
            }
        }
    }
}

// Backward for masks - compute gradient for each mask position
kernel void carafe_backward_masks_fp32(
    device const float* grad_output [[buffer(0)]],
    device const float* features [[buffer(1)]],
    device float* grad_masks [[buffer(2)]],
    constant int& batch [[buffer(3)]],
    constant int& channels [[buffer(4)]],
    constant int& in_height [[buffer(5)]],
    constant int& in_width [[buffer(6)]],
    constant int& out_height [[buffer(7)]],
    constant int& out_width [[buffer(8)]],
    constant int& kernel_size [[buffer(9)]],
    constant int& group_size [[buffer(10)]],
    constant int& scale_factor [[buffer(11)]],
    uint3 gid [[thread_position_in_grid]]
) {
    int ow = gid.x;
    int oh = gid.y;
    int bk = gid.z;

    int mask_channels = group_size * kernel_size * kernel_size;
    int b = bk / mask_channels;
    int k_idx = bk % mask_channels;

    if (ow >= out_width || oh >= out_height || b >= batch) return;

    int g = k_idx / (kernel_size * kernel_size);
    int k_pos = k_idx % (kernel_size * kernel_size);
    int ky = k_pos / kernel_size;
    int kx = k_pos % kernel_size;

    int ih = oh / scale_factor;
    int iw = ow / scale_factor;
    int k_half = kernel_size / 2;

    int iy = ih + ky - k_half;
    int ix = iw + kx - k_half;

    int group_channels = channels / group_size;
    float grad_sum = 0.0f;

    for (int gc = 0; gc < group_channels; gc++) {
        int c = g * group_channels + gc;

        float feat_val = 0.0f;
        if (iy >= 0 && iy < in_height && ix >= 0 && ix < in_width) {
            feat_val = features[b * channels * in_height * in_width +
                               c * in_height * in_width +
                               iy * in_width + ix];
        }

        float grad_out_val = grad_output[b * channels * out_height * out_width +
                                         c * out_height * out_width +
                                         oh * out_width + ow];

        grad_sum += feat_val * grad_out_val;
    }

    grad_masks[b * mask_channels * out_height * out_width +
               k_idx * out_height * out_width +
               oh * out_width + ow] = grad_sum;
}
)";

static void ensure_initialized() {
    if (g_device != nil) return;

    g_device = MTLCreateSystemDefaultDevice();
    NSError* error = nil;

    NSString* source = [NSString stringWithUTF8String:METAL_SHADER];
    g_library = [g_device newLibraryWithSource:source options:nil error:&error];

    if (error) {
        NSLog(@"Failed to compile Metal shader: %@", error);
        throw std::runtime_error("Failed to compile Metal shader");
    }

    id<MTLFunction> fwd_fp32 = [g_library newFunctionWithName:@"carafe_forward_fp32"];
    id<MTLFunction> fwd_fp16 = [g_library newFunctionWithName:@"carafe_forward_fp16"];
    id<MTLFunction> fwd_bf16 = [g_library newFunctionWithName:@"carafe_forward_bf16"];
    id<MTLFunction> bwd_feat = [g_library newFunctionWithName:@"carafe_backward_features_fp32"];
    id<MTLFunction> bwd_mask = [g_library newFunctionWithName:@"carafe_backward_masks_fp32"];

    g_carafe_forward_fp32 = [g_device newComputePipelineStateWithFunction:fwd_fp32 error:&error];
    g_carafe_forward_fp16 = [g_device newComputePipelineStateWithFunction:fwd_fp16 error:&error];
    g_carafe_forward_bf16 = [g_device newComputePipelineStateWithFunction:fwd_bf16 error:&error];
    g_carafe_backward_features_fp32 = [g_device newComputePipelineStateWithFunction:bwd_feat error:&error];
    g_carafe_backward_masks_fp32 = [g_device newComputePipelineStateWithFunction:bwd_mask error:&error];
}

torch::Tensor carafe_forward_mps(
    const torch::Tensor& features,
    const torch::Tensor& masks,
    int kernel_size,
    int group_size,
    int scale_factor
) {
    ensure_initialized();

    TORCH_CHECK(features.device().type() == torch::kMPS, "features must be on MPS");
    TORCH_CHECK(masks.device().type() == torch::kMPS, "masks must be on MPS");

    int batch = features.size(0);
    int channels = features.size(1);
    int in_height = features.size(2);
    int in_width = features.size(3);

    int out_height = in_height * scale_factor;
    int out_width = in_width * scale_factor;

    TORCH_CHECK(masks.size(0) == batch, "masks batch size mismatch");
    TORCH_CHECK(masks.size(1) == group_size * kernel_size * kernel_size,
                "masks channels should be group_size * kernel_size^2");
    TORCH_CHECK(masks.size(2) == out_height, "masks height mismatch");
    TORCH_CHECK(masks.size(3) == out_width, "masks width mismatch");
    TORCH_CHECK(channels % group_size == 0, "channels must be divisible by group_size");

    auto features_contig = features.contiguous();
    auto masks_contig = masks.contiguous();
    auto output = torch::zeros({batch, channels, out_height, out_width}, features_contig.options());

    // Get Metal buffers BEFORE calling commandEncoder() (important for zero-sync!)
    id<MTLBuffer> features_buf = at::native::mps::getMTLBufferStorage(features_contig);
    id<MTLBuffer> masks_buf = at::native::mps::getMTLBufferStorage(masks_contig);
    id<MTLBuffer> output_buf = at::native::mps::getMTLBufferStorage(output);

    // Use PyTorch's MPS stream command encoder (zero-sync)
    @autoreleasepool {
        auto stream = at::mps::getCurrentMPSStream();
        id<MTLComputeCommandEncoder> encoder = stream->commandEncoder();

        // Select kernel based on dtype - native support for FP32, FP16, BF16
        id<MTLComputePipelineState> pso;
        if (features_contig.scalar_type() == at::kHalf) {
            pso = g_carafe_forward_fp16;
        } else if (features_contig.scalar_type() == at::kBFloat16) {
            pso = g_carafe_forward_bf16;
        } else {
            pso = g_carafe_forward_fp32;
        }

        [encoder setComputePipelineState:pso];
        [encoder setBuffer:features_buf
                    offset:features_contig.storage_offset() * features_contig.element_size() atIndex:0];
        [encoder setBuffer:masks_buf
                    offset:masks_contig.storage_offset() * masks_contig.element_size() atIndex:1];
        [encoder setBuffer:output_buf
                    offset:output.storage_offset() * output.element_size() atIndex:2];

        [encoder setBytes:&batch length:sizeof(int) atIndex:3];
        [encoder setBytes:&channels length:sizeof(int) atIndex:4];
        [encoder setBytes:&in_height length:sizeof(int) atIndex:5];
        [encoder setBytes:&in_width length:sizeof(int) atIndex:6];
        [encoder setBytes:&out_height length:sizeof(int) atIndex:7];
        [encoder setBytes:&out_width length:sizeof(int) atIndex:8];
        [encoder setBytes:&kernel_size length:sizeof(int) atIndex:9];
        [encoder setBytes:&group_size length:sizeof(int) atIndex:10];
        [encoder setBytes:&scale_factor length:sizeof(int) atIndex:11];

        MTLSize gridSize = MTLSizeMake(out_width, out_height, batch * channels);
        MTLSize threadGroupSize = MTLSizeMake(8, 8, 1);
        [encoder dispatchThreads:gridSize threadsPerThreadgroup:threadGroupSize];
    }

    return output;
}

std::tuple<torch::Tensor, torch::Tensor> carafe_backward_mps(
    const torch::Tensor& grad_output,
    const torch::Tensor& features,
    const torch::Tensor& masks,
    int kernel_size,
    int group_size,
    int scale_factor
) {
    ensure_initialized();

    int batch = features.size(0);
    int channels = features.size(1);
    int in_height = features.size(2);
    int in_width = features.size(3);

    int out_height = in_height * scale_factor;
    int out_width = in_width * scale_factor;
    int mask_channels = group_size * kernel_size * kernel_size;

    // Backward always uses FP32 kernel (Metal doesn't have atomic_half/atomic_bfloat)
    at::ScalarType orig_dtype = features.scalar_type();

    auto grad_output_f = grad_output.to(at::kFloat).contiguous();
    auto features_f = features.to(at::kFloat).contiguous();
    auto masks_f = masks.to(at::kFloat).contiguous();

    auto grad_features = torch::zeros_like(features_f);
    auto grad_masks = torch::zeros({batch, mask_channels, out_height, out_width},
                                   grad_output_f.options());

    // Get Metal buffers BEFORE calling commandEncoder() (important for zero-sync!)
    id<MTLBuffer> grad_out_buf = at::native::mps::getMTLBufferStorage(grad_output_f);
    id<MTLBuffer> features_buf = at::native::mps::getMTLBufferStorage(features_f);
    id<MTLBuffer> masks_buf = at::native::mps::getMTLBufferStorage(masks_f);
    id<MTLBuffer> grad_feat_buf = at::native::mps::getMTLBufferStorage(grad_features);
    id<MTLBuffer> grad_mask_buf = at::native::mps::getMTLBufferStorage(grad_masks);

    // Use PyTorch's MPS stream command encoder (zero-sync)
    @autoreleasepool {
        auto stream = at::mps::getCurrentMPSStream();
        id<MTLComputeCommandEncoder> encoder = stream->commandEncoder();

        // Backward for features
        [encoder setComputePipelineState:g_carafe_backward_features_fp32];
        [encoder setBuffer:grad_out_buf offset:grad_output_f.storage_offset() * grad_output_f.element_size() atIndex:0];
        [encoder setBuffer:masks_buf offset:masks_f.storage_offset() * masks_f.element_size() atIndex:1];
        [encoder setBuffer:grad_feat_buf offset:grad_features.storage_offset() * grad_features.element_size() atIndex:2];

        [encoder setBytes:&batch length:sizeof(int) atIndex:3];
        [encoder setBytes:&channels length:sizeof(int) atIndex:4];
        [encoder setBytes:&in_height length:sizeof(int) atIndex:5];
        [encoder setBytes:&in_width length:sizeof(int) atIndex:6];
        [encoder setBytes:&out_height length:sizeof(int) atIndex:7];
        [encoder setBytes:&out_width length:sizeof(int) atIndex:8];
        [encoder setBytes:&kernel_size length:sizeof(int) atIndex:9];
        [encoder setBytes:&group_size length:sizeof(int) atIndex:10];
        [encoder setBytes:&scale_factor length:sizeof(int) atIndex:11];

        MTLSize gridSize = MTLSizeMake(out_width, out_height, batch * channels);
        MTLSize threadGroupSize = MTLSizeMake(8, 8, 1);
        [encoder dispatchThreads:gridSize threadsPerThreadgroup:threadGroupSize];

        // Backward for masks
        [encoder setComputePipelineState:g_carafe_backward_masks_fp32];
        [encoder setBuffer:grad_out_buf offset:grad_output_f.storage_offset() * grad_output_f.element_size() atIndex:0];
        [encoder setBuffer:features_buf offset:features_f.storage_offset() * features_f.element_size() atIndex:1];
        [encoder setBuffer:grad_mask_buf offset:grad_masks.storage_offset() * grad_masks.element_size() atIndex:2];

        [encoder setBytes:&batch length:sizeof(int) atIndex:3];
        [encoder setBytes:&channels length:sizeof(int) atIndex:4];
        [encoder setBytes:&in_height length:sizeof(int) atIndex:5];
        [encoder setBytes:&in_width length:sizeof(int) atIndex:6];
        [encoder setBytes:&out_height length:sizeof(int) atIndex:7];
        [encoder setBytes:&out_width length:sizeof(int) atIndex:8];
        [encoder setBytes:&kernel_size length:sizeof(int) atIndex:9];
        [encoder setBytes:&group_size length:sizeof(int) atIndex:10];
        [encoder setBytes:&scale_factor length:sizeof(int) atIndex:11];

        gridSize = MTLSizeMake(out_width, out_height, batch * mask_channels);
        [encoder dispatchThreads:gridSize threadsPerThreadgroup:threadGroupSize];
    }

    return std::make_tuple(
        grad_features.to(orig_dtype),
        grad_masks.to(masks.scalar_type())
    );
}

PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
    m.def("carafe_forward", &carafe_forward_mps, "CARAFE forward (MPS)");
    m.def("carafe_backward", &carafe_backward_mps, "CARAFE backward (MPS)");
}
