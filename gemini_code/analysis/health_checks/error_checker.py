"""
Error checker for health monitoring.
"""

import ast
import sys
import subprocess
from typing import Dict, Any, List
from pathlib import Path
import time

from .base_checker import BaseHealthChecker, CheckResult


class ErrorChecker(BaseHealthChecker):
    """Checks for syntax and runtime errors."""
    
    def get_threshold_config(self) -> Dict[str, float]:
        """Error thresholds."""
        return {
            'good': 95,      # < 5% files with errors
            'warning': 80,   # < 20% files with errors
            'critical': 0    # Any critical errors
        }
    
    async def check(self, project_path: str) -> CheckResult:
        """Check for errors in the project."""
        start_time = time.time()
        
        python_files = self._filter_valid_python_files(project_path)
        
        if not python_files:
            return CheckResult(
                name="Error Check",
                score=100,
                status="good",
                details={"message": "No Python files found to check"},
                recommendations=[],
                execution_time=time.time() - start_time
            )
        
        syntax_errors = []
        import_errors = []
        runtime_issues = []
        
        for file_path in python_files:
            # Check syntax errors
            syntax_result = self._check_syntax(file_path)
            if syntax_result:
                syntax_errors.append(syntax_result)
            
            # Check import errors
            import_result = self._check_imports(file_path)
            if import_result:
                import_errors.append(import_result)
            
            # Basic runtime issue detection
            runtime_result = self._check_runtime_issues(file_path)
            if runtime_result:
                runtime_issues.extend(runtime_result)
        
        # Calculate score
        total_files = len(python_files)
        error_files = len(set([err['file'] for err in syntax_errors + import_errors]))
        
        if total_files == 0:
            score = 100
        else:
            error_rate = (error_files / total_files) * 100
            score = max(0, 100 - error_rate * 2)  # Penalize errors heavily
        
        # Determine status
        thresholds = self.get_threshold_config()
        status = self._calculate_status(score, thresholds)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(syntax_errors, import_errors, runtime_issues)
        
        details = {
            "total_files": total_files,
            "syntax_errors": len(syntax_errors),
            "import_errors": len(import_errors),
            "runtime_issues": len(runtime_issues),
            "error_details": {
                "syntax": syntax_errors[:5],  # Limit to first 5
                "imports": import_errors[:5],
                "runtime": runtime_issues[:5]
            }
        }
        
        return CheckResult(
            name="Error Check",
            score=score,
            status=status,
            details=details,
            recommendations=recommendations,
            execution_time=time.time() - start_time
        )
    
    def _check_syntax(self, file_path: Path) -> Dict[str, Any]:
        """Check for syntax errors."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try to parse the AST
            ast.parse(content)
            return None
            
        except SyntaxError as e:
            return {
                "file": str(file_path),
                "type": "syntax",
                "line": e.lineno,
                "message": str(e),
                "severity": "critical"
            }
        except Exception as e:
            return {
                "file": str(file_path),
                "type": "parsing",
                "message": str(e),
                "severity": "warning"
            }
    
    def _check_imports(self, file_path: Path) -> Dict[str, Any]:
        """Check for import errors."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Extract imports
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
            
            # Check if imports are available (basic check)
            missing_imports = []
            for imp in imports:
                if imp and not self._is_import_available(imp):
                    missing_imports.append(imp)
            
            if missing_imports:
                return {
                    "file": str(file_path),
                    "type": "import",
                    "missing_imports": missing_imports,
                    "severity": "warning"
                }
            
            return None
            
        except Exception:
            return None
    
    def _is_import_available(self, module_name: str) -> bool:
        """Check if module can be imported."""
        try:
            # Skip relative imports and known system modules
            if module_name.startswith('.') or module_name in ['os', 'sys', 'json', 'time', 'datetime']:
                return True
            
            __import__(module_name)
            return True
        except ImportError:
            return False
        except Exception:
            return True  # Assume available if other error
    
    def _check_runtime_issues(self, file_path: Path) -> List[Dict[str, Any]]:
        """Check for potential runtime issues."""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                # Check for bare except clauses
                if isinstance(node, ast.ExceptHandler) and node.type is None:
                    issues.append({
                        "file": str(file_path),
                        "line": node.lineno,
                        "type": "bare_except",
                        "message": "Bare except clause found",
                        "severity": "warning"
                    })
                
                # Check for TODO/FIXME comments
                if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                    if isinstance(node.value.value, str):
                        value = node.value.value.upper()
                        if 'TODO' in value or 'FIXME' in value:
                            issues.append({
                                "file": str(file_path),
                                "line": node.lineno,
                                "type": "todo",
                                "message": "TODO/FIXME comment found",
                                "severity": "info"
                            })
        
        except Exception:
            pass
        
        return issues
    
    def _generate_recommendations(self, syntax_errors: List, import_errors: List, runtime_issues: List) -> List[str]:
        """Generate recommendations based on found errors."""
        recommendations = []
        
        if syntax_errors:
            recommendations.append(f"🔧 Fix {len(syntax_errors)} syntax errors found in the code")
            recommendations.append("💡 Use an IDE with syntax highlighting to catch errors early")
        
        if import_errors:
            recommendations.append(f"📦 Resolve {len(import_errors)} import issues")
            recommendations.append("💡 Check requirements.txt and install missing dependencies")
        
        if len(runtime_issues) > 5:
            recommendations.append("🧹 Address runtime issues like bare except clauses")
            recommendations.append("💡 Use specific exception handling and add proper logging")
        
        if not recommendations:
            recommendations.append("✅ No critical errors found - great job!")
        
        return recommendations