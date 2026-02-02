import json
from fastmcp import FastMCP
from .client import ProwlarrClient


def register_prowlarr_tools(mcp: FastMCP, client: ProwlarrClient) -> None:
    """Enregistre tous les outils Prowlarr sur le serveur MCP."""

    @mcp.tool()
    async def prowlarr_system_status() -> str:
        """Récupère le statut du système Prowlarr (version, état, etc.)."""
        status = await client.get_system_status()
        return json.dumps(status, indent=2, ensure_ascii=False)

    @mcp.tool()
    async def prowlarr_get_health() -> str:
        """Récupère les problèmes de santé détectés par Prowlarr."""
        health = await client.get_health()
        if not health:
            return json.dumps({"status": "ok", "message": "Aucun problème détecté"}, indent=2, ensure_ascii=False)
        return json.dumps(health, indent=2, ensure_ascii=False)

    @mcp.tool()
    async def prowlarr_get_indexers() -> str:
        """Liste tous les indexeurs configurés dans Prowlarr."""
        indexers = await client.get_indexers()
        simplified = []
        for idx in indexers:
            simplified.append({
                "id": idx.get("id"),
                "name": idx.get("name"),
                "protocol": idx.get("protocol"),
                "privacy": idx.get("privacy"),
                "enable": idx.get("enable"),
                "priority": idx.get("priority"),
                "appProfileId": idx.get("appProfileId"),
            })
        return json.dumps(simplified, indent=2, ensure_ascii=False)

    @mcp.tool()
    async def prowlarr_get_indexer(indexer_id: int) -> str:
        """
        Récupère les détails complets d'un indexeur par son ID.

        Args:
            indexer_id: L'identifiant unique de l'indexeur dans Prowlarr
        """
        indexer = await client.get_indexer(indexer_id)
        return json.dumps(indexer, indent=2, ensure_ascii=False)

    @mcp.tool()
    async def prowlarr_test_indexer(indexer_id: int) -> str:
        """
        Teste la connexion à un indexeur spécifique.

        Args:
            indexer_id: L'identifiant unique de l'indexeur à tester
        """
        try:
            indexer = await client.get_indexer(indexer_id)
            name = indexer.get("name", f"ID:{indexer_id}")
            await client.test_indexer(indexer_id)
            return json.dumps({
                "status": "ok",
                "indexer": name,
                "message": f"L'indexeur '{name}' fonctionne correctement"
            }, indent=2, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                "status": "error",
                "indexer_id": indexer_id,
                "message": f"Erreur lors du test: {str(e)}"
            }, indent=2, ensure_ascii=False)

    @mcp.tool()
    async def prowlarr_test_all_indexers() -> str:
        """Teste tous les indexeurs configurés."""
        try:
            results = await client.test_all_indexers()
            return json.dumps(results, indent=2, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Erreur lors du test: {str(e)}"
            }, indent=2, ensure_ascii=False)

    @mcp.tool()
    async def prowlarr_search(
        query: str,
        indexer_ids: list[int] | None = None,
        categories: list[int] | None = None,
        limit: int = 50,
    ) -> str:
        """
        Recherche du contenu sur les indexeurs configurés.

        Args:
            query: Le terme de recherche
            indexer_ids: Liste des IDs d'indexeurs à utiliser (optionnel, tous par défaut)
            categories: Liste des catégories à rechercher (optionnel). Ex: 2000=Films, 5000=TV
            limit: Nombre maximum de résultats (défaut: 50)
        """
        results = await client.search(
            query=query,
            indexer_ids=indexer_ids,
            categories=categories,
            limit=limit,
        )
        simplified = []
        for r in results:
            simplified.append({
                "title": r.get("title"),
                "indexer": r.get("indexer"),
                "size": _format_size(r.get("size", 0)),
                "seeders": r.get("seeders"),
                "leechers": r.get("leechers"),
                "publishDate": r.get("publishDate"),
                "categories": [c.get("name") for c in r.get("categories", [])],
                "downloadUrl": r.get("downloadUrl"),
                "infoUrl": r.get("infoUrl"),
            })
        return json.dumps({
            "total": len(simplified),
            "results": simplified
        }, indent=2, ensure_ascii=False)

    @mcp.tool()
    async def prowlarr_get_stats(
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> str:
        """
        Récupère les statistiques des indexeurs.

        Args:
            start_date: Date de début au format YYYY-MM-DD (optionnel)
            end_date: Date de fin au format YYYY-MM-DD (optionnel)
        """
        stats = await client.get_indexer_stats(start_date, end_date)
        return json.dumps(stats, indent=2, ensure_ascii=False)

    @mcp.tool()
    async def prowlarr_get_applications() -> str:
        """Liste les applications connectées à Prowlarr (Radarr, Sonarr, etc.)."""
        apps = await client.get_applications()
        simplified = []
        for app in apps:
            simplified.append({
                "id": app.get("id"),
                "name": app.get("name"),
                "implementation": app.get("implementation"),
                "syncLevel": app.get("syncLevel"),
                "tags": app.get("tags", []),
            })
        return json.dumps(simplified, indent=2, ensure_ascii=False)

    @mcp.tool()
    async def prowlarr_get_history(limit: int = 20) -> str:
        """
        Récupère l'historique des recherches effectuées.

        Args:
            limit: Nombre maximum de résultats (défaut: 20)
        """
        history = await client.get_history(page=1, page_size=limit)
        records = history.get("records", [])
        simplified = []
        for r in records:
            simplified.append({
                "date": r.get("date"),
                "eventType": r.get("eventType"),
                "indexer": r.get("data", {}).get("indexer"),
                "query": r.get("data", {}).get("query"),
                "successful": r.get("successful"),
            })
        return json.dumps({
            "totalRecords": history.get("totalRecords", 0),
            "records": simplified
        }, indent=2, ensure_ascii=False)


def _format_size(size_bytes: int) -> str:
    """Formate une taille en bytes en format lisible."""
    if size_bytes == 0:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"
