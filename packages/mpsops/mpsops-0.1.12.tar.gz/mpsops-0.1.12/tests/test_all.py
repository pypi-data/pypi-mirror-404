#!/usr/bin/env python3
"""
Test and benchmark all MPS packages after zero-sync updates.
Run: python test_all_mps_packages.py
"""

import torch
import time
import sys

device = torch.device("mps")

def benchmark(fn, warmup=3, iters=20):
    """Benchmark a function, return ms per iteration."""
    for _ in range(warmup):
        fn()
    torch.mps.synchronize()

    t0 = time.perf_counter()
    for _ in range(iters):
        fn()
    torch.mps.synchronize()
    return (time.perf_counter() - t0) / iters * 1000

def test_mps_flash_attention():
    """Test mps-flash-attn forward and backward."""
    print("\n" + "="*60)
    print("MPS Flash Attention")
    print("="*60)

    try:
        from mps_flash_attn import flash_attention
    except ImportError as e:
        print(f"SKIP: {e}")
        return False

    B, H, S, D = 2, 8, 2048, 64
    q = torch.randn(B, H, S, D, device=device, dtype=torch.float16, requires_grad=True)
    k = torch.randn(B, H, S, D, device=device, dtype=torch.float16, requires_grad=True)
    v = torch.randn(B, H, S, D, device=device, dtype=torch.float16, requires_grad=True)

    # Forward
    out = flash_attention(q, k, v)
    assert out.shape == (B, H, S, D), f"Shape mismatch: {out.shape}"
    assert not torch.isnan(out).any(), "NaN in output"

    # Backward
    loss = out.sum()
    loss.backward()
    assert q.grad is not None, "No grad for Q"
    assert not torch.isnan(q.grad).any(), "NaN in Q grad"

    # Benchmark
    q2 = torch.randn(B, H, S, D, device=device, dtype=torch.float16)
    k2 = torch.randn(B, H, S, D, device=device, dtype=torch.float16)
    v2 = torch.randn(B, H, S, D, device=device, dtype=torch.float16)

    mfa_time = benchmark(lambda: flash_attention(q2, k2, v2))
    sdpa_time = benchmark(lambda: torch.nn.functional.scaled_dot_product_attention(q2, k2, v2))

    print(f"  Forward B={B}, H={H}, S={S}, D={D}")
    print(f"  MFA:  {mfa_time:.2f} ms")
    print(f"  SDPA: {sdpa_time:.2f} ms")
    print(f"  Speedup: {sdpa_time/mfa_time:.2f}x")
    print("  ✓ PASSED")
    return True

def test_mamba_metal():
    """Test mamba-metal (metal_pscan) forward and backward."""
    print("\n" + "="*60)
    print("Mamba Metal (metal_pscan)")
    print("="*60)

    try:
        from metal_pscan import metal_pscan
    except ImportError as e:
        print(f"SKIP: {e}")
        return False

    # Expected: (B, num_heads, L, D)
    B, H, L, D = 2, 4, 1024, 64
    x = torch.randn(B, H, L, D, device=device, dtype=torch.float32, requires_grad=True)
    a = torch.randn(B, H, L, D, device=device, dtype=torch.float32, requires_grad=True)

    # Forward
    out = metal_pscan(x, a)
    assert out.shape == (B, H, L, D), f"Shape mismatch: {out.shape}"
    assert not torch.isnan(out).any(), "NaN in output"

    # Backward
    loss = out.sum()
    loss.backward()
    assert x.grad is not None, "No grad for x"
    assert not torch.isnan(x.grad).any(), "NaN in x grad"

    # Benchmark
    x2 = torch.randn(B, H, L, D, device=device, dtype=torch.float32)
    a2 = torch.randn(B, H, L, D, device=device, dtype=torch.float32)

    pscan_time = benchmark(lambda: metal_pscan(x2, a2))

    print(f"  Forward B={B}, H={H}, L={L}, D={D}")
    print(f"  Time: {pscan_time:.2f} ms")
    print("  ✓ PASSED")
    return True

def test_mps_bitsandbytes():
    """Test mps-bitsandbytes quantization."""
    print("\n" + "="*60)
    print("MPS BitsAndBytes")
    print("="*60)

    try:
        from mps_bitsandbytes import quantize_rowwise, dequantize_rowwise
    except ImportError as e:
        print(f"SKIP: {e}")
        return False

    M, N = 1024, 1024
    x = torch.randn(M, N, device=device, dtype=torch.float16)

    # Quantize
    quant, state = quantize_rowwise(x)
    assert quant is not None, "Quantization failed"

    # Dequantize
    deq = dequantize_rowwise(quant, state)
    assert deq.shape == x.shape, f"Shape mismatch: {deq.shape}"

    # Check reconstruction error
    error = (x - deq).abs().mean().item()
    print(f"  Quantize/Dequantize {M}x{N}")
    print(f"  Mean abs error: {error:.4f}")

    # Benchmark
    quant_time = benchmark(lambda: quantize_rowwise(x))
    print(f"  Quantize time: {quant_time:.2f} ms")
    print("  ✓ PASSED")
    return True

def test_mps_deform_conv():
    """Test mps-deform-conv forward and backward."""
    print("\n" + "="*60)
    print("MPS Deformable Conv2D")
    print("="*60)

    try:
        from mps_deform_conv import deform_conv2d
    except ImportError as e:
        print(f"SKIP: {e}")
        return False

    B, C_in, H, W = 2, 64, 32, 32
    C_out, kH, kW = 64, 3, 3

    x = torch.randn(B, C_in, H, W, device=device, dtype=torch.float32, requires_grad=True)
    weight = torch.randn(C_out, C_in, kH, kW, device=device, dtype=torch.float32, requires_grad=True)
    offset = torch.randn(B, 2*kH*kW, H, W, device=device, dtype=torch.float32, requires_grad=True)

    # Forward
    out = deform_conv2d(x, offset, weight)
    assert out.shape[0] == B and out.shape[1] == C_out, f"Shape mismatch: {out.shape}"
    assert not torch.isnan(out).any(), "NaN in output"

    # Backward
    loss = out.sum()
    loss.backward()
    assert x.grad is not None, "No grad for x"

    # Benchmark
    x2 = torch.randn(B, C_in, H, W, device=device, dtype=torch.float32)
    offset2 = torch.randn(B, 2*kH*kW, H, W, device=device, dtype=torch.float32)

    deform_time = benchmark(lambda: deform_conv2d(x2, offset2, weight.detach()))

    print(f"  Forward B={B}, C={C_in}, H={H}, W={W}")
    print(f"  Time: {deform_time:.2f} ms")
    print("  ✓ PASSED")
    return True

def test_mps_correlation():
    """Test mps-correlation forward and backward."""
    print("\n" + "="*60)
    print("MPS Correlation")
    print("="*60)

    try:
        from mps_correlation import correlation
    except ImportError as e:
        print(f"SKIP: {e}")
        return False

    B, C, H, W = 2, 64, 32, 32
    max_disp = 4

    x1 = torch.randn(B, C, H, W, device=device, dtype=torch.float32, requires_grad=True)
    x2 = torch.randn(B, C, H, W, device=device, dtype=torch.float32, requires_grad=True)

    # Forward
    out = correlation(x1, x2, max_displacement=max_disp)
    assert not torch.isnan(out).any(), "NaN in output"

    # Backward
    loss = out.sum()
    loss.backward()
    assert x1.grad is not None, "No grad for x1"

    # Benchmark
    x1_2 = torch.randn(B, C, H, W, device=device, dtype=torch.float32)
    x2_2 = torch.randn(B, C, H, W, device=device, dtype=torch.float32)

    corr_time = benchmark(lambda: correlation(x1_2, x2_2, max_displacement=max_disp))

    print(f"  Forward B={B}, C={C}, H={H}, W={W}, max_disp={max_disp}")
    print(f"  Output shape: {out.shape}")
    print(f"  Time: {corr_time:.2f} ms")
    print("  ✓ PASSED")
    return True

def test_mps_carafe():
    """Test mps-carafe forward and backward."""
    print("\n" + "="*60)
    print("MPS CARAFE")
    print("="*60)

    try:
        from mps_carafe import carafe
    except ImportError as e:
        print(f"SKIP: {e}")
        return False

    B, C, H, W = 2, 64, 16, 16
    scale = 2
    k_up = 5
    group = 1

    x = torch.randn(B, C, H, W, device=device, dtype=torch.float32, requires_grad=True)
    # CARAFE expects mask at OUTPUT resolution
    H_out, W_out = H * scale, W * scale
    mask = torch.randn(B, group * k_up*k_up, H_out, W_out, device=device, dtype=torch.float32, requires_grad=True)

    # Forward
    out = carafe(x, mask, kernel_size=k_up, group_size=group, scale_factor=scale)
    assert out.shape == (B, C, H_out, W_out), f"Shape mismatch: {out.shape}"
    assert not torch.isnan(out).any(), "NaN in output"

    # Backward
    loss = out.sum()
    loss.backward()
    assert x.grad is not None, "No grad for x"

    # Benchmark
    x2 = torch.randn(B, C, H, W, device=device, dtype=torch.float32)
    mask2 = torch.randn(B, group * k_up*k_up, H_out, W_out, device=device, dtype=torch.float32)

    carafe_time = benchmark(lambda: carafe(x2, mask2, kernel_size=k_up, group_size=group, scale_factor=scale))

    print(f"  Forward B={B}, C={C}, H={H}, W={W}, scale={scale}")
    print(f"  Time: {carafe_time:.2f} ms")
    print("  ✓ PASSED")
    return True

def test_mps_conv3d():
    """Test mps-conv3d forward and backward."""
    print("\n" + "="*60)
    print("MPS Conv3D")
    print("="*60)

    try:
        from mps_conv3d import conv3d
    except ImportError as e:
        print(f"SKIP: {e}")
        return False

    B, C_in, D, H, W = 2, 32, 8, 16, 16
    C_out, kD, kH, kW = 64, 3, 3, 3

    x = torch.randn(B, C_in, D, H, W, device=device, dtype=torch.float32, requires_grad=True)
    weight = torch.randn(C_out, C_in, kD, kH, kW, device=device, dtype=torch.float32, requires_grad=True)

    # Forward
    out = conv3d(x, weight)
    assert out.shape[0] == B and out.shape[1] == C_out, f"Shape mismatch: {out.shape}"
    assert not torch.isnan(out).any(), "NaN in output"

    # Backward
    loss = out.sum()
    loss.backward()
    assert x.grad is not None, "No grad for x"

    # Benchmark
    x2 = torch.randn(B, C_in, D, H, W, device=device, dtype=torch.float32)

    conv3d_time = benchmark(lambda: conv3d(x2, weight.detach()))

    print(f"  Forward B={B}, C={C_in}, D={D}, H={H}, W={W}")
    print(f"  Output shape: {out.shape}")
    print(f"  Time: {conv3d_time:.2f} ms")
    print("  ✓ PASSED")
    return True

def main():
    print("="*60)
    print("MPS Packages Test Suite")
    print("="*60)
    print(f"PyTorch: {torch.__version__}")
    print(f"MPS available: {torch.backends.mps.is_available()}")

    if not torch.backends.mps.is_available():
        print("ERROR: MPS not available!")
        sys.exit(1)

    results = {}

    tests = [
        ("mps-flash-attn", test_mps_flash_attention),
        ("mamba-metal", test_mamba_metal),
        ("mps-bitsandbytes", test_mps_bitsandbytes),
        ("mps-deform-conv", test_mps_deform_conv),
        ("mps-correlation", test_mps_correlation),
        ("mps-carafe", test_mps_carafe),
        ("mps-conv3d", test_mps_conv3d),
    ]

    for name, test_fn in tests:
        try:
            results[name] = test_fn()
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL/SKIP"
        print(f"  {name}: {status}")

    print(f"\n{passed}/{total} packages tested successfully")

    if passed < total:
        sys.exit(1)

if __name__ == "__main__":
    main()
