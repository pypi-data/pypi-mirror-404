"""
Metadata management for AntiAI files.

This module handles creation, validation, and serialization of
metadata including copyright information, C2PA signatures, and
usage terms.
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Optional

from ..core.exceptions import ValidationError


@dataclass
class AuthorInfo:
    """
    Information about the content author.

    Attributes:
        name: Author's name
        email: Author's email (optional)
        organization: Organization name (optional)
        url: Author's website (optional)
    """

    name: str
    email: Optional[str] = None
    organization: Optional[str] = None
    url: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class CopyrightInfo:
    """
    Copyright and licensing information.

    Attributes:
        statement: Copyright statement (e.g., "© 2025 Author Name")
        license: License type (e.g., "All Rights Reserved", "CC BY-NC")
        usage_terms: Detailed usage terms
        year: Copyright year
        jurisdiction: Legal jurisdiction (optional)
    """

    statement: str
    license: str = "All Rights Reserved"
    usage_terms: str = "All rights reserved. No AI training permitted."
    year: int = field(default_factory=lambda: datetime.now().year)
    jurisdiction: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ProtectionInfo:
    """
    Information about applied protections.

    Attributes:
        adversarial: Adversarial protection applied
        adversarial_strength: Strength level 0-10
        watermark: Watermark embedded
        watermark_hash: Hash of watermark data
        encrypted: Content encrypted
        signed: Cryptographic signature present
    """

    adversarial: bool = False
    adversarial_strength: int = 0
    watermark: bool = False
    watermark_hash: Optional[str] = None
    encrypted: bool = False
    signed: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ImageMetadata:
    """
    Complete metadata for AntiAI image.

    This class aggregates all metadata associated with a protected image,
    including authorship, copyright, technical details, and protection info.

    Example:
        >>> from antiai.protection.metadata import ImageMetadata, AuthorInfo
        >>> author = AuthorInfo(name="Miguel", email="miguel@example.com")
        >>> metadata = ImageMetadata(
        ...     author=author,
        ...     title="My Artwork",
        ...     description="Original digital art"
        ... )
    """

    # Core identification
    version: str = "1.0"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    modified_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Authorship
    author: Optional[AuthorInfo] = None
    title: Optional[str] = None
    description: Optional[str] = None

    # Copyright
    copyright: Optional[CopyrightInfo] = None

    # Technical details
    original_filename: Optional[str] = None
    original_format: Optional[str] = None
    dimensions: Optional[tuple[int, int]] = None
    color_mode: Optional[str] = None

    # Protection details
    protection: ProtectionInfo = field(default_factory=ProtectionInfo)

    # AI training restriction
    do_not_train: bool = True
    do_not_scrape: bool = True

    # Custom fields
    custom: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate metadata after initialization."""
        if self.author and not isinstance(self.author, AuthorInfo):
            raise ValidationError("author must be an AuthorInfo instance")

        if self.copyright and not isinstance(self.copyright, CopyrightInfo):
            raise ValidationError("copyright must be a CopyrightInfo instance")

        if not isinstance(self.protection, ProtectionInfo):
            raise ValidationError("protection must be a ProtectionInfo instance")

    def to_dict(self) -> dict[str, Any]:
        """
        Convert metadata to dictionary.

        Returns:
            Dictionary representation of metadata

        Example:
            >>> metadata = ImageMetadata(version="1.0")
            >>> data = metadata.to_dict()
            >>> data['version']
            '1.0'
        """
        result = {
            "version": self.version,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "do_not_train": self.do_not_train,
            "do_not_scrape": self.do_not_scrape,
        }

        # Add optional fields
        if self.author:
            result["author"] = self.author.to_dict()

        if self.title:
            result["title"] = self.title

        if self.description:
            result["description"] = self.description

        if self.copyright:
            result["copyright"] = self.copyright.to_dict()

        if self.original_filename:
            result["original_filename"] = self.original_filename

        if self.original_format:
            result["original_format"] = self.original_format

        if self.dimensions:
            result["dimensions"] = {"width": self.dimensions[0], "height": self.dimensions[1]}

        if self.color_mode:
            result["color_mode"] = self.color_mode

        # Protection info
        result["protection"] = self.protection.to_dict()

        # Custom fields
        if self.custom:
            result["custom"] = self.custom

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ImageMetadata":
        """
        Create metadata from dictionary.

        Args:
            data: Dictionary with metadata fields

        Returns:
            ImageMetadata instance

        Raises:
            ValidationError: If data is invalid

        Example:
            >>> data = {"version": "1.0", "do_not_train": True}
            >>> metadata = ImageMetadata.from_dict(data)
        """
        try:
            # Parse author
            author = None
            if "author" in data:
                author = AuthorInfo(**data["author"])

            # Parse copyright
            copyright_info = None
            if "copyright" in data:
                copyright_info = CopyrightInfo(**data["copyright"])

            # Parse protection
            protection = ProtectionInfo()
            if "protection" in data:
                protection = ProtectionInfo(**data["protection"])

            # Parse dimensions
            dimensions = None
            if "dimensions" in data:
                dims = data["dimensions"]
                dimensions = (dims["width"], dims["height"])

            return cls(
                version=data.get("version", "1.0"),
                created_at=data.get("created_at", datetime.now().isoformat()),
                modified_at=data.get("modified_at", datetime.now().isoformat()),
                author=author,
                title=data.get("title"),
                description=data.get("description"),
                copyright=copyright_info,
                original_filename=data.get("original_filename"),
                original_format=data.get("original_format"),
                dimensions=dimensions,
                color_mode=data.get("color_mode"),
                protection=protection,
                do_not_train=data.get("do_not_train", True),
                do_not_scrape=data.get("do_not_scrape", True),
                custom=data.get("custom", {}),
            )

        except Exception as e:
            raise ValidationError(f"Failed to parse metadata: {e}") from e

    def to_json(self, indent: int = 2) -> str:
        """
        Convert metadata to JSON string.

        Args:
            indent: JSON indentation level

        Returns:
            JSON string

        Example:
            >>> metadata = ImageMetadata(version="1.0")
            >>> json_str = metadata.to_json()
        """
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> "ImageMetadata":
        """
        Create metadata from JSON string.

        Args:
            json_str: JSON string

        Returns:
            ImageMetadata instance

        Raises:
            ValidationError: If JSON is invalid
        """
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON: {e}") from e

    def update_modified_time(self) -> None:
        """Update the modified_at timestamp to current time."""
        self.modified_at = datetime.now().isoformat()

    def add_custom_field(self, key: str, value: Any) -> None:
        """
        Add a custom metadata field.

        Args:
            key: Field name
            value: Field value (must be JSON-serializable)

        Example:
            >>> metadata = ImageMetadata()
            >>> metadata.add_custom_field("project", "AlamOpsCloud")
        """
        self.custom[key] = value
        self.update_modified_time()

    def get_custom_field(self, key: str, default: Any = None) -> Any:
        """
        Get a custom metadata field.

        Args:
            key: Field name
            default: Default value if key not found

        Returns:
            Field value or default

        Example:
            >>> metadata = ImageMetadata()
            >>> metadata.add_custom_field("project", "AlamOpsCloud")
            >>> metadata.get_custom_field("project")
            'AlamOpsCloud'
        """
        return self.custom.get(key, default)


class MetadataBuilder:
    """
    Builder class for constructing ImageMetadata with fluent interface.

    Example:
        >>> from antiai.protection.metadata import MetadataBuilder
        >>> metadata = (
        ...     MetadataBuilder()
        ...     .set_author("Miguel", email="miguel@example.com")
        ...     .set_title("My Artwork")
        ...     .set_copyright("© 2025 Miguel", license="All Rights Reserved")
        ...     .enable_adversarial(strength=7)
        ...     .enable_watermark(watermark_hash="abc123")
        ...     .build()
        ... )
    """

    def __init__(self) -> None:
        """Initialize builder with default metadata."""
        self._metadata = ImageMetadata()

    def set_author(
        self,
        name: str,
        email: Optional[str] = None,
        organization: Optional[str] = None,
        url: Optional[str] = None,
    ) -> "MetadataBuilder":
        """
        Set author information.

        Args:
            name: Author name
            email: Author email
            organization: Organization name
            url: Author website

        Returns:
            Self for chaining
        """
        self._metadata.author = AuthorInfo(
            name=name, email=email, organization=organization, url=url
        )
        return self

    def set_title(self, title: str) -> "MetadataBuilder":
        """Set image title."""
        self._metadata.title = title
        return self

    def set_description(self, description: str) -> "MetadataBuilder":
        """Set image description."""
        self._metadata.description = description
        return self

    def set_copyright(
        self,
        statement: str,
        license: str = "All Rights Reserved",
        usage_terms: Optional[str] = None,
        year: Optional[int] = None,
    ) -> "MetadataBuilder":
        """
        Set copyright information.

        Args:
            statement: Copyright statement
            license: License type
            usage_terms: Usage terms
            year: Copyright year

        Returns:
            Self for chaining
        """
        self._metadata.copyright = CopyrightInfo(
            statement=statement,
            license=license,
            usage_terms=usage_terms or "All rights reserved. No AI training permitted.",
            year=year or datetime.now().year,
        )
        return self

    def set_original_file_info(
        self, filename: Optional[str] = None, format: Optional[str] = None
    ) -> "MetadataBuilder":
        """Set original file information."""
        if filename:
            self._metadata.original_filename = filename
        if format:
            self._metadata.original_format = format
        return self

    def set_dimensions(self, width: int, height: int) -> "MetadataBuilder":
        """Set image dimensions."""
        self._metadata.dimensions = (width, height)
        return self

    def set_color_mode(self, mode: str) -> "MetadataBuilder":
        """Set color mode (e.g., 'RGB', 'RGBA', 'L')."""
        self._metadata.color_mode = mode
        return self

    def enable_adversarial(self, strength: int) -> "MetadataBuilder":
        """Enable adversarial protection in metadata."""
        self._metadata.protection.adversarial = True
        self._metadata.protection.adversarial_strength = strength
        return self

    def enable_watermark(self, watermark_hash: str) -> "MetadataBuilder":
        """Enable watermark in metadata."""
        self._metadata.protection.watermark = True
        self._metadata.protection.watermark_hash = watermark_hash
        return self

    def enable_encryption(self) -> "MetadataBuilder":
        """Enable encryption flag in metadata."""
        self._metadata.protection.encrypted = True
        return self

    def enable_signature(self) -> "MetadataBuilder":
        """Enable signature flag in metadata."""
        self._metadata.protection.signed = True
        return self

    def set_ai_restrictions(
        self, do_not_train: bool = True, do_not_scrape: bool = True
    ) -> "MetadataBuilder":
        """Set AI usage restrictions."""
        self._metadata.do_not_train = do_not_train
        self._metadata.do_not_scrape = do_not_scrape
        return self

    def add_custom(self, key: str, value: Any) -> "MetadataBuilder":
        """Add custom metadata field."""
        self._metadata.add_custom_field(key, value)
        return self

    def build(self) -> ImageMetadata:
        """
        Build and return the ImageMetadata instance.

        Returns:
            Constructed ImageMetadata
        """
        return self._metadata
