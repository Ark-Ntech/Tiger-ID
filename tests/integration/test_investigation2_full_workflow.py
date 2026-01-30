#!/usr/bin/env python3
"""
Comprehensive End-to-End Test for Investigation 2.0 Workflow

This script tests the complete Investigation 2.0 workflow with:
- Real tiger images from the ATRW dataset
- Full 7-phase execution (parse -> web_intelligence -> detection -> matching -> database_search -> omnivinci -> report)
- Gemini Search Grounding verification (citations)
- Gemini Pro report generation verification
- Phase-by-phase validation and output capture

Usage:
    python test_investigation2_full_workflow.py

Requirements:
    - GEMINI_API_KEY environment variable set
    - PostgreSQL database running (or MODAL_USE_MOCK=true for mocked responses)
    - Tiger images in data/models/atrw/images/Amur Tigers/test/
"""

import asyncio
import os
import sys
import json
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4
from typing import Dict, Any, List, Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment variables for testing
# Note: MODAL_USE_MOCK defaults to false in .env for production
# Set to true here only if you want to test without real Modal calls
os.environ.setdefault("MODAL_USE_MOCK", "false")  # Use real Modal responses
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("DEBUG", "true")


class Investigation2WorkflowTester:
    """End-to-end tester for Investigation 2.0 workflow"""

    def __init__(self):
        self.test_results: Dict[str, Any] = {
            "test_started_at": datetime.utcnow().isoformat(),
            "phases_tested": [],
            "errors": [],
            "warnings": [],
            "success": False
        }
        self.workflow = None
        self.db_session = None
        self.investigation_id: Optional[UUID] = None

    def log(self, message: str, level: str = "INFO"):
        """Log with timestamp and level"""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        prefix = {
            "INFO": "[INFO]",
            "SUCCESS": "[SUCCESS]",
            "ERROR": "[ERROR]",
            "WARNING": "[WARNING]",
            "PHASE": "[PHASE]"
        }.get(level, "[LOG]")
        print(f"{timestamp} {prefix} {message}")

    async def setup(self):
        """Setup test environment"""
        self.log("=" * 80)
        self.log("INVESTIGATION 2.0 WORKFLOW END-TO-END TEST")
        self.log("=" * 80)
        self.log("")

        # Check environment
        self.log("Checking environment configuration...")

        gemini_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_key:
            self.log("GEMINI_API_KEY not set - Gemini features will fail!", "WARNING")
            self.test_results["warnings"].append("GEMINI_API_KEY not configured")
        else:
            self.log(f"GEMINI_API_KEY: {gemini_key[:8]}...{gemini_key[-4:]}", "SUCCESS")

        modal_mock = os.environ.get("MODAL_USE_MOCK", "false").lower() == "true"
        self.log(f"MODAL_USE_MOCK: {modal_mock}")

        # Import components
        self.log("")
        self.log("Importing workflow components...")
        try:
            from backend.agents.investigation2_workflow import Investigation2Workflow
            self.log("Imports successful", "SUCCESS")
        except ImportError as e:
            self.log(f"Import error: {e}", "ERROR")
            self.test_results["errors"].append(f"Import error: {e}")
            raise

        # For this test, we'll run WITHOUT a database to avoid PostgreSQL dependency
        # The workflow is designed to work without a database session
        self.log("")
        self.log("Running in database-free mode (workflow handles None db)...")
        self.db_session = None
        self.log("Database session: None (skipping DB operations)", "WARNING")
        self.test_results["warnings"].append("Running without database connection")

        # Generate investigation ID
        self.investigation_id = uuid4()
        self.log(f"Generated investigation ID: {self.investigation_id}", "SUCCESS")

        # Initialize workflow WITHOUT database
        self.log("")
        self.log("Initializing Investigation2Workflow (db=None)...")
        try:
            self.workflow = Investigation2Workflow(db=None)
            self.log("Workflow initialized", "SUCCESS")
        except Exception as e:
            self.log(f"Workflow initialization failed: {e}", "ERROR")
            self.test_results["errors"].append(f"Workflow init error: {e}")
            raise

    def load_test_image(self) -> bytes:
        """Load a test tiger image from ATRW dataset"""
        self.log("")
        self.log("Loading test tiger image...")

        # Try multiple image paths
        image_paths = [
            project_root / "data" / "models" / "atrw" / "images" / "Amur Tigers" / "test" / "000000.jpg",
            project_root / "data" / "models" / "atrw" / "images" / "Amur Tigers" / "test" / "000004.jpg",
            project_root / "data" / "models" / "atrw" / "images" / "Amur Tigers" / "test" / "000005.jpg",
        ]

        for image_path in image_paths:
            if image_path.exists():
                with open(image_path, "rb") as f:
                    image_bytes = f.read()
                self.log(f"Loaded image: {image_path.name} ({len(image_bytes)} bytes)", "SUCCESS")
                self.test_results["test_image"] = str(image_path)
                self.test_results["test_image_size"] = len(image_bytes)
                return image_bytes

        # Create a minimal test image if no real images available
        self.log("No test images found, creating synthetic test image...", "WARNING")
        try:
            from PIL import Image
            import io

            # Create a simple orange/black striped image (tiger-like)
            img = Image.new("RGB", (640, 480), color=(255, 165, 0))
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG")
            image_bytes = buffer.getvalue()
            self.log(f"Created synthetic test image ({len(image_bytes)} bytes)", "WARNING")
            self.test_results["test_image"] = "synthetic"
            self.test_results["test_image_size"] = len(image_bytes)
            return image_bytes
        except Exception as e:
            self.log(f"Failed to create test image: {e}", "ERROR")
            raise

    async def run_workflow(self, image_bytes: bytes) -> Dict[str, Any]:
        """Run the complete workflow"""
        self.log("")
        self.log("=" * 60)
        self.log("STARTING INVESTIGATION 2.0 WORKFLOW")
        self.log("=" * 60)

        context = {
            "location": "Primorsky Krai, Russia",
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "notes": "E2E test of Gemini migration - testing all 7 phases"
        }

        self.log(f"Investigation ID: {self.investigation_id}")
        self.log(f"Context: {json.dumps(context, indent=2)}")
        self.log("")

        try:
            # Run the workflow
            final_state = await self.workflow.run(
                investigation_id=self.investigation_id,
                uploaded_image=image_bytes,
                context=context
            )
            return final_state
        except Exception as e:
            self.log(f"Workflow execution failed: {e}", "ERROR")
            self.test_results["errors"].append(f"Workflow error: {e}")
            import traceback
            self.log(traceback.format_exc(), "ERROR")
            raise

    def validate_phase_results(self, final_state: Dict[str, Any]):
        """Validate results from each phase"""
        self.log("")
        self.log("=" * 60)
        self.log("VALIDATING PHASE RESULTS")
        self.log("=" * 60)

        # Phase 1: Upload and Parse
        self.log("")
        self.log("PHASE 1: Upload and Parse", "PHASE")
        self.log("-" * 40)

        phase_result = {
            "name": "upload_and_parse",
            "status": "unknown",
            "details": {}
        }

        if final_state.get("uploaded_image"):
            phase_result["status"] = "success"
            phase_result["details"]["image_size"] = len(final_state["uploaded_image"])
            self.log(f"Image uploaded: {len(final_state['uploaded_image'])} bytes", "SUCCESS")
        else:
            phase_result["status"] = "failed"
            self.log("No image in final state", "ERROR")

        self.test_results["phases_tested"].append(phase_result)

        # Phase 2: Web Intelligence (Gemini Search Grounding)
        self.log("")
        self.log("PHASE 2: Web Intelligence (Gemini Search Grounding)", "PHASE")
        self.log("-" * 40)

        phase_result = {
            "name": "web_intelligence",
            "status": "unknown",
            "details": {}
        }

        reverse_search = final_state.get("reverse_search_results", {})
        if isinstance(reverse_search, dict):
            provider = reverse_search.get("provider", "unknown")
            citations = reverse_search.get("citations", [])
            summary = reverse_search.get("summary", "")
            query = reverse_search.get("query", "")
            error = reverse_search.get("error")

            phase_result["details"]["provider"] = provider
            phase_result["details"]["citations_count"] = len(citations)
            phase_result["details"]["summary_length"] = len(summary)
            phase_result["details"]["search_query"] = query

            if error:
                phase_result["status"] = "error"
                phase_result["details"]["error"] = str(error)
                self.log(f"Web intelligence error: {error}", "ERROR")
            elif provider == "gemini_search_grounding":
                phase_result["status"] = "success"
                self.log(f"Provider: {provider}", "SUCCESS")
                self.log(f"Search Query: {query}", "INFO")
                self.log(f"Citations found: {len(citations)}", "SUCCESS" if len(citations) > 0 else "WARNING")
                self.log(f"Summary length: {len(summary)} chars", "INFO")

                if len(citations) > 0:
                    self.log("Sample citations:", "INFO")
                    for i, cite in enumerate(citations[:3]):
                        title = cite.get("title", "No title")[:50]
                        uri = cite.get("uri", "No URI")[:60]
                        self.log(f"  {i+1}. {title}...", "INFO")
                        self.log(f"     {uri}...", "INFO")
            else:
                phase_result["status"] = "warning"
                self.log(f"Unexpected provider: {provider}", "WARNING")
        else:
            phase_result["status"] = "failed"
            self.log("No web intelligence results", "ERROR")

        self.test_results["phases_tested"].append(phase_result)

        # Phase 3: Tiger Detection (MegaDetector)
        self.log("")
        self.log("PHASE 3: Tiger Detection (MegaDetector)", "PHASE")
        self.log("-" * 40)

        phase_result = {
            "name": "tiger_detection",
            "status": "unknown",
            "details": {}
        }

        detected_tigers = final_state.get("detected_tigers", [])
        if isinstance(detected_tigers, list):
            phase_result["details"]["tigers_detected"] = len(detected_tigers)

            if len(detected_tigers) > 0:
                phase_result["status"] = "success"
                self.log(f"Tigers detected: {len(detected_tigers)}", "SUCCESS")

                for i, tiger in enumerate(detected_tigers):
                    confidence = tiger.get("confidence", 0)
                    bbox = tiger.get("bbox", [])
                    has_crop = tiger.get("crop") is not None
                    self.log(f"  Tiger {i+1}: confidence={confidence:.2%}, bbox={bbox}, has_crop={has_crop}", "INFO")

                avg_conf = sum(t.get("confidence", 0) for t in detected_tigers) / len(detected_tigers)
                phase_result["details"]["average_confidence"] = avg_conf
                self.log(f"Average confidence: {avg_conf:.2%}", "INFO")
            else:
                phase_result["status"] = "warning"
                self.log("No tigers detected (may be expected for some test images)", "WARNING")
        else:
            phase_result["status"] = "failed"
            self.log("Invalid detection results", "ERROR")

        self.test_results["phases_tested"].append(phase_result)

        # Phase 4: Stripe Analysis (Multi-model matching)
        self.log("")
        self.log("PHASE 4: Stripe Analysis (Multi-model Matching)", "PHASE")
        self.log("-" * 40)

        phase_result = {
            "name": "stripe_analysis",
            "status": "unknown",
            "details": {}
        }

        stripe_embeddings = final_state.get("stripe_embeddings", {})
        database_matches = final_state.get("database_matches", {})

        if isinstance(stripe_embeddings, dict):
            models_run = list(stripe_embeddings.keys())
            phase_result["details"]["models_run"] = models_run
            phase_result["details"]["models_count"] = len(models_run)

            self.log(f"Models executed: {len(models_run)}", "SUCCESS" if len(models_run) > 0 else "WARNING")
            for model_name in models_run:
                embedding = stripe_embeddings[model_name]
                if embedding is not None:
                    if hasattr(embedding, 'shape'):
                        self.log(f"  {model_name}: embedding shape {embedding.shape}", "INFO")
                    else:
                        self.log(f"  {model_name}: embedding available", "INFO")

            if len(models_run) > 0:
                phase_result["status"] = "success"
            else:
                phase_result["status"] = "warning"
        else:
            phase_result["status"] = "failed"
            self.log("No stripe embeddings generated", "ERROR")

        # Database matches
        if isinstance(database_matches, dict):
            total_matches = sum(len(m) for m in database_matches.values())
            phase_result["details"]["total_database_matches"] = total_matches
            self.log(f"Total database matches: {total_matches}", "INFO")

            for model_name, matches in database_matches.items():
                if matches:
                    self.log(f"  {model_name}: {len(matches)} matches", "INFO")
                    for match in matches[:2]:
                        similarity = match.get("similarity", 0)
                        tiger_name = match.get("tiger_name", "Unknown")
                        self.log(f"    - {tiger_name}: {similarity:.2%}", "INFO")

        self.test_results["phases_tested"].append(phase_result)

        # Phase 5: OmniVinci Comparison
        self.log("")
        self.log("PHASE 5: OmniVinci Comparison", "PHASE")
        self.log("-" * 40)

        phase_result = {
            "name": "omnivinci_comparison",
            "status": "unknown",
            "details": {}
        }

        omnivinci = final_state.get("omnivinci_comparison")
        if omnivinci:
            analysis = omnivinci.get("visual_analysis", "")
            analysis_type = omnivinci.get("analysis_type", "unknown")
            confidence = omnivinci.get("confidence", "unknown")
            top_matches = omnivinci.get("top_matches", [])

            phase_result["details"]["analysis_type"] = analysis_type
            phase_result["details"]["confidence"] = confidence
            phase_result["details"]["analysis_length"] = len(analysis)
            phase_result["details"]["top_matches_count"] = len(top_matches)

            if analysis:
                phase_result["status"] = "success"
                self.log(f"Analysis type: {analysis_type}", "SUCCESS")
                self.log(f"Confidence: {confidence}", "INFO")
                self.log(f"Analysis length: {len(analysis)} chars", "INFO")
                self.log(f"Analysis preview: {analysis[:200]}...", "INFO")
            else:
                phase_result["status"] = "warning"
                self.log("OmniVinci analysis empty or unavailable", "WARNING")
        else:
            phase_result["status"] = "skipped"
            self.log("OmniVinci comparison skipped (no detected tigers or service unavailable)", "WARNING")

        self.test_results["phases_tested"].append(phase_result)

        # Phase 6: Report Generation (Gemini Pro)
        self.log("")
        self.log("PHASE 6: Report Generation (Gemini Pro)", "PHASE")
        self.log("-" * 40)

        phase_result = {
            "name": "report_generation",
            "status": "unknown",
            "details": {}
        }

        report = final_state.get("report")
        if report:
            if isinstance(report, dict):
                error = report.get("error")
                if error:
                    phase_result["status"] = "error"
                    phase_result["details"]["error"] = str(error)
                    self.log(f"Report generation error: {error}", "ERROR")
                else:
                    summary = report.get("summary", "")
                    model_used = report.get("model_used", "unknown")
                    detection_count = report.get("detection_count", 0)
                    total_matches = report.get("total_matches", 0)

                    phase_result["details"]["summary_length"] = len(summary)
                    phase_result["details"]["model_used"] = model_used
                    phase_result["details"]["detection_count"] = detection_count
                    phase_result["details"]["total_matches"] = total_matches

                    if summary and model_used == "gemini-2.5-pro":
                        phase_result["status"] = "success"
                        self.log(f"Model used: {model_used}", "SUCCESS")
                        self.log(f"Report length: {len(summary)} chars", "SUCCESS")
                        self.log(f"Detections: {detection_count}, Matches: {total_matches}", "INFO")

                        # Check for report sections
                        sections_found = []
                        for section in ["EXECUTIVE SUMMARY", "DETECTION", "WEB INTELLIGENCE", "VISUAL", "CONFIDENCE", "RECOMMENDATIONS", "CONCLUSION"]:
                            if section in summary.upper():
                                sections_found.append(section)

                        phase_result["details"]["sections_found"] = sections_found
                        self.log(f"Report sections found: {len(sections_found)}/7", "INFO")

                        # Show report preview
                        self.log("")
                        self.log("Report Preview (first 500 chars):", "INFO")
                        self.log("-" * 40)
                        print(summary[:500])
                        self.log("-" * 40)
                    elif summary:
                        phase_result["status"] = "warning"
                        self.log(f"Report generated but model is {model_used}", "WARNING")
                    else:
                        phase_result["status"] = "failed"
                        self.log("Report summary is empty", "ERROR")
            else:
                phase_result["status"] = "failed"
                self.log(f"Invalid report format: {type(report)}", "ERROR")
        else:
            phase_result["status"] = "failed"
            self.log("No report generated", "ERROR")

        self.test_results["phases_tested"].append(phase_result)

        # Phase 7: Workflow Completion
        self.log("")
        self.log("PHASE 7: Workflow Completion", "PHASE")
        self.log("-" * 40)

        phase_result = {
            "name": "completion",
            "status": "unknown",
            "details": {}
        }

        final_status = final_state.get("status")
        final_phase = final_state.get("phase")
        errors = final_state.get("errors", [])

        phase_result["details"]["final_status"] = final_status
        phase_result["details"]["final_phase"] = final_phase
        phase_result["details"]["error_count"] = len(errors)

        self.log(f"Final status: {final_status}", "SUCCESS" if final_status == "completed" else "ERROR")
        self.log(f"Final phase: {final_phase}", "INFO")
        self.log(f"Error count: {len(errors)}", "SUCCESS" if len(errors) == 0 else "WARNING")

        if errors:
            phase_result["status"] = "warning"
            self.log("Errors encountered:", "WARNING")
            for err in errors:
                self.log(f"  - {err.get('phase')}: {err.get('error')}", "WARNING")
                self.test_results["errors"].append(f"{err.get('phase')}: {err.get('error')}")

        if final_status == "completed":
            phase_result["status"] = "success"
        elif final_status == "failed":
            phase_result["status"] = "failed"
        else:
            phase_result["status"] = "warning"

        self.test_results["phases_tested"].append(phase_result)

    def print_summary(self):
        """Print test summary"""
        self.log("")
        self.log("=" * 80)
        self.log("TEST SUMMARY")
        self.log("=" * 80)

        # Count results
        success_count = sum(1 for p in self.test_results["phases_tested"] if p["status"] == "success")
        warning_count = sum(1 for p in self.test_results["phases_tested"] if p["status"] == "warning")
        error_count = sum(1 for p in self.test_results["phases_tested"] if p["status"] in ["failed", "error"])
        skipped_count = sum(1 for p in self.test_results["phases_tested"] if p["status"] == "skipped")
        total_phases = len(self.test_results["phases_tested"])

        self.log("")
        self.log(f"Phases tested: {total_phases}/7")
        self.log(f"Successful: {success_count}")
        self.log(f"Warnings: {warning_count}")
        self.log(f"Errors: {error_count}")
        self.log(f"Skipped: {skipped_count}")

        self.log("")
        self.log("Phase Results:")
        for phase in self.test_results["phases_tested"]:
            status_icon = {
                "success": "[PASS]",
                "warning": "[WARN]",
                "failed": "[FAIL]",
                "error": "[ERR]",
                "skipped": "[SKIP]",
                "unknown": "[???]"
            }.get(phase["status"], "[???]")
            self.log(f"  {status_icon} {phase['name']}")

        # Overall determination
        self.log("")
        if error_count == 0 and success_count >= 5:
            self.test_results["success"] = True
            self.log("OVERALL RESULT: PASS", "SUCCESS")
            self.log("Gemini migration verification successful!", "SUCCESS")
        elif error_count <= 2 and success_count >= 4:
            self.test_results["success"] = True
            self.log("OVERALL RESULT: PASS (with warnings)", "WARNING")
            self.log("Gemini migration mostly successful, some issues to investigate", "WARNING")
        else:
            self.test_results["success"] = False
            self.log("OVERALL RESULT: FAIL", "ERROR")
            self.log("Gemini migration has critical issues that need to be addressed", "ERROR")

        # Print errors if any
        if self.test_results["errors"]:
            self.log("")
            self.log("Errors to investigate:", "ERROR")
            for err in self.test_results["errors"]:
                self.log(f"  - {err}", "ERROR")

        # Print warnings if any
        if self.test_results["warnings"]:
            self.log("")
            self.log("Warnings:", "WARNING")
            for warn in self.test_results["warnings"]:
                self.log(f"  - {warn}", "WARNING")

        self.test_results["test_completed_at"] = datetime.utcnow().isoformat()

        # Save results to JSON
        results_path = project_root / "test_investigation2_results.json"
        with open(results_path, "w") as f:
            # Convert non-serializable items
            serializable_results = json.loads(json.dumps(self.test_results, default=str))
            json.dump(serializable_results, f, indent=2)
        self.log("")
        self.log(f"Detailed results saved to: {results_path}")

    async def cleanup(self):
        """Cleanup test resources"""
        self.log("")
        self.log("Cleaning up test resources...")

        if self.db_session:
            try:
                # Optionally delete test investigation
                # self.db_session.rollback()
                self.db_session.close()
                self.log("Database session closed", "SUCCESS")
            except Exception as e:
                self.log(f"Cleanup error: {e}", "WARNING")

    async def run_test(self):
        """Run the complete test"""
        try:
            await self.setup()
            image_bytes = self.load_test_image()
            final_state = await self.run_workflow(image_bytes)
            self.validate_phase_results(final_state)
            self.print_summary()
        except Exception as e:
            self.log(f"Test failed with exception: {e}", "ERROR")
            self.test_results["errors"].append(f"Test exception: {e}")
            import traceback
            self.log(traceback.format_exc(), "ERROR")
            self.test_results["success"] = False
        finally:
            await self.cleanup()

        return self.test_results["success"]


async def main():
    """Main entry point"""
    tester = Investigation2WorkflowTester()
    success = await tester.run_test()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
