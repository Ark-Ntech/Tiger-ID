"""Timeline construction service for investigations"""

from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from collections import defaultdict

from backend.database import get_db_session, Evidence, Investigation, InvestigationStep, Facility, Tiger
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class TimelineService:
    """Service for constructing investigation timelines"""
    
    def __init__(self, session: Optional[Session] = None):
        """
        Initialize timeline service
        
        Args:
            session: Database session (optional)
        """
        self.session = session
    
    def build_investigation_timeline(
        self,
        investigation_id: UUID,
        include_web_evidence: bool = True,
        include_reference_events: bool = True
    ) -> Dict[str, Any]:
        """
        Build timeline for an investigation
        
        Args:
            investigation_id: Investigation ID
            include_web_evidence: Include web-discovered evidence
            include_reference_events: Include reference facility events
            
        Returns:
            Timeline data
        """
        if not self.session:
            with get_db_session() as session:
                self.session = session
                return self.build_investigation_timeline(
                    investigation_id,
                    include_web_evidence,
                    include_reference_events
                )
        
        # Get investigation
        investigation = self.session.query(Investigation).filter(
            Investigation.investigation_id == investigation_id
        ).first()
        
        if not investigation:
            return {"error": "Investigation not found"}
        
        timeline_events = []
        
        # Investigation creation
        timeline_events.append({
            "date": investigation.created_at.isoformat(),
            "type": "investigation_created",
            "title": "Investigation Created",
            "description": investigation.description or "",
            "source": "system"
        })
        
        # Investigation steps
        steps = self.session.query(InvestigationStep).filter(
            InvestigationStep.investigation_id == investigation_id
        ).order_by(InvestigationStep.timestamp).all()
        
        for step in steps:
            timeline_events.append({
                "date": step.timestamp.isoformat(),
                "type": step.step_type,
                "title": f"{step.agent_name or 'System'}: {step.step_type.replace('_', ' ').title()}",
                "status": step.status,
                "source": "investigation_step",
                "result": step.result
            })
        
        # Evidence items
        if include_web_evidence:
            evidence_items = self.session.query(Evidence).filter(
                Evidence.investigation_id == investigation_id
            ).order_by(Evidence.created_at).all()
            
            for evidence in evidence_items:
                content = evidence.content or {}
                
                # Extract dates from evidence content
                extracted_date = content.get("date") or content.get("posted_date") or content.get("event_date")
                
                event_date = None
                if extracted_date:
                    try:
                        event_date = datetime.fromisoformat(extracted_date.replace("Z", "+00:00"))
                    except:
                        event_date = evidence.created_at
                else:
                    event_date = evidence.created_at
                
                timeline_events.append({
                    "date": event_date.isoformat(),
                    "type": evidence.source_type,
                    "title": content.get("title") or f"Evidence from {evidence.source_type}",
                    "description": evidence.extracted_text or content.get("snippet", "")[:200],
                    "source": "evidence",
                    "url": evidence.source_url,
                    "relevance_score": evidence.relevance_score,
                    "facility_id": content.get("facility_id")
                })
        
        # Reference facility events
        if include_reference_events:
            # Get related facilities
            related_facilities = investigation.related_facilities or []
            
            for facility_id_str in related_facilities[:10]:  # Limit to 10 facilities
                try:
                    facility_id = UUID(facility_id_str)
                    facility = self.session.query(Facility).filter(
                        Facility.facility_id == facility_id
                    ).first()
                    
                    if facility and facility.is_reference_facility:
                        # Add facility inspection dates
                        if facility.last_inspection_date:
                            timeline_events.append({
                                "date": facility.last_inspection_date.isoformat(),
                                "type": "inspection",
                                "title": f"Inspection: {facility.exhibitor_name}",
                                "description": f"USDA inspection for {facility.exhibitor_name}",
                                "source": "reference_facility",
                                "facility_id": str(facility_id)
                            })
                        
                        # Add violation history dates
                        if facility.violation_history:
                            for violation in facility.violation_history:
                                violation_date = violation.get("date")
                                if violation_date:
                                    try:
                                        violation_dt = datetime.fromisoformat(violation_date.replace("Z", "+00:00"))
                                        timeline_events.append({
                                            "date": violation_dt.isoformat(),
                                            "type": "violation",
                                            "title": f"Violation: {facility.exhibitor_name}",
                                            "description": violation.get("type", "Violation"),
                                            "source": "reference_facility",
                                            "facility_id": str(facility_id)
                                        })
                                    except:
                                        pass
                
                except Exception as e:
                    logger.warning(f"Error processing facility {facility_id_str}: {e}")
        
        # Sort events by date
        timeline_events.sort(key=lambda x: x["date"])
        
        # Group by date
        events_by_date = defaultdict(list)
        for event in timeline_events:
            date_key = event["date"][:10]  # YYYY-MM-DD
            events_by_date[date_key].append(event)
        
        return {
            "investigation_id": str(investigation_id),
            "timeline_events": timeline_events,
            "events_by_date": dict(events_by_date),
            "total_events": len(timeline_events),
            "date_range": {
                "start": timeline_events[0]["date"] if timeline_events else None,
                "end": timeline_events[-1]["date"] if timeline_events else None
            },
            "event_types": list(set(e["type"] for e in timeline_events))
        }
    
    def identify_timeline_gaps(
        self,
        investigation_id: UUID,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """
        Identify gaps in investigation timeline
        
        Args:
            investigation_id: Investigation ID
            date_range: Optional date range to analyze
            
        Returns:
            Timeline gaps identified
        """
        timeline = self.build_investigation_timeline(investigation_id)
        
        events = timeline.get("timeline_events", [])
        
        if len(events) < 2:
            return {
                "gaps": [],
                "total_gaps": 0
            }
        
        gaps = []
        
        # Sort events by date
        sorted_events = sorted(events, key=lambda x: x["date"])
        
        for i in range(len(sorted_events) - 1):
            current_date = datetime.fromisoformat(sorted_events[i]["date"].replace("Z", "+00:00"))
            next_date = datetime.fromisoformat(sorted_events[i + 1]["date"].replace("Z", "+00:00"))
            
            # Calculate gap in days
            gap_days = (next_date - current_date).days
            
            # If gap is significant (more than 30 days)
            if gap_days > 30:
                gaps.append({
                    "start_date": sorted_events[i]["date"],
                    "end_date": sorted_events[i + 1]["date"],
                    "gap_days": gap_days,
                    "before_event": sorted_events[i]["title"],
                    "after_event": sorted_events[i + 1]["title"]
                })
        
        return {
            "gaps": gaps,
            "total_gaps": len(gaps),
            "investigation_id": str(investigation_id)
        }
    
    def correlate_events(
        self,
        facility_id: UUID,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """
        Correlate events across investigations for a facility
        
        Args:
            facility_id: Facility ID
            date_range: Optional date range
            
        Returns:
            Correlated events
        """
        if not self.session:
            with get_db_session() as session:
                self.session = session
                return self.correlate_events(facility_id, date_range)
        
        # Find investigations mentioning this facility
        evidence_items = self.session.query(Evidence).filter(
            Evidence.content.contains({"facility_id": str(facility_id)})
        )
        
        if date_range:
            evidence_items = evidence_items.filter(
                Evidence.created_at >= date_range[0],
                Evidence.created_at <= date_range[1]
            )
        
        evidence_items = evidence_items.order_by(Evidence.created_at).all()
        
        # Group by investigation
        investigations = {}
        
        for evidence in evidence_items:
            inv_id = str(evidence.investigation_id)
            if inv_id not in investigations:
                investigations[inv_id] = []
            investigations[inv_id].append({
                "date": evidence.created_at.isoformat(),
                "type": evidence.source_type,
                "url": evidence.source_url,
                "title": (evidence.content or {}).get("title", "")
            })
        
        return {
            "facility_id": str(facility_id),
            "investigations": investigations,
            "total_investigations": len(investigations),
            "total_events": len(evidence_items),
            "date_range": date_range
        }


def get_timeline_service(session: Optional[Session] = None) -> TimelineService:
    """Get timeline service instance"""
    return TimelineService(session)

