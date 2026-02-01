"""Tests for AntiAI encoder."""

from pathlib import Path
import numpy as np
import pytest

from antiai import AntiAIEncoder
from antiai.core.exceptions import ImageError
from PIL import Image



class TestAntiAIEncoder:
    """Test suite for AntiAIEncoder class."""

    def test_encoder_initialization(self):
        """Test encoder can be initialized."""
        encoder = AntiAIEncoder()
        assert encoder is not None
        assert encoder.use_cuda in [True, False]

    def test_encode_basic(self, sample_image_file, test_data_dir, cleanup_output_files):
        """Test basic encoding functionality."""
        encoder = AntiAIEncoder(use_cuda=False)
        output_path = cleanup_output_files(test_data_dir / "encoded.antiAI")

        stats = encoder.encode(
            input_image=sample_image_file,
            output_path=output_path,
            author="Test Author",
            protection_level=5,
        )

        assert output_path.exists()
        assert stats["protection_level"] == 5
        assert "adversarial" in stats
        assert "watermark" in stats
        assert stats["output_size_bytes"] > 0

    def test_encode_with_metadata(self, sample_image_file, test_data_dir, cleanup_output_files):
        """Test encoding with full metadata."""
        encoder = AntiAIEncoder(use_cuda=False)
        output_path = cleanup_output_files(test_data_dir / "encoded_meta.antiAI")

        stats = encoder.encode(
            input_image=sample_image_file,
            output_path=output_path,
            author="Test Author",
            protection_level=7,
            title="Test Image",
            description="A beautiful test image",
            copyright_statement="© 2025 Test Author",
            license_type="CC BY-NC",
        )

        assert output_path.exists()
        assert stats["metadata"]["title"] == "Test Image"
        assert stats["metadata"]["description"] == "A beautiful test image"

    @pytest.mark.parametrize("protection_level", [1, 3, 5, 7, 10])
    def test_encode_different_protection_levels(
        self, sample_image_file, test_data_dir, cleanup_output_files, protection_level
    ):
        """Test encoding with different protection levels."""
        encoder = AntiAIEncoder(use_cuda=False)
        output_path = cleanup_output_files(
            test_data_dir / f"encoded_level_{protection_level}.antiAI"
        )

        stats = encoder.encode(
            input_image=sample_image_file,
            output_path=output_path,
            author="Test Author",
            protection_level=protection_level,
        )

        assert output_path.exists()
        assert stats["adversarial"]["strength"] == protection_level

    def test_encode_invalid_protection_level(self, sample_image_file, test_data_dir):
        """Test that invalid protection level raises error."""
        encoder = AntiAIEncoder(use_cuda=False)
        output_path = test_data_dir / "invalid.antiAI"

        with pytest.raises(ValueError, match="protection_level must be 0-10"):
            encoder.encode(
                input_image=sample_image_file,
                output_path=output_path,
                author="Test Author",
                protection_level=15,
            )

    def test_encode_nonexistent_file(self, test_data_dir):
        """Test encoding nonexistent file raises error."""
        encoder = AntiAIEncoder(use_cuda=False)
        output_path = test_data_dir / "output.antiAI"

        with pytest.raises(FileNotFoundError):
            encoder.encode(
                input_image="nonexistent.jpg",
                output_path=output_path,
                author="Test Author",
            )

    def test_encode_batch(self, test_data_dir, sample_image_rgb, cleanup_output_files):
        """Test batch encoding."""
        encoder = AntiAIEncoder(use_cuda=False)

        # Create multiple test images
        image_files = []
        for i in range(3):
            img_path = test_data_dir / f"test_{i}.png"

            Image.fromarray(sample_image_rgb).save(img_path)
            image_files.append(img_path)

        # Encode batch
        results = encoder.encode_batch(
            input_images=image_files,
            output_dir=test_data_dir / "batch_output",
            author="Test Author",
            protection_level=5,
        )

        assert len(results) == 3
        assert all(r["success"] for r in results)

        # Cleanup
        for result in results:
            output_file = Path(result["output_file"])
            cleanup_output_files(output_file)

    def test_encode_quality_metrics(self, sample_image_file, test_data_dir, cleanup_output_files):
        """Test that quality metrics are reasonable."""
        encoder = AntiAIEncoder(use_cuda=False)
        output_path = cleanup_output_files(test_data_dir / "quality_test.antiAI")

        stats = encoder.encode(
            input_image=sample_image_file,
            output_path=output_path,
            author="Test Author",
            protection_level=5,
        )

        quality = stats["adversarial"]["quality"]

        # PSNR should be reasonable (>30 dB for good quality)
        assert quality["psnr_db"] > 30

        # SSIM should be high (>0.85 for good quality)
        assert quality["ssim"] > 0.85

        # Should not be too visible to humans
        assert not quality["human_visible"] or quality["psnr_db"] > 35
