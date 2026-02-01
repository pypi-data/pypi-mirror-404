"""
Adversarial perturbation for AI protection.

This module implements adversarial attack techniques to protect images
from being used in AI training. The perturbations are imperceptible to
humans but cause AI models to misclassify or fail to extract features.

Based on research from:
- Glaze: Protecting Artists from Style Mimicry
- Nightshade: Prompt-Specific Poisoning Attacks
- Madry et al.: Towards Deep Learning Models Resistant to Adversarial Attacks
"""

from dataclasses import dataclass, field
from typing import Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from ..core.exceptions import AdversarialError
from ..utils.image_ops import (
    calculate_psnr,
    calculate_ssim_simple,
    denormalize_array,
    normalize_array,
)
from ..utils.logger import logger

# ImageNet normalization constants
IMAGENET_MEAN = torch.tensor([0.485, 0.456, 0.406])
IMAGENET_STD = torch.tensor([0.229, 0.224, 0.225])


@dataclass
class AdversarialConfig:
    """
    Configuration for adversarial protection.

    Attributes:
        strength: Protection strength 0-10 (higher = stronger but more visible)
        epsilon: Maximum perturbation magnitude [0, 1] (auto-calculated if not set)
        iterations: Number of optimization iterations (auto-calculated if not set)
        alpha: Step size for iterative attacks (auto-calculated)
        targeted: If True, target specific misclassification
        device: Torch device ('cuda' or 'cpu')
        attack_mode: Type of attack ('feature_disruption' or 'classification')
    """

    strength: int = 5
    epsilon: Optional[float] = field(default=None)
    iterations: Optional[int] = field(default=None)
    alpha: Optional[float] = field(default=None)
    targeted: bool = False
    device: str = "cpu"
    attack_mode: str = "feature_disruption"

    def __post_init__(self) -> None:
        """Validate and compute configuration parameters."""
        if not 0 <= self.strength <= 10:
            raise ValueError(f"strength must be 0-10, got {self.strength}")

        if self.attack_mode not in ("feature_disruption", "classification"):
            raise ValueError(f"attack_mode must be 'feature_disruption' or 'classification'")

        # Validate epsilon if explicitly set
        if self.epsilon is not None and not 0 < self.epsilon <= 0.1:
            raise ValueError(f"epsilon must be in (0, 0.1], got {self.epsilon}")

        # Calculate epsilon based on strength if not explicitly set
        # Range: 0.005 (strength=1) to 0.05 (strength=10)
        if self.epsilon is None:
            self.epsilon = max(0.005, (self.strength / 10.0) * 0.05)

        # Calculate iterations based on strength if not explicitly set
        # More iterations = better optimization but slower
        if self.iterations is None:
            self.iterations = max(10, self.strength * 4)

        # Calculate step size: typical rule is alpha = epsilon / iterations * 2
        if self.alpha is None:
            self.alpha = (self.epsilon / self.iterations) * 2.5


def _load_surrogate_model(device: torch.device) -> nn.Module:
    """
    Load a pre-trained model as surrogate for adversarial generation.

    Uses ResNet-18 pre-trained on ImageNet. The model's learned features
    transfer well to other vision models, making perturbations more universal.

    Args:
        device: Torch device to load model on

    Returns:
        Pre-trained model in eval mode with frozen parameters
    """
    try:
        from torchvision.models import resnet18, ResNet18_Weights

        # Load with pre-trained weights
        model = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)
        logger.info("Loaded ResNet-18 with ImageNet weights as surrogate model")

    except (ImportError, Exception) as e:
        logger.warning(f"Could not load pre-trained ResNet-18: {e}")
        logger.warning("Falling back to simple surrogate (less effective)")
        model = _SimpleSurrogateModel()

    model = model.to(device)
    model.eval()

    # Freeze all parameters
    for param in model.parameters():
        param.requires_grad = False

    return model


class _SimpleSurrogateModel(nn.Module):
    """
    Fallback surrogate model when pre-trained models are unavailable.

    This is a simple VGG-style CNN. Less effective than pre-trained models
    but provides basic adversarial capability.
    """

    def __init__(self) -> None:
        super().__init__()

        self.features = nn.Sequential(
            # Block 1
            nn.Conv2d(3, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            # Block 2
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            # Block 3
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
        )

        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        self.classifier = nn.Sequential(
            nn.Linear(256, 128),
            nn.ReLU(inplace=True),
            nn.Linear(128, 1000)  # ImageNet classes
        )

        # Initialize with random weights (not ideal but functional)
        self._initialize_weights()

    def _initialize_weights(self) -> None:
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        features = self.features(x)
        pooled = self.pool(features)
        flattened = pooled.view(pooled.size(0), -1)
        return self.classifier(flattened)

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        """Extract intermediate features for feature disruption attack."""
        features = self.features(x)
        pooled = self.pool(features)
        return pooled.view(pooled.size(0), -1)


class AdversarialProtection:
    """
    Main class for adversarial image protection.

    This class generates imperceptible perturbations that cause AI models
    to fail at feature extraction, classification, or style transfer.

    Uses PGD (Projected Gradient Descent) attack with a pre-trained ResNet-18
    as surrogate model. Perturbations generated against ResNet transfer well
    to other models due to the universality of learned features.

    Example:
        >>> from antiai.protection import AdversarialProtection
        >>> import numpy as np
        >>> protector = AdversarialProtection(strength=7)
        >>> image = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        >>> protected, metadata = protector.protect(image)
        >>> metadata['quality']['psnr_db'] > 30
        True
    """

    def __init__(
        self,
        strength: int = 5,
        config: Optional[AdversarialConfig] = None,
        use_cuda: bool = True
    ) -> None:
        """
        Initialize adversarial protector.

        Args:
            strength: Protection strength 0-10
            config: Optional custom configuration
            use_cuda: Use CUDA if available

        Example:
            >>> protector = AdversarialProtection(strength=8)
        """
        if config is None:
            device = "cuda" if use_cuda and torch.cuda.is_available() else "cpu"
            config = AdversarialConfig(strength=strength, device=device)

        self.config = config
        self.device = torch.device(config.device)

        logger.info(
            f"Initializing adversarial protection (strength={config.strength}, "
            f"device={self.device}, mode={config.attack_mode})"
        )

        # Load pre-trained surrogate model
        self.model = _load_surrogate_model(self.device)

        # Prepare ImageNet normalization tensors for the device
        self._mean = IMAGENET_MEAN.view(1, 3, 1, 1).to(self.device)
        self._std = IMAGENET_STD.view(1, 3, 1, 1).to(self.device)

    def protect(self, image: np.ndarray) -> Tuple[np.ndarray, dict]:
        """
        Apply adversarial protection to image.

        Args:
            image: Input image as numpy array (H, W, 3) in range [0, 255]

        Returns:
            Tuple of (protected_image, metadata_dict)

        Raises:
            AdversarialError: If protection fails

        Example:
            >>> img = np.ones((100, 100, 3), dtype=np.uint8) * 128
            >>> protected, meta = protector.protect(img)
            >>> protected.shape
            (100, 100, 3)
        """
        try:
            logger.info(f"Applying adversarial protection to image {image.shape}")

            # Validate input
            if image.ndim != 3 or image.shape[2] != 3:
                raise AdversarialError(f"Expected RGB image (H, W, 3), got {image.shape}")

            # Normalize to [0, 1]
            img_normalized = normalize_array(image)

            # Generate perturbation
            perturbation = self._generate_perturbation(img_normalized)

            # Apply perturbation
            protected = np.clip(img_normalized + perturbation, 0.0, 1.0)

            # Denormalize back to [0, 255]
            protected_uint8 = denormalize_array(protected)

            # Calculate quality metrics
            quality = self._calculate_quality(image, protected_uint8)

            # Build metadata
            metadata = {
                "algorithm": "adversarial_pgd_v1",
                "strength": self.config.strength,
                "epsilon": float(self.config.epsilon),
                "iterations": self.config.iterations,
                "perturbation_l2_norm": float(np.linalg.norm(perturbation)),
                "perturbation_linf_norm": float(np.max(np.abs(perturbation))),
                "quality": quality,
            }

            logger.info(
                f"Protection complete: PSNR={quality['psnr_db']:.2f}dB, "
                f"SSIM={quality['ssim']:.4f}"
            )

            return protected_uint8, metadata

        except Exception as e:
            raise AdversarialError(f"Failed to apply adversarial protection: {e}") from e

    def _normalize_for_model(self, img_tensor: torch.Tensor) -> torch.Tensor:
        """
        Apply ImageNet normalization for the surrogate model.

        Args:
            img_tensor: Image tensor in [0, 1] range

        Returns:
            Normalized tensor for model input
        """
        return (img_tensor - self._mean) / self._std

    def _generate_perturbation(self, image: np.ndarray) -> np.ndarray:
        """
        Generate adversarial perturbation using PGD (Projected Gradient Descent).

        Implements an iterative attack that either:
        - 'feature_disruption': Maximizes feature distortion in the model
        - 'classification': Maximizes classification loss (untargeted attack)

        The perturbation is constrained to an L-infinity ball of radius epsilon.

        Args:
            image: Normalized image [0, 1]

        Returns:
            Perturbation array (same shape as image)
        """
        # Convert to torch tensor (B, C, H, W)
        img_tensor = torch.from_numpy(image).permute(2, 0, 1).unsqueeze(0).float()
        img_tensor = img_tensor.to(self.device)

        # Initialize perturbation with small random noise for better exploration
        perturbation = torch.empty_like(img_tensor).uniform_(
            -self.config.epsilon * 0.1, self.config.epsilon * 0.1
        )
        perturbation = perturbation.to(self.device)
        perturbation.requires_grad = True

        # Get original features/predictions for reference (no grad needed)
        with torch.no_grad():
            original_normalized = self._normalize_for_model(img_tensor)
            original_output = self.model(original_normalized)

            if self.config.attack_mode == "classification":
                # Get the predicted class to maximize loss against
                original_class = original_output.argmax(dim=1)

        # PGD iterations
        for iteration in range(self.config.iterations):
            # Ensure perturbation requires grad
            if not perturbation.requires_grad:
                perturbation.requires_grad = True

            # Apply perturbation and clamp to valid range
            perturbed_img = torch.clamp(img_tensor + perturbation, 0, 1)

            # Normalize for model
            perturbed_normalized = self._normalize_for_model(perturbed_img)

            # Forward pass
            output = self.model(perturbed_normalized)

            # Calculate loss based on attack mode
            if self.config.attack_mode == "feature_disruption":
                # Feature disruption: maximize distance from original features
                # This disrupts the model's ability to extract meaningful features
                # We use the output logits as a proxy for features
                feature_diff = output - original_output
                loss = -feature_diff.norm(p=2)  # Negative because we want to maximize

            else:  # classification mode
                # Untargeted attack: maximize cross-entropy loss
                # This makes the model misclassify the image
                loss = -F.cross_entropy(output, original_class)

            # Backward pass
            loss.backward()

            # Update perturbation using signed gradient (PGD step)
            with torch.no_grad():
                if perturbation.grad is not None:
                    # FGSM-style update with sign of gradient
                    grad_sign = perturbation.grad.sign()
                    perturbation = perturbation + self.config.alpha * grad_sign

                    # Project to epsilon ball (L-infinity constraint)
                    perturbation = torch.clamp(
                        perturbation,
                        -self.config.epsilon,
                        self.config.epsilon
                    )

                    # Ensure perturbed image stays in valid [0, 1] range
                    perturbed_img = torch.clamp(img_tensor + perturbation, 0, 1)
                    perturbation = perturbed_img - img_tensor

            # Detach and prepare for next iteration
            perturbation = perturbation.detach().clone()
            perturbation.requires_grad = True

        # Convert back to numpy
        final_perturbation = perturbation.detach().squeeze(0).permute(1, 2, 0).cpu().numpy()

        # Clean up GPU memory
        del perturbation, img_tensor
        if self.device.type == 'cuda':
            torch.cuda.empty_cache()

        return final_perturbation

    def _calculate_quality(self, original: np.ndarray, protected: np.ndarray) -> dict:
        """
        Calculate quality metrics between original and protected images.

        Args:
            original: Original image [0, 255]
            protected: Protected image [0, 255]

        Returns:
            Dictionary with quality metrics
        """
        psnr = calculate_psnr(original, protected)
        ssim = calculate_ssim_simple(original, protected)

        max_diff = int(np.max(np.abs(original.astype(int) - protected.astype(int))))

        return {
            "psnr_db": float(psnr),
            "ssim": float(ssim),
            "max_pixel_difference": max_diff,
            "human_visible": psnr < 40,  # Below 40dB is usually visible
            "quality_level": self._get_quality_level(psnr, ssim),
        }

    @staticmethod
    def _get_quality_level(psnr: float, ssim: float) -> str:
        """
        Determine subjective quality level.

        Args:
            psnr: PSNR value in dB
            ssim: SSIM value [0, 1]

        Returns:
            Quality level string
        """
        if psnr >= 45 and ssim >= 0.98:
            return "excellent"
        elif psnr >= 40 and ssim >= 0.95:
            return "very_good"
        elif psnr >= 35 and ssim >= 0.90:
            return "good"
        elif psnr >= 30 and ssim >= 0.85:
            return "acceptable"
        else:
            return "poor"

    def verify_protection(self, original: np.ndarray, protected: np.ndarray) -> dict:
        """
        Verify that protection was applied correctly.

        Args:
            original: Original image [0, 255]
            protected: Protected image [0, 255]

        Returns:
            Verification results

        Example:
            >>> result = protector.verify_protection(original, protected)
            >>> result['is_protected']
            True
        """
        quality = self._calculate_quality(original, protected)

        # Check if images are different
        are_different = not np.array_equal(original, protected)

        # Check if quality is acceptable
        quality_ok = quality["psnr_db"] >= 30 and quality["ssim"] >= 0.85

        return {
            "is_protected": are_different and quality_ok,
            "images_different": are_different,
            "quality_acceptable": quality_ok,
            "quality_metrics": quality,
        }
