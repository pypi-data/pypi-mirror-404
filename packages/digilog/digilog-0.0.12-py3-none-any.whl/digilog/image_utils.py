"""
Image utilities for detecting and converting various image types to bytes.

Supports:
- PIL Images (from Pillow)
- Numpy arrays
- File paths (strings or Path objects)
- Matplotlib figures
"""

import io
import os
from pathlib import Path
from typing import Tuple, Union, Any, Optional


class ImageConversionError(Exception):
    """Raised when image conversion fails."""
    pass


def detect_image_type(obj: Any) -> Optional[str]:
    """
    Detect the type of image object.
    
    Args:
        obj: Object to check
        
    Returns:
        String indicating type: 'pil', 'numpy', 'path', 'matplotlib', or None
    """
    # Check for PIL Image
    try:
        from PIL import Image
        if isinstance(obj, Image.Image):
            return 'pil'
    except ImportError:
        pass
    
    # Check for numpy array
    try:
        import numpy as np
        if isinstance(obj, np.ndarray):
            # Verify it looks like an image (2D or 3D array)
            if len(obj.shape) in [2, 3]:
                return 'numpy'
    except ImportError:
        pass
    
    # Check for matplotlib figure
    try:
        import matplotlib.figure
        if isinstance(obj, matplotlib.figure.Figure):
            return 'matplotlib'
    except ImportError:
        pass
    
    # Check for file path
    if isinstance(obj, (str, Path)):
        path = Path(obj)
        if path.exists() and path.is_file():
            # Check if it has an image extension
            ext = path.suffix.lower()
            if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp']:
                return 'path'
    
    return None


def convert_to_bytes(
    obj: Any,
    format: str = "PNG",
    quality: int = 95
) -> Tuple[bytes, str, str]:
    """
    Convert various image types to bytes.
    
    Args:
        obj: Image object (PIL Image, numpy array, file path, or matplotlib figure)
        format: Output format (PNG, JPEG, etc.)
        quality: JPEG quality (1-100)
        
    Returns:
        Tuple of (bytes, mime_type, filename)
        
    Raises:
        ImageConversionError: If conversion fails
    """
    image_type = detect_image_type(obj)
    
    if image_type is None:
        raise ImageConversionError(
            f"Unsupported image type: {type(obj)}. "
            "Supported types: PIL.Image, numpy.ndarray, file path, or matplotlib.figure.Figure"
        )
    
    try:
        if image_type == 'pil':
            return _pil_to_bytes(obj, format, quality)
        elif image_type == 'numpy':
            return _numpy_to_bytes(obj, format, quality)
        elif image_type == 'path':
            return _path_to_bytes(obj, format, quality)
        elif image_type == 'matplotlib':
            return _matplotlib_to_bytes(obj, format, quality)
        else:
            raise ImageConversionError(f"Unknown image type: {image_type}")
    except Exception as e:
        raise ImageConversionError(f"Failed to convert image: {e}")


def _pil_to_bytes(
    img: Any,
    format: str = "PNG",
    quality: int = 95
) -> Tuple[bytes, str, str]:
    """Convert PIL Image to bytes."""
    buffer = io.BytesIO()
    
    # Handle RGBA images for JPEG
    if format.upper() == "JPEG" and img.mode in ('RGBA', 'LA', 'P'):
        # Convert to RGB
        rgb_img = img.convert('RGB')
        rgb_img.save(buffer, format=format, quality=quality)
    else:
        img.save(buffer, format=format, quality=quality if format.upper() == "JPEG" else None)
    
    buffer.seek(0)
    mime_type = get_mime_type(format)
    filename = f"image.{format.lower()}"
    
    return buffer.read(), mime_type, filename


def _numpy_to_bytes(
    arr: Any,
    format: str = "PNG",
    quality: int = 95
) -> Tuple[bytes, str, str]:
    """Convert numpy array to bytes via PIL."""
    try:
        from PIL import Image
        import numpy as np
    except ImportError as e:
        raise ImageConversionError(f"Required library not installed: {e}")
    
    # Normalize array to 0-255 uint8
    if arr.dtype != np.uint8:
        # Normalize to 0-1 if needed
        if arr.max() <= 1.0 and arr.min() >= 0.0:
            arr = (arr * 255).astype(np.uint8)
        else:
            # Scale to 0-255
            arr = ((arr - arr.min()) / (arr.max() - arr.min()) * 255).astype(np.uint8)
    
    # Convert to PIL Image
    if len(arr.shape) == 2:
        # Grayscale
        img = Image.fromarray(arr, mode='L')
    elif len(arr.shape) == 3:
        if arr.shape[2] == 3:
            # RGB
            img = Image.fromarray(arr, mode='RGB')
        elif arr.shape[2] == 4:
            # RGBA
            img = Image.fromarray(arr, mode='RGBA')
        else:
            raise ImageConversionError(f"Unsupported array shape: {arr.shape}")
    else:
        raise ImageConversionError(f"Unsupported array shape: {arr.shape}")
    
    return _pil_to_bytes(img, format, quality)


def _path_to_bytes(
    path: Union[str, Path],
    format: str = "PNG",
    quality: int = 95
) -> Tuple[bytes, str, str]:
    """Convert image file to bytes."""
    try:
        from PIL import Image
    except ImportError as e:
        raise ImageConversionError(f"PIL not installed: {e}")
    
    path = Path(path)
    
    if not path.exists():
        raise ImageConversionError(f"File not found: {path}")
    
    # Open and convert
    img = Image.open(path)
    original_filename = path.name
    
    # If format is not specified, keep original format
    if format == "PNG" and path.suffix.lower() in ['.jpg', '.jpeg']:
        format = "JPEG"
    
    bytes_data, mime_type, _ = _pil_to_bytes(img, format, quality)
    
    return bytes_data, mime_type, original_filename


def _matplotlib_to_bytes(
    fig: Any,
    format: str = "PNG",
    quality: int = 95
) -> Tuple[bytes, str, str]:
    """Convert matplotlib figure to bytes."""
    buffer = io.BytesIO()
    
    # Save figure to buffer
    fig.savefig(
        buffer,
        format=format.lower(),
        bbox_inches='tight',
        dpi=150
    )
    buffer.seek(0)
    
    mime_type = get_mime_type(format)
    filename = f"plot.{format.lower()}"
    
    return buffer.read(), mime_type, filename


def get_mime_type(format: str) -> str:
    """
    Get MIME type from image format.
    
    Args:
        format: Image format (e.g., 'PNG', 'JPEG')
        
    Returns:
        MIME type string
    """
    mime_types = {
        'PNG': 'image/png',
        'JPEG': 'image/jpeg',
        'JPG': 'image/jpeg',
        'GIF': 'image/gif',
        'BMP': 'image/bmp',
        'TIFF': 'image/tiff',
        'WEBP': 'image/webp',
    }
    
    return mime_types.get(format.upper(), 'image/png')

