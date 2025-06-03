"""
Documentation checker for health monitoring.
"""

import ast
import time
from typing import Dict, Any, List
from pathlib import Path

from .base_checker import BaseHealthChecker, CheckResult


class DocumentationChecker(BaseHealthChecker):
    """Checks documentation coverage and quality."""
    
    def get_threshold_config(self) -> Dict[str, float]:
        """Documentation thresholds."""
        return {
            'good': 70,      # Good documentation coverage
            'warning': 40,   # Minimal documentation
            'critical': 0    # Poor documentation
        }
    
    async def check(self, project_path: str) -> CheckResult:
        """Check documentation coverage."""
        start_time = time.time()
        
        python_files = self._filter_valid_python_files(project_path)
        
        if not python_files:
            return CheckResult(
                name="Documentation Check",
                score=100,
                status="good",
                details={"message": "No Python files found to check"},
                recommendations=[],
                execution_time=time.time() - start_time
            )
        
        total_functions = 0
        documented_functions = 0
        total_classes = 0
        documented_classes = 0
        
        documentation_issues = []
        
        for file_path in python_files:
            file_stats = self._analyze_file_documentation(file_path)
            
            total_functions += file_stats["total_functions"]
            documented_functions += file_stats["documented_functions"]
            total_classes += file_stats["total_classes"]
            documented_classes += file_stats["documented_classes"]
            
            documentation_issues.extend(file_stats["issues"])
        
        # Calculate coverage
        if total_functions + total_classes == 0:
            coverage = 100
        else:
            coverage = ((documented_functions + documented_classes) / 
                       (total_functions + total_classes)) * 100
        
        # Determine status
        thresholds = self.get_threshold_config()
        status = self._calculate_status(coverage, thresholds)
        
        # Generate recommendations
        recommendations = self._generate_documentation_recommendations(
            total_functions, documented_functions, total_classes, documented_classes
        )
        
        details = {
            "total_functions": total_functions,
            "documented_functions": documented_functions,
            "total_classes": total_classes,
            "documented_classes": documented_classes,
            "function_coverage": round((documented_functions / max(1, total_functions)) * 100, 1),
            "class_coverage": round((documented_classes / max(1, total_classes)) * 100, 1),
            "overall_coverage": round(coverage, 1),
            "undocumented_items": len(documentation_issues)
        }
        
        return CheckResult(
            name="Documentation Check",
            score=coverage,
            status=status,
            details=details,
            recommendations=recommendations,
            execution_time=time.time() - start_time
        )
    
    def _analyze_file_documentation(self, file_path: Path) -> Dict[str, Any]:
        """Analyze documentation in a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            total_functions = 0
            documented_functions = 0
            total_classes = 0
            documented_classes = 0
            issues = []
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Skip private methods and special methods for documentation requirements
                    if not node.name.startswith('_'):
                        total_functions += 1
                        
                        if self._has_docstring(node):
                            documented_functions += 1
                        else:
                            issues.append({
                                "file": str(file_path),
                                "name": node.name,
                                "type": "function",
                                "line": node.lineno
                            })
                
                elif isinstance(node, ast.ClassDef):
                    total_classes += 1
                    
                    if self._has_docstring(node):
                        documented_classes += 1
                    else:
                        issues.append({
                            "file": str(file_path),
                            "name": node.name,
                            "type": "class",
                            "line": node.lineno
                        })
            
            return {
                "total_functions": total_functions,
                "documented_functions": documented_functions,
                "total_classes": total_classes,
                "documented_classes": documented_classes,
                "issues": issues
            }
            
        except Exception:
            return {
                "total_functions": 0,
                "documented_functions": 0,
                "total_classes": 0,
                "documented_classes": 0,
                "issues": []
            }
    
    def _has_docstring(self, node: ast.AST) -> bool:
        """Check if node has a docstring."""
        return (
            node.body and
            isinstance(node.body[0], ast.Expr) and
            isinstance(node.body[0].value, ast.Constant) and
            isinstance(node.body[0].value.value, str) and
            len(node.body[0].value.value.strip()) > 10  # Minimum meaningful docstring length
        )
    
    def _generate_documentation_recommendations(self, total_functions: int, documented_functions: int,
                                               total_classes: int, documented_classes: int) -> List[str]:
        """Generate documentation improvement recommendations."""
        recommendations = []
        
        undocumented_functions = total_functions - documented_functions
        undocumented_classes = total_classes - documented_classes
        
        if undocumented_functions > 0:
            recommendations.append(f"📝 Add docstrings to {undocumented_functions} public functions")
        
        if undocumented_classes > 0:
            recommendations.append(f"📚 Add docstrings to {undocumented_classes} classes")
        
        if total_functions + total_classes > 0:
            coverage = ((documented_functions + documented_classes) / 
                       (total_functions + total_classes)) * 100
            
            if coverage < 30:
                recommendations.append("💡 Start with docstrings for the most important/complex functions")
                recommendations.append("📖 Use tools like pydoc to generate documentation from docstrings")
            elif coverage < 70:
                recommendations.append("💡 Focus on documenting public APIs and complex logic")
                recommendations.append("📋 Include parameter descriptions and return value explanations")
            else:
                recommendations.append("✨ Great documentation coverage! Consider adding examples")
        
        if not recommendations:
            recommendations.append("📖 Excellent documentation coverage!")
        
        return recommendations