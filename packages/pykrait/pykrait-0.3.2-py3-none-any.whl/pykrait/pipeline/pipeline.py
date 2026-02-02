import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import os
import tifffile
import warnings
import pandas as pd
import numpy as np
import dask.array as da
from dataclasses import dataclass, fields, asdict

from typing import Literal, Tuple

from pykrait.io.images import (
    load_timelapse_lazy,
    get_pixel_contour_from_label_img
)
from pykrait.io.files import (
    get_files_from_folder,
    get_pykrait_version,
    save_Txnrois,
    save_NroisxF,
)
from pykrait.preprocessing.segmentation import (
    create_cellpose_segmentation,
    timelapse_projection
)
from pykrait.preprocessing.timeseries_extraction import (
    extract_mean_intensities,
    extract_cell_properties,
    get_adjacency_matrix,
)
from pykrait.trace_analysis.filtering import detrend_with_sinc_filter
from pykrait.trace_analysis.peak_analysis import find_peaks, calculate_normalized_peaks, create_peak_properties
from pykrait.trace_analysis.oscillations import find_oscillating_rois, find_median_frequency
from pykrait.trace_analysis.synchronicity import calculate_synchronicity_zscore
from pykrait.visualization.image_overlays import create_synchronicity_image, create_heatmap_image

@dataclass
class AnalysisParameters:
    """This dataclass holds the modifiable parameters for calcium video analysis.

    :var tproj_type: Type of projection accross T-axis to be used for segmentation; 'std' computes standard deviation, 'sum' computes temporal sum, defaults to std.
    :vartype tproj_type: Literal['std', 'sum'], optional

    :var CLAHE_normalize: whether to apply CLAHE (Contrast Limited Adaptive Histogram Equalization) normalization to enhance image contrast.
    :vartype CLAHE_normalize: bool, optional

    :var cellpose_model_path: Path to the Cellpose model used for segmentation. Defaults to "cpsam" for the built-in CPSAM model.
    :vartype cellpose_model_path: str, optional

    :var frame_interval: time interval between consecutive video frames in seconds, defaults to None. If None provided, the frame interval obtained from the image metadata will be used or it will default to 1 second. The code will output a warning if a frame interval is provided which doesn't match with the metadata frame interval.
    :vartype frame_interval: float, optional

    :var neighbour_tolerance: Maximum distance in micrometers used to detect neighboring cells. Converted to pixels internally.
    :vartype neighbour_tolerance: float, optional

    :var sinc_filter_window: Window size for the sinc filter used to detrend the signal, specified in seconds. Converted to frame count internally.
    :vartype sinc_filter_window: float, optional

    :var peak_min_width: Minimum width at half-maximum of a detected peak in seconds. Converted to frames internally.
    :vartype peak_min_width: float, optional

    :var peak_max_width: Maximum width at half-maximum of a detected peak in seconds. Converted to frames internally.
    :vartype peak_max_width: float, optional

    :var peak_prominence: Minimum prominence of a detected peak, defined as the height difference between the peak and its surrounding baseline. Arbitrary units.
    :vartype peak_prominence: float, optional

    :var peak_min_height: Minimum height of a detected peak in arbitrary units.
    :vartype peak_min_height: float, optional

    :var periodicity_method: Method to determine periodicity of ROIs, either "cutoff" for fixed thresholds or "quantile" for quantile-based thresholds.
    :vartype periodicity_method: Literal['cutoff', 'quantile'], optional

    :var std_threshold: Threshold for the Standard Deviation, either quantile or cutoff depending on method.
    :vartype std_quantile: float, optional

    :var cov_quantile: Threshold for the CoV, either quantile or cutoff depending on method.
    :vartype cov_quantile: float, optional

    :var time_window: Time window in seconds within which peaks are considered synchronous. Calculated to frames internally. Defaults to 10 seconds.
    :vartype time_window: float, optional
    """

    tproj_type: Literal["std", "sum"] = "std"
    CLAHE_normalize: bool = True
    cellpose_model_path: str = "cpsam"
    frame_interval: float = None
    neighbour_tolerance: float = 10
    sinc_filter_window: float = 300
    peak_min_width: float = 1
    peak_max_width: float = 40
    peak_prominence: float = 1000
    peak_min_height: float = 80
    periodicity_method: Literal["cutoff", "quantile"] = "cutoff"
    std_threshold: float = 15
    cov_threshold: float = 0.2
    time_window: float = 10

    def to_pandas(self) -> pd.DataFrame:
        """Convert the dataclass to a pandas DataFrame."""
        return pd.DataFrame([asdict(self)])


@dataclass
class AnalysisOutput:
    """
    This dataclass holds the output variables of the pipeline.
    :var filepath: Path to the calcium imaging video file.
    :vartype filepath: str
    :var filename: name of the video file
    :vartype filename: str
    :var tproj_path: Path to the zproj file.
    :vartype tproj_path: str
    :var masks_path: Path to the zproj file.
    :vartype masks_path: str
    :var frame_interval: time interval between frames in seconds
    :vartype frame_interval: float
    :var pixel_interval_y: pixel size in y direction in micrometers
    :vartype pixel_interval_y: float
    :var pixel_interval_x: pixel size in x direction in micrometers
    :vartype pixel_interval_x: float
    :var number_of_cells: number of cells detected in the video
    :vartype number_of_cells: int
    :var number_of_frames: number of frames in the video
    :vartype number_of_frames: int
    :var normalized_peaks: number of peaks per 100 cells and 10 minutes of recording
    :vartype normalized_peaks: float
    :var cells_four_peaks: number of cells with at least 4 peaks detected
    :vartype cells_four_peaks: int
    :var std_cutoff: cutoff for STD threshold for the standard deviation in seconds
    :vartype std_cutoff: float
    :var random_below_std: number of cells with a standard deviation below the threshold in the random control
    :vartype random_below_std: int
    :var experiment_below_std: number of cells with a standard deviation below the threshold in the recording
    :vartype experiment_below_std: int
    :var cov_cutoff: cutoff for CoV (coefficient of variation) in the recording
    :vartype cov_threshold: float
    :var cov_quantile: quantile of random CoV compared to randomly shuffled peaks
    :vartype cov_quantile: float
    :var random_below_cov: number of cells with a coefficient of variation below the threshold in the random control
    :vartype random_below_cov: int
    :var experiment_below_cov: number of cells with a coefficient of variation below the threshold in the recording
    :vartype experiment_below_cov: int
    :var median_frequency_mHz: median frequency of all peak-peak intervals in mHz
    :vartype median_frequency_mHz: float
    :var active_cells_median_frequency_mHz: median frequency of the median peak-peak intervals of cells with at least 4 peaks in mHz
    :vartype active_cells_median_frequency_mHz: float
    :var median_peakwidth_s: median peak width at half maximum in seconds
    :vartype median_peakwidth_s: float
    :var median_rise2080_s: median rise time from 20% to 80% of peak height in seconds
    :vartype median_rise2080_s: float
    :var median_decay8020_s: median decay time from 80% to 20% of peak height in seconds
    :vartype median_decay8020_s: float
    :var total_coinciding_peaks_1st_neighbour: total number of coinciding peaks between 1st degree neighbours
    :vartype total_coinciding_peaks_1st_neighbour: int
    :var possible_coinciding_peaks_1st_neighbour: total number of possible coinciding peaks between 1st degree neighbours
    :vartype possible_coinciding_peaks_1st_neighbour: int
    :var random_1st_neighbour_zscore: z-score of synchronicity of the first neighbours in the random control
    :vartype random_1st_neighbour_zscore: float
    :var random_2nd_neighbour_zscore: z-score of synchronicity of the second neighbours in the random control
    :vartype random_2nd_neighbour_zscore: float
    :var random_3rd_neighbour_zscore: z-score of synchronicity of the third neighbours in the random control
    :vartype random_3rd_neighbour_zscore: float
    :var experiment_1st_neighbour_zscore: z-score of synchronicity of the first neighbours in the recording
    :vartype experiment_1st_neighbour_zscore: float
    :var experiment_2nd_neighbour_zscore: z-score of synchronicity of the second neighbours in the recording
    :vartype experiment_2nd_neighbour_zscore: float
    :var experiment_3rd_neighbour_zscore: z-score of synchronicity of the third neighbours in the recording
    :vartype experiment_3rd_neighbour_zscore: float
    :var pykrait_version: version of the pykrait package used for the analysis
    :vartype pykrait_version: str
    :var timestamp: timestamp of the analysis
    :vartype timestamp: np.datetime64
    """

    filepath: str = None
    filename: str = None
    tproj_path: str = None
    masks_path: str = None
    analysis_folder: str = None
    frame_interval: float = None
    pixel_interval_y: float = None
    pixel_interval_x: float = None
    number_of_cells: int = None
    number_of_frames: int = None
    normalized_peaks: float = None
    cells_four_peaks: int = None
    std_cutoff: float = None
    std_quantile: float = None
    random_below_std: int = None
    experimental_below_std: int = None
    cov_cutoff: float = None
    cov_quantile: float = None
    random_below_cov: int = None
    experimental_below_cov: int = None
    median_frequency_mHz: float = None
    active_cells_median_frequency_mHz: float = None
    median_peakwidth_s: float = None
    median_rise2080_s: float = None
    median_decay8020_s: float = None
    total_coinciding_peaks_1st_neighbour: int = None
    possible_coinciding_peaks_1st_neighbour: int = None
    random_1st_neighbour_zscore: float = None
    random_2nd_neighbour_zscore: float = None
    random_3rd_neighbour_zscore: float = None
    experiment_1st_neighbour_zscore: float = None
    experiment_2nd_neighbour_zscore: float = None
    experiment_3rd_neighbour_zscore: float = None
    pykrait_version: str = None
    timestamp: np.datetime64 = None

    def to_pandas(self):
        """Convert the dataclass to a pandas DataFrame."""
        return pd.DataFrame([asdict(self)])

    @classmethod
    def from_pandas(cls, df: pd.DataFrame) -> "AnalysisOutput":
        """Safely construct a dataclass from the first row of a pandas DataFrame."""
        if df.empty:
            raise ValueError("DataFrame is empty, cannot construct AnalysisOutput.")

        row = df.iloc[0].to_dict()
        init_args = {}

        for f in fields(cls):
            if f.name not in row:
                raise ValueError(f"Missing required field '{f.name}' in DataFrame.")

            val = row[f.name]

            # Handle missing / NaN
            if pd.isna(val):
                init_args[f.name] = None
                continue

            # Special case: np.datetime64
            if f.type == np.datetime64:
                init_args[f.name] = np.datetime64(val)
            else:
                try:
                    init_args[f.name] = f.type(val)  # cast to correct type
                except Exception:
                    raise TypeError(f"Cannot cast field '{f.name}' to {f.type}: {val}")

        return cls(**init_args)


class CalciumVideo:
    """
    Class to run the analysis pipeline on a single calcium video.
    """

    def __init__(self, video_path: str, params: AnalysisParameters):
        """
        _summary_

        :param video_path: path to the calcium video
        :type video_path: str
        :param cellpose_model_path: path to the cellpose model, defaults to "cpsam" to use the built-in cellpose model
        :type cellpose_model_path: str, optional
        """
        self.analysis_parameters = params
        self.analysis_output = AnalysisOutput(filepath=video_path)

    def run(self, skip_existing: bool = True) -> AnalysisOutput:
        """
        runs the analysis pipeline on the calcium video and returns the analysis output

        :param skip_existing: whether to skip files where the analysis has already been performed, defaults to True
        :type skip_existing: bool, optional
        :return: returns the AnalysisOutput dataclass, containing the results of the analysis
        :rtype: AnalysisOutput
        """

        # creating the analysis folder
        self.analysis_output = create_analysis_folder(self.analysis_output)

        filename = os.path.basename(self.analysis_output.filepath)
        filename_wo_ext = os.path.splitext(filename)[0]

        if (
            skip_existing
            and os.path.exists(
                os.path.join(
                    self.analysis_output.analysis_folder,
                    f"{filename_wo_ext}_cp_masks.ome.tif",
                )
            )
            and os.path.exists(
                os.path.join(
                    self.analysis_output.analysis_folder,
                    f"{filename_wo_ext}_raw_intensities.csv.zst",
                )
            )
        ):
            print(
                f"Analysis already exists for {self.analysis_output.filename}, loading existing results."
            )
            pd_output = pd.read_csv(
                os.path.join(
                    self.analysis_output.analysis_folder,
                    f"{filename_wo_ext}_analysis_output.csv",
                )
            )
            self.analysis_output = AnalysisOutput.from_pandas(pd_output)
            return self.analysis_output

        print(f"Running analysis on {self.analysis_output.filename}")
        # loading the timelapse data and analysing frame interval
        self.timelapse_data, self.analysis_output = load_timelapse(
            self.analysis_output, self.analysis_parameters
        )
        # creating the masks and saving them to the analysis folder
        self.tproj, self.rois, self.masks, self.analysis_output = create_masks(
            self.timelapse_data, self.analysis_output, self.analysis_parameters
        )
        # extracting the mean intensities from the timelapse data and saving them to the analysis folder
        self.mean_intensities, self.cell_properties, self.analysis_output = (
            create_mean_intensities(
                self.timelapse_data, self.masks, self.analysis_output
            )
        )

        # convert seconds and µm to frames and pixels
        neighbour_tolerance_pixels = int(
            self.analysis_parameters.neighbour_tolerance
            / self.analysis_output.pixel_interval_x
        )  # convert micrometers to pixels
        peak_min_width_frames = int(
            self.analysis_parameters.peak_min_width
            / self.analysis_output.frame_interval
        )  # convert seconds to frames
        peak_max_width_frames = int(
            self.analysis_parameters.peak_max_width
            / self.analysis_output.frame_interval
        )  # convert seconds to frames

        # checking if the parameters are valid
        if neighbour_tolerance_pixels < 1:
            warnings.warn(
                f"Neighbour tolerance of {neighbour_tolerance_pixels} pixels is too small, setting to 1 pixel."
            )
            neighbour_tolerance_pixels = 1
        if peak_min_width_frames < 1:
            warnings.warn(
                f"Peak minimum width of {peak_min_width_frames} frames is too small, setting to 1 frame."
            )
            peak_min_width_frames = 1
        if peak_max_width_frames <= peak_min_width_frames:
            warnings.warn(
                f"Peak maximum width of {peak_max_width_frames} frames is smaller or equal than peak minimum width of {peak_min_width_frames} seconds, setting to peak minimum width + 1."
            )
            peak_max_width_frames = peak_min_width_frames + 1

        self.detrended_timeseries = detrend_with_sinc_filter(
            signals=self.mean_intensities,
            cutoff_period=self.analysis_parameters.sinc_filter_window,
            sampling_interval=self.analysis_output.frame_interval,
        )

        self.peak_series, peak_properties_df, peak_frame_nonzero, self.analysis_output = do_peak_analysis(
            detrended_timeseries=self.detrended_timeseries,
            peak_min_width_frames=peak_min_width_frames,
            peak_max_width_frames=peak_max_width_frames,
            analysis_parameters=self.analysis_parameters,
            analysis_output=self.analysis_output,
        )

        self.analyis_output, self.experimental_stds, self.experimental_covs = (
            calculate_periodic_cells(
                self.peak_series, self.analysis_parameters, self.analysis_output
            )
        )

        self.adjacency_matrix, self.shortest_path_matrix = get_adjacency_matrix(
            self.masks, neighbour_tolerance=neighbour_tolerance_pixels
        )

        (
            self.analysis_output,
            self.true_synchronous_peaks_matrix,
            self.rand_synchronous_peaks_matrix,
        ) = calculate_synchronicity(
            self.shortest_path_matrix,
            self.peak_series,
            self.analysis_parameters,
            self.analysis_output,
        )
        # saving the parameters and output to the analysis folder
        self.analysis_output.pykrait_version = get_pykrait_version()
        self.analysis_output.timestamp = np.datetime64("now")
        save_analysis_results(
            self.tproj,
            self.masks,
            self.true_synchronous_peaks_matrix,
            self.analysis_output,
            self.analysis_parameters,
            self.detrended_timeseries,
            self.peak_series,
            self.mean_intensities,
            stds=self.experimental_stds,
            covs=self.experimental_covs,
            overwrite=True,
        )
        return self.analysis_output


class BatchExperiment:
    """
    Class to run a batch experiment on multiple calcium videos in a folder.
    """

    def __init__(
        self, folder: str, params: AnalysisParameters, extension: str = ".czi"
    ):
        """
        _summary_

        :param folder: folder that contains the calcium videos to be analyzed
        :type folder: str
        :param params: AnalysisParameters object containing the parameters for the analysis
        :type params: AnalysisParameters
        :param extension: File Extension of Calcium Videos, defaults to ".czi"
        :type extension: str, optional
        """
        files = get_files_from_folder(folder, extension=extension)
        self.experiments = [
            CalciumVideo(video_path=video_path, params=params) for video_path in files
        ]
        self.results = pd.DataFrame()

    def run(self):
        """
        runs the analysis pipeline for each video in the folder and stores the results in a pandas DataFrame
        """
        for experiment in self.experiments:
            result = experiment.run().to_pandas()
            self.results = pd.concat([self.results, result], ignore_index=True)


def create_analysis_folder(analysis_output: AnalysisOutput) -> AnalysisOutput:
    """
    creates an analysis subfolder in the parent directory of the video file

    :param analysis_output: AnalysisOutput object containing the filepath of the video file
    :type analysis_output: AnalysisOutput
    :return: returns the AnalysisOutput object with the analysis folder path set
    :rtype: AnalysisOutput
    """
    analysis_output.filename = analysis_output.filepath.split("/")[-1]
    # Create analysis folder in the parent directory of the video file
    parent_dir = os.path.dirname(analysis_output.filepath)
    filename_wo_ext = os.path.splitext(analysis_output.filename)[0]
    analysis_folder = os.path.join(parent_dir, f"Analysis_{filename_wo_ext}")
    os.makedirs(analysis_folder, exist_ok=True)
    analysis_output.analysis_folder = analysis_folder
    return analysis_output


def load_timelapse(
    analysis_output: AnalysisOutput, analysis_parameters: AnalysisParameters
) -> Tuple[da.Array, AnalysisOutput]:
    (
        timelapse_data,
        frame_interval,
        analysis_output.pixel_interval_y,
        analysis_output.pixel_interval_x,
    ) = load_timelapse_lazy(file_path=analysis_output.filepath)
    if (
        frame_interval is None and analysis_parameters.frame_interval is None
    ):  # nothing provided in metadata or parameters
        warnings.warn(
            "No frame interval found in metadata and no frame interval provided in parameters. Using default value of 1.0 seconds.",
            UserWarning,
        )
        analysis_output.frame_interval = 1.0
    elif (
        frame_interval is None and analysis_parameters.frame_interval is not None
    ):  # no metadata, but parameter provided
        analysis_output.frame_interval = analysis_parameters.frame_interval
    elif (
        frame_interval is not None and analysis_parameters.frame_interval is None
    ):  # metadata provided, but no parameter
        analysis_output.frame_interval = frame_interval
    elif round(frame_interval, 2) == round(
        analysis_parameters.frame_interval, 2
    ):  # both provided and match
        analysis_output.frame_interval = frame_interval
    elif round(frame_interval, 2) != round(analysis_parameters.frame_interval, 2):
        warnings.warn(
            f"Provided frame_interval ({analysis_parameters.frame_interval}) does not match inferred frame_interval ({frame_interval}) from metadata. Using provided value."
        )
        analysis_output.frame_interval = analysis_parameters.frame_interval
    else:
        warnings.warn(
            "Unexpected paramets in metadata frame interval {frame_interval} and provided frame interval {self.analyis_parameters.frame_interval}. Using default value of 1.0 seconds.",
            UserWarning,
        )
        analysis_output.frame_interval = 1.0
    return timelapse_data, analysis_output


def create_masks(
    timelapse_data: da.Array,
    analysis_output: AnalysisOutput,
    analysis_parameters: AnalysisParameters,
) -> Tuple[np.ndarray, np.ndarray, AnalysisOutput]:
    """
    creates a cellpose segmentation mask from the timelapse data and saves it to the analysis folder.

    Returns the tproj, the masks and the modified AnalysisOutput object with the mask path set.

    :param analysis_output: AnalysisOutput object to be modified with the mask path and other analysis results
    :type analysis_output: AnalysisOutput
    :param analysis_parameters: AnalysisParameters object containing the parameters for the analysis
    :type analysis_parameters: AnalysisParameters
    :return: returns the masks and the modified AnalysisOutput object with the mask path set
    :rtype: List[np.ndarray, np.ndarray, AnalysisOutput]
    """
    # perform the tproj
    print("Performing T Projection...")
    tproj = timelapse_projection(
        timelapse_data,
        method=analysis_parameters.tproj_type,
        normalize=analysis_parameters.CLAHE_normalize,
        verbose=True,
    )

    filename_wo_ext = os.path.splitext(analysis_output.filename)[0]
    analysis_output.tproj_path = os.path.join(
        analysis_output.analysis_folder, f"{filename_wo_ext}_tproj.ome.tif"
    )
    tifffile.imwrite(
        analysis_output.tproj_path,
        tproj.astype(np.uint16),
        metadata={"axes": "CYX"},
        compression="zlib",
    )

    # create cellpose segmentation
    print("Performing Cellpose Segmentation...")
    masks = create_cellpose_segmentation(
        tproj, cellpose_model_path=analysis_parameters.cellpose_model_path
    )
    masks_path = os.path.join(
        analysis_output.analysis_folder, f"{filename_wo_ext}_cp_masks.ome.tif"
    )
    analysis_output.masks_path = masks_path
    tifffile.imwrite(
        masks_path, masks.astype(np.uint16), metadata={"axes": "YX"}, compression="zlib"
    )

    rois = get_pixel_contour_from_label_img(masks)

    return tproj, rois, masks, analysis_output


def create_mean_intensities(
    timelapse_data: da.Array, masks: np.ndarray, analysis_output: AnalysisOutput
) -> Tuple[np.ndarray, tuple, AnalysisOutput]:
    """
    wrapper to extract mean intensities from the timelapse data and update the analysis output

    :param timelapse_data: lazily loaded timelapse data as a Dask array
    :type timelapse_data: da.Array
    :param analysis_output: object to be modified with the mean intensities and number of frames and cells
    :type analysis_output: AnalysisOutput
    :param masks: analysis
    :type masks: np.ndarray
    :return: returns a T x nroi
    :rtype: List[np.ndarray, tuple, AnalysisOutput]
    """
    print("Extracting Mean Intensities...")
    mean_intensities = extract_mean_intensities(timelapse_data, masks, verbose=True)
    analysis_output.number_of_frames, analysis_output.number_of_cells = (
        mean_intensities.shape
    )
    cell_properties = extract_cell_properties(masks)
    return mean_intensities, cell_properties, analysis_output

def do_peak_analysis(detrended_timeseries:np.ndarray, peak_min_width_frames:int, peak_max_width_frames:int, analysis_parameters: AnalysisParameters, analysis_output: AnalysisOutput) -> Tuple[np.ndarray, pd.DataFrame, np.ndarray, AnalysisOutput]:
    """
    Wrapper function for peak analysis. It detects peaks, computes the normalized_peaks, analyses the peak properties and frequency.

    :param detrended_timeseries: T x n_roi timeseries with already detrended signals
    :type detrended_timeseries: np.ndarray
    :param peak_min_width_frames: minimum peak width in frames
    :type peak_min_width_frames: int
    :param peak_max_width_frames: maximum peak width in frames
    :type peak_max_width_frames: int
    :param analysis_parameters: analysis parameter object
    :type analysis_parameters: AnalysisParameters
    :param analysis_output: analysis output object
    :type analysis_output: AnalysisOutput
    :return: returns the peak series (binary T x n_roi where 1 = peak), the peak properties dataframe, an array with the 70 frames around the peak for visualization, and the modified analysis output object
    :rtype: Tuple[np.ndarray, pd.DataFrame, np.ndarray, AnalysisOutput]
    """    
    # find peaks
    peak_series = find_peaks(
            peak_min_width=peak_min_width_frames,
            peak_max_width=peak_max_width_frames,
            peak_prominence=analysis_parameters.peak_prominence,
            peak_min_height=analysis_parameters.peak_min_height,
            detrended_timeseries=detrended_timeseries,
    )

    # compute normalized peaks
    peaks_per_100c_per_10_min = calculate_normalized_peaks(
            peak_series, analysis_output.frame_interval
    )
    analysis_output.normalized_peaks = round(peaks_per_100c_per_10_min, 2)

    # compute number of cells with at least 4 peaks
    analysis_output.cells_four_peaks = np.sum(
        np.sum(peak_series, axis=0) >= 4
    )

    # compute peak properties
    peak_properties_df, peak_frame_nonzero = create_peak_properties(peak_series, detrended_timeseries, analysis_output.frame_interval)
    analysis_output.median_peakwidth_s = round(peak_properties_df["FWHM"].median(), 2)
    analysis_output.median_rise2080_s = round(peak_properties_df["rise2080"].median(), 2)
    analysis_output.median_decay8020_s = round(peak_properties_df["decay8020"].median(), 2)

    # compute median frequency
    analysis_output.median_frequency_mHz, analysis_output.active_cells_median_frequency_mHz = find_median_frequency(peak_series, analysis_output.frame_interval)
    
    return peak_series, peak_properties_df, peak_frame_nonzero, analysis_output

def calculate_periodic_cells(
    peaks, analysis_parameters: AnalysisParameters, analysis_output: AnalysisOutput
) -> Tuple[int, int]:
    results, experimental_stds, experimental_covs = find_oscillating_rois(
        periodicity_method=analysis_parameters.periodicity_method,
        peak_series=peaks,
        std_threshold=analysis_parameters.std_threshold,
        cov_threshold=analysis_parameters.cov_threshold,
        frame_interval=analysis_output.frame_interval,
        n_iter=100,
    )

    analysis_output.std_cutoff = results["std_cutoff"]
    analysis_output.std_quantile = results["std_quantile"]
    analysis_output.cov_cutoff = results["cov_cutoff"]
    analysis_output.cov_quantile = results["cov_quantile"]
    analysis_output.random_below_std = results["random_below_std"]
    analysis_output.experimental_below_std = results["experimental_below_std"]
    analysis_output.random_below_cov = results["random_below_cov"]
    analysis_output.experimental_below_cov = results["experimental_below_cov"]

    return analysis_output, experimental_stds, experimental_covs


def calculate_synchronicity(
    shortest_path_matrix: np.ndarray,
    peak_series: np.ndarray,
    analysis_parameters: AnalysisParameters,
    analysis_output: AnalysisOutput,
) -> Tuple[AnalysisOutput, np.ndarray, np.ndarray]:
    """
    calculates the synchronicity z-scores for 1st, 2nd and 3rd degree neighbours and updates the analysis output

    :param shortest_path_matrix: ROI x ROI matrix with shortest path lengths between cells n and m
    :type shortest_path_matrix: np.ndarray
    :param peak_series: T x ROI binary matrix with 1s at calcium peak frames
    :type peak_series: np.ndarray
    :param time_window: time window in seconds within which peaks are considered synchronous
    :type time_window: float
    :param analysis_parameters: AnalysisParameters object containing the parameters for the analysis
    :type analysis_parameters: AnalysisParameters
    :param analysis_output: AnalysisOutput object to be modified with the synchronicity z-scores
    :type analysis_output: AnalysisOutput
    :return: returns the analysis output, the synchronous peaks matrix for the experiment with and one example random synchronous peaks matrix
    :rtype: Tuple[np.ndarray, np.ndarray]
    """
    # calculate synchronicity for 1st, 2nd and 3rd degree neighbours
    frame_window = int(analysis_parameters.time_window / analysis_output.frame_interval)
    for neighbour_degree in [3, 2, 1]:
        t_zscore, r_zscore, true_synchronous_peaks_matrix, rand_synchronous_peaks_matrix, potential_synchronous_peaks_matrix = (
            calculate_synchronicity_zscore(
                shortest_path_matrix,
                peak_series,
                neighbour_degree,
                frame_window * neighbour_degree,
                n_iter=100,
            )
        )
        if neighbour_degree == 1:
            analysis_output.total_coinciding_peaks_1st_neighbour = np.nansum(true_synchronous_peaks_matrix)
            analysis_output.possible_coinciding_peaks_1st_neighbour = np.nansum(potential_synchronous_peaks_matrix)
            analysis_output.experiment_1st_neighbour_zscore = round(t_zscore, 2)
            analysis_output.random_1st_neighbour_zscore = round(r_zscore, 2)
        elif neighbour_degree == 2:
            analysis_output.experiment_2nd_neighbour_zscore = round(t_zscore, 2)
            analysis_output.random_2nd_neighbour_zscore = round(r_zscore, 2)
        elif neighbour_degree == 3:
            analysis_output.experiment_3rd_neighbour_zscore = round(t_zscore, 2)
            analysis_output.random_3rd_neighbour_zscore = round(r_zscore, 2)

    return analysis_output, true_synchronous_peaks_matrix, rand_synchronous_peaks_matrix

def save_params(analysis_output:AnalysisOutput, analysis_params:AnalysisParameters, overwrite:bool=False):
    filename = os.path.basename(analysis_output.filepath)
    filename_wo_ext = os.path.splitext(filename)[0]
    parent_dir = os.path.dirname(analysis_output.filepath)
    analysis_folder = os.path.join(parent_dir, f"Analysis_{filename_wo_ext}")
    os.makedirs(analysis_folder, exist_ok=True)

    output_file = os.path.join(
        analysis_folder, f"{filename_wo_ext}_analysis_output.csv"
    )
    param_file = os.path.join(
        analysis_folder, f"{filename_wo_ext}_analysis_parameters.csv"
    )

    if not overwrite:
        for f in [output_file, param_file]:
            if os.path.exists(f):
                raise FileExistsError(
                    f"{f} already exists. Enable 'overwrite' to replace."
                )
    analysis_output.to_pandas().to_csv(output_file, index=False)
    analysis_params.to_pandas().to_csv(param_file, index=False)

def save_analysis_results(
    tproj: np.ndarray,
    masks: np.ndarray,
    synchronous_peaks_matrix: np.ndarray,
    analysis_output: AnalysisOutput,
    analysis_params: AnalysisParameters,
    detrended_intensities: np.ndarray,
    peaks: np.ndarray,
    intensities: np.ndarray,
    stds: np.ndarray,
    covs: np.ndarray,
    overwrite: bool = False,
):
    filename = os.path.basename(analysis_output.filepath)
    filename_wo_ext = os.path.splitext(filename)[0]
    parent_dir = os.path.dirname(analysis_output.filepath)
    analysis_folder = os.path.join(parent_dir, f"Analysis_{filename_wo_ext}")
    os.makedirs(analysis_folder, exist_ok=True)

    output_file = os.path.join(
        analysis_folder, f"{filename_wo_ext}_analysis_output.csv"
    )
    param_file = os.path.join(
        analysis_folder, f"{filename_wo_ext}_analysis_parameters.csv"
    )

    if not overwrite:
        for f in [output_file, param_file]:
            if os.path.exists(f):
                raise FileExistsError(
                    f"{f} already exists. Enable 'overwrite' to replace."
                )

    # Save output
    analysis_output.pykrait_version = get_pykrait_version()
    analysis_output.timestamp = np.datetime64("now")

    analysis_output.to_pandas().to_csv(output_file, index=False)
    analysis_params.to_pandas().to_csv(param_file, index=False)

    # Save arrays
    stds_covs = np.column_stack((stds, covs))
    save_NroisxF(
        stds_covs,
        os.path.join(analysis_folder, f"{filename_wo_ext}_stds.csv.zst"),
        header=["STD", "CoV"],
    )
    save_Txnrois(
        peaks,
        analysis_output.frame_interval,
        os.path.join(analysis_folder, f"{filename_wo_ext}_peaks.csv.zst"),
    )
    save_Txnrois(
        detrended_intensities,
        analysis_output.frame_interval,
        os.path.join(
            analysis_folder, f"{filename_wo_ext}_detrended_intensities.csv.zst"
        ),
    )
    save_Txnrois(
        intensities,
        analysis_output.frame_interval,
        os.path.join(analysis_folder, f"{filename_wo_ext}_raw_intensities.csv.zst"),
    )

    fig = create_synchronicity_image(
        tproj=tproj,
        masks=masks,
        synchronous_peaks_matrix=synchronous_peaks_matrix,
        savepath=os.path.join(analysis_folder, f"{filename_wo_ext}_synchronicity_on_tproj.svg")
    )
    plt.close(fig)
    fig = create_heatmap_image(
        masks=masks,
        peak_series=peaks,
        savepath=os.path.join(analysis_folder, f"{filename_wo_ext}_activity_heatmap.svg")
    )
    plt.close(fig)
