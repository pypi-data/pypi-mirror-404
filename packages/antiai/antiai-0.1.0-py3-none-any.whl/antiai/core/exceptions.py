"""
Custom exceptions for the AntiAI library.

This module defines all custom exceptions used throughout the library,
providing clear error messages and proper exception hierarchy.
"""

from typing import Optional


class AntiAIError(Exception):
    """Base exception for all AntiAI errors."""

    def __init__(self, message: str, details: Optional[dict] = None) -> None:
        """
        Initialize AntiAIError.

        Args:
            message: Human-readable error message
            details: Optional dict with additional error context
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return string representation of error."""
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class FormatError(AntiAIError):
    """Raised when file format is invalid or corrupted."""

    pass


class InvalidHeaderError(FormatError):
    """Raised when AntiAI file header is invalid."""

    pass


class VersionMismatchError(FormatError):
    """Raised when file version is not supported."""

    def __init__(self, found_version: int, supported_versions: list[int]) -> None:
        """
        Initialize VersionMismatchError.

        Args:
            found_version: Version number found in file
            supported_versions: List of supported version numbers
        """
        message = (
            f"Unsupported file version {found_version}. "
            f"Supported versions: {supported_versions}"
        )
        super().__init__(message, {"found": found_version, "supported": supported_versions})


class CorruptedDataError(FormatError):
    """Raised when file data is corrupted or checksum fails."""

    pass


class ProtectionError(AntiAIError):
    """Base exception for protection-related errors."""

    pass


class AdversarialError(ProtectionError):
    """Raised when adversarial protection fails."""

    pass


class WatermarkError(ProtectionError):
    """Raised when watermark embedding/extraction fails."""

    pass


class EncryptionError(ProtectionError):
    """Raised when encryption/decryption fails."""

    pass


class ValidationError(AntiAIError):
    """Raised when validation checks fail."""

    pass


class IntegrityError(ValidationError):
    """Raised when file integrity check fails."""

    pass


class SignatureError(ValidationError):
    """Raised when signature verification fails."""

    pass


class ImageError(AntiAIError):
    """Raised for image processing errors."""

    pass


class UnsupportedImageFormatError(ImageError):
    """Raised when image format is not supported."""

    def __init__(self, format_name: str, supported_formats: list[str]) -> None:
        """
        Initialize UnsupportedImageFormatError.

        Args:
            format_name: The unsupported format name
            supported_formats: List of supported format names
        """
        message = f"Unsupported image format: {format_name}. Supported: {supported_formats}"
        super().__init__(message, {"format": format_name, "supported": supported_formats})


class ImageTooLargeError(ImageError):
    """Raised when image dimensions exceed maximum allowed."""

    def __init__(self, width: int, height: int, max_dimension: int) -> None:
        """
        Initialize ImageTooLargeError.

        Args:
            width: Image width in pixels
            height: Image height in pixels
            max_dimension: Maximum allowed dimension
        """
        message = f"Image too large: {width}x{height}. " f"Maximum dimension: {max_dimension}px"
        super().__init__(message, {"width": width, "height": height, "max": max_dimension})
