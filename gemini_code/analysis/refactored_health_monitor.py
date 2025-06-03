"""
Refactored Health Monitor using modular checkers.
"""

import asyncio
import time
from typing import Dict, Any, List
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime

from ..core.gemini_client import GeminiClient
from ..core.file_manager import FileManagementSystem
from .health_checks import (
    ErrorChecker,
    CodeQualityChecker,
    PerformanceChecker,
    DocumentationChecker,
    TestCoverageChecker
)
from .health_checks.base_checker import CheckResult


@dataclass
class HealthReport:
    """Comprehensive health report."""
    overall_score: float
    status: str  # 'healthy', 'needs_attention', 'critical'
    check_results: List[CheckResult]
    summary: Dict[str, Any]
    recommendations: List[str]
    scan_duration: float
    timestamp: datetime


class RefactoredHealthMonitor:
    """Modular health monitor using specialized checkers."""
    
    def __init__(self, gemini_client: GeminiClient, file_manager: FileManagementSystem):
        self.gemini_client = gemini_client
        self.file_manager = file_manager
        
        # Initialize checkers
        self.checkers = [
            ErrorChecker(gemini_client, file_manager),
            CodeQualityChecker(gemini_client, file_manager),
            PerformanceChecker(gemini_client, file_manager),
            DocumentationChecker(gemini_client, file_manager),
            TestCoverageChecker(gemini_client, file_manager)
        ]
        
        # Weights for overall score calculation
        self.checker_weights = {
            'ErrorChecker': 0.35,          # Errors are most critical
            'CodeQualityChecker': 0.25,    # Quality is important
            'PerformanceChecker': 0.20,    # Performance matters
            'DocumentationChecker': 0.15,  # Documentation is valuable
            'TestCoverageChecker': 0.15    # Tests are essential
        }
    
    async def run_full_analysis(self, project_path: str) -> Dict[str, Any]:
        """Run comprehensive health analysis."""
        start_time = time.time()
        
        try:
            # Run all checkers concurrently
            check_tasks = [
                checker.check(project_path) for checker in self.checkers
            ]
            
            check_results = await asyncio.gather(*check_tasks, return_exceptions=True)
            
            # Handle any exceptions
            valid_results = []
            for i, result in enumerate(check_results):
                if isinstance(result, Exception):
                    # Create a fallback result for failed checkers
                    checker_name = self.checkers[i].__class__.__name__
                    fallback_result = CheckResult(
                        name=f"{checker_name} (Failed)",
                        score=50,  # Neutral score for failed checks
                        status="warning",
                        details={"error": str(result)},
                        recommendations=[f"Fix {checker_name} configuration"],
                        execution_time=0
                    )
                    valid_results.append(fallback_result)
                else:
                    valid_results.append(result)
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(valid_results)
            
            # Determine overall status
            status = self._determine_overall_status(overall_score)
            
            # Generate summary
            summary = self._generate_summary(valid_results)
            
            # Collect all recommendations
            all_recommendations = []
            for result in valid_results:
                all_recommendations.extend(result.recommendations)
            
            # Prioritize recommendations
            prioritized_recommendations = self._prioritize_recommendations(
                all_recommendations, valid_results
            )
            
            scan_duration = time.time() - start_time
            
            # Create health report
            health_report = HealthReport(
                overall_score=overall_score,
                status=status,
                check_results=valid_results,
                summary=summary,
                recommendations=prioritized_recommendations,
                scan_duration=scan_duration,
                timestamp=datetime.now()
            )
            
            # Convert to dict for backward compatibility
            return self._report_to_dict(health_report)
            
        except Exception as e:
            # Fallback for complete failure
            return {
                "overall_score": 0,
                "status": "critical",
                "error": str(e),
                "analysis_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            }
    
    def _calculate_overall_score(self, results: List[CheckResult]) -> float:
        """Calculate weighted overall score."""
        total_weighted_score = 0
        total_weight = 0
        
        for result in results:
            checker_name = result.name.replace(" Check", "Checker").replace(" (Failed)", "Checker")
            weight = self.checker_weights.get(checker_name, 0.1)  # Default weight
            
            total_weighted_score += result.score * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0
        
        return total_weighted_score / total_weight
    
    def _determine_overall_status(self, score: float) -> str:
        """Determine overall health status."""
        if score >= 80:
            return "healthy"
        elif score >= 50:
            return "needs_attention"
        else:
            return "critical"
    
    def _generate_summary(self, results: List[CheckResult]) -> Dict[str, Any]:
        """Generate summary of all check results."""
        summary = {
            "checks_run": len(results),
            "checks_passed": len([r for r in results if r.status == "good"]),
            "checks_warning": len([r for r in results if r.status == "warning"]),
            "checks_critical": len([r for r in results if r.status == "critical"]),
            "detailed_scores": {}
        }
        
        for result in results:
            summary["detailed_scores"][result.name] = {
                "score": result.score,
                "status": result.status,
                "execution_time": result.execution_time
            }
        
        return summary
    
    def _prioritize_recommendations(self, recommendations: List[str], 
                                   results: List[CheckResult]) -> List[str]:
        """Prioritize recommendations based on check results."""
        prioritized = []
        
        # First, add critical recommendations (from critical status checks)
        for result in results:
            if result.status == "critical":
                prioritized.extend(result.recommendations[:2])  # Top 2 from critical
        
        # Then, add warning recommendations
        for result in results:
            if result.status == "warning":
                prioritized.extend(result.recommendations[:1])  # Top 1 from warning
        
        # Finally, add good status recommendations (improvements)
        for result in results:
            if result.status == "good":
                prioritized.extend(result.recommendations[:1])  # Top 1 from good
        
        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in prioritized:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)
        
        return unique_recommendations[:10]  # Limit to top 10
    
    def _report_to_dict(self, report: HealthReport) -> Dict[str, Any]:
        """Convert health report to dictionary for backward compatibility."""
        return {
            "overall_score": report.overall_score,
            "status": report.status,
            "analysis_time": report.scan_duration,
            "timestamp": report.timestamp.isoformat(),
            "summary": report.summary,
            "recommendations": report.recommendations,
            "detailed_results": {
                result.name: {
                    "score": result.score,
                    "status": result.status,
                    "details": result.details,
                    "recommendations": result.recommendations,
                    "execution_time": result.execution_time
                }
                for result in report.check_results
            },
            # Legacy fields for compatibility
            "errors_found": self._extract_errors_count(report.check_results),
            "files_analyzed": self._extract_files_count(report.check_results),
            "code_quality_score": self._extract_quality_score(report.check_results),
            "performance_score": self._extract_performance_score(report.check_results),
            "documentation_score": self._extract_documentation_score(report.check_results)
        }
    
    def _extract_errors_count(self, results: List[CheckResult]) -> int:
        """Extract error count for backward compatibility."""
        for result in results:
            if "Error" in result.name:
                details = result.details
                return (
                    details.get("syntax_errors", 0) +
                    details.get("import_errors", 0) +
                    details.get("runtime_issues", 0)
                )
        return 0
    
    def _extract_files_count(self, results: List[CheckResult]) -> int:
        """Extract files analyzed count."""
        for result in results:
            if "Error" in result.name:
                return result.details.get("total_files", 0)
        return 0
    
    def _extract_quality_score(self, results: List[CheckResult]) -> float:
        """Extract code quality score."""
        for result in results:
            if "Quality" in result.name:
                return result.score / 10  # Convert to 0-10 scale
        return 5.0
    
    def _extract_performance_score(self, results: List[CheckResult]) -> float:
        """Extract performance score."""
        for result in results:
            if "Performance" in result.name:
                return result.score / 10  # Convert to 0-10 scale
        return 5.0
    
    def _extract_documentation_score(self, results: List[CheckResult]) -> float:
        """Extract documentation score."""
        for result in results:
            if "Documentation" in result.name:
                return result.score / 10  # Convert to 0-10 scale
        return 5.0
    
    async def run_specific_check(self, check_name: str, project_path: str) -> CheckResult:
        """Run a specific health check."""
        checker_map = {
            "errors": ErrorChecker,
            "quality": CodeQualityChecker,
            "performance": PerformanceChecker,
            "documentation": DocumentationChecker,
            "tests": TestCoverageChecker
        }
        
        checker_class = checker_map.get(check_name.lower())
        if not checker_class:
            raise ValueError(f"Unknown check: {check_name}")
        
        checker = checker_class(self.gemini_client, self.file_manager)
        return await checker.check(project_path)
    
    def get_available_checks(self) -> List[str]:
        """Get list of available health checks."""
        return [checker.__class__.__name__ for checker in self.checkers]