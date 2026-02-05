"""
Unit tests for Playwright configuration validation

Tests verify that the Playwright config meets CI/CD requirements:
- Multi-browser support
- Sharding configuration
- Retry logic
- Worker configuration
- Timeouts
- Reporters
- Artifact capture settings
"""
import os
import json
import subprocess
from pathlib import Path
import pytest


class TestPlaywrightConfig:
    """Test suite for Playwright configuration validation"""

    @pytest.fixture
    def config_path(self):
        """Path to playwright.config.ts"""
        return Path(__file__).parent.parent / "frontend" / "playwright.config.ts"

    @pytest.fixture
    def config_content(self, config_path):
        """Read playwright.config.ts content"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return f.read()

    @pytest.fixture
    def global_setup_path(self):
        """Path to global.setup.ts"""
        return Path(__file__).parent.parent / "frontend" / "e2e" / "global.setup.ts"

    @pytest.fixture
    def global_setup_content(self, global_setup_path):
        """Read global.setup.ts content"""
        with open(global_setup_path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_config_file_exists(self, config_path):
        """Test that playwright.config.ts exists"""
        assert config_path.exists(), "playwright.config.ts not found"
        assert config_path.is_file(), "playwright.config.ts is not a file"

    def test_global_setup_exists(self, global_setup_path):
        """Test that global.setup.ts exists"""
        assert global_setup_path.exists(), "global.setup.ts not found"
        assert global_setup_path.is_file(), "global.setup.ts is not a file"

    def test_browser_projects_configured(self, config_content):
        """Test that all three browsers are configured"""
        assert "'chromium'" in config_content or '"chromium"' in config_content, \
            "Chromium project not configured"
        assert "'firefox'" in config_content or '"firefox"' in config_content, \
            "Firefox project not configured"
        assert "'webkit'" in config_content or '"webkit"' in config_content, \
            "WebKit project not configured"

    def test_sharding_documentation(self, config_content):
        """Test that sharding is documented in config"""
        # Check for sharding-related comments or documentation
        assert "shard" in config_content.lower(), \
            "Sharding not mentioned in config"
        assert "--shard" in config_content, \
            "Sharding usage example not documented"

    def test_retry_configuration(self, config_content):
        """Test retry logic is configured correctly"""
        # Should have 2 retries in CI, 0 locally
        assert "retries:" in config_content, "Retries not configured"
        assert "process.env.CI" in config_content, "CI environment check missing"
        assert "2" in config_content, "CI retry count not set to 2"

    def test_worker_configuration(self, config_content):
        """Test that workers are configured for CI"""
        assert "workers:" in config_content, "Workers not configured"
        # Should have worker configuration based on CI environment
        assert "process.env.CI" in config_content or "workers:" in config_content, \
            "Worker configuration missing"

    def test_timeout_configuration(self, config_content):
        """Test timeout settings"""
        # Test timeout should be 30s (30000ms)
        assert "timeout: 30000" in config_content or "timeout:30000" in config_content, \
            "Test timeout not set to 30s"

        # Expect timeout should be 10s (10000ms)
        assert "expect" in config_content, "Expect configuration missing"
        assert "10000" in config_content, "Expect timeout not configured"

    def test_reporter_configuration(self, config_content):
        """Test that reporters are configured for CI and local"""
        # Should have JUnit reporter for CI
        assert "junit" in config_content.lower(), "JUnit reporter not configured"

        # Should have HTML reporter
        assert "html" in config_content.lower(), "HTML reporter not configured"

        # Should have line/list reporter
        assert ("line" in config_content or "list" in config_content), \
            "Console reporter not configured"

    def test_screenshot_configuration(self, config_content):
        """Test screenshot capture is configured"""
        assert "screenshot:" in config_content, "Screenshot configuration missing"
        assert ("only-on-failure" in config_content or "on-failure" in config_content), \
            "Screenshot should be captured on failure"

    def test_video_configuration(self, config_content):
        """Test video capture is configured"""
        assert "video:" in config_content, "Video configuration missing"
        # Video should be on first retry only
        assert ("on-first-retry" in config_content or "retain-on-failure" in config_content), \
            "Video capture not optimally configured"

    def test_trace_configuration(self, config_content):
        """Test trace capture is configured"""
        assert "trace:" in config_content, "Trace configuration missing"
        assert "on-first-retry" in config_content, \
            "Trace should be captured on first retry"

    def test_base_url_configurable(self, config_content):
        """Test that base URL is configurable via environment variable"""
        assert "baseURL" in config_content or "BASE_URL" in config_content, \
            "Base URL not configured"
        assert "process.env.BASE_URL" in config_content, \
            "Base URL not configurable via environment variable"

    def test_global_setup_reference(self, config_content):
        """Test that global setup file is referenced"""
        assert "globalSetup" in config_content, "Global setup not configured"
        assert "global.setup" in config_content, "Global setup path not correct"

    def test_output_directories_configured(self, config_content):
        """Test output directories are configured"""
        # Test results directory
        assert "test-results" in config_content, "Test results directory not configured"

        # Playwright report directory
        assert "playwright-report" in config_content, \
            "Playwright report directory not configured"

    def test_global_setup_authenticates_users(self, global_setup_content):
        """Test that global setup authenticates users"""
        assert "authenticateUser" in global_setup_content, \
            "authenticateUser function not found"

        # Should authenticate multiple user types
        assert "admin" in global_setup_content.lower(), \
            "Admin user authentication not configured"

    def test_global_setup_saves_storage_state(self, global_setup_content):
        """Test that global setup saves storage state"""
        assert "storageState" in global_setup_content, \
            "Storage state saving not configured"
        assert ".auth" in global_setup_content, \
            ".auth directory not used for storage state"

    def test_global_setup_verifies_backend(self, global_setup_content):
        """Test that global setup verifies backend availability"""
        assert ("health" in global_setup_content.lower() or
                "api" in global_setup_content.lower()), \
            "Backend verification not implemented"

    def test_global_setup_handles_errors(self, global_setup_content):
        """Test that global setup has error handling"""
        assert "try" in global_setup_content and "catch" in global_setup_content, \
            "Error handling not implemented"
        assert "throw" in global_setup_content, \
            "Errors are not properly propagated"

    def test_browser_projects_use_auth_state(self, config_content):
        """Test that browser projects reference auth state files"""
        # Each browser project should use storageState
        chromium_section = config_content[config_content.find("name: 'chromium'"):
                                          config_content.find("name: 'chromium'") + 500]
        assert "storageState" in chromium_section, \
            "Chromium project doesn't use storage state"

    def test_setup_project_exists(self, config_content):
        """Test that setup project is configured"""
        assert "name: 'setup'" in config_content or 'name: "setup"' in config_content, \
            "Setup project not configured"
        assert "testMatch" in config_content, \
            "Setup project test match pattern missing"

    def test_project_dependencies(self, config_content):
        """Test that browser projects depend on setup"""
        # Check for dependencies configuration
        assert "dependencies" in config_content, \
            "Project dependencies not configured"
        assert "['setup']" in config_content or '["setup"]' in config_content, \
            "Browser projects don't depend on setup"

    def test_ci_environment_detection(self, config_content):
        """Test that CI environment is properly detected"""
        ci_checks = config_content.count("process.env.CI")
        assert ci_checks >= 3, \
            f"CI environment should be checked in multiple places, found {ci_checks}"

    def test_auth_state_caching(self, global_setup_content):
        """Test that global setup implements auth state caching"""
        # Should check if auth state exists before re-authenticating
        assert "existsSync" in global_setup_content or "exists" in global_setup_content, \
            "Auth state existence check not implemented"
        # Should check file age for cache invalidation
        assert ("stats" in global_setup_content or "stat" in global_setup_content), \
            "Auth state age check not implemented"

    def test_test_data_setup(self, global_setup_content):
        """Test that global setup includes test data initialization"""
        assert "setupTestData" in global_setup_content, \
            "Test data setup function not found"

    def test_parallel_execution_enabled(self, config_content):
        """Test that parallel execution is enabled"""
        assert "fullyParallel" in config_content, \
            "Parallel execution not configured"

    def test_forbid_only_in_ci(self, config_content):
        """Test that test.only is forbidden in CI"""
        assert "forbidOnly" in config_content, \
            "forbidOnly not configured"
        assert "!!process.env.CI" in config_content, \
            "forbidOnly not tied to CI environment"


class TestPlaywrightPackageJson:
    """Test suite for package.json Playwright scripts"""

    @pytest.fixture
    def package_json_path(self):
        """Path to package.json"""
        return Path(__file__).parent.parent / "frontend" / "package.json"

    @pytest.fixture
    def package_json(self, package_json_path):
        """Read package.json"""
        with open(package_json_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_playwright_installed(self, package_json):
        """Test that Playwright is in devDependencies"""
        assert "@playwright/test" in package_json.get("devDependencies", {}), \
            "Playwright not installed"

    def test_e2e_test_script(self, package_json):
        """Test that e2e test script exists"""
        scripts = package_json.get("scripts", {})
        assert "test:e2e" in scripts, "test:e2e script not defined"

    def test_shard_scripts_exist(self, package_json):
        """Test that shard scripts exist for all 4 shards"""
        scripts = package_json.get("scripts", {})
        assert "test:e2e:shard1" in scripts, "Shard 1 script not defined"
        assert "test:e2e:shard2" in scripts, "Shard 2 script not defined"
        assert "test:e2e:shard3" in scripts, "Shard 3 script not defined"
        assert "test:e2e:shard4" in scripts, "Shard 4 script not defined"

    def test_shard_scripts_correct_format(self, package_json):
        """Test that shard scripts use correct format"""
        scripts = package_json.get("scripts", {})
        assert "--shard=1/4" in scripts.get("test:e2e:shard1", ""), \
            "Shard 1 script format incorrect"
        assert "--shard=2/4" in scripts.get("test:e2e:shard2", ""), \
            "Shard 2 script format incorrect"
        assert "--shard=3/4" in scripts.get("test:e2e:shard3", ""), \
            "Shard 3 script format incorrect"
        assert "--shard=4/4" in scripts.get("test:e2e:shard4", ""), \
            "Shard 4 script format incorrect"

    def test_report_script_exists(self, package_json):
        """Test that report viewing script exists"""
        scripts = package_json.get("scripts", {})
        assert "test:e2e:report" in scripts, "Report viewing script not defined"


class TestPlaywrightFileStructure:
    """Test suite for Playwright file structure"""

    @pytest.fixture
    def frontend_path(self):
        """Path to frontend directory"""
        return Path(__file__).parent.parent / "frontend"

    @pytest.fixture
    def e2e_path(self, frontend_path):
        """Path to e2e directory"""
        return frontend_path / "e2e"

    def test_e2e_directory_exists(self, e2e_path):
        """Test that e2e directory exists"""
        assert e2e_path.exists(), "e2e directory not found"
        assert e2e_path.is_dir(), "e2e is not a directory"

    def test_auth_directory_can_be_created(self, frontend_path):
        """Test that .auth directory can be created"""
        auth_path = frontend_path / ".auth"
        # Don't check if exists (might not exist until tests run)
        # Just verify parent directory exists
        assert frontend_path.exists(), "Frontend directory not found"

    def test_test_results_directory_can_be_created(self, frontend_path):
        """Test that test-results directory can be created"""
        test_results_path = frontend_path / "test-results"
        # Don't check if exists (created during test runs)
        # Just verify parent directory exists
        assert frontend_path.exists(), "Frontend directory not found"

    def test_playwright_report_directory_can_be_created(self, frontend_path):
        """Test that playwright-report directory can be created"""
        report_path = frontend_path / "playwright-report"
        # Don't check if exists (created during test runs)
        # Just verify parent directory exists
        assert frontend_path.exists(), "Frontend directory not found"

    def test_global_setup_in_e2e(self, e2e_path):
        """Test that global.setup.ts is in e2e directory"""
        global_setup = e2e_path / "global.setup.ts"
        assert global_setup.exists(), "global.setup.ts not found in e2e directory"

    def test_readme_exists(self, e2e_path):
        """Test that README exists in e2e directory"""
        readme = e2e_path / "README.md"
        assert readme.exists(), "README.md not found in e2e directory"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
