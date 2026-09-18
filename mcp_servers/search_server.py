"""
Serveur MCP pour Flight Agent et Hotel Agent.
Remplace AviationStack/Tavily du schéma par Tavily (recherche web, gratuit,
suffisant pour un projet étudiant : il retourne de vraies pages de résultats).
"""
import os
from dotenv import load_dotenv
from tavily import TavilyClient
from mcp.server.fastmcp import FastMCP

load_dotenv()
mcp = FastMCP("search-server")
tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])


@mcp.tool()
def search_flights(origin: str, destination: str, month: str) -> str:
    """Recherche des vols entre deux villes pour un mois donné."""
    query = f"vols {origin} vers {destination} en {month} prix"
    results = tavily.search(query=query, max_results=5)
    lines = [f"Résultats de recherche de vols {origin} -> {destination} ({month}):"]
    for r in results["results"]:
        lines.append(f"- {r['title']}: {r['content'][:200]}... ({r['url']})")
    return "\n".join(lines)


@mcp.tool()
def search_hotels(destination: str, nights: int) -> str:
    """Recherche des hôtels dans une ville pour un nombre de nuits donné."""
    query = f"meilleurs hôtels {destination} {nights} nuits prix avis"
    results = tavily.search(query=query, max_results=5)
    lines = [f"Résultats de recherche d'hôtels à {destination} ({nights} nuits):"]
    for r in results["results"]:
        lines.append(f"- {r['title']}: {r['content'][:200]}... ({r['url']})")
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run(transport="stdio")
