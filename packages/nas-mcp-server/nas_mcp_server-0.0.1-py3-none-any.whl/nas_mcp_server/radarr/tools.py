import json
from fastmcp import FastMCP
from .client import RadarrClient


def register_radarr_tools(mcp: FastMCP, client: RadarrClient) -> None:
    """Enregistre tous les outils Radarr sur le serveur MCP."""

    @mcp.tool()
    async def radarr_system_status() -> str:
        """Récupère le statut du système Radarr (version, état, etc.)."""
        status = await client.get_system_status()
        return json.dumps(status, indent=2, ensure_ascii=False)

    @mcp.tool()
    async def radarr_get_movies() -> str:
        """Liste tous les films de la bibliothèque Radarr avec leurs informations principales."""
        movies = await client.get_movies()
        simplified = []
        for m in movies:
            simplified.append({
                "id": m.get("id"),
                "title": m.get("title"),
                "year": m.get("year"),
                "tmdbId": m.get("tmdbId"),
                "monitored": m.get("monitored"),
                "hasFile": m.get("hasFile"),
                "status": m.get("status"),
                "overview": (m.get("overview") or "")[:200] + "..." if len(m.get("overview") or "") > 200 else m.get("overview", ""),
            })
        return json.dumps(simplified, indent=2, ensure_ascii=False)

    @mcp.tool()
    async def radarr_get_movie(movie_id: int) -> str:
        """
        Récupère les détails complets d'un film par son ID Radarr.

        Args:
            movie_id: L'identifiant unique du film dans Radarr
        """
        movie = await client.get_movie(movie_id)
        return json.dumps(movie, indent=2, ensure_ascii=False)

    @mcp.tool()
    async def radarr_search_movie(term: str) -> str:
        """
        Recherche un film à ajouter via TMDB. Retourne les résultats de recherche avec TMDB ID.

        Args:
            term: Le terme de recherche (titre du film)
        """
        results = await client.search_movie(term)
        simplified = []
        for r in results[:10]:
            simplified.append({
                "tmdbId": r.get("tmdbId"),
                "title": r.get("title"),
                "year": r.get("year"),
                "overview": (r.get("overview") or "")[:200] + "..." if len(r.get("overview") or "") > 200 else r.get("overview", ""),
                "ratings": r.get("ratings", {}).get("tmdb", {}).get("value"),
                "studio": r.get("studio"),
                "alreadyInLibrary": r.get("id") is not None,
            })
        return json.dumps(simplified, indent=2, ensure_ascii=False)

    @mcp.tool()
    async def radarr_add_movie(
        tmdb_id: int,
        quality_profile_id: int | None = None,
        root_folder_path: str | None = None,
        monitored: bool = True,
        search_for_movie: bool = True,
    ) -> str:
        """
        Ajoute un film à la bibliothèque Radarr.

        Args:
            tmdb_id: L'identifiant TMDB du film (obtenu via radarr_search_movie)
            quality_profile_id: L'ID du profil de qualité (optionnel, utilise le premier disponible)
            root_folder_path: Le chemin du dossier racine (optionnel, utilise le premier disponible)
            monitored: Si le film doit être surveillé pour téléchargement
            search_for_movie: Lancer une recherche immédiate après l'ajout
        """
        if quality_profile_id is None:
            profiles = await client.get_quality_profiles()
            if not profiles:
                return "Erreur: Aucun profil de qualité configuré"
            quality_profile_id = profiles[0]["id"]

        if root_folder_path is None:
            folders = await client.get_root_folders()
            if not folders:
                return "Erreur: Aucun dossier racine configuré"
            root_folder_path = folders[0]["path"]

        lookup = await client.search_movie(f"tmdb:{tmdb_id}")
        title = lookup[0]["title"] if lookup else f"TMDB:{tmdb_id}"

        movie = await client.add_movie(
            tmdb_id=tmdb_id,
            title=title,
            quality_profile_id=quality_profile_id,
            root_folder_path=root_folder_path,
            monitored=monitored,
            search_for_movie=search_for_movie,
        )
        return f"Film ajouté avec succès:\n{json.dumps({'id': movie.get('id'), 'title': movie.get('title'), 'year': movie.get('year'), 'path': movie.get('path')}, indent=2, ensure_ascii=False)}"

    @mcp.tool()
    async def radarr_delete_movie(
        movie_id: int,
        delete_files: bool = False,
        add_import_exclusion: bool = False,
    ) -> str:
        """
        Supprime un film de la bibliothèque Radarr.

        Args:
            movie_id: L'identifiant unique du film dans Radarr
            delete_files: Supprimer également les fichiers du disque
            add_import_exclusion: Ajouter à la liste d'exclusion pour éviter une réimportation
        """
        try:
            movie = await client.get_movie(movie_id)
            title = movie.get("title", f"ID:{movie_id}")
        except Exception:
            title = f"ID:{movie_id}"

        await client.delete_movie(
            movie_id=movie_id,
            delete_files=delete_files,
            add_import_exclusion=add_import_exclusion,
        )
        msg = f"Film '{title}' supprimé avec succès."
        if delete_files:
            msg += " Fichiers supprimés."
        if add_import_exclusion:
            msg += " Ajouté à la liste d'exclusion."
        return msg

    @mcp.tool()
    async def radarr_get_queue() -> str:
        """Récupère la queue de téléchargement en cours."""
        queue = await client.get_queue()
        records = queue.get("records", [])
        simplified = []
        for r in records:
            simplified.append({
                "movieId": r.get("movieId"),
                "title": r.get("title"),
                "status": r.get("status"),
                "progress": f"{r.get('sizeleft', 0) / r.get('size', 1) * 100:.1f}%" if r.get("size") else "N/A",
                "estimatedCompletionTime": r.get("estimatedCompletionTime"),
                "downloadClient": r.get("downloadClient"),
            })
        return json.dumps({
            "totalRecords": queue.get("totalRecords", 0),
            "records": simplified
        }, indent=2, ensure_ascii=False)

    @mcp.tool()
    async def radarr_get_calendar(
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> str:
        """
        Récupère le calendrier des sorties de films.

        Args:
            start_date: Date de début au format YYYY-MM-DD (optionnel)
            end_date: Date de fin au format YYYY-MM-DD (optionnel)
        """
        calendar = await client.get_calendar(start_date, end_date)
        simplified = []
        for m in calendar:
            simplified.append({
                "id": m.get("id"),
                "title": m.get("title"),
                "year": m.get("year"),
                "digitalRelease": m.get("digitalRelease"),
                "physicalRelease": m.get("physicalRelease"),
                "inCinemas": m.get("inCinemas"),
                "monitored": m.get("monitored"),
                "hasFile": m.get("hasFile"),
            })
        return json.dumps(simplified, indent=2, ensure_ascii=False)
