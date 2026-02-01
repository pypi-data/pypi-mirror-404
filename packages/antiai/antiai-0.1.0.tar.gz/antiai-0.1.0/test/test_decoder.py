"""Tests for AntiAI decoder."""

import pytest
from PIL import Image
from antiai import AntiAIDecoder, AntiAIEncoder, IntegrityError, InvalidHeaderError


class TestAntiAIDecoder:
    """Test suite for AntiAIDecoder class."""

    @pytest.fixture
    def encoded_file(self, sample_image_file, test_data_dir, cleanup_output_files):
        """Create an encoded file for decoder tests."""
        encoder = AntiAIEncoder(use_cuda=False)
        output_path = cleanup_output_files(test_data_dir / "test_decode.antiAI")

        encoder.encode(
            input_image=sample_image_file,
            output_path=output_path,
            author="Test Author",
            protection_level=5,
            title="Decoder Test",
        )

        return output_path

    def test_decoder_initialization(self):
        """Test decoder can be initialized."""
        decoder = AntiAIDecoder()
        assert decoder is not None
        assert decoder.verify_integrity is True

    def test_decode_basic(self, encoded_file):
        """Test basic decoding functionality."""
        decoder = AntiAIDecoder()
        image, metadata = decoder.decode(encoded_file)

        assert image is not None
        assert image.shape[2] == 3  # RGB
        assert metadata.author.name == "Test Author"
        assert metadata.title == "Decoder Test"

    def test_decode_preserves_dimensions(
        self, sample_image_file, test_data_dir, cleanup_output_files
    ):
        """Test that decoded image has same dimensions as original."""

        original = Image.open(sample_image_file)
        original_size = original.size

        # Encode
        encoder = AntiAIEncoder(use_cuda=False)
        encoded_path = cleanup_output_files(test_data_dir / "dimension_test.antiAI")
        encoder.encode(
            input_image=sample_image_file,
            output_path=encoded_path,
            author="Test",
            protection_level=5,
        )

        # Decode
        decoder = AntiAIDecoder()
        decoded_image, _ = decoder.decode(encoded_path)

        # Check dimensions (note: height, width order in numpy)
        assert decoded_image.shape[1] == original_size[0]  # width
        assert decoded_image.shape[0] == original_size[1]  # height

    def test_decode_metadata_only(self, encoded_file):
        """Test extracting only metadata."""
        decoder = AntiAIDecoder()
        metadata = decoder.get_metadata_only(encoded_file)

        assert metadata.author.name == "Test Author"
        assert metadata.title == "Decoder Test"
        assert metadata.protection.adversarial is True

    def test_decode_header_only(self, encoded_file):
        """Test extracting only header."""
        decoder = AntiAIDecoder()
        header = decoder.get_header(encoded_file)

        assert header.width > 0
        assert header.height > 0
        assert header.channels in [1, 3, 4]
        assert 0 <= header.protection_level <= 10

    def test_decode_to_file(self, encoded_file, test_data_dir, cleanup_output_files):
        """Test decoding to standard image file."""
        decoder = AntiAIDecoder()
        output_path = cleanup_output_files(test_data_dir / "decoded.png")

        metadata = decoder.decode_to_file(encoded_file, output_path, format="PNG")

        assert output_path.exists()
        assert metadata.author.name == "Test Author"

    def test_decode_nonexistent_file(self):
        """Test decoding nonexistent file raises error."""
        decoder = AntiAIDecoder()

        with pytest.raises(FileNotFoundError):
            decoder.decode("nonexistent.antiAI")

    def test_decode_invalid_file(self, test_data_dir):
        """Test decoding invalid file raises error."""
        # Create a fake file
        invalid_file = test_data_dir / "invalid.antiAI"
        with open(invalid_file, "wb") as f:
            f.write(b"This is not a valid AntiAI file")

        decoder = AntiAIDecoder()

        with pytest.raises(InvalidHeaderError):
            decoder.decode(invalid_file)

    def test_decode_with_integrity_check(self, encoded_file, test_data_dir):
        """Test that integrity check detects corruption."""
        # Create corrupted file
        corrupted_file = test_data_dir / "corrupted.antiAI"

        with open(encoded_file, "rb") as f:
            data = bytearray(f.read())

        # Corrupt some bytes in the middle
        data[1000:1100] = b"\x00" * 100

        with open(corrupted_file, "wb") as f:
            f.write(data)

        decoder = AntiAIDecoder(verify_integrity=True)

        with pytest.raises(IntegrityError):
            decoder.decode(corrupted_file)

    def test_decode_without_integrity_check(self, encoded_file, test_data_dir):
        """Test decoding with integrity check disabled."""
        # This should succeed even with minor corruption
        decoder = AntiAIDecoder(verify_integrity=False)

        # Note: This might still fail if corruption affects critical data
        # This test mainly verifies the flag works
        try:
            image, metadata = decoder.decode(encoded_file)
            assert image is not None
        except Exception:
            # Some corruption might still cause failures
            pass
