"""Data models/schemas for external API responses"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class USDAFacility(BaseModel):
    """USDA facility record"""
    license_number: str = Field(..., description="USDA license number")
    exhibitor_name: str = Field(..., description="Facility/exhibitor name")
    state: Optional[str] = Field(None, description="State code")
    city: Optional[str] = Field(None, description="City name")
    address: Optional[str] = Field(None, description="Facility address")
    license_type: Optional[str] = Field(None, description="License type")
    status: Optional[str] = Field(None, description="License status")
    issue_date: Optional[datetime] = Field(None, description="License issue date")
    expiration_date: Optional[datetime] = Field(None, description="License expiration date")
    tiger_count: Optional[int] = Field(None, description="Number of tigers")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class USDAInspectionReport(BaseModel):
    """USDA inspection report"""
    report_id: str = Field(..., description="Inspection report ID")
    license_number: str = Field(..., description="USDA license number")
    inspection_date: datetime = Field(..., description="Inspection date")
    inspector_name: Optional[str] = Field(None, description="Inspector name")
    findings: Optional[str] = Field(None, description="Inspection findings")
    violations: List[str] = Field(default_factory=list, description="List of violations")
    compliance_status: Optional[str] = Field(None, description="Compliance status")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class CITESTradeRecord(BaseModel):
    """CITES trade record"""
    record_id: str = Field(..., description="Trade record ID")
    species: str = Field(..., description="Scientific species name")
    common_name: Optional[str] = Field(None, description="Common species name")
    country_origin: str = Field(..., description="Origin country code")
    country_destination: str = Field(..., description="Destination country code")
    quantity: Optional[int] = Field(None, description="Quantity traded")
    unit: Optional[str] = Field(None, description="Unit of quantity")
    purpose: Optional[str] = Field(None, description="Trade purpose code")
    source: Optional[str] = Field(None, description="Source code")
    year: int = Field(..., description="Year of trade")
    permit_number: Optional[str] = Field(None, description="CITES permit number")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class CITESPermit(BaseModel):
    """CITES permit record"""
    permit_number: str = Field(..., description="Permit number")
    species: str = Field(..., description="Scientific species name")
    country_origin: str = Field(..., description="Origin country code")
    country_destination: str = Field(..., description="Destination country code")
    issue_date: Optional[datetime] = Field(None, description="Permit issue date")
    expiration_date: Optional[datetime] = Field(None, description="Permit expiration date")
    quantity: Optional[int] = Field(None, description="Permitted quantity")
    purpose: Optional[str] = Field(None, description="Trade purpose")
    status: Optional[str] = Field(None, description="Permit status")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class USFWSPermit(BaseModel):
    """USFWS permit record"""
    permit_number: str = Field(..., description="Permit number")
    applicant_name: str = Field(..., description="Applicant name")
    permit_type: str = Field(..., description="Type of permit (Import/Export)")
    species: Optional[str] = Field(None, description="Species name")
    issue_date: Optional[datetime] = Field(None, description="Permit issue date")
    expiration_date: Optional[datetime] = Field(None, description="Permit expiration date")
    status: Optional[str] = Field(None, description="Permit status")
    purpose: Optional[str] = Field(None, description="Permit purpose")
    country_origin: Optional[str] = Field(None, description="Origin country")
    country_destination: Optional[str] = Field(None, description="Destination country")
    quantity: Optional[int] = Field(None, description="Permitted quantity")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class USFWSLaceyActDeclaration(BaseModel):
    """USFWS Lacey Act declaration"""
    declaration_id: str = Field(..., description="Declaration ID")
    importer_name: str = Field(..., description="Importer name")
    species: str = Field(..., description="Species name")
    country_origin: str = Field(..., description="Origin country code")
    import_date: Optional[datetime] = Field(None, description="Import date")
    quantity: Optional[int] = Field(None, description="Quantity imported")
    unit: Optional[str] = Field(None, description="Unit of quantity")
    port_entry: Optional[str] = Field(None, description="Port of entry")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ESARecord(BaseModel):
    """Endangered Species Act record"""
    record_id: str = Field(..., description="Record ID")
    species: str = Field(..., description="Species name")
    action_type: str = Field(..., description="Type of action")
    action_date: Optional[datetime] = Field(None, description="Action date")
    status: Optional[str] = Field(None, description="Status")
    region: Optional[str] = Field(None, description="Region")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class APIResponse(BaseModel):
    """Generic API response wrapper"""
    success: bool = Field(..., description="Whether request was successful")
    data: Any = Field(..., description="Response data")
    message: Optional[str] = Field(None, description="Response message")
    error: Optional[str] = Field(None, description="Error message if failed")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

