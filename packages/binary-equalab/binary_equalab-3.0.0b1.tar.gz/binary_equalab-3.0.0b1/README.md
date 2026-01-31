# Binary EquaLab CLI

<p align="center">
  <img src="../docs/banner_cli.png" alt="Binary EquaLab CLI" width="500">
</p>

<p align="center">
  <em>"Las matemáticas también sienten, pero estas no se equivocan."</em>
</p>

---

## 🚀 Installation

```bash
pip install binary-equalab
```

Or from source:
```bash
# En carpeta binary-cli
pip install -e .
bneqls
```
(La opción `-e` hace que los cambios se reflejen al momento sin reinstalar).

### 📱 Termux (Android)
La instalación en Termux nativo requiere compilar algunas dependencias (NumPy/SymPy).

```bash
# 1. Instalar compiladores y librerías del sistema
pkg update
pkg install python clang make pkg-config libjpeg-turbo freetype libpng

# 2. Instalar Binary EquaLab
pip install binary-equalab
```

---

## 🐚 Universal Shell Setup
Binary EquaLab incluye un configurador mágico para tu terminal. Instala temas (Oh My Posh/Zsh), fuentes y plugins automáticamente.

```bash
# Ejecutar configurador
binary setup-shell
# O directamente:
python -m binary_equalab.cli setup-shell
```

Soporta:
-   **Windows**: Oh My Posh + Nerd Fonts.
-   **Termux**: Zsh + Oh My Zsh + Autosuggestions.
-   **Linux**: Recomendaciones de Starship.

## 🚀 Uso del CLI

### REPL Mode
```bash
binary-math
```

```
Binary EquaLab CLI v1.0.0
>>> derivar(x^2 + 3x, x)
→ 2*x + 3

>>> integrar(sin(x), x)
→ -cos(x)

>>> factorial(5)
→ 120

>>> van(0.10, -1000, 300, 400, 500)
→ 78.82
```

### One-liner Mode
```bash
binary-math "derivar(x^3, x)"
# Output: 3*x^2

binary-math "factorial(10)"
# Output: 3628800

binary-math "0b1010 + 0b0101"
# Output: 15
```

---

## 🔢 Functions

### Calculus
| Function                | Example                    | Result    |
| ----------------------- | -------------------------- | --------- |
| `derivar(f, x)`         | `derivar(x^2, x)`          | `2*x`     |
| `integrar(f, x)`        | `integrar(sin(x), x)`      | `-cos(x)` |
| `limite(f, x, a)`       | `limite(sin(x)/x, x, 0)`   | `1`       |
| `sumatoria(f, n, a, b)` | `sumatoria(n^2, n, 1, 10)` | `385`     |

### Algebra
| Function         | Example                      | Result        |
| ---------------- | ---------------------------- | ------------- |
| `simplificar(f)` | `simplificar((x^2-1)/(x-1))` | `x+1`         |
| `expandir(f)`    | `expandir((x+1)^2)`          | `x^2+2*x+1`   |
| `factorizar(f)`  | `factorizar(x^2-1)`          | `(x-1)*(x+1)` |
| `resolver(f, x)` | `resolver(x^2-4, x)`         | `[-2, 2]`     |

### Statistics
| Function          | Example                        |
| ----------------- | ------------------------------ |
| `media(...)`      | `media(1, 2, 3, 4, 5)` → `3`   |
| `mediana(...)`    | `mediana(1, 2, 3, 4, 5)` → `3` |
| `desviacion(...)` | Standard deviation             |
| `varianza(...)`   | Variance                       |

### Finance
| Function                        | Example                                |
| ------------------------------- | -------------------------------------- |
| `van(r, cf0, cf1, ...)`         | `van(0.10, -1000, 300, 400)`           |
| `tir(cf0, cf1, ...)`            | `tir(-1000, 300, 400, 500)`            |
| `depreciar(cost, res, years)`   | `depreciar(10000, 1000, 5)`            |
| `interes_simple(c, r, t)`       | `interes_simple(1000, 0.05, 3)`        |
| `interes_compuesto(c, r, n, t)` | `interes_compuesto(1000, 0.05, 12, 3)` |

### Number Systems
```
0b1010    → 10   (binary)
0xFF      → 255  (hexadecimal)
0o17      → 15   (octal)
```

---

## 🥚 Easter Eggs

Try these:
- `1+1`
- `(-1)*(-1)`
- `0b101010`

---

## 🛠️ Development

```bash
cd binary-cli
pip install -e ".[dev]"
pytest
```

---

MIT © Aldra's Team
