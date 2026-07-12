import os
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
        ids=list(range(len(vectors))),
        payload=[{"text": doc.page_content} for doc in chunks],
        vectors=vectors
    )

    return {"status": f"Uploaded {len(chunks)} chunks from {len(input['files'])} files"}

@mcp.tool()
def handle_search(msg):
    query_vector = get_embedding(msg)
    results = search_collection(query_vector)
    print(f"Search results: {results}")
    return results["results"]

create_collection()
# inputs = get_info()
# handle_upload(inputs)

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
