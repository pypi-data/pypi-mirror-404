from math import pi, log10, ceil
from typing import Optional, Dict, Union, Tuple

import numpy as np
import plotkit.plotkit as pk
from sympy import Expr, sympify, Symbol

Value = Union[float, int, complex]


class FrequencyDomainPlotter:
    S = Symbol("s")

    def __init__(self, expr: Expr) -> None:
        self.expr: Expr = expr
        self.fmin: float = 1
        self.fmax: float = 100e3
        self.points_per_decade: int = 50

    def set_range(self, fmin: float, fmax: float):
        self.fmin = fmin
        self.fmax = fmax

    def _evaluate(self, values: Dict[str, Value]) -> Tuple[np.ndarray, np.ndarray]:
        rvals = {Symbol(n): sympify(v) for n, v in values.items()}
        rexpr: Expr = self.expr.xreplace(rvals)
        vtest = rexpr.evalf(subs={self.S: 1})
        if vtest.free_symbols:
            raise ValueError("Some symbols not given values: " + str(vtest.free_symbols))
        feval = np.vectorize(lambda w: complex(rexpr.evalf(subs={self.S: w})), otypes=[np.cfloat])

        points = ceil(log10(self.fmax / self.fmin) * self.points_per_decade)
        X = np.geomspace(self.fmin, self.fmax, points)
        Xiw = X * 2 * pi * 1j
        Y = feval(Xiw)
        return X, Y

    def bode(self, values: Optional[Dict[str, Value]] = None, *,
             ax: Optional[Tuple[pk.Axes, pk.Axes]] = None, return_fig=False,
             amplitude_linear=False, frequency_linear=False,
             ) -> Optional[pk.Figure]:
        if values is None:
            values = {}

        X, Y = self._evaluate(values)

        if amplitude_linear:
            ampl = np.abs(Y)
        else:
            ampl = 20 * np.log10(np.abs(Y))
        phase = np.angle(Y, deg=True)

        if ax is None:
            fig, (ax1, ax2) = pk.new_regular(2, 1)
        else:
            ax1, ax2 = ax
            fig = None

        if frequency_linear:
            ax1.plot(X, ampl)
        else:
            ax1.semilogx(X, ampl)
        if amplitude_linear:
            ax1.set_ylabel("Amplitude")
        else:
            ax1.set_ylabel("Amplitude / dB")
        pk.set_grid(ax1)
        ax1.set_xlim(self.fmin, self.fmax)
        if frequency_linear:
            ax2.plot(X, phase)
        else:
            ax2.semilogx(X, phase)
        ax2.set_ylabel("Phase / °")
        ax2.set_xlabel("Frequency / Hz")
        pk.set_grid(ax2)
        ax2.set_xlim(self.fmin, self.fmax)
        if return_fig:
            return fig
        pk.finalize(fig)

    def nyquist(self, values: Optional[Dict[str, Value]] = None, *,
                ax: Optional[Tuple[pk.Axes, pk.Axes]] = None, return_fig=False) -> Optional[pk.Figure]:
        if values is None:
            values = {}

        X, Y = self._evaluate(values)

        if ax is None:
            fig, ax = pk.new_regular(1, 1)
        else:
            fig = None

        ax.set_aspect("equal")
        ax.plot(np.real(Y), np.imag(Y))
        ax.set_ylabel("Imag")
        ax.set_xlabel("Real")
        pk.set_grid(ax)
        if return_fig:
            return fig
        pk.finalize(fig)
