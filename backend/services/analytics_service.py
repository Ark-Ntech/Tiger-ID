"""Analytics service for generating dashboard metrics and statistics"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from backend.database.models import (
    Investigation, Evidence, InvestigationStep, Facility, Tiger,
    VerificationQueue
)
from backend.utils.logging import get_logger

# For backward compatibility and verification analytics
Verification = VerificationQueue

logger = get_logger(__name__)


class AnalyticsService:
    """Service for generating analytics and dashboard metrics"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_investigation_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Get investigation analytics
        
        Args:
            start_date: Start date filter
            end_date: End date filter
            user_id: Optional user ID filter
        
        Returns:
            Investigation analytics dictionary
        """
        query = self.session.query(Investigation)

        if start_date:
            query = query.filter(Investigation.created_at >= start_date)
        if end_date:
            query = query.filter(Investigation.created_at <= end_date)
        if user_id:
            # Convert UUID to string for SQLite comparison
            query = query.filter(Investigation.created_by == str(user_id))
        
        investigations = query.all()
        
        # Status distribution
        status_counts = {}
        for inv in investigations:
            status = inv.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Priority distribution
        priority_counts = {}
        for inv in investigations:
            priority = inv.priority
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        # Completion rate
        completed = len([
            inv for inv in investigations 
            if (hasattr(inv.status, 'value') and inv.status.value == "completed") 
            or str(inv.status) == "completed"
        ])
        total = len(investigations)
        completion_rate = (completed / total * 100) if total > 0 else 0
        
        # Average investigation duration
        durations = []
        for inv in investigations:
            is_completed = (hasattr(inv.status, 'value') and inv.status.value == "completed") or str(inv.status) == "completed"
            if is_completed and hasattr(inv, 'completed_at') and inv.completed_at:
                if inv.created_at and inv.completed_at:
                    duration = (inv.completed_at - inv.created_at).days
                    durations.append(duration)
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Timeline data (investigations created over time)
        timeline_data = {}
        for inv in investigations:
            if inv.created_at:
                date_key = inv.created_at.date().isoformat()
                timeline_data[date_key] = timeline_data.get(date_key, 0) + 1
        
        return {
            "total_investigations": total,
            "status_distribution": status_counts,
            "priority_distribution": priority_counts,
            "completion_rate": completion_rate,
            "average_duration_days": avg_duration,
            "timeline_data": timeline_data,
            "completed": completed,
            "in_progress": len([
                inv for inv in investigations 
                if (hasattr(inv.status, 'value') and inv.status.value == "in_progress") 
                or str(inv.status) == "in_progress"
            ]),
            "paused": len([
                inv for inv in investigations 
                if (hasattr(inv.status, 'value') and inv.status.value == "paused") 
                or str(inv.status) == "paused"
            ]),
            "cancelled": len([
                inv for inv in investigations 
                if (hasattr(inv.status, 'value') and inv.status.value == "cancelled") 
                or str(inv.status) == "cancelled"
            ]),
            "by_status": status_counts,  # Frontend expects this field name
            "by_priority": priority_counts  # Frontend expects this field name
        }
    
    def get_evidence_analytics(
        self,
        investigation_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get evidence analytics
        
        Args:
            investigation_id: Optional investigation ID filter
            start_date: Start date filter
            end_date: End date filter
        
        Returns:
            Evidence analytics dictionary
        """
        query = self.session.query(Evidence)
        
        if investigation_id:
            query = query.filter(Evidence.investigation_id == investigation_id)
        if start_date:
            query = query.filter(Evidence.created_at >= start_date)
        if end_date:
            query = query.filter(Evidence.created_at <= end_date)
        
        evidence_items = query.all()
        
        # Source type distribution
        source_type_counts = {}
        for ev in evidence_items:
            # Handle enum values
            source_type = ev.source_type.value if hasattr(ev.source_type, 'value') else str(ev.source_type) if ev.source_type else "unknown"
            source_type_counts[source_type] = source_type_counts.get(source_type, 0) + 1
        
        # Relevance score distribution
        relevance_scores = [ev.relevance_score or 0 for ev in evidence_items]
        avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0
        
        # High relevance evidence count
        high_relevance = len([ev for ev in evidence_items if (ev.relevance_score or 0) >= 0.7])
        
        # Timeline data (evidence created over time)
        timeline_data = {}
        for ev in evidence_items:
            if ev.created_at:
                date_key = ev.created_at.date().isoformat()
                timeline_data[date_key] = timeline_data.get(date_key, 0) + 1
        
        return {
            "total_evidence": len(evidence_items),
            "by_type": source_type_counts,  # Frontend expects this field name
            "source_type_distribution": source_type_counts,  # Keep both for compatibility
            "average_relevance": avg_relevance,
            "average_relevance_score": avg_relevance,  # Keep both for compatibility
            "high_relevance_count": high_relevance,
            "high_relevance_percentage": (high_relevance / len(evidence_items) * 100) if evidence_items else 0,
            "timeline_data": timeline_data,
            "relevance_distribution": {
                "low": len([ev for ev in evidence_items if (ev.relevance_score or 0) < 0.3]),
                "medium": len([ev for ev in evidence_items if 0.3 <= (ev.relevance_score or 0) < 0.7]),
                "high": len([ev for ev in evidence_items if (ev.relevance_score or 0) >= 0.7])
            }
        }
    
    def get_verification_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get verification analytics
        
        Args:
            start_date: Start date filter
            end_date: End date filter
        
        Returns:
            Verification analytics dictionary
        """
        query = self.session.query(Verification)
        
        if start_date:
            query = query.filter(Verification.created_at >= start_date)
        if end_date:
            query = query.filter(Verification.created_at <= end_date)
        
        verifications = query.all()
        
        # Status distribution
        status_counts = {}
        for ver in verifications:
            # VerificationQueue uses status which is a VerificationStatus enum
            status = ver.status.value if hasattr(ver.status, 'value') else str(ver.status)
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Approval rate
        approved = len([v for v in verifications if (hasattr(v.status, 'value') and v.status.value == "approved") or str(v.status) == "approved"])
        total = len(verifications)
        approval_rate = (approved / total * 100) if total > 0 else 0
        
        # Average processing time
        processing_times = []
        for ver in verifications:
            status_str = ver.status.value if hasattr(ver.status, 'value') else str(ver.status)
            if status_str in ["approved", "rejected"] and hasattr(ver, 'reviewed_at') and ver.reviewed_at:
                if ver.created_at and ver.reviewed_at:
                    processing_time = (ver.reviewed_at - ver.created_at).days
                    processing_times.append(processing_time)
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        # Timeline data
        timeline_data = {}
        for ver in verifications:
            if ver.created_at:
                date_key = ver.created_at.date().isoformat()
                timeline_data[date_key] = timeline_data.get(date_key, 0) + 1
        
        return {
            "total_verifications": total,
            "total_tasks": total,  # Frontend expects this field name
            "by_status": status_counts,  # Frontend expects this field name
            "status_distribution": status_counts,  # Keep both for compatibility
            "approval_rate": approval_rate,
            "average_processing_time_days": avg_processing_time,
            "average_completion_time": avg_processing_time * 24,  # Convert days to hours for frontend
            "timeline_data": timeline_data,
            "pending": len([v for v in verifications if (hasattr(v.status, 'value') and v.status.value == "pending") or str(v.status) == "pending"]),
            "in_review": len([v for v in verifications if (hasattr(v.status, 'value') and v.status.value == "in_review") or str(v.status) == "in_review"]),
            "approved": approved,
            "rejected": len([v for v in verifications if (hasattr(v.status, 'value') and v.status.value == "rejected") or str(v.status) == "rejected"])
        }
    
    def get_geographic_analytics(
        self,
        investigation_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Get geographic analytics
        
        Args:
            investigation_id: Optional investigation ID filter
        
        Returns:
            Geographic analytics dictionary
        """
        # Get facilities with locations
        query = self.session.query(Facility)
        if investigation_id:
            # Filter by investigation's related facilities
            investigation = self.session.query(Investigation).filter(
                Investigation.investigation_id == investigation_id
            ).first()
            if investigation and hasattr(investigation, 'related_facilities'):
                facility_ids = investigation.related_facilities or []
                if facility_ids:
                    query = query.filter(Facility.facility_id.in_(facility_ids))
        
        # Filter facilities with location data (SQLite compatible)
        facilities = [
            fac for fac in query.all()
            if fac.city and fac.state
        ]
        
        # State distribution
        state_counts = {}
        for fac in facilities:
            state = fac.state or "Unknown"
            state_counts[state] = state_counts.get(state, 0) + 1
        
        # City distribution
        city_counts = {}
        for fac in facilities:
            if fac.city and fac.state:
                location = f"{fac.city}, {fac.state}"
                city_counts[location] = city_counts.get(location, 0) + 1
        
        # Facility coordinates (for mapping)
        facility_locations = []
        for fac in facilities:
            # Parse coordinates from JSON field
            lat, lon = None, None
            if fac.coordinates:
                try:
                    import json
                    coords_data = json.loads(fac.coordinates) if isinstance(fac.coordinates, str) else fac.coordinates
                    if coords_data:
                        lat = coords_data.get("latitude")
                        lon = coords_data.get("longitude")
                except (json.JSONDecodeError, TypeError, AttributeError):
                    pass

            # Include all facilities that have coordinates or city/state
            if lat is not None or (fac.city and fac.state):
                facility_locations.append({
                    "facility_id": str(fac.facility_id),
                    "name": fac.exhibitor_name,
                    "city": fac.city,
                    "state": fac.state,
                    "tiger_count": fac.tiger_count or 0,
                    "latitude": lat,
                    "longitude": lon
                })
        
        # Convert to list format for investigations_by_location if needed
        investigations_by_location = []
        # This would be populated from actual investigation data if needed
        
        return {
            "total_facilities": len(facilities),
            "facilities_by_state": state_counts,  # Frontend expects this field name
            "state_distribution": state_counts,  # Keep both for compatibility
            "city_distribution": city_counts,
            "facility_locations": facility_locations,
            "states_with_facilities": len(state_counts),
            "cities_with_facilities": len(city_counts),
            "investigations_by_location": investigations_by_location  # Frontend expects this
        }
    
    def get_tiger_analytics(
        self,
        investigation_id: Optional[UUID] = None,
        facility_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Get tiger analytics
        
        Args:
            investigation_id: Optional investigation ID filter
            facility_id: Optional facility ID filter
        
        Returns:
            Tiger analytics dictionary
        """
        query = self.session.query(Tiger)
        
        if facility_id:
            # Use origin_facility_id which is the actual field name
            query = query.filter(Tiger.origin_facility_id == facility_id)
        
        tigers = query.all()
        
        # Status distribution
        status_counts = {}
        for tiger in tigers:
            if hasattr(tiger, 'status'):
                status = tiger.status or "unknown"
                status_counts[status] = status_counts.get(status, 0) + 1
        
        # Facility distribution
        facility_distribution = {}
        for tiger in tigers:
            if hasattr(tiger, 'facility_id') and tiger.facility_id:
                fac_id = str(tiger.facility_id)
                facility_distribution[fac_id] = facility_distribution.get(fac_id, 0) + 1
        
        # Timeline data (if tigers have created_at)
        timeline_data = {}
        for tiger in tigers:
            if hasattr(tiger, 'created_at') and tiger.created_at:
                date_key = tiger.created_at.date().isoformat()
                timeline_data[date_key] = timeline_data.get(date_key, 0) + 1
        
        # Last seen locations
        last_seen_locations = {}
        for tiger in tigers:
            if hasattr(tiger, 'last_seen_location') and tiger.last_seen_location:
                location = tiger.last_seen_location
                last_seen_locations[location] = last_seen_locations.get(location, 0) + 1
        
        # Calculate identification rate (placeholder - would need actual identification data)
        identification_rate = 0
        
        # Create trends data from timeline
        trends = [
            {"date": date, "count": count} 
            for date, count in sorted(timeline_data.items())
        ]
        
        return {
            "total_tigers": len(tigers),
            "by_status": status_counts,  # Frontend expects this field name
            "status_distribution": status_counts,  # Keep both for compatibility
            "facility_distribution": facility_distribution,
            "timeline_data": timeline_data,
            "trends": trends,  # Frontend expects this field name
            "last_seen_locations": last_seen_locations,
            "identification_rate": identification_rate,  # Frontend expects this
            "monitored": len([
                t for t in tigers 
                if hasattr(t, 'status') and (
                    (hasattr(t.status, 'value') and t.status.value == "monitored") 
                    or str(t.status) == "monitored"
                )
            ]),
            "active": len([
                t for t in tigers 
                if hasattr(t, 'status') and (
                    (hasattr(t.status, 'value') and t.status.value == "active") 
                    or str(t.status) == "active"
                )
            ]),
            "seized": len([
                t for t in tigers 
                if hasattr(t, 'status') and (
                    (hasattr(t.status, 'value') and t.status.value == "seized") 
                    or str(t.status) == "seized"
                )
            ])
        }
    
    def get_facility_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get facility analytics
        
        Args:
            start_date: Start date filter
            end_date: End date filter
        
        Returns:
            Facility analytics dictionary
        """
        query = self.session.query(Facility)
        
        if start_date and hasattr(Facility, 'created_at'):
            query = query.filter(Facility.created_at >= start_date)
        if end_date and hasattr(Facility, 'created_at'):
            query = query.filter(Facility.created_at <= end_date)
        
        facilities = query.all()
        
        # State distribution
        state_counts = {}
        for facility in facilities:
            state = facility.state if hasattr(facility, 'state') else 'Unknown'
            state_counts[state] = state_counts.get(state, 0) + 1
        
        # Tiger count statistics
        tiger_counts = [f.tiger_count for f in facilities if hasattr(f, 'tiger_count') and f.tiger_count]
        total_tigers = sum(tiger_counts) if tiger_counts else 0
        avg_tigers_per_facility = total_tigers / len(facilities) if facilities else 0
        
        return {
            "total_facilities": len(facilities),
            "state_distribution": state_counts,
            "total_tigers": total_tigers,
            "avg_tigers_per_facility": round(avg_tigers_per_facility, 2),
            "facilities_with_violations": 0  # Add when violation data available
        }
    
    def get_agent_performance_analytics(
        self,
        investigation_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get agent performance analytics
        
        Args:
            investigation_id: Optional investigation ID filter
            start_date: Start date filter
            end_date: End date filter
        
        Returns:
            Agent performance analytics dictionary
        """
        query = self.session.query(InvestigationStep)
        
        if investigation_id:
            query = query.filter(InvestigationStep.investigation_id == investigation_id)
        
        # Join with investigations for date filtering
        query = query.join(Investigation)
        
        if start_date:
            query = query.filter(Investigation.created_at >= start_date)
        if end_date:
            query = query.filter(Investigation.created_at <= end_date)
        
        steps = query.all()
        
        # Agent activity counts
        agent_counts = {}
        for step in steps:
            agent_name = step.agent_name or "system"
            agent_counts[agent_name] = agent_counts.get(agent_name, 0) + 1
        
        # Step type distribution
        step_type_counts = {}
        for step in steps:
            step_type = step.step_type or "unknown"
            step_type_counts[step_type] = step_type_counts.get(step_type, 0) + 1
        
        # Success rate by agent
        agent_success = {}
        for step in steps:
            agent_name = step.agent_name or "system"
            if agent_name not in agent_success:
                agent_success[agent_name] = {"total": 0, "success": 0}
            agent_success[agent_name]["total"] += 1
            if step.status == "completed":
                agent_success[agent_name]["success"] += 1
        
        # Calculate success rates
        agent_success_rates = {}
        for agent, stats in agent_success.items():
            success_rate = (stats["success"] / stats["total"] * 100) if stats["total"] > 0 else 0
            agent_success_rates[agent] = {
                "success_rate": success_rate,
                "total_steps": stats["total"],
                "successful_steps": stats["success"]
            }
        
        return {
            "total_steps": len(steps),
            "agent_activity": agent_counts,
            "step_type_distribution": step_type_counts,
            "agent_success_rates": agent_success_rates,
            "unique_agents": len(agent_counts)
        }


def get_analytics_service(session: Session) -> AnalyticsService:
    """Get analytics service instance"""
    return AnalyticsService(session)

