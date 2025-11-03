"""Analysis Agent for synthesizing evidence and reasoning"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from backend.services.investigation_service import InvestigationService
from backend.database import get_db_session
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class AnalysisAgent:
    """Agent specialized in analyzing evidence and reasoning about trafficking"""
    
    def __init__(
        self, 
        db: Optional[Session] = None,
        investigation_service: Optional[InvestigationService] = None
    ):
        """
        Initialize Analysis Agent
        
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
    
    async def analyze_evidence(
        self,
        evidence_items: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze compiled evidence for trafficking indicators
        
        Args:
            evidence_items: List of evidence items to analyze
            context: Additional context about the investigation
            
        Returns:
            Analysis results with trafficking assessment
        """
        analysis = {
            "trafficking_indicators": [],
            "contradictions": [],
            "evidence_strength": "weak",  # weak, moderate, strong
            "confidence": 0.0,
            "legal_implications": [],
            "recommendations": []
        }
        
        # Analyze evidence for trafficking indicators
        indicators = []
        
        # Check for location mismatches
        locations = {}
        for item in evidence_items:
            if "location" in item:
                loc = item["location"]
                tiger_id = item.get("tiger_id")
                if tiger_id:
                    if tiger_id in locations and locations[tiger_id] != loc:
                        indicators.append({
                            "type": "location_mismatch",
                            "description": f"Tiger {tiger_id} seen in different locations",
                            "severity": "high"
                        })
                    locations[tiger_id] = loc
        
        # Check for facility violations
        violations = []
        for item in evidence_items:
            if "facility" in item and "violations" in item["facility"]:
                violations.extend(item["facility"]["violations"])
        
        if violations:
            indicators.append({
                "type": "facility_violations",
                "description": f"Facility has {len(violations)} violations",
                "violations": violations,
                "severity": "high"
            })
        
        # Check for interstate transfers
        for item in evidence_items:
            if "transfer" in item and item["transfer"].get("interstate"):
                indicators.append({
                    "type": "interstate_transfer",
                    "description": "Possible interstate transfer detected",
                    "from": item["transfer"].get("from"),
                    "to": item["transfer"].get("to"),
                    "severity": "critical"
                })
        
        # Check for unlicensed facilities
        for item in evidence_items:
            if "facility" in item:
                facility = item["facility"]
                if not facility.get("usda_license"):
                    indicators.append({
                        "type": "unlicensed_facility",
                        "description": "Tiger found at unlicensed facility",
                        "facility_name": facility.get("name"),
                        "severity": "high"
                    })
        
        analysis["trafficking_indicators"] = indicators
        
        # Assess evidence strength
        critical_count = sum(1 for i in indicators if i["severity"] == "critical")
        high_count = sum(1 for i in indicators if i["severity"] == "high")
        
        if critical_count > 0 or high_count >= 2:
            analysis["evidence_strength"] = "strong"
            analysis["confidence"] = 0.8
        elif high_count > 0 or len(indicators) >= 2:
            analysis["evidence_strength"] = "moderate"
            analysis["confidence"] = 0.6
        else:
            analysis["evidence_strength"] = "weak"
            analysis["confidence"] = 0.3
        
        # Identify legal implications
        legal_implications = []
        
        if any(i["type"] == "interstate_transfer" for i in indicators):
            legal_implications.append({
                "law": "Big Cat Public Safety Act (2022)",
                "violation": "Interstate transfer without permit",
                "severity": "critical"
            })
        
        if any(i["type"] == "unlicensed_facility" for i in indicators):
            legal_implications.append({
                "law": "Animal Welfare Act",
                "violation": "Unlicensed facility holding tigers",
                "severity": "high"
            })
        
        analysis["legal_implications"] = legal_implications
        
        # Generate recommendations
        recommendations = []
        
        if analysis["evidence_strength"] == "strong":
            recommendations.append({
                "action": "Notify authorities",
                "priority": "high",
                "description": "Strong evidence of trafficking - notify law enforcement"
            })
        elif analysis["evidence_strength"] == "moderate":
            recommendations.append({
                "action": "Gather additional evidence",
                "priority": "medium",
                "description": "Continue investigation to strengthen case"
            })
        
        if violations:
            recommendations.append({
                "action": "Review USDA inspection reports",
                "priority": "medium",
                "description": "Examine facility violation history"
            })
        
        analysis["recommendations"] = recommendations
        
        return analysis
    
    async def identify_contradictions(
        self,
        evidence_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Identify contradictions in evidence
        
        Args:
            evidence_items: List of evidence items
            
        Returns:
            List of identified contradictions
        """
        contradictions = []
        
        # Check for conflicting locations
        location_map = {}
        for item in evidence_items:
            tiger_id = item.get("tiger_id")
            location = item.get("location")
            date = item.get("date")
            
            if tiger_id and location:
                if tiger_id not in location_map:
                    location_map[tiger_id] = []
                location_map[tiger_id].append({
                    "location": location,
                    "date": date,
                    "source": item.get("source")
                })
        
        # Find location conflicts
        for tiger_id, locations in location_map.items():
            unique_locations = set(l["location"] for l in locations)
            if len(unique_locations) > 1:
                # Check if dates are close enough to be suspicious
                dates = [l["date"] for l in locations if l["date"]]
                if dates:
                    # If same tiger in different locations on similar dates, flag
                    contradictions.append({
                        "type": "location_conflict",
                        "tiger_id": tiger_id,
                        "locations": locations,
                        "severity": "medium"
                    })
        
        return contradictions
    
    async def assess_trafficking_probability(
        self,
        evidence_items: List[Dict[str, Any]],
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess probability that trafficking occurred
        
        Args:
            evidence_items: List of evidence items
            analysis: Previous analysis results
            
        Returns:
            Probability assessment
        """
        # Calculate trafficking probability score
        score = 0.0
        factors = []
        
        # Location mismatch increases probability
        if any(i["type"] == "location_mismatch" for i in analysis.get("trafficking_indicators", [])):
            score += 0.3
            factors.append("Location mismatch detected")
        
        # Interstate transfer is strong indicator
        if any(i["type"] == "interstate_transfer" for i in analysis.get("trafficking_indicators", [])):
            score += 0.4
            factors.append("Interstate transfer detected")
        
        # Unlicensed facility
        if any(i["type"] == "unlicensed_facility" for i in analysis.get("trafficking_indicators", [])):
            score += 0.2
            factors.append("Unlicensed facility")
        
        # Facility violations
        if any(i["type"] == "facility_violations" for i in analysis.get("trafficking_indicators", [])):
            score += 0.1
            factors.append("Facility violations")
        
        # Cap at 1.0
        score = min(score, 1.0)
        
        # Determine probability level
        if score >= 0.7:
            probability = "high"
        elif score >= 0.4:
            probability = "moderate"
        else:
            probability = "low"
        
        return {
            "probability": probability,
            "score": score,
            "factors": factors,
            "recommendation": "immediate_action" if score >= 0.7 else "continue_investigation" if score >= 0.4 else "monitor"
        }
