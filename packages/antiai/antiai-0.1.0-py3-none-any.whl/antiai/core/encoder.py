"""
AntiAI file encoder.

This module provides the main encoder class for creating .antiAI files
from standard images, applying protection mechanisms and embedding metadata.
"""

import struct
from io import BytesIO
from pathlib import Path
from typing import Any, Optional, Union

import numpy as np
from PIL import Image

from ..protection.adversarial import AdversarialProtection
from ..protection.metadata import AuthorInfo, ImageMetadata, MetadataBuilder
from ..protection.watermark import InvisibleWatermark
from ..utils.image_ops import array_to_bytes, load_image
from ..utils.logger import logger
from .exceptions import ImageError
from .format_spec import (
    AntiAIHeader,
    Chunk,
    MetadataChunk,
    ProtectionFlags,
    calculate_signature,
)


class AntiAIEncoder:
    """
    Encoder for creating .antiAI protected image files.

    This class orchestrates the entire encoding process:
    1. Load and validate input image
    2. Apply adversarial protection
    3. Embed invisible watermark
    4. Create metadata
    5. Serialize to .antiAI format

    Example:
        >>> from antiai import AntiAIEncoder
        >>> encoder = AntiAIEncoder()
        >>> stats = encoder.encode(
        ...     input_image="artwork.jpg",
        ...     output_path="artwork.antiAI",
        ...     author="Miguel",
        ...     protection_level=7
        ... )
        >>> print(f"Created: {stats['output_file']['path']}")
    """

    def __init__(
        self,
        use_cuda: bool = True,
        adversarial_strength: Optional[int] = None,
        watermark_strength: float = 0.1,
    ) -> None:
        """
        Initialize encoder.

        Args:
            use_cuda: Use CUDA acceleration if available
            adversarial_strength: Override default adversarial strength
            watermark_strength: Watermark embedding strength (0.01-0.5)

        Example:
            >>> encoder = AntiAIEncoder(use_cuda=True)
        """
        self.use_cuda = use_cuda
        self.default_adversarial_strength = adversarial_strength
        self.watermark_strength = watermark_strength

        # Will be initialized on first use
        self._adversarial: Optional[AdversarialProtection] = None
        self._watermark: Optional[InvisibleWatermark] = None

        logger.info("AntiAI Encoder initialized")

    def encode(
        self,
        input_image: Union[str, Path],
        output_path: Union[str, Path],
        author: str,
        protection_level: int = 5,
        watermark_data: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        copyright_statement: Optional[str] = None,
        license_type: str = "All Rights Reserved",
        usage_terms: Optional[str] = None,
        **custom_metadata: Any,
    ) -> dict:
        """
        Encode image to .antiAI format with protection.

        Args:
            input_image: Path to input image file
            output_path: Path for output .antiAI file
            author: Name of the content creator
            protection_level: Protection strength 0-10 (default: 5)
            watermark_data: Custom watermark data (default: auto-generated)
            title: Image title (optional)
            description: Image description (optional)
            copyright_statement: Copyright statement (optional)
            license_type: License type (default: "All Rights Reserved")
            usage_terms: Detailed usage terms (optional)
            **custom_metadata: Additional custom metadata fields

        Returns:
            Dictionary with encoding statistics and metadata

        Raises:
            ImageError: If input image cannot be processed
            ValueError: If parameters are invalid

        Example:
            >>> encoder = AntiAIEncoder()
            >>> stats = encoder.encode(
            ...     input_image="photo.jpg",
            ...     output_path="photo.antiAI",
            ...     author="Miguel",
            ...     protection_level=8,
            ...     title="Beautiful Sunset",
            ...     description="Original photograph taken in 2025"
            ... )
        """
        logger.info(f"Starting encoding: {input_image} -> {output_path}")

        # Validate parameters
        if not 0 <= protection_level <= 10:
            raise ValueError(f"protection_level must be 0-10, got {protection_level}")

        input_path = Path(input_image)
        output_path = Path(output_path)

        # Statistics dictionary
        stats = {
            "input_file": str(input_path),
            "output_file": str(output_path),
            "protection_level": protection_level,
        }

        # Step 1: Load image
        logger.info("[1/6] Loading input image...")
        img_array, img_pil = load_image(input_path)
        height, width = img_array.shape[:2]
        channels = img_array.shape[2] if img_array.ndim == 3 else 1

        stats["input_dimensions"] = {"width": width, "height": height, "channels": channels}

        # Step 2: Apply adversarial protection
        logger.info(f"[2/6] Applying adversarial protection (level {protection_level})...")
        protected_img, adv_metadata = self._apply_adversarial(img_array, protection_level)
        stats["adversarial"] = adv_metadata

        # Step 3: Embed watermark
        logger.info("[3/6] Embedding invisible watermark...")
        if watermark_data is None:
            from datetime import datetime

            watermark_data = f"{author}_{datetime.now().timestamp()}"

        watermarked_img, wm_metadata = self._apply_watermark(protected_img, watermark_data)
        stats["watermark"] = wm_metadata

        # Step 4: Build metadata
        logger.info("[4/6] Creating metadata...")
        metadata = self._build_metadata(
            author=author,
            title=title,
            description=description,
            copyright_statement=copyright_statement,
            license_type=license_type,
            usage_terms=usage_terms,
            original_filename=input_path.name,
            original_format=img_pil.format,
            width=width,
            height=height,
            channels=channels,
            adversarial_strength=protection_level,
            watermark_hash=wm_metadata["watermark_hash"],
            custom_metadata=custom_metadata,
        )
        stats["metadata"] = metadata.to_dict()

        # Step 5: Serialize to .antiAI format
        logger.info("[5/6] Serializing to .antiAI format...")
        self._write_antiai_file(
            output_path=output_path,
            image_array=watermarked_img,
            metadata=metadata,
            protection_level=protection_level,
        )

        # Step 6: Calculate final statistics
        logger.info("[6/6] Finalizing...")
        output_size = output_path.stat().st_size
        stats["output_size_bytes"] = output_size
        stats["output_size_mb"] = output_size / (1024 * 1024)

        input_size = input_path.stat().st_size
        stats["size_increase_percent"] = ((output_size - input_size) / input_size) * 100

        logger.info(
            f"✅ Encoding complete: {output_path} "
            f"({stats['output_size_mb']:.2f} MB, "
            f"+{stats['size_increase_percent']:.1f}%)"
        )

        return stats

    def _apply_adversarial(self, image: np.ndarray, strength: int) -> tuple[np.ndarray, dict]:
        """Apply adversarial protection to image."""
        if self._adversarial is None or self._adversarial.config.strength != strength:
            self._adversarial = AdversarialProtection(strength=strength, use_cuda=self.use_cuda)

        return self._adversarial.protect(image)

    def _apply_watermark(self, image: np.ndarray, watermark_data: str) -> tuple[np.ndarray, dict]:
        """Apply invisible watermark to image."""
        if self._watermark is None:
            self._watermark = InvisibleWatermark(strength=self.watermark_strength)

        return self._watermark.embed(image, watermark_data)

    def _build_metadata(
        self,
        author: str,
        title: Optional[str],
        description: Optional[str],
        copyright_statement: Optional[str],
        license_type: str,
        usage_terms: Optional[str],
        original_filename: str,
        original_format: Optional[str],
        width: int,
        height: int,
        channels: int,
        adversarial_strength: int,
        watermark_hash: str,
        custom_metadata: dict,
    ) -> ImageMetadata:
        """Build metadata object."""
        from datetime import datetime

        # Build metadata using builder pattern
        builder = (
            MetadataBuilder()
            .set_author(author)
            .set_original_file_info(filename=original_filename, format=original_format)
            .set_dimensions(width, height)
            .set_color_mode("RGB" if channels == 3 else "RGBA" if channels == 4 else "L")
            .enable_adversarial(adversarial_strength)
            .enable_watermark(watermark_hash)
        )

        if title:
            builder.set_title(title)

        if description:
            builder.set_description(description)

        # Copyright
        if copyright_statement is None:
            copyright_statement = f"© {datetime.now().year} {author}"

        builder.set_copyright(
            statement=copyright_statement, license=license_type, usage_terms=usage_terms
        )

        # Add custom fields
        for key, value in custom_metadata.items():
            builder.add_custom(key, value)

        return builder.build()

    def _write_antiai_file(
        self,
        output_path: Path,
        image_array: np.ndarray,
        metadata: ImageMetadata,
        protection_level: int,
    ) -> None:
        """Write complete .antiAI file."""
        # Create header
        height, width = image_array.shape[:2]
        channels = image_array.shape[2] if image_array.ndim == 3 else 1

        header = AntiAIHeader(
            width=width,
            height=height,
            channels=channels,
            protection_level=protection_level,
            flags=int(ProtectionFlags.ADVERSARIAL | ProtectionFlags.WATERMARK),
        )

        # Create metadata chunk
        metadata_chunk = MetadataChunk.from_dict(metadata.to_dict())

        # Create image data chunk (PNG compressed)
        image_data = array_to_bytes(image_array, format="PNG", compress_level=6)
        image_chunk = Chunk(image_data)

        # Assemble file data
        file_data = BytesIO()

        # Write header
        header_bytes = header.to_bytes()
        file_data.write(header_bytes)

        # Write metadata chunk
        metadata_bytes = metadata_chunk.to_bytes()
        file_data.write(metadata_bytes)

        # Write image chunk
        image_chunk_bytes = image_chunk.to_bytes()
        file_data.write(image_chunk_bytes)

        # Calculate signature over all data
        data_to_sign = file_data.getvalue()
        signature = calculate_signature(data_to_sign)

        # Write to file
        with open(output_path, "wb") as f:
            f.write(data_to_sign)
            f.write(signature)

        logger.info(f"Written {len(data_to_sign) + len(signature)} bytes to {output_path}")

    def encode_batch(
        self,
        input_images: list[Union[str, Path]],
        output_dir: Union[str, Path],
        author: str,
        protection_level: int = 5,
        **common_metadata: Any,
    ) -> list[dict]:
        """
        Encode multiple images in batch.

        Args:
            input_images: List of input image paths
            output_dir: Output directory for .antiAI files
            author: Author name
            protection_level: Protection level for all images
            **common_metadata: Common metadata for all images

        Returns:
            List of statistics dictionaries for each image

        Example:
            >>> encoder = AntiAIEncoder()
            >>> images = ["photo1.jpg", "photo2.jpg", "photo3.jpg"]
            >>> results = encoder.encode_batch(
            ...     input_images=images,
            ...     output_dir="protected/",
            ...     author="Miguel",
            ...     protection_level=6
            ... )
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results = []

        logger.info(f"Starting batch encoding: {len(input_images)} images")

        for i, input_image in enumerate(input_images, 1):
            input_path = Path(input_image)
            output_path = output_dir / f"{input_path.stem}.antiAI"

            logger.info(f"[{i}/{len(input_images)}] Processing {input_path.name}...")

            try:
                stats = self.encode(
                    input_image=input_path,
                    output_path=output_path,
                    author=author,
                    protection_level=protection_level,
                    **common_metadata,
                )
                stats["success"] = True
                results.append(stats)

            except Exception as e:
                logger.error(f"Failed to encode {input_path}: {e}")
                results.append({"input_file": str(input_path), "success": False, "error": str(e)})

        success_count = sum(1 for r in results if r.get("success", False))
        logger.info(f"Batch encoding complete: {success_count}/{len(input_images)} successful")

        return results
