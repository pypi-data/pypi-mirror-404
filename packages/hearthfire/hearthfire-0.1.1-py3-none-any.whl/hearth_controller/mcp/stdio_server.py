import asyncio
import json
import sys

from hearth_controller.mcp.server import HearthMCPServer


async def handle_message(server: HearthMCPServer, message: dict) -> dict:
    method = message.get("method")
    params = message.get("params", {})
    request_id = message.get("id")

    if method == "initialize":
        result = {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "hearth", "version": "0.1.0"},
        }
    elif method == "tools/list":
        result = {"tools": server.get_tools()}
    elif method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments", {})
        tool_result = await server.call_tool(name, arguments)
        result = {
            "content": [
                {"type": "text", "text": json.dumps(tool_result, indent=2, ensure_ascii=False)}
            ]
        }
    elif method == "notifications/initialized":
        return None
    else:
        result = {"error": {"code": -32601, "message": f"Unknown method: {method}"}}

    if request_id is None:
        return None

    return {"jsonrpc": "2.0", "id": request_id, "result": result}


async def run_stdio_server() -> None:
    server = HearthMCPServer()

    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)

    writer_transport, writer_protocol = await asyncio.get_event_loop().connect_write_pipe(
        asyncio.streams.FlowControlMixin, sys.stdout
    )
    writer = asyncio.StreamWriter(writer_transport, writer_protocol, None, asyncio.get_event_loop())

    while True:
        try:
            line = await reader.readline()
            if not line:
                break

            message = json.loads(line.decode())
            response = await handle_message(server, message)

            if response:
                output = json.dumps(response) + "\n"
                writer.write(output.encode())
                await writer.drain()

        except json.JSONDecodeError:
            continue
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": str(e)},
            }
            writer.write((json.dumps(error_response) + "\n").encode())
            await writer.drain()


def main() -> None:
    asyncio.run(run_stdio_server())


if __name__ == "__main__":
    main()
