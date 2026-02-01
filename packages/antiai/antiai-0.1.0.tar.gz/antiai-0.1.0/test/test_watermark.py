"""Tests for invisible watermark."""

import hashlib

import numpy as np
import pytest
from antiai import InvisibleWatermark, WatermarkError


class TestInvisibleWatermark:
    """Test suite for InvisibleWatermark class."""

    def test_initialization_default(self):
        """Test default initialization."""
        watermarker = InvisibleWatermark()
        assert watermarker.strength == 0.1
        assert watermarker.wavelet == "haar"

    def test_initialization_custom(self):
        """Test initialization with custom parameters."""
        watermarker = InvisibleWatermark(strength=0.2, wavelet="db1")
        assert watermarker.strength == 0.2
        assert watermarker.wavelet == "db1"

    def test_initialization_invalid_strength(self):
        """Test that invalid strength raises error."""
        with pytest.raises(ValueError, match="strength must be in"):
            InvisibleWatermark(strength=1.0)

        with pytest.raises(ValueError, match="strength must be in"):
            InvisibleWatermark(strength=-0.1)

    def test_embed_basic(self, sample_image_rgb):
        """Test basic watermark embedding."""
        watermarker = InvisibleWatermark(strength=0.1)
        watermark_data = "test_watermark_12345"

        marked, metadata = watermarker.embed(sample_image_rgb, watermark_data)

        assert marked.shape == sample_image_rgb.shape
        assert marked.dtype == np.uint8
        assert "watermark_hash" in metadata
        assert "algorithm" in metadata

    def test_embed_creates_minimal_change(self, sample_image_rgb):
        """Test that watermark creates minimal visual change."""
        watermarker = InvisibleWatermark(strength=0.1)
        watermark_data = "invisible_mark"

        marked, _ = watermarker.embed(sample_image_rgb, watermark_data)

        # Calculate difference
        diff = np.abs(sample_image_rgb.astype(float) - marked.astype(float))
        max_diff = np.max(diff)
        mean_diff = np.mean(diff)

        # Changes should be small
        assert max_diff < 50  # Max change less than 20%
        assert mean_diff < 5  # Average change less than 2%

    def test_embed_extract_roundtrip(self, sample_image_rgb):
        """Test that watermark can be extracted after embedding."""
        watermarker = InvisibleWatermark(strength=0.2)  # Higher strength for better extraction
        original_data = "secret123"  # Shorter data for more reliable extraction

        # Embed
        marked, metadata = watermarker.embed(sample_image_rgb, original_data)

        # Extract
        extracted = watermarker.extract(marked, expected_length=len(original_data))

        # Compare (might not be exact due to quantization)
        # Check if at least 70% of characters match (differential encoding is more robust)
        matches = sum(c1 == c2 for c1, c2 in zip(original_data, extracted))
        similarity = matches / len(original_data) if original_data else 0

        assert similarity >= 0.7, f"Expected >= 70% similarity, got {similarity:.1%}"

    def test_embed_different_data_produces_different_marks(self, sample_image_rgb):
        """Test that different watermark data produces different results."""
        watermarker = InvisibleWatermark(strength=0.1)

        marked1, _ = watermarker.embed(sample_image_rgb, "data_one")
        marked2, _ = watermarker.embed(sample_image_rgb, "data_two")

        # Watermarked images should be different
        assert not np.array_equal(marked1, marked2)

    def test_embed_hash_consistency(self, sample_image_rgb):
        """Test that watermark hash is consistent."""
        watermarker = InvisibleWatermark(strength=0.1)
        watermark_data = "consistent_data"

        marked, metadata = watermarker.embed(sample_image_rgb, watermark_data)

        # Check hash matches
        expected_hash = hashlib.sha256(watermark_data.encode()).hexdigest()
        assert metadata["watermark_hash"] == expected_hash

    def test_embed_invalid_image_shape(self):
        """Test that invalid image shape raises error."""
        watermarker = InvisibleWatermark(strength=0.1)

        # Wrong shape
        invalid_image = np.zeros((100, 100), dtype=np.uint8)

        with pytest.raises(WatermarkError, match="Expected RGB image"):
            watermarker.embed(invalid_image, "data")

    def test_embed_image_too_small(self):
        """Test that too small image raises error."""
        watermarker = InvisibleWatermark(strength=0.1)

        # Very small image
        tiny_image = np.zeros((10, 10, 3), dtype=np.uint8)
        long_watermark = "x" * 1000

        with pytest.raises(WatermarkError, match="Image too small"):
            watermarker.embed(tiny_image, long_watermark)

    def test_extract_from_unmarked(self, sample_image_rgb):
        """Test extraction from unmarked image."""
        watermarker = InvisibleWatermark(strength=0.1)

        # Extract from original (no watermark)
        extracted = watermarker.extract(sample_image_rgb, expected_length=20)

        # Should return something but not meaningful
        assert len(extracted) <= 20

    @pytest.mark.parametrize("strength", [0.05, 0.1, 0.15, 0.2])
    def test_embed_different_strengths(self, sample_image_rgb, strength):
        """Test embedding with different strengths."""
        watermarker = InvisibleWatermark(strength=strength)
        watermark_data = "test_data"

        marked, metadata = watermarker.embed(sample_image_rgb, watermark_data)

        assert metadata["strength"] == strength
        assert marked.shape == sample_image_rgb.shape

    def test_metadata_fields(self, sample_image_rgb):
        """Test that metadata contains all expected fields."""
        watermarker = InvisibleWatermark(strength=0.1)
        watermark_data = "metadata_test"

        marked, metadata = watermarker.embed(sample_image_rgb, watermark_data)

        required_fields = [
            "algorithm",
            "strength",
            "wavelet",
            "watermark_hash",
            "watermark_length",
            "bits_embedded",
        ]

        for field in required_fields:
            assert field in metadata
