"""Relationship analysis service for mapping connections between entities"""

from typing import Dict, Any, List, Optional, Set, Tuple
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from collections import defaultdict

from backend.database import get_db_session, Facility, Tiger, Evidence, Investigation
from backend.services.reference_data_service import ReferenceDataService
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class RelationshipAnalysisService:
    """Service for analyzing relationships between facilities, tigers, and other entities"""
    
    def __init__(self, session: Optional[Session] = None):
        """
        Initialize relationship analysis service
        
        Args:
            session: Database session (optional)
        """
        self.session = session
        if session:
            self.ref_service = ReferenceDataService(session)
    
    def analyze_facility_relationships(
        self,
        facility_id: UUID
    ) -> Dict[str, Any]:
        """
        Analyze relationships for a specific facility
        
        Args:
            facility_id: Facility ID to analyze
            
        Returns:
            Relationship analysis results
        """
        if not self.session:
            with get_db_session() as session:
                self.session = session
                self.ref_service = ReferenceDataService(session)
                return self.analyze_facility_relationships(facility_id)
        
        facility = self.session.query(Facility).filter(
            Facility.facility_id == facility_id
        ).first()
        
        if not facility:
            return {"error": "Facility not found"}
        
        relationships = {
            "facility_id": str(facility_id),
            "facility_name": facility.exhibitor_name,
            "connections": [],
            "network": {}
        }
        
        # Find tigers associated with this facility
        tigers = self.session.query(Tiger).filter(
            Tiger.origin_facility_id == facility_id
        ).all()
        
        relationships["tigers"] = [
            {
                "tiger_id": str(t.tiger_id),
                "name": t.name,
                "status": t.status
            }
            for t in tigers
        ]
        
        # Find shared tigers (tigers seen at multiple facilities)
        if tigers:
            tiger_ids = [t.tiger_id for t in tigers]
            
            # Look for evidence mentioning these tigers at other facilities
            evidence_items = self.session.query(Evidence).filter(
                Evidence.content.contains({"tiger_id": str(tiger_id)})
            ).all()
            
            for evidence in evidence_items:
                if "facility_id" in evidence.content:
                    other_facility_id = evidence.content["facility_id"]
                    if other_facility_id != str(facility_id):
                        relationships["connections"].append({
                            "type": "shared_tiger",
                            "facility_id": other_facility_id,
                            "connection_strength": 0.8
                        })
        
        # Find geographic proximity (same state/city)
        if facility.state or facility.city:
            nearby_facilities = self.session.query(Facility).filter(
                Facility.facility_id != facility_id
            )
            
            if facility.state:
                nearby_facilities = nearby_facilities.filter(Facility.state == facility.state)
            if facility.city:
                nearby_facilities = nearby_facilities.filter(Facility.city == facility.city)
            
            for nearby in nearby_facilities.all():
                relationships["connections"].append({
                    "type": "geographic_proximity",
                    "facility_id": str(nearby.facility_id),
                    "facility_name": nearby.exhibitor_name,
                    "connection_strength": 0.6 if facility.city else 0.4
                })
        
        # Remove duplicates and group by facility
        unique_connections = {}
        for conn in relationships["connections"]:
            other_id = conn["facility_id"]
            if other_id not in unique_connections:
                unique_connections[other_id] = conn
            else:
                # Merge connections, increase strength
                unique_connections[other_id]["connection_strength"] = min(1.0, 
                    unique_connections[other_id]["connection_strength"] + 0.1)
        
        relationships["connections"] = list(unique_connections.values())
        
        return relationships
    
    def build_network_graph(
        self,
        facility_ids: Optional[List[UUID]] = None,
        include_reference_facilities: bool = True
    ) -> Dict[str, Any]:
        """
        Build a network graph of facility relationships
        
        Args:
            facility_ids: Specific facility IDs to include (None for all)
            include_reference_facilities: Include reference facilities in network
            
        Returns:
            Network graph data
        """
        if not self.session:
            with get_db_session() as session:
                self.session = session
                self.ref_service = ReferenceDataService(session)
                return self.build_network_graph(facility_ids, include_reference_facilities)
        
        # Get facilities to analyze
        query = self.session.query(Facility)
        
        if facility_ids:
            query = query.filter(Facility.facility_id.in_(facility_ids))
        elif include_reference_facilities:
            query = query.filter(Facility.is_reference_facility == True)
        
        facilities = query.all()
        
        nodes = []
        edges = []
        
        # Create nodes
        for facility in facilities:
            node = {
                "id": str(facility.facility_id),
                "label": facility.exhibitor_name,
                "type": "facility",
                "is_reference": facility.is_reference_facility or False,
                "state": facility.state,
                "tiger_count": facility.tiger_count
            }
            nodes.append(node)
        
        # Create edges (relationships)
        for facility in facilities:
            relationships = self.analyze_facility_relationships(facility.facility_id)
            
            for conn in relationships.get("connections", []):
                edge = {
                    "from": str(facility.facility_id),
                    "to": conn["facility_id"],
                    "type": conn["type"],
                    "strength": conn["connection_strength"],
                    "label": conn["type"].replace("_", " ").title()
                }
                edges.append(edge)
        
        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges)
        }
    
    def find_common_patterns(
        self,
        facility_ids: List[UUID]
    ) -> Dict[str, Any]:
        """
        Find common patterns among facilities
        
        Args:
            facility_ids: Facility IDs to analyze
            
        Returns:
            Common patterns found
        """
        if not self.session:
            with get_db_session() as session:
                self.session = session
                self.ref_service = ReferenceDataService(session)
                return self.find_common_patterns(facility_ids)
        
        facilities = self.session.query(Facility).filter(
            Facility.facility_id.in_(facility_ids)
        ).all()
        
        patterns = {
            "common_states": defaultdict(int),
            "common_cities": defaultdict(int),
            "common_violations": defaultdict(int),
            "shared_tigers": [],
            "social_media_patterns": defaultdict(list)
        }
        
        for facility in facilities:
            if facility.state:
                patterns["common_states"][facility.state] += 1
            if facility.city:
                patterns["common_cities"][facility.city] += 1
            
            if facility.violation_history:
                for violation in facility.violation_history:
                    patterns["common_violations"][violation.get("type", "unknown")] += 1
            
            if facility.social_media_links:
                for platform in facility.social_media_links.keys():
                    patterns["social_media_patterns"][platform].append(str(facility.facility_id))
        
        # Find most common patterns
        common_patterns = {
            "most_common_state": max(patterns["common_states"].items(), key=lambda x: x[1])[0] if patterns["common_states"] else None,
            "most_common_city": max(patterns["common_cities"].items(), key=lambda x: x[1])[0] if patterns["common_cities"] else None,
            "most_common_violation": max(patterns["common_violations"].items(), key=lambda x: x[1])[0] if patterns["common_violations"] else None,
            "platforms_used": list(patterns["social_media_patterns"].keys())
        }
        
        return {
            "patterns": patterns,
            "common_patterns": common_patterns,
            "facility_count": len(facilities)
        }
    
    def map_timeline_relationships(
        self,
        facility_id: UUID,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """
        Map timeline of relationships for a facility
        
        Args:
            facility_id: Facility ID
            date_range: Optional date range to filter by
            
        Returns:
            Timeline relationships
        """
        if not self.session:
            with get_db_session() as session:
                self.session = session
                self.ref_service = ReferenceDataService(session)
                return self.map_timeline_relationships(facility_id, date_range)
        
        facility = self.session.query(Facility).filter(
            Facility.facility_id == facility_id
        ).first()
        
        if not facility:
            return {"error": "Facility not found"}
        
        # Get evidence related to this facility
        query = self.session.query(Evidence).filter(
            Evidence.content.contains({"facility_id": str(facility_id)})
        )
        
        if date_range:
            query = query.filter(
                Evidence.created_at >= date_range[0],
                Evidence.created_at <= date_range[1]
            )
        
        evidence_items = query.order_by(Evidence.created_at).all()
        
        timeline_events = []
        
        for evidence in evidence_items:
            event = {
                "date": evidence.created_at.isoformat(),
                "type": evidence.source_type,
                "url": evidence.source_url,
                "relevance": evidence.relevance_score
            }
            
            # Extract related entities from content
            content = evidence.content or {}
            if "tiger_id" in content:
                event["related_tiger"] = content["tiger_id"]
            if "matched_facilities" in content:
                event["matched_facilities"] = content["matched_facilities"]
            
            timeline_events.append(event)
        
        return {
            "facility_id": str(facility_id),
            "facility_name": facility.exhibitor_name,
            "timeline_events": timeline_events,
            "event_count": len(timeline_events),
            "date_range": date_range
        }


def get_relationship_analysis_service(session: Optional[Session] = None) -> RelationshipAnalysisService:
    """Get relationship analysis service instance"""
    return RelationshipAnalysisService(session)

