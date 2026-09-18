"""
Connecte le projet aux serveurs MCP définis dans mcp_servers/.
langchain-mcp-adapters transforme chaque outil MCP en outil LangChain utilisable
directement par un agent LLM (create_react_agent).
"""
import os
import sys
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _build_client():
    server_env = os.environ.copy()

    # Sur Streamlit Cloud (installation via "uv"), le sous-processus lancé pour un
    # serveur MCP ne retrouvait pas les paquets pourtant installés (ModuleNotFoundError
    # sur dotenv/httpx) : l'environnement hérité ne suffit pas à lui seul. On force donc
    # explicitement le sous-processus à chercher dans les MÊMES dossiers que l'interpréteur
    # actuel (sys.path), ce qui règle le problème quel que soit le mécanisme d'installation.
    server_env["PYTHONPATH"] = os.pathsep.join(sys.path)

    return MultiServerMCPClient(
        {
            "weather": {
                "command": sys.executable,  # plus fiable que "python" (pas toujours dans le PATH du conteneur)
                "args": ["-u", os.path.join(BASE_DIR, "mcp_servers", "weather_server.py")],
                "transport": "stdio",
                "env": server_env,
            },
            "search": {
                "command": sys.executable,
                "args": ["-u", os.path.join(BASE_DIR, "mcp_servers", "search_server.py")],
                "transport": "stdio",
                "env": server_env,
            },
        }
    )


# Sans cache, flight/hotel/weather agents (exécutés en parallèle) relançaient
# CHAQUE fois 2 sous-processus MCP (6 lancements par requête) : lent et inutile,
# les outils ne changent jamais pendant la vie du processus. On ne les charge qu'une fois.
_tools_cache = None
_tools_lock = asyncio.Lock()


async def get_all_tools():
    """Retourne tous les outils MCP (weather + search) comme outils LangChain, en cache."""
    global _tools_cache
    if _tools_cache is None:
        async with _tools_lock:
            if _tools_cache is None:  # revérifié après acquisition du verrou
                _tools_cache = await _build_client().get_tools()
    return _tools_cache
