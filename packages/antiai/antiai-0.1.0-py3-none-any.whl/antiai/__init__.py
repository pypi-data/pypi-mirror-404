"""
AntiAI - Advanced Image Protection System.

This library provides comprehensive protection for images against
AI training, unauthorized use, and manipulation.

Basic Usage:
    >>> from antiai import AntiAIEncoder, AntiAIDecoder
    >>> encoder = AntiAIEncoder()
    >>> encoder.encode("input.png", "output.antiAI", author="Miguel")
    >>> decoder = AntiAIDecoder()
    >>> image, metadata = decoder.decode("output.antiAI")

"""

from .__version__ import (
    __author__,
    __author_email__,
    __description__,
    __license__,
    __title__,
    __url__,
    __version__,
    __version_info__,
)
from .core.decoder import AntiAIDecoder
from .core.encoder import AntiAIEncoder
from .core.exceptions import (
    AdversarialError,
    AntiAIError,
    CorruptedDataError,
    EncryptionError,
    FormatError,
    ImageError,
    IntegrityError,
    InvalidHeaderError,
    ProtectionError,
    SignatureError,
    UnsupportedImageFormatError,
    ValidationError,
    VersionMismatchError,
    WatermarkError,
)
from .core.format_spec import AntiAIHeader, ColorMode, ProtectionFlags
from .protection.adversarial import AdversarialConfig, AdversarialProtection
from .protection.watermark import InvisibleWatermark
from .validation.verify import ProtectionVerifier

__all__ = [
    # Version info
    "__version__",
    "__version_info__",
    "__title__",
    "__description__",
    "__author__",
    "__author_email__",
    "__license__",
    "__url__",
    # Main classes
    "AntiAIEncoder",
    "AntiAIDecoder",
    "ProtectionVerifier",
    # Protection
    "AdversarialProtection",
    "AdversarialConfig",
    "InvisibleWatermark",
    # Format
    "AntiAIHeader",
    "ProtectionFlags",
    "ColorMode",
    # Exceptions
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
]
