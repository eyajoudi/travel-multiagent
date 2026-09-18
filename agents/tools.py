"""
Version "in-process" des outils exposés par les serveurs MCP (mcp_servers/).

Pourquoi ce fichier existe en plus de mcp_servers/ :
Les serveurs MCP (weather_server.py, search_server.py) tournent normalement en
sous-processus séparé — c'est la vraie architecture MCP, et ils restent utilisables
tels quels avec n'importe quel client MCP (Claude Desktop, mcp dev, etc.), pour la
démonstration du protocole.

Mais certains hébergeurs (Streamlit Community Cloud, dont l'installation des
dépendances passe par "uv") empêchent un sous-processus Python de retrouver les
paquets pourtant installés, peu importe les variables d'environnement transmises.
Pour que l'application déployée reste fiable, les agents appellent donc ici la
MÊME logique, mais exécutée directement dans le processus de l'application
(mêmes fonctions, même comportement, juste sans le saut par sous-processus).
"""
import httpx
from langchain_core.tools import tool
from tavily import TavilyClient
import os


@tool
async def get_weather_forecast(city: str) -> str:
    """Retourne les prévisions météo (température, conditions) pour une ville."""
    async with httpx.AsyncClient() as client:
        geo = await client.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1},
        )
        geo_data = geo.json()
        if not geo_data.get("results"):
            return f"Ville '{city}' introuvable."

        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]

        forecast = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                "timezone": "auto",
            },
        )
        data = forecast.json()["daily"]
        lines = [f"Prévisions météo pour {city}:"]
        for i, date in enumerate(data["time"]):
            lines.append(
                f"- {date}: {data['temperature_2m_min'][i]}°C à {data['temperature_2m_max'][i]}°C, "
                f"probabilité de pluie {data['precipitation_probability_max'][i]}%"
            )
        return "\n".join(lines)


def _get_tavily():
    key = os.environ.get("TAVILY_API_KEY")
    if not key:
        raise RuntimeError("TAVILY_API_KEY manquante dans l'environnement.")
    return TavilyClient(api_key=key)


@tool
def search_flights(origin: str, destination: str, month: str) -> str:
    """Recherche des vols entre deux villes pour un mois donné."""
    tavily = _get_tavily()
    query = f"vols {origin} vers {destination} en {month} prix"
    results = tavily.search(query=query, max_results=5)
    lines = [f"Résultats de recherche de vols {origin} -> {destination} ({month}):"]
    for r in results["results"]:
        lines.append(f"- {r['title']}: {r['content'][:200]}... ({r['url']})")
    return "\n".join(lines)


@tool
def search_hotels(destination: str, nights: int) -> str:
    """Recherche des hôtels dans une ville pour un nombre de nuits donné."""
    tavily = _get_tavily()
    query = f"meilleurs hôtels {destination} {nights} nuits prix avis"
    results = tavily.search(query=query, max_results=5)
    lines = [f"Résultats de recherche d'hôtels à {destination} ({nights} nuits):"]
    for r in results["results"]:
        lines.append(f"- {r['title']}: {r['content'][:200]}... ({r['url']})")
    return "\n".join(lines)


async def get_all_tools():
    """Même signature que l'ancien mcp_client.get_all_tools(), pour ne rien changer
    côté agents (flight_agent.py, hotel_agent.py, weather_agent.py)."""
    return [get_weather_forecast, search_flights, search_hotels]
