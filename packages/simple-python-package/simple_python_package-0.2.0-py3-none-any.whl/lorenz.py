'''Lorenz butterfly plot utilities.'''

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple

import matplotlib.pyplot as plt
import pandas as pd


@dataclass
class LorenzButterfly:
    '''Generate and plot Lorenz butterfly trajectories.'''

    sigma: float = 10.0
    rho: float = 28.0
    beta: float = 8.0 / 3.0
    dt: float = 0.01
    steps: int = 10_000
    initial: Tuple[float, float, float] = (0.0, 1.0, 1.05)

    def generate_data(
        self,
        *,
        steps: int | None = None,
        dt: float | None = None,
        initial: Sequence[float] | None = None,
    ) -> pd.DataFrame:
        '''Generate Lorenz system data.

        Returns a Pandas dataframe of coordinate lists.
        '''

        total_steps = steps if steps is not None else self.steps
        delta_t = dt if dt is not None else self.dt
        start = initial if initial is not None else self.initial

        x, y, z = float(start[0]), float(start[1]), float(start[2])
        xs: List[float] = [x]
        ys: List[float] = [y]
        zs: List[float] = [z]

        for _ in range(total_steps):
            dx = self.sigma * (y - x)
            dy = x * (self.rho - z) - y
            dz = x * y - self.beta * z

            x += dx * delta_t
            y += dy * delta_t
            z += dz * delta_t

            xs.append(x)
            ys.append(y)
            zs.append(z)

        return pd.DataFrame({'x': xs, 'y': ys, 'z': zs})

    def plot(
        self,
        *,
        ax: plt.Axes | None = None,
        steps: int | None = None,
        dt: float | None = None,
        initial: Sequence[float] | None = None,
        **plot_kwargs,
    ) -> plt.Axes:
        '''Plot the Lorenz butterfly trajectory and return the axes.'''

        data = self.generate_data(steps=steps, dt=dt, initial=initial)

        if ax is None:
            fig = plt.figure(figsize=plot_kwargs.pop('figsize', (8, 6)))
            ax = fig.add_subplot(111, projection='3d')

        ax.set_title('Lorenz butterfly')
        ax.plot(data['x'], data['y'], data['z'], **plot_kwargs)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
