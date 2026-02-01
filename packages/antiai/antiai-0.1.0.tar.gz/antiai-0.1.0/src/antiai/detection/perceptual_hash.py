"""
Perceptual hashing for image similarity detection.

Perceptual hashes allow finding similar or copied images even after
modifications like resizing, compression, or minor edits.
"""

from typing import Tuple

import numpy as np
from PIL import Image
from scipy.fftpack import dct


from ..utils.logger import logger


class PerceptualHash:
    """
    Generate perceptual hashes for image similarity detection.

    This implements multiple hash algorithms:
    - Average Hash (aHash): Fast, basic similarity
    - Difference Hash (dHash): Edge-based comparison
    - DCT Hash (pHash): Frequency-based, more robust

    Example:
        >>> from antiai.detection import PerceptualHash
        >>> import numpy as np
        >>> hasher = PerceptualHash()
        >>> image = np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)
        >>> hash_value = hasher.compute_phash(image)
        >>> len(hash_value)
        64
    """

    def __init__(self, hash_size: int = 8) -> None:
        """
        Initialize perceptual hasher.

        Args:
            hash_size: Size of the hash (8 = 64-bit hash, 16 = 256-bit)

        Example:
            >>> hasher = PerceptualHash(hash_size=8)
        """
        self.hash_size = hash_size
        logger.info(f"Initialized PerceptualHash (size={hash_size})")

    def compute_ahash(self, image: np.ndarray) -> str:
        """
        Compute Average Hash (aHash).

        Simple algorithm that compares pixel values to their average.
        Fast but less robust to transformations.

        Args:
            image: Image array (H, W, 3) or (H, W)

        Returns:
            Hexadecimal hash string

        Example:
            >>> img = np.ones((100, 100, 3), dtype=np.uint8) * 128
            >>> hash_val = hasher.compute_ahash(img)
        """
        # Convert to grayscale if needed
        if image.ndim == 3:
            gray = np.dot(image[..., :3], [0.299, 0.587, 0.114])
        else:
            gray = image

        # Resize to hash_size x hash_size
        pil_img = Image.fromarray(gray.astype(np.uint8))
        pil_img = pil_img.resize((self.hash_size, self.hash_size), Image.Resampling.LANCZOS)
        pixels = np.array(pil_img).flatten()

        # Compare to average
        avg = pixels.mean()
        hash_bits = (pixels > avg).astype(int)

        # Convert to hex
        hash_hex = self._bits_to_hex(hash_bits)

        return hash_hex

    def compute_dhash(self, image: np.ndarray) -> str:
        """
        Compute Difference Hash (dHash).

        Compares adjacent pixels to detect edges and patterns.
        More robust than aHash to color changes.

        Args:
            image: Image array (H, W, 3) or (H, W)

        Returns:
            Hexadecimal hash string

        Example:
            >>> hash_val = hasher.compute_dhash(image)
        """
        # Convert to grayscale
        if image.ndim == 3:
            gray = np.dot(image[..., :3], [0.299, 0.587, 0.114])
        else:
            gray = image

        # Resize to (hash_size+1) x hash_size
        pil_img = Image.fromarray(gray.astype(np.uint8))
        pil_img = pil_img.resize((self.hash_size + 1, self.hash_size), Image.Resampling.LANCZOS)
        pixels = np.array(pil_img)

        # Compute horizontal gradient
        diff = pixels[:, 1:] > pixels[:, :-1]
        hash_bits = diff.flatten().astype(int)

        # Convert to hex
        hash_hex = self._bits_to_hex(hash_bits)

        return hash_hex

    def compute_phash(self, image: np.ndarray) -> str:
        """
        Compute Perceptual Hash (pHash) using DCT.

        Uses Discrete Cosine Transform to focus on frequency content.
        Most robust to transformations but slower.

        Args:
            image: Image array (H, W, 3) or (H, W)

        Returns:
            Hexadecimal hash string

        Example:
            >>> hash_val = hasher.compute_phash(image)
        """

        # Convert to grayscale
        if image.ndim == 3:
            gray = np.dot(image[..., :3], [0.299, 0.587, 0.114])
        else:
            gray = image

        # Resize to 32x32 for DCT
        pil_img = Image.fromarray(gray.astype(np.uint8))
        pil_img = pil_img.resize((32, 32), Image.Resampling.LANCZOS)
        pixels = np.array(pil_img, dtype=np.float32)

        # Compute DCT
        dct_coeff = dct(dct(pixels.T, norm="ortho").T, norm="ortho")

        # Extract low frequencies (top-left corner)
        dct_low = dct_coeff[: self.hash_size, : self.hash_size]

        # Compare to median
        median = np.median(dct_low)
        hash_bits = (dct_low > median).flatten().astype(int)

        # Convert to hex
        hash_hex = self._bits_to_hex(hash_bits)

        return hash_hex

    def compute_all(self, image: np.ndarray) -> dict[str, str]:
        """
        Compute all hash types.

        Args:
            image: Image array

        Returns:
            Dictionary with all hash types

        Example:
            >>> hashes = hasher.compute_all(image)
            >>> hashes.keys()
            dict_keys(['ahash', 'dhash', 'phash'])
        """
        return {
            "ahash": self.compute_ahash(image),
            "dhash": self.compute_dhash(image),
            "phash": self.compute_phash(image),
        }

    def hamming_distance(self, hash1: str, hash2: str) -> int:
        """
        Calculate Hamming distance between two hashes.

        Lower distance = more similar images.
        Distance of 0 = identical or near-identical images.

        Args:
            hash1: First hash (hex string)
            hash2: Second hash (hex string)

        Returns:
            Hamming distance (number of different bits)

        Example:
            >>> hash1 = hasher.compute_phash(image1)
            >>> hash2 = hasher.compute_phash(image2)
            >>> distance = hasher.hamming_distance(hash1, hash2)
            >>> similarity = 100 * (1 - distance / 64)
        """
        if len(hash1) != len(hash2):
            raise ValueError(f"Hash length mismatch: {len(hash1)} vs {len(hash2)}")

        # Convert hex to binary
        bits1 = bin(int(hash1, 16))[2:].zfill(len(hash1) * 4)
        bits2 = bin(int(hash2, 16))[2:].zfill(len(hash2) * 4)

        # Count differing bits
        distance = sum(b1 != b2 for b1, b2 in zip(bits1, bits2))

        return distance

    def similarity_score(self, hash1: str, hash2: str) -> float:
        """
        Calculate similarity score as percentage.

        Args:
            hash1: First hash
            hash2: Second hash

        Returns:
            Similarity percentage (0-100)

        Example:
            >>> score = hasher.similarity_score(hash1, hash2)
            >>> print(f"Images are {score:.1f}% similar")
        """
        distance = self.hamming_distance(hash1, hash2)
        max_distance = len(hash1) * 4  # 4 bits per hex char

        similarity = 100 * (1 - distance / max_distance)

        return similarity

    def _bits_to_hex(self, bits: np.ndarray) -> str:
        """Convert bit array to hexadecimal string."""
        # Convert bits to string
        bit_string = "".join(str(b) for b in bits)

        # Convert to integer then hex
        hash_int = int(bit_string, 2)
        hash_hex = format(hash_int, f"0{len(bits) // 4}x")

        return hash_hex
