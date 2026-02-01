"""
AntiAI file decoder.

This module provides the decoder class for reading .antiAI files,
extracting protected images and metadata.
"""

from pathlib import Path
from typing import Tuple, Union

import numpy as np

from ..protection.metadata import ImageMetadata
from ..utils.image_ops import bytes_to_array
from ..utils.logger import logger
from .exceptions import CorruptedDataError, IntegrityError
from .format_spec import (
    AntiAIHeader,
    Chunk,
    MetadataChunk,
    SIGNATURE_SIZE,
    verify_signature,
)


class AntiAIDecoder:
    """
    Decoder for reading .antiAI protected image files.

    This class handles:
    1. File validation and integrity checking
    2. Header parsing
    3. Metadata extraction
    4. Image data decompression

    Example:
        >>> from antiai import AntiAIDecoder
        >>> decoder = AntiAIDecoder()
        >>> image, metadata = decoder.decode("artwork.antiAI")
        >>> print(f"Author: {metadata.author.name}")
        >>> print(f"Dimensions: {image.shape}")
    """

    def __init__(self, verify_integrity: bool = True) -> None:
        """
        Initialize decoder.

        Args:
            verify_integrity: Verify file signature on decode (default: True)

        Example:
            >>> decoder = AntiAIDecoder(verify_integrity=True)
        """
        self.verify_integrity = verify_integrity
        logger.info("AntiAI Decoder initialized")

    def decode(self, input_path: Union[str, Path]) -> Tuple[np.ndarray, ImageMetadata]:
        """
        Decode .antiAI file to image and metadata.

        Args:
            input_path: Path to .antiAI file

        Returns:
            Tuple of (image_array, metadata)

        Raises:
            InvalidHeaderError: If file header is invalid
            CorruptedDataError: If file data is corrupted
            IntegrityError: If signature verification fails

        Example:
            >>> decoder = AntiAIDecoder()
            >>> image, metadata = decoder.decode("protected.antiAI")
            >>> image.shape
            (1080, 1920, 3)
            >>> metadata.author.name
            'Miguel'
        """
        input_path = Path(input_path)

        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")

        logger.info(f"Decoding: {input_path}")

        # Read entire file
        with open(input_path, "rb") as f:
            file_data = f.read()

        logger.info(f"Read {len(file_data)} bytes")

        # Verify signature if enabled
        if self.verify_integrity:
            logger.info("Verifying file integrity...")
            self._verify_file_integrity(file_data)

        # Parse header
        logger.info("Parsing header...")
        header = AntiAIHeader.from_bytes(file_data)

        logger.info(
            f"Header: {header.width}x{header.height}, "
            f"{header.channels} channels, "
            f"protection level {header.protection_level}"
        )

        # Parse metadata chunk
        logger.info("Parsing metadata...")
        metadata_chunk, offset = MetadataChunk.from_bytes(file_data, offset=AntiAIHeader.SIZE)
        metadata = ImageMetadata.from_dict(metadata_chunk.to_dict())

        # Parse image data chunk
        logger.info("Extracting image data...")
        image_chunk, offset = Chunk.from_bytes(file_data, offset=offset)

        # Decompress image
        image_array = bytes_to_array(image_chunk.data)

        # Validate dimensions match header
        if image_array.shape[:2] != (header.height, header.width):
            raise CorruptedDataError(
                f"Image dimensions mismatch: "
                f"header says {header.width}x{header.height}, "
                f"got {image_array.shape[1]}x{image_array.shape[0]}"
            )

        logger.info(f"✅ Decoding complete: {image_array.shape}")

        return image_array, metadata

    def _verify_file_integrity(self, file_data: bytes) -> None:
        """
        Verify file integrity using signature.

        Args:
            file_data: Complete file data

        Raises:
            IntegrityError: If signature is invalid
            CorruptedDataError: If file is too short
        """
        if len(file_data) < SIGNATURE_SIZE:
            raise CorruptedDataError(
                f"File too short: {len(file_data)} bytes, " f"minimum {SIGNATURE_SIZE}"
            )

        # Split data and signature
        data = file_data[:-SIGNATURE_SIZE]
        signature = file_data[-SIGNATURE_SIZE:]

        # Verify
        if not verify_signature(data, signature):
            raise IntegrityError(
                "File integrity check failed: signature mismatch. "
                "File may be corrupted or tampered with."
            )

        logger.info("✓ File integrity verified")

    def get_metadata_only(self, input_path: Union[str, Path]) -> ImageMetadata:
        """
        Extract only metadata without decompressing image.

        This is faster when you only need metadata information.

        Args:
            input_path: Path to .antiAI file

        Returns:
            ImageMetadata object

        Example:
            >>> decoder = AntiAIDecoder()
            >>> metadata = decoder.get_metadata_only("artwork.antiAI")
            >>> print(metadata.title)
        """
        input_path = Path(input_path)

        with open(input_path, "rb") as f:
            # Read header + enough for metadata (estimate 64KB should be plenty)
            file_data = f.read(AntiAIHeader.SIZE + 65536)

        # Parse header (validates file)
        header = AntiAIHeader.from_bytes(file_data)

        # Parse metadata chunk
        metadata_chunk, _ = MetadataChunk.from_bytes(file_data, offset=AntiAIHeader.SIZE)
        metadata = ImageMetadata.from_dict(metadata_chunk.to_dict())

        return metadata

    def get_header(self, input_path: Union[str, Path]) -> AntiAIHeader:
        """
        Extract only file header.

        Args:
            input_path: Path to .antiAI file

        Returns:
            AntiAIHeader object

        Example:
            >>> decoder = AntiAIDecoder()
            >>> header = decoder.get_header("image.antiAI")
            >>> print(f"{header.width}x{header.height}")
        """
        input_path = Path(input_path)

        with open(input_path, "rb") as f:
            header_data = f.read(AntiAIHeader.SIZE)

        return AntiAIHeader.from_bytes(header_data)

    def decode_to_file(
        self, input_path: Union[str, Path], output_path: Union[str, Path], format: str = "PNG"
    ) -> ImageMetadata:
        """
        Decode .antiAI file and save image to standard format.

        Note: This removes all protections. The output image will be a
        standard unprotected image file.

        Args:
            input_path: Path to .antiAI file
            output_path: Path for output image file
            format: Output format (PNG, JPEG, etc.)

        Returns:
            Extracted metadata

        Example:
            >>> decoder = AntiAIDecoder()
            >>> metadata = decoder.decode_to_file(
            ...     "protected.antiAI",
            ...     "unprotected.png",
            ...     format="PNG"
            ... )
        """
        from ..utils.image_ops import save_image

        # Decode
        image_array, metadata = self.decode(input_path)

        # Save
        save_image(image_array, output_path, format=format)

        logger.info(f"Saved unprotected image to {output_path}")

        return metadata
