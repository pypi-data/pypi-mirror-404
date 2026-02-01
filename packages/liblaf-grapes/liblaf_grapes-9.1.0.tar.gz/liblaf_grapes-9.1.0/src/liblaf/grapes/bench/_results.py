from __future__ import annotations

from typing import TYPE_CHECKING, Any

import attrs

from liblaf.grapes import deps

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure


@attrs.define
class BenchResults:
    outputs: dict[str, list[Any]]
    sizes: list[float]
    timings: dict[str, list[float]]

    def plot(
        self,
        *,
        relative_to: str | None = None,
        xlabel: str = "Size",
        ylabel: str = "Time (sec)",
        log_scale: bool = True,
    ) -> Figure:
        with deps.optional_deps("liblaf-grapes", "bench"):
            import matplotlib.pyplot as plt

        if relative_to is None:
            relative_to = min(self.timings.keys(), key=lambda k: self.timings[k][-1])

        fig: Figure
        ax0: Axes
        ax1: Axes
        fig, (ax0, ax1) = plt.subplots(1, 2, sharex="all", figsize=(12.8, 4.8))

        for label, timings in self.timings.items():
            ax0.plot(self.sizes, timings, label=label)
            base: list[float] = self.timings[relative_to]
            relative: list[float] = [t / b for t, b in zip(timings, base, strict=True)]
            ax1.plot(self.sizes, relative, label=label)

        ax0.grid(which="both", linestyle="--")
        ax0.legend()
        ax0.set_xlabel(xlabel)
        ax0.set_ylabel(ylabel)

        ax1.grid(which="both", linestyle="--")
        ax1.legend()
        ax1.set_xlabel(xlabel)
        ax1.set_ylabel(f"{ylabel} (relative to {relative_to})")

        if log_scale:
            ax0.set_xscale("log")
            ax0.set_yscale("log")
            ax1.set_xscale("log")

        fig.tight_layout()
        return fig
