from PySide6.QtCore import QObject, Signal, Slot
import traceback
import numpy as np
from pykrait.io.images import read_label_image, get_pixel_contour_from_label_img
from pykrait.io.files import read_Txnrois
from pykrait.preprocessing.segmentation import timelapse_projection
import tifffile
from pykrait.preprocessing.timeseries_extraction import extract_mean_intensities, get_adjacency_matrix
from pykrait.trace_analysis.filtering import detrend_with_sinc_filter
import os

from pykrait.pipeline.pipeline import (
    AnalysisParameters,
    AnalysisOutput,
    create_analysis_folder,
    load_timelapse,
    create_masks,
    do_peak_analysis,
    calculate_periodic_cells,
    calculate_synchronicity,
    save_analysis_results,
    save_params
)

class ExtractIntensitiesWorker(QObject):
    """
    Worker for extracting mean intensities from a timelapse dataset, using either Cellpose segmentation or a label image.
    """

    progress_changed = Signal(int, str)  # progress percent, status message
    finished = Signal(dict)  # analysis results
    error = Signal(str)  # error message

    def __init__(
        self,
        analysis_params: AnalysisParameters,
        output_params: AnalysisOutput,
        mode: str,
        mean_intensities_path: str = None,
    ):
        super().__init__()
        self.analysis_parameters = analysis_params
        self.analysis_output = output_params
        self.mode = mode
        self.mean_intensities_path = mean_intensities_path

    @Slot()
    def run(self):
        try:
            self.analysis_output = create_analysis_folder(self.analysis_output)
            print(f"Running analysis on {self.analysis_output.filename}")
            # loading the timelapse data and analysing frame interval
            self.timelapse_data, self.analysis_output = load_timelapse(
                self.analysis_output, self.analysis_parameters
            )

            if self.mode == "cellpose":
                # perform the tproj
                self.progress_changed.emit(
                    10, "Performing T Projection and Cellpose Segmentation..."
                )
                # creating the masks and saving them to the analysis folder
                _, _, self.masks, self.analysis_output = create_masks(
                    self.timelapse_data, self.analysis_output, self.analysis_parameters
                )
                # extracts the mean intensities of the masks
                self.progress_changed.emit(60, "Extracting intensities...")
                mean_intensities = extract_mean_intensities(
                    self.timelapse_data, self.masks
                )
            elif self.mode == "label_image":
                if self.analysis_output.tproj_path is None:
                    print("Performing T Projection...")
                    tproj = timelapse_projection(
                        self.timelapse_data,
                        method="std",
                        normalize=True,
                        verbose=True,
                    )

                    filename_wo_ext = os.path.splitext(self.analysis_output.filename)[0]
                    self.analysis_output.tproj_path = os.path.join(
                        self.analysis_output.analysis_folder, f"{filename_wo_ext}_tproj.ome.tif"
                    )
                    tifffile.imwrite(
                        self.analysis_output.tproj_path,
                        tproj.astype(np.uint16),
                        metadata={"axes": "CYX"},
                        compression="zlib",
                    )
                self.progress_changed.emit(20, "Loading label image...")
                self.masks = read_label_image(self.analysis_output.masks_path)
                # extracts the mean intensities of the masks
                self.progress_changed.emit(60, "Extracting intensities...")
                mean_intensities = extract_mean_intensities(
                    self.timelapse_data, self.masks
                )
            elif self.mode == "csv":
                self.progress_changed.emit(20, "Loading label image...")
                self.masks = read_label_image(self.analysis_output.masks_path)
                self.progress_changed.emit(60, "Reading intensities...")
                mean_intensities = read_Txnrois(
                    self.mean_intensities_path,
                    n_frames=self.timelapse_data.shape[0],
                    n_rois=self.masks.max(),
                )
            else:
                raise ValueError("Unknown mode.")

            (
                self.analysis_output.number_of_frames,
                self.analysis_output.number_of_cells,
            ) = mean_intensities.shape

            # All done
            self.progress_changed.emit(90, "Calculating ROI boundaries...")
            rois = get_pixel_contour_from_label_img(
                self.masks, orig_shape=self.masks.shape, target_shape=(512, 512)
            )

            self.progress_changed.emit(100, "Done.")

            results = {
                "frames": self.timelapse_data,
                "analysis_output": self.analysis_output,
                "analysis_parameters": self.analysis_parameters,
                "masks": self.masks,
                "rois": rois,
                "mean_intensities": mean_intensities,
            }
            save_params(self.analysis_output, self.analysis_parameters, overwrite=True)
            self.finished.emit(results)

        except Exception as e:
            tb = traceback.format_exc()
            print(f"Error during analysis: {e}\n{tb}")
            self.error.emit(str(e))


class DetrendWorker(QObject):
    """
    _summary_

    :param QObject: _description_
    :type QObject: _type_
    """

    finished = Signal(np.ndarray)
    error = Signal(Exception)

    def __init__(self, intensities, sinc_window, frame_interval):
        super().__init__()
        self.intensities = intensities
        self.sinc_window = sinc_window
        self.frame_interval = frame_interval

    def run(self):
        try:
            # Call your actual function here
            detrended = detrend_with_sinc_filter(
                signals=self.intensities,
                cutoff_period=self.sinc_window,
                sampling_interval=self.frame_interval,
            )
            self.finished.emit(detrended)
        except Exception as e:
            self.error.emit(e)


class PeakDetectionWorker(QObject):
    """
    Worker for detecting peaks in detrended traces, wraps the `find_peaks` function.
    """

    finished = Signal(np.ndarray)
    error = Signal(Exception)

    def __init__(self, detrended_traces, min_width, max_width, analysis_params, analysis_output):
        super().__init__()
        self.traces = detrended_traces
        self.min_width = min_width
        self.max_width = max_width
        self.analysis_params = analysis_params
        self.analysis_output = analysis_output

    def run(self):
        try:
            peak_series, peak_properties_df, peak_frame_nonzero, analysis_output = do_peak_analysis(self.traces, self.min_width, self.max_width, self.analysis_params, self.analysis_output)
            result = [peak_series, analysis_output]
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(e)


class PeriodicCellWorker(QObject):
    """
    Worker for finding oscillating ROIs in the peak series, wraps the `find_oscillating_rois` function.
    """

    finished = Signal(AnalysisOutput, np.ndarray, np.ndarray)
    error = Signal(Exception)

    def __init__(self, peaks: np.ndarray, analysis_params, analysis_output):
        super().__init__()
        self.peaks = peaks
        self.analysis_output = analysis_output
        self.analysis_params = analysis_params

    def run(self):
        try:
            analysis_output, stds, covs = calculate_periodic_cells(
                self.peaks, self.analysis_params, self.analysis_output
            )
            self.finished.emit(analysis_output, stds, covs)
        except Exception as e:
            self.error.emit(e)


class AdjacencyMatrixWorker(QObject):
    """
    Worker for calculating the adjacency matrix from the masks, wraps the `get_adjacency_matrix` function.
    """

    finished = Signal(np.ndarray, np.ndarray)
    error = Signal(Exception)

    def __init__(self, masks: np.ndarray, neighbour_tolerance_pixels: int = 1):
        super().__init__()
        self.masks = masks
        self.neighbour_tolerance_pixels = neighbour_tolerance_pixels

    def run(self):
        try:
            adjacency_matrix, shortest_path_matrix = get_adjacency_matrix(
                self.masks, neighbour_tolerance=self.neighbour_tolerance_pixels
            )
            self.finished.emit(adjacency_matrix, shortest_path_matrix)
        except Exception as e:
            self.error.emit(e)


class SynchronicityWorker(QObject):
    """
    Worker for calculating the synchronicity matrix from the detrended intensities, wraps the `calculate_synchronicity_matrix` function.
    """

    finished = Signal(np.ndarray)
    error = Signal(Exception)

    def __init__(self, analysis_output:AnalysisOutput, analysis_parameters:AnalysisParameters, peak_series: np.ndarray, shortest_path_matrix: np.ndarray):
        super().__init__()
        self.peak_series = peak_series
        self.shortest_path_matrix = shortest_path_matrix
        self.analysis_output = analysis_output
        self.analysis_parameters = analysis_parameters

    def run(self):
        try:
            results = calculate_synchronicity(
                self.shortest_path_matrix,
                self.peak_series,
                self.analysis_parameters,
                self.analysis_output
            )
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(e)


class AnalysisSaveWorker(QObject):
    """
    Worker for saving the analysis results, wraps the `save_analysis_results` function.
    """

    finished = Signal(str)  # emit output file path or summary message
    error = Signal(Exception)

    def __init__(
        self,
        tproj:np.ndarray,
        masks:np.ndarray,
        synchronous_peaks_matrix:np.ndarray,
        analysis_output,
        analysis_params,
        peaks: np.ndarray,
        detrended_intensities: np.ndarray,
        intensities: np.ndarray,
        stds: np.ndarray = None,
        covs: np.ndarray = None,
        overwrite: bool = False,
    ):
        super().__init__()
        self.tproj = tproj
        self.masks = masks
        self.synchronous_peaks_matrix = synchronous_peaks_matrix
        self.analysis_output = analysis_output
        self.analysis_params = analysis_params
        self.peaks = peaks
        self.detrended_intensities = detrended_intensities
        self.intensities = intensities
        self.overwrite = overwrite
        self.stds = stds
        self.covs = covs

    def run(self):
        try:
            save_analysis_results(
                tproj=self.tproj,
                masks=self.masks,
                synchronous_peaks_matrix=self.synchronous_peaks_matrix,
                analysis_output=self.analysis_output,
                analysis_params=self.analysis_params,
                detrended_intensities=self.detrended_intensities,
                peaks=self.peaks,
                intensities=self.intensities,
                stds=self.stds,
                covs=self.covs,
                overwrite=self.overwrite,
            )
            self.finished.emit(f"Saved to {self.analysis_output.analysis_folder}")

        except Exception as e:
            self.error.emit(e)
