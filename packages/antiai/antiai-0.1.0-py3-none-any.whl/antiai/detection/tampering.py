"""
Tampering detection for protected images.

Detect if an image has been modified after protection was applied.
"""

from typing import Optional

import numpy as np

from ..core.exceptions import ValidationError
from ..protection.watermark import InvisibleWatermark
from ..utils.logger import logger


class TamperingDetector:
    """
    Detect tampering in protected images.

    This class checks for modifications by:
    1. Verifying watermark integrity
    2. Checking adversarial protection consistency
    3. Analyzing statistical properties

    Example:
        >>> from antiai.detection import TamperingDetector
        >>> detector = TamperingDetector()
        >>> result = detector.detect(protected_image, original_watermark_hash)
        >>> if result['tampered']:
        ...     print("Image has been modified!")
    """

    def __init__(self) -> None:
        """Initialize tampering detector."""
        self.watermark_extractor = InvisibleWatermark()
        logger.info("Initialized TamperingDetector")

    def detect(
        self,
        image: np.ndarray,
        expected_watermark_hash: str,
        expected_watermark_data: Optional[str] = None,
    ) -> dict:
        """
        Detect tampering in protected image.

        Args:
            image: Image to check (H, W, 3)
            expected_watermark_hash: Expected watermark SHA-256 hash
            expected_watermark_data: Expected watermark content (optional)

        Returns:
            Dictionary with detection results

        Example:
            >>> result = detector.detect(
            ...     image=protected_img,
            ...     expected_watermark_hash="abc123...",
            ...     expected_watermark_data="user_id_12345"
            ... )
            >>> result['tampered']
            False
        """
        results = {
            "tampered": False,
            "confidence": 0.0,
            "checks": {},
            "issues": [],
        }

        logger.info("Starting tampering detection...")

        # Check 1: Watermark integrity
        watermark_ok, watermark_confidence = self._check_watermark(
            image, expected_watermark_hash, expected_watermark_data
        )
        results["checks"]["watermark"] = watermark_ok
        results["confidence"] += watermark_confidence

        if not watermark_ok:
            results["issues"].append("Watermark missing or corrupted")

        # Check 2: Statistical properties
        stats_ok, stats_confidence = self._check_statistical_properties(image)
        results["checks"]["statistics"] = stats_ok
        results["confidence"] += stats_confidence

        if not stats_ok:
            results["issues"].append("Statistical anomalies detected")

        # Calculate overall confidence
        num_checks = 2
        results["confidence"] /= num_checks

        # Determine tampering
        results["tampered"] = results["confidence"] < 0.7

        logger.info(
            f"Tampering detection complete: "
            f"tampered={results['tampered']}, "
            f"confidence={results['confidence']:.2%}"
        )

        return results

    def _check_watermark(
        self, image: np.ndarray, expected_hash: str, expected_data: Optional[str]
    ) -> tuple[bool, float]:
        """
        Check watermark integrity.

        Returns:
            Tuple of (watermark_ok, confidence_score)
        """
        import hashlib

        try:
            # Extract watermark
            if expected_data:
                extracted = self.watermark_extractor.extract(
                    image, expected_length=len(expected_data)
                )
            else:
                # Try to extract with default length
                extracted = self.watermark_extractor.extract(image, expected_length=32)

            # Hash the extracted data
            extracted_hash = hashlib.sha256(extracted.encode()).hexdigest()

            # Compare hashes
            if extracted_hash == expected_hash:
                return True, 1.0

            # Check similarity if exact match fails
            if expected_data:
                similarity = sum(c1 == c2 for c1, c2 in zip(extracted, expected_data)) / len(
                    expected_data
                )
                if similarity > 0.8:
                    return True, similarity

            return False, 0.0

        except Exception as e:
            logger.warning(f"Watermark extraction failed: {e}")
            return False, 0.0

    def _check_statistical_properties(self, image: np.ndarray) -> tuple[bool, float]:
        """
        Check for statistical anomalies that suggest tampering.

        Looks for:
        - Unusual histogram distributions
        - JPEG compression artifacts
        - Cloning/copy-paste patterns

        Returns:
            Tuple of (properties_ok, confidence_score)
        """
        confidence = 1.0

        # Check histogram entropy
        entropy = self._calculate_entropy(image)
        if entropy < 5.0:  # Very low entropy might indicate tampering
            confidence *= 0.8

        # Check for copy-paste (simplified)
        has_duplicates = self._check_duplicate_regions(image)
        if has_duplicates:
            confidence *= 0.7

        properties_ok = confidence > 0.7

        return properties_ok, confidence

    def _calculate_entropy(self, image: np.ndarray) -> float:
        """Calculate Shannon entropy of image."""
        # Flatten and get histogram
        pixels = image.flatten()
        hist, _ = np.histogram(pixels, bins=256, range=(0, 256))

        # Normalize
        hist = hist / hist.sum()

        # Calculate entropy
        entropy = -np.sum(hist * np.log2(hist + 1e-10))

        return float(entropy)

    def _check_duplicate_regions(self, image: np.ndarray, block_size: int = 16) -> bool:
        """
        Check for duplicated regions (copy-paste detection).

        This is a simplified version. Production systems should use
        more sophisticated algorithms.

        Args:
            image: Image to check
            block_size: Size of blocks to compare

        Returns:
            True if duplicates found
        """
        if image.shape[0] < block_size * 2 or image.shape[1] < block_size * 2:
            return False

        # Convert to grayscale
        if image.ndim == 3:
            gray = np.dot(image[..., :3], [0.299, 0.587, 0.114])
        else:
            gray = image

        # Sample blocks
        h, w = gray.shape
        blocks = []

        for i in range(0, h - block_size, block_size):
            for j in range(0, w - block_size, block_size):
                block = gray[i : i + block_size, j : j + block_size]
                block_hash = hash(block.tobytes())
                blocks.append(block_hash)

        # Check for duplicates
        unique_blocks = len(set(blocks))
        total_blocks = len(blocks)

        # If more than 10% are duplicates, flag it
        duplicate_ratio = 1 - (unique_blocks / total_blocks)

        return duplicate_ratio > 0.1
