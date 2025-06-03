"""
Unit tests for RefactoredHealthMonitor module.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import sys
from unittest.mock import Mock, AsyncMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from gemini_code.analysis.refactored_health_monitor import RefactoredHealthMonitor
from gemini_code.analysis.health_checks.base_checker import CheckResult


class TestRefactoredHealthMonitor:
    """Test suite for RefactoredHealthMonitor."""
    
    @pytest.fixture
    def temp_project_path(self):
        """Create temporary project directory with test files."""
        temp_dir = tempfile.mkdtemp()
        
        # Create test Python files
        test_files = {
            'good_file.py': '''
"""Good quality Python file."""

def calculate_sum(a: int, b: int) -> int:
    """Calculate sum of two numbers."""
    return a + b

class Calculator:
    """Simple calculator class."""
    
    def add(self, x: int, y: int) -> int:
        """Add two numbers."""
        return x + y
''',
            'bad_file.py': '''
def very_long_function_with_many_lines():
    x = 1
    y = 2
    z = 3
    a = 4
    b = 5
    c = 6
    d = 7
    e = 8
    f = 9
    g = 10
    h = 11
    i = 12
    j = 13
    k = 14
    l = 15
    m = 16
    n = 17
    o = 18
    p = 19
    q = 20
    r = 21
    s = 22
    t = 23
    u = 24
    v = 25
    w = 26
    x = 27
    y = 28
    z = 29
    return x + y + z

def BadNamingFunction():
    try:
        pass
    except:
        pass
''',
            'syntax_error.py': '''
def broken_function(
    print("Missing closing parenthesis"
''',
            'test_example.py': '''
"""Test file example."""
import unittest

class TestCalculator(unittest.TestCase):
    """Test calculator functionality."""
    
    def test_addition(self):
        """Test addition operation."""
        self.assertEqual(2 + 2, 4)
'''
        }
        
        for filename, content in test_files.items():
            file_path = Path(temp_dir) / filename
            file_path.write_text(content)
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_gemini_client(self):
        """Mock Gemini client."""
        client = Mock()
        client.generate_response = AsyncMock(return_value="Mock analysis result")
        return client
    
    @pytest.fixture
    def mock_file_manager(self):
        """Mock file manager."""
        return Mock()
    
    @pytest.fixture
    def health_monitor(self, mock_gemini_client, mock_file_manager):
        """RefactoredHealthMonitor instance with mocked dependencies."""
        return RefactoredHealthMonitor(mock_gemini_client, mock_file_manager)
    
    def test_initialization(self, health_monitor):
        """Test RefactoredHealthMonitor initialization."""
        assert health_monitor.gemini_client is not None
        assert health_monitor.file_manager is not None
        assert len(health_monitor.checkers) == 5
        assert len(health_monitor.checker_weights) == 5
        
        # Check that all expected checkers are present
        checker_names = [checker.__class__.__name__ for checker in health_monitor.checkers]
        expected_checkers = [
            'ErrorChecker',
            'CodeQualityChecker',
            'PerformanceChecker',
            'DocumentationChecker',
            'TestCoverageChecker'
        ]
        
        for expected in expected_checkers:
            assert expected in checker_names
    
    def test_checker_weights_sum(self, health_monitor):
        """Test that checker weights sum to approximately 1.0."""
        total_weight = sum(health_monitor.checker_weights.values())
        assert abs(total_weight - 1.0) < 0.01  # Allow small floating point differences
    
    @pytest.mark.asyncio
    async def test_run_full_analysis(self, health_monitor, temp_project_path):
        """Test full health analysis."""
        result = await health_monitor.run_full_analysis(temp_project_path)
        
        # Check basic structure
        assert 'overall_score' in result
        assert 'status' in result
        assert 'analysis_time' in result
        assert 'timestamp' in result
        assert 'summary' in result
        assert 'recommendations' in result
        assert 'detailed_results' in result
        
        # Check score is valid
        assert 0 <= result['overall_score'] <= 100
        
        # Check status is valid
        assert result['status'] in ['healthy', 'needs_attention', 'critical']
        
        # Check that all checkers ran
        assert len(result['detailed_results']) == 5
    
    @pytest.mark.asyncio
    async def test_error_checker_integration(self, health_monitor, temp_project_path):
        """Test error checker integration."""
        result = await health_monitor.run_full_analysis(temp_project_path)
        
        # Should detect syntax error in syntax_error.py
        error_result = result['detailed_results'].get('Error Check')
        assert error_result is not None
        assert error_result['details']['syntax_errors'] > 0
        assert error_result['score'] < 100  # Should be penalized for syntax errors
    
    @pytest.mark.asyncio
    async def test_code_quality_integration(self, health_monitor, temp_project_path):
        """Test code quality checker integration."""
        result = await health_monitor.run_full_analysis(temp_project_path)
        
        quality_result = result['detailed_results'].get('Code Quality Check')
        assert quality_result is not None
        assert 'complexity_issues' in quality_result['details']
        assert 'naming_issues' in quality_result['details']
        assert 'long_functions' in quality_result['details']
    
    @pytest.mark.asyncio
    async def test_test_coverage_integration(self, health_monitor, temp_project_path):
        """Test test coverage checker integration."""
        result = await health_monitor.run_full_analysis(temp_project_path)
        
        test_result = result['detailed_results'].get('Test Coverage Check')
        assert test_result is not None
        assert 'test_files' in test_result['details']
        assert 'source_files' in test_result['details']
        
        # Should detect test_example.py as a test file
        assert test_result['details']['test_files'] >= 1
    
    def test_calculate_overall_score(self, health_monitor):
        """Test overall score calculation."""
        # Create mock results
        mock_results = [
            CheckResult("Error Check", 90, "good", {}, [], 0.1),
            CheckResult("Code Quality Check", 80, "good", {}, [], 0.1),
            CheckResult("Performance Check", 70, "warning", {}, [], 0.1),
            CheckResult("Documentation Check", 60, "warning", {}, [], 0.1),
            CheckResult("Test Coverage Check", 50, "critical", {}, [], 0.1)
        ]
        
        score = health_monitor._calculate_overall_score(mock_results)
        
        # Score should be weighted average
        assert 0 <= score <= 100
        assert isinstance(score, float)
        
        # Should be closer to higher-weighted scores (errors have highest weight)
        assert score > 50  # Error score (90) should pull average up
    
    def test_determine_overall_status(self, health_monitor):
        """Test overall status determination."""
        assert health_monitor._determine_overall_status(90) == "healthy"
        assert health_monitor._determine_overall_status(70) == "needs_attention"
        assert health_monitor._determine_overall_status(30) == "critical"
        assert health_monitor._determine_overall_status(80) == "healthy"
        assert health_monitor._determine_overall_status(50) == "needs_attention"
    
    def test_prioritize_recommendations(self, health_monitor):
        """Test recommendation prioritization."""
        mock_results = [
            CheckResult("Critical Check", 20, "critical", {}, ["Fix critical issue"], 0.1),
            CheckResult("Warning Check", 60, "warning", {}, ["Fix warning issue"], 0.1),
            CheckResult("Good Check", 90, "good", {}, ["Improvement suggestion"], 0.1)
        ]
        
        recommendations = health_monitor._prioritize_recommendations([], mock_results)
        
        # Should prioritize critical recommendations first
        assert len(recommendations) > 0
        assert "Fix critical issue" in recommendations
        
        # Critical should come before warning and good
        critical_index = recommendations.index("Fix critical issue")
        if "Fix warning issue" in recommendations:
            warning_index = recommendations.index("Fix warning issue")
            assert critical_index < warning_index
    
    @pytest.mark.asyncio
    async def test_run_specific_check(self, health_monitor, temp_project_path):
        """Test running specific health checks."""
        # Test error check
        error_result = await health_monitor.run_specific_check("errors", temp_project_path)
        assert error_result.name == "Error Check"
        assert isinstance(error_result.score, (int, float))
        
        # Test quality check
        quality_result = await health_monitor.run_specific_check("quality", temp_project_path)
        assert quality_result.name == "Code Quality Check"
        
        # Test invalid check name
        with pytest.raises(ValueError):
            await health_monitor.run_specific_check("invalid", temp_project_path)
    
    def test_get_available_checks(self, health_monitor):
        """Test getting available health checks."""
        checks = health_monitor.get_available_checks()
        
        assert len(checks) == 5
        expected_checks = [
            'ErrorChecker',
            'CodeQualityChecker',
            'PerformanceChecker',
            'DocumentationChecker',
            'TestCoverageChecker'
        ]
        
        for expected in expected_checks:
            assert expected in checks
    
    def test_legacy_field_extraction(self, health_monitor):
        """Test extraction of legacy fields for backward compatibility."""
        mock_results = [
            CheckResult("Error Check", 80, "good", {
                "syntax_errors": 2,
                "import_errors": 1,
                "runtime_issues": 0,
                "total_files": 10
            }, [], 0.1),
            CheckResult("Code Quality Check", 70, "warning", {}, [], 0.1),
            CheckResult("Performance Check", 85, "good", {}, [], 0.1),
            CheckResult("Documentation Check", 60, "warning", {}, [], 0.1)
        ]
        
        errors_count = health_monitor._extract_errors_count(mock_results)
        assert errors_count == 3  # 2 + 1 + 0
        
        files_count = health_monitor._extract_files_count(mock_results)
        assert files_count == 10
        
        quality_score = health_monitor._extract_quality_score(mock_results)
        assert quality_score == 7.0  # 70 / 10
    
    @pytest.mark.asyncio
    async def test_checker_failure_handling(self, health_monitor, temp_project_path):
        """Test handling of checker failures."""
        # Mock one checker to fail
        original_check = health_monitor.checkers[0].check
        health_monitor.checkers[0].check = AsyncMock(side_effect=Exception("Test error"))
        
        result = await health_monitor.run_full_analysis(temp_project_path)
        
        # Should still complete with fallback results
        assert 'overall_score' in result
        assert result['overall_score'] >= 0
        
        # Should have results for all checkers (including failed one with fallback)
        assert len(result['detailed_results']) == 5
        
        # Restore original method
        health_monitor.checkers[0].check = original_check
    
    @pytest.mark.asyncio
    async def test_empty_project_handling(self, health_monitor):
        """Test handling of empty project directory."""
        with tempfile.TemporaryDirectory() as empty_dir:
            result = await health_monitor.run_full_analysis(empty_dir)
            
            # Should handle empty project gracefully
            assert 'overall_score' in result
            assert result['overall_score'] >= 0
            assert result['status'] in ['healthy', 'needs_attention', 'critical']


if __name__ == "__main__":
    pytest.main([__file__])