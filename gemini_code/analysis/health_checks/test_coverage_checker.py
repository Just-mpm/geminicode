"""
Test coverage checker for health monitoring.
"""

import time
from typing import Dict, Any, List
from pathlib import Path

from .base_checker import BaseHealthChecker, CheckResult


class TestCoverageChecker(BaseHealthChecker):
    """Checks test coverage and quality."""
    
    def get_threshold_config(self) -> Dict[str, float]:
        """Test coverage thresholds."""
        return {
            'good': 60,      # Good test coverage
            'warning': 30,   # Some tests present
            'critical': 0    # No tests
        }
    
    async def check(self, project_path: str) -> CheckResult:
        """Check test coverage."""
        start_time = time.time()
        
        python_files = self._filter_valid_python_files(project_path)
        test_files = self._find_test_files(project_path)
        
        if not python_files:
            return CheckResult(
                name="Test Coverage Check",
                score=100,
                status="good",
                details={"message": "No Python files found to check"},
                recommendations=[],
                execution_time=time.time() - start_time
            )
        
        # Calculate basic metrics
        source_files = [f for f in python_files if not self._is_test_file(f)]
        
        if not source_files:
            coverage = 100  # Only test files exist
        else:
            # Simple heuristic: ratio of test files to source files
            test_ratio = len(test_files) / len(source_files)
            
            # Estimate coverage based on test file presence and naming patterns
            coverage = min(100, test_ratio * 80)  # Cap at 80% for heuristic
            
            # Bonus for comprehensive test naming
            if self._has_comprehensive_tests(test_files):
                coverage = min(100, coverage * 1.2)
        
        # Determine status
        thresholds = self.get_threshold_config()
        status = self._calculate_status(coverage, thresholds)
        
        # Generate recommendations
        recommendations = self._generate_test_recommendations(
            len(source_files), len(test_files), coverage
        )
        
        details = {
            "source_files": len(source_files),
            "test_files": len(test_files),
            "test_ratio": round(len(test_files) / max(1, len(source_files)), 2),
            "estimated_coverage": round(coverage, 1),
            "test_file_list": [str(f.name) for f in test_files[:10]],  # First 10
            "missing_tests": self._find_untested_modules(source_files, test_files)
        }
        
        return CheckResult(
            name="Test Coverage Check",
            score=coverage,
            status=status,
            details=details,
            recommendations=recommendations,
            execution_time=time.time() - start_time
        )
    
    def _find_test_files(self, project_path: str) -> List[Path]:
        """Find test files in the project."""
        test_files = []
        project_path = Path(project_path)
        
        # Common test patterns
        test_patterns = [
            '**/test_*.py',
            '**/*_test.py',
            '**/tests/*.py',
            '**/test/*.py'
        ]
        
        for pattern in test_patterns:
            test_files.extend(project_path.glob(pattern))
        
        # Remove duplicates and filter valid files
        unique_test_files = []
        seen = set()
        
        for f in test_files:
            if f.is_file() and str(f) not in seen:
                seen.add(str(f))
                unique_test_files.append(f)
        
        return unique_test_files
    
    def _is_test_file(self, file_path: Path) -> bool:
        """Check if a file is a test file."""
        name = file_path.name
        return (
            name.startswith('test_') or
            name.endswith('_test.py') or
            'test' in file_path.parts
        )
    
    def _has_comprehensive_tests(self, test_files: List[Path]) -> bool:
        """Check if tests appear comprehensive based on naming."""
        if not test_files:
            return False
        
        # Check for various test types
        test_types = {
            'unit': False,
            'integration': False,
            'functional': False,
            'e2e': False
        }
        
        for test_file in test_files:
            content_lower = str(test_file).lower()
            
            if 'unit' in content_lower:
                test_types['unit'] = True
            if 'integration' in content_lower:
                test_types['integration'] = True
            if 'functional' in content_lower:
                test_types['functional'] = True
            if 'e2e' in content_lower or 'end_to_end' in content_lower:
                test_types['e2e'] = True
        
        # Consider comprehensive if at least 2 types are present
        return sum(test_types.values()) >= 2
    
    def _find_untested_modules(self, source_files: List[Path], test_files: List[Path]) -> List[str]:
        """Find source modules that don't have corresponding tests."""
        untested = []
        
        # Extract module names from test files
        tested_modules = set()
        for test_file in test_files:
            name = test_file.name
            
            # Extract module name from test file name
            if name.startswith('test_'):
                module_name = name[5:-3]  # Remove 'test_' prefix and '.py' suffix
                tested_modules.add(module_name)
            elif name.endswith('_test.py'):
                module_name = name[:-8]  # Remove '_test.py' suffix
                tested_modules.add(module_name)
        
        # Check which source files don't have tests
        for source_file in source_files:
            module_name = source_file.stem  # filename without extension
            
            # Skip special files
            if module_name.startswith('__') or module_name in ['setup', 'main']:
                continue
            
            if module_name not in tested_modules:
                untested.append(module_name)
        
        return untested[:10]  # Return first 10
    
    def _generate_test_recommendations(self, source_count: int, test_count: int, coverage: float) -> List[str]:
        """Generate test improvement recommendations."""
        recommendations = []
        
        if test_count == 0:
            recommendations.append("🧪 Start by creating unit tests for core functionality")
            recommendations.append("💡 Use pytest or unittest framework for testing")
            recommendations.append("📝 Begin with testing the most critical functions")
        
        elif coverage < 30:
            recommendations.append(f"🧪 Increase test coverage - currently {test_count} test files for {source_count} source files")
            recommendations.append("💡 Focus on testing public APIs and business logic")
            recommendations.append("🎯 Aim for at least one test file per source module")
        
        elif coverage < 60:
            recommendations.append("🧪 Good start on testing! Consider adding more comprehensive tests")
            recommendations.append("💡 Add integration tests to complement unit tests")
            recommendations.append("🔍 Test edge cases and error conditions")
        
        else:
            recommendations.append("✨ Great test coverage! Keep maintaining it")
            recommendations.append("💡 Consider adding performance and end-to-end tests")
        
        # Always recommend automation
        if test_count > 0:
            recommendations.append("🤖 Set up automated testing in CI/CD pipeline")
        
        return recommendations