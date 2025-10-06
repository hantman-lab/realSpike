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