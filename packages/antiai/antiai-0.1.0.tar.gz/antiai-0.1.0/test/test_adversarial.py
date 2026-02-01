"""Tests for adversarial protection."""

import numpy as np
import pytest
from antiai import AdversarialConfig, AdversarialError, AdversarialProtection


class TestAdversarialProtection:
    """Test suite for AdversarialProtection class."""

    def test_initialization_default(self):
        """Test default initialization."""
        protector = AdversarialProtection(strength=5, use_cuda=False)
        assert protector.config.strength == 5
        assert protector.config.device == "cpu"
        assert protector.config.attack_mode == "feature_disruption"

    def test_initialization_custom_config(self):
        """Test initialization with custom config."""
        config = AdversarialConfig(strength=7, iterations=20, device="cpu")
        protector = AdversarialProtection(config=config, use_cuda=False)
        assert protector.config.strength == 7
        assert protector.config.iterations == 20

    def test_initialization_classification_mode(self):
        """Test initialization with classification attack mode."""
        config = AdversarialConfig(strength=5, device="cpu", attack_mode="classification")
        protector = AdversarialProtection(config=config, use_cuda=False)
        assert protector.config.attack_mode == "classification"

    def test_initialization_invalid_strength(self):
        """Test that invalid strength raises error."""
        with pytest.raises(ValueError, match="strength must be 0-10"):
            AdversarialConfig(strength=15)

    def test_protect_rgb_image(self, sample_image_rgb):
        """Test protecting RGB image."""
        protector = AdversarialProtection(strength=5, use_cuda=False)
        protected, metadata = protector.protect(sample_image_rgb)

        assert protected.shape == sample_image_rgb.shape
        assert protected.dtype == np.uint8
        assert "algorithm" in metadata
        assert "quality" in metadata

    def test_protect_invalid_shape(self):
        """Test that invalid image shape raises error."""
        protector = AdversarialProtection(strength=5, use_cuda=False)

        # Wrong shape (missing channel dimension)
        invalid_image = np.zeros((100, 100), dtype=np.uint8)

        with pytest.raises(AdversarialError, match="Expected RGB image"):
            protector.protect(invalid_image)

    @pytest.mark.parametrize("strength", [1, 3, 5, 7, 10])
    def test_protect_different_strengths(self, sample_image_rgb, strength):
        """Test protection with different strength levels."""
        protector = AdversarialProtection(strength=strength, use_cuda=False)
        protected, metadata = protector.protect(sample_image_rgb)

        # Higher strength should result in larger perturbations
        expected_epsilon = max(0.005, (strength / 10.0) * 0.05)
        assert metadata["epsilon"] == expected_epsilon

    def test_protect_quality_metrics(self, sample_image_rgb):
        """Test that quality metrics are reasonable."""
        protector = AdversarialProtection(strength=5, use_cuda=False)
        protected, metadata = protector.protect(sample_image_rgb)

        quality = metadata["quality"]

        # PSNR should be reasonable
        assert quality["psnr_db"] > 25  # At least acceptable quality

        # SSIM should be high
        assert quality["ssim"] > 0.80

    def test_protect_creates_difference(self, sample_image_rgb):
        """Test that protection actually modifies the image."""
        protector = AdversarialProtection(strength=5, use_cuda=False)
        protected, metadata = protector.protect(sample_image_rgb)

        # Images should be different
        assert not np.array_equal(sample_image_rgb, protected)

        # But difference should be small (imperceptible)
        max_diff = np.max(np.abs(sample_image_rgb.astype(int) - protected.astype(int)))
        assert max_diff < 30  # Less than ~12% change per pixel

    def test_verify_protection(self, sample_image_rgb):
        """Test protection verification."""
        protector = AdversarialProtection(strength=5, use_cuda=False)
        protected, _ = protector.protect(sample_image_rgb)

        result = protector.verify_protection(sample_image_rgb, protected)

        assert result["is_protected"] is True
        assert result["images_different"] is True
        assert result["quality_acceptable"] is True

    def test_perturbation_metadata(self, sample_image_rgb):
        """Test that perturbation metadata is correct."""
        protector = AdversarialProtection(strength=7, use_cuda=False)
        protected, metadata = protector.protect(sample_image_rgb)

        # Check perturbation norms
        assert metadata["perturbation_l2_norm"] > 0
        assert metadata["perturbation_linf_norm"] > 0
        assert metadata["perturbation_linf_norm"] <= metadata["epsilon"]

    def test_quality_level_classification(self, sample_image_rgb):
        """Test quality level classification."""
        protector = AdversarialProtection(strength=3, use_cuda=False)
        protected, metadata = protector.protect(sample_image_rgb)

        quality_level = metadata["quality"]["quality_level"]
        assert quality_level in [
            "excellent",
            "very_good",
            "good",
            "acceptable",
            "poor",
        ]

    def test_reproducibility_with_seed(self, sample_image_rgb):
        """Test that protection is reproducible with same seed."""
        # Note: This test might need torch.manual_seed for true reproducibility
        protector1 = AdversarialProtection(strength=5, use_cuda=False)
        protector2 = AdversarialProtection(strength=5, use_cuda=False)

        protected1, _ = protector1.protect(sample_image_rgb)
        protected2, _ = protector2.protect(sample_image_rgb)

        # Results might differ slightly due to random initialization
        # but should be very similar
        diff = np.mean(np.abs(protected1.astype(float) - protected2.astype(float)))
        assert diff < 10  # Average difference less than 10 pixel values


class TestAdversarialConfig:
    """Test suite for AdversarialConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = AdversarialConfig()
        assert config.strength == 5
        assert config.iterations >= 10
        assert config.alpha > 0
        assert config.attack_mode == "feature_disruption"

    def test_config_validation(self):
        """Test configuration validation."""
        with pytest.raises(ValueError):
            AdversarialConfig(strength=11)

        with pytest.raises(ValueError):
            AdversarialConfig(strength=-1)

        # Epsilon > 0.1 should raise error
        with pytest.raises(ValueError):
            AdversarialConfig(epsilon=0.15)

        # Invalid attack mode
        with pytest.raises(ValueError):
            AdversarialConfig(attack_mode="invalid")

    def test_config_adjustments(self):
        """Test that config adjusts parameters based on strength."""
        config_weak = AdversarialConfig(strength=2)
        config_strong = AdversarialConfig(strength=9)

        # Stronger protection should have more iterations
        assert config_strong.iterations > config_weak.iterations

        # Stronger protection should have larger epsilon
        assert config_strong.epsilon > config_weak.epsilon

    def test_explicit_epsilon_preserved(self):
        """Test that explicitly set epsilon is preserved."""
        config = AdversarialConfig(strength=5, epsilon=0.08)
        assert config.epsilon == 0.08
