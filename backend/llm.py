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
            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents="What does the document say about ISTQB?",
                config=types.GenerateContentConfig(
                    temperature=0,
                    tools=[session],  # automatic function calling against the MCP session
                ),
            )

            print(response.text)
            print(response.text)
            # Handle function calls manually
            # part = response.candidates[0].content.parts[0]
            # if part.function_call:
            #     fc = part.function_call
            #     result = await session.call_tool(fc.name, dict(fc.args))
            #     result_text = "\n".join(
            #         c.text for c in result.content if hasattr(c, "text")
            #     )

            #     contents.append(response.candidates[0].content)
            #     contents.append(types.Content(
            #         role="user",
            #         parts=[types.Part(function_response=types.FunctionResponse(
            #             name=fc.name,
            #             response={"result": result_text},
            #         ))],
            #     ))

            #     final = await client.aio.models.generate_content(
            #         model="gemini-2.5-flash",
            #         contents=contents,
            #         config=types.GenerateContentConfig(tools=[gemini_tool]),
            #     )
            #     print(final.text)
            # else:
            #     print(response.text)

if __name__ == "__main__":
    asyncio.run(main())