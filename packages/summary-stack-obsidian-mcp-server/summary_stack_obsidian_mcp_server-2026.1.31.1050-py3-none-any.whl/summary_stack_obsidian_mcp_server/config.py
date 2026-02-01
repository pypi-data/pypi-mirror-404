"""Configuration loading for the MCP server."""

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class Config(BaseModel):
    """MCP server configuration."""

    api_url: str = Field(default="http://localhost:8019", description="Summary Stack API URL")
    api_key: str = Field(default="", description="API key for authentication")
    vault_root_path: str = Field(description="Absolute path to Obsidian vault root")
    target_relative_folder: str = Field(default="", description="Relative path from vault root where notes are saved")


def _load_from_env() -> Config | None:
    """Load configuration from environment variables.

    Required env vars:
        SUMMARY_STACK_API_URL: API base URL
        SUMMARY_STACK_OBSIDIAN_LOCAL_VAULT_ROOT_PATH: Absolute path to Obsidian vault root

    Optional env vars:
        SUMMARY_STACK_API_KEY: API key for authentication
        SUMMARY_STACK_TARGET_RELATIVE_FOLDER: Relative path from vault root

    Returns:
        Config if required env vars are set, None otherwise
    """
    api_url = os.environ.get("SUMMARY_STACK_API_URL")
    vault_root = os.environ.get("SUMMARY_STACK_OBSIDIAN_LOCAL_VAULT_ROOT_PATH")

    if not api_url or not vault_root:
        return None

    return Config(
        api_url=api_url,
        api_key=os.environ.get("SUMMARY_STACK_API_KEY", ""),
        vault_root_path=vault_root,
        target_relative_folder=os.environ.get("SUMMARY_STACK_TARGET_RELATIVE_FOLDER", ""),
    )


def _get_config_path() -> Path:
    """Get the configuration file path.

    Checks in order:
    1. SUMMARY_STACK_OBSIDIAN_CONFIG env var
    2. ~/.config/summary-stack-obsidian-mcp/config.yaml

    Returns:
        Path to config file
    """
    if env_path := os.environ.get("SUMMARY_STACK_OBSIDIAN_CONFIG"):
        return Path(env_path)
    return Path.home() / ".config" / "summary-stack-obsidian-mcp" / "config.yaml"


def _load_from_file() -> Config:
    """Load configuration from YAML file.

    Returns:
        Config object with loaded settings

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    config_path = _get_config_path()

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}. Either set SUMMARY_STACK_API_URL and SUMMARY_STACK_OBSIDIAN_LOCAL_VAULT_ROOT_PATH env vars, or create a config file.")

    with open(config_path) as f:
        data = yaml.safe_load(f)

    return Config.model_validate(data)


def load_config() -> Config:
    """Load configuration from environment variables or file.

    Priority:
    1. Environment variables (if SUMMARY_STACK_API_URL and SUMMARY_STACK_OBSIDIAN_LOCAL_VAULT_ROOT_PATH are set)
    2. YAML config file

    Returns:
        Config object with loaded settings
    """
    # Try env vars first
    if config := _load_from_env():
        return config

    # Fall back to file
    return _load_from_file()
