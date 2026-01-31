"""
Data Augmentation Suite

This module implements various data augmentation techniques for training neural networks.
Augmentation artificially increases dataset size and diversity, improving generalization.

Implemented Techniques:

Image Augmentation:
1. Rotation - Rotate images by random angles
2. Horizontal Flip - Mirror images horizontally
3. Vertical Flip - Mirror images vertically
4. Random Crop - Extract random patches
5. Center Crop - Extract center region
6. Color Jitter - Adjust brightness, contrast, saturation
7. Gaussian Noise - Add random noise
8. Gaussian Blur - Apply blur filter
9. Random Erasing - Erase random rectangular regions
10. Cutout - Mask out square regions
11. Mixup - Blend two images
12. Normalize - Standardize pixel values

Text Augmentation:
1. Synonym Replacement - Replace words with synonyms
2. Random Insertion - Insert random words
3. Random Swap - Swap word positions
4. Random Deletion - Delete random words

References:
- Rotation/Flip/Crop: Classic augmentation techniques
- Mixup: "mixup: Beyond Empirical Risk Minimization" (Zhang et al., 2017)
- Cutout: "Improved Regularization of CNNs with Cutout" (DeVries & Taylor, 2017)
- Random Erasing: "Random Erasing Data Augmentation" (Zhong et al., 2017)
- AutoAugment: "AutoAugment: Learning Augmentation Policies" (Cubuk et al., 2018)

Author: Ali Mehdi
Date: January 15, 2026
"""

import numpy as np
from typing import Tuple, Optional, List
import random


class ImageAugmenter:
    """
    Image Augmentation Pipeline.
    
    Provides various augmentation techniques for image data.
    All methods work with NumPy arrays in (H, W, C) format.
    
    Example:
        >>> aug = ImageAugmenter()
        >>> image = np.random.rand(224, 224, 3)
        >>> rotated = aug.rotate(image, angle=30)
        >>> flipped = aug.horizontal_flip(image)
        >>> noisy = aug.gaussian_noise(image, std=0.1)
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize augmenter.
        
        Args:
            seed: Random seed for reproducibility
        """
        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)
    
    def rotate(self, image: np.ndarray, angle: float) -> np.ndarray:
        """
        Rotate image by specified angle.
        
        Args:
            image: Input image (H, W, C)
            angle: Rotation angle in degrees (positive = counter-clockwise)
        
        Returns:
            Rotated image
        
        Example:
            >>> aug = ImageAugmenter()
            >>> image = np.random.rand(100, 100, 3)
            >>> rotated = aug.rotate(image, angle=45)
        """
        from scipy.ndimage import rotate as scipy_rotate
        return scipy_rotate(image, angle, reshape=False, mode='nearest')
    
    def random_rotation(self, image: np.ndarray, max_angle: float = 30) -> np.ndarray:
        """
        Rotate image by random angle.
        
        Args:
            image: Input image (H, W, C)
            max_angle: Maximum rotation angle in degrees
        
        Returns:
            Randomly rotated image
        """
        angle = np.random.uniform(-max_angle, max_angle)
        return self.rotate(image, angle)
    
    def horizontal_flip(self, image: np.ndarray) -> np.ndarray:
        """
        Flip image horizontally (left-right).
        
        Args:
            image: Input image (H, W, C)
        
        Returns:
            Horizontally flipped image
        
        Example:
            >>> aug = ImageAugmenter()
            >>> image = np.random.rand(100, 100, 3)
            >>> flipped = aug.horizontal_flip(image)
        """
        return np.fliplr(image)
    
    def vertical_flip(self, image: np.ndarray) -> np.ndarray:
        """
        Flip image vertically (up-down).
        
        Args:
            image: Input image (H, W, C)
        
        Returns:
            Vertically flipped image
        
        Example:
            >>> aug = ImageAugmenter()
            >>> image = np.random.rand(100, 100, 3)
            >>> flipped = aug.vertical_flip(image)
        """
        return np.flipud(image)
    
    def random_crop(self, image: np.ndarray, crop_size: Tuple[int, int]) -> np.ndarray:
        """
        Extract random crop from image.
        
        Args:
            image: Input image (H, W, C)
            crop_size: (height, width) of crop
        
        Returns:
            Randomly cropped image
        
        Example:
            >>> aug = ImageAugmenter()
            >>> image = np.random.rand(224, 224, 3)
            >>> cropped = aug.random_crop(image, crop_size=(128, 128))
        """
        h, w = image.shape[:2]
        crop_h, crop_w = crop_size
        
        if crop_h > h or crop_w > w:
            raise ValueError(f"Crop size {crop_size} larger than image {(h, w)}")
        
        top = np.random.randint(0, h - crop_h + 1)
        left = np.random.randint(0, w - crop_w + 1)
        
        return image[top:top + crop_h, left:left + crop_w]
    
    def center_crop(self, image: np.ndarray, crop_size: Tuple[int, int]) -> np.ndarray:
        """
        Extract center crop from image.
        
        Args:
            image: Input image (H, W, C)
            crop_size: (height, width) of crop
        
        Returns:
            Center cropped image
        
        Example:
            >>> aug = ImageAugmenter()
            >>> image = np.random.rand(224, 224, 3)
            >>> cropped = aug.center_crop(image, crop_size=(128, 128))
        """
        h, w = image.shape[:2]
        crop_h, crop_w = crop_size
        
        if crop_h > h or crop_w > w:
            raise ValueError(f"Crop size {crop_size} larger than image {(h, w)}")
        
        top = (h - crop_h) // 2
        left = (w - crop_w) // 2
        
        return image[top:top + crop_h, left:left + crop_w]
    
    def color_jitter(self, image: np.ndarray, brightness: float = 0.2,
                     contrast: float = 0.2, saturation: float = 0.2) -> np.ndarray:
        """
        Randomly adjust brightness, contrast, and saturation.
        
        Args:
            image: Input image (H, W, C) in range [0, 1]
            brightness: Max brightness adjustment factor
            contrast: Max contrast adjustment factor
            saturation: Max saturation adjustment factor
        
        Returns:
            Color-jittered image
        
        Example:
            >>> aug = ImageAugmenter()
            >>> image = np.random.rand(100, 100, 3)
            >>> jittered = aug.color_jitter(image, brightness=0.3)
        """
        # Brightness
        brightness_factor = 1 + np.random.uniform(-brightness, brightness)
        image = np.clip(image * brightness_factor, 0, 1)
        
        # Contrast
        contrast_factor = 1 + np.random.uniform(-contrast, contrast)
        mean = image.mean(axis=(0, 1), keepdims=True)
        image = np.clip((image - mean) * contrast_factor + mean, 0, 1)
        
        # Saturation (convert to HSV, adjust S channel)
        if saturation > 0 and image.shape[-1] == 3:
            saturation_factor = 1 + np.random.uniform(-saturation, saturation)
            # Simple saturation adjustment in RGB space
            gray = image.mean(axis=-1, keepdims=True)
            image = np.clip((image - gray) * saturation_factor + gray, 0, 1)
        
        return image
    
    def gaussian_noise(self, image: np.ndarray, mean: float = 0.0,
                       std: float = 0.1) -> np.ndarray:
        """
        Add Gaussian noise to image.
        
        Args:
            image: Input image (H, W, C)
            mean: Mean of Gaussian noise
            std: Standard deviation of Gaussian noise
        
        Returns:
            Noisy image
        
        Example:
            >>> aug = ImageAugmenter()
            >>> image = np.random.rand(100, 100, 3)
            >>> noisy = aug.gaussian_noise(image, std=0.05)
        """
        noise = np.random.normal(mean, std, image.shape)
        noisy_image = image + noise
        return np.clip(noisy_image, 0, 1)
    
    def gaussian_blur(self, image: np.ndarray, sigma: float = 1.0) -> np.ndarray:
        """
        Apply Gaussian blur to image.
        
        Args:
            image: Input image (H, W, C)
            sigma: Standard deviation of Gaussian kernel
        
        Returns:
            Blurred image
        
        Example:
            >>> aug = ImageAugmenter()
            >>> image = np.random.rand(100, 100, 3)
            >>> blurred = aug.gaussian_blur(image, sigma=2.0)
        """
        from scipy.ndimage import gaussian_filter
        return gaussian_filter(image, sigma=(sigma, sigma, 0))
    
    def random_erasing(self, image: np.ndarray, probability: float = 0.5,
                       area_ratio_range: Tuple[float, float] = (0.02, 0.4),
                       aspect_ratio_range: Tuple[float, float] = (0.3, 3.3)) -> np.ndarray:
        """
        Randomly erase rectangular regions (Random Erasing augmentation).
        
        Args:
            image: Input image (H, W, C)
            probability: Probability of applying erasing
            area_ratio_range: Range of erased area ratio
            aspect_ratio_range: Range of aspect ratio
        
        Returns:
            Image with random erasing applied
        
        Example:
            >>> aug = ImageAugmenter()
            >>> image = np.random.rand(100, 100, 3)
            >>> erased = aug.random_erasing(image, probability=0.5)
        
        Reference:
            Zhong et al., "Random Erasing Data Augmentation", 2017
        """
        if np.random.random() > probability:
            return image
        
        h, w = image.shape[:2]
        area = h * w
        
        for _ in range(100):  # Try up to 100 times
            target_area = np.random.uniform(*area_ratio_range) * area
            aspect_ratio = np.random.uniform(*aspect_ratio_range)
            
            erase_h = int(np.sqrt(target_area * aspect_ratio))
            erase_w = int(np.sqrt(target_area / aspect_ratio))
            
            if erase_h < h and erase_w < w:
                top = np.random.randint(0, h - erase_h)
                left = np.random.randint(0, w - erase_w)
                
                # Erase with random values
                image = image.copy()
                image[top:top + erase_h, left:left + erase_w] = np.random.random(
                    (erase_h, erase_w, image.shape[2])
                )
                break
        
        return image
    
    def cutout(self, image: np.ndarray, n_holes: int = 1,
               length: int = 16) -> np.ndarray:
        """
        Apply Cutout augmentation (mask out square regions).
        
        Args:
            image: Input image (H, W, C)
            n_holes: Number of holes to cut out
            length: Side length of square holes
        
        Returns:
            Image with cutout applied
        
        Example:
            >>> aug = ImageAugmenter()
            >>> image = np.random.rand(100, 100, 3)
            >>> cutout_img = aug.cutout(image, n_holes=1, length=20)
        
        Reference:
            DeVries & Taylor, "Improved Regularization of CNNs with Cutout", 2017
        """
        h, w = image.shape[:2]
        image = image.copy()
        
        for _ in range(n_holes):
            y = np.random.randint(h)
            x = np.random.randint(w)
            
            y1 = np.clip(y - length // 2, 0, h)
            y2 = np.clip(y + length // 2, 0, h)
            x1 = np.clip(x - length // 2, 0, w)
            x2 = np.clip(x + length // 2, 0, w)
            
            image[y1:y2, x1:x2] = 0
        
        return image
    
    def mixup(self, image1: np.ndarray, image2: np.ndarray,
              alpha: float = 0.2) -> Tuple[np.ndarray, float]:
        """
        Apply Mixup augmentation (blend two images).
        
        Args:
            image1: First input image (H, W, C)
            image2: Second input image (H, W, C)
            alpha: Beta distribution parameter
        
        Returns:
            Tuple of (mixed image, mixing coefficient lambda)
        
        Example:
            >>> aug = ImageAugmenter()
            >>> img1 = np.random.rand(100, 100, 3)
            >>> img2 = np.random.rand(100, 100, 3)
            >>> mixed, lam = aug.mixup(img1, img2, alpha=0.2)
        
        Reference:
            Zhang et al., "mixup: Beyond Empirical Risk Minimization", 2017
        """
        if image1.shape != image2.shape:
            raise ValueError(f"Image shapes must match: {image1.shape} vs {image2.shape}")
        
        lam = np.random.beta(alpha, alpha) if alpha > 0 else 1
        mixed_image = lam * image1 + (1 - lam) * image2
        
        return mixed_image, lam
    
    def normalize(self, image: np.ndarray, mean: Tuple[float, ...],
                  std: Tuple[float, ...]) -> np.ndarray:
        """
        Normalize image with mean and standard deviation.
        
        Args:
            image: Input image (H, W, C)
            mean: Mean for each channel
            std: Standard deviation for each channel
        
        Returns:
            Normalized image
        
        Example:
            >>> aug = ImageAugmenter()
            >>> image = np.random.rand(100, 100, 3)
            >>> normalized = aug.normalize(image, mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5))
        """
        mean = np.array(mean).reshape(1, 1, -1)
        std = np.array(std).reshape(1, 1, -1)
        return (image - mean) / std


class TextAugmenter:
    """
    Text Augmentation Pipeline.
    
    Provides various augmentation techniques for text data.
    Useful for NLP tasks with limited training data.
    
    Example:
        >>> aug = TextAugmenter()
        >>> text = "The quick brown fox jumps over the lazy dog"
        >>> augmented = aug.random_deletion(text, p=0.1)
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize text augmenter.
        
        Args:
            seed: Random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)
    
    def synonym_replacement(self, text: str, n: int = 1) -> str:
        """
        Replace n words with synonyms.
        
        Note: This is a simplified version. For production, use libraries
        like NLTK with WordNet for actual synonym replacement.
        
        Args:
            text: Input text
            n: Number of words to replace
        
        Returns:
            Text with synonyms replaced
        
        Example:
            >>> aug = TextAugmenter()
            >>> text = "The quick brown fox"
            >>> augmented = aug.synonym_replacement(text, n=1)
        """
        words = text.split()
        
        # Simple synonym dictionary (expand for production use)
        synonyms = {
            'quick': ['fast', 'rapid', 'swift'],
            'brown': ['tan', 'beige', 'chocolate'],
            'lazy': ['idle', 'sluggish', 'inactive'],
            'big': ['large', 'huge', 'enormous'],
            'small': ['tiny', 'little', 'mini'],
        }
        
        for _ in range(n):
            replaceable = [i for i, w in enumerate(words) if w.lower() in synonyms]
            if not replaceable:
                break
            
            idx = random.choice(replaceable)
            word = words[idx].lower()
            words[idx] = random.choice(synonyms[word])
        
        return ' '.join(words)
    
    def random_insertion(self, text: str, n: int = 1) -> str:
        """
        Randomly insert n words into the text.
        
        Args:
            text: Input text
            n: Number of words to insert
        
        Returns:
            Text with random insertions
        
        Example:
            >>> aug = TextAugmenter()
            >>> text = "The quick fox"
            >>> augmented = aug.random_insertion(text, n=1)
        """
        words = text.split()
        
        for _ in range(n):
            if not words:
                break
            
            # Insert a random word from the text
            random_word = random.choice(words)
            random_idx = random.randint(0, len(words))
            words.insert(random_idx, random_word)
        
        return ' '.join(words)
    
    def random_swap(self, text: str, n: int = 1) -> str:
        """
        Randomly swap n pairs of words.
        
        Args:
            text: Input text
            n: Number of swaps to perform
        
        Returns:
            Text with random swaps
        
        Example:
            >>> aug = TextAugmenter()
            >>> text = "The quick brown fox"
            >>> augmented = aug.random_swap(text, n=1)
        """
        words = text.split()
        
        for _ in range(n):
            if len(words) < 2:
                break
            
            idx1, idx2 = random.sample(range(len(words)), 2)
            words[idx1], words[idx2] = words[idx2], words[idx1]
        
        return ' '.join(words)
    
    def random_deletion(self, text: str, p: float = 0.1) -> str:
        """
        Randomly delete words with probability p.
        
        Args:
            text: Input text
            p: Probability of deleting each word
        
        Returns:
            Text with random deletions
        
        Example:
            >>> aug = TextAugmenter()
            >>> text = "The quick brown fox jumps"
            >>> augmented = aug.random_deletion(text, p=0.2)
        """
        words = text.split()
        
        if len(words) == 1:
            return text
        
        new_words = [w for w in words if random.random() > p]
        
        # If all words deleted, return random word
        if len(new_words) == 0:
            return random.choice(words)
        
        return ' '.join(new_words)


class AugmentationPipeline:
    """
    Composable augmentation pipeline.
    
    Chain multiple augmentation operations together.
    
    Example:
        >>> from ilovetools.ml.augmentation import ImageAugmenter, AugmentationPipeline
        >>> aug = ImageAugmenter()
        >>> pipeline = AugmentationPipeline([
        ...     lambda x: aug.random_rotation(x, max_angle=15),
        ...     lambda x: aug.horizontal_flip(x) if np.random.random() > 0.5 else x,
        ...     lambda x: aug.gaussian_noise(x, std=0.05)
        ... ])
        >>> image = np.random.rand(100, 100, 3)
        >>> augmented = pipeline(image)
    """
    
    def __init__(self, transforms: List):
        """
        Initialize pipeline.
        
        Args:
            transforms: List of augmentation functions
        """
        self.transforms = transforms
    
    def __call__(self, data):
        """Apply all transforms in sequence."""
        for transform in self.transforms:
            data = transform(data)
        return data
    
    def add(self, transform):
        """Add transform to pipeline."""
        self.transforms.append(transform)
    
    def remove(self, index: int):
        """Remove transform at index."""
        del self.transforms[index]


# Convenience functions
def rotate_image(image: np.ndarray, angle: float) -> np.ndarray:
    """Rotate image by angle."""
    return ImageAugmenter().rotate(image, angle)


def flip_horizontal(image: np.ndarray) -> np.ndarray:
    """Flip image horizontally."""
    return ImageAugmenter().horizontal_flip(image)


def add_noise(image: np.ndarray, std: float = 0.1) -> np.ndarray:
    """Add Gaussian noise to image."""
    return ImageAugmenter().gaussian_noise(image, std=std)


__all__ = [
    'ImageAugmenter',
    'TextAugmenter',
    'AugmentationPipeline',
    'rotate_image',
    'flip_horizontal',
    'add_noise',
]
