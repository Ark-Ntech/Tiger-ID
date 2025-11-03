"""Validation Agent for fact-checking and quality assurance"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from backend.services.investigation_service import InvestigationService
from backend.database import get_db_session
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class ValidationAgent:
    """Agent specialized in fact-checking and validating findings"""
    
    def __init__(
        self, 
        db: Optional[Session] = None,
        investigation_service: Optional[InvestigationService] = None
    ):
        """
        Initialize Validation Agent
        
        Args:
            db: Database session (optional, will create if not provided)
            investigation_service: InvestigationService instance (optional, for testing)
        """
        self.db = db
        # Allow dependency injection for testing
        if investigation_service:
            self.investigation_service = investigation_service
        else:
            self.investigation_service = InvestigationService(db) if db else None
    
    async def validate_evidence(
        self,
        evidence_items: List[Dict[str, Any]],
        sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Validate evidence items for accuracy and reliability
        
        Args:
            evidence_items: List of evidence items to validate
            sources: List of source URLs or identifiers
            
        Returns:
            Validation results with confidence scores
        """
        validation = {
            "validated_items": [],
            "invalid_items": [],
            "uncertain_items": [],
            "overall_confidence": 0.0,
            "issues": []
        }
        
        for item in evidence_items:
            item_validation = await self._validate_single_evidence(item, sources)
            
            if item_validation["confidence"] >= 0.8:
                validation["validated_items"].append({
                    "item": item,
                    "validation": item_validation
                })
            elif item_validation["confidence"] >= 0.5:
                validation["uncertain_items"].append({
                    "item": item,
                    "validation": item_validation
                })
            else:
                validation["invalid_items"].append({
                    "item": item,
                    "validation": item_validation
                })
        
        # Calculate overall confidence
        if evidence_items:
            total_confidence = sum(
                item["validation"]["confidence"]
                for item in validation["validated_items"] + validation["uncertain_items"]
            )
            validation["overall_confidence"] = total_confidence / len(evidence_items) if len(evidence_items) > 0 else 0.0
        
        # Check for issues
        if validation["invalid_items"]:
            validation["issues"].append({
                "type": "invalid_evidence",
                "count": len(validation["invalid_items"]),
                "severity": "high"
            })
        
        if validation["uncertain_items"]:
            validation["issues"].append({
                "type": "uncertain_evidence",
                "count": len(validation["uncertain_items"]),
                "severity": "medium"
            })
        
        return validation
    
    async def _validate_single_evidence(
        self,
        item: Dict[str, Any],
        sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Validate a single evidence item"""
        confidence = 1.0
        issues = []
        sources_found = []
        
        # Check for source
        if item.get("source_url"):
            sources_found.append(item["source_url"])
            # Verify source is accessible (basic check)
            confidence *= 0.9  # Assume source exists
        
        # Check for extracted text
        if item.get("extracted_text"):
            # Basic validation - check if text seems valid
            text = item["extracted_text"]
            if len(text) < 10:
                confidence *= 0.7
                issues.append("Text too short")
        
        # Check for relevance score
        if "relevance_score" in item:
            relevance = item["relevance_score"]
            if relevance < 0.5:
                confidence *= 0.6
                issues.append("Low relevance score")
        
        # Check for verification status
        if item.get("verified"):
            confidence *= 1.1  # Boost for verified items
        else:
            confidence *= 0.9  # Slight reduction for unverified
        
        # Cap confidence at 1.0
        confidence = min(confidence, 1.0)
        
        return {
            "confidence": confidence,
            "issues": issues,
            "sources": sources_found,
            "validation_status": "valid" if confidence >= 0.8 else "uncertain" if confidence >= 0.5 else "invalid"
        }
    
    async def cross_verify_facts(
        self,
        facts: List[Dict[str, Any]],
        evidence_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Cross-verify facts against evidence
        
        Args:
            facts: List of facts to verify
            evidence_items: List of evidence items to verify against
            
        Returns:
            Verification results
        """
        verification = {
            "verified_facts": [],
            "unverified_facts": [],
            "contradictions": [],
            "confidence": 0.0
        }
        
        for fact in facts:
            fact_text = fact.get("text", "")
            fact_type = fact.get("type", "")
            
            # Search for supporting evidence
            supporting_evidence = []
            contradicting_evidence = []
            
            for evidence in evidence_items:
                evidence_text = evidence.get("extracted_text", "")
                
                # Simple keyword matching (in production, use better NLP)
                fact_keywords = set(fact_text.lower().split())
                evidence_keywords = set(evidence_text.lower().split())
                
                # Check if evidence supports fact
                overlap = fact_keywords.intersection(evidence_keywords)
                if len(overlap) > 2:  # Significant overlap
                    if fact_type == "location" and "location" in evidence:
                        # Check if locations match
                        fact_location = fact.get("location", "").lower()
                        evidence_location = evidence.get("location", "").lower()
                        if fact_location == evidence_location:
                            supporting_evidence.append(evidence)
                        else:
                            contradicting_evidence.append(evidence)
                    else:
                        supporting_evidence.append(evidence)
            
            if supporting_evidence:
                verification["verified_facts"].append({
                    "fact": fact,
                    "supporting_evidence": supporting_evidence,
                    "confidence": min(1.0, len(supporting_evidence) * 0.3)
                })
            else:
                verification["unverified_facts"].append(fact)
            
            if contradicting_evidence:
                verification["contradictions"].append({
                    "fact": fact,
                    "contradicting_evidence": contradicting_evidence
                })
        
        # Calculate overall confidence
        if facts:
            verified_count = len(verification["verified_facts"])
            verification["confidence"] = verified_count / len(facts)
        
        return verification
    
    async def check_for_hallucinations(
        self,
        findings: Dict[str, Any],
        evidence_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Check for hallucinations or unsupported claims
        
        Args:
            findings: Investigation findings
            evidence_items: List of evidence items
            
        Returns:
            Hallucination check results
        """
        hallucinations = {
            "potential_hallucinations": [],
            "supported_claims": [],
            "uncertain_claims": []
        }
        
        claims = findings.get("claims", [])
        
        for claim in claims:
            claim_text = claim.get("text", "")
            claim_sources = claim.get("sources", [])
            
            # Check if claim has sources
            if not claim_sources:
                hallucinations["uncertain_claims"].append({
                    "claim": claim,
                    "reason": "No sources cited"
                })
                continue
            
            # Verify sources exist in evidence
            source_evidence = []
            for source in claim_sources:
                found = False
                for evidence in evidence_items:
                    if evidence.get("source_url") == source or evidence.get("evidence_id") == source:
                        source_evidence.append(evidence)
                        found = True
                        break
                
                if not found:
                    hallucinations["potential_hallucinations"].append({
                        "claim": claim,
                        "reason": f"Source not found in evidence: {source}",
                        "severity": "high"
                    })
            
            if source_evidence:
                hallucinations["supported_claims"].append({
                    "claim": claim,
                    "supporting_evidence": source_evidence
                })
        
        return hallucinations
    
    async def validate_final_report(
        self,
        report: Dict[str, Any],
        evidence_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate final investigation report
        
        Args:
            report: Final investigation report
            evidence_items: All evidence items
            
        Returns:
            Validation results
        """
        validation = {
            "report_valid": True,
            "issues": [],
            "confidence": 1.0,
            "recommendations": []
        }
        
        # Check for hallucinations
        hallucinations = await self.check_for_hallucinations(report, evidence_items)
        
        if hallucinations["potential_hallucinations"]:
            validation["report_valid"] = False
            validation["issues"].append({
                "type": "hallucinations",
                "count": len(hallucinations["potential_hallucinations"]),
                "severity": "high"
            })
            validation["confidence"] *= 0.7
        
        # Check for unsupported claims
        if hallucinations["uncertain_claims"]:
            validation["issues"].append({
                "type": "uncertain_claims",
                "count": len(hallucinations["uncertain_claims"]),
                "severity": "medium"
            })
            validation["confidence"] *= 0.9
        
        # Check for missing evidence citations
        claims = report.get("claims", [])
        for claim in claims:
            if not claim.get("sources"):
                validation["issues"].append({
                    "type": "missing_sources",
                    "claim": claim.get("text", "")[:50],
                    "severity": "medium"
                })
        
        # Generate recommendations
        if validation["issues"]:
            validation["recommendations"].append({
                "action": "Review evidence citations",
                "priority": "high",
                "description": "Some claims lack proper source citations"
            })
        
        if hallucinations["potential_hallucinations"]:
            validation["recommendations"].append({
                "action": "Verify all claims",
                "priority": "critical",
                "description": "Potential hallucinations detected - verify all claims before publishing"
            })
        
        return validation
