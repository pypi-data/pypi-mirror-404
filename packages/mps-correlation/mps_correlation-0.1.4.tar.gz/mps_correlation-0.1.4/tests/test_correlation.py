"""Test mps-correlation: FP32, FP16, BF16 support"""

import torch
import time

# Build and load the extension
print("Loading mps_correlation...")
from mps_correlation import correlation, Correlation, CorrBlock, is_available

print(f"MPS available: {is_available()}")

def test_forward(dtype, name):
    """Test forward pass"""
    torch.manual_seed(42)

    B, C, H, W = 2, 32, 32, 32
    kernel_size = 1
    max_displacement = 4
    stride1 = 1
    stride2 = 1
    pad_size = 4

    input1 = torch.randn(B, C, H, W, device='mps', dtype=dtype)
    input2 = torch.randn(B, C, H, W, device='mps', dtype=dtype)

    output = correlation(input1, input2, kernel_size, max_displacement, stride1, stride2, pad_size)

    has_nan = torch.isnan(output).any().item()
    has_inf = torch.isinf(output).any().item()
    ok = not has_nan and not has_inf

    # Expected output channels = (2*max_displacement/stride2 + 1)^2 = 81
    neighborhood_size = 2 * max_displacement // stride2 + 1
    expected_channels = neighborhood_size * neighborhood_size

    padded_height = H + 2 * pad_size
    padded_width = W + 2 * pad_size
    expected_h = (padded_height - 2 * max_displacement - 1) // stride1 + 1
    expected_w = (padded_width - 2 * max_displacement - 1) // stride1 + 1

    shape_ok = output.shape == (B, expected_channels, expected_h, expected_w)

    print(f"  {name} forward: shape={output.shape}, dtype={output.dtype}, ok={ok and shape_ok}")
    return ok and shape_ok

def test_backward(dtype, name):
    """Test backward pass"""
    torch.manual_seed(42)

    B, C, H, W = 2, 16, 16, 16
    kernel_size = 1
    max_displacement = 2
    stride1 = 1
    stride2 = 1
    pad_size = 2

    input1 = torch.randn(B, C, H, W, device='mps', dtype=dtype, requires_grad=True)
    input2 = torch.randn(B, C, H, W, device='mps', dtype=dtype, requires_grad=True)

    output = correlation(input1, input2, kernel_size, max_displacement, stride1, stride2, pad_size)
    loss = output.sum()
    loss.backward()

    grad_input1_ok = input1.grad is not None and not torch.isnan(input1.grad).any()
    grad_input2_ok = input2.grad is not None and not torch.isnan(input2.grad).any()
    ok = grad_input1_ok and grad_input2_ok

    print(f"  {name} backward: input1={grad_input1_ok}, input2={grad_input2_ok}")
    return ok

def test_module(dtype, name):
    """Test Correlation module"""
    torch.manual_seed(42)

    B, C, H, W = 2, 32, 32, 32
    kernel_size = 1
    max_displacement = 4
    stride1 = 1
    stride2 = 1
    pad_size = 4

    module = Correlation(kernel_size, max_displacement, stride1, stride2, pad_size)
    input1 = torch.randn(B, C, H, W, device='mps', dtype=dtype)
    input2 = torch.randn(B, C, H, W, device='mps', dtype=dtype)

    output = module(input1, input2)

    ok = not torch.isnan(output).any() and not torch.isinf(output).any()
    print(f"  {name} Correlation module: shape={output.shape}, ok={ok}")
    return ok

def test_corrblock(dtype, name):
    """Test RAFT-style CorrBlock"""
    torch.manual_seed(42)

    B, C, H, W = 2, 64, 32, 32
    num_levels = 4
    radius = 4

    fmap1 = torch.randn(B, C, H, W, device='mps', dtype=dtype)
    fmap2 = torch.randn(B, C, H, W, device='mps', dtype=dtype)

    corr_block = CorrBlock(fmap1, fmap2, num_levels=num_levels, radius=radius)

    # Test lookup with random coordinates
    coords = torch.randn(B, 2, H, W, device='mps', dtype=dtype) * 5

    try:
        output = corr_block(coords)
        ok = not torch.isnan(output).any() and not torch.isinf(output).any()
        print(f"  {name} CorrBlock: shape={output.shape}, ok={ok}")
        return ok
    except Exception as e:
        print(f"  {name} CorrBlock: FAILED - {e}")
        return False

def test_gradient_correctness():
    """Test gradient correctness via numerical differentiation"""
    torch.manual_seed(42)

    B, C, H, W = 1, 4, 8, 8
    kernel_size = 1
    max_displacement = 2
    stride1 = 1
    stride2 = 1
    pad_size = 2
    eps = 1e-3

    input1 = torch.randn(B, C, H, W, device='mps', dtype=torch.float32, requires_grad=True)
    input2 = torch.randn(B, C, H, W, device='mps', dtype=torch.float32, requires_grad=True)

    def forward():
        return correlation(input1, input2, kernel_size, max_displacement, stride1, stride2, pad_size)

    def check_grad(name, param):
        # Analytical gradient
        input1.grad = input2.grad = None
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

    ok_input1 = check_grad('input1', input1)
    ok_input2 = check_grad('input2', input2)

    ok = ok_input1 and ok_input2
    print(f"  Gradient correctness: input1={ok_input1}, input2={ok_input2}")
    return ok

def compare_fp32_bf16():
    """Compare FP32 vs BF16 outputs"""
    torch.manual_seed(42)

    B, C, H, W = 1, 16, 16, 16
    kernel_size = 1
    max_displacement = 2
    stride1 = 1
    stride2 = 1
    pad_size = 2

    input1_fp32 = torch.randn(B, C, H, W, device='mps', dtype=torch.float32)
    input2_fp32 = torch.randn(B, C, H, W, device='mps', dtype=torch.float32)

    output_fp32 = correlation(input1_fp32, input2_fp32, kernel_size, max_displacement, stride1, stride2, pad_size)

    # BF16
    input1_bf16 = input1_fp32.to(torch.bfloat16)
    input2_bf16 = input2_fp32.to(torch.bfloat16)

    output_bf16 = correlation(input1_bf16, input2_bf16, kernel_size, max_displacement, stride1, stride2, pad_size)

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
    kernel_size = 1
    max_displacement = 4
    stride1 = 1
    stride2 = 1
    pad_size = 4

    input1 = torch.randn(B, C, H, W, device='mps', dtype=dtype)
    input2 = torch.randn(B, C, H, W, device='mps', dtype=dtype)

    for _ in range(warmup):
        _ = correlation(input1, input2, kernel_size, max_displacement, stride1, stride2, pad_size)
    torch.mps.synchronize()

    start = time.time()
    for _ in range(runs):
        _ = correlation(input1, input2, kernel_size, max_displacement, stride1, stride2, pad_size)
    torch.mps.synchronize()
    elapsed = time.time() - start

    ms = (elapsed / runs) * 1000
    print(f"  {name}: {ms:.2f} ms")
    return ms

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("Testing mps-correlation")
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

    print("\n3. Correlation module:")
    all_ok &= test_module(torch.float32, "FP32")
    all_ok &= test_module(torch.float16, "FP16")
    all_ok &= test_module(torch.bfloat16, "BF16")

    print("\n4. RAFT CorrBlock:")
    all_ok &= test_corrblock(torch.float32, "FP32")
    all_ok &= test_corrblock(torch.float16, "FP16")
    all_ok &= test_corrblock(torch.bfloat16, "BF16")

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
