"""
Performance checker for health monitoring.
"""

import ast
import time
from typing import Dict, Any, List
from pathlib import Path

from .base_checker import BaseHealthChecker, CheckResult


class PerformanceChecker(BaseHealthChecker):
    """Checks for performance issues."""
    
    def get_threshold_config(self) -> Dict[str, float]:
        """Performance thresholds."""
        return {
            'good': 80,      # Good performance
            'warning': 60,   # Some performance issues
            'critical': 0    # Significant performance issues
        }
    
    async def check(self, project_path: str) -> CheckResult:
        """Check for performance issues."""
        start_time = time.time()
        
        python_files = self._filter_valid_python_files(project_path)
        
        if not python_files:
            return CheckResult(
                name="Performance Check",
                score=100,
                status="good",
                details={"message": "No Python files found to check"},
                recommendations=[],
                execution_time=time.time() - start_time
            )
        
        performance_issues = {
            "inefficient_loops": [],
            "string_concatenation": [],
            "unnecessary_imports": [],
            "memory_leaks": []
        }
        
        total_penalty = 0
        files_checked = 0
        
        for file_path in python_files:
            file_penalty = self._analyze_file_performance(file_path, performance_issues)
            total_penalty += file_penalty
            files_checked += 1
        
        # Calculate score
        if files_checked == 0:
            score = 100
        else:
            # Average penalty per file, capped at 100
            avg_penalty = min(100, total_penalty / files_checked)
            score = max(0, 100 - avg_penalty)
        
        # Determine status
        thresholds = self.get_threshold_config()
        status = self._calculate_status(score, thresholds)
        
        # Generate recommendations
        recommendations = self._generate_performance_recommendations(performance_issues)
        
        details = {
            "total_files": files_checked,
            "inefficient_loops": len(performance_issues["inefficient_loops"]),
            "string_concat_issues": len(performance_issues["string_concatenation"]),
            "unnecessary_imports": len(performance_issues["unnecessary_imports"]),
            "memory_issues": len(performance_issues["memory_leaks"]),
            "top_issues": self._get_top_performance_issues(performance_issues)
        }
        
        return CheckResult(
            name="Performance Check",
            score=score,
            status=status,
            details=details,
            recommendations=recommendations,
            execution_time=time.time() - start_time
        )
    
    def _analyze_file_performance(self, file_path: Path, issues: Dict) -> float:
        """Analyze performance of a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            penalty = 0
            
            # Check for performance anti-patterns
            penalty += self._check_inefficient_loops(tree, file_path, issues)
            penalty += self._check_string_concatenation(tree, file_path, issues)
            penalty += self._check_unnecessary_imports(tree, file_path, issues)
            penalty += self._check_memory_issues(tree, file_path, issues)
            
            return penalty
            
        except Exception:
            return 0  # Can't analyze, no penalty
    
    def _check_inefficient_loops(self, tree: ast.AST, file_path: Path, issues: Dict) -> float:
        """Check for inefficient loop patterns."""
        penalty = 0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.AsyncFor)):
                # Check for nested loops (potential O(n²) issues)
                nested_loops = [n for n in ast.walk(node) if isinstance(n, (ast.For, ast.AsyncFor)) and n != node]
                if len(nested_loops) >= 2:
                    issues["inefficient_loops"].append({
                        "file": str(file_path),
                        "line": node.lineno,
                        "type": "deeply_nested_loops",
                        "nesting_level": len(nested_loops) + 1,
                        "severity": "warning"
                    })
                    penalty += 5
                
                # Check for list.append() in loops (should use list comprehension)
                for child in ast.walk(node):
                    if (isinstance(child, ast.Call) and
                        isinstance(child.func, ast.Attribute) and
                        child.func.attr == 'append'):
                        issues["inefficient_loops"].append({
                            "file": str(file_path),
                            "line": node.lineno,
                            "type": "append_in_loop",
                            "suggestion": "Consider using list comprehension",
                            "severity": "info"
                        })
                        penalty += 2
        
        return penalty
    
    def _check_string_concatenation(self, tree: ast.AST, file_path: Path, issues: Dict) -> float:
        """Check for inefficient string concatenation."""
        penalty = 0
        
        for node in ast.walk(tree):
            # Check for string concatenation in loops
            if isinstance(node, (ast.For, ast.AsyncFor)):
                for child in ast.walk(node):
                    if (isinstance(child, ast.AugAssign) and
                        isinstance(child.op, ast.Add)):
                        # Potential string concatenation in loop
                        issues["string_concatenation"].append({
                            "file": str(file_path),
                            "line": child.lineno,
                            "type": "string_concat_in_loop",
                            "suggestion": "Use join() or f-strings instead",
                            "severity": "warning"
                        })
                        penalty += 3
        
        return penalty
    
    def _check_unnecessary_imports(self, tree: ast.AST, file_path: Path, issues: Dict) -> float:
        """Check for unnecessary imports."""
        penalty = 0
        
        # Collect all imports
        imports = set()
        used_names = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.asname or alias.name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imports.add(alias.asname or alias.name)
            elif isinstance(node, ast.Name):
                used_names.add(node.id)
        
        # Find unused imports
        unused_imports = imports - used_names
        if len(unused_imports) > 3:  # Only penalize if many unused imports
            issues["unnecessary_imports"].append({
                "file": str(file_path),
                "unused_count": len(unused_imports),
                "unused_imports": list(unused_imports)[:10],  # Limit to 10
                "severity": "info"
            })
            penalty += len(unused_imports) * 0.5
        
        return penalty
    
    def _check_memory_issues(self, tree: ast.AST, file_path: Path, issues: Dict) -> float:
        """Check for potential memory issues."""
        penalty = 0
        
        for node in ast.walk(tree):
            # Check for large list/dict comprehensions
            if isinstance(node, (ast.ListComp, ast.DictComp, ast.SetComp)):
                # Heuristic: nested loops in comprehensions can be memory intensive
                generators = [g for g in ast.walk(node) if isinstance(g, ast.comprehension)]
                if len(generators) > 1:
                    issues["memory_leaks"].append({
                        "file": str(file_path),
                        "line": node.lineno,
                        "type": "complex_comprehension",
                        "suggestion": "Consider using generator expressions or breaking into smaller parts",
                        "severity": "info"
                    })
                    penalty += 2
            
            # Check for potential memory leaks with file handling
            if isinstance(node, ast.Call):
                if (isinstance(node.func, ast.Name) and node.func.id == 'open'):
                    # Check if 'with' statement is used for file handling
                    parent = node
                    in_with = False
                    # Simple check - this is a heuristic
                    for ancestor in ast.walk(tree):
                        if (isinstance(ancestor, ast.With) and
                            any(isinstance(item.context_expr, ast.Call) and
                                isinstance(item.context_expr.func, ast.Name) and
                                item.context_expr.func.id == 'open'
                                for item in ancestor.items)):
                            in_with = True
                            break
                    
                    if not in_with:
                        issues["memory_leaks"].append({
                            "file": str(file_path),
                            "line": node.lineno,
                            "type": "file_without_context_manager",
                            "suggestion": "Use 'with' statement for file handling",
                            "severity": "warning"
                        })
                        penalty += 3
        
        return penalty
    
    def _get_top_performance_issues(self, issues: Dict) -> List[Dict]:
        """Get top performance issues."""
        all_issues = []
        
        for category, issue_list in issues.items():
            for issue in issue_list:
                issue["category"] = category
                all_issues.append(issue)
        
        # Sort by severity
        all_issues.sort(key=lambda x: (x["severity"] != "warning", x["severity"] != "info"))
        
        return all_issues[:10]
    
    def _generate_performance_recommendations(self, issues: Dict) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []
        
        inefficient_loops = len(issues["inefficient_loops"])
        if inefficient_loops > 0:
            recommendations.append(f"🔄 Optimize {inefficient_loops} inefficient loop patterns")
            recommendations.append("💡 Use list comprehensions and avoid nested loops when possible")
        
        string_issues = len(issues["string_concatenation"])
        if string_issues > 0:
            recommendations.append(f"🔤 Fix {string_issues} string concatenation issues")
            recommendations.append("💡 Use join() for multiple strings or f-strings for formatting")
        
        unused_imports = len(issues["unnecessary_imports"])
        if unused_imports > 0:
            recommendations.append(f"🧹 Remove {unused_imports} unused imports")
            recommendations.append("💡 Use tools like autoflake to automatically remove unused imports")
        
        memory_issues = len(issues["memory_leaks"])
        if memory_issues > 0:
            recommendations.append(f"🧠 Address {memory_issues} potential memory issues")
            recommendations.append("💡 Use context managers and generator expressions for better memory usage")
        
        if not recommendations:
            recommendations.append("⚡ No major performance issues detected!")
        
        return recommendations