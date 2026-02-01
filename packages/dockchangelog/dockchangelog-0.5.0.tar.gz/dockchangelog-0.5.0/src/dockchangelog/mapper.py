"""
Map Docker images to GitHub repositories.
"""

import re
from typing import Optional

from .checker import DockerImage, ComposeService
from .config import Config


class ImageMapper:
    """Map Docker images to GitHub repository identifiers."""
    
    def __init__(self, config: Config):
        """
        Initialize mapper with configuration.
        
        Args:
            config: Configuration object with image mappings
        """
        self.config = config
        self.common_mappings = self._load_common_mappings()
    
    def _load_common_mappings(self) -> dict[str, str]:
        """
        Load common image to repo mappings.
        
        These are well-known images where the mapping isn't obvious.
        """
        return {
            # Popular self-hosted apps
            "vaultwarden/server": "dani-garcia/vaultwarden",
            "jellyfin/jellyfin": "jellyfin/jellyfin",
            "linuxserver/plex": "linuxserver/docker-plex",
            "linuxserver/sonarr": "linuxserver/docker-sonarr",
            "linuxserver/radarr": "linuxserver/docker-radarr",
            
            # Official images (no github releases usually)
            "postgres": None,
            "mysql": None,
            "redis": None,
            "nginx": None,
        }
    
    def map(self, service: ComposeService) -> Optional[str]:
        """
        Map a service to its GitHub repository.
        
        Args:
            service: ComposeService to map
        
        Returns:
            GitHub repo in format "owner/repo" or None if not found
        """
        # 1. Check explicit config mappings
        if service.image.original in self.config.image_mappings:
            return self.config.image_mappings[service.image.original]
        
        # 2. Check Docker IMAGE labels (from actual running container)
        if self.config.auto_detect_from_labels:
            # First try the actual image labels (new approach!)
            image_labels = service.get_image_labels()
            if image_labels:
                # Try various OCI label keys
                for label_key in [
                    "org.opencontainers.image.source",
                    "org.opencontainers.image.url",
                    "org.label-schema.vcs-url",
                ]:
                    source_url = image_labels.get(label_key)
                    if source_url:
                        repo = self._extract_repo_from_url(source_url)
                        if repo:
                            return repo
            
            # Fallback to compose file labels (old approach)
            source_url = service.get_source_label()
            if source_url:
                repo = self._extract_repo_from_url(source_url)
                if repo:
                    return repo
        
        # 3. Check common mappings
        if service.image.name in self.common_mappings:
            return self.common_mappings[service.image.name]
        
        # 4. Use heuristics based on registry
        return self._heuristic_mapping(service.image)
    
    def _extract_repo_from_url(self, url: str) -> Optional[str]:
        """
        Extract owner/repo from GitHub URL.
        
        Args:
            url: GitHub URL (e.g., https://github.com/owner/repo)
        
        Returns:
            "owner/repo" or None
        """
        # Handle github.com URLs
        patterns = [
            r"github\.com[:/]([^/]+/[^/]+?)(?:\.git)?$",
            r"github\.com[:/]([^/]+/[^/]+)/",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def _heuristic_mapping(self, image: DockerImage) -> Optional[str]:
        """
        Use heuristics to guess GitHub repo from image.
        
        Common patterns:
        - ghcr.io/owner/repo -> owner/repo
        - registry/owner/repo -> owner/repo (maybe)
        """
        # GHCR pattern: ghcr.io/owner/repo
        if image.registry == "ghcr.io":
            return image.name
        
        # Docker Hub pattern: owner/repo
        if image.registry is None and "/" in image.name:
            return image.name
        
        # Can't determine
        return None
