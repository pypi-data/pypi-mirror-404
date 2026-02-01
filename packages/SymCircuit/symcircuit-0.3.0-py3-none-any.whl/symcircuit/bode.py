from typing import Optional, Dict

import plotkit.plotkit as pk
from sympy import Expr

from .plotting import FrequencyDomainPlotter


def plot_system(transfer: Expr, fmin: float = 1, fmax: float = 100000,
                amplitude_linear: bool = False,
                points_per_decade: int = 50,
                values: Optional[Dict[str, float]] = None,
                return_fig=False) -> Optional[pk.Figure]:
    plotter = FrequencyDomainPlotter(transfer)
    plotter.set_range(fmin, fmax)
    plotter.points_per_decade = points_per_decade

    return plotter.bode(values, return_fig=return_fig, amplitude_linear=amplitude_linear)
