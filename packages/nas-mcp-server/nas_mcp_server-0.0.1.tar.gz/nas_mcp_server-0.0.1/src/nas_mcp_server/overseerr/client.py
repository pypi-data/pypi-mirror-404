import os
from typing import Any
import httpx


class OverseerrClient:
    """Client HTTP pour l'API Overseerr."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.base_url = (base_url or os.getenv("OVERSEERR_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("OVERSEERR_API_KEY", "")

        if not self.base_url:
            raise ValueError("OVERSEERR_URL is required")
        if not self.api_key:
            raise ValueError("OVERSEERR_API_KEY is required")

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
        """Execute une requête HTTP vers l'API Overseerr."""
        url = f"{self.base_url}/api/v1{endpoint}"

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

    async def search(self, query: str, page: int = 1) -> dict[str, Any]:
        """
        Recherche des films, séries ou personnes.
        Retourne un mix de résultats avec le type (movie, tv, person).
        """
        return await self._request(
            "GET", "/search", params={"query": query, "page": page}
        )

    async def get_person(self, person_id: int) -> dict[str, Any]:
        """
        Récupère les détails d'une personne (acteur, réalisateur, etc.)
        incluant sa filmographie complète.
        """
        return await self._request("GET", f"/person/{person_id}")

    async def get_person_combined_credits(self, person_id: int) -> dict[str, Any]:
        """
        Récupère les crédits combinés d'une personne (films + séries).
        """
        return await self._request("GET", f"/person/{person_id}/combined_credits")

    async def get_movie(self, movie_id: int) -> dict[str, Any]:
        """
        Récupère les détails d'un film par son ID TMDB.
        Inclut le statut de disponibilité (mediaInfo).
        """
        return await self._request("GET", f"/movie/{movie_id}")

    async def get_tv(self, tv_id: int) -> dict[str, Any]:
        """
        Récupère les détails d'une série par son ID TMDB.
        """
        return await self._request("GET", f"/tv/{tv_id}")

    async def request_movie(self, movie_id: int) -> dict[str, Any]:
        """
        Fait une demande pour un film (envoie à Radarr).
        """
        return await self._request(
            "POST", "/request", json_data={"mediaType": "movie", "mediaId": movie_id}
        )

    async def request_tv(
        self, tv_id: int, seasons: list[int] | None = None
    ) -> dict[str, Any]:
        """
        Fait une demande pour une série (envoie à Sonarr).
        Si seasons n'est pas spécifié, demande toutes les saisons.
        """
        data: dict[str, Any] = {"mediaType": "tv", "mediaId": tv_id}
        if seasons:
            data["seasons"] = seasons
        return await self._request("POST", "/request", json_data=data)

    async def get_status(self) -> dict[str, Any]:
        """Récupère le statut du serveur Overseerr."""
        return await self._request("GET", "/status")

    async def get_requests(
        self,
        take: int = 20,
        skip: int = 0,
        filter_status: str | None = None,
    ) -> dict[str, Any]:
        """
        Récupère la liste des demandes.

        Args:
            take: Nombre de résultats à retourner
            skip: Nombre de résultats à sauter (pagination)
            filter_status: Filtrer par statut (pending, approved, declined, available)
        """
        params: dict[str, Any] = {"take": take, "skip": skip}
        if filter_status:
            params["filter"] = filter_status
        return await self._request("GET", "/request", params=params)

    async def discover_movies(
        self,
        page: int = 1,
        genre: int | None = None,
    ) -> dict[str, Any]:
        """
        Découvre des films populaires ou par genre.
        """
        params: dict[str, Any] = {"page": page}
        if genre:
            params["genre"] = genre
        return await self._request("GET", "/discover/movies", params=params)

    async def get_movie_recommendations(self, movie_id: int) -> dict[str, Any]:
        """
        Récupère les recommandations basées sur un film.
        """
        return await self._request("GET", f"/movie/{movie_id}/recommendations")
