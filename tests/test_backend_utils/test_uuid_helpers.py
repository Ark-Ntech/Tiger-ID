"""Tests for UUID helper utilities"""

import pytest
from uuid import UUID, uuid4

from backend.utils.uuid_helpers import safe_uuid, parse_uuid, uuid_to_string


class TestSafeUUID:
    """Tests for safe_uuid function"""
    
    def test_valid_uuid(self):
        """Test safe_uuid with valid UUID string"""
        uuid_str = str(uuid4())
        result = safe_uuid(uuid_str)
        
        assert result is not None
        assert isinstance(result, UUID)
        assert str(result) == uuid_str
    
    def test_invalid_uuid(self):
        """Test safe_uuid with invalid UUID string"""
        result = safe_uuid("not-a-uuid")
        
        assert result is None
    
    def test_none_input(self):
        """Test safe_uuid with None input"""
        result = safe_uuid(None)
        
        assert result is None
    
    def test_empty_string(self):
        """Test safe_uuid with empty string"""
        result = safe_uuid("")
        
        assert result is None
    
    def test_malformed_uuid(self):
        """Test safe_uuid with malformed UUID"""
        result = safe_uuid("12345678-1234-1234-1234")
        
        assert result is None
    
    def test_numeric_string(self):
        """Test safe_uuid with numeric string"""
        result = safe_uuid("123456789012345678901234567890")
        
        assert result is None


class TestParseUUID:
    """Tests for parse_uuid function"""
    
    def test_valid_uuid(self):
        """Test parse_uuid with valid UUID string"""
        uuid_str = str(uuid4())
        result = parse_uuid(uuid_str)
        
        assert isinstance(result, UUID)
        assert str(result) == uuid_str
    
    def test_invalid_uuid_raises_error(self):
        """Test parse_uuid with invalid UUID raises ValueError"""
        with pytest.raises(ValueError) as exc_info:
            parse_uuid("not-a-uuid")
        
        assert "Invalid UUID string" in str(exc_info.value)
    
    def test_empty_string_raises_error(self):
        """Test parse_uuid with empty string raises ValueError"""
        with pytest.raises(ValueError) as exc_info:
            parse_uuid("")
        
        assert "cannot be empty" in str(exc_info.value)
    
    def test_none_input_raises_error(self):
        """Test parse_uuid with None raises ValueError"""
        with pytest.raises(ValueError):
            parse_uuid(None)
    
    def test_malformed_uuid_raises_error(self):
        """Test parse_uuid with malformed UUID raises ValueError"""
        with pytest.raises(ValueError):
            parse_uuid("12345678-1234-1234-1234")


class TestUUIDToString:
    """Tests for uuid_to_string function"""
    
    def test_valid_uuid(self):
        """Test uuid_to_string with valid UUID"""
        uuid_obj = uuid4()
        result = uuid_to_string(uuid_obj)
        
        assert isinstance(result, str)
        assert result == str(uuid_obj)
    
    def test_none_input(self):
        """Test uuid_to_string with None input"""
        result = uuid_to_string(None)
        
        assert result is None
    
    def test_uuid_from_string(self):
        """Test uuid_to_string preserves UUID format"""
        uuid_str = str(uuid4())
        uuid_obj = UUID(uuid_str)
        result = uuid_to_string(uuid_obj)
        
        assert result == uuid_str

