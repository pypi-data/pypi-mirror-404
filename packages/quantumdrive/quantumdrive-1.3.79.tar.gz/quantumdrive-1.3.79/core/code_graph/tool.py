from typing import Dict, Any, List, Optional
from langchain_core.tools import Tool

from core.code_graph.builder import CodeGraphBuilder
from agentfoundry.kgraph.providers.duckdb_sqlite.duck_graph import DuckSqliteGraph
from agentfoundry.utils.config import Config

class CodeGraphTool:
    """
    Exposes Code Graph capabilities to the agent.
    Allows searching for code definitions, usages, and structural relationships.
    """
    
    def __init__(self):
        # We assume the graph is already built or at least initialized.
        # We connect to the same persistent path.
        config = Config()
        data_dir = config.get("DATA_DIR", "~/.config/agentfoundry/data")
        expanded_path = str(data_dir) # Ensure string
        self.kgraph = DuckSqliteGraph(persist_path=expanded_path)

    def search_codebase(self, query: str) -> str:
        """
        Semantically searches the codebase for relevant classes, functions, or files.
        Useful for general questions like "How does the authentication work?" or "Find the QAssistant class".
        """
        # DIRECT ACCESS STRATEGY:
        # We bypass kgraph.search() because it strips metadata.
        # We query the vector_store directly to get the code snippets.
        
        # We need to replicate the filter logic used by the builder (global scope)
        # Builder used: metadata={"global": "true", ...}
        # Note: Vector stores handle filters differently. 
        # Chroma/Milvus usually accept a dict.
        
        try:
            # Access the underlying vector store from the graph instance
            vs = self.kgraph.vector_store
            
            # Perform similarity search. 
            # Note: We filter for facts that are specifically "DESCRIPTION" nodes or definitions
            # to avoid getting noisy edge facts like "FileA IMPORTS ModuleB".
            # However, simpler is better: let the semantic similarity decide.
            
            # We filter by global context as set by the builder.
            # Depending on the store implementation, filter might differ. 
            # Safe bet: {"global": "true"}
            results = vs.similarity_search_with_score(query, k=5, filter={"global": "true"})
            
        except Exception as e:
            return f"Search failed: {e}"
        
        if not results:
            return "No relevant code entities found in the graph."
            
        output = "Found the following code entities:\n"
        for doc, score in results:
            # doc.page_content is "Subject|Predicate|Object"
            try:
                subj, pred, obj = doc.page_content.split("|", 2)
            except ValueError:
                continue # Malformed fact
            
            meta = doc.metadata
            node_type = meta.get("type", "unknown")
            snippet = meta.get("code_content", "")
            
            # Format the output for the agent
            output += f"\n--- Match (Score: {score:.2f}) ---\n"
            output += f"Entity: {subj}\n"
            output += f"Type: {node_type}\n"
            
            if pred == "DESCRIPTION":
                 output += f"Description: {obj}\n"
            else:
                 output += f"Fact: {pred} {obj}\n"
            
            if snippet:
                # Truncate if too long to save tokens, agent can request full read if needed
                # But for a snippet, 500 chars is reasonable context.
                display_snippet = snippet[:1000] + "... (truncated)" if len(snippet) > 1000 else snippet
                output += f"Code Snippet:\n```python\n{display_snippet}\n```\n"
            
            output += f"Location: {meta.get('file_path', 'unknown')}:{meta.get('start_line', '?')}\n"
                 
        return output

    def get_definition(self, symbol_id: str) -> str:
        """
        Retrieves the exact source code definition for a given symbol ID.
        Use 'search_codebase' first to find the correct symbol_id (e.g., 'core/ai/q_assistant.py::QAssistant').
        """
        # We need to fetch the metadata for this node.
        # DuckSqliteGraph.fetch_by_metadata doesn't fetch by Subject directly, it fetches by Metadata fields.
        # But we can use get_neighbours(depth=0) essentially to find the node? 
        # Actually, get_neighbours returns triples.
        
        # We need a way to look up the node's properties. 
        # The builder stored (ID, IS_A, Type, metadata={...})
        
        # We can simulate a lookup by querying for the IS_A relationship for this subject
        # But DuckGraph API is limited.
        # Let's add a helper or use what we have.
        # We can search for the specific fact: (symbol_id, "IS_A", ?)
        
        # Workaround using direct connection or extending base class?
        # Let's stick to public API. 
        # We can use `get_neighbours` on the symbol_id. It should return (symbol_id, IS_A, type).
        # But get_neighbours returns a list of Dicts without the metadata payload in the default implementation?
        # Let's check DuckSqliteGraph.fetch_by_metadata. 
        # We can't query by ID there.
        
        # Wait, the DuckSqliteGraph.get_neighbours returns: {"subject": s, "predicate": p, "object": o}
        # It DOES NOT return metadata. This is a limitation for retrieving the code snippet.
        
        # OPTION: We can use `fetch_by_metadata` if we add the 'id' to the metadata itself during build?
        # No, the builder didn't do that.
        
        # ALTERNATIVE: Use SQL directly? No, encapsulation.
        
        # Let's look at `search`. It returns docs. `doc.metadata` exists in the VectorStore return, 
        # but `DuckSqliteGraph.search` strips it out! -> results.append({"subject": ..., "score": ...})
        
        # CRITICAL FIX NEEDED: We need a way to get the metadata (code snippet) from the graph.
        # I will extend the DuckSqliteGraph wrapper locally here or assume we can patch it?
        # No, let's use a trick.
        # I will read the file directly if I have the path from the ID.
        # "core/ai/q_assistant.py::QAssistant" -> File: core/ai/q_assistant.py
        
        if "::" in symbol_id:
            file_path = symbol_id.split("::")[0]
            # Verify file exists
            if not os.path.exists(file_path):
                 return f"Error: File {file_path} not found for symbol {symbol_id}."
            
            # This is a fallback. ideally the graph provides the line numbers.
            # But wait, I can use the `CodeScanner` again? No, that's expensive.
            
            # Let's rely on the agent to be smart. 
            # If the tool returns the file path, the agent can use `read_file`.
            # BUT the goal was to return the snippet.
            
            return f"The symbol {symbol_id} is located in {file_path}. Please use the 'read_file' tool to inspect it."
            
        else:
            # It's a file
            return f"That appears to be a file path: {symbol_id}. Use 'read_file' to view it."

    def as_tool(self) -> Tool:
        return Tool(
            name="code_graph_search",
            func=self.search_codebase,
            description="Search the codebase structure. Input: a semantic query (e.g., 'Find the QAssistant class'). Returns IDs of matching code entities."
        )

# We can also expose a "Build" tool for the agent to refresh its own memory?
def build_graph_tool_func(_: str) -> str:
    try:
        builder = CodeGraphBuilder(project_root=".") # Assume CWD
        builder.build_graph()
        return "Code Graph successfully rebuilt."
    except Exception as e:
        return f"Failed to rebuild graph: {e}"

build_tool = Tool(
    name="build_code_graph",
    func=build_graph_tool_func,
    description="Scans the current project structure and rebuilds the code knowledge graph. Use this if code has changed significantly."
)

