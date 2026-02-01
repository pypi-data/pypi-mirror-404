import os
import logging
from typing import List

from core.code_graph.scanner import CodeScanner
from core.code_graph.models import CodeNode, FileNode, ClassNode, FunctionNode, ImportNode, CodeEdge
from agentfoundry.kgraph.providers.duckdb_sqlite.duck_graph import DuckSqliteGraph

logger = logging.getLogger(__name__)

class CodeGraphBuilder:
    """
    Orchestrates scanning the codebase and populating the Knowledge Graph.
    """

    def __init__(self, project_root: str, kgraph_path: str = "~/.config/agentfoundry/data"):
        self.project_root = os.path.abspath(project_root)
        self.scanner = CodeScanner()
        # Ensure path is expanded
        expanded_path = os.path.expanduser(kgraph_path)
        self.kgraph = DuckSqliteGraph(persist_path=expanded_path)
        logger.info(f"CodeGraphBuilder initialized. Root: {self.project_root}, KGraph: {expanded_path}")

    def build_graph(self, scan_paths: List[str] = None):
        """
        Scans all python files in the project and updates the Knowledge Graph.
        
        Args:
            scan_paths: Optional list of subdirectories to scan. Defaults to project root.
        """
        logger.info("Starting code graph build...")
        
        target_dirs = [os.path.join(self.project_root, p) for p in scan_paths] if scan_paths else [self.project_root]
        
        count_files = 0
        count_nodes = 0
        
        for target_dir in target_dirs:
            for root, _, files in os.walk(target_dir):
                for file in files:
                    if file.endswith(".py"):
                        file_path = os.path.join(root, file)
                        
                        # Skip virtual environments or hidden folders if needed
                        if ".venv" in file_path or "__pycache__" in file_path:
                            continue

                        self._process_file(file_path)
                        count_files += 1

        logger.info(f"Code graph build complete. Scanned {count_files} files.")

    def _process_file(self, file_path: str):
        """
        Scans a single file and upserts facts to KGraph.
        """
        try:
            file_node, nodes, edges = self.scanner.scan_file(file_path, self.project_root)
            
            # 1. Insert File Node
            self._upsert_node(file_node)
            
            # 2. Insert all Child Nodes (Classes, Functions, Imports)
            for node in nodes:
                self._upsert_node(node)
                
            # 3. Insert Edges
            for edge in edges:
                self._upsert_edge(edge)

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")

    def _upsert_node(self, node: CodeNode):
        """
        Converts a CodeNode into a KGraph Fact (Triple).
        Subject: Node ID
        Predicate: "IS_A"
        Object: Node Type
        Metadata: Full node details (docstring, line numbers, code snippet)
        """
        
        # Prepare metadata for the node
        metadata = {
            "type": node.node_type,
            "name": node.name,
            "file_path": node.file_path,
            "start_line": node.start_line,
            "end_line": node.end_line,
            "docstring": node.docstring or "",
            # We store the snippet in metadata so the agent can read it instantly!
            "code_content": node.code_content or "",
            "global": "true" # Marker for global context
        }
        
        # Specific fields per type
        if isinstance(node, ClassNode):
            metadata["bases"] = node.bases
        elif isinstance(node, FunctionNode):
            metadata["parameters"] = str(node.parameters) # JSON dump?
            metadata["returns"] = str(node.returns)
        
        # Upsert the primary definition fact
        # (core/ai/q_assistant.py, IS_A, file)
        # (core/ai/q_assistant.py::QAssistant, IS_A, class)
        self.kgraph.upsert_fact(
            subject=node.id,
            predicate="IS_A",
            obj=node.node_type,
            metadata=metadata
        )
        
        # Optional: Add searchable text fact for semantic search
        # "QAssistant class in core/ai/q_assistant.py"
        description = f"{node.node_type} {node.name} defined in {node.file_path}"
        if node.docstring:
            description += f": {node.docstring}"
            
        # We can add a secondary fact or just rely on the first one being indexed.
        # The DuckSqliteGraph indexes the triple string. 
        # "core/ai/q_assistant.py::QAssistant|IS_A|class" is not very searchable.
        
        # Let's add a "DESCRIPTION" fact specifically for semantic search
        self.kgraph.upsert_fact(
            subject=node.id,
            predicate="DESCRIPTION",
            obj=description,
            metadata={"global": "true"}
        )


    def _upsert_edge(self, edge: CodeEdge):
        """
        Converts a CodeEdge into a KGraph Fact.
        """
        # (core/ai/q_assistant.py, CONTAINS, core/ai/q_assistant.py::QAssistant)
        
        self.kgraph.upsert_fact(
            subject=edge.source_id,
            predicate=edge.edge_type,
            obj=edge.target_id,
            metadata={"global": "true", **edge.metadata}
        )

if __name__ == "__main__":
    # Simple CLI to run the builder
    import sys
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    project_path = os.getcwd()
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
        
    builder = CodeGraphBuilder(project_path)
    builder.build_graph()
