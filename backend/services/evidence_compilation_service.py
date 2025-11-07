"""Evidence compilation service for extracting and scoring evidence from web sources"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from collections import defaultdict

from backend.database import get_db_session, Evidence, Investigation, Facility
from backend.services.reference_data_service import ReferenceDataService
from backend.services.data_extraction_service import DataExtractionService
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class EvidenceCompilationService:
    """Service for compiling and scoring evidence from web sources"""
    
    def __init__(self, session: Optional[Session] = None):
        """
        Initialize evidence compilation service
        
        Args:
            session: Database session (optional)
        """
        self.session = session
        if session:
            self.ref_service = ReferenceDataService(session)
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
            investigation_id: Investigation ID to link evidence to
            source_url: URL of web source
            source_type: Type of source (web_search, social_media, etc.)
            
        Returns:
            Compiled evidence record
        """
        if not self.session:
            session = next(get_db_session())
            try:
                self.session = session
                self.ref_service = ReferenceDataService(session)
                result = await self.compile_evidence_from_web(investigation_id, source_url, source_type)
                self.session = None
                return result
            finally:
                session.close()
        
        try:
            # Extract data from URL
            extracted = await self.data_extraction.extract_structured_data(source_url)
            
            # Score evidence
            score = self._score_evidence(
                source_url=source_url,
                extracted_data=extracted.get("extracted", {}),
                source_type=source_type
            )
            
            # Check if related to reference facilities
            facility_matches = []
            extracted_data = extracted.get("extracted", {})
            
            if "facility_name" in extracted_data:
                facility_name = extracted_data["facility_name"]
                matches = self.ref_service.find_matching_facilities(name=facility_name)
                facility_matches = [
                    {
                        "facility_id": str(f.facility_id),
                        "exhibitor_name": f.exhibitor_name,
                        "is_reference": f.is_reference_facility
                    }
                    for f in matches
                ]
                
                # Boost score if matches reference facility
                if facility_matches and any(f["is_reference"] for f in facility_matches):
                    score = min(1.0, score + 0.2)
            
            # Create evidence record
            evidence = Evidence(
                investigation_id=investigation_id,
                source_type=source_type,
                source_url=source_url,
                content={
                    **extracted_data,
                    "extraction_method": extracted.get("extraction_method"),
                    "facility_matches": facility_matches,
                    "extraction_timestamp": datetime.utcnow().isoformat()
                },
                extracted_text=extracted.get("extracted", {}).get("description", ""),
                relevance_score=score
            )
            
            self.session.add(evidence)
            self.session.commit()
            self.session.refresh(evidence)
            
            return {
                "evidence_id": str(evidence.evidence_id),
                "source_url": source_url,
                "score": score,
                "facility_matches": facility_matches,
                "status": "created"
            }
        
        except Exception as e:
            logger.error(f"Evidence compilation failed: {e}", exc_info=True)
            return {"error": str(e), "source_url": source_url}
    
    async def compile_multiple_evidence(
        self,
        investigation_id: UUID,
        sources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compile evidence from multiple sources
        
        Args:
            investigation_id: Investigation ID
            sources: List of source dictionaries with 'url' and 'type'
            
        Returns:
            Compilation results
        """
        compiled = []
        errors = []
        
        for source in sources:
            url = source.get("url")
            source_type = source.get("type", "web_search")
            
            try:
                result = await self.compile_evidence_from_web(
                    investigation_id,
                    url,
                    source_type
                )
                
                if "error" not in result:
                    compiled.append(result)
                else:
                    errors.append({"url": url, "error": result.get("error")})
            
            except Exception as e:
                logger.error(f"Failed to compile evidence from {url}: {e}")
                errors.append({"url": url, "error": str(e)})
        
        return {
            "compiled_count": len(compiled),
            "error_count": len(errors),
            "compiled": compiled,
            "errors": errors
        }
    
    def group_related_evidence(
        self,
        investigation_id: UUID
    ) -> Dict[str, Any]:
        """
        Group related evidence items
        
        Args:
            investigation_id: Investigation ID
            
        Returns:
            Grouped evidence
        """
        if not self.session:
            session = next(get_db_session())
            try:
                self.session = session
                self.ref_service = ReferenceDataService(session)
                result = self.group_related_evidence(investigation_id)
                self.session = None
                return result
            finally:
                session.close()
        
        evidence_items = self.session.query(Evidence).filter(
            Evidence.investigation_id == investigation_id
        ).all()
        
        groups = {
            "by_facility": defaultdict(list),
            "by_source_type": defaultdict(list),
            "by_date": defaultdict(list),
            "high_relevance": []
        }
        
        for evidence in evidence_items:
            # Group by facility
            content = evidence.content or {}
            if "facility_id" in content:
                facility_id = content["facility_id"]
                groups["by_facility"][facility_id].append({
                    "evidence_id": str(evidence.evidence_id),
                    "url": evidence.source_url,
                    "score": evidence.relevance_score
                })
            
            # Group by source type
            groups["by_source_type"][evidence.source_type].append({
                "evidence_id": str(evidence.evidence_id),
                "url": evidence.source_url,
                "score": evidence.relevance_score
            })
            
            # Group by date (month)
            date_key = evidence.created_at.strftime("%Y-%m")
            groups["by_date"][date_key].append({
                "evidence_id": str(evidence.evidence_id),
                "url": evidence.source_url,
                "date": evidence.created_at.isoformat()
            })
            
            # High relevance
            if evidence.relevance_score and evidence.relevance_score >= 0.8:
                groups["high_relevance"].append({
                    "evidence_id": str(evidence.evidence_id),
                    "url": evidence.source_url,
                    "score": evidence.relevance_score,
                    "source_type": evidence.source_type
                })
        
        # Sort high relevance by score
        groups["high_relevance"].sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "investigation_id": str(investigation_id),
            "total_evidence": len(evidence_items),
            "groups": {
                "by_facility": dict(groups["by_facility"]),
                "by_source_type": dict(groups["by_source_type"]),
                "by_date": dict(groups["by_date"]),
                "high_relevance": groups["high_relevance"]
            }
        }
    
    def _score_evidence(
        self,
        source_url: str,
        extracted_data: Dict[str, Any],
        source_type: str
    ) -> float:
        """
        Score evidence relevance
        
        Args:
            source_url: Source URL
            extracted_data: Extracted data
            source_type: Type of source
            
        Returns:
            Relevance score (0.0 to 1.0)
        """
        score = 0.5  # Base score
        
        # Boost for specific data found
        if "facility_name" in extracted_data:
            score += 0.1
        if "usda_license" in extracted_data:
            score += 0.15
        if "tiger_count" in extracted_data:
            score += 0.1
        if "violation" in str(extracted_data).lower():
            score += 0.2
        
        # Boost for reference facility matches
        if "matched_facilities" in extracted_data:
            score += 0.2
        
        # Source type weighting
        if source_type == "web_search":
            score += 0.05
        elif source_type == "social_media":
            score += 0.1  # Social media can be very revealing
        
        # URL domain credibility
        url_lower = source_url.lower()
        if any(domain in url_lower for domain in [".gov", ".edu", ".org"]):
            score += 0.1
        
        return min(1.0, score)


def get_evidence_compilation_service(session: Optional[Session] = None) -> EvidenceCompilationService:
    """Get evidence compilation service instance"""
    return EvidenceCompilationService(session)

