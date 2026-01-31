"""
Binary EquaLab - Giac Engine Connector (PoC)
--------------------------------------------
Bridge between Python and the C++ Giac CAS engine via 'giacpy'.
This module provides raw speed for Gröbner bases and heavy algebra.
"""

import sys

HAS_GIAC = False
try:
    import giacpy
    from giacpy import giac
    HAS_GIAC = True
except ImportError:
    pass

class GiacEngine:
    def __init__(self):
        if not HAS_GIAC:
            print("⚠️  GiacPy not installed. Running in SymPy-only mode.")
            print("   To enable C++ speed: pip install giacpy")
            
    def eval(self, expr: str):
        """Evaluate expression using Giac C++ engine"""
        if not HAS_GIAC:
            return "Error: Giac C++ engine not available."
        
        try:
            # Giac handles the string parsing
            result = giac(expr)
            return result
        except Exception as e:
            return f"Giac Error: {e}"

    def benchmark(self):
        """Run a speed test vs SymPy"""
        if not HAS_GIAC:
            return
        
        import time
        from sympy import expand, symbols
        
        print("\n🏎️  BENCHMARK: Python (SymPy) vs C++ (Giac)")
        print("-" * 40)
        
        # Test Case: Expand big polynomial
        poly_str = "(x+y+z+1)^15"
        
        # SymPy
        x, y, z = symbols('x y z')
        start = time.time()
        # sympy_res = expand((x+y+z+1)**15) # Warning: This is huge
        # Keeping it smaller for quick test
        _ = expand((x+y+z+1)**5)
        dt_sympy = time.time() - start
        print(f"SymPy (Power 5): {dt_sympy:.4f}s")
        
        # Giac
        start = time.time()
        _ = giac("(x+y+z+1)^5").expand()
        dt_giac = time.time() - start
        print(f"Giac  (Power 5): {dt_giac:.4f}s")
        
        print(f"🏆 Winner: {'Giac' if dt_giac < dt_sympy else 'SymPy'}")

if __name__ == "__main__":
    g = GiacEngine()
    if HAS_GIAC:
        print("Testing Giac...")
        print(f"Diff(sin(x^2)): {g.eval('diff(sin(x^2), x)')}")
        g.benchmark()
    else:
        print("Install giacpy to run this test.")
