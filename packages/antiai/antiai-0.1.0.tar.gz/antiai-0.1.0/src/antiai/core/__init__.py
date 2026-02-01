"""Core encoding and decoding functionality."""

from .decoder import AntiAIDecoder
from .encoder import AntiAIEncoder
from .exceptions import (
    AdversarialError,
    AntiAIError,
    CorruptedDataError,
    EncryptionError,
    FormatError,
    ImageError,
    ImageTooLargeError,
    IntegrityError,
    InvalidHeaderError,
    ProtectionError,
    SignatureError,
    UnsupportedImageFormatError,
    ValidationError,
    VersionMismatchError,
    WatermarkError,
)
from .format_spec import AntiAIHeader, ColorMode, ProtectionFlags

__all__ = [
    "AntiAIEncoder",
    "AntiAIDecoder",
    "AntiAIHeader",
    "ColorMode",
    "ProtectionFlags",
    "AntiAIError",
    "FormatError",
    "InvalidHeaderError",
    "VersionMismatchError",
    "CorruptedDataError",
    "ProtectionError",
    "AdversarialError",
    "WatermarkError",
    "EncryptionError",
    "ValidationError",
    "IntegrityError",
    "SignatureError",
    "ImageError",
    "UnsupportedImageFormatError",
    "ImageTooLargeError",
]
