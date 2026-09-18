"""
Serveur MCP "Custom Weather MCP" du schéma.
Expose un outil `get_weather_forecast` via le protocole MCP (stdio).
Utilise Open-Meteo : gratuit, sans clé API.
"""
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("weather-server")


@mcp.tool()
async def get_weather_forecast(city: str) -> str:
    """Retourne les prévisions météo (température, conditions) pour une ville."""
    async with httpx.AsyncClient() as client:
        # 1. Géocodage du nom de ville
        geo = await client.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1},
        )
        geo_data = geo.json()
        if not geo_data.get("results"):
            return f"Ville '{city}' introuvable."

        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]

        # 2. Prévisions
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


if __name__ == "__main__":
    mcp.run(transport="stdio")
