"""Clipboard utilities for image handling.

Uses platform-native clipboard access (no Pillow dependency).
"""

import base64
from typing import Optional, Tuple

from emdash_core.utils.image import (
    read_clipboard_image,
    is_clipboard_image_available,
    get_image_info,
    ClipboardImageError,
)


def get_clipboard_image() -> Optional[Tuple[str, str]]:
    """Get image from clipboard if available.

    Returns:
        Tuple of (base64_data, format) if image found, None otherwise.
    """
    try:
        if not is_clipboard_image_available():
            return None

        image_data = read_clipboard_image()
        if image_data is None:
            return None

        # Encode to base64
        base64_data = base64.b64encode(image_data).decode('utf-8')
        return base64_data, 'png'

    except ClipboardImageError:
        return None
    except Exception:
        return None


def get_image_from_path(path: str) -> Optional[Tuple[str, str]]:
    """Load image from file path.

    Only PNG files are fully supported. Other formats will be read as raw bytes.

    Args:
        path: Path to image file

    Returns:
        Tuple of (base64_data, format) if successful, None otherwise.
    """
    try:
        with open(path, 'rb') as f:
            image_data = f.read()

        # Determine format from file extension
        ext = path.lower().split('.')[-1]
        if ext in ('jpg', 'jpeg'):
            img_format = 'jpeg'
        elif ext == 'png':
            img_format = 'png'
        elif ext == 'gif':
            img_format = 'gif'
        elif ext == 'webp':
            img_format = 'webp'
        else:
            img_format = 'png'

        base64_data = base64.b64encode(image_data).decode('utf-8')
        return base64_data, img_format

    except Exception:
        return None


def get_image_dimensions(base64_data: str) -> Optional[Tuple[int, int]]:
    """Get dimensions of base64-encoded PNG image.

    Args:
        base64_data: Base64-encoded image data

    Returns:
        Tuple of (width, height) if successful, None otherwise.
    """
    try:
        image_bytes = base64.b64decode(base64_data)
        info = get_image_info(image_bytes)
        if info.get("width") and info.get("height"):
            return info["width"], info["height"]
        return None
    except Exception:
        return None
