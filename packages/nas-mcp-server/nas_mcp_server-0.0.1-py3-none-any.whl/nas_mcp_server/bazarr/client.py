import os
from typing import Any
import httpx


class BazarrClient:
    """Client HTTP pour l'API Bazarr."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.base_url = (base_url or os.getenv("BAZARR_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("BAZARR_API_KEY", "")

        if not self.base_url:
            raise ValueError("BAZARR_URL is required")
        if not self.api_key:
            raise ValueError("BAZARR_API_KEY is required")

        self.headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> Any:
        """Execute une requête HTTP vers l'API Bazarr."""
        url = f"{self.base_url}/api{endpoint}"

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                json=json_data,
                timeout=30.0,
            )
            response.raise_for_status()

            if response.status_code == 204:
                return None
            return response.json()

    # ==================== Système ====================

    async def get_system_status(self) -> dict[str, Any]:
        """Récupère le statut du système Bazarr."""
        return await self._request("GET", "/system/status")

    async def get_languages(self, history: bool = False) -> list[dict[str, Any]]:
        """Récupère les langues configurées.

        Args:
            history: Si True, récupère les langues depuis l'historique
        """
        params = {"history": "true"} if history else None
        return await self._request("GET", "/system/languages", params=params)

    # ==================== Providers ====================

    async def get_providers(self, history: str | None = None) -> list[dict[str, Any]]:
        """Récupère la liste des providers de sous-titres.

        Args:
            history: Nom du provider pour les stats d'historique
        """
        params = {"history": history} if history else None
        return await self._request("GET", "/providers", params=params)

    async def reset_providers(self) -> None:
        """Réinitialise les providers throttled."""
        await self._request("POST", "/providers", json_data={"action": "reset"})

    # ==================== Films ====================

    async def get_movies(
        self,
        start: int = 0,
        length: int = -1,
        radarr_id: int | None = None,
    ) -> dict[str, Any]:
        """Récupère les films avec leurs informations de sous-titres.

        Args:
            start: Position de départ pour la pagination
            length: Nombre d'éléments (-1 pour tous)
            radarr_id: ID Radarr spécifique pour filtrer
        """
        params: dict[str, Any] = {"start": start, "length": length}
        if radarr_id is not None:
            params["radarrid[]"] = radarr_id
        return await self._request("GET", "/movies", params=params)

    async def get_movies_wanted(
        self,
        start: int = 0,
        length: int = -1,
    ) -> dict[str, Any]:
        """Récupère les films avec sous-titres manquants.

        Args:
            start: Position de départ pour la pagination
            length: Nombre d'éléments (-1 pour tous)
        """
        params = {"start": start, "length": length}
        return await self._request("GET", "/movies/wanted", params=params)

    async def get_movies_history(
        self,
        start: int = 0,
        length: int = -1,
        radarr_id: int | None = None,
    ) -> dict[str, Any]:
        """Récupère l'historique des sous-titres de films.

        Args:
            start: Position de départ pour la pagination
            length: Nombre d'éléments (-1 pour tous)
            radarr_id: ID Radarr pour filtrer
        """
        params: dict[str, Any] = {"start": start, "length": length}
        if radarr_id is not None:
            params["radarrid"] = radarr_id
        return await self._request("GET", "/movies/history", params=params)

    async def search_movie_subtitles(
        self,
        radarr_id: int,
        language: str,
        forced: bool = False,
        hi: bool = False,
    ) -> None:
        """Lance une recherche de sous-titres pour un film.

        Args:
            radarr_id: ID Radarr du film
            language: Code langue ISO 639-1 (ex: "fr", "en")
            forced: Sous-titres forcés uniquement
            hi: Sous-titres pour malentendants
        """
        params = {
            "radarrid": radarr_id,
            "language": language,
            "forced": str(forced).lower(),
            "hi": str(hi).lower(),
        }
        await self._request("PATCH", "/movies/subtitles", params=params)

    async def sync_movies(self) -> None:
        """Synchronise les films avec Radarr."""
        await self._request(
            "PATCH",
            "/movies",
            params={"action": "sync"},
        )

    async def scan_disk_movies(self, radarr_id: int | None = None) -> None:
        """Analyse le disque pour les sous-titres de films.

        Args:
            radarr_id: ID Radarr spécifique, ou None pour tous
        """
        params: dict[str, Any] = {"action": "scan-disk"}
        if radarr_id is not None:
            params["radarrid"] = radarr_id
        await self._request("PATCH", "/movies", params=params)

    async def search_wanted_movies(self) -> None:
        """Lance une recherche de sous-titres pour tous les films wanted."""
        await self._request(
            "PATCH",
            "/movies",
            params={"action": "search-wanted"},
        )

    # ==================== Séries ====================

    async def get_series(
        self,
        start: int = 0,
        length: int = -1,
        series_id: int | None = None,
    ) -> dict[str, Any]:
        """Récupère les séries avec leurs informations de sous-titres.

        Args:
            start: Position de départ pour la pagination
            length: Nombre d'éléments (-1 pour tous)
            series_id: ID Sonarr spécifique pour filtrer
        """
        params: dict[str, Any] = {"start": start, "length": length}
        if series_id is not None:
            params["seriesid[]"] = series_id
        return await self._request("GET", "/series", params=params)

    async def get_episodes_wanted(
        self,
        start: int = 0,
        length: int = -1,
    ) -> dict[str, Any]:
        """Récupère les épisodes avec sous-titres manquants.

        Args:
            start: Position de départ pour la pagination
            length: Nombre d'éléments (-1 pour tous)
        """
        params = {"start": start, "length": length}
        return await self._request("GET", "/episodes/wanted", params=params)

    async def get_episodes_history(
        self,
        start: int = 0,
        length: int = -1,
        episode_id: int | None = None,
    ) -> dict[str, Any]:
        """Récupère l'historique des sous-titres d'épisodes.

        Args:
            start: Position de départ pour la pagination
            length: Nombre d'éléments (-1 pour tous)
            episode_id: ID d'épisode Sonarr pour filtrer
        """
        params: dict[str, Any] = {"start": start, "length": length}
        if episode_id is not None:
            params["episodeid"] = episode_id
        return await self._request("GET", "/episodes/history", params=params)

    async def search_episode_subtitles(
        self,
        episode_id: int,
        language: str,
        forced: bool = False,
        hi: bool = False,
    ) -> None:
        """Lance une recherche de sous-titres pour un épisode.

        Args:
            episode_id: ID Sonarr de l'épisode
            language: Code langue ISO 639-1 (ex: "fr", "en")
            forced: Sous-titres forcés uniquement
            hi: Sous-titres pour malentendants
        """
        params = {
            "sonarrepisodeid": episode_id,
            "language": language,
            "forced": str(forced).lower(),
            "hi": str(hi).lower(),
        }
        await self._request("PATCH", "/episodes/subtitles", params=params)

    async def sync_series(self) -> None:
        """Synchronise les séries avec Sonarr."""
        await self._request(
            "PATCH",
            "/series",
            params={"action": "sync"},
        )

    async def scan_disk_series(self, series_id: int | None = None) -> None:
        """Analyse le disque pour les sous-titres de séries.

        Args:
            series_id: ID Sonarr spécifique, ou None pour tous
        """
        params: dict[str, Any] = {"action": "scan-disk"}
        if series_id is not None:
            params["seriesid"] = series_id
        await self._request("PATCH", "/series", params=params)

    async def search_wanted_episodes(self) -> None:
        """Lance une recherche de sous-titres pour tous les épisodes wanted."""
        await self._request(
            "PATCH",
            "/series",
            params={"action": "search-wanted"},
        )
