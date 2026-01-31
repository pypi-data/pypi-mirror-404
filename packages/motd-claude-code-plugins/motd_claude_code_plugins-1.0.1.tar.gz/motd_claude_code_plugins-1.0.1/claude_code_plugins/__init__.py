"""
Claude Code Plugins Package

This package contains bundled plugins for Claude Code including:
- Agent SDK development tools
- PR review toolkit
- Commit workflows
- And many more developer productivity tools

See https://code.claude.com/docs for more information.
"""

__version__ = "1.0.0"
__author__ = "Anthropic"
__email__ = "support@anthropic.com"

from pathlib import Path

# Get the package directory
PACKAGE_DIR = Path(__file__).parent.parent

# Paths to important directories
CLAUDE_PLUGIN_DIR = PACKAGE_DIR / ".claude-plugin"
PLUGINS_DIR = PACKAGE_DIR / "plugins"

def get_marketplace_json_path():
    """Returns the path to the marketplace.json file."""
    return CLAUDE_PLUGIN_DIR / "marketplace.json"

def get_plugins_dir():
    """Returns the path to the plugins directory."""
    return PLUGINS_DIR

def list_available_plugins():
    """Returns a list of available plugin names."""
    if not PLUGINS_DIR.exists():
        return []
    return [p.name for p in PLUGINS_DIR.iterdir() if p.is_dir() and not p.name.startswith('.')]

__all__ = [
    '__version__',
    'PACKAGE_DIR',
    'CLAUDE_PLUGIN_DIR',
    'PLUGINS_DIR',
    'get_marketplace_json_path',
    'get_plugins_dir',
    'list_available_plugins',
]
