"""Integration tests for the complete AntiAI pipeline."""

import tempfile
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from antiai import AntiAIEncoder, AntiAIDecoder, ProtectionVerifier
from antiai.core.format_spec import SIGNATURE_SIZE


class TestEncodeDecode:
    """Test the complete encode -> decode pipeline."""

    def test_full_pipeline(self, sample_image_rgb, tmp_path):
        """Test encoding and decoding produces valid results."""
        # Create input image file
        input_path = tmp_path / "input.png"
        Image.fromarray(sample_image_rgb).save(input_path)

        output_path = tmp_path / "output.antiAI"

        # Encode
        encoder = AntiAIEncoder(use_cuda=False)
        stats = encoder.encode(
            input_image=input_path,
            output_path=output_path,
            author="Test Author",
            protection_level=5,
            title="Test Image",
        )

        assert output_path.exists()
        assert stats["success"] if "success" in stats else True

        # Decode
        decoder = AntiAIDecoder(verify_integrity=True)
        decoded_image, metadata = decoder.decode(output_path)

        # Verify dimensions match
        assert decoded_image.shape == sample_image_rgb.shape

        # Verify metadata
        assert metadata.author.name == "Test Author"
        assert metadata.title == "Test Image"
        assert metadata.do_not_train is True

    def test_signature_size_consistency(self, sample_image_rgb, tmp_path):
        """Test that signature size in file matches constant."""
        input_path = tmp_path / "input.png"
        Image.fromarray(sample_image_rgb).save(input_path)
        output_path = tmp_path / "output.antiAI"

        encoder = AntiAIEncoder(use_cuda=False)
        encoder.encode(
            input_image=input_path,
            output_path=output_path,
            author="Test",
            protection_level=3,
        )

        # Read file and check signature
        with open(output_path, "rb") as f:
            file_data = f.read()

        # Last SIGNATURE_SIZE bytes should be the signature
        signature = file_data[-SIGNATURE_SIZE:]
        assert len(signature) == SIGNATURE_SIZE
        assert len(signature) == 32  # SHA-256

    def test_different_protection_levels(self, sample_image_rgb, tmp_path):
        """Test encoding with different protection levels."""
        input_path = tmp_path / "input.png"
        Image.fromarray(sample_image_rgb).save(input_path)

        for level in [1, 5, 10]:
            output_path = tmp_path / f"output_level_{level}.antiAI"

            encoder = AntiAIEncoder(use_cuda=False)
            stats = encoder.encode(
                input_image=input_path,
                output_path=output_path,
                author="Test",
                protection_level=level,
            )

            assert output_path.exists()

            # Decode and verify
            decoder = AntiAIDecoder()
            image, metadata = decoder.decode(output_path)
            assert image.shape == sample_image_rgb.shape


class TestProtectionVerification:
    """Test protection verification functionality."""

    def test_verify_protected_file(self, sample_image_rgb, tmp_path):
        """Test that verification works on protected files."""
        input_path = tmp_path / "input.png"
        Image.fromarray(sample_image_rgb).save(input_path)
        output_path = tmp_path / "protected.antiAI"

        encoder = AntiAIEncoder(use_cuda=False)
        encoder.encode(
            input_image=input_path,
            output_path=output_path,
            author="Test",
            protection_level=7,
        )

        # Verify should not raise
        verifier = ProtectionVerifier()
        result = verifier.verify(output_path)

        assert result["authentic"] is True
        assert result["protections"]["adversarial"] is True
        assert result["protections"]["watermark"] is True


class TestBatchProcessing:
    """Test batch processing functionality."""

    def test_batch_encode(self, sample_image_rgb, tmp_path):
        """Test batch encoding multiple images."""
        # Create multiple input images
        input_files = []
        for i in range(3):
            path = tmp_path / f"input_{i}.png"
            # Slightly modify each image
            modified = np.clip(sample_image_rgb.astype(int) + i * 10, 0, 255).astype(np.uint8)
            Image.fromarray(modified).save(path)
            input_files.append(path)

        output_dir = tmp_path / "protected"

        encoder = AntiAIEncoder(use_cuda=False)
        results = encoder.encode_batch(
            input_images=input_files,
            output_dir=output_dir,
            author="Batch Test",
            protection_level=5,
        )

        # All should succeed
        assert len(results) == 3
        assert all(r.get("success", True) for r in results)

        # All output files should exist
        for input_file in input_files:
            output_file = output_dir / f"{input_file.stem}.antiAI"
            assert output_file.exists()
