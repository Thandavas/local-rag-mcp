import asyncio
import os
import json
from pathlib import Path
from typing import List
from fastapi import FastAPI, Request , UploadFile, File
from fastapi.responses import HTMLResponse, StreamingResponse
from dotenv import load_dotenv
from google import genai
from google.genai import types
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

load_dotenv()
app = FastAPI()

# Standard google-genai client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def mcp_tool_to_gemini(tool):
    schema = tool.inputSchema or {"type": "object", "properties": {}}
    return types.FunctionDeclaration(
        name=tool.name,
        description=tool.description or "",
        parameters=schema,
    )

async def run_gemini_mcp_loop(user_query: str):
    """
    Connects to the MCP server, initializes the Gemini loop, 
    and yields real-time updates back to the UI.
    """
    async with streamable_http_client("http://localhost:8000/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. Fetch and convert MCP tools
            mcp_tools = (await session.list_tools()).tools
            gemini_tool = types.Tool(
                function_declarations=[mcp_tool_to_gemini(t) for t in mcp_tools]
            )

            # 2. Setup initial history state
            contents = [types.Content(role="user", parts=[
                types.Part.from_text(text=user_query)
            ])]

            while True:
                response = await client.aio.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=contents,
                    config=types.GenerateContentConfig(tools=[gemini_tool]),
                )
                
                function_calls = response.function_calls
                
                if not function_calls:
                    # Final answer reached. Send it and exit the loop.
                    yield f"data: {json.dumps({'type': 'final', 'content': response.text})}\n\n"
                    break
                
                # Append the model's intent to history
                contents.append(response.candidates[0].content)
                
                tool_response_parts = []
                for function_call in function_calls:
                    # Notify the UI that a tool execution is happening
                    status_msg = f"Running tool '{function_call.name}'..."
                    yield f"data: {json.dumps({'type': 'status', 'content': status_msg})}\n\n"
                    
                    try:
                        args_dict = dict(function_call.args)
                        mcp_result = await session.call_tool(function_call.name, arguments=args_dict)
                        
                        if hasattr(mcp_result, 'content'):
                            result_text = "\n".join([block.text for block in mcp_result.content if hasattr(block, 'text')])
                        else:
                            result_text = str(mcp_result)
                            
                    except Exception as e:
                        result_text = f"Error: {str(e)}"
                    
                    tool_response_parts.append(
                        types.Part.from_function_response(
                            name=function_call.name,
                            response={"result": result_text}
                        )
                    )
                
                # Send tool data back to Gemini
                contents.append(types.Content(role="user", parts=tool_response_parts))

@app.get("/chat/stream")
async def chat_stream(q: str):
    """Exposes an endpoint that streams Server-Sent Events (SSE)."""
    return StreamingResponse(run_gemini_mcp_loop(q), media_type="text/event-stream")

BASE_DIR = Path(__file__).resolve().parent.parent
@app.get("/", response_class=HTMLResponse)
async def index():
    """Serves the single-page chat application layout safely using absolute paths."""
    # This looks for index.html inside the exact same directory as app.py
    html_path = os.path.join(BASE_DIR, "ui\index.html")
    
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse(
            status_code=404,
            content=f"<h3>Configuration Error</h3><p>Could not find 'index.html' at: <code>{html_path}</code>. Please ensure it is placed in the same folder as app.py.</p>"
        )
    
@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    UPLOAD_DIR = os.path.join(BASE_DIR, "data\documents\\")
    saved_files = []
    
    for file in files:
        # 1. Clean the filename to prevent directory traversal attacks
        filename = os.path.basename(file.filename)
        file_path = UPLOAD_DIR+filename
        
        # 2. Write the file stream chunk by chunk to save memory
        with open(file_path, "wb") as buffer:
            # chunk_size=1024*1024 reads 1MB at a time (great for large files)
            while content := await file.read(1024 * 1024):
                buffer.write(content)
                
        #print(f"Saved file to local storage: {file_path}")
        saved_files.append(filename)

        # 3. (Optional) Pass the local file path to your MCP tool instead of raw bytes
        # await session.call_tool("upload_document", arguments={"name": filename, "path": str(file_path)})

    return {
        "status": "success", 
        "count": len(files),
        "saved_files": saved_files
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="0.0.0.0", port=3000, reload=True)