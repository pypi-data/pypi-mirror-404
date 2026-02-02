import os
import dask.array as da
import numpy as np
import warnings
import re
from bioio import BioImage
import bioio_tifffile
import xml.etree.ElementTree as ET
from skimage.measure import find_contours
from scipy.ndimage import label

ALLOWED_IMAGE_EXTENSIONS = [".czi", ".tif", ".tiff"]

def load_timelapse_lazy(
    file_path: str,
) -> list[da.Array, float, float, float]:
    """Load a timelapse image file lazily using AICSImageIO, returning a Dask array of the image data along with the frame interval and pixel sizes.

    Currently supports CZI and TIF/TIFF files. The image data is returned as a Dask array with shape (T, C, Y, X) where T is time, C is channels, Y is height, and X is width. The Z dimension is dropped if it has only one slice.

    :param file_path: input file path to the timelapse image file
    :type file_path: str
    :raises TypeError: if filepath is not a string
    :raises FileNotFoundError: if the file does not exist
    :raises ValueError: if the extension is not supported
    :raises ValueError: if the image does not have the expected 5D shape (TCZYX)
    :raises ValueError: if the image has more than one Z slice and Z cannot be automatically dropped
    :return: returns a list of a Dask array containing the image data, the frame interval in seconds, and pixel sizes in micrometers (Y, X)
    :rtype: list[da.Array, float, float, float]
    """
    if not isinstance(file_path, str):
        raise TypeError("file_path must be a string")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[-1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError(
            f"Image to load has the unsupported file format '{ext}'. Supported file formats are: {ALLOWED_IMAGE_EXTENSIONS}"
        )

    # Load with BioImage using Dask
    if ext == ".czi":
        print("Using bioio_czi with aicspylibczi as backend to read")
        img = BioImage(file_path, reconstruct_mosaic=False, use_aicspylibczi=True)
    elif ext in [".tif", ".tiff"]:
        print("Using bioio_tifffile.Reader to read")
        img = BioImage(
            file_path, reconstruct_mosaic=False, reader=bioio_tifffile.Reader
        )
    # extract the relevant metadata
    pixel_sizes = img.physical_pixel_sizes  # Units are in micrometers (µm)
    y_um = round(pixel_sizes.Y, 2) if pixel_sizes else None
    x_um = round(pixel_sizes.X, 2) if pixel_sizes else None

    frame_interval = None

    # accessing frame interval from tif/tiff meadata
    if ext == ".tiff" or ext == ".tif":
        try:
            match = re.search(r"finterval=([0-9.]+)", img.metadata)
            if match is not None:
                frame_interval = float(match.group(1))
            else:
                root = ET.fromstring(img.metadata)
                deltas = []
                for plane in root.findall(".//{*}Plane"):
                    dt = plane.attrib.get("DeltaT")
                    if dt is not None:
                        deltas.append(float(dt))

                if len(deltas) >= 2:
                    # Compute median interval between frames
                    delta_ts_unique = sorted(set(deltas))
                    frame_interval = float(np.median(np.diff(delta_ts_unique)))
                else:
                    # Some files store TimeIncrement directly
                    increment = root.find(".//{*}Pixels")
                    if increment is not None and "TimeIncrement" in increment.attrib:
                        frame_interval = float(increment.attrib["TimeIncrement"])
        except Exception as e:
            warnings.warn(
                f"Failed to extract frame interval from metadata: {type(e).__name__}: {e}",
                UserWarning,
            )
    elif ext == ".czi":
        try:
            root = img.metadata
            increment_elem = root.find(".//T/Positions/Interval/Increment")

            if increment_elem is not None and increment_elem.text:
                frame_interval = float(increment_elem.text)
            else:
                frame_interval = img.time_interval.total_seconds()
        except Exception as e:
            warnings.warn(
                f"Failed to extract frame interval from metadata: {type(e).__name__}: {e}",
                UserWarning,
            )
    dask_img = img.dask_data  # TCZYX

    if dask_img.ndim != 5:
        raise ValueError(f"Expected 5D image (TCZYX), but got shape {dask_img.shape}")

    T, C, Z, Y, X = dask_img.shape

    if T > 1 and Z == 1:
        dask_img = dask_img[:, :, 0, :, :]  # shape: (T, C, Z, Y, X)
    elif len([dim for dim in dask_img.shape if dim != 1]) == 3:  #
        print("Image has three non-singleton dimensions, presuming order is (T, Y, X).")
        dask_img = _reorder_dask_array(dask_img)  # reorder to (T, C, Y, X)
        dask_img = dask_img[:, :, 0, :, :]  # shape: (T, C, Z, Y, X)
    else:
        raise ValueError(
            f"Cannot drop Z dimension automatically: Z={Z}. Consider handling it explicitly. Image shape: {dask_img.shape}"
        )

    print(f"Returning lazy array of shape {dask_img.shape} (T, C, Y, X)")
    return dask_img, frame_interval, y_um, x_um

def _reorder_dask_array(
    dask_img: da.Array,
) -> da.Array:
    """Reorders a Dask array to the specified order.

    :param dask_array: input Dask array
    :type dask_array: da.Array
    :return: reordered Dask array
    :rtype: da.Array
    """
    shape = dask_img.shape
    non_1_axes = [i for i, dim in enumerate(shape) if dim != 1]

    if len(non_1_axes) < 3:
        raise ValueError(f"Expected at least 3 non-1 dimensions in {shape}")

    # Identify T, Y, X from non-1 dimensions
    non1_indices = [i for i, d in enumerate(dask_img.shape) if d != 1]

    T_axis = non1_indices[0]  # First non-singleton = T
    Y_axis = non1_indices[-2]  # Second last non-singleton = Y
    X_axis = non1_indices[-1]  # Last non-singleton = X

    # Fill in dummy axes for C and Z
    all_axes = list(range(5))
    used_axes = {T_axis, Y_axis, X_axis}
    unused_axes = [a for a in all_axes if a not in used_axes]

    # Fix order to (T, C, Z, Y, X)
    axis_map = {
        "T": T_axis,
        "C": unused_axes[0],
        "Z": unused_axes[1],
        "Y": Y_axis,
        "X": X_axis,
    }

    perm = [axis_map[k] for k in ["T", "C", "Z", "Y", "X"]]

    return dask_img.transpose(*perm)

def read_image(
    file_path: str,
) -> np.ndarray:
    """Reads a image from a file and returns it as a Dask array.

    :param file_path: path to the image file
    :type file_path: str
    :return: Dask array of the image
    :rtype: da.Array
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        img = BioImage(file_path, reconstruct_mosaic=True).dask_data.compute()
        return img[
            0, 0, 0, :, :
        ]  # Assuming the label image is single-channel, return as (Y, X)
    except Exception as e:
        raise ValueError(
            f"Failed to read label image from {file_path}: {type(e).__name__}: {e}"
        )
        return None

def read_label_image(
    file_path: str,
) -> np.ndarray:
    """Reads a label image from a file and returns it as a Dask array.

    :param file_path: path to the label image file
    :type file_path: str
    :return: Dask array of the label image
    :rtype: da.Array
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        img = BioImage(file_path, reconstruct_mosaic=True).dask_data.compute()
        img = img[0, 0, 0, :, :]
        clean_masks = np.zeros_like(img)
        roi_labels = np.unique(img)
        roi_labels = roi_labels[roi_labels != 0]

        # 8-way connectivity in 2D
        kernel = np.ones((3, 3), dtype=bool)

        for label_val in roi_labels:
            roi_mask = img == label_val
            labeled, n = label(roi_mask, structure=kernel)

            # if mask is not connected
            if n > 1:
                component_sizes = np.bincount(labeled.ravel())[1:]
                largest_idx = np.argmax(component_sizes) + 1
                clean_masks[labeled == largest_idx] = label_val

                warnings.warn(
                    f"ROI {label_val} had {n} disconnected components — kept the largest ({component_sizes[largest_idx-1]} px).",
                    UserWarning,
                )
            else:
                clean_masks[roi_mask] = label_val
        return clean_masks
        
    except Exception as e:
        raise ValueError(
            f"Failed to read label image from {file_path}: {type(e).__name__}: {e}"
        )
        return None

def get_pixel_contour_from_label_img(
    label_img: np.ndarray, orig_shape: tuple=(1,1), target_shape: tuple=(1,1)
) -> list:
    """
    Generates pixel contours from a labeled image, scaled to a target shape.

    :param label_img: a label image where each pixel is labeled with an integer representing the ROI it belongs to
    :type label_img: np.ndarray
    :param orig_shape: original shape of the image (height, width)
    :type orig_shape: tuple
    :param target_shape: target shape to which the contours should be scaled (height, width)
    :type target_shape: tuple
    :return: returns a list of polygons representing the scaled contours of each ROI
    :rtype: list
    """
    roi_polygons = []
    orig_height, orig_width = orig_shape
    target_height, target_width = target_shape
    scale_y = target_height / orig_height
    scale_x = target_width / orig_width
    for index in range(1, label_img.max() + 1):  # skip background (0)
        contours = find_contours(label_img == index, 0.5)
        if contours:
            contour = contours[0]
            y, x = contour.T
            y, x = y * scale_y, x * scale_x  # rescales coordinates to target shape
            polygon = list(zip(x, y))
            roi_polygons.append(polygon)
    return roi_polygons
    