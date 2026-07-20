# local-rag-mcp

A simple local RAG (Retrieval-Augmented Generation) project with an MCP server and a backend UI.

## Quick Start

Follow these steps to get the project running locally:

1. Create a virtual environment
   ```bash
   uv venv .venv
   ```

2. Activate the environment
   ```powershell
   .\.venv\Scripts\activate
   ```

3. Initialize the project dependencies
   ```bash
   uv init
   uv add -r .\requirements.txt
   ```

4. Start the MCP server
   ```bash
   uv run -m mymcp.server
   ```

   After this step, open the project root folder in another command prompt and run the next command:

5. Start the backend app
   ```bash
   uv run -m backend.app
   ```
   This will open the app on `http://localhost:3000`.

## Notes

- Run the commands from the project root folder.
- If you are using PowerShell, the activation command above is the correct one.
- The backend provides the local web interface, while the MCP server handles the retrieval workflow.
