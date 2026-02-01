"""Tests for metadata management."""

import json

import pytest
from antiai import ValidationError
from antiai.protection import AuthorInfo, CopyrightInfo, ImageMetadata, MetadataBuilder, ProtectionInfo




class TestAuthorInfo:
    """Test suite for AuthorInfo class."""

    def test_creation_basic(self):
        """Test basic author info creation."""
        author = AuthorInfo(name="John Doe")
        assert author.name == "John Doe"
        assert author.email is None

    def test_creation_full(self):
        """Test author info with all fields."""
        author = AuthorInfo(
            name="Jane Smith",
            email="jane@example.com",
            organization="Test Corp",
            url="https://example.com",
        )
        assert author.name == "Jane Smith"
        assert author.email == "jane@example.com"
        assert author.organization == "Test Corp"
        assert author.url == "https://example.com"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        author = AuthorInfo(name="Test", email="test@test.com")
        author_dict = author.to_dict()

        assert author_dict["name"] == "Test"
        assert author_dict["email"] == "test@test.com"
        assert "organization" not in author_dict  # None values excluded


class TestCopyrightInfo:
    """Test suite for CopyrightInfo class."""

    def test_creation_basic(self):
        """Test basic copyright info creation."""
        copyright_info = CopyrightInfo(statement="© 2025 Test")
        assert copyright_info.statement == "© 2025 Test"
        assert copyright_info.license == "All Rights Reserved"

    def test_creation_custom_year(self):
        """Test copyright info with custom year."""
        copyright_info = CopyrightInfo(statement="© Test", year=2024)
        assert copyright_info.year == 2024

    def test_to_dict(self):
        """Test conversion to dictionary."""
        copyright_info = CopyrightInfo(
            statement="© 2025 Test", license="MIT", usage_terms="Free to use"
        )
        copyright_dict = copyright_info.to_dict()

        assert copyright_dict["statement"] == "© 2025 Test"
        assert copyright_dict["license"] == "MIT"
        assert copyright_dict["usage_terms"] == "Free to use"


class TestProtectionInfo:
    """Test suite for ProtectionInfo class."""

    def test_creation_default(self):
        """Test default protection info."""
        protection = ProtectionInfo()
        assert protection.adversarial is False
        assert protection.watermark is False
        assert protection.encrypted is False

    def test_creation_with_protections(self):
        """Test protection info with protections enabled."""
        protection = ProtectionInfo(
            adversarial=True, adversarial_strength=7, watermark=True, watermark_hash="abc123"
        )
        assert protection.adversarial is True
        assert protection.adversarial_strength == 7
        assert protection.watermark is True
        assert protection.watermark_hash == "abc123"


class TestImageMetadata:
    """Test suite for ImageMetadata class."""

    def test_creation_default(self):
        """Test default metadata creation."""
        metadata = ImageMetadata()
        assert metadata.version == "1.0"
        assert metadata.do_not_train is True
        assert metadata.do_not_scrape is True

    def test_creation_with_author(self):
        """Test metadata with author info."""
        author = AuthorInfo(name="Test Author")
        metadata = ImageMetadata(author=author, title="Test Image")

        assert metadata.author.name == "Test Author"
        assert metadata.title == "Test Image"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        author = AuthorInfo(name="Test")
        metadata = ImageMetadata(author=author, title="Test Title")
        metadata_dict = metadata.to_dict()

        assert metadata_dict["version"] == "1.0"
        assert metadata_dict["author"]["name"] == "Test"
        assert metadata_dict["title"] == "Test Title"

    def test_from_dict(self, sample_metadata_dict):
        """Test creation from dictionary."""
        metadata = ImageMetadata.from_dict(sample_metadata_dict)

        assert metadata.version == "1.0"
        assert metadata.author.name == "Test Author"
        assert metadata.title == "Test Image"

    def test_to_json(self):
        """Test JSON serialization."""
        metadata = ImageMetadata(title="Test")
        json_str = metadata.to_json()

        parsed = json.loads(json_str)
        assert parsed["version"] == "1.0"
        assert parsed["title"] == "Test"

    def test_from_json(self):
        """Test JSON deserialization."""
        json_str = '{"version": "1.0", "title": "From JSON"}'
        metadata = ImageMetadata.from_json(json_str)

        assert metadata.version == "1.0"
        assert metadata.title == "From JSON"

    def test_add_custom_field(self):
        """Test adding custom fields."""
        metadata = ImageMetadata()
        metadata.add_custom_field("project", "TestProject")
        metadata.add_custom_field("tags", ["test", "example"])

        assert metadata.get_custom_field("project") == "TestProject"
        assert metadata.get_custom_field("tags") == ["test", "example"]

    def test_get_custom_field_default(self):
        """Test getting custom field with default."""
        metadata = ImageMetadata()
        value = metadata.get_custom_field("nonexistent", default="default_value")

        assert value == "default_value"

    def test_invalid_author_type(self):
        """Test that invalid author type raises error."""
        with pytest.raises(ValidationError, match="author must be"):
            ImageMetadata(author="not an AuthorInfo object")


class TestMetadataBuilder:
    """Test suite for MetadataBuilder class."""

    def test_builder_basic(self):
        """Test basic builder usage."""
        metadata = MetadataBuilder().set_author("Test Author").set_title("Test Title").build()

        assert metadata.author.name == "Test Author"
        assert metadata.title == "Test Title"

    def test_builder_full_chain(self):
        """Test full builder chain."""
        metadata = (
            MetadataBuilder()
            .set_author("John Doe", email="john@example.com")
            .set_title("My Artwork")
            .set_description("A beautiful piece")
            .set_copyright("© 2025 John Doe", license="CC BY-NC")
            .set_dimensions(1920, 1080)
            .set_color_mode("RGB")
            .enable_adversarial(strength=7)
            .enable_watermark(watermark_hash="abc123")
            .add_custom("project", "Portfolio")
            .build()
        )

        assert metadata.author.name == "John Doe"
        assert metadata.title == "My Artwork"
        assert metadata.dimensions == (1920, 1080)
        assert metadata.protection.adversarial is True
        assert metadata.protection.adversarial_strength == 7
        assert metadata.get_custom_field("project") == "Portfolio"

    def test_builder_protections(self):
        """Test builder protection settings."""
        metadata = (
            MetadataBuilder()
            .set_author("Test")
            .enable_adversarial(5)
            .enable_watermark("hash123")
            .enable_encryption()
            .enable_signature()
            .build()
        )

        assert metadata.protection.adversarial is True
        assert metadata.protection.watermark is True
        assert metadata.protection.encrypted is True
        assert metadata.protection.signed is True

    def test_builder_ai_restrictions(self):
        """Test builder AI restriction settings."""
        metadata = (
            MetadataBuilder()
            .set_author("Test")
            .set_ai_restrictions(do_not_train=False, do_not_scrape=True)
            .build()
        )

        assert metadata.do_not_train is False
        assert metadata.do_not_scrape is True
