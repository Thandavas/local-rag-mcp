from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from mcp.client import MCPClient

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow your frontend
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/", StaticFiles(directory="ui", html=True), name="ui")
client = MCPClient(host="localhost", port=8000)  # adjust to your MCP server

@app.post("/chat/upload")
async def upload(files: list[UploadFile] = File(...)):
    input_files = []
    for f in files:
        content = await f.read()
        input_files.append({"filename": f.filename, "content": content.decode("latin1")})
    return client.call_tool("upload_docs", {"files": input_files})

@app.get("/chat/ask")
async def ask(query: str):
    return client.call_tool("search_docs", {"query": query})
