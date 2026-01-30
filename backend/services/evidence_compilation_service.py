"""Evidence Compilation Service for gathering and scoring investigation evidence"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from backend.database.models import Evidence, Investigation
from backend.services.data_extraction_service import DataExtractionService
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class EvidenceCompilationService:
    """Service for compiling and scoring evidence from various sources"""

    def __init__(self, db: Optional[Session] = None):
        """
        Initialize Evidence Compilation Service

        Args:
            db: Database session (optional)
        """
        self.db = db
        self.data_extraction = DataExtractionService()

    async def compile_evidence_from_web(
        self,
        investigation_id: UUID,
        source_url: str,
        source_type: str = "web_search"
    ) -> Dict[str, Any]:
        """
        Compile evidence from a web source

        Args:
            investigation_id: Investigation ID
            source_url: URL to extract evidence from
            source_type: Type of source (web_search, document, etc.)

        Returns:
            Dictionary with evidence details
        """
        try:
            # Extract structured data from URL
            extracted = await self.data_extraction.extract_structured_data(source_url)

            # Score the evidence
            relevance_score = self._score_evidence(
                source_url=source_url,
                extracted_data=extracted.get("extracted", {}),
                source_type=source_type
            )

            # Store in database if session available
            evidence_id = None
            if self.db:
                from backend.services.investigation_service import InvestigationService
                inv_service = InvestigationService(self.db)

                evidence = inv_service.add_evidence(
                    investigation_id=investigation_id,
                    source_type=source_type,
                    source_url=source_url,
                    content=extracted.get("extracted", {}),
                    extracted_text=extracted.get("extracted", {}).get("content", ""),
                    relevance_score=relevance_score
                )
                evidence_id = evidence.evidence_id

            return {
                "evidence_id": str(evidence_id) if evidence_id else None,
                "source_url": source_url,
                "source_type": source_type,
                "extracted_data": extracted.get("extracted", {}),
                "relevance_score": relevance_score,
                "success": True
            }

        except Exception as e:
            logger.error(f"Failed to compile evidence from {source_url}: {e}")
            return {
                "source_url": source_url,
                "source_type": source_type,
                "error": str(e),
                "success": False
            }

    async def compile_evidence_batch(
        self,
        investigation_id: UUID,
        source_urls: List[str],
        source_type: str = "web_search"
    ) -> List[Dict[str, Any]]:
        """
        Compile evidence from multiple sources

        Args:
            investigation_id: Investigation ID
            source_urls: List of URLs to extract evidence from
            source_type: Type of sources

        Returns:
            List of evidence compilation results
        """
        results = []
        for url in source_urls:
            result = await self.compile_evidence_from_web(
                investigation_id=investigation_id,
                source_url=url,
                source_type=source_type
            )
            results.append(result)

        return results

    def _score_evidence(
        self,
        source_url: str,
        extracted_data: Dict[str, Any],
        source_type: str
    ) -> float:
        """
        Score evidence based on relevance and quality

        Args:
            source_url: Source URL
            extracted_data: Extracted data from the source
            source_type: Type of source

        Returns:
            Relevance score between 0 and 1
        """
        score = 0.5  # Base score

        # Check for tiger-related keywords
        tiger_keywords = [
            "tiger", "feline", "panthera", "captive", "facility",
            "trafficking", "wildlife", "endangered", "conservation",
            "usda", "exhibitor", "violation", "permit"
        ]

        content = extracted_data.get("content", "").lower()
        title = extracted_data.get("title", "").lower()

        # Score based on keyword presence
        keyword_count = sum(1 for kw in tiger_keywords if kw in content or kw in title)
        keyword_score = min(keyword_count * 0.1, 0.4)
        score += keyword_score

        # Score based on source type
        source_scores = {
            "web_search": 0.0,
            "document": 0.1,
            "database": 0.15,
            "official_report": 0.2
        }
        score += source_scores.get(source_type, 0.0)

        # Score based on content length
        if len(content) > 1000:
            score += 0.05
        if len(content) > 5000:
            score += 0.05

        return min(score, 1.0)

    def get_evidence_summary(self, investigation_id: UUID) -> Dict[str, Any]:
        """
        Get summary of evidence for an investigation

        Args:
            investigation_id: Investigation ID

        Returns:
            Dictionary with evidence summary
        """
        if not self.db:
            return {
                "total_evidence": 0,
                "evidence_count": 0,
                "sources": [],
                "avg_relevance": 0.0
            }

        try:
            evidence_list = self.db.query(Evidence).filter(
                Evidence.investigation_id == investigation_id
            ).all()

            sources_by_type: Dict[str, int] = {}
            total_relevance = 0.0

            for evidence in evidence_list:
                source_type = str(evidence.source_type.value) if evidence.source_type else "unknown"
                sources_by_type[source_type] = sources_by_type.get(source_type, 0) + 1
                if evidence.relevance_score:
                    total_relevance += evidence.relevance_score

            avg_relevance = total_relevance / len(evidence_list) if evidence_list else 0.0

            return {
                "total_evidence": len(evidence_list),
                "evidence_count": len(evidence_list),
                "sources": sources_by_type,
                "avg_relevance": avg_relevance
            }

        except Exception as e:
            logger.error(f"Failed to get evidence summary: {e}")
            return {
                "total_evidence": 0,
                "evidence_count": 0,
                "sources": [],
                "avg_relevance": 0.0,
                "error": str(e)
            }


# Singleton instance
_evidence_compilation_service: Optional[EvidenceCompilationService] = None


def get_evidence_compilation_service(db: Optional[Session] = None) -> EvidenceCompilationService:
    """Get global evidence compilation service instance"""
    global _evidence_compilation_service
    if _evidence_compilation_service is None or db is not None:
        _evidence_compilation_service = EvidenceCompilationService(db=db)
    return _evidence_compilation_service
