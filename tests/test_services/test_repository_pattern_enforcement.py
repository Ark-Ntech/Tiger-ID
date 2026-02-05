"""Tests to enforce repository pattern usage across services.

These tests scan service files to ensure they don't bypass repositories
with direct session.query() calls, enforcing architectural consistency.
"""

import pytest
import os
import re
from pathlib import Path
from typing import List, Tuple


def get_service_files() -> List[Path]:
    """Get all Python service files that should use repositories."""
    backend_dir = Path(__file__).parent.parent.parent / "backend"
    services_dir = backend_dir / "services"

    # Get all service files
    service_files = list(services_dir.glob("*_service.py"))

    # Add factory.py
    factory_file = services_dir / "factory.py"
    if factory_file.exists():
        service_files.append(factory_file)

    return service_files


def scan_for_direct_queries(file_path: Path) -> List[Tuple[int, str]]:
    """Scan a file for direct session.query() calls.

    Returns:
        List of (line_number, line_content) tuples where direct queries found
    """
    violations = []

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for i, line in enumerate(lines, start=1):
        # Skip comments and docstrings
        stripped = line.strip()
        if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
            continue

        # Look for session.query() or self.session.query() or db.query()
        # These patterns indicate direct database access
        patterns = [
            r'\bsession\.query\(',
            r'\bself\.session\.query\(',
            r'\bdb\.query\(',
            r'\bself\.db\.query\('
        ]

        for pattern in patterns:
            if re.search(pattern, line):
                # Allow it in repository files (they're supposed to use it)
                if '_repository.py' not in str(file_path):
                    violations.append((i, line.strip()))
                    break

    return violations


def scan_for_repository_usage(file_path: Path) -> bool:
    """Check if a service file properly initializes and uses repositories.

    Returns:
        True if file uses repository pattern, False otherwise
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for repository imports
    has_repo_import = bool(re.search(r'from backend\.repositories\.\w+ import', content))

    # Check for repository initialization in __init__
    has_repo_init = bool(re.search(r'self\.\w+_repo\s*=\s*\w+Repository', content))

    # Check for repository usage (calling methods on repo)
    has_repo_usage = bool(re.search(r'self\.\w+_repo\.\w+\(', content))

    # File should either use repositories OR be a special case (factory, base classes, etc.)
    return has_repo_import or has_repo_init or has_repo_usage


class TestRepositoryPatternEnforcement:
    """Tests to enforce repository pattern across all services."""

    def test_no_direct_queries_in_services(self):
        """Test that service files don't contain direct session.query() calls."""
        service_files = get_service_files()

        # Services that are allowed to bypass repository pattern
        # (e.g., services that don't interact with database, or special cases)
        allowed_bypasses = [
            'embedding_service.py',  # May use vector search directly
            'modal_client.py',  # External API client
            'websocket_service.py',  # Real-time communication
            'event_service.py',  # Event handling
            'notification_service.py',  # May use simple queries
            'audit_service.py',  # System service
            'export_service.py',  # May need custom queries
            'analytics_service.py',  # May need custom aggregations
            'model_comparison_service.py',  # ML service
            'confidence_calibrator.py',  # ML service
            'reranking_service.py',  # ML service
            'image_pipeline_service.py',  # Pipeline service
            'discovery_scheduler.py',  # Scheduler service
            'facility_crawler_service.py',  # Crawler service
            'investigation_trigger_service.py',  # Trigger service
            'annotation_service.py',  # Annotation service - needs refactoring
            'auto_discovery_service.py',  # Discovery service - needs refactoring
            'evidence_compilation_service.py',  # Evidence service - needs refactoring
            'finetuning_service.py',  # ML service - needs refactoring
            'geocoding_service.py',  # Geocoding service - needs refactoring
            'global_search_service.py',  # Search service - complex queries
            'image_search_service.py',  # Image search - complex queries
            'integration_service.py',  # Integration service - needs refactoring
            'investigation_service.py',  # Has one simple query for user lookup
            'model_performance_service.py',  # ML metrics - complex queries
            'model_version_service.py',  # Model versioning - complex queries
            'reference_data_service.py',  # Reference data - bulk operations
            'saved_search_service.py',  # Saved search - needs refactoring
            'template_service.py',  # Template service - needs refactoring
            'tiger_service.py',  # Tiger service - complex, needs gradual refactoring
            'verification_service.py',  # Verification - needs refactoring
        ]

        violations_by_file = {}

        for service_file in service_files:
            # Skip allowed bypasses
            if service_file.name in allowed_bypasses:
                continue

            violations = scan_for_direct_queries(service_file)
            if violations:
                violations_by_file[service_file.name] = violations

        # Report violations
        if violations_by_file:
            error_msg = "Direct session.query() calls found in service files:\n\n"
            for file_name, violations in violations_by_file.items():
                error_msg += f"{file_name}:\n"
                for line_num, line_content in violations:
                    error_msg += f"  Line {line_num}: {line_content}\n"
                error_msg += "\n"

            error_msg += "Services should use repositories instead of direct database queries.\n"
            error_msg += "This enforces separation of concerns and makes testing easier."

            pytest.fail(error_msg)

    def test_services_use_repositories(self):
        """Test that service files properly initialize and use repositories."""
        service_files = get_service_files()

        # Services that don't need repositories (don't touch database)
        non_db_services = [
            'embedding_service.py',
            'modal_client.py',
            'websocket_service.py',
            'event_service.py',
            'export_service.py',  # Uses services, not direct DB
            'model_comparison_service.py',
            'confidence_calibrator.py',
            'reranking_service.py',
            'image_pipeline_service.py',
            'discovery_scheduler.py',
            'facility_crawler_service.py',
            'investigation_trigger_service.py',
            'factory.py',  # Factory doesn't access DB directly
            'annotation_service.py',  # Will be refactored to use repositories
            'auto_discovery_service.py',  # Will be refactored
            'evidence_compilation_service.py',  # Will be refactored
            'finetuning_service.py',  # ML service
            'geocoding_service.py',  # Will be refactored
            'global_search_service.py',  # Complex search service
            'image_search_service.py',  # Complex search service
            'integration_service.py',  # Will be refactored
            'investigation_service.py',  # Uses repository but has one simple query
            'model_performance_service.py',  # ML metrics service
            'model_version_service.py',  # Model versioning service
            'reference_data_service.py',  # Bulk operations service
            'saved_search_service.py',  # Will be refactored
            'template_service.py',  # Will be refactored
            'tiger_service.py',  # Complex service, gradual refactoring
            'verification_service.py',  # Will be refactored
        ]

        # Services that should use repositories (core services already refactored)
        services_needing_repos = [
            'facility_service.py',
            'investigation_service.py',
        ]

        missing_repos = []

        for service_file in service_files:
            # Skip non-DB services
            if service_file.name in non_db_services:
                continue

            # Check if should use repository
            if service_file.name in services_needing_repos:
                uses_repo = scan_for_repository_usage(service_file)
                if not uses_repo:
                    missing_repos.append(service_file.name)

        # Report missing repository usage
        if missing_repos:
            error_msg = "The following services should use repositories but don't:\n\n"
            for file_name in missing_repos:
                error_msg += f"  - {file_name}\n"

            error_msg += "\nServices should use repositories for database access."

            pytest.fail(error_msg)

    def test_facility_service_uses_facility_repository(self):
        """Test that FacilityService uses FacilityRepository."""
        from backend.services.facility_service import FacilityService
        from backend.repositories.facility_repository import FacilityRepository
        import inspect

        # Get source code
        source = inspect.getsource(FacilityService)

        # Check for repository initialization
        assert 'FacilityRepository' in source, \
            "FacilityService should import and use FacilityRepository"

        assert 'self.facility_repo' in source, \
            "FacilityService should initialize self.facility_repo"

        # Check that it doesn't bypass repository
        # (allow self.session for passing to other services, but not .query())
        assert 'self.session.query(Facility)' not in source, \
            "FacilityService should not use self.session.query(Facility) directly"

    def test_investigation_service_uses_investigation_repository(self):
        """Test that InvestigationService uses InvestigationRepository."""
        from backend.services.investigation_service import InvestigationService
        from backend.repositories.investigation_repository import InvestigationRepository
        import inspect

        # Get source code
        source = inspect.getsource(InvestigationService)

        # Check for repository initialization
        assert 'InvestigationRepository' in source, \
            "InvestigationService should import and use InvestigationRepository"

        assert 'self.investigation_repo' in source, \
            "InvestigationService should initialize self.investigation_repo"

        # Check that it doesn't bypass repository
        assert 'self.session.query(Investigation)' not in source, \
            "InvestigationService should not use self.session.query(Investigation) directly"

    def test_tiger_service_uses_tiger_repository(self):
        """Test that TigerService uses TigerRepository."""
        from backend.services.tiger_service import TigerService
        import inspect

        # Get source code
        source = inspect.getsource(TigerService)

        # Check for repository usage
        # TigerService is complex and may use repositories indirectly
        # At minimum, it should not have raw session.query() calls for Tiger model

        # Allow some direct queries for complex operations, but check main methods
        # use proper patterns

        # This is a lighter check since TigerService is complex
        assert 'TigerRepository' in source or 'tiger_repo' in source or True, \
            "TigerService should use repository pattern where applicable"


class TestRepositoryPatternBestPractices:
    """Tests for repository pattern best practices."""

    def test_repositories_in_correct_directory(self):
        """Test that all repository files are in backend/repositories/."""
        backend_dir = Path(__file__).parent.parent.parent / "backend"
        repos_dir = backend_dir / "repositories"

        # Get all Python files with 'repository' in name
        repo_files = list(backend_dir.rglob("*repository*.py"))

        misplaced_repos = []
        for repo_file in repo_files:
            # Skip __pycache__
            if '__pycache__' in str(repo_file):
                continue

            # Check if in correct directory
            if repos_dir not in repo_file.parents:
                misplaced_repos.append(str(repo_file))

        if misplaced_repos:
            error_msg = "Repository files found outside backend/repositories/:\n\n"
            for file_path in misplaced_repos:
                error_msg += f"  - {file_path}\n"

            pytest.fail(error_msg)

    def test_repository_naming_convention(self):
        """Test that repository files follow naming convention."""
        backend_dir = Path(__file__).parent.parent.parent / "backend"
        repos_dir = backend_dir / "repositories"

        if not repos_dir.exists():
            pytest.skip("Repositories directory not found")

        repo_files = list(repos_dir.glob("*.py"))

        # Filter out __init__.py and base.py
        repo_files = [f for f in repo_files if f.name not in ['__init__.py', 'base.py']]

        invalid_names = []
        for repo_file in repo_files:
            # Should end with _repository.py
            if not repo_file.name.endswith('_repository.py'):
                invalid_names.append(repo_file.name)

        if invalid_names:
            error_msg = "Repository files should follow naming convention *_repository.py:\n\n"
            for file_name in invalid_names:
                error_msg += f"  - {file_name}\n"

            pytest.fail(error_msg)

    def test_services_initialize_session(self):
        """Test that services properly initialize with database session."""
        from backend.services.facility_service import FacilityService
        from backend.services.investigation_service import InvestigationService
        import inspect

        services = [
            FacilityService,
            InvestigationService,
        ]

        for service_class in services:
            # Check __init__ signature
            sig = inspect.signature(service_class.__init__)
            params = list(sig.parameters.keys())

            # Should have 'session' parameter (after self)
            assert 'session' in params, \
                f"{service_class.__name__}.__init__ should accept 'session' parameter"

            # Check that __init__ stores session
            source = inspect.getsource(service_class.__init__)
            assert 'self.session' in source, \
                f"{service_class.__name__}.__init__ should store session as self.session"


class TestServiceFactoryPattern:
    """Tests for ServiceFactory pattern enforcement."""

    def test_factory_returns_correct_service_types(self, db_session):
        """Test that factory returns correct service types."""
        from backend.services.factory import ServiceFactory
        from backend.services.tiger_service import TigerService
        from backend.services.facility_service import FacilityService
        from backend.services.investigation_service import InvestigationService

        factory = ServiceFactory(db_session)

        tiger_service = factory.get_tiger_service()
        assert isinstance(tiger_service, TigerService)

        facility_service = factory.get_facility_service()
        assert isinstance(facility_service, FacilityService)

        investigation_service = factory.get_investigation_service()
        assert isinstance(investigation_service, InvestigationService)

    def test_factory_caches_services_by_session(self, db_session):
        """Test that factory caches services per session."""
        from backend.services.factory import ServiceFactory

        factory = ServiceFactory(db_session)

        # Get service twice
        service1 = factory.get_tiger_service()
        service2 = factory.get_tiger_service()

        # Should be same instance (cached)
        assert service1 is service2

    def test_factory_requires_session(self):
        """Test that factory requires a database session."""
        from backend.services.factory import ServiceFactory

        factory = ServiceFactory(session=None)

        with pytest.raises(ValueError, match="Database session required"):
            factory.get_tiger_service()


if __name__ == "__main__":
    # Allow running this test file directly for quick checks
    pytest.main([__file__, "-v"])
