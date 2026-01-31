"""
Dukpyra Semantic Analyzer - Validation and Error Checking

This module validates the AST before code generation, catching errors like:
- Path parameters not matching function parameters
- Undefined variable references
- Duplicate class or endpoint definitions
- Invalid type hints

Architecture:
    Source → Lexer → Parser → AST → Analyzer → CodeGen → C#
                                    ^^^^^^^^^^
                                    This module
"""

from dataclasses import dataclass, field
from typing import List, Set, Dict, Optional
import re

from .ast import (
    ProgramNode,
    ClassDefNode,
    ClassPropertyNode,
    EndpointNode,
    DecoratorNode,
    FunctionDefNode,
    ParameterNode,
    ExpressionNode,
    StringExpr,
    NumberExpr,
    BoolExpr,
    NoneExpr,
    IdentifierExpr,
    MemberAccessExpr,
    DictExpr,
    DictItemNode,
    ListExpr,
    GenericEndpointNode,
    ListCompNode,
    BinaryOpExpr,
)


# ==============================================================================
# Error and Warning Types
# ==============================================================================

@dataclass
class SemanticError:
    """
    Represents a semantic error that prevents compilation.
    
    Example:
        SemanticError(
            message="Path parameter 'user_id' not found in function parameters",
            line=10,
            code="E001"
        )
    """
    message: str
    line: int = 0
    code: str = "E000"
    
    def __str__(self) -> str:
        return f"Error {self.code} (line {self.line}): {self.message}"


@dataclass
class SemanticWarning:
    """
    Represents a warning that doesn't prevent compilation.
    
    Example:
        SemanticWarning(
            message="Function 'get_user' has unused parameter 'limit'",
            line=15,
            code="W001"
        )
    """
    message: str
    line: int = 0
    code: str = "W000"
    
    def __str__(self) -> str:
        return f"Warning {self.code} (line {self.line}): {self.message}"


@dataclass
class AnalysisResult:
    """Result of semantic analysis."""
    errors: List[SemanticError] = field(default_factory=list)
    warnings: List[SemanticWarning] = field(default_factory=list)
    
    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    @property
    def is_valid(self) -> bool:
        return not self.has_errors


# ==============================================================================
# Symbol Table
# ==============================================================================

@dataclass
class SymbolTable:
    """
    Tracks all named entities in the program.
    
    - classes: Map of class name -> ClassDefNode
    - endpoints: Map of "METHOD /path" -> EndpointNode
    - builtin_types: Set of valid type hint names
    """
    classes: Dict[str, ClassDefNode] = field(default_factory=dict)
    endpoints: Dict[str, EndpointNode] = field(default_factory=dict)
    builtin_types: Set[str] = field(default_factory=lambda: {"int", "str", "float", "bool", "list", "dict"})


# ==============================================================================
# Semantic Analyzer
# ==============================================================================

class SemanticAnalyzer:
    """
    Validates AST and catches semantic errors before code generation.
    
    Usage:
        analyzer = SemanticAnalyzer()
        result = analyzer.analyze(ast)
        if result.has_errors:
            for error in result.errors:
                print(error)
    """
    
    def __init__(self):
        self.symbols = SymbolTable()
        self.errors: List[SemanticError] = []
        self.warnings: List[SemanticWarning] = []
    
    def analyze(self, program: ProgramNode) -> AnalysisResult:
        """
        Perform semantic analysis on the entire program.
        
        Steps:
        1. Build symbol table (collect all definitions)
        2. Validate classes
        3. Validate endpoints
        """
        if program is None:
            return AnalysisResult()
        
        # Reset state
        self.symbols = SymbolTable()
        self.errors = []
        self.warnings = []
        
        # Phase 1: Build symbol table
        self._collect_classes(program.classes)
        self._collect_endpoints(program.endpoints)
        
        # Phase 2: Validate
        self._validate_classes(program.classes)
        self._validate_endpoints(program.endpoints)
        
        return AnalysisResult(
            errors=self.errors,
            warnings=self.warnings
        )
    
    # ==========================================================================
    # Symbol Collection
    # ==========================================================================
    
    def _collect_classes(self, classes: List[ClassDefNode]) -> None:
        """Collect all class definitions into symbol table."""
        for cls in classes:
            if cls.name in self.symbols.classes:
                self._error(
                    f"Duplicate class definition: '{cls.name}'",
                    cls.lineno,
                    "E001"
                )
            else:
                self.symbols.classes[cls.name] = cls
    
    def _collect_endpoints(self, endpoints: List[GenericEndpointNode]) -> None:
        """Collect all endpoints and check for duplicates."""
        for endpoint in endpoints:
            method = endpoint.method.upper()
            path = endpoint.path
            key = f"{method} {path}"
            
            if key in self.symbols.endpoints:
                self._error(
                    f"Duplicate endpoint: {key}",
                    endpoint.lineno,
                    "E002"
                )
            else:
                self.symbols.endpoints[key] = endpoint
    
    # ==========================================================================
    # Class Validation
    # ==========================================================================
    
    def _validate_classes(self, classes: List[ClassDefNode]) -> None:
        """Validate all class definitions."""
        for cls in classes:
            self._validate_class(cls)
    
    def _validate_class(self, cls: ClassDefNode) -> None:
        """Validate a single class definition."""
        seen_props = set()
        
        for prop in cls.properties:
            # Check for duplicate properties
            if prop.name in seen_props:
                self._error(
                    f"Duplicate property '{prop.name}' in class '{cls.name}'",
                    prop.lineno,
                    "E003"
                )
            seen_props.add(prop.name)
            
            # Check type hint is valid
            if not self._is_valid_type(prop.type_hint):
                self._error(
                    f"Unknown type '{prop.type_hint}' for property '{prop.name}'",
                    prop.lineno,
                    "E004"
                )
    
    # ==========================================================================
    # Endpoint Validation
    # ==========================================================================
    
    def _validate_endpoints(self, endpoints: List[GenericEndpointNode]) -> None:
        """Validate all endpoints."""
        for endpoint in endpoints:
            self._validate_endpoint(endpoint)
    
    def _validate_endpoint(self, endpoint: GenericEndpointNode) -> None:
        """Validate a single endpoint."""
        function = endpoint.handler
        
        # Extract path parameters like {user_id} from path
        path_params = self._extract_path_params(endpoint.path)
        
        # Get function parameter names
        func_params = {p.name for p in function.params}
        
        # Check: all path params must exist in function params
        for path_param in path_params:
            if path_param not in func_params:
                self._error(
                    f"Path parameter '{{{path_param}}}' not found in function '{function.name}'",
                    endpoint.lineno,
                    "E010"
                )
        
        # Validate function parameters
        for param in function.params:
            self._validate_parameter(param, path_params)
        
        # Validate function body references
        if function.body:
            self._validate_expression(function.body, func_params)
    
    def _validate_parameter(self, param: ParameterNode, path_params: Set[str]) -> None:
        """Validate a function parameter."""
        # Check type hint is valid
        if param.type_hint:
            if not self._is_valid_type(param.type_hint):
                self._error(
                    f"Unknown type '{param.type_hint}' for parameter '{param.name}'",
                    param.lineno,
                    "E011"
                )
    
    def _validate_expression(self, expr: ExpressionNode, scope: Set[str]) -> None:
        """Validate expression references."""
        if isinstance(expr, IdentifierExpr):
            if expr.name not in scope:
                self._error(
                    f"Undefined variable '{expr.name}'",
                    expr.lineno,
                    "E020"
                )
        
        elif isinstance(expr, MemberAccessExpr):
            # Check object exists
            if expr.object_name not in scope:
                self._error(
                    f"Undefined variable '{expr.object_name}'",
                    expr.lineno,
                    "E020"
                )
            # Note: We could also check if member exists on the type
        
        elif isinstance(expr, DictExpr):
            for item in expr.items:
                self._validate_expression(item.value, scope)
        
        elif isinstance(expr, ListExpr):
            for item in expr.items:
                self._validate_expression(item, scope)

        elif isinstance(expr, BinaryOpExpr):
            self._validate_expression(expr.left, scope)
            self._validate_expression(expr.right, scope)

        elif isinstance(expr, ListCompNode):
            # [expr for target in iterable if condition]
            # Validate iterable in CURRENT scope
            self._validate_expression(expr.iterable, scope)
            
            # Create NEW scope for expression and condition (includes target)
            inner_scope = scope.copy()
            inner_scope.add(expr.target)
            
            self._validate_expression(expr.expression, inner_scope)
            if expr.condition:
                self._validate_expression(expr.condition, inner_scope)
    
    # ==========================================================================
    # Helper Methods
    # ==========================================================================
    
    def _extract_path_params(self, path: str) -> Set[str]:
        """
        Extract path parameters from URL path.
        
        Example: "/users/{user_id}/posts/{post_id}" -> {"user_id", "post_id"}
        """
        pattern = r'\{([^}]+)\}'
        matches = re.findall(pattern, path)
        return set(matches)
    
    def _is_valid_type(self, type_hint: str) -> bool:
        """Check if a type hint is valid (builtin or defined class)."""
        if type_hint in self.symbols.builtin_types:
            return True
        if type_hint in self.symbols.classes:
            return True
        return False
    
    def _error(self, message: str, line: int, code: str) -> None:
        """Add a semantic error."""
        self.errors.append(SemanticError(message=message, line=line, code=code))
    
    def _warning(self, message: str, line: int, code: str) -> None:
        """Add a semantic warning."""
        self.warnings.append(SemanticWarning(message=message, line=line, code=code))


# ==============================================================================
# Convenience Function
# ==============================================================================

def analyze(program: ProgramNode) -> AnalysisResult:
    """
    Convenience function to analyze an AST.
    
    Usage:
        from dukpyra.analyzer import analyze
        result = analyze(ast)
    """
    analyzer = SemanticAnalyzer()
    return analyzer.analyze(program)
