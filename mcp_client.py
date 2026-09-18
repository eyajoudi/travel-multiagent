"""
Connecte le projet aux serveurs MCP définis dans mcp_servers/.
langchain-mcp-adapters transforme chaque outil MCP en outil LangChain utilisable
directement par un agent LLM (create_react_agent).
"""
import os
from langchain_mcp_adapters.client import MultiServerMCPClient

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

mcp_client = MultiServerMCPClient(
    {
        "weather": {
            "command": "python",
            "args": [os.path.join(BASE_DIR, "mcp_servers", "weather_server.py")],
            "transport": "stdio",
        },
        "search": {
            "command": "python",
            "args": [os.path.join(BASE_DIR, "mcp_servers", "search_server.py")],
            "transport": "stdio",
        },
    }
)


async def get_all_tools():
    """Retourne tous les outils MCP (weather + search) comme outils LangChain."""
    return await mcp_client.get_tools()
