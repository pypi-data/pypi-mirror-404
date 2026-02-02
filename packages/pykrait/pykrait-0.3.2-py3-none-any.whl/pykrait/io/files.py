import os
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, get_origin, get_args, Union
from importlib.metadata import version

def get_files_from_folder(
    folder: str,
    extension: str = ".czi",
) -> list[str]:
    """returns all files from a folder with specified extensions.

    :param folder: path to the folder
    :type folder: str
    :param extensions: str of file extension (default is ".czi")
    :type extensions: str
    :return: list of file paths with the specified extensions
    :rtype: list[str]
    """
    if not os.path.isdir(folder):
        raise NotADirectoryError(f"Provided path is not a directory: {folder}")

    files = [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if os.path.isfile(os.path.join(folder, f))
        and os.path.splitext(f)[-1].lower() == extension
    ]
    files = [f for f in files if not os.path.basename(f).startswith(".")]
    return files


def get_pykrait_version() -> str:
    """returns the current version of pykrait."""
    try:
        __version__ = version("pykrait")
        return __version__
    except Exception as e:
        print(f"Could not retrieve pykrait version: {e}")
        return None  # Default version if not found

def save_Txnrois(array: np.ndarray, frame_interval: float, filepath: str) -> None:
    """
    Saves a T x n_roi array to a CSV file with a header to denote the ROIs and a time index

    :param array: T x n_roi array to save
    :type array: np.ndarray
    :param filename: name of the output file
    :type filename: str
    :param frame_interval: frame interval in seconds
    :type frame_interval: float
    """
    if not isinstance(array, np.ndarray):
        raise TypeError("Input must be a numpy ndarray")

    if array.ndim != 2:
        raise ValueError("Input array must be 2D (T x n_roi)")

    n_frames, n_rois = array.shape
    timepoints = np.round((np.arange(n_frames) * frame_interval), 2)
    columns = [f"ROI_{i}" for i in range(n_rois)]

    df = pd.DataFrame(array, columns=columns, index=timepoints)
    df.index.name = "Time (s)"
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=True, compression="zstd")


def read_Txnrois(filepath: str, n_frames: int = None, n_rois: int = None) -> np.ndarray:
    """
    loads a T x n_roi array to a CSV file with a header to denote the ROIs and a time index

    :param filepath: path to the CSV file
    :type filepath: str
    :param n_frames: number of frames in the timelapse
    :type n_frames: int
    :return: numpy array of shape (n_frames, n_rois)
    :rtype: np.ndarray
    """
    df = pd.read_csv(filepath, index_col=0)

    if n_frames is not None and df.shape[0] != n_frames:
        raise ValueError(
            f"Expected {n_frames} frames, but got {df.shape[0]} in {filepath}"
        )
    if n_rois is not None and df.shape[1] != n_rois:
        raise ValueError(f"Expected {n_rois} ROIs, but got {df.shape[1]} in {filepath}")

    return df.to_numpy()


def save_NroisxF(
    array: np.ndarray,
    filepath: str,
    header: List[str] = None,
) -> None:
    """
    Saves a Nrois x F array to a CSV file with an index to denote the ROIs and a header for the features
    :param array: T x n_roi array to save
    :type array: np.ndarray
    :param filename: name of the output file
    :type filename: str
    :param frame_interval: frame interval in seconds
    :type frame_interval: float
    """
    if not isinstance(array, np.ndarray):
        raise TypeError("Input must be a numpy ndarray")
    if len(header) != array.shape[1]:
        raise ValueError("Header length must match the number of columns in the array")
    df = pd.DataFrame(array, columns=header)
    df.index.name = "ROIs"
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=True, compression="zstd")


def concat_analysis_files(root_folder: str, filetype:str="output") -> None:
    """
    Concatenates all *_analysis_output.csv files in the given root folder and its subdirectories into a single CSV file named experiment_overview.csv.

    :param root_folder: folder where *_analysis_output.csv files are located
    :type root_folder: str
    :raises FileNotFoundError: if no *_analysis_output.csv files are found
    """
    root = Path(root_folder)
    # Search recursively for *_analysis_output.csv
    if filetype == "output":
        csv_files = [
            f
            for f in root.rglob("*_analysis_output.csv")
            if not f.name.startswith(".")  # skip hidden files
        ]
        if not csv_files:
            raise FileNotFoundError(
                "No *_analysis_output.csv files found in the directory or subdirectories."
            )
        output_path = root / "analysis_output_overview.csv"
    elif filetype == "parameters":
        csv_files = [
            f
            for f in root.rglob("*_analysis_parameters.csv")
            if not f.name.startswith(".")  # skip hidden files
        ]
        if not csv_files:
            raise FileNotFoundError(
                "No *_analysis_parameters.csv files found in the directory or subdirectories."
            )
        output_path = root / "analysis_params_overview.csv"
    else:
        raise ValueError(f"Unexpected filetype: {filetype}, use 'parameters' or 'output'")
    dfs = []
    for f in csv_files:
        df = pd.read_csv(f)
        # Record the relative path for context
        df["source_file"] = str(f.relative_to(root))
        dfs.append(df)

    combined = pd.concat(dfs, ignore_index=True)

    combined.to_csv(output_path, index=False)
    print(f"Saved combined CSV to {output_path}")

def _auto_cast(value: str, target_type):
    """Safely cast a CSV string to the given target type."""
    if value is None:
        return None

    value = value.strip()
    if value == "":
        return None

    # Handle Optional[T]
    if get_origin(target_type) is Union:
        args = [t for t in get_args(target_type) if t is not type(None)]
        if args:
            target_type = args[0]

    try:
        if target_type is bool:
            return value.lower() in ("1", "true", "yes", "y", "t")
        elif target_type is int:
            return int(value)
        elif target_type is float:
            return float(value)
        elif target_type is str:
            return value
        else:
            # fallback: return as string
            return value
    except Exception:
        raise ValueError(f"Cannot convert '{value}' to {target_type}")
