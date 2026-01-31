from __future__ import annotations

from enum import Enum

import numpy as np
from foxglove.schemas import RawImage as FoxgloveRawImage
from pydantic import Field

from common.message.message import Message


class ImageEncoding(str, Enum):
    """
    Image encodings with associated metadata.

    Example:
        ```python
        from common.message import ImageEncoding

        # Get bytes per pixel for an encoding
        encoding = ImageEncoding.RGB8
        bpp = encoding.bytes_per_pixel  # 3

        # Get numpy dtype for an encoding
        dtype = encoding.numpy_dtype  # np.uint8

        # Get number of channels
        channels = encoding.channels  # 3
        ```
    """

    # Monochrome images
    MONO8 = "mono8"
    MONO16 = "mono16"

    # Color images
    RGB8 = "rgb8"
    RGBA8 = "rgba8"
    BGR8 = "bgr8"
    BGRA8 = "bgra8"

    # Depth images
    DEPTH_U16 = "16UC1"
    DEPTH_F32 = "32FC1"

    @property
    def bytes_per_pixel(self) -> int:
        """
        Get the number of bytes per pixel for this encoding.

        :return: The number of bytes per pixel.
        """

        return {
            ImageEncoding.MONO8: 1,
            ImageEncoding.MONO16: 2,
            ImageEncoding.RGB8: 3,
            ImageEncoding.RGBA8: 4,
            ImageEncoding.BGR8: 3,
            ImageEncoding.BGRA8: 4,
            ImageEncoding.DEPTH_U16: 2,
            ImageEncoding.DEPTH_F32: 4,
        }[self]

    @property
    def numpy_dtype(self) -> np.dtype:
        """
        Get the numpy dtype for this encoding.

        :return: The numpy dtype.
        """

        dtype_map = {
            ImageEncoding.MONO8: np.uint8,
            ImageEncoding.MONO16: np.uint16,
            ImageEncoding.RGB8: np.uint8,
            ImageEncoding.RGBA8: np.uint8,
            ImageEncoding.BGR8: np.uint8,
            ImageEncoding.BGRA8: np.uint8,
            ImageEncoding.DEPTH_U16: np.uint16,
            ImageEncoding.DEPTH_F32: np.float32,
        }
        return np.dtype(dtype_map[self])

    @property
    def channels(self) -> int:
        """
        Get the number of color channels.

        :return: The number of color channels.
        """

        if self in (
            ImageEncoding.MONO8,
            ImageEncoding.MONO16,
            ImageEncoding.DEPTH_U16,
            ImageEncoding.DEPTH_F32,
        ):
            return 1
        elif self in (ImageEncoding.RGB8, ImageEncoding.BGR8):
            return 3
        elif self in (ImageEncoding.RGBA8, ImageEncoding.BGRA8):
            return 4
        else:
            return 1


class Image(Message):
    """
    An image with raw data.

    Example:
        ```python
        from common.message import Image, ImageEncoding
        import numpy as np

        # Create an image from a numpy array
        rgb_array = np.zeros((480, 640, 3), dtype=np.uint8)
        rgb_array[:, :, 0] = 255  # Red channel
        image = Image.from_numpy(rgb_array, ImageEncoding.RGB8)

        # Convert back to numpy for processing
        array = image.to_numpy()
        print(f"Shape: {array.shape}")  # (480, 640, 3)

        # Create a depth image
        depth_array = np.ones((480, 640), dtype=np.float32) * 2.5
        depth_image = Image.from_numpy(depth_array, ImageEncoding.DEPTH_F32)
        ```
    """

    _type = "antioch/image"
    encoding: ImageEncoding = Field(description="Pixel encoding format of the image")
    width: int = Field(description="Image width in pixels")
    height: int = Field(description="Image height in pixels")
    data: bytes = Field(description="Raw image data as bytes")

    @classmethod
    def from_numpy(cls, array: np.ndarray, encoding: ImageEncoding | None = None) -> Image:
        """
        Create an Image from a numpy array.

        For uint8 encodings (RGB8, RGBA8, MONO8), pixel values should be in the range [0, 255].
        For float32 depth encodings (DEPTH_F32), values are typically in meters.
        For uint16 encodings (DEPTH_U16, MONO16), values use the full uint16 range.

        If the array dtype doesn't match the encoding's dtype, it will be converted
        via astype().

        :param array: The numpy array containing image data.
        :param encoding: The image encoding (auto-detected if None).
        :return: An Image instance.
        :raises ValueError: If array shape doesn't match a supported format.
        """

        # Auto-detect encoding based on array shape and dtype
        if encoding is None:
            if array.ndim == 2:
                # Grayscale or depth
                if array.dtype == np.uint8:
                    encoding = ImageEncoding.MONO8
                elif array.dtype == np.uint16:
                    encoding = ImageEncoding.DEPTH_U16
                elif array.dtype == np.float32:
                    encoding = ImageEncoding.DEPTH_F32
                else:
                    raise ValueError(f"Unsupported dtype for 2D array: {array.dtype}")
            elif array.ndim == 3:
                # Color image
                channels = array.shape[2]
                if channels == 3:
                    encoding = ImageEncoding.RGB8
                elif channels == 4:
                    encoding = ImageEncoding.RGBA8
                else:
                    raise ValueError(f"Unsupported number of channels: {channels}")
            else:
                raise ValueError(f"Unsupported array dimensions: {array.ndim}")

        # Convert array dtype to match encoding if necessary
        expected_dtype = encoding.numpy_dtype
        if array.dtype != expected_dtype:
            array = array.astype(expected_dtype)

        # Standard packing (handles both contiguous and non-contiguous)
        if array.ndim < 2:
            raise ValueError(f"Image array must be at least 2D, got shape {array.shape}")
        height, width = array.shape[:2]
        data = array.tobytes()
        return cls(encoding=encoding, width=width, height=height, data=data)

    def to_numpy(self) -> np.ndarray:
        """
        Convert the image to a numpy array.

        :return: A numpy array with the image data.
        """

        # Standard contiguous buffer
        shape = (self.height, self.width) if self.encoding.channels == 1 else (self.height, self.width, self.encoding.channels)
        array = np.frombuffer(self.data, dtype=self.encoding.numpy_dtype)
        return array.reshape(shape)

    def to_foxglove(self) -> FoxgloveRawImage:
        """
        Convert to Foxglove RawImage for telemetry.

        :return: Foxglove RawImage schema.
        """

        step = self.width * self.encoding.bytes_per_pixel
        return FoxgloveRawImage(
            timestamp=None,
            frame_id="",
            width=self.width,
            height=self.height,
            encoding=self.encoding.value,
            step=step,
            data=self.data,
        )
