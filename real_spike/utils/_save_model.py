import pickle
import numpy as np

def save_model(
        path: str,
        animal_id: str,
        session_id: str,
        model_data: np.ndarray,
        input_data: np.ndarray,
        latent_dim: int,
        observation_dim: int,
        input_dim: int,
        phases: int,
        model: object,
        raw_trajectories: np.ndarray,
        smooth_trajectories: np.ndarray,
):
    """
    Pickle a model object and related inputs for an LDS fit using the ssm library.

    Parameters
    ----------
    animal_id: str
        The animal id, e.g. rb50
    session_id: str
        The session id, e.g. 20250125
    path: str
        The location of the pickle file to output (/wasabi/ProjectionProject/rb69/20260303/stim-only.pkl)
    model_data: np.ndarray
        The model data used to fit the model
    input_data: np.ndarray
        The input data used to fit the model, can be None if no inputs (i.e. control trials only)
    latent_dim: int
        The latent dimension of the model (how many dims being projected down to)
    observation_dim: int
        The observation dimension of the model (how many neurons or channels observed)
    phases: int
        Number of phases (LDS vs. SLDS)
    input_dim: int
        The dimension of the inputs (how many conditions)
    model: object
        The ssm LDS model object
    raw_trajectories: np.ndarray
        The raw latent trajectories for each trial
    smooth_trajectories: np.ndarray
        The smooth latent trajectories for each trial

    """
    output = dict()
    output["animal_id"] = animal_id
    output["session_id"] = session_id
    output["model_data"] = model_data
    output["input_data"] = input_data
    output["latent_dim"] = latent_dim
    output["observation_dim"] = observation_dim
    output["input_dim"] = input_dim
    output["num_phases"] = phases
    output["model"] = model
    output["raw_trajectories"] = raw_trajectories
    output["smooth_trajectories"] = smooth_trajectories




    with open(path, "wb") as f:
        pickle.dump(output, f)
