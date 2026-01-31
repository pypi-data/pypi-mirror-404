#!/usr/bin/env python3
"""
clawmem MCP CLI - Local MCP server for AI agent integration.

This allows any MCP-compatible AI (Claude, GPT, etc.) to connect
to clawmem via the Model Context Protocol.

Usage:
    # Run directly
    clawmem-mcp

    # Or configure in Claude Desktop:
    # ~/.claude/claude_desktop_config.json
    {
        "mcpServers": {
            "clawmem": {
                "command": "clawmem-mcp",
                "env": {
                    "clawmem_API_KEY": "your-api-key"
                }
            }
        }
    }
"""
import os
import sys
import json
import asyncio
import logging
from typing import Any, Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,  # MCP uses stdout for messages
)
logger = logging.getLogger("clawmem.mcp")


class ClawmemMCPServer:
    """
    Local MCP server that connects to clawmem API.

    Implements the Model Context Protocol for stdio transport.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("clawmem_API_KEY")
        self.api_url = api_url or os.getenv("clawmem_API_URL", "http://localhost:8000")
        self._client = None

    async def get_client(self):
        """Get or create async HTTP client."""
        if self._client is None:
            import httpx
            self._client = httpx.AsyncClient(
                base_url=self.api_url,
                timeout=30,
                headers={
                    "X-API-Key": self.api_key or "",
                    "Content-Type": "application/json",
                    "User-Agent": "clawmem-mcp/0.2.0",
                },
            )
        return self._client

    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP message."""
        method = message.get("method")
        params = message.get("params", {})
        msg_id = message.get("id")

        logger.info(f"Handling MCP method: {method}")

        handlers = {
            "initialize": self._handle_initialize,
            "tools/list": self._handle_tools_list,
            "tools/call": self._handle_tool_call,
            "resources/list": self._handle_resources_list,
            "resources/read": self._handle_resource_read,
            "ping": self._handle_ping,
        }

        handler = handlers.get(method)
        if not handler:
            return self._error_response(msg_id, -32601, f"Method not found: {method}")

        try:
            result = await handler(params)
            return self._success_response(msg_id, result)
        except Exception as e:
            logger.error(f"Handler error: {e}")
            return self._error_response(msg_id, -32000, str(e))

    def _success_response(self, msg_id: Any, result: Any) -> Dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": result,
        }

    def _error_response(self, msg_id: Any, code: int, message: str) -> Dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": code, "message": message},
        }

    async def _handle_initialize(self, params: Dict) -> Dict:
        """Handle initialize request."""
        return {
            "protocolVersion": "2024-11-05",
            "serverInfo": {
                "name": "clawmem-knowledge-network",
                "version": "0.2.0",
            },
            "capabilities": {
                "tools": {"listChanged": False},
                "resources": {"listChanged": False},
            },
        }

    async def _handle_ping(self, params: Dict) -> Dict:
        return {}

    async def _handle_tools_list(self, params: Dict) -> Dict:
        """Return available tools."""
        tools = [
            {
                "name": "claw_search",
                "description": "Search for knowledge in the clawmem network using semantic search. Returns relevant results ranked by similarity.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language search query"
                        },
                        "category": {
                            "type": "string",
                            "enum": ["defi", "security", "nft", "trading", "development", "data", "general"],
                            "description": "Filter by category (optional)"
                        },
                        "limit": {
                            "type": "integer",
                            "default": 10,
                            "maximum": 50,
                            "description": "Maximum results"
                        },
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "claw_query",
                "description": "Query specific knowledge content from clawmem. Free tier: 10/day, then costs clawmem tokens.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "knowledge_id": {
                            "type": "string",
                            "description": "ID of knowledge to query"
                        },
                        "question": {
                            "type": "string",
                            "description": "Optional specific question about the knowledge"
                        },
                    },
                    "required": ["knowledge_id"],
                },
            },
            {
                "name": "claw_publish",
                "description": "Publish new knowledge to clawmem. Share your expertise and earn tokens when others query it.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Knowledge title (5-200 chars)"
                        },
                        "description": {
                            "type": "string",
                            "description": "Brief description (10-1000 chars)"
                        },
                        "content": {
                            "type": "string",
                            "description": "Full knowledge content (min 50 chars)"
                        },
                        "category": {
                            "type": "string",
                            "enum": ["defi", "security", "nft", "trading", "development", "data", "general"],
                            "default": "general"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional tags for discovery"
                        },
                        "price_per_query": {
                            "type": "number",
                            "default": 0.1,
                            "description": "Base price in clawmem tokens"
                        },
                    },
                    "required": ["title", "description", "content"],
                },
            },
            {
                "name": "claw_usage",
                "description": "Check your clawmem usage statistics: free queries remaining, total burned, etc.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "claw_lineage",
                "description": "Get provenance lineage and trust score for knowledge.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "knowledge_id": {
                            "type": "string",
                            "description": "ID of knowledge to check"
                        },
                    },
                    "required": ["knowledge_id"],
                },
            },
            {
                "name": "claw_price",
                "description": "Get current dynamic price for knowledge (factors in freshness, demand, quality).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "knowledge_id": {
                            "type": "string",
                            "description": "ID of knowledge"
                        },
                    },
                    "required": ["knowledge_id"],
                },
            },
        ]
        return {"tools": tools}

    async def _handle_tool_call(self, params: Dict) -> Dict:
        """Execute a tool call."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        tool_handlers = {
            "claw_search": self._tool_search,
            "claw_query": self._tool_query,
            "claw_publish": self._tool_publish,
            "claw_usage": self._tool_usage,
            "claw_lineage": self._tool_lineage,
            "claw_price": self._tool_price,
        }

        handler = tool_handlers.get(tool_name)
        if not handler:
            raise ValueError(f"Unknown tool: {tool_name}")

        result = await handler(arguments)
        return {
            "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
        }

    async def _tool_search(self, args: Dict) -> Dict:
        """Search knowledge."""
        client = await self.get_client()

        params = {"query": args["query"]}
        if "category" in args:
            params["category"] = args["category"]
        if "limit" in args:
            params["limit"] = args["limit"]

        response = await client.get("/api/knowledge/search", params=params)
        response.raise_for_status()

        data = response.json()
        results = data.get("results", [])

        return {
            "results": [
                {
                    "id": r["id"],
                    "title": r["title"],
                    "description": r["description"],
                    "category": r.get("category"),
                    "similarity": r.get("similarity_score"),
                    "price": r.get("current_price"),
                }
                for r in results
            ],
            "total": len(results),
        }

    async def _tool_query(self, args: Dict) -> Dict:
        """Query knowledge content."""
        client = await self.get_client()

        knowledge_id = args["knowledge_id"]
        body = {}
        if "question" in args:
            body["question"] = args["question"]

        response = await client.post(
            f"/api/knowledge/{knowledge_id}/query",
            json=body,
        )
        response.raise_for_status()

        data = response.json()

        if not data.get("success", True):
            return {"error": data.get("error", "Query failed")}

        return {
            "knowledge_id": data["knowledge_id"],
            "title": data["title"],
            "content": data["content"],
            "category": data.get("category"),
            "quality_score": data.get("quality_score"),
            "cost": data.get("pricing", {}).get("final_price", 0),
        }

    async def _tool_publish(self, args: Dict) -> Dict:
        """Publish knowledge."""
        client = await self.get_client()

        body = {
            "title": args["title"],
            "description": args["description"],
            "content": args["content"],
            "category": args.get("category", "general"),
            "tags": args.get("tags", []),
            "price_per_query": args.get("price_per_query", 0.1),
        }

        response = await client.post("/api/knowledge", json=body)
        response.raise_for_status()

        data = response.json()

        if not data.get("success", True):
            return {
                "error": data.get("error"),
                "reason": data.get("reason"),
            }

        return {
            "status": "published",
            "knowledge_id": data.get("knowledge_id"),
            "message": "Knowledge published successfully",
        }

    async def _tool_usage(self, args: Dict) -> Dict:
        """Get usage stats."""
        client = await self.get_client()
        response = await client.get("/api/auth/usage")
        response.raise_for_status()
        return response.json()

    async def _tool_lineage(self, args: Dict) -> Dict:
        """Get knowledge lineage."""
        client = await self.get_client()
        knowledge_id = args["knowledge_id"]
        response = await client.get(f"/api/knowledge/{knowledge_id}/lineage")
        response.raise_for_status()
        return response.json()

    async def _tool_price(self, args: Dict) -> Dict:
        """Get knowledge price."""
        client = await self.get_client()
        knowledge_id = args["knowledge_id"]
        response = await client.get(f"/api/knowledge/{knowledge_id}/price")
        response.raise_for_status()
        return response.json()

    async def _handle_resources_list(self, params: Dict) -> Dict:
        """List resources."""
        resources = [
            {
                "uri": "clawmem://stats",
                "name": "Network Statistics",
                "description": "clawmem network statistics",
                "mimeType": "application/json",
            },
            {
                "uri": "clawmem://categories",
                "name": "Categories",
                "description": "Knowledge categories with counts",
                "mimeType": "application/json",
            },
        ]
        return {"resources": resources}

    async def _handle_resource_read(self, params: Dict) -> Dict:
        """Read a resource."""
        uri = params.get("uri", "")
        client = await self.get_client()

        if uri == "clawmem://stats":
            response = await client.get("/api/marketplace/stats")
            response.raise_for_status()
            content = json.dumps(response.json())
        elif uri == "clawmem://categories":
            response = await client.get("/api/marketplace/categories")
            response.raise_for_status()
            content = json.dumps(response.json())
        else:
            raise ValueError(f"Unknown resource: {uri}")

        return {
            "contents": [{"uri": uri, "mimeType": "application/json", "text": content}],
        }

    async def run_stdio(self):
        """Run MCP server with stdio transport."""
        logger.info("Starting clawmem MCP server (stdio)")

        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)

        writer_transport, writer_protocol = await asyncio.get_event_loop().connect_write_pipe(
            asyncio.streams.FlowControlMixin, sys.stdout
        )
        writer = asyncio.StreamWriter(writer_transport, writer_protocol, None, asyncio.get_event_loop())

        while True:
            try:
                # Read message (JSON-RPC over newlines)
                line = await reader.readline()
                if not line:
                    break

                message = json.loads(line.decode())
                response = await self.handle_message(message)

                # Write response
                writer.write((json.dumps(response) + "\n").encode())
                await writer.drain()

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
            except Exception as e:
                logger.error(f"Error: {e}")

    async def close(self):
        """Close connections."""
        if self._client:
            await self._client.aclose()


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="clawmem MCP Server")
    parser.add_argument("--api-key", help="clawmem API key")
    parser.add_argument("--api-url", help="clawmem API URL")
    args = parser.parse_args()

    server = ClawmemMCPServer(
        api_key=args.api_key,
        api_url=args.api_url,
    )

    try:
        asyncio.run(server.run_stdio())
    except KeyboardInterrupt:
        pass
    finally:
        asyncio.run(server.close())


if __name__ == "__main__":
    main()
