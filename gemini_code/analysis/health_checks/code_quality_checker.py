"""
Code quality checker for health monitoring.
"""

import ast
from typing import Dict, Any, List
from pathlib import Path
import time

from .base_checker import BaseHealthChecker, CheckResult


class CodeQualityChecker(BaseHealthChecker):
    """Checks code quality metrics."""
    
    def get_threshold_config(self) -> Dict[str, float]:
        """Code quality thresholds."""
        return {
            'good': 75,      # Good quality code
            'warning': 50,   # Acceptable quality
            'critical': 0    # Poor quality
        }
    
    async def check(self, project_path: str) -> CheckResult:
        """Check code quality metrics."""
        start_time = time.time()
        
        python_files = self._filter_valid_python_files(project_path)
        
        if not python_files:
            return CheckResult(
                name="Code Quality Check",
                score=100,
                status="good",
                details={"message": "No Python files found to check"},
                recommendations=[],
                execution_time=time.time() - start_time
            )
        
        quality_metrics = {
            "complexity": [],
            "length": [],
            "documentation": [],
            "naming": []
        }
        
        total_score = 0
        file_scores = []
        
        for file_path in python_files:
            file_score = self._analyze_file_quality(file_path, quality_metrics)
            file_scores.append(file_score)
            total_score += file_score
        
        # Calculate average score
        if file_scores:
            average_score = total_score / len(file_scores)
        else:
            average_score = 100
        
        # Determine status
        thresholds = self.get_threshold_config()
        status = self._calculate_status(average_score, thresholds)
        
        # Generate recommendations
        recommendations = self._generate_quality_recommendations(quality_metrics, average_score)
        
        details = {
            "total_files": len(python_files),
            "average_score": round(average_score, 1),
            "complexity_issues": len([m for m in quality_metrics["complexity"] if m["severity"] != "good"]),
            "long_functions": len([m for m in quality_metrics["length"] if m["severity"] != "good"]),
            "undocumented": len([m for m in quality_metrics["documentation"] if m["severity"] != "good"]),
            "naming_issues": len([m for m in quality_metrics["naming"] if m["severity"] != "good"]),
            "top_issues": self._get_top_issues(quality_metrics)
        }
        
        return CheckResult(
            name="Code Quality Check",
            score=average_score,
            status=status,
            details=details,
            recommendations=recommendations,
            execution_time=time.time() - start_time
        )
    
    def _analyze_file_quality(self, file_path: Path, quality_metrics: Dict) -> float:
        """Analyze quality of a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Initialize file score
            file_score = 100
            
            # Check cyclomatic complexity
            complexity_penalty = self._check_complexity(tree, file_path, quality_metrics)
            file_score -= complexity_penalty
            
            # Check function length
            length_penalty = self._check_function_length(tree, file_path, quality_metrics)
            file_score -= length_penalty
            
            # Check documentation
            doc_penalty = self._check_documentation(tree, file_path, quality_metrics)
            file_score -= doc_penalty
            
            # Check naming conventions
            naming_penalty = self._check_naming(tree, file_path, quality_metrics)
            file_score -= naming_penalty
            
            return max(0, file_score)
            
        except Exception:
            return 50  # Default score for unparseable files
    
    def _check_complexity(self, tree: ast.AST, file_path: Path, metrics: Dict) -> float:
        """Check cyclomatic complexity."""
        penalty = 0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = self._calculate_complexity(node)
                
                if complexity > 15:  # Very high complexity
                    metrics["complexity"].append({
                        "file": str(file_path),
                        "function": node.name,
                        "complexity": complexity,
                        "line": node.lineno,
                        "severity": "critical"
                    })
                    penalty += 10
                elif complexity > 10:  # High complexity
                    metrics["complexity"].append({
                        "file": str(file_path),
                        "function": node.name,
                        "complexity": complexity,
                        "line": node.lineno,
                        "severity": "warning"
                    })
                    penalty += 5
        
        return penalty
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            # Count decision points
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.With, ast.AsyncWith):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # Count boolean operators
                complexity += len(child.values) - 1
        
        return complexity
    
    def _check_function_length(self, tree: ast.AST, file_path: Path, metrics: Dict) -> float:
        """Check function length."""
        penalty = 0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Calculate function length in lines
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    length = node.end_lineno - node.lineno
                else:
                    length = 0
                
                if length > 100:  # Very long function
                    metrics["length"].append({
                        "file": str(file_path),
                        "function": node.name,
                        "length": length,
                        "line": node.lineno,
                        "severity": "critical"
                    })
                    penalty += 8
                elif length > 50:  # Long function
                    metrics["length"].append({
                        "file": str(file_path),
                        "function": node.name,
                        "length": length,
                        "line": node.lineno,
                        "severity": "warning"
                    })
                    penalty += 3
        
        return penalty
    
    def _check_documentation(self, tree: ast.AST, file_path: Path, metrics: Dict) -> float:
        """Check documentation coverage."""
        penalty = 0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                has_docstring = (
                    node.body and
                    isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)
                )
                
                if not has_docstring:
                    metrics["documentation"].append({
                        "file": str(file_path),
                        "name": node.name,
                        "type": type(node).__name__,
                        "line": node.lineno,
                        "severity": "warning"
                    })
                    penalty += 2
        
        return penalty
    
    def _check_naming(self, tree: ast.AST, file_path: Path, metrics: Dict) -> float:
        """Check naming conventions."""
        penalty = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check function naming (should be snake_case)
                if not self._is_snake_case(node.name) and not node.name.startswith('_'):
                    metrics["naming"].append({
                        "file": str(file_path),
                        "name": node.name,
                        "type": "function",
                        "issue": "not_snake_case",
                        "line": node.lineno,
                        "severity": "warning"
                    })
                    penalty += 1
            
            elif isinstance(node, ast.ClassDef):
                # Check class naming (should be PascalCase)
                if not self._is_pascal_case(node.name):
                    metrics["naming"].append({
                        "file": str(file_path),
                        "name": node.name,
                        "type": "class",
                        "issue": "not_pascal_case",
                        "line": node.lineno,
                        "severity": "warning"
                    })
                    penalty += 1
        
        return penalty
    
    def _is_snake_case(self, name: str) -> bool:
        """Check if name follows snake_case convention."""
        return name.islower() and '_' in name or name.islower()
    
    def _is_pascal_case(self, name: str) -> bool:
        """Check if name follows PascalCase convention."""
        return name[0].isupper() and not '_' in name
    
    def _get_top_issues(self, metrics: Dict) -> List[Dict]:
        """Get top quality issues."""
        all_issues = []
        
        for category, issues in metrics.items():
            for issue in issues:
                issue["category"] = category
                all_issues.append(issue)
        
        # Sort by severity (critical first, then warning)
        all_issues.sort(key=lambda x: (x["severity"] != "critical", x["severity"] != "warning"))
        
        return all_issues[:10]  # Return top 10 issues
    
    def _generate_quality_recommendations(self, metrics: Dict, score: float) -> List[str]:
        """Generate quality improvement recommendations."""
        recommendations = []
        
        complexity_issues = len([m for m in metrics["complexity"] if m["severity"] == "critical"])
        if complexity_issues > 0:
            recommendations.append(f"🧠 Refactor {complexity_issues} highly complex functions")
            recommendations.append("💡 Break down complex functions into smaller, focused ones")
        
        long_functions = len([m for m in metrics["length"] if m["severity"] == "critical"])
        if long_functions > 0:
            recommendations.append(f"📏 Split {long_functions} very long functions")
            recommendations.append("💡 Keep functions under 50 lines when possible")
        
        undocumented = len(metrics["documentation"])
        if undocumented > 5:
            recommendations.append(f"📝 Add documentation to {undocumented} functions/classes")
            recommendations.append("💡 Use docstrings to explain function purpose and parameters")
        
        naming_issues = len(metrics["naming"])
        if naming_issues > 3:
            recommendations.append(f"🏷️ Fix {naming_issues} naming convention issues")
            recommendations.append("💡 Use snake_case for functions and PascalCase for classes")
        
        if score > 80:
            recommendations.append("✨ Excellent code quality! Keep up the good work!")
        elif not recommendations:
            recommendations.append("📈 Code quality is good but could be improved")
        
        return recommendations