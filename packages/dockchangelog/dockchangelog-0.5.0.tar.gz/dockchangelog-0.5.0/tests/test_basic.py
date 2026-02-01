"""
Unit tests for dockchangelog.
"""

import pytest
from pathlib import Path

from dockchangelog.checker import DockerImage
from dockchangelog.parser import ReleaseNotesParser


class TestDockerImage:
    """Test Docker image parsing."""
    
    def test_simple_image(self):
        """Test simple image name."""
        img = DockerImage("nginx:latest")
        assert img.registry is None
        assert img.name == "nginx"
        assert img.tag == "latest"
    
    def test_ghcr_image(self):
        """Test GitHub Container Registry image."""
        img = DockerImage("ghcr.io/owner/repo:v1.0.0")
        assert img.registry == "ghcr.io"
        assert img.name == "owner/repo"
        assert img.tag == "v1.0.0"
    
    def test_docker_hub_image(self):
        """Test Docker Hub image with owner."""
        img = DockerImage("owner/repo:latest")
        assert img.registry is None
        assert img.name == "owner/repo"
        assert img.tag == "latest"
    
    def test_image_without_tag(self):
        """Test image without explicit tag defaults to latest."""
        img = DockerImage("nginx")
        assert img.name == "nginx"
        assert img.tag == "latest"


class TestReleaseNotesParser:
    """Test release notes parsing."""
    
    def test_parse_features(self):
        """Test parsing feature list."""
        parser = ReleaseNotesParser()
        notes = parser.parse("""
## Features
- Added new feature A
- Added new feature B
        """)
        
        assert len(notes.features) == 2
        assert "Added new feature A" in notes.features
    
    def test_parse_fixes(self):
        """Test parsing bug fixes."""
        parser = ReleaseNotesParser()
        notes = parser.parse("""
## Bug Fixes
- Fixed bug A
- Fixed bug B
        """)
        
        assert len(notes.fixes) == 2
    
    def test_parse_breaking_changes(self):
        """Test parsing breaking changes."""
        parser = ReleaseNotesParser()
        notes = parser.parse("""
## Breaking Changes
- Removed deprecated API
        """)
        
        assert len(notes.breaking) == 1
    
    def test_heuristic_parsing(self):
        """Test heuristic parsing without structure."""
        parser = ReleaseNotesParser()
        notes = parser.parse("""
- Added new feature
- Fixed critical bug
- Updated dependencies
        """)
        
        # Should categorize items
        assert len(notes.features) > 0 or len(notes.fixes) > 0
    
    def test_empty_notes(self):
        """Test empty release notes."""
        parser = ReleaseNotesParser()
        notes = parser.parse("")
        
        assert notes.is_empty()
