import os
import uuid
from mcp.server.fastmcp import FastMCP
# Create an MCP server
mcp = FastMCP("Demo", json_response=True)

import sys
from pathlib import Path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from backend.qdrant import create_collection
from backend.embedding import get_embedding
from backend.chunking import get_chunks
from backend.qdrant import insert_collection , search_collection

def get_info():
    input_data = {}
    pdf_dir = "data/documents/"
    pdf_files = [
        pdf_dir+f for f in os.listdir(pdf_dir)
        if f.lower().endswith(".pdf")
    ]
    input_data["files"] = pdf_files
    return input_data

@mcp.tool()
def handle_upload(input):

    chunks = get_chunks(input["files"])
    vectors = [get_embedding(doc.page_content) for doc in chunks]

    insert_collection(
        ids=[str(uuid.uuid4()) for _ in vectors],
        payload=[{"text": doc.page_content} for doc in chunks],
        vectors=vectors
    )

    return {"status": f"Uploaded {len(chunks)} chunks from {len(input['files'])} files"}

@mcp.tool(
    name="search_docs",
    description="Search the uploaded documents using semantic search and return the most relevant passages."
)
def handle_search(query: str) -> list[str]:
    """
        Search uploaded documents for information relevant to the user's question.

        Args:
            query: Natural language search query.

        Returns:
            List of matching document chunks.
    """
    query_vector = get_embedding(query)
    results = search_collection(query_vector)
    print(f"Search results: {results}")
    return results["results"]

create_collection()

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
