"""
Dukpyra Code Generator - AST to C# Transpiler

This module walks the AST and generates C# code for ASP.NET Core Minimal API.
It uses Jinja2 templates for the final code output.

Architecture:
    Source Code → Lexer → Parser → AST → CodeGen → C# Code (via Templates)
"""

import json
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from .ast import (
    Node,
    ProgramNode,
    ImportNode,
    AppCreationNode,
    ClassDefNode,
    ClassPropertyNode,
    ClassPropertyNode,
    GenericEndpointNode,
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
    ListCompNode,
    BinaryOpExpr,
)

class CSharpCodeGenerator:
    """
    Generates C# ASP.NET Core Minimal API code from Dukpyra AST.
    
    Uses the Visitor pattern to prepare data for Jinja2 templates.
    """
    
    def __init__(self):
        # Setup Jinja2 environment
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.template = self.env.get_template('Program.cs.j2')
        
        # Load Runtime Types if available
        self.collected_types = {}
        types_path = Path(".dukpyra/types.json")
        if types_path.exists():
            try:
                with open(types_path, "r") as f:
                    self.collected_types = json.load(f)
            except Exception:
                pass # Ignore load errors

    def generate(self, program: ProgramNode) -> str:
        # ... (same as before) ...
        """
        Generate complete C# code from a ProgramNode.
        
        Returns a complete Program.cs file content.
        """
        if program is None:
            return ""
        
        # Prepare data for template
        classes = [self.visit_class(c) for c in program.classes]
        endpoints = [self.visit_endpoint(e) for e in program.endpoints]
        
        # Render template
        return self.template.render(
            classes=classes,
            endpoints=endpoints
        )
    
    def visit_class(self, node: ClassDefNode) -> str:
        # ... (same as before) ...
        """
        Generate C# record type definition string.
        """
        params = []
        for prop in node.properties:
            csharp_type = self.python_type_to_csharp(prop.type_hint)
            params.append(f"{csharp_type} {prop.name}")
        
        params_str = ", ".join(params)
        return f"public record {node.name}({params_str});"

    def visit_endpoint(self, node: GenericEndpointNode) -> Dict[str, str]:
        """
        Prepare endpoint data for template.
        Works with GenericEndpointNode now, decoupled from decorators.
        """
        method = node.method.capitalize()
        path = node.path
        
        # Pass function name to visit_params to lookup types
        params = self.visit_params(node.handler.params, func_name=node.handler.name)
        
        # In generic node, raw_csharp would need a different mechanism
        # For now we assume standard body generation
        body = self.visit_function_body(node.handler)
        
        return {
            "method": method,
            "path": path,
            "params": params,
            "body": body
        }
    
    def visit_params(self, params: list, func_name: str = "") -> str:
        """
        Generate C# lambda parameter list string.
        """
        if not params:
            return ""
        
        param_strs = []
        for param in params:
            csharp_type = self.python_type_to_csharp(param.type_hint)
            
            # If type is dynamic (unknown), try to find it in collected types
            if csharp_type == "dynamic" and func_name in self.collected_types:
                collected = self.collected_types[func_name].get(param.name)
                if collected:
                    csharp_type = self.python_type_to_csharp(collected)

            param_strs.append(f"{csharp_type} {param.name}")
        
        return ", ".join(param_strs)
    
    def python_type_to_csharp(self, python_type: str) -> str:
        """
        Convert Python type hint to C# type.
        """
        type_map = {
            "int": "int",
            "str": "string",
            "float": "double",
            "bool": "bool",
            "list": "List<dynamic>",
            "dict": "Dictionary<string, dynamic>",
        }
        
        if python_type is None:
            return "dynamic"
        
        return type_map.get(python_type, python_type)
    
    def visit_function_body(self, node: FunctionDefNode) -> str:
        """
        Generate C# code for function body.
        """
        if node.body is None:
            return "return Results.Ok();"
        
        expr = self.visit_expression(node.body)
        return f"return Results.Ok({expr});"
    
    def visit_expression(self, node: ExpressionNode) -> str:
        """
        Dispatch to the appropriate expression visitor.
        """
        if isinstance(node, StringExpr):
            return self.visit_string(node)
        elif isinstance(node, NumberExpr):
            return self.visit_number(node)
        elif isinstance(node, BoolExpr):
            return self.visit_bool(node)
        elif isinstance(node, NoneExpr):
            return self.visit_none(node)
        elif isinstance(node, IdentifierExpr):
            return self.visit_identifier(node)
        elif isinstance(node, MemberAccessExpr):
            return self.visit_member_access(node)
        elif isinstance(node, DictExpr):
            return self.visit_dict(node)
        elif isinstance(node, ListExpr):
            return self.visit_list(node)
        elif isinstance(node, ListCompNode):
            return self.visit_list_comp(node)
        elif isinstance(node, BinaryOpExpr):
            return self.visit_binary_op(node)
        else:
            raise ValueError(f"Unknown expression type: {type(node)}")
    
    def visit_string(self, node: StringExpr) -> str:
        # Escape special characters for C#
        escaped = node.value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    
    def visit_number(self, node: NumberExpr) -> str:
        return str(node.value)
    
    def visit_bool(self, node: BoolExpr) -> str:
        return "true" if node.value else "false"
    
    def visit_none(self, node: NoneExpr) -> str:
        return "(object?)null"
    
    def visit_identifier(self, node: IdentifierExpr) -> str:
        return node.name
    
    def visit_member_access(self, node: MemberAccessExpr) -> str:
        return f"{node.object_name}.{node.member_name}"
    
    def visit_dict(self, node: DictExpr) -> str:
        if not node.items:
            return "new { }"
        
        items = []
        for item in node.items:
            key = item.key
            value = self.visit_expression(item.value)
            items.append(f"{key} = {value}")
        
        return "new { " + ", ".join(items) + " }"
    
    def visit_list(self, node: ListExpr) -> str:
        if not node.items:
            return "Array.Empty<object>()"
        
        items = [self.visit_expression(item) for item in node.items]
        items = [self.visit_expression(item) for item in node.items]
        return "new[] { " + ", ".join(items) + " }"

    def visit_list_comp(self, node: ListCompNode) -> str:
        """
        Generate LINQ expression for list comprehension.
        Python: [expr for target in iterable if condition]
        C#: iterable.Where(target => condition).Select(target => expr).ToList()
        """
        iterable = self.visit_expression(node.iterable)
        target = node.target
        
        # Start LINQ chain
        linq = iterable
        
        # Add .Where(...) if condition exists
        if node.condition:
            condition_expr = self.visit_expression(node.condition)
            linq += f".Where({target} => {condition_expr})"
            
        # Add .Select(...)
        select_expr = self.visit_expression(node.expression)
        linq += f".Select({target} => {select_expr})"
        
        # Finalize
        linq += ".ToList()"
        
        return linq

    def visit_binary_op(self, node: BinaryOpExpr) -> str:
        """
        Generate C# binary operation string.
        """
        left = self.visit_expression(node.left)
        right = self.visit_expression(node.right)
        return f"{left} {node.op} {right}"


def generate_csharp(program: ProgramNode) -> str:
    """
    Convenience function to generate C# code from AST.
    """
    generator = CSharpCodeGenerator()
    return generator.generate(program)
