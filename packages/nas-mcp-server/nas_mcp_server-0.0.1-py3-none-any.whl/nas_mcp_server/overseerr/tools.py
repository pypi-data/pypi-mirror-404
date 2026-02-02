import asyncio
import json
from fastmcp import FastMCP
from .client import OverseerrClient


def register_overseerr_tools(mcp: FastMCP, client: OverseerrClient, radarr_client=None) -> None:
    """Enregistre tous les outils Overseerr sur le serveur MCP.

    Args:
        mcp: Le serveur FastMCP
        client: Le client Overseerr
        radarr_client: Client Radarr optionnel pour enrichir avec les notes IMDB
    """

    @mcp.tool()
    async def overseerr_status() -> str:
        """Récupère le statut du serveur Overseerr."""
        status = await client.get_status()
        return json.dumps(status, indent=2, ensure_ascii=False)

    @mcp.tool()
    async def overseerr_search(query: str, page: int = 1) -> str:
        """
        Recherche des films, séries ou personnes dans Overseerr/TMDB.

        Args:
            query: Le terme de recherche (titre, nom d'acteur, etc.)
            page: Numéro de page pour la pagination (défaut: 1)
        """
        results = await client.search(query, page)

        simplified = []
        for item in results.get("results", [])[:15]:
            media_type = item.get("mediaType")

            if media_type == "movie":
                simplified.append({
                    "type": "movie",
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "year": item.get("releaseDate", "")[:4] if item.get("releaseDate") else None,
                    "overview": (item.get("overview") or "")[:150] + "..." if len(item.get("overview") or "") > 150 else item.get("overview"),
                    "popularity": item.get("popularity"),
                    "status": item.get("mediaInfo", {}).get("status") if item.get("mediaInfo") else "not_requested",
                })
            elif media_type == "tv":
                simplified.append({
                    "type": "tv",
                    "id": item.get("id"),
                    "title": item.get("name"),
                    "year": item.get("firstAirDate", "")[:4] if item.get("firstAirDate") else None,
                    "overview": (item.get("overview") or "")[:150] + "..." if len(item.get("overview") or "") > 150 else item.get("overview"),
                    "popularity": item.get("popularity"),
                    "status": item.get("mediaInfo", {}).get("status") if item.get("mediaInfo") else "not_requested",
                })
            elif media_type == "person":
                simplified.append({
                    "type": "person",
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "knownFor": item.get("knownForDepartment"),
                    "popularity": item.get("popularity"),
                })

        return json.dumps({
            "totalResults": results.get("totalResults", 0),
            "page": results.get("page", 1),
            "totalPages": results.get("totalPages", 1),
            "results": simplified,
        }, indent=2, ensure_ascii=False)

    @mcp.tool()
    async def overseerr_get_person(person_id: int) -> str:
        """
        Récupère les détails d'une personne (acteur, réalisateur) et sa filmographie.

        Args:
            person_id: L'identifiant TMDB de la personne (obtenu via overseerr_search)
        """
        person = await client.get_person(person_id)

        # Extraire la filmographie des crédits
        cast_credits = person.get("credits", {}).get("cast", [])
        crew_credits = person.get("credits", {}).get("crew", [])

        # Trier par popularité
        cast_credits.sort(key=lambda x: x.get("popularity", 0), reverse=True)

        filmography = []
        for credit in cast_credits[:50]:  # Limiter à 50 films
            media_type = credit.get("mediaType", "movie")
            filmography.append({
                "type": media_type,
                "id": credit.get("id"),
                "title": credit.get("title") if media_type == "movie" else credit.get("name"),
                "year": (credit.get("releaseDate") or credit.get("firstAirDate") or "")[:4] or None,
                "character": credit.get("character"),
                "popularity": credit.get("popularity"),
                "voteAverage": credit.get("voteAverage"),
                "status": credit.get("mediaInfo", {}).get("status") if credit.get("mediaInfo") else "not_requested",
            })

        return json.dumps({
            "id": person.get("id"),
            "name": person.get("name"),
            "biography": (person.get("biography") or "")[:500] + "..." if len(person.get("biography") or "") > 500 else person.get("biography"),
            "birthday": person.get("birthday"),
            "placeOfBirth": person.get("placeOfBirth"),
            "knownForDepartment": person.get("knownForDepartment"),
            "popularity": person.get("popularity"),
            "filmographyCount": len(cast_credits),
            "filmography": filmography,
        }, indent=2, ensure_ascii=False)

    @mcp.tool()
    async def overseerr_get_movie(movie_id: int) -> str:
        """
        Récupère les détails d'un film et son statut de disponibilité.

        Args:
            movie_id: L'identifiant TMDB du film
        """
        movie = await client.get_movie(movie_id)

        media_info = movie.get("mediaInfo")
        status = "not_requested"
        if media_info:
            status_code = media_info.get("status")
            status_map = {
                1: "unknown",
                2: "pending",
                3: "processing",
                4: "partially_available",
                5: "available",
            }
            status = status_map.get(status_code, "unknown")

        return json.dumps({
            "id": movie.get("id"),
            "title": movie.get("title"),
            "originalTitle": movie.get("originalTitle"),
            "year": movie.get("releaseDate", "")[:4] if movie.get("releaseDate") else None,
            "releaseDate": movie.get("releaseDate"),
            "overview": movie.get("overview"),
            "runtime": movie.get("runtime"),
            "voteAverage": movie.get("voteAverage"),
            "voteCount": movie.get("voteCount"),
            "genres": [g.get("name") for g in movie.get("genres", [])],
            "director": next((c.get("name") for c in movie.get("credits", {}).get("crew", []) if c.get("job") == "Director"), None),
            "status": status,
            "inLibrary": status == "available",
        }, indent=2, ensure_ascii=False)

    @mcp.tool()
    async def overseerr_request_movie(movie_id: int) -> str:
        """
        Fait une demande pour ajouter un film à la bibliothèque (envoie à Radarr).

        Args:
            movie_id: L'identifiant TMDB du film à demander
        """
        # D'abord récupérer les infos du film
        movie = await client.get_movie(movie_id)
        title = movie.get("title", f"TMDB:{movie_id}")

        # Vérifier si déjà disponible
        media_info = movie.get("mediaInfo")
        if media_info and media_info.get("status") == 5:
            return f"Le film '{title}' est déjà disponible dans la bibliothèque."

        # Faire la demande
        result = await client.request_movie(movie_id)

        return json.dumps({
            "success": True,
            "message": f"Demande créée pour '{title}'",
            "requestId": result.get("id"),
            "status": result.get("status"),
        }, indent=2, ensure_ascii=False)

    @mcp.tool()
    async def overseerr_get_requests(
        take: int = 20,
        skip: int = 0,
        filter_status: str | None = None,
    ) -> str:
        """
        Récupère la liste des demandes en cours.

        Args:
            take: Nombre de résultats à retourner (défaut: 20)
            skip: Nombre de résultats à sauter pour pagination (défaut: 0)
            filter_status: Filtrer par statut: pending, approved, declined, available (optionnel)
        """
        requests = await client.get_requests(take, skip, filter_status)

        simplified = []
        for req in requests.get("results", []):
            media = req.get("media", {})
            simplified.append({
                "id": req.get("id"),
                "type": req.get("type"),
                "title": media.get("title") or media.get("name"),
                "year": (media.get("releaseDate") or media.get("firstAirDate") or "")[:4] or None,
                "status": req.get("status"),
                "requestedBy": req.get("requestedBy", {}).get("displayName"),
                "createdAt": req.get("createdAt"),
            })

        return json.dumps({
            "totalResults": requests.get("pageInfo", {}).get("results", 0),
            "requests": simplified,
        }, indent=2, ensure_ascii=False)

    @mcp.tool()
    async def overseerr_discover_movies(page: int = 1, genre: int | None = None) -> str:
        """
        Découvre des films populaires, optionnellement filtrés par genre.

        Args:
            page: Numéro de page (défaut: 1)
            genre: ID du genre TMDB (optionnel). Ex: 28=Action, 35=Comédie, 18=Drame, 27=Horreur, 878=SF
        """
        results = await client.discover_movies(page, genre)

        simplified = []
        for movie in results.get("results", [])[:20]:
            media_info = movie.get("mediaInfo")
            status = "not_requested"
            if media_info:
                status_code = media_info.get("status")
                status_map = {1: "unknown", 2: "pending", 3: "processing", 4: "partially_available", 5: "available"}
                status = status_map.get(status_code, "unknown")

            simplified.append({
                "id": movie.get("id"),
                "title": movie.get("title"),
                "year": movie.get("releaseDate", "")[:4] if movie.get("releaseDate") else None,
                "voteAverage": movie.get("voteAverage"),
                "popularity": movie.get("popularity"),
                "overview": (movie.get("overview") or "")[:150] + "..." if len(movie.get("overview") or "") > 150 else movie.get("overview"),
                "status": status,
                "inLibrary": status == "available",
            })

        return json.dumps({
            "page": results.get("page", 1),
            "totalPages": results.get("totalPages", 1),
            "totalResults": results.get("totalResults", 0),
            "results": simplified,
        }, indent=2, ensure_ascii=False)

    async def _fetch_imdb_rating(tmdb_id: int) -> tuple[int, float | None]:
        """Récupère la note IMDB d'un film via Radarr."""
        if not radarr_client:
            return tmdb_id, None
        try:
            results = await radarr_client.search_movie(f"tmdb:{tmdb_id}")
            if results:
                imdb_rating = results[0].get("ratings", {}).get("imdb", {}).get("value")
                return tmdb_id, imdb_rating
        except Exception:
            pass
        return tmdb_id, None

    @mcp.tool()
    async def overseerr_get_actor_missing_movies(person_id: int, include_imdb_ratings: bool = True) -> str:
        """
        Compare la filmographie d'un acteur avec la bibliothèque et retourne les films manquants.
        Enrichit avec les notes IMDB via Radarr si disponible.

        Args:
            person_id: L'identifiant TMDB de la personne (obtenu via overseerr_search)
            include_imdb_ratings: Inclure les notes IMDB (nécessite des requêtes Radarr supplémentaires)
        """
        person = await client.get_person(person_id)

        cast_credits = person.get("credits", {}).get("cast", [])

        # Filtrer uniquement les films (pas les séries)
        movies_only = [c for c in cast_credits if c.get("mediaType") == "movie"]

        # Trier par popularité
        movies_only.sort(key=lambda x: x.get("popularity", 0), reverse=True)

        missing = []
        available = []

        for credit in movies_only:
            media_info = credit.get("mediaInfo")
            is_available = media_info and media_info.get("status") == 5

            movie_data = {
                "id": credit.get("id"),
                "title": credit.get("title"),
                "year": (credit.get("releaseDate") or "")[:4] or None,
                "character": credit.get("character"),
                "popularity": credit.get("popularity"),
                "tmdbRating": credit.get("voteAverage"),
            }

            if is_available:
                available.append(movie_data)
            else:
                missing.append(movie_data)

        # Limiter aux top 30 manquants
        missing = missing[:30]

        # Enrichir avec les notes IMDB en parallèle si Radarr est disponible
        if include_imdb_ratings and radarr_client and missing:
            tmdb_ids = [m["id"] for m in missing]
            rating_tasks = [_fetch_imdb_rating(tmdb_id) for tmdb_id in tmdb_ids]
            ratings_results = await asyncio.gather(*rating_tasks)

            # Créer un dict tmdb_id -> imdb_rating
            imdb_ratings = {tmdb_id: rating for tmdb_id, rating in ratings_results}

            # Ajouter les notes IMDB aux films manquants
            for movie in missing:
                movie["imdbRating"] = imdb_ratings.get(movie["id"])

        return json.dumps({
            "person": {
                "id": person.get("id"),
                "name": person.get("name"),
            },
            "summary": {
                "total": len(movies_only),
                "available": len(available),
                "missing": len(missing),
            },
            "missingMovies": missing,
            "availableMovies": available[:10],  # Top 10 disponibles
        }, indent=2, ensure_ascii=False)
