"""
Agent integration helpers for dnd_5e_core

This module provides a small, stable surface that agentic systems can call to
initialize the package for fast lookup, load collections, and obtain JSON-serializable
responses suitable for LM agents.

The API is intentionally small and dependency-free to make it easy to call from
external orchestrators or agents.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, Optional

from .data import (
    set_collections_directory,
    get_collections_directory,
    get_monsters_list,
    get_collection_item,
)


@dataclass
class AgentContext:
    """Context object returned by init_for_agent.

    Attributes:
        collections_dir: Path where collections JSON files are located.
        monster_index_map: Mapping lowercase monster name -> index slug (for quick lookup).
    """

    collections_dir: Path
    monster_index_map: Dict[str, str]


def init_for_agent(config: Optional[Dict[str, Any]] = None) -> AgentContext:
    """Initialise le package pour une utilisation agentique.

    Args:
        config: Optional dict. Supported keys:
            - "collections_dir": str|Path explicit path to the collections/ folder.

    Returns:
        AgentContext instance with precomputed lookup maps.
    """
    if config is None:
        config = {}

    if "collections_dir" in config and config["collections_dir"]:
        set_collections_directory(str(config["collections_dir"]))

    collections_dir = get_collections_directory()

    # Build simple name->index map for monsters to allow name lookup by agents
    monster_map: Dict[str, str] = {}
    try:
        monster_indexes = get_monsters_list(with_url=True)
        for idx, url in monster_indexes:
            # idx is the slug, try to get full item to discover name
            item = get_collection_item("monsters", idx)
            if item and "name" in item:
                monster_map[item["name"].lower()] = idx
            else:
                monster_map[idx.lower()] = idx
    except Exception:
        # If collections are missing or malformed, return empty index map but keep going
        monster_map = {}

    return AgentContext(collections_dir=collections_dir, monster_index_map=monster_map)


def serialize_for_agent(obj: Any) -> Any:
    """Return a JSON-serializable representation of common objects.

    Currently supports: AgentContext (dataclass), dict-like objects returned from
    collection loaders. For unknown objects it falls back to asdict() when possible or
    str(). The goal is to provide simple, predictable outputs to LMs/agents.
    """
    if obj is None:
        return None

    # Dataclasses
    try:
        return asdict(obj)
    except Exception:
        pass

    # If it's already JSON serializable (dict/list/str/int/float/bool)
    if isinstance(obj, (dict, list, str, int, float, bool)):
        return obj

    # Fallback: try to convert to dict-like via __dict__
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}

    return str(obj)


def get_monster_by_name(ctx: AgentContext, name: str) -> Optional[Dict[str, Any]]:
    """Lookup a monster by (case-insensitive) name and return the collection item dict.

    Args:
        ctx: AgentContext from init_for_agent
        name: Monster name (e.g., "Goblin")

    Returns:
        The collection item (dict with index, name, url) or None if not found.
    """
    if not ctx or not name:
        return None

    key = name.lower()
    idx = ctx.monster_index_map.get(key)
    if not idx:
        # Try to search by scanning all results as a final fallback
        try:
            indexes = get_monsters_list(with_url=True)
            for slug, _url in indexes:
                item = get_collection_item("monsters", slug)
                if item and item.get("name", "").lower() == key:
                    return item
        except Exception:
            return None
        return None

    return get_collection_item("monsters", idx)
