"""
Image Analysis MCP Server

Provides image quality assessment and analysis tools.
Uses OpenCV, PIL, and scikit-image for local processing.
"""

from typing import Any, Dict, List, Optional, Tuple
import io
import base64
import numpy as np
from PIL import Image
from dataclasses import dataclass

from backend.mcp_servers.base_mcp_server import MCPServerBase, MCPTool
from backend.utils.logging import get_logger

logger = get_logger(__name__)

# Try to import optional dependencies
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    logger.warning("OpenCV not available, some features will be limited")

try:
    from skimage import feature, filters
    HAS_SKIMAGE = True
except ImportError:
    HAS_SKIMAGE = False
    logger.warning("scikit-image not available, some features will be limited")


@dataclass
class QualityMetrics:
    """Image quality metrics."""
    resolution: Tuple[int, int]
    blur_score: float  # Higher = sharper
    brightness: float  # 0-255 average
    contrast: float
    sharpness: float
    stripe_visibility: float  # Estimated 0-1
    overall_score: float  # 0-100

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resolution": list(self.resolution),
            "blur_score": self.blur_score,
            "brightness": self.brightness,
            "contrast": self.contrast,
            "sharpness": self.sharpness,
            "stripe_visibility": self.stripe_visibility,
            "overall_score": self.overall_score
        }


class ImageAnalysisMCPServer(MCPServerBase):
    """
    MCP server for image quality assessment and analysis.

    Provides tools for:
    - Assessing image quality for tiger identification
    - Extracting image features (edges, keypoints, texture)
    - Comparing stripe patterns
    - Detecting potential image manipulation

    All processing is done locally using OpenCV, PIL, and scikit-image.
    """

    def __init__(self):
        """Initialize the Image Analysis MCP server."""
        super().__init__("image_analysis")
        self._register_tools()
        logger.info("ImageAnalysisMCPServer initialized")

    def _register_tools(self):
        """Register available tools."""
        self.tools = {
            "assess_image_quality": MCPTool(
                name="assess_image_quality",
                description="Assess image quality for tiger identification suitability. Returns resolution, blur, brightness, contrast, and overall quality score.",
                parameters={
                    "type": "object",
                    "properties": {
                        "image_data": {
                            "type": "string",
                            "description": "Base64 encoded image data"
                        },
                        "image_path": {
                            "type": "string",
                            "description": "Path to image file (alternative to image_data)"
                        },
                        "detection_bbox": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "Optional bounding box [x1, y1, x2, y2] to analyze specific region"
                        }
                    }
                },
                handler=self._handle_assess_quality
            ),
            "analyze_image_features": MCPTool(
                name="analyze_image_features",
                description="Extract visual features from an image including edges, histogram, texture, and keypoints.",
                parameters={
                    "type": "object",
                    "properties": {
                        "image_data": {
                            "type": "string",
                            "description": "Base64 encoded image data"
                        },
                        "image_path": {
                            "type": "string",
                            "description": "Path to image file"
                        },
                        "features_to_extract": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["edges", "color_histogram", "texture", "keypoints", "contours"]
                            },
                            "description": "Which features to extract",
                            "default": ["edges", "color_histogram"]
                        }
                    }
                },
                handler=self._handle_analyze_features
            ),
            "compare_stripe_patterns": MCPTool(
                name="compare_stripe_patterns",
                description="Compare stripe patterns between two tiger images using edge detection and pattern matching.",
                parameters={
                    "type": "object",
                    "properties": {
                        "image1_data": {
                            "type": "string",
                            "description": "Base64 encoded first image"
                        },
                        "image2_data": {
                            "type": "string",
                            "description": "Base64 encoded second image"
                        },
                        "comparison_method": {
                            "type": "string",
                            "enum": ["edge_matching", "histogram", "feature_matching"],
                            "description": "Method to use for comparison",
                            "default": "edge_matching"
                        }
                    },
                    "required": ["image1_data", "image2_data"]
                },
                handler=self._handle_compare_patterns
            ),
            "detect_image_manipulation": MCPTool(
                name="detect_image_manipulation",
                description="Detect signs of image manipulation or tampering using Error Level Analysis (ELA) and metadata analysis.",
                parameters={
                    "type": "object",
                    "properties": {
                        "image_data": {
                            "type": "string",
                            "description": "Base64 encoded image data"
                        },
                        "image_path": {
                            "type": "string",
                            "description": "Path to image file"
                        },
                        "sensitivity": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                            "description": "Detection sensitivity level",
                            "default": "medium"
                        }
                    }
                },
                handler=self._handle_detect_manipulation
            )
        }

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools."""
        return [tool.to_dict() for tool in self.tools.values()]

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool."""
        if tool_name not in self.tools:
            return {"error": f"Tool {tool_name} not found"}

        try:
            return await self.tools[tool_name].call(arguments)
        except Exception as e:
            logger.error(f"Tool call failed: {tool_name}", error=str(e), exc_info=True)
            return {"error": str(e)}

    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources."""
        return []

    def _load_image(
        self,
        image_data: Optional[str] = None,
        image_path: Optional[str] = None
    ) -> Image.Image:
        """Load image from base64 data or file path."""
        if image_path:
            return Image.open(image_path)
        elif image_data:
            # Decode base64
            image_bytes = base64.b64decode(image_data)
            return Image.open(io.BytesIO(image_bytes))
        else:
            raise ValueError("Either image_data or image_path must be provided")

    def _pil_to_cv2(self, pil_image: Image.Image) -> np.ndarray:
        """Convert PIL image to OpenCV format."""
        if pil_image.mode == 'RGBA':
            pil_image = pil_image.convert('RGB')
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    async def _handle_assess_quality(
        self,
        image_data: Optional[str] = None,
        image_path: Optional[str] = None,
        detection_bbox: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """Handle image quality assessment."""
        try:
            # Load image
            pil_image = self._load_image(image_data, image_path)

            # Crop to bbox if provided
            if detection_bbox and len(detection_bbox) == 4:
                x1, y1, x2, y2 = [int(v) for v in detection_bbox]
                pil_image = pil_image.crop((x1, y1, x2, y2))

            # Get resolution
            width, height = pil_image.size
            resolution = (width, height)

            # Convert to grayscale for analysis
            gray_image = pil_image.convert('L')
            gray_array = np.array(gray_image)

            # Calculate metrics
            blur_score = self._calculate_blur_score(gray_array)
            brightness = float(np.mean(gray_array))
            contrast = float(np.std(gray_array))
            sharpness = self._calculate_sharpness(gray_array)
            stripe_visibility = self._estimate_stripe_visibility(gray_array)

            # Calculate overall score
            overall_score = self._calculate_overall_score(
                resolution, blur_score, brightness, contrast, sharpness, stripe_visibility
            )

            metrics = QualityMetrics(
                resolution=resolution,
                blur_score=blur_score,
                brightness=brightness,
                contrast=contrast,
                sharpness=sharpness,
                stripe_visibility=stripe_visibility,
                overall_score=overall_score
            )

            # Generate recommendations
            recommendations = self._generate_quality_recommendations(metrics)

            return {
                "success": True,
                "metrics": metrics.to_dict(),
                "suitable_for_identification": overall_score >= 60,
                "recommendations": recommendations,
                "message": self._get_quality_message(overall_score)
            }

        except Exception as e:
            logger.error(f"Quality assessment failed: {e}")
            return {"error": str(e), "success": False}

    def _calculate_blur_score(self, gray_array: np.ndarray) -> float:
        """Calculate blur score using Laplacian variance."""
        if HAS_CV2:
            laplacian = cv2.Laplacian(gray_array, cv2.CV_64F)
            return float(laplacian.var())
        else:
            # Fallback: simple gradient-based blur detection
            gx = np.diff(gray_array, axis=1)
            gy = np.diff(gray_array, axis=0)
            return float(np.mean(np.abs(gx)) + np.mean(np.abs(gy)))

    def _calculate_sharpness(self, gray_array: np.ndarray) -> float:
        """Calculate sharpness score."""
        if HAS_CV2:
            # Use Sobel gradients
            sobelx = cv2.Sobel(gray_array, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(gray_array, cv2.CV_64F, 0, 1, ksize=3)
            gradient_magnitude = np.sqrt(sobelx**2 + sobely**2)
            return float(np.mean(gradient_magnitude))
        else:
            return self._calculate_blur_score(gray_array) / 10  # Approximate

    def _estimate_stripe_visibility(self, gray_array: np.ndarray) -> float:
        """Estimate stripe pattern visibility (0-1)."""
        # Stripes should produce high-frequency horizontal/vertical components
        if HAS_CV2:
            # Use Canny edge detection
            edges = cv2.Canny(gray_array, 50, 150)
            edge_density = np.mean(edges) / 255.0

            # Also check for directional patterns
            sobelx = cv2.Sobel(gray_array, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(gray_array, cv2.CV_64F, 0, 1, ksize=3)

            # Tiger stripes tend to be more vertical
            vertical_strength = np.mean(np.abs(sobelx))
            horizontal_strength = np.mean(np.abs(sobely))

            # Good stripes have both but typically more vertical
            pattern_score = min(1.0, (vertical_strength + horizontal_strength) / 100)

            return min(1.0, (edge_density * 0.5 + pattern_score * 0.5))
        else:
            # Fallback: use standard deviation as proxy
            return min(1.0, np.std(gray_array) / 64.0)

    def _calculate_overall_score(
        self,
        resolution: Tuple[int, int],
        blur_score: float,
        brightness: float,
        contrast: float,
        sharpness: float,
        stripe_visibility: float
    ) -> float:
        """Calculate overall quality score (0-100)."""
        score = 100.0

        # Resolution penalty
        min_dim = min(resolution)
        if min_dim < 640:
            score -= 30
        elif min_dim < 1024:
            score -= 10

        # Blur penalty (blur_score < 100 is usually blurry)
        if blur_score < 50:
            score -= 30
        elif blur_score < 100:
            score -= 15

        # Brightness penalty (too dark or too bright)
        if brightness < 50 or brightness > 220:
            score -= 20
        elif brightness < 80 or brightness > 180:
            score -= 10

        # Contrast penalty (low contrast makes stripes hard to see)
        if contrast < 30:
            score -= 20
        elif contrast < 50:
            score -= 10

        # Stripe visibility penalty
        if stripe_visibility < 0.3:
            score -= 25
        elif stripe_visibility < 0.5:
            score -= 10

        return max(0, min(100, score))

    def _generate_quality_recommendations(self, metrics: QualityMetrics) -> List[str]:
        """Generate recommendations based on quality metrics."""
        recommendations = []

        if min(metrics.resolution) < 640:
            recommendations.append("Image resolution is too low. Use a higher resolution image (at least 640px).")

        if metrics.blur_score < 100:
            recommendations.append("Image appears blurry. Ensure the camera is in focus and steady.")

        if metrics.brightness < 50:
            recommendations.append("Image is too dark. Improve lighting conditions.")
        elif metrics.brightness > 220:
            recommendations.append("Image is overexposed. Reduce lighting or adjust camera settings.")

        if metrics.contrast < 30:
            recommendations.append("Low contrast makes stripe patterns hard to detect. Improve lighting.")

        if metrics.stripe_visibility < 0.5:
            recommendations.append("Stripe pattern is not clearly visible. Use a flank view with good lighting.")

        if not recommendations:
            recommendations.append("Image quality is good for identification.")

        return recommendations

    def _get_quality_message(self, score: float) -> str:
        """Get human-readable quality message."""
        if score >= 80:
            return "Excellent quality - ideal for identification"
        elif score >= 60:
            return "Good quality - suitable for identification"
        elif score >= 40:
            return "Fair quality - may affect identification accuracy"
        else:
            return "Poor quality - consider using a better image"

    async def _handle_analyze_features(
        self,
        image_data: Optional[str] = None,
        image_path: Optional[str] = None,
        features_to_extract: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Handle feature extraction from image."""
        try:
            if not features_to_extract:
                features_to_extract = ["edges", "color_histogram"]

            pil_image = self._load_image(image_data, image_path)
            gray_array = np.array(pil_image.convert('L'))

            results = {
                "success": True,
                "features": {}
            }

            if "edges" in features_to_extract and HAS_CV2:
                edges = cv2.Canny(gray_array, 50, 150)
                results["features"]["edges"] = {
                    "edge_count": int(np.sum(edges > 0)),
                    "edge_density": float(np.mean(edges) / 255.0),
                    "shape": list(edges.shape)
                }

            if "color_histogram" in features_to_extract:
                rgb_array = np.array(pil_image.convert('RGB'))
                histograms = {}
                for i, channel in enumerate(['red', 'green', 'blue']):
                    hist, _ = np.histogram(rgb_array[:, :, i], bins=32, range=(0, 256))
                    histograms[channel] = hist.tolist()
                results["features"]["color_histogram"] = histograms

            if "texture" in features_to_extract and HAS_CV2:
                # Local Binary Pattern approximation
                results["features"]["texture"] = {
                    "uniformity": float(np.std(gray_array)),
                    "entropy": float(-np.sum(np.histogram(gray_array, bins=256)[0] / gray_array.size *
                                            np.log2(np.histogram(gray_array, bins=256)[0] / gray_array.size + 1e-10)))
                }

            if "keypoints" in features_to_extract and HAS_CV2:
                orb = cv2.ORB_create(nfeatures=100)
                keypoints = orb.detect(gray_array, None)
                results["features"]["keypoints"] = {
                    "count": len(keypoints),
                    "locations": [(int(kp.pt[0]), int(kp.pt[1])) for kp in keypoints[:20]]
                }

            if "contours" in features_to_extract and HAS_CV2:
                edges = cv2.Canny(gray_array, 50, 150)
                contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                results["features"]["contours"] = {
                    "count": len(contours),
                    "total_length": sum(cv2.arcLength(c, False) for c in contours)
                }

            return results

        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return {"error": str(e), "success": False}

    async def _handle_compare_patterns(
        self,
        image1_data: str,
        image2_data: str,
        comparison_method: str = "edge_matching"
    ) -> Dict[str, Any]:
        """Handle stripe pattern comparison between two images."""
        try:
            img1 = self._load_image(image_data=image1_data)
            img2 = self._load_image(image_data=image2_data)

            gray1 = np.array(img1.convert('L'))
            gray2 = np.array(img2.convert('L'))

            similarity = 0.0
            details = {}

            if comparison_method == "histogram":
                # Compare color histograms
                hist1, _ = np.histogram(gray1.flatten(), bins=256, range=(0, 256))
                hist2, _ = np.histogram(gray2.flatten(), bins=256, range=(0, 256))

                hist1 = hist1.astype(float) / hist1.sum()
                hist2 = hist2.astype(float) / hist2.sum()

                similarity = 1.0 - np.sum(np.abs(hist1 - hist2)) / 2
                details["method"] = "histogram_comparison"

            elif comparison_method == "feature_matching" and HAS_CV2:
                # ORB feature matching
                orb = cv2.ORB_create(nfeatures=500)
                kp1, des1 = orb.detectAndCompute(gray1, None)
                kp2, des2 = orb.detectAndCompute(gray2, None)

                if des1 is not None and des2 is not None:
                    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
                    matches = bf.match(des1, des2)
                    good_matches = [m for m in matches if m.distance < 50]

                    similarity = len(good_matches) / max(len(kp1), len(kp2)) if kp1 and kp2 else 0
                    details["method"] = "orb_feature_matching"
                    details["keypoints_img1"] = len(kp1)
                    details["keypoints_img2"] = len(kp2)
                    details["good_matches"] = len(good_matches)

            else:  # edge_matching (default)
                if HAS_CV2:
                    edges1 = cv2.Canny(gray1, 50, 150)
                    edges2 = cv2.Canny(gray2, 50, 150)

                    # Resize to same size for comparison
                    target_size = (256, 256)
                    edges1_resized = cv2.resize(edges1, target_size)
                    edges2_resized = cv2.resize(edges2, target_size)

                    # Compare edge patterns
                    edges1_norm = edges1_resized.astype(float) / 255
                    edges2_norm = edges2_resized.astype(float) / 255

                    intersection = np.sum(edges1_norm * edges2_norm)
                    union = np.sum(edges1_norm) + np.sum(edges2_norm) - intersection

                    similarity = intersection / union if union > 0 else 0
                    details["method"] = "canny_edge_matching"
                else:
                    # Fallback: simple correlation
                    from scipy.stats import pearsonr
                    gray1_resized = np.array(img1.resize((256, 256)).convert('L')).flatten()
                    gray2_resized = np.array(img2.resize((256, 256)).convert('L')).flatten()
                    correlation, _ = pearsonr(gray1_resized, gray2_resized)
                    similarity = (correlation + 1) / 2  # Scale to 0-1
                    details["method"] = "correlation"

            return {
                "success": True,
                "similarity": float(similarity),
                "match_likely": similarity > 0.6,
                "details": details,
                "message": self._get_similarity_message(similarity)
            }

        except Exception as e:
            logger.error(f"Pattern comparison failed: {e}")
            return {"error": str(e), "success": False}

    def _get_similarity_message(self, similarity: float) -> str:
        """Get human-readable similarity message."""
        if similarity >= 0.8:
            return "Very high similarity - likely same tiger"
        elif similarity >= 0.6:
            return "Moderate similarity - possible match, needs verification"
        elif similarity >= 0.4:
            return "Low similarity - probably different tigers"
        else:
            return "Very low similarity - different tigers"

    async def _handle_detect_manipulation(
        self,
        image_data: Optional[str] = None,
        image_path: Optional[str] = None,
        sensitivity: str = "medium"
    ) -> Dict[str, Any]:
        """Handle image manipulation detection."""
        try:
            pil_image = self._load_image(image_data, image_path)
            findings = []
            manipulation_score = 0.0  # 0 = authentic, 1 = manipulated

            # Check 1: Image format and quality consistency
            if pil_image.format:
                if pil_image.format == 'PNG' and pil_image.mode == 'RGB':
                    findings.append({
                        "check": "format_analysis",
                        "finding": "PNG with RGB mode (could be re-saved JPEG)",
                        "severity": "low"
                    })
                    manipulation_score += 0.1

            # Check 2: EXIF metadata analysis
            exif = pil_image._getexif() if hasattr(pil_image, '_getexif') else None
            if exif is None:
                findings.append({
                    "check": "metadata_analysis",
                    "finding": "No EXIF metadata found (may have been stripped)",
                    "severity": "medium"
                })
                manipulation_score += 0.2
            else:
                # Check for editing software tags
                software_tag = exif.get(305, '')  # Software tag
                if any(s in str(software_tag).lower() for s in ['photoshop', 'gimp', 'lightroom']):
                    findings.append({
                        "check": "software_detection",
                        "finding": f"Edited with: {software_tag}",
                        "severity": "medium"
                    })
                    manipulation_score += 0.3

            # Check 3: Error Level Analysis (ELA) approximation
            if HAS_CV2:
                # Re-compress and compare
                gray_array = np.array(pil_image.convert('L'))

                # Encode to JPEG and decode
                _, encoded = cv2.imencode('.jpg', gray_array, [cv2.IMWRITE_JPEG_QUALITY, 95])
                recompressed = cv2.imdecode(encoded, cv2.IMREAD_GRAYSCALE)

                # Calculate error
                error = cv2.absdiff(gray_array, recompressed)
                error_mean = np.mean(error)
                error_std = np.std(error)

                # High local variance in error may indicate manipulation
                sensitivity_thresholds = {
                    "low": 15,
                    "medium": 10,
                    "high": 5
                }
                threshold = sensitivity_thresholds.get(sensitivity, 10)

                if error_std > threshold:
                    findings.append({
                        "check": "error_level_analysis",
                        "finding": f"Inconsistent compression artifacts detected (std: {error_std:.2f})",
                        "severity": "high" if error_std > threshold * 2 else "medium"
                    })
                    manipulation_score += min(0.4, error_std / 30)

            # Check 4: Resolution anomalies
            width, height = pil_image.size
            if width % 16 != 0 or height % 16 != 0:
                # Non-standard dimensions might indicate cropping
                findings.append({
                    "check": "dimension_analysis",
                    "finding": f"Non-standard dimensions ({width}x{height}) - may indicate cropping",
                    "severity": "low"
                })
                manipulation_score += 0.05

            # Determine verdict
            manipulation_score = min(1.0, manipulation_score)

            if manipulation_score < 0.2:
                verdict = "authentic"
                confidence = "high"
            elif manipulation_score < 0.5:
                verdict = "possibly_modified"
                confidence = "medium"
            else:
                verdict = "likely_manipulated"
                confidence = "high" if manipulation_score > 0.7 else "medium"

            return {
                "success": True,
                "manipulation_score": manipulation_score,
                "verdict": verdict,
                "confidence": confidence,
                "findings": findings,
                "sensitivity_used": sensitivity,
                "message": self._get_manipulation_message(verdict, manipulation_score)
            }

        except Exception as e:
            logger.error(f"Manipulation detection failed: {e}")
            return {"error": str(e), "success": False}

    def _get_manipulation_message(self, verdict: str, score: float) -> str:
        """Get human-readable manipulation verdict message."""
        if verdict == "authentic":
            return "No significant signs of manipulation detected"
        elif verdict == "possibly_modified":
            return f"Some indicators of modification found (score: {score:.0%}). Review findings for details."
        else:
            return f"Strong indicators of manipulation detected (score: {score:.0%}). Use with caution."

    # Convenience methods for direct workflow integration
    async def assess_image_quality(
        self,
        image_data: bytes,
        detection_results: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Convenience method to assess image quality for tiger identification.
        Wraps _handle_assess_quality for direct workflow use.

        Args:
            image_data: Raw image bytes
            detection_results: Optional detection results from MegaDetector

        Returns:
            Quality assessment results including overall_score and issues
        """
        import base64
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        return await self._handle_assess_quality(
            image_data=image_b64,
            detection_results=detection_results
        )

    async def analyze_image_features(
        self,
        image_data: bytes,
        features: List[str] = None
    ) -> Dict[str, Any]:
        """
        Convenience method to extract image features.
        Wraps _handle_extract_features for direct workflow use.
        """
        import base64
        if features is None:
            features = ["edges", "histogram", "keypoints"]
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        return await self._handle_extract_features(
            image_data=image_b64,
            features_to_extract=features
        )


# Singleton instance
_server_instance: Optional[ImageAnalysisMCPServer] = None


def get_image_analysis_server() -> ImageAnalysisMCPServer:
    """Get or create the singleton server instance."""
    global _server_instance
    if _server_instance is None:
        _server_instance = ImageAnalysisMCPServer()
    return _server_instance
