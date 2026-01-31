"""
Binary EquaLab - Math Engine
Core symbolic computation using SymPy with Spanish function translations.
"""

import sympy as sp
from sympy import (
    Symbol, symbols, sin, cos, tan, sqrt, exp, log, ln, pi, E, I,
    diff, integrate, limit, summation, simplify, expand, factor, solve,
    Abs, factorial, gamma, binomial, floor, ceiling,
    Matrix, det, Transpose
)
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations, implicit_multiplication_application,
    convert_xor, function_exponentiation
)
from typing import Any, Union, List, Optional
import re

from .parser_enhanced import EnhancedParser
from .sonify import AudioEngine
from .geometry import GeometryEngine

# Symbol shortcuts
x, y, z, t, n, k = symbols('x y z t n k')


class MathEngine:
    """
    Core math engine with Spanish function support.
    Wraps SymPy with user-friendly Spanish aliases.
    """
    
    def __init__(self):
        self.symbols = {'x': x, 'y': y, 'z': z, 't': t, 'n': n, 'k': k}
        self.last_result = None
        self.history: List[str] = []
        
        # Spanish → SymPy function mapping
        self.function_map = {
            # Calculus
            'derivar': self._derivar,
            'integrar': self._integrar,
            'limite': self._limite,
            'sumatoria': self._sumatoria,
            
            # Algebra
            'simplificar': self._simplificar,
            'expandir': self._expandir,
            'factorizar': self._factorizar,
            'resolver': self._resolver,
            
            # Statistics
            'media': self._media,
            'mediana': self._mediana,
            'desviacion': self._desviacion,
            'varianza': self._varianza,
            
            # Finance
            'van': self._van,
            'tir': self._tir,
            'depreciar': self._depreciar,
            'interes_simple': self._interes_simple,
            'interes_compuesto': self._interes_compuesto,
            
            # Audio / Sonification
            'sonify': self._sonify,
            'sonificar': self._sonify,

            # Geometry
            'distancia': self._distancia,
            'punto_medio': self._punto_medio,
            'pendiente': self._pendiente,
            'recta': self._recta,
            'circulo': self._circulo,
            
            # Trigonometry aliases
            'seno': sin,
            'coseno': cos,
            'tangente': tan,
            'arcoseno': sp.asin,
            'arcocoseno': sp.acos,
            'arcotangente': sp.atan,
        }
    
    def parse(self, expression: str) -> Any:
        """Parse a math expression string into SymPy."""
        # Preprocess Spanish functions
        expr = self._preprocess(expression)
        
        # Parse with transformations
        transformations = (
            standard_transformations + 
            (implicit_multiplication_application, convert_xor, function_exponentiation)
        )
        
        try:
            result = parse_expr(expr, local_dict=self.symbols, transformations=transformations)
            return result
        except Exception as e:
            raise ValueError(f"Parse error: {e}")
    
    def evaluate(self, expression: str) -> Any:
        """Evaluate a math expression and return the result."""
        expression = expression.strip()
        
        if not expression:
            return None
            
        self.history.append(expression)
        
        if expression.lower().strip() in ["sentimiento", "amor", "error", "feel"]:
            return "Aquí el sentimiento existe. El error, no."

        # Check for variable assignment (e.g., "a = 5")
        assignment_match = re.match(r'^([a-zA-Z_]\w*)\s*=\s*(.+)$', expression)
        if assignment_match:
            var_name, val_expr = assignment_match.groups()
            try:
                # Calculate value first
                val_result = self.evaluate(val_expr)
                # Store in symbols
                self.symbols[var_name] = val_result
                return val_result
            except Exception as e:
                raise ValueError(f"Assignment error: {e}")

        # Check for function calls
        for func_name, func in self.function_map.items():
            if expression.startswith(f'{func_name}('):
                result = self._call_function(expression)
                self.last_result = result
                return result
        
        # Standard expression evaluation
        try:
            parsed = self.parse(expression)
            result = sp.simplify(parsed)
            self.last_result = result
            return result
        except Exception as e:
            raise ValueError(f"Evaluation error: {e}")
    
    def _preprocess(self, expr: str) -> str:
        """Convert Spanish function names and shortcuts."""
        # Replace Spanish trig
        replacements = {
            'seno': 'sin',
            'sen': 'sin',
            'coseno': 'cos', 
            'tangente': 'tan',
            'arcoseno': 'asin',
            'arcocoseno': 'acos',
            'arcotangente': 'atan',
            'raiz': 'sqrt',
            'absoluto': 'Abs',
            'logaritmo': 'log',
            'exponencial': 'exp',
        }
        
        for es, en in replacements.items():
            expr = re.sub(rf'\b{es}\b', en, expr, flags=re.IGNORECASE)
        
        # Enhanced Parser Logic (Sugared Syntax)
        expr = EnhancedParser.preprocess(expr)

        # Handle ^ as power (fallback)
        expr = expr.replace('^', '**')
        
        return expr
    
    def _call_function(self, expression: str) -> Any:
        """Call a Spanish function with arguments."""
        # Extract function name and args
        match = re.match(r'(\w+)\((.*)\)$', expression, re.DOTALL)
        if not match:
            raise ValueError(f"Invalid function call: {expression}")
        
        func_name = match.group(1)
        args_str = match.group(2)
        
        if func_name not in self.function_map:
            raise ValueError(f"Unknown function: {func_name}")
        
        func = self.function_map[func_name]
        
        # Parse arguments
        args = self._parse_args(args_str)
        
        return func(*args)
    
    def _parse_args(self, args_str: str) -> List[Any]:
        """Parse function arguments, handling nested parentheses."""
        args = []
        current = ""
        depth = 0
        
        for char in args_str:
            if char == '(':
                depth += 1
                current += char
            elif char == ')':
                depth -= 1
                current += char
            elif char == ',' and depth == 0:
                if current.strip():
                    args.append(self._parse_single_arg(current.strip()))
                current = ""
            else:
                current += char
        
        if current.strip():
            args.append(self._parse_single_arg(current.strip()))
        
        return args
    
    def _parse_single_arg(self, arg: str) -> Any:
        """Parse a single argument - could be number, symbol, or expression."""
        try:
            return float(arg)
        except ValueError:
            pass
        
        if arg in self.symbols:
            return self.symbols[arg]
        
        return self.parse(arg)
    
    # ============ CALCULUS ============
    
    def _derivar(self, expr, var=None, n=1):
        """Derivative: derivar(x^2 + 3x, x) → 2x + 3"""
        if var is None:
            var = x
        return diff(expr, var, n)
    
    def _integrar(self, expr, var=None, a=None, b=None):
        """Integral: integrar(x^2, x) or integrar(x^2, x, 0, 1)"""
        if var is None:
            var = x
        if a is not None and b is not None:
            return integrate(expr, (var, a, b))
        return integrate(expr, var)
    
    def _limite(self, expr, var=None, punto=0, direccion=None):
        """Limit: limite(sin(x)/x, x, 0) → 1"""
        if var is None:
            var = x
        if direccion:
            return limit(expr, var, punto, direccion)
        return limit(expr, var, punto)
    
    def _sumatoria(self, expr, var=None, a=0, b=10):
        """Sum: sumatoria(n^2, n, 1, 10) → 385"""
        if var is None:
            var = n
        return summation(expr, (var, a, b))
    
    # ============ ALGEBRA ============
    
    def _simplificar(self, expr):
        """Simplify: simplificar((x^2-1)/(x-1)) → x+1"""
        return simplify(expr)
    
    def _expandir(self, expr):
        """Expand: expandir((x+1)^2) → x^2 + 2x + 1"""
        return expand(expr)
    
    def _factorizar(self, expr):
        """Factor: factorizar(x^2 - 1) → (x-1)(x+1)"""
        return factor(expr)
    
    def _resolver(self, expr, var=None):
        """Solve: resolver(x^2 - 4, x) → [-2, 2]"""
        if var is None:
            var = x
        return solve(expr, var)
    
    # ============ STATISTICS ============
    
    def _media(self, *values):
        """Mean: media(1, 2, 3, 4, 5) → 3"""
        nums = [float(v) for v in values]
        return sum(nums) / len(nums)
    
    def _mediana(self, *values):
        """Median: mediana(1, 2, 3, 4, 5) → 3"""
        nums = sorted([float(v) for v in values])
        n = len(nums)
        mid = n // 2
        if n % 2 == 0:
            return (nums[mid - 1] + nums[mid]) / 2
        return nums[mid]
    
    def _desviacion(self, *values):
        """Standard deviation: desviacion(1, 2, 3, 4, 5)"""
        nums = [float(v) for v in values]
        mean = sum(nums) / len(nums)
        variance = sum((x - mean) ** 2 for x in nums) / len(nums)
        return variance ** 0.5
    
    def _varianza(self, *values):
        """Variance: varianza(1, 2, 3, 4, 5)"""
        nums = [float(v) for v in values]
        mean = sum(nums) / len(nums)
        return sum((x - mean) ** 2 for x in nums) / len(nums)

    # ============ FINANCE ============

    def _van(self, tasa, *flujos):
        """NPV: van(0.10, -1000, 300, 400, 500)"""
        r = float(tasa)
        result = 0
        for i, flujo in enumerate(flujos):
            result += float(flujo) / ((1 + r) ** i)
        return round(result, 2)

    def _tir(self, *flujos):
        """IRR: tir(-1000, 300, 400, 500) using Newton-Raphson"""
        flows = [float(f) for f in flujos]

        def npv(r):
            return sum(f / ((1 + r) ** i) for i, f in enumerate(flows))

        def npv_deriv(r):
            return sum(-i * f / ((1 + r) ** (i + 1)) for i, f in enumerate(flows))

        r = 0.1  # Initial guess
        for _ in range(100):
            npv_val = npv(r)
            if abs(npv_val) < 1e-10:
                break
            deriv = npv_deriv(r)
            if deriv == 0:
                break
            r = r - npv_val / deriv

        return round(r * 100, 2)  # Return as percentage

    def _depreciar(self, costo, residual, años):
        """Straight-line depreciation: depreciar(10000, 1000, 5)"""
        c, r, n = float(costo), float(residual), int(años)
        annual = (c - r) / n
        schedule = []
        for i in range(n):
            schedule.append({
                'año': i + 1,
                'depreciacion': round(annual, 2),
                'acumulado': round(annual * (i + 1), 2),
                'valor_libro': round(c - annual * (i + 1), 2)
            })
        return schedule

    def _interes_simple(self, capital, tasa, tiempo):
        """Simple interest: interes_simple(1000, 0.05, 3)"""
        c, r, t = float(capital), float(tasa), float(tiempo)
        interest = c * r * t
        return {
            'interes': round(interest, 2),
            'monto_final': round(c + interest, 2)
        }

    def _interes_compuesto(self, capital, tasa, n, tiempo):
        """Compound interest: interes_compuesto(1000, 0.05, 12, 3)"""
        c, r, periods, t = float(capital), float(tasa), int(n), float(tiempo)
        monto = c * ((1 + r / periods) ** (periods * t))
        return {
            'monto_final': round(monto, 2),
            'interes': round(monto - c, 2)
        }

    def _distancia(self, p1, p2):
        geo = GeometryEngine()
        return geo.distancia(p1, p2)

    def _punto_medio(self, p1, p2):
        geo = GeometryEngine()
        return geo.punto_medio(p1, p2)

    def _pendiente(self, p1, p2):
        geo = GeometryEngine()
        return geo.pendiente(p1, p2)

    def _recta(self, p1, p2):
        geo = GeometryEngine()
        return geo.recta(p1, p2)

    def _circulo(self, centro, radio):
        geo = GeometryEngine()
        return geo.circulo(centro, radio)

    def _sonify(self, expr, duration=3.0, filename="output.wav"):
        """Generate audio from expression: sonify(sin(440*2*pi*t))"""
        engine = AudioEngine()
        return engine.generate(str(expr), float(duration), str(filename))

# Convenience functions for direct import
def derivar(expr, var=None, n=1):
    engine = MathEngine()
    return engine._derivar(engine.parse(str(expr)), var, n)

def integrar(expr, var=None, a=None, b=None):
    engine = MathEngine()
    return engine._integrar(engine.parse(str(expr)), var, a, b)

def limite(expr, var=None, punto=0):
    engine = MathEngine()
    return engine._limite(engine.parse(str(expr)), var, punto)

def sumatoria(expr, var=None, a=0, b=10):
    engine = MathEngine()
    return engine._sumatoria(engine.parse(str(expr)), var, a, b)

def simplificar(expr):
    engine = MathEngine()
    return engine._simplificar(engine.parse(str(expr)))

def expandir(expr):
    engine = MathEngine()
    return engine._expandir(engine.parse(str(expr)))

def factorizar(expr):
    engine = MathEngine()
    return engine._factorizar(engine.parse(str(expr)))

def resolver(expr, var=None):
    engine = MathEngine()
    return engine._resolver(engine.parse(str(expr)), var)

def van(tasa, *flujos):
    engine = MathEngine()
    return engine._van(tasa, *flujos)

def tir(*flujos):
    engine = MathEngine()
    return engine._tir(*flujos)

def depreciar(costo, residual, años):
    engine = MathEngine()
    return engine._depreciar(costo, residual, años)

def interes_simple(capital, tasa, tiempo):
    engine = MathEngine()
    return engine._interes_simple(capital, tasa, tiempo)

def interes_compuesto(capital, tasa, n, tiempo):
    engine = MathEngine()
    return engine._interes_compuesto(capital, tasa, n, tiempo)

def media(*values):
    engine = MathEngine()
    return engine._media(*values)

def mediana(*values):
    engine = MathEngine()
    return engine._mediana(*values)

def desviacion(*values):
    engine = MathEngine()
    return engine._desviacion(*values)

def varianza(*values):
    engine = MathEngine()
    return engine._varianza(*values)



# ... (Global functions) ...

def distancia(p1, p2):
    engine = MathEngine()
    return engine._distancia(p1, p2)

def punto_medio(p1, p2):
    engine = MathEngine()
    return engine._punto_medio(p1, p2)

def pendiente(p1, p2):
    engine = MathEngine()
    return engine._pendiente(p1, p2)

def recta(p1, p2):
    engine = MathEngine()
    return engine._recta(p1, p2)

def circulo(centro, radio):
    engine = MathEngine()
    return engine._circulo(centro, radio)

def sonify(expr, duration=3.0, filename="output.wav"):
    engine = MathEngine()
    return engine._sonify(expr, duration, filename)
