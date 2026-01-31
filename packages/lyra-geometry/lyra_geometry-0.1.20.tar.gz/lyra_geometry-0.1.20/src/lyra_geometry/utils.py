import sympy as sp

from .core import TensorSpace
from .tensors import D, U


def greek(name):
    mapping = {
        "alpha": "𝛼",
        "beta": "𝛽",
        "gamma": "𝛾",
        "delta": "𝛿",
        "epsilon": "𝜀",
        "zeta": "𝜁",
        "eta": "𝜂",
        "theta": "𝜃",
        "iota": "𝜄",
        "kappa": "𝜅",
        "lambda": "𝜆",
        "mu": "𝜇",
        "nu": "𝜈",
        "xi": "𝜉",
        "omicron": "𝜊",
        "pi": "𝜋",
        "rho": "𝜌",
        "sigma": "𝜎",
        "tau": "𝜏",
        "upsilon": "𝜐",
        "phi": "𝜑",
        "chi": "𝜒",
        "psi": "𝜓",
        "omega": "𝜔",
        "partial": "𝜕",
        "varepsilon": "𝜖",
        "vartheta": "𝜗",
        "varpi": "𝜘",
        "varphi": "𝜙",
        "varrho": "𝜚",
        "varsigma": "𝜛",
    }
    key = str(name).strip().lower()
    if key not in mapping:
        raise ValueError(f"Unknown greek letter: {name!r}.")
    return mapping[key]


def example_indexing():
    x, y = sp.symbols("x y")
    space = TensorSpace(2, (x, y))
    a, b, c = space.index("a b c")
    T = space.generic("T", (U, D))
    g = space.generic("g", (U, U))
    return T[U(a), D(b)] * g[U(b), U(c)]


__all__ = ["example_indexing", "greek"]
