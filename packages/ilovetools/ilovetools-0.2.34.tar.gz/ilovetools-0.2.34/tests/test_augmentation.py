"""
Comprehensive Tests for Data Augmentation

Tests all augmentation techniques with various scenarios and edge cases.

Author: Ali Mehdi
Date: January 15, 2026
"""

import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ilovetools.ml.augmentation import (
    ImageAugmenter,
    TextAugmenter,
    AugmentationPipeline,
    rotate_image,
    flip_horizontal,
    add_noise,
)


def test_image_augmenter_init():
    """Test ImageAugmenter initialization."""
    print("Testing ImageAugmenter initialization...")
    
    aug = ImageAugmenter()
    assert aug is not None
    
    aug_seeded = ImageAugmenter(seed=42)
    assert aug_seeded is not None
    
    print("✓ ImageAugmenter initialization test passed")


def test_horizontal_flip():
    """Test horizontal flip."""
    print("Testing horizontal flip...")
    
    aug = ImageAugmenter()
    image = np.random.rand(100, 100, 3)
    
    flipped = aug.horizontal_flip(image)
    
    assert flipped.shape == image.shape
    assert np.allclose(flipped, np.fliplr(image))
    
    # Double flip should return original
    double_flipped = aug.horizontal_flip(flipped)
    assert np.allclose(double_flipped, image)
    
    print("✓ Horizontal flip test passed")


def test_vertical_flip():
    """Test vertical flip."""
    print("Testing vertical flip...")
    
    aug = ImageAugmenter()
    image = np.random.rand(100, 100, 3)
    
    flipped = aug.vertical_flip(image)
    
    assert flipped.shape == image.shape
    assert np.allclose(flipped, np.flipud(image))
    
    print("✓ Vertical flip test passed")


def test_random_crop():
    """Test random crop."""
    print("Testing random crop...")
    
    aug = ImageAugmenter(seed=42)
    image = np.random.rand(224, 224, 3)
    
    cropped = aug.random_crop(image, crop_size=(128, 128))
    
    assert cropped.shape == (128, 128, 3)
    
    # Test error on invalid crop size
    try:
        aug.random_crop(image, crop_size=(300, 300))
        assert False, "Should raise ValueError"
    except ValueError:
        pass
    
    print("✓ Random crop test passed")


def test_center_crop():
    """Test center crop."""
    print("Testing center crop...")
    
    aug = ImageAugmenter()
    image = np.random.rand(224, 224, 3)
    
    cropped = aug.center_crop(image, crop_size=(128, 128))
    
    assert cropped.shape == (128, 128, 3)
    
    # Verify it's actually centered
    top = (224 - 128) // 2
    left = (224 - 128) // 2
    expected = image[top:top + 128, left:left + 128]
    assert np.allclose(cropped, expected)
    
    print("✓ Center crop test passed")


def test_color_jitter():
    """Test color jitter."""
    print("Testing color jitter...")
    
    aug = ImageAugmenter(seed=42)
    image = np.random.rand(100, 100, 3)
    
    jittered = aug.color_jitter(image, brightness=0.2, contrast=0.2, saturation=0.2)
    
    assert jittered.shape == image.shape
    assert jittered.min() >= 0
    assert jittered.max() <= 1
    
    print("✓ Color jitter test passed")


def test_gaussian_noise():
    """Test Gaussian noise."""
    print("Testing Gaussian noise...")
    
    aug = ImageAugmenter(seed=42)
    image = np.random.rand(100, 100, 3)
    
    noisy = aug.gaussian_noise(image, mean=0.0, std=0.1)
    
    assert noisy.shape == image.shape
    assert noisy.min() >= 0
    assert noisy.max() <= 1
    
    # Noise should change the image
    assert not np.allclose(noisy, image)
    
    print("✓ Gaussian noise test passed")


def test_gaussian_blur():
    """Test Gaussian blur."""
    print("Testing Gaussian blur...")
    
    aug = ImageAugmenter()
    image = np.random.rand(100, 100, 3)
    
    blurred = aug.gaussian_blur(image, sigma=2.0)
    
    assert blurred.shape == image.shape
    
    # Blurred image should be different
    assert not np.allclose(blurred, image)
    
    print("✓ Gaussian blur test passed")


def test_random_erasing():
    """Test random erasing."""
    print("Testing random erasing...")
    
    aug = ImageAugmenter(seed=42)
    image = np.random.rand(100, 100, 3)
    
    # With probability 1.0, should always erase
    erased = aug.random_erasing(image, probability=1.0)
    
    assert erased.shape == image.shape
    
    # With probability 0.0, should never erase
    not_erased = aug.random_erasing(image, probability=0.0)
    assert np.allclose(not_erased, image)
    
    print("✓ Random erasing test passed")


def test_cutout():
    """Test cutout."""
    print("Testing cutout...")
    
    aug = ImageAugmenter(seed=42)
    image = np.ones((100, 100, 3))
    
    cutout_img = aug.cutout(image, n_holes=1, length=20)
    
    assert cutout_img.shape == image.shape
    
    # Should have some zeros (cutout regions)
    assert (cutout_img == 0).any()
    
    print("✓ Cutout test passed")


def test_mixup():
    """Test mixup."""
    print("Testing mixup...")
    
    aug = ImageAugmenter(seed=42)
    image1 = np.ones((100, 100, 3))
    image2 = np.zeros((100, 100, 3))
    
    mixed, lam = aug.mixup(image1, image2, alpha=0.2)
    
    assert mixed.shape == image1.shape
    assert 0 <= lam <= 1
    
    # Mixed image should be between image1 and image2
    assert mixed.min() >= 0
    assert mixed.max() <= 1
    
    # Test shape mismatch error
    try:
        aug.mixup(image1, np.ones((50, 50, 3)))
        assert False, "Should raise ValueError"
    except ValueError:
        pass
    
    print("✓ Mixup test passed")


def test_normalize():
    """Test normalization."""
    print("Testing normalization...")
    
    aug = ImageAugmenter()
    image = np.random.rand(100, 100, 3)
    
    normalized = aug.normalize(image, mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5))
    
    assert normalized.shape == image.shape
    
    # Check normalization is applied
    expected = (image - 0.5) / 0.5
    assert np.allclose(normalized, expected)
    
    print("✓ Normalization test passed")


def test_text_augmenter_init():
    """Test TextAugmenter initialization."""
    print("Testing TextAugmenter initialization...")
    
    aug = TextAugmenter()
    assert aug is not None
    
    aug_seeded = TextAugmenter(seed=42)
    assert aug_seeded is not None
    
    print("✓ TextAugmenter initialization test passed")


def test_synonym_replacement():
    """Test synonym replacement."""
    print("Testing synonym replacement...")
    
    aug = TextAugmenter(seed=42)
    text = "The quick brown fox"
    
    augmented = aug.synonym_replacement(text, n=1)
    
    assert isinstance(augmented, str)
    assert len(augmented.split()) == len(text.split())
    
    print("✓ Synonym replacement test passed")


def test_random_insertion():
    """Test random insertion."""
    print("Testing random insertion...")
    
    aug = TextAugmenter(seed=42)
    text = "The quick fox"
    
    augmented = aug.random_insertion(text, n=1)
    
    assert isinstance(augmented, str)
    assert len(augmented.split()) == len(text.split()) + 1
    
    print("✓ Random insertion test passed")


def test_random_swap():
    """Test random swap."""
    print("Testing random swap...")
    
    aug = TextAugmenter(seed=42)
    text = "The quick brown fox"
    
    augmented = aug.random_swap(text, n=1)
    
    assert isinstance(augmented, str)
    assert len(augmented.split()) == len(text.split())
    
    # Words should be same, just reordered
    assert set(augmented.split()) == set(text.split())
    
    print("✓ Random swap test passed")


def test_random_deletion():
    """Test random deletion."""
    print("Testing random deletion...")
    
    aug = TextAugmenter(seed=42)
    text = "The quick brown fox jumps"
    
    augmented = aug.random_deletion(text, p=0.2)
    
    assert isinstance(augmented, str)
    assert len(augmented.split()) <= len(text.split())
    
    # Single word should not be deleted
    single_word = "Hello"
    result = aug.random_deletion(single_word, p=0.5)
    assert result == single_word
    
    print("✓ Random deletion test passed")


def test_augmentation_pipeline():
    """Test augmentation pipeline."""
    print("Testing augmentation pipeline...")
    
    aug = ImageAugmenter(seed=42)
    
    pipeline = AugmentationPipeline([
        lambda x: aug.horizontal_flip(x),
        lambda x: aug.gaussian_noise(x, std=0.05)
    ])
    
    image = np.random.rand(100, 100, 3)
    augmented = pipeline(image)
    
    assert augmented.shape == image.shape
    
    # Test add and remove
    pipeline.add(lambda x: aug.gaussian_blur(x, sigma=1.0))
    assert len(pipeline.transforms) == 3
    
    pipeline.remove(2)
    assert len(pipeline.transforms) == 2
    
    print("✓ Augmentation pipeline test passed")


def test_convenience_functions():
    """Test convenience functions."""
    print("Testing convenience functions...")
    
    image = np.random.rand(100, 100, 3)
    
    # Rotate
    rotated = rotate_image(image, angle=45)
    assert rotated.shape == image.shape
    
    # Flip
    flipped = flip_horizontal(image)
    assert flipped.shape == image.shape
    
    # Noise
    noisy = add_noise(image, std=0.1)
    assert noisy.shape == image.shape
    
    print("✓ Convenience functions test passed")


def test_reproducibility():
    """Test reproducibility with seed."""
    print("Testing reproducibility...")
    
    # Image augmentation
    aug1 = ImageAugmenter(seed=42)
    aug2 = ImageAugmenter(seed=42)
    
    image = np.random.rand(100, 100, 3)
    
    result1 = aug1.random_rotation(image, max_angle=30)
    result2 = aug2.random_rotation(image, max_angle=30)
    
    assert np.allclose(result1, result2)
    
    # Text augmentation
    text_aug1 = TextAugmenter(seed=42)
    text_aug2 = TextAugmenter(seed=42)
    
    text = "The quick brown fox"
    
    text_result1 = text_aug1.random_swap(text, n=2)
    text_result2 = text_aug2.random_swap(text, n=2)
    
    assert text_result1 == text_result2
    
    print("✓ Reproducibility test passed")


def test_edge_cases():
    """Test edge cases."""
    print("Testing edge cases...")
    
    aug = ImageAugmenter()
    
    # Small image
    small_image = np.random.rand(10, 10, 3)
    flipped = aug.horizontal_flip(small_image)
    assert flipped.shape == small_image.shape
    
    # Single channel image
    gray_image = np.random.rand(100, 100, 1)
    noisy = aug.gaussian_noise(gray_image, std=0.1)
    assert noisy.shape == gray_image.shape
    
    # Empty text
    text_aug = TextAugmenter()
    empty_text = ""
    result = text_aug.random_deletion(empty_text, p=0.5)
    assert result == ""
    
    print("✓ Edge cases test passed")


def run_all_tests():
    """Run all augmentation tests."""
    print("=" * 80)
    print("RUNNING DATA AUGMENTATION TESTS")
    print("=" * 80)
    print()
    
    tests = [
        test_image_augmenter_init,
        test_horizontal_flip,
        test_vertical_flip,
        test_random_crop,
        test_center_crop,
        test_color_jitter,
        test_gaussian_noise,
        test_gaussian_blur,
        test_random_erasing,
        test_cutout,
        test_mixup,
        test_normalize,
        test_text_augmenter_init,
        test_synonym_replacement,
        test_random_insertion,
        test_random_swap,
        test_random_deletion,
        test_augmentation_pipeline,
        test_convenience_functions,
        test_reproducibility,
        test_edge_cases,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        print()
    
    print("=" * 80)
    print(f"TESTS COMPLETED: {passed} passed, {failed} failed")
    print("=" * 80)
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! 🎉\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
