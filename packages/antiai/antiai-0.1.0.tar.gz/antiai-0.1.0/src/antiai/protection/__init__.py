"""Protection mechanisms for images."""

from .adversarial import AdversarialConfig, AdversarialProtection
from .metadata import (
    AuthorInfo,
    CopyrightInfo,
    ImageMetadata,
    MetadataBuilder,
    ProtectionInfo,
)
from .watermark import InvisibleWatermark

__all__ = [
    "AdversarialProtection",
    "AdversarialConfig",
    "InvisibleWatermark",
    "ImageMetadata",
    "MetadataBuilder",
    "AuthorInfo",
    "CopyrightInfo",
    "ProtectionInfo",
]
