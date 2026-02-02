import asyncio
import json
from fastmcp import FastMCP

from ..plex.client import PlexClient
from ..radarr.client import RadarrClient
from ..overseerr.client import OverseerrClient
from ..bazarr.client import BazarrClient
from ..prowlarr.client import ProwlarrClient


def register_unified_tools(
    mcp: FastMCP,
    plex_client: PlexClient | None = None,
    radarr_client: RadarrClient | None = None,
    overseerr_client: OverseerrClient | None = None,
    bazarr_client: BazarrClient | None = None,
    prowlarr_client: ProwlarrClient | None = None,
) -> None:
    """Enregistre les outils unifiés de haut niveau."""

    @mcp.tool()
    async def system_health_check() -> str:
        """
        Vérifie l'état de santé de tous les services du NAS.

        Retourne un rapport unifié avec le statut de chaque service
        (Plex, Radarr, Overseerr, Bazarr, Prowlarr).
        """

        async def check_plex() -> dict:
            if plex_client is None:
                return {"status": "not_configured"}
            try:
                server_info = await plex_client.get_server_info()
                sessions = await plex_client.get_active_sessions()
                return {
                    "status": "online",
                    "version": server_info.get("version"),
                    "name": server_info.get("friendlyName"),
                    "platform": server_info.get("platform"),
                    "active_sessions": len(sessions),
                }
            except Exception as e:
                return {"status": "offline", "error": str(e)}

        async def check_radarr() -> dict:
            if radarr_client is None:
                return {"status": "not_configured"}
            try:
                status = await radarr_client.get_system_status()
                movies = await radarr_client.get_movies()
                queue = await radarr_client.get_queue()
                monitored = sum(1 for m in movies if m.get("monitored", False))
                return {
                    "status": "online",
                    "version": status.get("version"),
                    "movies_total": len(movies),
                    "movies_monitored": monitored,
                    "queue_count": queue.get("totalRecords", 0),
                }
            except Exception as e:
                return {"status": "offline", "error": str(e)}

        async def check_overseerr() -> dict:
            if overseerr_client is None:
                return {"status": "not_configured"}
            try:
                status = await overseerr_client.get_status()
                requests = await overseerr_client.get_requests(take=100)
                pending = sum(1 for r in requests.get("results", [])
                             if r.get("status") == 1)  # 1 = pending
                return {
                    "status": "online",
                    "version": status.get("version"),
                    "pending_requests": pending,
                }
            except Exception as e:
                return {"status": "offline", "error": str(e)}

        async def check_bazarr() -> dict:
            if bazarr_client is None:
                return {"status": "not_configured"}
            try:
                status = await bazarr_client.get_system_status()
                providers = await bazarr_client.get_providers()
                movies_wanted = await bazarr_client.get_movies_wanted(limit=1000)
                episodes_wanted = await bazarr_client.get_episodes_wanted(limit=1000)

                providers_ok = sum(1 for p in providers if p.get("status") == "active")
                providers_throttled = sum(1 for p in providers if p.get("status") == "throttled")

                return {
                    "status": "online",
                    "version": status.get("version"),
                    "providers_ok": providers_ok,
                    "providers_throttled": providers_throttled,
                    "missing_movie_subtitles": len(movies_wanted.get("data", [])),
                    "missing_episode_subtitles": len(episodes_wanted.get("data", [])),
                }
            except Exception as e:
                return {"status": "offline", "error": str(e)}

        async def check_prowlarr() -> dict:
            if prowlarr_client is None:
                return {"status": "not_configured"}
            try:
                status = await prowlarr_client.get_system_status()
                health = await prowlarr_client.get_health()
                indexers = await prowlarr_client.get_indexers()

                indexers_enabled = sum(1 for i in indexers if i.get("enable", False))
                indexers_disabled = len(indexers) - indexers_enabled
                health_issues = [h.get("message") for h in health] if health else []

                return {
                    "status": "online",
                    "version": status.get("version"),
                    "indexers_total": len(indexers),
                    "indexers_enabled": indexers_enabled,
                    "indexers_disabled": indexers_disabled,
                    "health_issues": health_issues,
                }
            except Exception as e:
                return {"status": "offline", "error": str(e)}

        # Exécuter tous les checks en parallèle
        results = await asyncio.gather(
            check_plex(),
            check_radarr(),
            check_overseerr(),
            check_bazarr(),
            check_prowlarr(),
        )

        services = {
            "plex": results[0],
            "radarr": results[1],
            "overseerr": results[2],
            "bazarr": results[3],
            "prowlarr": results[4],
        }

        # Calculer le statut global
        configured_services = [s for s in services.values() if s["status"] != "not_configured"]
        online_services = [s for s in configured_services if s["status"] == "online"]
        offline_services = [s for s in configured_services if s["status"] == "offline"]

        # Vérifier les warnings (providers throttled, health issues)
        has_warnings = False
        warnings = []

        if services["bazarr"].get("providers_throttled", 0) > 0:
            has_warnings = True
            warnings.append(f"Bazarr: {services['bazarr']['providers_throttled']} provider(s) throttled")

        if services["prowlarr"].get("health_issues"):
            has_warnings = True
            warnings.append(f"Prowlarr: {len(services['prowlarr']['health_issues'])} problème(s)")

        # Déterminer overall_status
        if offline_services:
            overall_status = "critical"
        elif has_warnings:
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        # Construire le résumé
        summary_parts = []
        summary_parts.append(f"{len(online_services)}/{len(configured_services)} services online")
        if offline_services:
            offline_names = [name for name, s in services.items() if s["status"] == "offline"]
            summary_parts.append(f"Offline: {', '.join(offline_names)}")
        if warnings:
            summary_parts.extend(warnings)

        response = {
            "overall_status": overall_status,
            "services": services,
            "summary": ". ".join(summary_parts) + ".",
        }

        return json.dumps(response, indent=2, ensure_ascii=False)
