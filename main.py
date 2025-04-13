# based on https://github.com/openai/openai-agents-python/tree/main/examples/mcp/filesystem_example

import sys
import asyncio
import os
import shutil

from agents import Agent, Runner, gen_trace_id, trace
from agents.mcp import MCPServer, MCPServerStdio

from openai.types.responses import ResponseTextDeltaEvent

from dotenv import load_dotenv

async def run(mcp_servers: [MCPServer]):
    print("*** Hello!")

    agent = Agent(
        name="Assistant",
        instructions="Use the tools to read the filesystem and answer questions based on those files.",
        mcp_servers=mcp_servers,
    )

    queries = [
        "Read the files and list them.",
        "What is my #1 favorite book?",
        "Look at my favorite songs. Suggest one new song that I might like.",
        "What time is it now?",
        "いま何時? 使ったツール名も教えて。",
    ]

    for query in queries:
        print(f"Running: {query}")
        #result = await Runner.run(starting_agent=agent, input=query)
        #print(result.final_output)
        result = Runner.run_streamed(starting_agent=agent, input=query)
        async for event in result.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                print(event.data.delta, end="", flush=True)
        print("")
        print("")

    print("*** Bye!")


async def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    samples_dir = os.path.join(current_dir, "sample_files")

    fs_server = MCPServerStdio(
        name="Filesystem Server, via npx",
        params={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", samples_dir],
        },
        cache_tools_list=True,
    )

    time_server = MCPServerStdio(
        name="Time Server, via uvx",
        params={
            "command": "uvx",
            "args": ["mcp-server-time", "--local-timezone=Asia/Tokyo"],
        },
        cache_tools_list=True,
    )

    async with fs_server, time_server:
        trace_id = gen_trace_id()
        with trace(workflow_name="MCP Filesystem and Time Example", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n")
            await run([fs_server, time_server])


if __name__ == "__main__":
    load_dotenv()

    if "OPENAI_API_KEY" not in os.environ:
        print("OPENAI_API_KEY is not set", file=sys.stderr)
        sys.exit(1)
        
    # Let's make sure the user has npx installed
    if not shutil.which("npx"):
        raise RuntimeError("npx is not installed. Please install it with `npm install -g npx`.")

    # Let's make sure the user has uvx installed
    if not shutil.which("uvx"):
        raise RuntimeError("uvx is not installed.")

    asyncio.run(main())
