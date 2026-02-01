"""
Verification and validation of protected images.

Verify that protections were applied correctly and images are authentic.
"""

from pathlib import Path
from typing import Optional, Union

import numpy as np

from ..core.decoder import AntiAIDecoder
from ..core.exceptions import ValidationError
from ..detection.perceptual_hash import PerceptualHash
from ..detection.tampering import TamperingDetector
from ..protection.metadata import ImageMetadata
from ..utils.logger import logger


class ProtectionVerifier:
    """
    Verify protection and authenticity of AntiAI files.

    This class provides comprehensive verification:
    - File integrity
    - Protection presence
    - Metadata validity
    - Tampering detection

    Example:
        >>> from antiai import ProtectionVerifier
        >>> verifier = ProtectionVerifier()
        >>> result = verifier.verify("protected.antiAI")
        >>> if result['authentic']:
        ...     print("✓ Image is authentic and protected")
    """

    def __init__(self) -> None:
        """Initialize verifier."""
        self.decoder = AntiAIDecoder(verify_integrity=True)
        self.tampering_detector = TamperingDetector()
        self.hasher = PerceptualHash()
        logger.info("Initialized ProtectionVerifier")

    def verify(self, file_path: Union[str, Path]) -> dict:
        """
        Verify AntiAI file comprehensively.

        Args:
            file_path: Path to .antiAI file

        Returns:
            Dictionary with verification results

        Example:
            >>> verifier = ProtectionVerifier()
            >>> result = verifier.verify("artwork.antiAI")
            >>> result['authentic']
            True
            >>> result['protections']['adversarial']
            True
        """
        file_path = Path(file_path)
        logger.info(f"Verifying: {file_path}")

        results = {
            "authentic": False,
            "file_path": str(file_path),
            "file_exists": file_path.exists(),
            "file_integrity": False,
            "format_valid": False,
            "protections": {
                "adversarial": False,
                "watermark": False,
                "encrypted": False,
                "signed": False,
            },
            "metadata_valid": False,
            "tampering_detected": False,
            "issues": [],
        }

        if not file_path.exists():
            results["issues"].append("File not found")
            return results

        try:
            # Step 1: Decode and verify integrity
            logger.info("Step 1: Decoding and verifying integrity...")
            image, metadata = self.decoder.decode(file_path)
            results["file_integrity"] = True
            results["format_valid"] = True

            # Step 2: Verify protections
            logger.info("Step 2: Verifying protections...")
            self._verify_protections(metadata, results)

            # Step 3: Verify metadata
            logger.info("Step 3: Verifying metadata...")
            self._verify_metadata(metadata, results)

            # Step 4: Check for tampering
            logger.info("Step 4: Checking for tampering...")
            if metadata.protection.watermark:
                tampering_result = self.tampering_detector.detect(
                    image,
                    expected_watermark_hash=metadata.protection.watermark_hash or "",
                )
                results["tampering_detected"] = tampering_result["tampered"]
                if tampering_result["tampered"]:
                    results["issues"].extend(tampering_result["issues"])

            # Overall authenticity
            results["authentic"] = (
                results["file_integrity"]
                and results["format_valid"]
                and results["metadata_valid"]
                and not results["tampering_detected"]
            )

            logger.info(f"Verification complete: authentic={results['authentic']}")

        except Exception as e:
            logger.error(f"Verification failed: {e}")
            results["issues"].append(f"Verification error: {e}")

        return results

    def _verify_protections(self, metadata: ImageMetadata, results: dict) -> None:
        """Verify that protections were applied."""
        protection = metadata.protection

        results["protections"]["adversarial"] = protection.adversarial
        results["protections"]["watermark"] = protection.watermark
        results["protections"]["encrypted"] = protection.encrypted
        results["protections"]["signed"] = protection.signed

        if not (protection.adversarial or protection.watermark):
            results["issues"].append("No protections applied")

    def _verify_metadata(self, metadata: ImageMetadata, results: dict) -> None:
        """Verify metadata validity."""
        issues = []

        # Check required fields
        if not metadata.author:
            issues.append("Missing author information")

        if not metadata.copyright:
            issues.append("Missing copyright information")

        # Check protection consistency
        protection = metadata.protection
        if protection.adversarial and protection.adversarial_strength == 0:
            issues.append("Adversarial protection enabled but strength is 0")

        if protection.watermark and not protection.watermark_hash:
            issues.append("Watermark enabled but hash is missing")

        results["metadata_valid"] = len(issues) == 0
        results["issues"].extend(issues)

    def quick_verify(self, file_path: Union[str, Path]) -> bool:
        """
        Quick verification - just check if file is valid AntiAI format.

        Args:
            file_path: Path to .antiAI file

        Returns:
            True if valid, False otherwise

        Example:
            >>> verifier.quick_verify("file.antiAI")
            True
        """
        try:
            self.decoder.get_header(file_path)
            return True
        except Exception:
            return False

    def compare_images(
        self, image1: Union[str, Path, np.ndarray], image2: Union[str, Path, np.ndarray]
    ) -> dict:
        """
        Compare two images for similarity.

        Args:
            image1: First image (path or array)
            image2: Second image (path or array)

        Returns:
            Dictionary with similarity scores

        Example:
            >>> result = verifier.compare_images("img1.antiAI", "img2.jpg")
            >>> result['similarity_percent']
            87.5
        """
        # Load images
        if isinstance(image1, (str, Path)):
            img1, _ = self.decoder.decode(image1)
        else:
            img1 = image1

        if isinstance(image2, (str, Path)):
            if str(image2).endswith(".antiAI"):
                img2, _ = self.decoder.decode(image2)
            else:
                from ..utils.image_ops import load_image

                img2, _ = load_image(image2)
        else:
            img2 = image2

        # Compute hashes
        hashes1 = self.hasher.compute_all(img1)
        hashes2 = self.hasher.compute_all(img2)

        # Calculate similarities
        similarities = {}
        for hash_type in ["ahash", "dhash", "phash"]:
            similarity = self.hasher.similarity_score(hashes1[hash_type], hashes2[hash_type])
            similarities[hash_type] = similarity

        # Average similarity
        avg_similarity = sum(similarities.values()) / len(similarities)

        return {
            "similarity_percent": avg_similarity,
            "similarities_by_type": similarities,
            "likely_same_image": avg_similarity > 90,
            "likely_modified": 70 < avg_similarity <= 90,
            "likely_different": avg_similarity <= 70,
        }
