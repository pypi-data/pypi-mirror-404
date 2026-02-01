"""
Configuration models and loading.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel, Field


class CacheConfig(BaseModel):
    """Cache configuration."""
    
    enabled: bool = True
    ttl_hours: int = 24
    path: Path = Field(default_factory=lambda: Path.home() / ".cache" / "dockchangelog")


class OutputConfig(BaseModel):
    """Output format configuration."""
    
    format: str = "text"  # text, json, markdown
    show_summary: bool = True
    max_release_notes_lines: int = 10


class UpdateConfig(BaseModel):
    """Update mode configuration."""
    
    require_confirmation: bool = True
    protected_services: List[str] = Field(default_factory=list)
    stop_timeout: int = 10


class Config(BaseModel):
    """Main configuration."""
    
    # Image to GitHub repo mappings
    image_mappings: Dict[str, str] = Field(default_factory=dict)
    
    # Auto-detect from Docker labels
    auto_detect_from_labels: bool = True
    
    # GitHub API token (optional, increases rate limit)
    github_token: Optional[str] = None
    
    # Cache settings
    cache: CacheConfig = Field(default_factory=CacheConfig)
    
    # Output settings
    output: OutputConfig = Field(default_factory=OutputConfig)
    
    # Update settings
    update: UpdateConfig = Field(default_factory=UpdateConfig)


def load_config(config_path: Optional[Path] = None) -> Config:
    """
    Load configuration from file or use defaults.
    
    Args:
        config_path: Path to config file. If None, looks for:
            - ./config.yml
            - ~/.config/dockchangelog/config.yml
    
    Returns:
        Config object with loaded or default settings
    """
    # Try to find config file
    if config_path is None:
        possible_paths = [
            Path("config.yml"),
            Path.home() / ".config" / "dockchangelog" / "config.yml",
        ]
        for path in possible_paths:
            if path.exists():
                config_path = path
                break
    
    # Load config if found
    if config_path and config_path.exists():
        with open(config_path) as f:
            data = yaml.safe_load(f)
            
            # Handle environment variable substitution
            if "github_token" in data and isinstance(data["github_token"], str):
                if data["github_token"].startswith("${") and data["github_token"].endswith("}"):
                    env_var = data["github_token"][2:-1]
                    data["github_token"] = os.getenv(env_var)
            
            return Config(**data)
    
    # Return defaults
    return Config()


def create_example_config() -> str:
    """Create example configuration file content."""
    return """# dockchangelog configuration

# map docker images to github repositories (when auto-detection fails)
# format: "image:tag": "github-org/repo"
image_mappings:
  # example: map official nginx to its github repo
  nginx:latest: nginx/nginx
  
  # example: custom registry image
  registry.example.com/myapp:latest: myorg/myapp
  
  # example: specific service mapping
  jellyfin/jellyfin:latest: jellyfin/jellyfin

# auto-detect repos from docker image labels (recommended)
# most modern images include org.opencontainers.image.source label
auto_detect_from_labels: true

# github api token (optional, increases rate limit from 60 to 5000/hour)
# set this as environment variable: export GITHUB_TOKEN=your_token
github_token: ${GITHUB_TOKEN}

# cache settings
cache:
  enabled: true
  ttl_hours: 24  # how long to cache github api responses
  path: ~/.cache/dockchangelog

# output format
output:
  format: text  # text, json, markdown
  show_summary: true
  max_release_notes_lines: 10

# update mode settings (for interactive tagging)
update:
  require_confirmation: true
  protected_services:
    # services that require extra confirmation before update
    - database
    - postgres
    - mysql
  stop_timeout: 10
"""
