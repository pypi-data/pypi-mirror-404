import ast
import os
from typing import List, Tuple, Optional
import logging

from core.code_graph.models import CodeNode, FileNode, ClassNode, FunctionNode, ImportNode, CodeEdge

logger = logging.getLogger(__name__)

class CodeScanner:
    """
    Scans Python files using AST to extract code structure and relationships.
    """

    def scan_file(self, file_path: str, root_dir: str) -> Tuple[FileNode, List[CodeNode], List[CodeEdge]]:
        """
        Scans a single Python file and returns the file node, all contained nodes (classes, functions),
        and the edges connecting them.
        
        Args:
            file_path: Absolute path to the file.
            root_dir: The root directory of the project (to calculate relative paths).

        Returns:
            Tuple containing:
            - The main FileNode
            - A list of all child nodes (classes, functions, imports)
            - A list of edges representing relationships (CONTAINS, IMPORTS, INHERITS)
        """
        rel_path = os.path.relpath(file_path, root_dir)
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source_code = f.read()
            
            tree = ast.parse(source_code)
        except Exception as e:
            logger.error(f"Failed to parse {rel_path}: {e}")
            return FileNode(id=rel_path, name=os.path.basename(file_path), file_path=rel_path), [], []

        file_node = FileNode(
            id=rel_path,
            name=os.path.basename(file_path),
            file_path=rel_path,
            code_content=source_code, # Store content for file node? Maybe too large. AST nodes will have snippets.
            docstring=ast.get_docstring(tree)
        )
        
        nodes: List[CodeNode] = []
        edges: List[CodeEdge] = []
        
        # We need to track the current scope (File -> Class -> Method) to create FQNs
        # But for simplicity, we can just link children to their direct parent.
        
        self._visit_node(tree, file_node, nodes, edges, rel_path, source_code)
        
        return file_node, nodes, edges

    def _visit_node(self, 
                    parent_ast_node: ast.AST, 
                    parent_graph_node: CodeNode, 
                    nodes: List[CodeNode], 
                    edges: List[CodeEdge], 
                    file_path: str,
                    source_code: str):
        
        for item in ast.iter_fields(parent_ast_node):
            field_name, field_value = item
            if isinstance(field_value, list):
                for sub_node in field_value:
                    if isinstance(sub_node, ast.AST):
                        self._process_ast_node(sub_node, parent_graph_node, nodes, edges, file_path, source_code)
            elif isinstance(field_value, ast.AST):
                self._process_ast_node(field_value, parent_graph_node, nodes, edges, file_path, source_code)

    def _process_ast_node(self, 
                          ast_node: ast.AST, 
                          parent_graph_node: CodeNode, 
                          nodes: List[CodeNode], 
                          edges: List[CodeEdge], 
                          file_path: str,
                          source_code: str):
        
        if isinstance(ast_node, (ast.Import, ast.ImportFrom)):
            self._handle_import(ast_node, parent_graph_node, nodes, edges, file_path)
            
        elif isinstance(ast_node, ast.ClassDef):
            class_node = self._handle_class(ast_node, parent_graph_node, nodes, edges, file_path, source_code)
            # Recurse into the class body
            self._visit_node(ast_node, class_node, nodes, edges, file_path, source_code)
            
        elif isinstance(ast_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_node = self._handle_function(ast_node, parent_graph_node, nodes, edges, file_path, source_code)
            # We treat functions as leaves for now, unless we want to track nested functions or calls.
            # Recurse to find calls? Or inner functions? Let's recurse for inner functions.
            self._visit_node(ast_node, func_node, nodes, edges, file_path, source_code)

    def _handle_import(self, node: ast.AST, parent: CodeNode, nodes: List[CodeNode], edges: List[CodeEdge], file_path: str):
        if isinstance(node, ast.Import):
            for alias in node.names:
                import_node = ImportNode(
                    id=f"{file_path}:import:{alias.name}", # Simple unique ID
                    node_type="import",
                    name=alias.name,
                    file_path=file_path,
                    start_line=node.lineno,
                    end_line=node.end_lineno,
                    module=alias.name,
                    name_as=alias.asname
                )
                nodes.append(import_node)
                edges.append(CodeEdge(source_id=parent.id, target_id=import_node.id, edge_type="IMPORTS"))
                
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                full_name = f"{module}.{alias.name}" if module else alias.name
                import_node = ImportNode(
                    id=f"{file_path}:import:{full_name}",
                    node_type="import",
                    name=alias.name,
                    file_path=file_path,
                    start_line=node.lineno,
                    end_line=node.end_lineno,
                    module=module,
                    imported_name=alias.name,
                    name_as=alias.asname,
                    is_from_import=True
                )
                nodes.append(import_node)
                edges.append(CodeEdge(source_id=parent.id, target_id=import_node.id, edge_type="IMPORTS"))

    def _handle_class(self, node: ast.ClassDef, parent: CodeNode, nodes: List[CodeNode], edges: List[CodeEdge], file_path: str, source_code: str) -> ClassNode:
        # Construct ID. If parent is a class, nested class. If parent is file, top-level.
        # But parent.id is 'file_path'. Let's use FQNs if possible? 
        # For simplicity: file_path::ClassName
        
        node_id = f"{parent.id}::{node.name}"
        
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                # e.g. module.Class
                bases.append(f"{base.value.id}.{base.attr}" if isinstance(base.value, ast.Name) else "complex_base")
            else:
                bases.append("unknown_base")

        code_snippet = self._extract_code(node, source_code)

        class_node = ClassNode(
            id=node_id,
            name=node.name,
            file_path=file_path,
            start_line=node.lineno,
            end_line=node.end_lineno,
            docstring=ast.get_docstring(node),
            bases=bases,
            code_content=code_snippet
        )
        
        nodes.append(class_node)
        edges.append(CodeEdge(source_id=parent.id, target_id=node_id, edge_type="CONTAINS"))
        
        # Add INHERITS edges? These are logical, not containment. 
        # We can create edges to string names, but they won't resolve to IDs yet.
        # Let's just store bases as property for now, resolution happens in graph builder.
        
        return class_node

    def _handle_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, parent: CodeNode, nodes: List[CodeNode], edges: List[CodeEdge], file_path: str, source_code: str) -> FunctionNode:
        
        node_id = f"{parent.id}::{node.name}"
        
        # Extract args
        args_dict = {}
        for arg in node.args.args:
            annotation = None
            if arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    annotation = arg.annotation.id
                elif isinstance(arg.annotation, ast.Constant):
                    annotation = str(arg.annotation.value)
                else:
                    annotation = "complex_type" # Simplify for now
            args_dict[arg.arg] = annotation or "Any"

        returns = None
        if node.returns:
             if isinstance(node.returns, ast.Name):
                returns = node.returns.id
             elif isinstance(node.returns, ast.Constant):
                returns = str(node.returns.value)
             else:
                returns = "complex_return"

        code_snippet = self._extract_code(node, source_code)

        func_node = FunctionNode(
            id=node_id,
            name=node.name,
            file_path=file_path,
            start_line=node.lineno,
            end_line=node.end_lineno,
            docstring=ast.get_docstring(node),
            parameters=args_dict,
            returns=returns,
            code_content=code_snippet
        )
        
        nodes.append(func_node)
        edges.append(CodeEdge(source_id=parent.id, target_id=node_id, edge_type="CONTAINS"))
        
        return func_node

    def _extract_code(self, node: ast.AST, source: str) -> str:
        """Extracts the exact source code for the node based on line numbers."""
        lines = source.splitlines()
        # line numbers are 1-based, list is 0-based
        if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
            # This is a rough extraction, indentation might be preserved
            start = node.lineno - 1
            end = node.end_lineno
            return "\n".join(lines[start:end])
        return ""
