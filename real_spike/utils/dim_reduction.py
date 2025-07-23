from filterpy.kalman import KalmanFilter
import numpy as np


def bin_spikes(spikes: np.ndarray, bin_size: int):
    """Bin spikes into bins of given size."""
    n_channels, n_timepoints = spikes.shape
    n_bins = n_timepoints // bin_size  # drop remainder
 #   print(n_bins)
    spikes = spikes[:, :n_bins * bin_size]  # truncate to fit bins

    # Reshape and sum
    binned = spikes.reshape(n_channels, n_bins, bin_size).sum(axis=2)
    return binned



def kalman_filter(data, A=1, H=1, Q=1e-2, R=1, initial_state=None):
    """
    Applies 1D Kalman filter to each channel in the binned spike data.

    Args:
        data (ndarray): Shape (n_channels, n_time_bins)
        A: State transition
        H: Observation model
        Q: Process noise
        R: Measurement noise
        initial_state: Optional starting value per channel

    Returns:
        ndarray: Smoothed data of same shape
    """
    n_channels, n_time = data.shape
    smoothed = np.zeros_like(data, dtype=float)

    for ch in range(n_channels):
        kf = KalmanFilter(dim_x=1, dim_z=1)
        kf.F = np.array([[A]])     # State transition matrix
        kf.H = np.array([[H]])     # Observation matrix
        kf.Q = np.array([[Q]])     # Process noise covariance
        kf.R = np.array([[R]])     # Measurement noise covariance
        kf.x = np.array([[initial_state[ch] if initial_state else data[ch, 0]]])  # Initial state
        kf.P = np.eye(1) * 1       # Initial covariance

        for t in range(n_time):
            kf.predict()
            kf.update(np.array([[data[ch, t]]]))
            smoothed[ch, t] = kf.x[0, 0]

    return smoothed



def get_trial_PCA(trial, pca, num_comp=3):
    """Returns the fraction of explained variance and projected trajectory for a given trial."""
    X = trial.T # (smoothed bins, channels)

    # total trial variance
    total_var = np.var(X, axis=0).sum()

    # project the data
    proj = pca.transform(X)

    # variance for a given number of comps
    pc_vars = np.var(proj, axis=0)

    # fraction of explained var
    explained = pc_vars / total_var

    return explained[:num_comp], proj