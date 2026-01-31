
from sympy import Point, Line, N, simplify, symbols, var
import sympy as sp

class GeometryEngine:
    """
    Geometry extraction from GeoGebra concepts.
    Handles 2D analytic geometry.
    """
    
    @staticmethod
    def _parse_point(p):
        """Convert input (tuple, list, or existing Point) to SymPy Point."""
        if isinstance(p, (tuple, list)):
            return Point(*p)
        if isinstance(p, Point):
            return p
        # Attempt to parse string "1,2" or "(1,2)"
        s = str(p).strip("()")
        try:
            parts = s.split(',')
            return Point(float(parts[0]), float(parts[1]))
        except:
            raise ValueError(f"Invalid point format: {p}")

    def distancia(self, p1, p2):
        """Distance between two points."""
        A = self._parse_point(p1)
        B = self._parse_point(p2)
        return A.distance(B)

    def punto_medio(self, p1, p2):
        """Midpoint of segment P1-P2."""
        A = self._parse_point(p1)
        B = self._parse_point(p2)
        return A.midpoint(B)

    def pendiente(self, p1, p2):
        """Slope of line passing through P1 and P2."""
        A = self._parse_point(p1)
        B = self._parse_point(p2)
        if A.x == B.x:
            return float('inf') # Vertical line
        return (B.y - A.y) / (B.x - A.x)

    def recta(self, p1, p2):
        """Equation of line passing through P1 and P2."""
        A = self._parse_point(p1)
        B = self._parse_point(p2)
        line = Line(A, B)
        # SymPy Line equation is generic. We want y = mx + b form usually.
        # equation() method returns a*x + b*y + c = 0
        x, y = symbols('x y')
        eq = line.equation(x, y)
        # Solve for y
        res = sp.solve(eq, y)
        if res:
            return sp.Eq(y, res[0])
        else:
            # Vertical line x = c
            res_x = sp.solve(eq, x)
            return sp.Eq(x, res_x[0])

    def circulo(self, centro, radio):
        """Equation of circle."""
        C = self._parse_point(centro)
        r = float(radio)
        x, y = symbols('x y')
        return sp.Eq((x - C.x)**2 + (y - C.y)**2, r**2)
