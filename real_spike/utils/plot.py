"""Utility plotting functions."""
import numpy as np


def plot_dynamics_2d(dynamics_matrix: np.ndarray,
                     bias_vector: np.ndarray,
                     axis,
                     mins=[-2, -2],
                     maxs=[2, 2],
                     npts=13,
                     **kwargs
                     ):
    assert dynamics_matrix.shape == (2, 2), "Must pass a 2 x 2 dynamics matrix to visualize."
    assert len(bias_vector) == 2, "Bias vector must have length 2."

    x_grid, y_grid = np.meshgrid(np.linspace(mins[0], maxs[0], npts), np.linspace(mins[1], maxs[1], npts))

    xy_grid = np.column_stack((x_grid.ravel(), y_grid.ravel(), np.zeros((npts ** 2, 0))))
    dx = xy_grid.dot(dynamics_matrix.T) + bias_vector - xy_grid

    q = axis.quiver(x_grid, y_grid, dx[:, 0], dx[:, 1], color='blue', **kwargs)

    return q

def plot_dynamics_3d(dynamics_matrix: np.ndarray,
                     bias_vector: np.ndarray,
                     axis,
                     mins=[-2.5, -2.5, -2.5],
                     maxs=[2.5, 2.5, 2.5],
                     npts=15,
                     **kwargs):
    assert dynamics_matrix.shape == (3, 3), "Must pass a 3 x 3 dynamics matrix to visualize."
    assert len(bias_vector) == 3, "Bias vector must have length 3."

    x = np.linspace(mins[0], maxs[0], npts)
    y = np.linspace(mins[1], maxs[1], npts)
    z = np.linspace(mins[2], maxs[2], npts)

    x_grid, y_grid, z_grid = np.meshgrid(x, y, z, indexing='ij')

    xyz_grid = np.stack([x_grid.ravel(), y_grid.ravel(), z_grid.ravel()], axis=1)

    I = np.eye(3)
    dx = (dynamics_matrix - I) @ xyz_grid.T + bias_vector[:, np.newaxis]

    U = dx[0].reshape(x_grid.shape)
    V = dx[1].reshape(y_grid.shape)
    W = dx[2].reshape(z_grid.shape)

    q = axis.quiver(x_grid, y_grid, z_grid, U, V, W, length=0.3, normalize=True, **kwargs)

    return q