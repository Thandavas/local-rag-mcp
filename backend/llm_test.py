import asyncio, os, json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def mcp_tool_to_gemini(tool):
    schema = tool.inputSchema or {"type": "object", "properties": {}}
    return types.FunctionDeclaration(
        name=tool.name,
        description=tool.description or "",
        parameters=schema,
    )

async def main():
    async with streamable_http_client("http://localhost:8000/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            mcp_tools = (await session.list_tools()).tools
            gemini_tool = types.Tool(
                function_declarations=[mcp_tool_to_gemini(t) for t in mcp_tools]
            )

            contents = [types.Content(role="user", parts=[
                types.Part(text="What does the document say about ISTQB?")
            ])]

            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=types.GenerateContentConfig(tools=[gemini_tool]),
            )
            function_calls = response.function_calls
                
            if not function_calls:
                # No more function calls, we have the final answer!
                print("\n--- Final Answer ---")
                print(response.text)

            tool_response_parts = []
            for function_call in function_calls:
                print(f" Gemini requested tool: {function_call.name} with args: {function_call.args}")
                    
                try:
                    # Execute the tool via your MCP session
                    # convert args from Gemini's map structure to a standard dict
                    args_dict = dict(function_call.args)
                    mcp_result = await session.call_tool(function_call.name, arguments=args_dict)
                        
                    # Extract the text content from the MCP tool result
                    # Most MCP tools return a list of content blocks
                    result_text = ""
                    if hasattr(mcp_result, 'content'):
                        result_text = "\n".join([block.text for block in mcp_result.content if hasattr(block, 'text')])
                    else:
                        result_text = str(mcp_result)
                            
                except Exception as e:
                    print(f"❌ Error executing tool {function_call.name}: {e}")
                    result_text = f"Error: {str(e)}"

                tool_response_parts.append(
                            types.Part.from_function_response(
                                name=function_call.name,
                                response={"result": result_text}
                            )
                        )
            contents.append(types.Content(role="user", parts=tool_response_parts))
            # print("\n--- Tool Results ---")
            # print(tool_response_parts)
            print("Sending tool results back to Gemini...")
            final = await client.aio.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=contents,
                    config=types.GenerateContentConfig(tools=[gemini_tool]),
                )
            print(final.text)
            
if __name__ == "__main__":
    asyncio.run(main())