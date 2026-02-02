import json
from fastmcp import FastMCP
from .client import BazarrClient


def register_bazarr_tools(mcp: FastMCP, client: BazarrClient) -> None:
    """Enregistre tous les outils Bazarr sur le serveur MCP."""

    # ==================== Système ====================

    @mcp.tool()
    async def bazarr_system_status() -> str:
        """Récupère le statut du système Bazarr (version, base de données, timezone)."""
        status = await client.get_system_status()
        return json.dumps(status, indent=2, ensure_ascii=False)

    @mcp.tool()
    async def bazarr_get_languages() -> str:
        """Liste les langues configurées dans Bazarr pour les sous-titres."""
        languages = await client.get_languages()
        simplified = []
        for lang in languages:
            simplified.append({
                "name": lang.get("name"),
                "code2": lang.get("code2"),
                "code3": lang.get("code3"),
                "enabled": lang.get("enabled"),
            })
        return json.dumps(simplified, indent=2, ensure_ascii=False)

    @mcp.tool()
    async def bazarr_get_providers() -> str:
        """Liste les providers de sous-titres configurés et leur statut (actif, throttled)."""
        providers = await client.get_providers()
        return json.dumps(providers, indent=2, ensure_ascii=False)

    @mcp.tool()
    async def bazarr_reset_providers() -> str:
        """Réinitialise les providers throttled pour permettre une nouvelle recherche."""
        await client.reset_providers()
        return "Providers réinitialisés avec succès."

    # ==================== Films ====================

    @mcp.tool()
    async def bazarr_get_movies(radarr_id: int | None = None) -> str:
        """
        Liste les films avec leurs informations de sous-titres.

        Args:
            radarr_id: ID Radarr pour filtrer sur un film spécifique (optionnel)
        """
        result = await client.get_movies(radarr_id=radarr_id)
        data = result.get("data", [])
        simplified = []
        for m in data[:50]:  # Limiter à 50 résultats
            subtitles = m.get("subtitles", [])
            missing = m.get("missing_subtitles", [])
            simplified.append({
                "radarrId": m.get("radarrId"),
                "title": m.get("title"),
                "year": m.get("year"),
                "monitored": m.get("monitored"),
                "subtitles": [
                    {"language": s.get("name"), "path": s.get("path")}
                    for s in subtitles[:5]
                ] if subtitles else [],
                "missing_subtitles": [
                    s.get("name") for s in missing
                ] if missing else [],
                "audio_language": m.get("audio_language", []),
            })
        return json.dumps({
            "total": result.get("total", len(data)),
            "movies": simplified,
        }, indent=2, ensure_ascii=False)

    @mcp.tool()
    async def bazarr_get_movies_wanted(limit: int = 20) -> str:
        """
        Liste les films avec sous-titres manquants.

        Args:
            limit: Nombre maximum de résultats (défaut: 20)
        """
        result = await client.get_movies_wanted(length=limit)
        data = result.get("data", [])
        simplified = []
        for m in data:
            simplified.append({
                "radarrId": m.get("radarrId"),
                "title": m.get("title"),
                "missing_subtitles": [
                    s.get("name") for s in m.get("missing_subtitles", [])
                ],
                "sceneName": m.get("sceneName"),
                "tags": m.get("tags", []),
            })
        return json.dumps({
            "total": result.get("total", len(data)),
            "movies": simplified,
        }, indent=2, ensure_ascii=False)

    @mcp.tool()
    async def bazarr_get_movies_history(limit: int = 20, radarr_id: int | None = None) -> str:
        """
        Récupère l'historique des téléchargements de sous-titres pour les films.

        Args:
            limit: Nombre maximum de résultats (défaut: 20)
            radarr_id: ID Radarr pour filtrer sur un film spécifique (optionnel)
        """
        result = await client.get_movies_history(length=limit, radarr_id=radarr_id)
        data = result.get("data", [])
        simplified = []
        for h in data:
            simplified.append({
                "radarrId": h.get("radarrId"),
                "title": h.get("title"),
                "language": h.get("language", {}).get("name") if isinstance(h.get("language"), dict) else h.get("language"),
                "provider": h.get("provider"),
                "timestamp": h.get("timestamp"),
                "score": h.get("score"),
                "subs_id": h.get("subs_id"),
                "action": h.get("action"),
            })
        return json.dumps({
            "total": result.get("total", len(data)),
            "history": simplified,
        }, indent=2, ensure_ascii=False)

    @mcp.tool()
    async def bazarr_search_movie_subtitles(
        radarr_id: int,
        language: str,
        hi: bool = False,
        forced: bool = False,
    ) -> str:
        """
        Lance une recherche et télécharge des sous-titres pour un film.

        Args:
            radarr_id: ID Radarr du film
            language: Code langue ISO (ex: "fr", "en")
            hi: Sous-titres pour malentendants (défaut: false)
            forced: Sous-titres forcés uniquement (défaut: false)
        """
        await client.search_movie_subtitles(
            radarr_id=radarr_id,
            language=language,
            hi=hi,
            forced=forced,
        )
        return f"Recherche de sous-titres lancée pour le film (radarrId: {radarr_id}, langue: {language})."

    @mcp.tool()
    async def bazarr_sync_movies() -> str:
        """Synchronise la liste des films avec Radarr."""
        await client.sync_movies()
        return "Synchronisation des films avec Radarr lancée."

    @mcp.tool()
    async def bazarr_search_wanted_movies() -> str:
        """Lance une recherche de sous-titres pour tous les films avec sous-titres manquants."""
        await client.search_wanted_movies()
        return "Recherche de sous-titres lancée pour tous les films wanted."

    # ==================== Séries ====================

    @mcp.tool()
    async def bazarr_get_series(series_id: int | None = None) -> str:
        """
        Liste les séries avec leurs informations de sous-titres.

        Args:
            series_id: ID Sonarr pour filtrer sur une série spécifique (optionnel)
        """
        result = await client.get_series(series_id=series_id)
        data = result.get("data", [])
        simplified = []
        for s in data[:50]:  # Limiter à 50 résultats
            simplified.append({
                "sonarrSeriesId": s.get("sonarrSeriesId"),
                "title": s.get("title"),
                "year": s.get("year"),
                "monitored": s.get("monitored"),
                "episodeFileCount": s.get("episodeFileCount"),
                "episodeMissingCount": s.get("episodeMissingCount", 0),
                "profileId": s.get("profileId"),
                "seriesType": s.get("seriesType"),
            })
        return json.dumps({
            "total": result.get("total", len(data)),
            "series": simplified,
        }, indent=2, ensure_ascii=False)

    @mcp.tool()
    async def bazarr_get_episodes_wanted(limit: int = 20) -> str:
        """
        Liste les épisodes avec sous-titres manquants.

        Args:
            limit: Nombre maximum de résultats (défaut: 20)
        """
        result = await client.get_episodes_wanted(length=limit)
        data = result.get("data", [])
        simplified = []
        for e in data:
            simplified.append({
                "sonarrSeriesId": e.get("sonarrSeriesId"),
                "sonarrEpisodeId": e.get("sonarrEpisodeId"),
                "seriesTitle": e.get("seriesTitle"),
                "episode_number": e.get("episode_number"),
                "episodeTitle": e.get("episodeTitle"),
                "missing_subtitles": [
                    s.get("name") for s in e.get("missing_subtitles", [])
                ],
                "sceneName": e.get("sceneName"),
            })
        return json.dumps({
            "total": result.get("total", len(data)),
            "episodes": simplified,
        }, indent=2, ensure_ascii=False)

    @mcp.tool()
    async def bazarr_get_episodes_history(limit: int = 20, episode_id: int | None = None) -> str:
        """
        Récupère l'historique des téléchargements de sous-titres pour les épisodes.

        Args:
            limit: Nombre maximum de résultats (défaut: 20)
            episode_id: ID Sonarr de l'épisode pour filtrer (optionnel)
        """
        result = await client.get_episodes_history(length=limit, episode_id=episode_id)
        data = result.get("data", [])
        simplified = []
        for h in data:
            simplified.append({
                "sonarrSeriesId": h.get("sonarrSeriesId"),
                "sonarrEpisodeId": h.get("sonarrEpisodeId"),
                "seriesTitle": h.get("seriesTitle"),
                "episode_number": h.get("episode_number"),
                "episodeTitle": h.get("episodeTitle"),
                "language": h.get("language", {}).get("name") if isinstance(h.get("language"), dict) else h.get("language"),
                "provider": h.get("provider"),
                "timestamp": h.get("timestamp"),
                "score": h.get("score"),
                "action": h.get("action"),
            })
        return json.dumps({
            "total": result.get("total", len(data)),
            "history": simplified,
        }, indent=2, ensure_ascii=False)

    @mcp.tool()
    async def bazarr_search_episode_subtitles(
        episode_id: int,
        language: str,
        hi: bool = False,
        forced: bool = False,
    ) -> str:
        """
        Lance une recherche et télécharge des sous-titres pour un épisode.

        Args:
            episode_id: ID Sonarr de l'épisode
            language: Code langue ISO (ex: "fr", "en")
            hi: Sous-titres pour malentendants (défaut: false)
            forced: Sous-titres forcés uniquement (défaut: false)
        """
        await client.search_episode_subtitles(
            episode_id=episode_id,
            language=language,
            hi=hi,
            forced=forced,
        )
        return f"Recherche de sous-titres lancée pour l'épisode (episodeId: {episode_id}, langue: {language})."

    @mcp.tool()
    async def bazarr_sync_series() -> str:
        """Synchronise la liste des séries avec Sonarr."""
        await client.sync_series()
        return "Synchronisation des séries avec Sonarr lancée."

    @mcp.tool()
    async def bazarr_search_wanted_episodes() -> str:
        """Lance une recherche de sous-titres pour tous les épisodes avec sous-titres manquants."""
        await client.search_wanted_episodes()
        return "Recherche de sous-titres lancée pour tous les épisodes wanted."
