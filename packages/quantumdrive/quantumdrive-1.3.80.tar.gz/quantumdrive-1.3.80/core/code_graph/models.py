from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass(kw_only=True)
class CodeNode:
    id: str  # Unique identifier (e.g., file_path, FQN for class/function)
    node_type: str  # e.g., "file", "class", "function", "import"
    name: str  # Name of the entity
    file_path: str
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    docstring: Optional[str] = None
    code_content: Optional[str] = None # The actual source code of this node

@dataclass(kw_only=True)
class FileNode(CodeNode):
    node_type: str = field(default="file")
    imports: List[str] = field(default_factory=list) # List of modules imported

@dataclass(kw_only=True)
class ClassNode(CodeNode):
    node_type: str = field(default="class")
    methods: List[str] = field(default_factory=list) # List of method names
    bases: List[str] = field(default_factory=list) # Base classes (inheritance)

@dataclass(kw_only=True)
class FunctionNode(CodeNode):
    node_type: str = field(default="function")
    signature: Optional[str] = None # Full signature string
    parameters: Dict[str, str] = field(default_factory=dict) # Param name -> type/default
    returns: Optional[str] = None # Return type annotation

@dataclass(kw_only=True)
class ImportNode(CodeNode):
    node_type: str = field(default="import")
    module: str  # e.g., "os", "core.ai.q_assistant"
    name_as: Optional[str] = None # e.g., "qa" for "import q_assistant as qa"
    is_from_import: bool = False # True for "from module import name"
    imported_name: Optional[str] = None # The specific name imported (for from imports)

@dataclass(kw_only=True)
class CodeEdge:
    source_id: str
    target_id: str
    edge_type: str # e.g., "CONTAINS", "IMPORTS", "CALLS", "INHERITS"
    metadata: Dict = field(default_factory=dict) # e.g., line number of import/call
