import sys
import logging
from dotenv import load_dotenv
from fastmcp import FastMCP

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("nas-mcp-server")

# Créer le serveur MCP
mcp = FastMCP("nas-mcp-server")

# Prompt guide pour l'IA
GUIDE = """
# NAS Media Server Guide

## Services disponibles

### Plex - Ta médiathèque
Utilise Plex quand l'utilisateur parle de :
- "ma bibliothèque", "mes films", "mes séries"
- "ce que j'ai", "déjà vu", "pas encore vu"
- "recommandations", "suggestions"

### Radarr - Gestionnaire de films
Utilise Radarr quand l'utilisateur veut :
- ajouter/télécharger un nouveau film
- voir les téléchargements en cours
- supprimer un film de la surveillance

### Overseerr - Découverte et demandes
Utilise Overseerr quand l'utilisateur veut :
- rechercher un acteur et voir sa filmographie
- savoir quels films d'un acteur manquent dans la bibliothèque
- découvrir des films populaires
- faire une demande de film/série

### Bazarr - Gestionnaire de sous-titres
Utilise Bazarr quand l'utilisateur parle de :
- sous-titres manquants, télécharger des sous-titres
- langues de sous-titres (français, anglais, etc.)
- providers de sous-titres (OpenSubtitles, etc.)
- synchroniser les sous-titres avec Radarr/Sonarr

### Prowlarr - Gestionnaire d'indexeurs
Utilise Prowlarr quand l'utilisateur parle de :
- indexeurs, trackers, sources de téléchargement
- rechercher sur les indexeurs
- tester les indexeurs
- statistiques des indexeurs
- applications connectées (Radarr, Sonarr, etc.)
"""

@mcp.prompt()
def nas_guide() -> str:
    """Guide d'utilisation des services NAS média."""
    return GUIDE

# Initialiser les clients (peuvent être None si non configurés)
plex_client = None
radarr_client = None
overseerr_client = None
bazarr_client = None
prowlarr_client = None

# Importer et enregistrer les outils Radarr
from .radarr import RadarrClient, register_radarr_tools
try:
    radarr_client = RadarrClient()
    register_radarr_tools(mcp, radarr_client)
    logger.info("Radarr tools registered successfully")
except ValueError as e:
    logger.warning(f"Radarr not configured: {e}")

# Importer et enregistrer les outils Plex
from .plex import PlexClient, register_plex_tools

try:
    plex_client = PlexClient()
    register_plex_tools(mcp, plex_client)
    logger.info("Plex tools registered successfully")
except ValueError as e:
    logger.warning(f"Plex not configured: {e}")

# Importer et enregistrer les outils Overseerr
from .overseerr import OverseerrClient, register_overseerr_tools

try:
    overseerr_client = OverseerrClient()
    # Passer le client Radarr pour enrichir avec les notes IMDB
    register_overseerr_tools(mcp, overseerr_client, radarr_client=radarr_client)
    logger.info("Overseerr tools registered successfully")
except ValueError as e:
    logger.warning(f"Overseerr not configured: {e}")

# Importer et enregistrer les outils Bazarr
from .bazarr import BazarrClient, register_bazarr_tools

try:
    bazarr_client = BazarrClient()
    register_bazarr_tools(mcp, bazarr_client)
    logger.info("Bazarr tools registered successfully")
except ValueError as e:
    logger.warning(f"Bazarr not configured: {e}")

# Importer et enregistrer les outils Prowlarr
from .prowlarr import ProwlarrClient, register_prowlarr_tools

try:
    prowlarr_client = ProwlarrClient()
    register_prowlarr_tools(mcp, prowlarr_client)
    logger.info("Prowlarr tools registered successfully")
except ValueError as e:
    logger.warning(f"Prowlarr not configured: {e}")

# Importer et enregistrer les outils unifiés (haut niveau)
from .unified import register_unified_tools

register_unified_tools(
    mcp,
    plex_client=plex_client,
    radarr_client=radarr_client,
    overseerr_client=overseerr_client,
    bazarr_client=bazarr_client,
    prowlarr_client=prowlarr_client,
)
logger.info("Unified tools registered successfully")


def main():
    """Point d'entrée principal."""
    logger.info("Starting NAS MCP Server")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
