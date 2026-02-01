import argparse
import logging
import sys
import os
import shutil

# Ensure we can import core modules
sys.path.insert(0, os.getcwd())

from core.code_graph.builder import CodeGraphBuilder
from core.code_graph.tool import CodeGraphTool
from agentfoundry.kgraph.providers.duckdb_sqlite.duck_graph import DuckSqliteGraph
from agentfoundry.utils.config import Config

# Configure logging to stdout for CLI usage
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("code_graph_cli")

def get_kgraph_path():
    config = Config()
    data_dir = config.get("DATA_DIR", "~/.config/agentfoundry/data")
    return os.path.expanduser(data_dir)

def cmd_build(args):
    """Builds or updates the code graph."""
    logger.info(f"Scanning project from: {args.path}")
    builder = CodeGraphBuilder(project_root=args.path)
    builder.build_graph()
    logger.info("Build complete.")

def cmd_clean(args):
    """Removes the persistent graph database."""
    path = get_kgraph_path()
    db_file = os.path.join(path, "kgraph.duckdb")
    
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
            logger.info(f"Deleted graph database at: {db_file}")
            
            # Also clean up vector store persistence if possible/needed?
            # Usually vector stores are in a separate dir.
            # Assuming 'chromadb' or similar subfolder.
            chroma_dir = os.path.join(path, "..", "chromadb") # Approximation based on defaults
            if os.path.exists(chroma_dir):
                 # We might not want to delete the whole vector store as it might have other memories
                 logger.warning(f"Note: Vector store at {chroma_dir} was NOT deleted. Semantic search might have stale embeddings.")
                 
        except Exception as e:
            logger.error(f"Failed to delete database: {e}")
    else:
        logger.info("No graph database found to clean.")

def cmd_search(args):
    """Performs a semantic search on the graph."""
    tool = CodeGraphTool()
    logger.info(f"Searching for: '{args.query}'")
    result = tool.search_codebase(args.query)
    print("\n" + "="*60)
    print(result)
    print("="*60 + "\n")

def cmd_inspect(args):
    """Inspects a specific node by ID to see its code snippet."""
    # We can reuse the search tool logic but filter by exact ID?
    # Or just use the search tool which prints snippets.
    # But let's try to find exact match.
    
    # Since our tool doesn't have a direct 'get_by_id' that returns snippets (limitation discussed),
    # we will simulate it by searching for the exact ID string which is usually unique enough.
    
    tool = CodeGraphTool()
    logger.info(f"Inspecting symbol: '{args.id}'")
    
    # We query the vector store directly here for precision
    vs = tool.kgraph.vector_store
    
    # Search for the exact subject ID in the text?
    # Actually, let's just search for it.
    results = vs.similarity_search_with_score(args.id, k=1, filter={"global": "true"})
    
    if results:
        doc, score = results[0]
        try:
            subj, pred, obj = doc.page_content.split("|", 2)
            if subj == args.id:
                print(f"\n--- Node: {subj} ---")
                print(f"Type: {doc.metadata.get('type')}")
                print(f"Location: {doc.metadata.get('file_path')}:{doc.metadata.get('start_line')}")
                print("\nCode Content:")
                print(doc.metadata.get('code_content', '(No content)'))
                return
        except:
            pass
            
    print("Node not found or no exact match in vector store.")

def main():
    parser = argparse.ArgumentParser(description="QuantumDrive Code Graph CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Build Command
    build_parser = subparsers.add_parser("build", help="Scan code and rebuild graph")
    build_parser.add_argument("--path", default=".", help="Project root directory (default: current)")

    # Clean Command
    subparsers.add_parser("clean", help="Delete the existing graph database")

    # Search Command
    search_parser = subparsers.add_parser("search", help="Semantic search for code entities")
    search_parser.add_argument("query", help="Natural language query string")

    # Inspect Command
    inspect_parser = subparsers.add_parser("inspect", help="Inspect a specific node ID")
    inspect_parser.add_argument("id", help="Node ID (e.g. 'core/ai/q_assistant.py::QAssistant')")

    args = parser.parse_args()

    if args.command == "build":
        cmd_build(args)
    elif args.command == "clean":
        cmd_clean(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "inspect":
        cmd_inspect(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
