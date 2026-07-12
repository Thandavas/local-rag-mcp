# local-rag-mcp
uv venv .venv 
.\.venv\Scripts\activate
uv init  
uv add -r .\requirements.txt
uv run -m mymcp.server   
