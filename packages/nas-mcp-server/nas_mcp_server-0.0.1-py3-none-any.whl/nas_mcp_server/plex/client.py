import os
from typing import Any
from xml.etree import ElementTree
import httpx


class PlexClient:
    """Client HTTP pour l'API Plex."""

    def __init__(self, base_url: str | None = None, token: str | None = None):
        self.base_url = (base_url or os.getenv("PLEX_URL", "")).rstrip("/")
        self.token = token or os.getenv("PLEX_TOKEN", "")

        if not self.base_url:
            raise ValueError("PLEX_URL is required")
        if not self.token:
            raise ValueError("PLEX_TOKEN is required")

        self.headers = {
            "X-Plex-Token": self.token,
            "Accept": "application/json",
        }

    async def _request(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute une requête HTTP vers l'API Plex."""
        url = f"{self.base_url}{endpoint}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url=url,
                headers=self.headers,
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def get_libraries(self) -> list[dict[str, Any]]:
        """Récupère toutes les bibliothèques."""
        data = await self._request("/library/sections")
        directories = data.get("MediaContainer", {}).get("Directory", [])
        return directories if isinstance(directories, list) else [directories]

    async def get_library_content(
        self,
        library_key: str,
        unwatched_only: bool = False,
        actor: str | None = None,
        director: str | None = None,
        genre: str | None = None,
        year: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Récupère le contenu d'une bibliothèque avec filtres optionnels.

        Args:
            library_key: Clé de la section de bibliothèque
            unwatched_only: Ne retourner que les médias non vus
            actor: Filtrer par nom d'acteur
            director: Filtrer par nom de réalisateur
            genre: Filtrer par genre
            year: Filtrer par année de sortie
        """
        endpoint = f"/library/sections/{library_key}/all"
        params = {"includeGuids": "1"}

        if unwatched_only:
            params["unwatched"] = "1"
        if actor:
            params["actor"] = actor
        if director:
            params["director"] = director
        if genre:
            params["genre"] = genre
        if year:
            params["year"] = str(year)

        data = await self._request(endpoint, params if params else None)
        metadata = data.get("MediaContainer", {}).get("Metadata", [])
        return metadata if isinstance(metadata, list) else [metadata] if metadata else []

    async def get_recently_added(self, limit: int = 50) -> list[dict[str, Any]]:
        """Récupère les médias récemment ajoutés."""
        data = await self._request("/library/recentlyAdded", {"X-Plex-Container-Size": limit})
        metadata = data.get("MediaContainer", {}).get("Metadata", [])
        return metadata if isinstance(metadata, list) else [metadata] if metadata else []

    async def get_on_deck(self) -> list[dict[str, Any]]:
        """Récupère les médias 'À suivre' (en cours de visionnage)."""
        data = await self._request("/library/onDeck")
        metadata = data.get("MediaContainer", {}).get("Metadata", [])
        return metadata if isinstance(metadata, list) else [metadata] if metadata else []

    async def search(
        self,
        query: str,
        search_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Recherche dans Plex.

        Args:
            query: Terme de recherche
            search_type: Type de média (movie, show, episode, artist, album, track)
        """
        params = {"query": query}
        if search_type:
            params["type"] = self._get_type_id(search_type)

        data = await self._request("/hubs/search", params)
        hubs = data.get("MediaContainer", {}).get("Hub", [])

        results = []
        for hub in (hubs if isinstance(hubs, list) else [hubs]):
            metadata = hub.get("Metadata", [])
            if metadata:
                items = metadata if isinstance(metadata, list) else [metadata]
                for item in items:
                    item["_hubType"] = hub.get("type", "unknown")
                results.extend(items if isinstance(items, list) else [items])

        return results

    async def get_metadata(self, rating_key: str) -> dict[str, Any]:
        """Récupère les métadonnées détaillées d'un média."""
        data = await self._request(f"/library/metadata/{rating_key}")
        metadata = data.get("MediaContainer", {}).get("Metadata", [])
        return metadata[0] if metadata else {}

    async def get_watch_history(self, limit: int = 100) -> list[dict[str, Any]]:
        """Récupère l'historique de visionnage."""
        data = await self._request("/status/sessions/history/all", {"X-Plex-Container-Size": limit})
        metadata = data.get("MediaContainer", {}).get("Metadata", [])
        return metadata if isinstance(metadata, list) else [metadata] if metadata else []

    async def get_active_sessions(self) -> list[dict[str, Any]]:
        """Récupère les sessions de lecture actives."""
        data = await self._request("/status/sessions")
        metadata = data.get("MediaContainer", {}).get("Metadata", [])
        return metadata if isinstance(metadata, list) else [metadata] if metadata else []

    async def get_similar(self, rating_key: str) -> list[dict[str, Any]]:
        """Récupère les médias similaires (recommandations)."""
        data = await self._request(f"/library/metadata/{rating_key}/similar")
        metadata = data.get("MediaContainer", {}).get("Metadata", [])
        return metadata if isinstance(metadata, list) else [metadata] if metadata else []

    async def get_server_info(self) -> dict[str, Any]:
        """Récupère les informations du serveur."""
        data = await self._request("/")
        return data.get("MediaContainer", {})

    def _get_type_id(self, type_name: str) -> str:
        """Convertit un nom de type en ID Plex."""
        type_map = {
            "movie": "1",
            "show": "2",
            "season": "3",
            "episode": "4",
            "artist": "8",
            "album": "9",
            "track": "10",
        }
        return type_map.get(type_name.lower(), "1")
