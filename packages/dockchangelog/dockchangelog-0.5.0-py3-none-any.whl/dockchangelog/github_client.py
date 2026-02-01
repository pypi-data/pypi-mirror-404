"""
GitHub API client for fetching releases and release notes.
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import json

import httpx


class Release:
    """Represents a GitHub release."""
    
    def __init__(self, data: dict):
        """Initialize from GitHub API response."""
        self.tag = data.get("tag_name", "")
        self.name = data.get("name", "")
        self.body = data.get("body", "")
        self.published_at = data.get("published_at", "")
        self.html_url = data.get("html_url", "")
        self.prerelease = data.get("prerelease", False)
        self.draft = data.get("draft", False)
    
    def get_version(self) -> str:
        """Get clean version string."""
        # Remove 'v' prefix if present
        version = self.tag
        if version.startswith("v"):
            version = version[1:]
        return version
    
    def get_published_date(self) -> Optional[datetime]:
        """Parse published date."""
        try:
            return datetime.fromisoformat(self.published_at.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None


class GitHubClient:
    """Client for GitHub API."""
    
    def __init__(self, token: Optional[str] = None, cache_dir: Optional[Path] = None):
        """
        Initialize GitHub client.
        
        Args:
            token: GitHub API token (optional, increases rate limit)
            cache_dir: Directory for caching responses
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.cache_dir = cache_dir or Path.home() / ".cache" / "dockchangelog"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup httpx client
        headers = {"Accept": "application/vnd.github+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        self.client = httpx.Client(
            headers=headers,
            timeout=30.0,
            follow_redirects=True,
        )
    
    def get_latest_release(self, repo: str, include_prerelease: bool = False) -> Optional[Release]:
        """
        Get the latest release for a repository.
        
        Args:
            repo: Repository in format "owner/repo"
            include_prerelease: Whether to include pre-releases
        
        Returns:
            Release object or None if not found
        """
        # Check cache first
        cached = self._get_from_cache(repo)
        if cached:
            return Release(cached)
        
        try:
            # Try /releases/latest endpoint first (excludes prereleases)
            if not include_prerelease:
                url = f"https://api.github.com/repos/{repo}/releases/latest"
                response = self.client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    self._save_to_cache(repo, data)
                    return Release(data)
            
            # Fall back to getting all releases and finding latest
            url = f"https://api.github.com/repos/{repo}/releases"
            response = self.client.get(url, params={"per_page": 10})
            
            if response.status_code == 200:
                releases = response.json()
                
                # Filter out drafts and optionally prereleases
                valid_releases = [
                    r for r in releases
                    if not r.get("draft") and (include_prerelease or not r.get("prerelease"))
                ]
                
                if valid_releases:
                    latest = valid_releases[0]
                    self._save_to_cache(repo, latest)
                    return Release(latest)
            
            return None
        
        except (httpx.HTTPError, httpx.TimeoutException):
            return None
    
    def _get_cache_path(self, repo: str) -> Path:
        """Get cache file path for a repo."""
        # Replace / with _ for filename
        filename = repo.replace("/", "_") + ".json"
        return self.cache_dir / filename
    
    def _get_from_cache(self, repo: str) -> Optional[dict]:
        """Get release from cache if available and fresh."""
        cache_file = self._get_cache_path(repo)
        
        if not cache_file.exists():
            return None
        
        try:
            # Check if cache is fresh (less than 24 hours old)
            mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if datetime.now() - mtime > timedelta(hours=24):
                return None
            
            with open(cache_file) as f:
                return json.load(f)
        
        except (json.JSONDecodeError, OSError):
            return None
    
    def _save_to_cache(self, repo: str, data: dict):
        """Save release data to cache."""
        cache_file = self._get_cache_path(repo)
        
        try:
            with open(cache_file, "w") as f:
                json.dump(data, f)
        except OSError:
            # Ignore cache errors
            pass
    
    def __del__(self):
        """Clean up client."""
        if hasattr(self, "client"):
            self.client.close()
