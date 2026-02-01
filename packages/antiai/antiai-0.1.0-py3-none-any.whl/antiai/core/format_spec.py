"""
AntiAI file format specification.

This module defines the binary structure of .antiAI files,
including headers, chunks, and data serialization.

Format Structure:
    [HEADER - 512 bytes]
    [METADATA CHUNK - variable]
    [WATERMARK CHUNK - variable]
    [ADVERSARIAL CHUNK - variable]
    [IMAGE DATA CHUNK - variable]
    [SIGNATURE - 256 bytes]
"""

import hashlib
import json
import struct
from dataclasses import dataclass, field
from enum import IntEnum, IntFlag
from typing import Any, ClassVar, Optional

from .exceptions import CorruptedDataError, InvalidHeaderError, VersionMismatchError

# Constants
MAGIC_BYTES: bytes = b"ANTIAI\x00\x01"
CURRENT_VERSION: int = 1
SUPPORTED_VERSIONS: list[int] = [1]
HEADER_SIZE: int = 512
SIGNATURE_SIZE: int = 32  # SHA-256 produces 32 bytes


class ProtectionFlags(IntFlag):
    """Bit flags for protection features."""

    NONE = 0
    ADVERSARIAL = 1 << 0  # bit 0
    WATERMARK = 1 << 1  # bit 1
    C2PA = 1 << 2  # bit 2
    ENCRYPTED = 1 << 3  # bit 3
    SIGNED = 1 << 4  # bit 4


class ColorMode(IntEnum):
    """Image color modes."""

    GRAYSCALE = 1
    RGB = 3
    RGBA = 4


@dataclass(frozen=True)
class AntiAIHeader:
    """
    Header structure for AntiAI files.

    The header is always 512 bytes and contains file metadata.

    Attributes:
        magic: Magic bytes for file identification (8 bytes)
        version: Format version number (2 bytes)
        width: Image width in pixels (4 bytes)
        height: Image height in pixels (4 bytes)
        channels: Number of color channels (1 byte)
        protection_level: Protection strength 0-10 (1 byte)
        flags: Protection feature flags (4 bytes)
    """

    MAGIC: ClassVar[bytes] = MAGIC_BYTES
    SIZE: ClassVar[int] = HEADER_SIZE
    STRUCT_FORMAT: ClassVar[str] = "<8sHIIBBHH"  # little-endian

    magic: bytes = field(default=MAGIC_BYTES)
    version: int = field(default=CURRENT_VERSION)
    width: int = 0
    height: int = 0
    channels: int = 3
    protection_level: int = 5
    flags: int = field(default=int(ProtectionFlags.ADVERSARIAL | ProtectionFlags.WATERMARK))
    reserved: int = 0  # For future use

    def __post_init__(self) -> None:
        """Validate header fields after initialization."""
        if self.magic != MAGIC_BYTES:
            raise InvalidHeaderError(f"Invalid magic bytes: {self.magic!r}")

        if self.version not in SUPPORTED_VERSIONS:
            raise VersionMismatchError(self.version, SUPPORTED_VERSIONS)

        if not 0 <= self.protection_level <= 10:
            raise ValueError(f"protection_level must be 0-10, got {self.protection_level}")

        if self.channels not in [1, 3, 4]:
            raise ValueError(f"channels must be 1, 3, or 4, got {self.channels}")

        if self.width <= 0 or self.height <= 0:
            raise ValueError(f"Invalid dimensions: {self.width}x{self.height}")

    def to_bytes(self) -> bytes:
        """
        Serialize header to bytes.

        Returns:
            512 bytes representing the header

        Example:
            >>> header = AntiAIHeader(width=1920, height=1080)
            >>> data = header.to_bytes()
            >>> len(data)
            512
        """
        # Pack the main structure
        packed = struct.pack(
            self.STRUCT_FORMAT,
            self.magic,
            self.version,
            self.width,
            self.height,
            self.channels,
            self.protection_level,
            self.flags,
            self.reserved,
        )

        # Pad to 512 bytes with zeros
        padding_size = self.SIZE - len(packed)
        return packed + b"\x00" * padding_size

    @classmethod
    def from_bytes(cls, data: bytes) -> "AntiAIHeader":
        """
        Deserialize header from bytes.

        Args:
            data: At least 512 bytes of header data

        Returns:
            Parsed AntiAIHeader instance

        Raises:
            InvalidHeaderError: If data is invalid
            VersionMismatchError: If version is not supported

        Example:
            >>> data = b"ANTIAI\\x00\\x01" + b"\\x00" * 504
            >>> header = AntiAIHeader.from_bytes(data)
        """
        if len(data) < cls.SIZE:
            raise InvalidHeaderError(f"Header too short: {len(data)} bytes, expected {cls.SIZE}")

        try:
            unpacked = struct.unpack(cls.STRUCT_FORMAT, data[: struct.calcsize(cls.STRUCT_FORMAT)])
        except struct.error as e:
            raise InvalidHeaderError(f"Failed to unpack header: {e}") from e

        magic, version, width, height, channels, protection, flags, reserved = unpacked

        return cls(
            magic=magic,
            version=version,
            width=width,
            height=height,
            channels=channels,
            protection_level=protection,
            flags=flags,
            reserved=reserved,
        )

    def has_flag(self, flag: ProtectionFlags) -> bool:
        """
        Check if a specific protection flag is set.

        Args:
            flag: Protection flag to check

        Returns:
            True if flag is set

        Example:
            >>> header = AntiAIHeader(width=100, height=100)
            >>> header.has_flag(ProtectionFlags.ADVERSARIAL)
            True
        """
        return bool(self.flags & flag)

    def get_color_mode(self) -> ColorMode:
        """
        Get the color mode enum.

        Returns:
            ColorMode enum value

        Example:
            >>> header = AntiAIHeader(width=100, height=100, channels=3)
            >>> header.get_color_mode()
            <ColorMode.RGB: 3>
        """
        return ColorMode(self.channels)


@dataclass
class Chunk:
    """
    Generic data chunk for AntiAI files.

    Format: [length: 4 bytes][data: length bytes]
    """

    data: bytes

    def to_bytes(self) -> bytes:
        """
        Serialize chunk to bytes with length prefix.

        Returns:
            Serialized chunk data

        Example:
            >>> chunk = Chunk(b"test data")
            >>> data = chunk.to_bytes()
            >>> len(data)
            13  # 4 bytes length + 9 bytes data
        """
        length = len(self.data)
        return struct.pack("<I", length) + self.data

    @classmethod
    def from_bytes(cls, data: bytes, offset: int = 0) -> tuple["Chunk", int]:
        """
        Deserialize chunk from bytes.

        Args:
            data: Bytes containing chunk
            offset: Starting position in data

        Returns:
            Tuple of (Chunk instance, next offset)

        Raises:
            CorruptedDataError: If chunk is malformed

        Example:
            >>> data = struct.pack("<I", 5) + b"hello"
            >>> chunk, next_offset = Chunk.from_bytes(data)
            >>> chunk.data
            b'hello'
        """
        if len(data) < offset + 4:
            raise CorruptedDataError("Not enough data for chunk length")

        length = struct.unpack("<I", data[offset : offset + 4])[0]
        chunk_start = offset + 4
        chunk_end = chunk_start + length

        if len(data) < chunk_end:
            raise CorruptedDataError(
                f"Chunk data truncated: expected {length} bytes, " f"got {len(data) - chunk_start}"
            )

        chunk_data = data[chunk_start:chunk_end]
        return cls(chunk_data), chunk_end


@dataclass
class MetadataChunk(Chunk):
    """
    Metadata chunk containing JSON-encoded information.

    This includes copyright, author, creation date, and usage terms.
    """

    @classmethod
    def from_dict(cls, metadata: dict[str, Any]) -> "MetadataChunk":
        """
        Create chunk from metadata dictionary.

        Args:
            metadata: Dictionary with metadata fields

        Returns:
            MetadataChunk instance

        Example:
            >>> meta = {"author": "Miguel", "version": "1.0"}
            >>> chunk = MetadataChunk.from_dict(meta)
        """
        json_data = json.dumps(metadata, indent=2).encode("utf-8")
        return cls(json_data)

    def to_dict(self) -> dict[str, Any]:
        """
        Parse chunk data as JSON.

        Returns:
            Dictionary with metadata

        Raises:
            CorruptedDataError: If JSON is invalid

        Example:
            >>> chunk = MetadataChunk(b'{"key": "value"}')
            >>> chunk.to_dict()
            {'key': 'value'}
        """
        try:
            return json.loads(self.data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise CorruptedDataError(f"Invalid metadata JSON: {e}") from e


def calculate_signature(data: bytes) -> bytes:
    """
    Calculate SHA-256 signature of data.

    Args:
        data: Bytes to sign

    Returns:
        32-byte SHA-256 hash

    Example:
        >>> sig = calculate_signature(b"test data")
        >>> len(sig)
        32
    """
    return hashlib.sha256(data).digest()


def verify_signature(data: bytes, signature: bytes) -> bool:
    """
    Verify SHA-256 signature of data.

    Args:
        data: Original data
        signature: Expected signature

    Returns:
        True if signature is valid

    Example:
        >>> data = b"test"
        >>> sig = calculate_signature(data)
        >>> verify_signature(data, sig)
        True
    """
    expected = calculate_signature(data)
    return signature == expected
