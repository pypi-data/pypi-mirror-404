import json

from fastapi import APIRouter, Request, Response

from hearth_controller.mcp.server import HearthMCPServer

router = APIRouter()


@router.post("/mcp")
async def mcp_endpoint(request: Request) -> Response:
    body = await request.json()

    method = body.get("method")
    params = body.get("params", {})
    request_id = body.get("id")

    auth_header = request.headers.get("Authorization", "")
    token = ""
    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip()

    server = HearthMCPServer(token=token)

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
    else:
        result = {"error": {"code": -32601, "message": f"Unknown method: {method}"}}

    return Response(
        content=json.dumps({"jsonrpc": "2.0", "id": request_id, "result": result}),
        media_type="application/json",
    )
