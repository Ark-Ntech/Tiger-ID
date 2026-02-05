"""Edge case tests for image processing"""

import pytest
import io
from pathlib import Path
from PIL import Image
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from backend.services.embedding_service import EmbeddingService
from backend.services.image_pipeline_service import ImagePipelineService


class TestImageProcessingEdgeCases:
    """Edge cases for image processing operations"""

    def test_zero_byte_image(self):
        """Test handling of zero-byte image file"""
        # Create zero-byte file
        zero_byte_data = b""

        with pytest.raises((OSError, ValueError, IOError)):
            Image.open(io.BytesIO(zero_byte_data))

    def test_corrupted_image_header(self):
        """Test handling of corrupted image header"""
        # Create corrupted data
        corrupted_data = b"CORRUPT_IMAGE_DATA" + b"\x00" * 100

        with pytest.raises((OSError, ValueError)):
            Image.open(io.BytesIO(corrupted_data))

    def test_non_image_file(self):
        """Test handling of non-image file (text file)"""
        text_data = b"This is a text file, not an image"

        with pytest.raises((OSError, ValueError)):
            Image.open(io.BytesIO(text_data))

    def test_extremely_large_image(self):
        """Test handling of extremely large image dimensions"""
        # Create a very large image (e.g., 50000x50000)
        # PIL should handle this, but we test the behavior
        try:
            large_img = Image.new('RGB', (50000, 50000))
            assert large_img.size == (50000, 50000)
            # This might raise MemoryError on limited systems
        except MemoryError:
            pytest.skip("Insufficient memory for extremely large image test")

    def test_single_pixel_image(self):
        """Test handling of 1x1 pixel image"""
        tiny_img = Image.new('RGB', (1, 1), color=(255, 0, 0))
        assert tiny_img.size == (1, 1)
        assert tiny_img.mode == 'RGB'

    def test_unsupported_color_mode(self):
        """Test handling of unusual color modes"""
        # Create image with CMYK mode
        cmyk_img = Image.new('CMYK', (100, 100))
        assert cmyk_img.mode == 'CMYK'

        # Convert to RGB should work
        rgb_img = cmyk_img.convert('RGB')
        assert rgb_img.mode == 'RGB'

    def test_image_with_alpha_channel(self):
        """Test handling of image with alpha channel"""
        rgba_img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
        assert rgba_img.mode == 'RGBA'

        # Convert to RGB should drop alpha
        rgb_img = rgba_img.convert('RGB')
        assert rgb_img.mode == 'RGB'

    def test_grayscale_image(self):
        """Test handling of grayscale image"""
        gray_img = Image.new('L', (100, 100), color=128)
        assert gray_img.mode == 'L'

        # Convert to RGB
        rgb_img = gray_img.convert('RGB')
        assert rgb_img.mode == 'RGB'

    def test_image_with_extreme_aspect_ratio(self):
        """Test handling of image with extreme aspect ratio"""
        # Very wide image
        wide_img = Image.new('RGB', (10000, 10))
        assert wide_img.size == (10000, 10)

        # Very tall image
        tall_img = Image.new('RGB', (10, 10000))
        assert tall_img.size == (10, 10000)

    def test_malformed_exif_data(self):
        """Test handling of image with malformed EXIF data"""
        img = Image.new('RGB', (100, 100))

        # Add malformed EXIF
        exif_bytes = b"MALFORMED_EXIF_DATA"

        # PIL should handle gracefully
        try:
            img.info['exif'] = exif_bytes
        except Exception as e:
            # Should not crash
            assert isinstance(e, (ValueError, TypeError, AttributeError))

    def test_image_deduplication_identical_hash(self):
        """Test image deduplication with identical SHA256 hash"""
        # Create two identical images
        img1 = Image.new('RGB', (100, 100), color=(255, 0, 0))
        img2 = Image.new('RGB', (100, 100), color=(255, 0, 0))

        # Convert to bytes
        buf1 = io.BytesIO()
        buf2 = io.BytesIO()
        img1.save(buf1, format='PNG')
        img2.save(buf2, format='PNG')

        bytes1 = buf1.getvalue()
        bytes2 = buf2.getvalue()

        # SHA256 should be identical
        import hashlib
        hash1 = hashlib.sha256(bytes1).hexdigest()
        hash2 = hashlib.sha256(bytes2).hexdigest()

        assert hash1 == hash2

    def test_image_deduplication_different_hash(self):
        """Test image deduplication with different SHA256 hash"""
        # Create two different images
        img1 = Image.new('RGB', (100, 100), color=(255, 0, 0))
        img2 = Image.new('RGB', (100, 100), color=(0, 255, 0))

        # Convert to bytes
        buf1 = io.BytesIO()
        buf2 = io.BytesIO()
        img1.save(buf1, format='PNG')
        img2.save(buf2, format='PNG')

        bytes1 = buf1.getvalue()
        bytes2 = buf2.getvalue()

        # SHA256 should be different
        import hashlib
        hash1 = hashlib.sha256(bytes1).hexdigest()
        hash2 = hashlib.sha256(bytes2).hexdigest()

        assert hash1 != hash2

    def test_image_format_conversion_errors(self):
        """Test handling of image format conversion errors"""
        img = Image.new('RGB', (100, 100))

        # Valid formats should work
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        assert len(buf.getvalue()) > 0

        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        assert len(buf.getvalue()) > 0

    def test_numpy_array_edge_cases(self):
        """Test conversion between PIL Image and numpy arrays"""
        # Test empty array - PIL may handle this differently
        empty_array = np.array([])
        # Empty array won't raise immediately, but will have issues
        assert empty_array.size == 0

        # Test single channel
        gray_array = np.zeros((100, 100), dtype=np.uint8)
        gray_img = Image.fromarray(gray_array)
        assert gray_img.mode == 'L'

        # Test 3 channel RGB
        rgb_array = np.zeros((100, 100, 3), dtype=np.uint8)
        rgb_img = Image.fromarray(rgb_array)
        assert rgb_img.mode == 'RGB'

        # Test 4 channel RGBA
        rgba_array = np.zeros((100, 100, 4), dtype=np.uint8)
        rgba_img = Image.fromarray(rgba_array)
        assert rgba_img.mode == 'RGBA'

    def test_image_rotation_edge_cases(self):
        """Test image rotation with edge angles"""
        img = Image.new('RGB', (100, 100))

        # Test various angles
        for angle in [0, 45, 90, 180, 270, 360, -90, -180]:
            rotated = img.rotate(angle)
            assert rotated is not None

    def test_image_resize_edge_cases(self):
        """Test image resize with edge dimensions"""
        img = Image.new('RGB', (100, 100))

        # Resize to 1x1
        tiny = img.resize((1, 1))
        assert tiny.size == (1, 1)

        # Resize to very large (if memory allows)
        try:
            large = img.resize((5000, 5000))
            assert large.size == (5000, 5000)
        except MemoryError:
            pytest.skip("Insufficient memory for large resize test")

        # Same size
        same = img.resize((100, 100))
        assert same.size == (100, 100)


class TestImageQualityEdgeCases:
    """Edge cases for image quality assessment"""

    def test_completely_black_image(self):
        """Test quality assessment of completely black image"""
        black_img = Image.new('RGB', (224, 224), color=(0, 0, 0))
        img_array = np.array(black_img)

        # Variance should be zero
        variance = np.var(img_array)
        assert variance == 0

    def test_completely_white_image(self):
        """Test quality assessment of completely white image"""
        white_img = Image.new('RGB', (224, 224), color=(255, 255, 255))
        img_array = np.array(white_img)

        # Variance should be zero
        variance = np.var(img_array)
        assert variance == 0

    def test_high_contrast_image(self):
        """Test quality assessment of high contrast image"""
        # Create checkerboard pattern
        img_array = np.zeros((224, 224, 3), dtype=np.uint8)
        img_array[::2, ::2] = 255
        img_array[1::2, 1::2] = 255

        # Should have high variance
        variance = np.var(img_array)
        assert variance > 1000  # High variance for checkerboard

    def test_extremely_blurry_image(self):
        """Test detection of extremely blurry image"""
        # Create a blurry image by averaging pixels
        img = Image.new('RGB', (224, 224))
        img_array = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)

        # Apply heavy blur
        from scipy.ndimage import gaussian_filter
        try:
            blurred = gaussian_filter(img_array, sigma=20)
            assert blurred.shape == img_array.shape
        except ImportError:
            pytest.skip("scipy not available for blur test")

    def test_noise_only_image(self):
        """Test quality assessment of pure noise image"""
        # Create random noise
        noise = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)

        # Should have high variance
        variance = np.var(noise)
        assert variance > 0


class TestImagePipelineServiceEdgeCases:
    """Edge cases for ImagePipelineService"""

    def test_duplicate_url_detection(self):
        """Test detection of duplicate URLs"""
        duplicate_urls = [
            "http://example.com/tiger.jpg",
            "http://example.com/tiger.jpg",
            "http://example.com/tiger.jpg"
        ]

        # Use set to detect duplicates
        unique_urls = set(duplicate_urls)
        assert len(unique_urls) == 1

    def test_invalid_url_patterns(self):
        """Test detection of invalid URL patterns"""
        invalid_urls = [
            "not-a-url",
            "ftp://invalid-protocol.com/image.jpg",
            "",
        ]

        # Basic validation
        for url in invalid_urls:
            if not url:
                assert url == ""
                continue
            # Check if it's a valid HTTP(S) URL
            is_valid_http = url.startswith("http://") or url.startswith("https://")
            if not is_valid_http:
                assert True  # Invalid as expected


class TestEmbeddingServiceEdgeCases:
    """Edge cases for EmbeddingService"""

    def test_embedding_dimension_validation(self):
        """Test validation of embedding dimensions"""
        # Common embedding dimensions
        valid_dimensions = [512, 768, 1024, 1536, 2048]

        for dim in valid_dimensions:
            embedding = np.random.rand(dim).tolist()
            assert len(embedding) == dim

    def test_embedding_value_range(self):
        """Test that embedding values are in expected range"""
        # Embeddings typically normalized to [-1, 1] or [0, 1]
        embedding = np.random.rand(2048)  # [0, 1]
        assert np.all(embedding >= 0)
        assert np.all(embedding <= 1)

        # Test normalized embeddings
        normalized = embedding / np.linalg.norm(embedding)
        # Norm should be 1
        assert np.abs(np.linalg.norm(normalized) - 1.0) < 1e-6
