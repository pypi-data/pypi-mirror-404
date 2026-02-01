"""
Invisible watermarking using DWT-DCT.

This module implements robust invisible watermarking that survives
common image manipulations like compression, resizing, and filtering.

The watermark uses:
- DWT (Discrete Wavelet Transform) for frequency domain representation
- DCT (Discrete Cosine Transform) for embedding in mid-frequencies
- Differential encoding for blind extraction (no reference needed)
- Repetition coding for error tolerance

Algorithm based on:
- Cox et al.: Secure Spread Spectrum Watermarking for Multimedia
- Al-Haj: Combined DWT-DCT Digital Image Watermarking
"""

import hashlib
from typing import Optional, Tuple

import numpy as np
import pywt
from scipy.fftpack import dct, idct
from scipy.ndimage import zoom

from ..core.exceptions import WatermarkError
from ..utils.image_ops import rgb_to_grayscale
from ..utils.logger import logger

# Constants for differential embedding
SYNC_PATTERN = [1, 0, 1, 1, 0, 0, 1, 0]  # 8-bit sync marker for alignment
REPETITION_FACTOR = 3  # Each bit embedded 3 times for error correction


class InvisibleWatermark:
    """
    Robust invisible watermark embedding and extraction.

    The watermark is embedded in the mid-frequency DCT coefficients
    of the DWT decomposition, making it resistant to common attacks
    while remaining imperceptible.

    Example:
        >>> from antiai.protection import InvisibleWatermark
        >>> import numpy as np
        >>> watermarker = InvisibleWatermark(strength=0.1)
        >>> image = np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)
        >>> watermark_data = "unique_user_id_12345"
        >>> marked, metadata = watermarker.embed(image, watermark_data)
    """

    def __init__(self, strength: float = 0.1, wavelet: str = "haar") -> None:
        """
        Initialize watermarker.

        Args:
            strength: Embedding strength (0.01-0.5, default 0.1)
            wavelet: Wavelet type for DWT (default 'haar')

        Raises:
            ValueError: If parameters are invalid
        """
        if not 0 < strength <= 0.5:
            raise ValueError(f"strength must be in (0, 0.5], got {strength}")

        if wavelet not in pywt.wavelist():
            raise ValueError(f"Invalid wavelet: {wavelet}")

        self.strength = strength
        self.wavelet = wavelet

        logger.info(f"Initialized watermark (strength={strength}, wavelet={wavelet})")

    def embed(self, image: np.ndarray, watermark_data: str) -> Tuple[np.ndarray, dict]:
        """
        Embed invisible watermark in image.

        Args:
            image: RGB image array (H, W, 3) in range [0, 255]
            watermark_data: String to embed (e.g., user ID, hash)

        Returns:
            Tuple of (watermarked_image, metadata)

        Raises:
            WatermarkError: If embedding fails

        Example:
            >>> img = np.ones((256, 256, 3), dtype=np.uint8) * 128
            >>> marked, meta = watermarker.embed(img, "user123")
            >>> meta['watermark_hash'][:8]
            'a665a45e'
        """
        try:
            logger.info(f"Embedding watermark (data length: {len(watermark_data)})")

            if image.ndim != 3 or image.shape[2] != 3:
                raise WatermarkError(f"Expected RGB image (H, W, 3), got {image.shape}")

            # Convert watermark string to bits
            watermark_bits = self._string_to_bits(watermark_data)

            # Check if image is large enough for watermark
            min_size = int(np.sqrt(len(watermark_bits))) * 8
            if min(image.shape[:2]) < min_size:
                raise WatermarkError(
                    f"Image too small for watermark. "
                    f"Minimum {min_size}x{min_size}, got {image.shape[:2]}"
                )

            # Convert to grayscale for watermarking (luminance channel)
            y_channel = rgb_to_grayscale(image).astype(np.float32)

            # Apply DWT
            coeffs = pywt.dwt2(y_channel, self.wavelet)
            LL, (LH, HL, HH) = coeffs

            # Apply DCT to LL subband
            dct_ll = self._dct2d(LL)

            # Embed watermark bits
            watermarked_dct = self._embed_bits(dct_ll, watermark_bits)

            # Reconstruct
            watermarked_ll = self._idct2d(watermarked_dct)
            watermarked_y = pywt.idwt2((watermarked_ll, (LH, HL, HH)), self.wavelet)

            # Handle size mismatch from DWT
            if watermarked_y.shape != y_channel.shape:
                watermarked_y = self._resize_to_match(watermarked_y, y_channel.shape)

            # Apply changes to RGB image
            watermarked_image = self._apply_luminance_change(
                image.astype(np.float32), y_channel, watermarked_y
            )

            # Clip and convert to uint8
            watermarked_image = np.clip(watermarked_image, 0, 255).astype(np.uint8)

            # Calculate watermark hash
            wm_hash = hashlib.sha256(watermark_data.encode()).hexdigest()

            metadata = {
                "algorithm": "dwt_dct_v1",
                "strength": self.strength,
                "wavelet": self.wavelet,
                "watermark_hash": wm_hash,
                "watermark_length": len(watermark_data),
                "bits_embedded": len(watermark_bits),
            }

            logger.info(f"Watermark embedded successfully (hash: {wm_hash[:16]}...)")

            return watermarked_image, metadata

        except Exception as e:
            raise WatermarkError(f"Failed to embed watermark: {e}") from e

    def extract(self, image: np.ndarray, expected_length: Optional[int] = None) -> str:
        """
        Extract watermark from image.

        Args:
            image: Watermarked image array (H, W, 3)
            expected_length: Expected watermark length in characters (optional)

        Returns:
            Extracted watermark string

        Raises:
            WatermarkError: If extraction fails

        Example:
            >>> extracted = watermarker.extract(marked_image)
            >>> extracted == "user123"
            True
        """
        try:
            logger.info("Extracting watermark from image")

            if image.ndim != 3 or image.shape[2] != 3:
                raise WatermarkError(f"Expected RGB image (H, W, 3), got {image.shape}")

            # Convert to grayscale
            y_channel = rgb_to_grayscale(image).astype(np.float32)

            # Apply DWT
            coeffs = pywt.dwt2(y_channel, self.wavelet)
            LL, _ = coeffs

            # Apply DCT
            dct_ll = self._dct2d(LL)

            # Extract bits
            if expected_length:
                num_bits = expected_length * 8
            else:
                # Extract maximum possible bits
                num_bits = self._get_max_embeddable_bits(dct_ll.shape)

            extracted_bits = self._extract_bits(dct_ll, num_bits)

            # Convert bits to string
            watermark_data = self._bits_to_string(extracted_bits)

            logger.info(f"Watermark extracted (length: {len(watermark_data)})")

            return watermark_data

        except Exception as e:
            raise WatermarkError(f"Failed to extract watermark: {e}") from e

    def _string_to_bits(self, s: str) -> list[int]:
        """Convert string to list of bits."""
        bits = []
        for char in s:
            # Convert character to 8-bit binary
            char_bits = format(ord(char), "08b")
            bits.extend([int(b) for b in char_bits])
        return bits

    def _bits_to_string(self, bits: list[int]) -> str:
        """Convert list of bits to string."""
        chars = []
        for i in range(0, len(bits), 8):
            byte = bits[i : i + 8]
            if len(byte) == 8:
                try:
                    char_code = int("".join(map(str, byte)), 2)
                    if 0 <= char_code <= 127:  # ASCII range
                        chars.append(chr(char_code))
                except ValueError:
                    continue
        return "".join(chars)

    def _dct2d(self, block: np.ndarray) -> np.ndarray:
        """Apply 2D DCT."""
        return dct(dct(block.T, norm="ortho").T, norm="ortho")

    def _idct2d(self, block: np.ndarray) -> np.ndarray:
        """Apply 2D inverse DCT."""
        return idct(idct(block.T, norm="ortho").T, norm="ortho")

    def _get_coefficient_pairs(self, shape: Tuple[int, int]) -> list[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        Get pairs of positions for differential embedding.

        Uses mid-frequency DCT coefficients. Each bit is embedded using
        the relationship between two adjacent coefficients, enabling
        blind extraction without the original image.

        Returns:
            List of ((i1, j1), (i2, j2)) coordinate pairs
        """
        h, w = shape
        pairs = []

        # Dynamic range based on image size
        start = max(4, min(h, w) // 32)
        end_h = min(h // 2, 64)
        end_w = min(w // 2, 64)

        # Create pairs of adjacent mid-frequency coefficients
        for i in range(start, end_h - 1):
            for j in range(start, end_w - 1):
                # Skip very low frequencies (too visible) and diagonal
                if i + j > start * 2:
                    # Pair horizontally adjacent coefficients
                    pairs.append(((i, j), (i, j + 1)))

        return pairs

    def _get_max_embeddable_bits(self, shape: Tuple[int, int]) -> int:
        """Calculate maximum number of data bits that can be embedded."""
        pairs = self._get_coefficient_pairs(shape)
        # Account for sync pattern and repetition factor
        raw_capacity = len(pairs)
        return (raw_capacity - len(SYNC_PATTERN)) // REPETITION_FACTOR

    def _prepare_payload(self, bits: list[int]) -> list[int]:
        """
        Prepare payload with sync pattern and repetition coding.

        Args:
            bits: Original data bits

        Returns:
            Encoded payload with sync marker and redundancy
        """
        # Add sync pattern at the beginning
        payload = list(SYNC_PATTERN)

        # Add data bits with repetition for error correction
        for bit in bits:
            payload.extend([bit] * REPETITION_FACTOR)

        return payload

    def _embed_bits(self, dct_block: np.ndarray, bits: list[int]) -> np.ndarray:
        """
        Embed bits using differential quantization.

        For each bit, modifies the relationship between two adjacent
        DCT coefficients:
        - bit 1: coefficient1 > coefficient2
        - bit 0: coefficient2 > coefficient1

        This enables blind extraction by comparing coefficient pairs.

        Args:
            dct_block: DCT coefficients
            bits: Bits to embed (raw data, will be encoded)

        Returns:
            Modified DCT block with embedded watermark
        """
        watermarked = dct_block.copy()
        pairs = self._get_coefficient_pairs(dct_block.shape)

        # Prepare payload with sync and redundancy
        payload = self._prepare_payload(bits)

        if len(payload) > len(pairs):
            raise WatermarkError(
                f"Too many bits to embed: {len(bits)} data bits "
                f"({len(payload)} with encoding), only {len(pairs)} positions available"
            )

        for idx, bit in enumerate(payload):
            (i1, j1), (i2, j2) = pairs[idx]

            c1 = watermarked[i1, j1]
            c2 = watermarked[i2, j2]

            # Calculate minimum delta for robust embedding
            avg_magnitude = (abs(c1) + abs(c2)) / 2
            delta = max(self.strength * avg_magnitude, self.strength * 20)

            if bit == 1:
                # Ensure c1 > c2 with margin delta
                if c1 <= c2 + delta:
                    adjustment = (c2 + delta - c1) / 2 + delta / 2
                    watermarked[i1, j1] = c1 + adjustment
                    watermarked[i2, j2] = c2 - adjustment
            else:
                # Ensure c2 > c1 with margin delta
                if c2 <= c1 + delta:
                    adjustment = (c1 + delta - c2) / 2 + delta / 2
                    watermarked[i1, j1] = c1 - adjustment
                    watermarked[i2, j2] = c2 + adjustment

        return watermarked

    def _extract_bits(self, dct_block: np.ndarray, num_data_bits: int) -> list[int]:
        """
        Extract bits using differential comparison.

        Compares pairs of coefficients to recover embedded bits.
        Uses majority voting over repeated bits for error correction.

        Args:
            dct_block: DCT coefficients
            num_data_bits: Expected number of data bits to extract

        Returns:
            Extracted data bits
        """
        pairs = self._get_coefficient_pairs(dct_block.shape)

        # First extract raw bits from all pairs
        raw_bits = []
        for (i1, j1), (i2, j2) in pairs:
            c1 = dct_block[i1, j1]
            c2 = dct_block[i2, j2]
            raw_bits.append(1 if c1 > c2 else 0)

        # Find sync pattern
        sync_position = self._find_sync_pattern(raw_bits)
        if sync_position < 0:
            logger.warning("Sync pattern not found, extraction may be unreliable")
            sync_position = 0

        # Extract data bits after sync pattern
        data_start = sync_position + len(SYNC_PATTERN)
        data_bits = []

        # Apply majority voting over repeated bits
        num_to_extract = min(num_data_bits, (len(raw_bits) - data_start) // REPETITION_FACTOR)

        for i in range(num_to_extract):
            start_idx = data_start + i * REPETITION_FACTOR
            end_idx = start_idx + REPETITION_FACTOR

            if end_idx <= len(raw_bits):
                repeated_bits = raw_bits[start_idx:end_idx]
                # Majority vote
                bit = 1 if sum(repeated_bits) > REPETITION_FACTOR // 2 else 0
                data_bits.append(bit)

        return data_bits

    def _find_sync_pattern(self, bits: list[int]) -> int:
        """
        Find the sync pattern in extracted bits.

        Args:
            bits: Raw extracted bits

        Returns:
            Position of sync pattern start, or -1 if not found
        """
        pattern_len = len(SYNC_PATTERN)

        for i in range(len(bits) - pattern_len + 1):
            # Allow 1 bit error in sync pattern detection
            errors = sum(
                bits[i + j] != SYNC_PATTERN[j]
                for j in range(pattern_len)
            )
            if errors <= 1:
                return i

        return -1

    def _resize_to_match(self, array: np.ndarray, target_shape: Tuple[int, int]) -> np.ndarray:
        """Resize array to match target shape."""

        scale_h = target_shape[0] / array.shape[0]
        scale_w = target_shape[1] / array.shape[1]

        return zoom(array, (scale_h, scale_w), order=1)

    def _apply_luminance_change(
        self, rgb_image: np.ndarray, old_y: np.ndarray, new_y: np.ndarray
    ) -> np.ndarray:
        """
        Apply luminance changes to RGB image while preserving chrominance.

        Args:
            rgb_image: Original RGB image
            old_y: Original luminance
            new_y: Modified luminance

        Returns:
            RGB image with modified luminance
        """
        # Calculate ratio
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = np.divide(new_y, old_y, out=np.ones_like(new_y), where=old_y != 0)

        # Clip ratio to reasonable range
        ratio = np.clip(ratio, 0.9, 1.1)

        # Apply to all channels
        result = rgb_image.copy()
        for c in range(3):
            result[:, :, c] *= ratio

        return result
