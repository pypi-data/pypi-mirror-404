"""Test mps-carafe: FP32, FP16, BF16 support"""

import torch
import time

# Build and load the extension
print("Loading mps_carafe...")
from mps_carafe import carafe, CARAFE, CARAFEPack, is_available

print(f"MPS available: {is_available()}")

def test_forward(dtype, name):
    """Test forward pass"""
    torch.manual_seed(42)

    B, C, H, W = 2, 32, 16, 16
    kernel_size = 5
    group_size = 1
    scale_factor = 2

    features = torch.randn(B, C, H, W, device='mps', dtype=dtype)

    out_h = H * scale_factor
    out_w = W * scale_factor
    mask_channels = group_size * kernel_size * kernel_size
    masks = torch.softmax(torch.randn(B, mask_channels, out_h, out_w, device='mps', dtype=dtype), dim=1)

    output = carafe(features, masks, kernel_size, group_size, scale_factor)

    has_nan = torch.isnan(output).any().item()
    has_inf = torch.isinf(output).any().item()
    ok = not has_nan and not has_inf

    expected_shape = (B, C, out_h, out_w)
    shape_ok = output.shape == expected_shape

    print(f"  {name} forward: shape={output.shape}, dtype={output.dtype}, ok={ok and shape_ok}")
    return ok and shape_ok

def test_backward(dtype, name):
    """Test backward pass"""
    torch.manual_seed(42)

    B, C, H, W = 2, 16, 8, 8
    kernel_size = 3
    group_size = 1
    scale_factor = 2

    features = torch.randn(B, C, H, W, device='mps', dtype=dtype, requires_grad=True)

    out_h = H * scale_factor
    out_w = W * scale_factor
    mask_channels = group_size * kernel_size * kernel_size
    masks = torch.softmax(torch.randn(B, mask_channels, out_h, out_w, device='mps', dtype=dtype), dim=1)
    masks.requires_grad_(True)

    output = carafe(features, masks, kernel_size, group_size, scale_factor)
    loss = output.sum()
    loss.backward()

    grad_features_ok = features.grad is not None and not torch.isnan(features.grad).any()
    grad_masks_ok = masks.grad is not None and not torch.isnan(masks.grad).any()
    ok = grad_features_ok and grad_masks_ok

    print(f"  {name} backward: features={grad_features_ok}, masks={grad_masks_ok}")
    return ok

def test_module(dtype, name):
    """Test CARAFE module"""
    torch.manual_seed(42)

    B, C, H, W = 2, 32, 16, 16
    kernel_size = 5
    group_size = 1
    scale_factor = 2

    module = CARAFE(kernel_size, group_size, scale_factor)
    features = torch.randn(B, C, H, W, device='mps', dtype=dtype)

    out_h = H * scale_factor
    out_w = W * scale_factor
    mask_channels = group_size * kernel_size * kernel_size
    masks = torch.softmax(torch.randn(B, mask_channels, out_h, out_w, device='mps', dtype=dtype), dim=1)

    output = module(features, masks)

    ok = not torch.isnan(output).any() and not torch.isinf(output).any()
    print(f"  {name} CARAFE module: shape={output.shape}, ok={ok}")
    return ok

def test_carafepack_module(dtype, name):
    """Test CARAFEPack module (with built-in mask predictor)"""
    torch.manual_seed(42)

    B, C, H, W = 2, 32, 16, 16
    scale_factor = 2

    module = CARAFEPack(C, kernel_size=5, group_size=1, scale_factor=scale_factor).to('mps').to(dtype)
    features = torch.randn(B, C, H, W, device='mps', dtype=dtype)

    output = module(features)

    ok = not torch.isnan(output).any() and not torch.isinf(output).any()
    expected_shape = (B, C, H * scale_factor, W * scale_factor)
    shape_ok = output.shape == expected_shape

    print(f"  {name} CARAFEPack module: shape={output.shape}, ok={ok and shape_ok}")
    return ok and shape_ok

def test_gradient_correctness():
    """Test gradient correctness via numerical differentiation"""
    torch.manual_seed(42)

    B, C, H, W = 1, 4, 4, 4
    kernel_size = 3
    group_size = 1
    scale_factor = 2
    eps = 1e-3

    features = torch.randn(B, C, H, W, device='mps', dtype=torch.float32, requires_grad=True)

    out_h = H * scale_factor
    out_w = W * scale_factor
    mask_channels = group_size * kernel_size * kernel_size
    masks = torch.softmax(torch.randn(B, mask_channels, out_h, out_w, device='mps', dtype=torch.float32), dim=1)
    masks.requires_grad_(True)

    def forward():
        return carafe(features, masks, kernel_size, group_size, scale_factor)

    def check_grad(name, param):
        # Analytical gradient
        features.grad = masks.grad = None
        output = forward()
        output.sum().backward()
        grad_analytical = param.grad.clone()

        # Numerical gradient
        grad_numerical = torch.zeros_like(param)
        param_data = param.data.clone()

        for i in range(min(param.numel(), 50)):  # Check first 50 elements
            param.data = param_data.clone()
            param.data.view(-1)[i] += eps
            out_plus = forward().sum().item()

            param.data = param_data.clone()
            param.data.view(-1)[i] -= eps
            out_minus = forward().sum().item()

            grad_numerical.view(-1)[i] = (out_plus - out_minus) / (2 * eps)

        param.data = param_data

        # Compare (only checked elements)
        n = min(param.numel(), 50)
        diff = (grad_analytical.view(-1)[:n] - grad_numerical.view(-1)[:n]).abs()
        rel_diff = (diff / (grad_analytical.view(-1)[:n].abs() + 1e-6)).mean().item() * 100
        return rel_diff < 10.0  # 10% tolerance for numerical precision

    ok_features = check_grad('features', features)
    ok_masks = check_grad('masks', masks)

    ok = ok_features and ok_masks
    print(f"  Gradient correctness: features={ok_features}, masks={ok_masks}")
    return ok

def compare_fp32_bf16():
    """Compare FP32 vs BF16 outputs"""
    torch.manual_seed(42)

    B, C, H, W = 1, 16, 8, 8
    kernel_size = 3
    group_size = 1
    scale_factor = 2

    features_fp32 = torch.randn(B, C, H, W, device='mps', dtype=torch.float32)

    out_h = H * scale_factor
    out_w = W * scale_factor
    mask_channels = group_size * kernel_size * kernel_size
    masks_fp32 = torch.softmax(torch.randn(B, mask_channels, out_h, out_w, device='mps', dtype=torch.float32), dim=1)

    output_fp32 = carafe(features_fp32, masks_fp32, kernel_size, group_size, scale_factor)

    # BF16
    features_bf16 = features_fp32.to(torch.bfloat16)
    masks_bf16 = masks_fp32.to(torch.bfloat16)

    output_bf16 = carafe(features_bf16, masks_bf16, kernel_size, group_size, scale_factor)

    diff = (output_fp32 - output_bf16.to(torch.float32)).abs()
    max_diff = diff.max().item()
    rel_diff = (diff / (output_fp32.abs() + 1e-6)).mean().item() * 100

    ok = rel_diff < 5.0
    print(f"  FP32 vs BF16: max_diff={max_diff:.6f}, rel_diff={rel_diff:.2f}%, ok={ok}")
    return ok

def benchmark(dtype, name, warmup=5, runs=20):
    """Benchmark forward pass"""
    torch.manual_seed(42)

    B, C, H, W = 4, 64, 64, 64
    kernel_size = 5
    group_size = 1
    scale_factor = 2

    features = torch.randn(B, C, H, W, device='mps', dtype=dtype)

    out_h = H * scale_factor
    out_w = W * scale_factor
    mask_channels = group_size * kernel_size * kernel_size
    masks = torch.softmax(torch.randn(B, mask_channels, out_h, out_w, device='mps', dtype=dtype), dim=1)

    for _ in range(warmup):
        _ = carafe(features, masks, kernel_size, group_size, scale_factor)
    torch.mps.synchronize()

    start = time.time()
    for _ in range(runs):
        _ = carafe(features, masks, kernel_size, group_size, scale_factor)
    torch.mps.synchronize()
    elapsed = time.time() - start

    ms = (elapsed / runs) * 1000
    print(f"  {name}: {ms:.2f} ms")
    return ms

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("Testing mps-carafe")
    print("=" * 50)

    all_ok = True

    print("\n1. Forward pass:")
    all_ok &= test_forward(torch.float32, "FP32")
    all_ok &= test_forward(torch.float16, "FP16")
    all_ok &= test_forward(torch.bfloat16, "BF16")

    print("\n2. Backward pass:")
    all_ok &= test_backward(torch.float32, "FP32")
    all_ok &= test_backward(torch.float16, "FP16")
    all_ok &= test_backward(torch.bfloat16, "BF16")

    print("\n3. CARAFE module:")
    all_ok &= test_module(torch.float32, "FP32")
    all_ok &= test_module(torch.float16, "FP16")
    all_ok &= test_module(torch.bfloat16, "BF16")

    print("\n4. CARAFEPack module:")
    all_ok &= test_carafepack_module(torch.float32, "FP32")
    all_ok &= test_carafepack_module(torch.float16, "FP16")
    all_ok &= test_carafepack_module(torch.bfloat16, "BF16")

    print("\n5. Gradient correctness:")
    all_ok &= test_gradient_correctness()

    print("\n6. FP32 vs BF16 comparison:")
    all_ok &= compare_fp32_bf16()

    print("\n7. Benchmarks:")
    benchmark(torch.float32, "FP32")
    benchmark(torch.float16, "FP16")
    benchmark(torch.bfloat16, "BF16")

    print("\n" + "=" * 50)
    if all_ok:
        print("ALL TESTS PASSED!")
    else:
        print("SOME TESTS FAILED!")
    print("=" * 50)
