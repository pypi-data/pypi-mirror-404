import numpy as np
import traceback
import dask.array as da
from matplotlib import cm
from pathlib import Path
from typing import List
import warnings

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QLabel,
    QFormLayout,
    QPushButton,
    QSplitter,
    QSlider,
    QDoubleSpinBox,
    QGroupBox,
    QCheckBox,
    QRadioButton,
    QButtonGroup,
    QLineEdit,
    QScrollArea
)
from PySide6.QtCore import Qt, QPointF, Signal, QThread
from PySide6.QtGui import (
    QImage,
    QPixmap,
    QPen,
    QPolygonF,
    QAction,
    QDoubleValidator,
    QBrush,
)
from PySide6.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsPixmapItem,
    QGraphicsPolygonItem,
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from pykrait.io.files import get_pykrait_version, concat_analysis_files
from pykrait.io.images import read_image
from pykrait.pipeline.pipeline import AnalysisParameters, AnalysisOutput
from pykrait.gui.async_workers import (
    DetrendWorker,
    PeakDetectionWorker,
    PeriodicCellWorker,
    AnalysisSaveWorker,
    SynchronicityWorker,
    AdjacencyMatrixWorker
)
from pykrait.gui.custom_widgets import ToggleSwitch, CollapsibleBox


class ImageDisplay(QGraphicsView):
    roiSelected = Signal(int)

    def __init__(self, parent=None, target_shape=(512, 512)):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.image_item = QGraphicsPixmapItem()
        self.scene.addItem(self.image_item)
        self.roi_items = []
        self.rois = []
        self.target_shape = target_shape  # target shape for downsampling
        self.selected_roi = None  # to track the active ROI
        self.last_sinc_window = (
            None  # to track the last used sinc window for detrending
        )
        self.intensity_clip_min = None
        self.intensity_clip_max = None

    def set_rois(self, rois):
        # Clear old ROIs
        for item in self.roi_items:
            self.scene.removeItem(item)
        self.roi_items.clear()
        self.rois = rois

        for i, poly_pts in enumerate(rois):
            polygon = QPolygonF([QPointF(x, y) for x, y in poly_pts])
            pen = QPen(Qt.white)  # White color
            pen.setWidth(1)  # Line width
            pen.setStyle(Qt.DashLine)  # Dashed line
            roi_item = QGraphicsPolygonItem(polygon)
            roi_item.setPen(pen)
            roi_item.setBrush(Qt.NoBrush)  # No fill
            roi_item.setZValue(1)
            roi_item.setData(0, i)
            self.scene.addItem(roi_item)
            self.roi_items.append(roi_item)
        self.highlight_selected_roi()

    def highlight_selected_roi(self):
        for i, roi_item in enumerate(self.roi_items):
            if i == self.selected_roi:
                pen = QPen(Qt.red)
                pen.setWidth(3)
                pen.setStyle(Qt.SolidLine)
                roi_item.setZValue(100)  # Highest level for selected
            else:
                pen = QPen(Qt.white)
                pen.setWidth(1)
                pen.setStyle(Qt.DashLine)
                roi_item.setZValue(1)  # Normal level for unselected
            roi_item.setPen(pen)
            roi_item.setBrush(Qt.NoBrush)

    def draw_roi_centers(self, indices: List[int], radius: int = 5) -> None:
        """
        draws red dots at the centers of the specified ROIs.

        :param indices: list of indices of ROIs to mark
        :type indices: List[int]
        :param radius: radius of the highlight, defaults to 3
        :type radius: int, optional
        """
        # Clear old center markers first (if needed)
        self.clear_roi_centers()

        self.center_items = []

        for i in indices:
            if i < 0 or i >= len(self.rois):
                continue  # Skip invalid indices

            poly_pts = self.rois[i]
            if not poly_pts:
                continue

            # Compute centroid
            xs, ys = zip(*poly_pts)
            cx = sum(xs) / len(xs)
            cy = sum(ys) / len(ys)

            # Create red dot (ellipse)
            dot = self.scene.addEllipse(
                cx - radius,
                cy - radius,
                2 * radius,
                2 * radius,
                QPen(Qt.green),
                QBrush(Qt.green),
            )
            dot.setZValue(2)  # Above polygons
            self.center_items.append(dot)

    def clear_roi_centers(self):
        if hasattr(self, "center_items"):
            for item in self.center_items:
                self.scene.removeItem(item)
            self.center_items.clear()

    def draw_roi_connections(self, shortest_path_matrix) -> None:
        """
        Draw lines between ROI centers for all connected pairs
        according to shortest_path_matrix.
        """
        # Clear old lines
        self.clear_roi_connections()

        # Compute all ROI centroids
        centers = {}
        for i, poly_pts in enumerate(self.rois):
            if not poly_pts:
                continue
            xs, ys = zip(*poly_pts)
            centers[i] = (sum(xs) / len(xs), sum(ys) / len(ys))

        self.connection_items = []
        n = len(self.rois)
        for i in range(len(self.rois)):
            for j in range(i + 1, n):  # only upper triangle, avoid self-loops
                dist = shortest_path_matrix[i][j]
                if dist == 1:
                    if i in centers and j in centers:
                        x1, y1 = centers[i]
                        x2, y2 = centers[j]
                        line = self.scene.addLine(x1, y1, x2, y2, QPen(Qt.blue, 2))
                        line.setZValue(1)  # behind the dots
                        self.connection_items.append(line)

    def clear_roi_connections(self):
        if hasattr(self, "connection_items"):
            for item in self.connection_items:
                self.scene.removeItem(item)
            self.connection_items.clear()

    def mousePressEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        for idx, roi_item in enumerate(self.roi_items):
            if roi_item.contains(scene_pos):
                self.selected_roi = idx
                self.highlight_selected_roi()
                self.roiSelected.emit(idx)  # <---- emit the signal
                break
        else:
            self.selected_roi = None
            self.highlight_selected_roi()
        super().mousePressEvent(event)

    def display_dask_frame(self, frame: da.Array, cmap="magma"):
        """
        displays a single frame from a dask array in the QGraphicsView.
        Uses coarsening to downsample the frame, and normalizes the brightness consistently.

        :param frame: dask array representing a single frame of the timelapse
        :type frame: da.Array
        :param cmap: colormap to display in, defaults to 'magma'
        :type cmap: str, optional
        :raises ValueError: raises ValueError if the input frame is not a 2D array
        :raises ValueError: raises ValueError if the original frame is too small for the target
        """
        if frame.ndim != 2:
            raise ValueError("Input frame must be a 2D array")
        h, w = frame.shape

        # Compute coarsening factors
        fh, fw = h // self.target_shape[0], w // self.target_shape[1]
        if fh < 1 or fw < 1:
            fh = 1
            fw = 1
            self.target_shape = frame.shape
            warnings.warn(f"Original frame too small for target {self.target_shape}, using original shape", UserWarning)

        # Downsample using mean pooling
        frame_ds = da.coarsen(np.mean, frame, {0: fh, 1: fw}, trim_excess=True)
        img = frame_ds.compute()

        # Normalize the image for optimized display
        if self.intensity_clip_min is None:
            self.intensity_clip_min = np.percentile(
                img, 1
            )  # 1st percentile for better contrast
        if self.intensity_clip_max is None:
            self.intensity_clip_max = np.percentile(img, 99)
        # Avoid divide-by-zero
        if self.intensity_clip_max - self.intensity_clip_min < 1e-6:
            norm = np.zeros_like(img, dtype=float)
        else:
            norm = np.clip(
                (img - self.intensity_clip_min)
                / (self.intensity_clip_max - self.intensity_clip_min),
                0,
                1,
            )

        # Apply colormap
        img_rgb = (cm.get_cmap(cmap)(norm)[..., :3] * 255).astype(np.uint8)

        # Convert to QImage and display
        h_ds, w_ds, _ = img_rgb.shape
        qimg = QImage(img_rgb.data, w_ds, h_ds, 3 * w_ds, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qimg)
        self.image_item.setPixmap(pix)
        self.fitInView(self.image_item, Qt.KeepAspectRatio)


class MainWindow(QMainWindow):
    def __init__(
        self,
        frames: da.Array,
        mask: np.ndarray,
        mean_intensities: np.ndarray,
        rois: list,
        analysis_output: AnalysisOutput,
        analysis_params: AnalysisParameters,
        app_controller=None,
    ):
        super().__init__()
        self.app_controller = app_controller
        self.frames = frames
        self.masks = mask
        self.rois = rois
        self.intensities = mean_intensities
        self.analysis_output = analysis_output
        self.analysis_params = analysis_params
        self.setWindowTitle(
            f"{self.analysis_output.filename}; pyKrait {get_pykrait_version()}"
        )

        self.selected_roi = 0  # Default to first ROI
        self.current_frame = 0
        self.show_detrended: bool = False
        self.detrended_intensities = None
        self.peaks = None
        self.tproj = read_image(self.analysis_output.tproj_path)
        # menu bar
        self._create_menu_bar()
        # Central widget and main layout
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        # -------- LEFT PANEL --------
        left_panel = QVBoxLayout()

        # Image display
        self.image_display = ImageDisplay()
        self.image_display.setMinimumSize(400, 400)
        left_panel.addWidget(self.image_display)

        # Video slider
        self.frame_slider = QSlider(Qt.Horizontal)
        self.frame_slider.setMinimum(0)
        self.frame_slider.setMaximum(self.frames.shape[0] - 1)  # Use -1 for index
        left_panel.addWidget(self.frame_slider)

        # Intensity plot
        self.fig = Figure(figsize=(4, 2))
        self.canvas = FigureCanvas(self.fig)
        left_panel.addWidget(self.canvas)
        self.ax = self.fig.add_subplot(111)

        # -------- RIGHT PANEL --------
        right_panel = QVBoxLayout()

        #region Trace Detrending Group
        trace_group = CollapsibleBox("Trace Detrending")

        # Container widget for the form layout
        form_container = QWidget()
        trace_layout = QFormLayout(form_container)
        trace_layout.setContentsMargins(0, 0, 0, 0)
        trace_layout.setSpacing(5)

        # Sinc filter window
        self.sinc_filter_spin = QDoubleSpinBox()
        self.sinc_filter_spin.setDecimals(2)
        sinc_max = self.frames.shape[0] * self.analysis_output.frame_interval
        self.sinc_filter_spin.setMinimum(1)
        self.sinc_filter_spin.setMaximum(sinc_max)
        self.sinc_filter_spin.setValue(
            int(self.frames.shape[0] * self.analysis_output.frame_interval / 2)
        )
        trace_layout.addRow("Sinc Filter Window [s]:", self.sinc_filter_spin)

        # Frame interval auto-detected
        self.frame_interval_value = QLabel(f"{self.analysis_output.frame_interval:.2f}")
        trace_layout.addRow("Frame Interval Auto-Detected [s]:", self.frame_interval_value)

        # Frame interval spin
        self.frame_interval_spin = QDoubleSpinBox()
        self.frame_interval_spin.setDecimals(2)
        self.frame_interval_spin.setMinimum(0.01)
        self.frame_interval_spin.setMaximum(1000)
        self.frame_interval_spin.setValue(self.analysis_output.frame_interval)
        trace_layout.addRow("Frame Interval [s]:", self.frame_interval_spin)

        # Video duration
        self.video_duration_value = QLabel(
            f"{self.analysis_output.frame_interval * self.intensities.shape[0]:.2f}"
        )
        trace_layout.addRow("Video Duration [s]:", self.video_duration_value)

        # Buttons in a horizontal layout
        trace_btn_layout = QHBoxLayout()
        self.show_detrended_btn = QPushButton("Show Detrended Traces")
        self.show_raw_btn = QPushButton("Show Raw Traces")
        trace_btn_layout.addWidget(self.show_detrended_btn)
        trace_btn_layout.addWidget(self.show_raw_btn)

        btn_container = QWidget()
        btn_container.setLayout(trace_btn_layout)
        trace_layout.addRow(btn_container)

        trace_group.add_widget(form_container)
        right_panel.addWidget(trace_group)
        #endregion

        #region Peak Identification Group
        peak_group = CollapsibleBox("Peak Identification")

        # Container widget for the QFormLayout
        form_container = QWidget()
        peak_layout = QFormLayout(form_container)
        peak_layout.setContentsMargins(0, 0, 0, 0)
        peak_layout.setSpacing(5)

        # Peak Min Width
        self.peak_min_width_spin = QDoubleSpinBox()
        self.peak_min_width_spin.setDecimals(2)
        self.peak_min_width_spin.setMinimum(1)
        self.peak_min_width_spin.setMaximum(1000)
        self.peak_min_width_spin.setValue(1.0)
        peak_layout.addRow("Peak Min Width [s]:", self.peak_min_width_spin)

        # Peak Max Width
        self.peak_max_width_spin = QDoubleSpinBox()
        self.peak_max_width_spin.setDecimals(2)
        self.peak_max_width_spin.setMinimum(0)
        self.peak_max_width_spin.setMaximum(1000)
        self.peak_max_width_spin.setValue(80.0)
        peak_layout.addRow("Peak Max Width [s]:", self.peak_max_width_spin)

        # Peak Min Height
        self.peak_min_height_spin = QDoubleSpinBox()
        self.peak_min_height_spin.setDecimals(0)
        self.peak_min_height_spin.setMinimum(0)
        self.peak_min_height_spin.setMaximum(65535)
        self.peak_min_height_spin.setValue(800)
        peak_layout.addRow("Peak Min Height [au]:", self.peak_min_height_spin)

        # Peak Prominence
        self.peak_prominence_spin = QDoubleSpinBox()
        self.peak_prominence_spin.setDecimals(0)
        self.peak_prominence_spin.setMinimum(0)
        self.peak_prominence_spin.setMaximum(65535)
        self.peak_prominence_spin.setValue(1500)
        peak_layout.addRow("Peak Prominence [au]:", self.peak_prominence_spin)

        # Find Peaks Button
        self.find_peaks_btn = QPushButton("Find Peaks")
        peak_layout.addRow(self.find_peaks_btn)

        # Labels
        self.norm_peak_label = QLabel("")
        self.fourpeak_label = QLabel("")
        self.frequency_label = QLabel("")
        peak_layout.addRow("normalized peaks:", self.norm_peak_label)
        peak_layout.addRow("% of cells w/ >= 4 peaks:", self.fourpeak_label)
        peak_layout.addRow("median Frequency mHz:", self.frequency_label)

        # Add the form container to the collapsible box
        peak_group.add_widget(form_container)
        right_panel.addWidget(peak_group)
        #endregion

        #region Periodicity
        periodicity_group = CollapsibleBox("Periodic Cells")

        # Container widget for the QFormLayout
        form_container = QWidget()
        periodicity_layout = QFormLayout(form_container)
        periodicity_layout.setContentsMargins(0, 0, 0, 0)
        periodicity_layout.setSpacing(5)

        # Row 0: mutually exclusive method buttons
        self.rb_periodicity_cutoff = QRadioButton("Use cut-off")
        self.rb_periodicity_quantile = QRadioButton("Use quantile")
        self.rb_periodicity_cutoff.setChecked(True)

        self.periodicity_method_group = QButtonGroup(self)
        self.periodicity_method_group.addButton(self.rb_periodicity_cutoff)
        self.periodicity_method_group.addButton(self.rb_periodicity_quantile)

        _method_row = QWidget()
        _method_row_layout = QHBoxLayout(_method_row)
        _method_row_layout.setContentsMargins(0, 0, 0, 0)
        _method_row_layout.addWidget(self.rb_periodicity_cutoff)
        _method_row_layout.addWidget(self.rb_periodicity_quantile)
        _method_row_layout.addStretch(1)
        periodicity_layout.addRow(_method_row)

        # Row 1: STD threshold input + labels
        self.periodicity_threshold_std_LineEdit = QLineEdit()
        self.periodicity_threshold_std_LineEdit.setMinimumWidth(40)
        self.periodicity_threshold_std_LineEdit.setValidator(QDoubleValidator(0.0, 1000.0, 2, self))
        self.periodicity_threshold_std_LineEdit.setText("15.0")

        self.std_cutoff_value_label = QLabel("cutoff: —s")
        self.std_quantile_value_label = QLabel("quantile: —%")

        _std_row = QWidget()
        _std_row_layout = QHBoxLayout(_std_row)
        _std_row_layout.setContentsMargins(0, 0, 0, 0)
        _std_row_layout.addWidget(self.periodicity_threshold_std_LineEdit)
        _std_row_layout.addSpacing(12)
        _std_row_layout.addWidget(self.std_cutoff_value_label)
        _std_row_layout.addSpacing(12)
        _std_row_layout.addWidget(self.std_quantile_value_label)
        _std_row_layout.addStretch(1)
        periodicity_layout.addRow("STD threshold:", _std_row)

        # Row 2: CoV threshold input + labels
        self.periodicity_threshold_cov_LineEdit = QLineEdit()
        self.periodicity_threshold_cov_LineEdit.setMinimumWidth(40)
        self.periodicity_threshold_cov_LineEdit.setValidator(QDoubleValidator(0.0, 1.0, 2, self))
        self.periodicity_threshold_cov_LineEdit.setText("0.20")

        self.cov_cutoff_value_label = QLabel("cutoff: —")
        self.cov_quantile_value_label = QLabel("quantile: —%")

        _cov_row = QWidget()
        _cov_row_layout = QHBoxLayout(_cov_row)
        _cov_row_layout.setContentsMargins(0, 0, 0, 0)
        _cov_row_layout.addWidget(self.periodicity_threshold_cov_LineEdit)
        _cov_row_layout.addSpacing(12)
        _cov_row_layout.addWidget(self.cov_cutoff_value_label)
        _cov_row_layout.addSpacing(12)
        _cov_row_layout.addWidget(self.cov_quantile_value_label)
        _cov_row_layout.addStretch(1)
        periodicity_layout.addRow("CoV threshold:", _cov_row)

        # Row 3: action button + toggle + display checkbox
        _periodic_btn_row = QWidget()
        _periodic_btn_row_layout = QHBoxLayout(_periodic_btn_row)
        _periodic_btn_row_layout.setContentsMargins(0, 0, 0, 0)

        self.periodicity_button = QPushButton("Find Periodic Cells")
        self.periodicity_toggle = ToggleSwitch(label_on="CoV", label_off="STD")
        self.periodic_display_checkbox = QCheckBox("Show Cells")
        self.periodic_display_checkbox.setDisabled(True)

        _periodic_btn_row_layout.addWidget(self.periodicity_button)
        _periodic_btn_row_layout.addWidget(self.periodicity_toggle)
        _periodic_btn_row_layout.addWidget(self.periodic_display_checkbox)
        _periodic_btn_row_layout.addStretch(1)

        periodicity_layout.addRow(_periodic_btn_row)

        # Row 4: labels for % periodic cells (STD / CoV)
        self.std_periodic_per_active_label = QLabel("Cells below STD cutoff: — %")
        self.cov_periodic_per_active_label = QLabel("Cells below CoV cutoff: — %")

        _pct_row = QWidget()
        _pct_row_layout = QHBoxLayout(_pct_row)
        _pct_row_layout.setContentsMargins(0, 0, 0, 0)
        _pct_row_layout.addWidget(self.std_periodic_per_active_label)
        _pct_row_layout.addSpacing(24)
        _pct_row_layout.addWidget(self.cov_periodic_per_active_label)
        _pct_row_layout.addStretch(1)

        periodicity_layout.addRow(_pct_row)

        # Add the form container to the collapsible box
        periodicity_group.add_widget(form_container)

        # Add the collapsible box to the panel
        right_panel.addWidget(periodicity_group)
        #endregion 

        #region Synchronicity
        self.synch_group = CollapsibleBox("Synchronicity Analysis")

        # Container widget for the QFormLayout
        form_container = QWidget()
        synch_layout = QFormLayout(form_container)
        synch_layout.setContentsMargins(0, 0, 0, 0)
        synch_layout.setSpacing(5)

        # Neighbour Distance input
        self.neighbour_distance_spin = QDoubleSpinBox()
        self.neighbour_distance_spin.setDecimals(2)
        self.neighbour_distance_spin.setMinimum(0)
        self.neighbour_distance_spin.setMaximum(100)
        self.neighbour_distance_spin.setValue(10.0)  # default value
        synch_layout.addRow("Neighbour Distance [µm]:", self.neighbour_distance_spin)

        # Time Window input
        self.time_window_spin = QDoubleSpinBox()
        self.time_window_spin.setDecimals(2)
        self.time_window_spin.setMinimum(0)
        self.time_window_spin.setMaximum(100)
        self.time_window_spin.setValue(10.0)  # default value
        synch_layout.addRow("Time Window [s]:", self.time_window_spin)

        # Action buttons
        _btn_row = QWidget()
        _btn_row_layout = QHBoxLayout(_btn_row)
        _btn_row_layout.setContentsMargins(0, 0, 0, 0)

        self.show_neighbour_btn = QPushButton("Show Neighbours")
        self.calculate_synchronous_btn = QPushButton("Calculate Synchronicity")

        _btn_row_layout.addWidget(self.show_neighbour_btn)
        _btn_row_layout.addWidget(self.calculate_synchronous_btn)
        _btn_row_layout.addStretch(1)

        synch_layout.addRow(_btn_row)

        # Optional labels for results
        self.synch_results_label = QLabel("")
        synch_layout.addRow("Results:", self.synch_results_label)

        # Add the form container to the collapsible box
        self.synch_group.add_widget(form_container)

        # Add the collapsible box to the panel
        right_panel.addWidget(self.synch_group)
        #endregion

        right_panel.addStretch()


        # Saving
        save_group = QGroupBox("Saving")
        save_layout = QVBoxLayout()
        save_row_layout = QHBoxLayout()

        self.overwrite_checkbox = QCheckBox("Overwrite")
        self.overwrite_checkbox.setChecked(True)
        self.save_btn = QPushButton("Save Analysis")
        self.save_btn.clicked.connect(self._save_analysis_results)

        save_row_layout.addWidget(self.save_btn)
        save_row_layout.addWidget(self.overwrite_checkbox)

        save_layout.addLayout(save_row_layout)
        save_group.setLayout(save_layout)
        right_panel.addWidget(save_group)

        # --- LEFT PANEL ---
        left_panel_widget = QWidget()
        self.left_panel_layout = QVBoxLayout(left_panel_widget) 

        # Add widgets to left panel
        self.left_panel_layout.addWidget(self.image_display)
        self.left_panel_layout.addWidget(self.frame_slider)
        self.left_panel_layout.addWidget(self.canvas)

        # --- RIGHT PANEL ---
        self.right_panel_layout = QVBoxLayout() 
        right_panel_widget_content = QWidget()
        right_panel_widget_content.setLayout(self.right_panel_layout)

        # Add your collapsible boxes and groups to the right_panel_layout here
        # For example:
        self.right_panel_layout.addWidget(trace_group)
        self.right_panel_layout.addWidget(peak_group)
        self.right_panel_layout.addWidget(periodicity_group)
        self.right_panel_layout.addWidget(self.synch_group)
        self.right_panel_layout.addStretch()
        self.right_panel_layout.addWidget(save_group)

        # --- SCROLL AREA SETUP ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # allows vertical resizing
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setWidget(right_panel_widget_content)

        # Function to dynamically update the width based on content
        def update_right_panel_width():
            width = right_panel_widget_content.sizeHint().width()
            right_panel_widget_content.setMinimumWidth(width)
            right_panel_widget_content.setMaximumWidth(width)
            scroll_area.updateGeometry()

        # Initial call
        update_right_panel_width()

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel_widget)
        splitter.addWidget(scroll_area)

        # Set initial splitter sizes
        initial_right_width = right_panel_widget_content.sizeHint().width()
        splitter.setSizes([700, initial_right_width])

        # Add splitter to main layout
        main_layout.addWidget(splitter)


        # set data
        self.image_display.display_dask_frame(self.frames[0, 0, :, :])  # TCYX format
        self.image_display.set_rois(self.rois)
        self.update_intensity_trace()

        # Connecting buttons and signals
        self.frame_slider.valueChanged.connect(self.on_slider_moved)
        self.show_raw_btn.clicked.connect(self.show_raw_traces)
        self.show_detrended_btn.clicked.connect(self.show_detrended_traces)
        self.image_display.roiSelected.connect(self.roi_selected)
        self.find_peaks_btn.clicked.connect(self._start_peak_worker)
        self.periodicity_button.clicked.connect(self._start_periodicity_worker)
        self.periodic_display_checkbox.stateChanged.connect(self._periodic_cell_highlight)
        self.periodicity_toggle.toggled.connect(self._periodic_cell_highlight)
        self.show_neighbour_btn.clicked.connect(self._start_neighbours_worker)
        self.calculate_synchronous_btn.clicked.connect(self._start_synchronicity_worker)

    def _create_menu_bar(self):
        self.menu_bar = self.menuBar()

        file_menu = self.menu_bar.addMenu("File")

        restart_action = QAction("Open New Image", self)
        restart_action.triggered.connect(self._on_new_analysis)
        file_menu.addAction(restart_action)

        concat_action = QAction("Generate Experiment Overview CSV", self)
        concat_action.triggered.connect(self._on_concat_results)
        file_menu.addAction(concat_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def on_slider_moved(self, idx):
        self.current_frame = idx
        self.image_display.display_dask_frame(self.frames[self.current_frame, 0, :, :])
        self.update_intensity_trace()

    def roi_selected(self, idx):
        self.selected_roi = idx
        self.update_intensity_trace()

    def update_intensity_trace(self):
        self.ax.clear()
        color_raw = "#1E2B33"
        color_detrended = "#4C0308"

        if self.show_detrended:
            try:
                self.ax.plot(
                    self.detrended_intensities[:, self.selected_roi],
                    color=color_detrended,
                    label=f"ROI {self.selected_roi}",
                )
                self.ax.set_ylabel("Detrended Intensity")
            except Exception as e:
                print(f"Error plotting detrended intensities: {e}")
        else:
            self.ax.plot(
                self.intensities[:, self.selected_roi],
                color=color_raw,
                label=f"ROI {self.selected_roi}",
            )
            self.ax.set_ylabel("Raw Intensity")

        if hasattr(self, "peaks") and self.peaks is not None:
            peak_indices = np.where(self.peaks[:, self.selected_roi] == 1)[0]
            self.ax.plot(
                peak_indices,
                (
                    self.detrended_intensities
                    if self.show_detrended
                    else self.intensities
                )[peak_indices, self.selected_roi],
                "bx",
                markersize=4,
            )

        self.ax.axvline(self.current_frame, color="k", linestyle="--")
        self.ax.set_xlabel("Frame")
        self.ax.legend()
        self.canvas.draw()

    def show_raw_traces(self):
        self.show_detrended = False
        self.update_intensity_trace()

    def show_detrended_traces(self):
        sinc_value = self.sinc_filter_spin.value()
        frame_interval = self.frame_interval_spin.value()
        # If needed, recompute
        needs_recompute = (
            self.detrended_intensities is None
            or self.last_sinc_window != sinc_value
            or self.analysis_output.frame_interval != frame_interval
        )
        if needs_recompute:
            # Optionally show a progress bar or message here
            # start computing
            self._start_detrend_worker(sinc_value, frame_interval)
        else:
            self.show_detrended = True
            self.update_intensity_trace()

    def _periodic_cell_highlight(self):
        if self.periodic_display_checkbox.isChecked():
            if self.analysis_output is not None:
                if self.periodicity_toggle.value() == "STD" and self.experimental_stds is not None:
                    periodic_indices = np.where(
                        self.experimental_stds
                        < self.analysis_output.std_cutoff
                    )[0].tolist()
                elif self.periodicity_toggle.value() == "CoV" and self.experimental_covs is not None:
                    periodic_indices = np.where(
                        self.experimental_covs
                        < self.analysis_output.cov_cutoff
                    )[0].tolist()
                else:
                    periodic_indices = []
                self.image_display.draw_roi_centers(periodic_indices, radius=5)
        else:
            self.image_display.clear_roi_centers()

    def _start_detrend_worker(self, sinc_value, frame_interval):
        self.detrend_thread = QThread()
        self.analysis_output.frame_interval = frame_interval
        self.detrend_worker = DetrendWorker(
            self.intensities, sinc_value, self.analysis_output.frame_interval
        )
        self.detrend_worker.moveToThread(self.detrend_thread)
        self.detrend_thread.started.connect(self.detrend_worker.run)
        self.detrend_worker.finished.connect(self._detrend_done)
        self.detrend_worker.error.connect(self._detrend_error)
        self.detrend_worker.finished.connect(self.detrend_thread.quit)
        self.detrend_worker.finished.connect(self.detrend_worker.deleteLater)
        self.detrend_thread.finished.connect(self.detrend_thread.deleteLater)
        self.detrend_thread.start()

    def _detrend_done(self, detrended):
        self.detrended_intensities = detrended
        self.analysis_params.sinc_filter_window = self.sinc_filter_spin.value()
        self.last_sinc_window = self.sinc_filter_spin.value()
        # Optionally hide progress bar or message here
        self.show_detrended = True
        self.update_intensity_trace()

    def _detrend_error(self, error):
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.critical(self, "Error", f"Detrending failed: {error}")

    def _start_peak_worker(self):
        if self.detrended_intensities is None:
            QMessageBox.warning(
                self,
                "Missing Data",
                "Detrended traces are required. Please detrend first.",
            )
            return

        frame_interval = self.analysis_output.frame_interval

        # update analysis params
        self.analysis_params.peak_min_width = self.peak_min_width_spin.value()
        self.analysis_params.peak_max_width = self.peak_max_width_spin.value()
        self.analysis_params.peak_prominence = self.peak_prominence_spin.value()
        self.analysis_params.peak_min_height = self.peak_min_height_spin.value()

        # Convert time-based spinboxes to frame units
        min_width = int(self.peak_min_width_spin.value() / frame_interval)
        max_width = int(self.peak_max_width_spin.value() / frame_interval)

        self.find_peaks_btn.setEnabled(False)  # Prevent repeat clicks

        # Launch async worker
        self.peak_thread = QThread()
        self.peak_worker = PeakDetectionWorker(
            detrended_traces=self.detrended_intensities,
            min_width=min_width,
            max_width=max_width,
            analysis_params=self.analysis_params,
            analysis_output=self.analysis_output,
        )
        self.peak_worker.moveToThread(self.peak_thread)
        self.peak_thread.started.connect(self.peak_worker.run)
        self.peak_worker.finished.connect(self._peaks_detected)
        self.peak_worker.error.connect(self._peak_error)
        self.peak_worker.finished.connect(self.peak_thread.quit)
        self.peak_worker.finished.connect(self.peak_worker.deleteLater)
        self.peak_thread.finished.connect(self.peak_thread.deleteLater)
        self.peak_thread.start()

    def _peaks_detected(self, result):
        self.peaks = result[0]
        self.analysis_output = result[1]
        self.find_peaks_btn.setEnabled(True)
 
        percentage_four_peaks = (
            self.analysis_output.cells_four_peaks
            / self.analysis_output.number_of_cells
            * 100
        )

        # display the peak stats
        self.norm_peak_label.setText(f"{self.analysis_output.normalized_peaks:.2f}")
        self.fourpeak_label.setText(f"{percentage_four_peaks:.0f}%")
        self.frequency_label.setText(f"{self.analysis_output.median_frequency_mHz:.2f}")

        # update the intensity trace to show peaks
        self.update_intensity_trace()

    def _peak_error(self, error):
        QMessageBox.critical(self, "Error", f"Peak detection failed: {error}")
        self.find_peaks_btn.setEnabled(True)

    def _start_periodicity_worker(self):
        if self.peaks is None:
            QMessageBox.warning(
                self, "Missing Data", "Run peak detection before computing periodicity."
            )
            return

        self.analysis_params.periodicity_method = (
            "cutoff" if self.rb_periodicity_cutoff.isChecked() else "quantile"
        )
        self.analysis_params.std_threshold = float(
            self.periodicity_threshold_std_LineEdit.text()
        )
        self.analysis_params.cov_threshold = float(
            self.periodicity_threshold_cov_LineEdit.text()
        )

        self.periodicity_button.setEnabled(False)
        self.periodicity_thread = QThread()
        self.periodicity_worker = PeriodicCellWorker(
            peaks=self.peaks,
            analysis_params=self.analysis_params,
            analysis_output=self.analysis_output,
        )
        self.periodicity_worker.moveToThread(self.periodicity_thread)
        self.periodicity_thread.started.connect(self.periodicity_worker.run)
        self.periodicity_worker.finished.connect(self._periodicity_done)
        self.periodicity_worker.error.connect(self._periodicity_error)
        self.periodicity_worker.finished.connect(self.periodicity_thread.quit)
        self.periodicity_worker.finished.connect(self.periodicity_worker.deleteLater)
        self.periodicity_thread.finished.connect(self.periodicity_thread.deleteLater)
        self.periodicity_thread.start()

    def _periodicity_done(self, analysis_output, stds, covs):
        self.analysis_output = analysis_output
        self.experimental_stds = stds
        self.experimental_covs = covs

        # Update the labels with periodicity cutoffs and quantiles
        self.cov_cutoff_value_label.setText(
            f"cutoff: {self.analysis_output.cov_cutoff:.2f}"
        )
        self.cov_quantile_value_label.setText(
            f"quantile: {(self.analysis_output.cov_quantile) * 100:.2f}%"
        )
        self.std_cutoff_value_label.setText(
            f"cutoff: {self.analysis_output.std_cutoff:.2f}"
        )
        self.std_quantile_value_label.setText(
            f"quantile: {(self.analysis_output.std_quantile) * 100:.2f}%"
        )

        # Update the periodicity percentage labels
        std_periodic_per_all = round(
            (
                (
                    self.analysis_output.experimental_below_std
                    / self.analysis_output.number_of_cells
                )
                * 100
            ),
            1,
        )
        cov_periodic_per_all = round(
            (
                (
                    self.analysis_output.experimental_below_cov
                    / self.analysis_output.number_of_cells
                )
                * 100
            ),
            1,
        )
        self.std_periodic_per_active_label.setText(
            f"Cells below STD cutoff: {std_periodic_per_all}%"
        )
        self.cov_periodic_per_active_label.setText(
            f"Cells below CoV cutoff: {cov_periodic_per_all}%"
        )

        self.periodicity_button.setEnabled(True)
        self.periodic_display_checkbox.setEnabled(True)

    def _periodicity_error(self, error):
        QMessageBox.critical(self, "Error", f"Periodic ROI analysis failed: {error}")
        self.periodicity_button.setEnabled(True)

    def _start_neighbours_worker(self):
        if self.peaks is None:
            QMessageBox.warning(
                self, "Missing Data", "Run peak detection before showing neighbours."
            )
            return
        if self.selected_roi is None:
            QMessageBox.warning(self, "No ROI Selected", "Please select an ROI first.")
            return

        self.show_neighbour_btn.setEnabled(False)
        self.neighbours_thread = QThread()
        self.analysis_params.neighbour_distance = self.neighbour_distance_spin.value()
        neighbour_tolerance_pixels = int(self.analysis_params.neighbour_distance / self.analysis_output.pixel_interval_y)
        self.neighbours_worker = AdjacencyMatrixWorker(
            masks=self.masks,
            neighbour_tolerance_pixels=neighbour_tolerance_pixels,
        )
        self.neighbours_worker.moveToThread(self.neighbours_thread)
        self.neighbours_thread.started.connect(self.neighbours_worker.run)
        self.neighbours_worker.finished.connect(self._neighbours_done)
        self.neighbours_worker.error.connect(self._neighbours_error)
        self.neighbours_worker.finished.connect(self.neighbours_thread.quit)
        self.neighbours_worker.finished.connect(self.neighbours_worker.deleteLater)
        self.neighbours_thread.finished.connect(self.neighbours_thread.deleteLater)
        self.neighbours_thread.start()
    
    def _neighbours_done(self, adjacency_matrix, shortest_path_matrix):
        self.adjacency_matrix = adjacency_matrix
        self.shortest_path_matrix = shortest_path_matrix

        # Highlight neighbours of the selected ROI
        self.image_display.draw_roi_connections(self.shortest_path_matrix)

        self.show_neighbour_btn.setEnabled(True)

    def _neighbours_error(self, error):
        QMessageBox.critical(self, "Error", f"Finding neighbours failed: {error}")
        self.show_neighbour_btn.setEnabled(True)

    def _start_synchronicity_worker(self):
        if self.peaks is None:
            QMessageBox.warning(
                self, "Missing Data", "Run peak detection before calculating synchronicity."
            )
            return
        if not hasattr(self, 'adjacency_matrix'):
            QMessageBox.warning(self, "No Neighbour Data", "Please find neighbours first.")
            return

        self.calculate_synchronous_btn.setEnabled(False)
        self.synchronicity_thread = QThread()
        self.analysis_params.time_window = self.time_window_spin.value()
        self.synchronicity_worker = SynchronicityWorker(
            self.analysis_output,
            self.analysis_params,
            self.peaks,
            self.shortest_path_matrix
        )
        self.synchronicity_worker.moveToThread(self.synchronicity_thread)
        self.synchronicity_thread.started.connect(self.synchronicity_worker.run)
        self.synchronicity_worker.finished.connect(self._synchronicity_done)
        self.synchronicity_worker.error.connect(self._synchronicity_error)
        self.synchronicity_worker.finished.connect(self.synchronicity_thread.quit)
        self.synchronicity_worker.finished.connect(self.synchronicity_worker.deleteLater)
        self.synchronicity_thread.finished.connect(self.synchronicity_thread.deleteLater)
        self.synchronicity_thread.start()

    def _synchronicity_done(self, results):
        self.analysis_output = results[0]
        self.true_synchronous_peaks_matrix = results[1]
        self.synch_results_label.setText(
            f"# of True Synchronous Peaks: {results[1].sum()}\n"
            f"# of Random Synchronous Peaks: {results[2].sum()}\n"
            f"Z-Score: {self.analysis_output.experiment_1st_neighbour_zscore:.2f}"
        )

        self.calculate_synchronous_btn.setEnabled(True)

    def _synchronicity_error(self, error):
        tb_str = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        QMessageBox.critical(self, "Error", f"Synchronicity analysis failed: {tb_str}")
        self.calculate_synchronous_btn.setEnabled(True)

    def _save_analysis_results(self):
        self.save_btn.setEnabled(False)
        self.analysis_save_thread = QThread()
        self.analysis_worker = AnalysisSaveWorker(
            tproj=self.tproj,
            masks=self.masks,
            synchronous_peaks_matrix=self.true_synchronous_peaks_matrix,
            analysis_output=self.analysis_output,
            analysis_params=self.analysis_params,
            peaks=self.peaks,
            detrended_intensities=self.detrended_intensities,
            intensities=self.intensities,
            stds=self.experimental_stds,
            covs=self.experimental_covs,
            overwrite=self.overwrite_checkbox.isChecked(),
        )
        self.analysis_worker.moveToThread(self.analysis_save_thread)

        self.analysis_save_thread.started.connect(self.analysis_worker.run)
        self.analysis_worker.finished.connect(self.on_save_finished)
        self.analysis_worker.error.connect(self.on_save_error)
        self.analysis_worker.finished.connect(self.analysis_save_thread.quit)
        self.analysis_worker.finished.connect(self.analysis_worker.deleteLater)
        self.analysis_save_thread.finished.connect(
            self.analysis_save_thread.deleteLater
        )

        self.analysis_save_thread.start()

    def on_save_finished(self, _: str):
        self.save_btn.setEnabled(True)
        QMessageBox.information(
            self, "Save Complete", "Analysis results saved successfully."
        )

    def on_save_error(self, e: Exception):
        self.save_btn.setEnabled(True)
        QMessageBox.critical(self, "Save Error", str(e))

    def _on_new_analysis(self):
        if self.app_controller:
            self.app_controller.restart()

    def _on_concat_results(self):
        try:
            if not self.analysis_output.filepath:
                QMessageBox.warning(self, "No Image", "No image is currently open.")
                return

            # Get parent folder of the current image
            image_path = Path(self.analysis_output.filepath)
            root_folder = image_path.parent

            # Call your concatenation function
            concat_analysis_files(str(root_folder))

            QMessageBox.information(
                self,
                "Success",
                f"Analysis results concatenated successfully in:\n{root_folder / 'experiment_overview.csv'}",
            )
        except FileNotFoundError as e:
            QMessageBox.warning(self, "No CSV Files", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred:\n{e}")
