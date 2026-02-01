"""
D&D 5e Core - API Client
Client for fetching data from D&D 5e API or local cache
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from urllib.request import urlopen
from urllib.error import URLError


class DndApiClient:
    """
    Client for accessing D&D 5e data from API or local files.
    """

    # Default API endpoint (can use dnd5eapi.co or local server)
    DEFAULT_API_BASE = "https://www.dnd5eapi.co/api"

    def __init__(
        self,
        api_base: Optional[str] = None,
        cache_dir: Optional[Path] = None,
        use_cache: bool = True
    ):
        """
        Initialize the API client.

        Args:
            api_base: Base URL for the API
            cache_dir: Directory to cache API responses
            use_cache: Whether to use cached data when available
        """
        self.api_base = api_base or self.DEFAULT_API_BASE
        self.cache_dir = cache_dir
        self.use_cache = use_cache

        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, endpoint: str) -> Optional[Path]:
        """Get the cache file path for an endpoint"""
        if not self.cache_dir:
            return None

        # Convert endpoint to safe filename
        filename = endpoint.replace("/", "_").replace(":", "_") + ".json"
        return self.cache_dir / filename

    def _read_cache(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Read data from cache if available"""
        if not self.use_cache:
            return None

        cache_path = self._get_cache_path(endpoint)
        if not cache_path or not cache_path.exists():
            return None

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def _write_cache(self, endpoint: str, data: Dict[str, Any]):
        """Write data to cache"""
        if not self.cache_dir:
            return

        cache_path = self._get_cache_path(endpoint)
        if not cache_path:
            return

        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except IOError:
            pass  # Silently fail on cache write errors

    def get(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """
        Fetch data from the API or cache.

        Args:
            endpoint: API endpoint (e.g., "/monsters/adult-black-dragon")

        Returns:
            JSON data as dictionary, or None if not found
        """
        # Try cache first
        cached_data = self._read_cache(endpoint)
        if cached_data is not None:
            return cached_data

        # Fetch from API
        url = f"{self.api_base}{endpoint}"

        try:
            with urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))

                # Cache the response
                self._write_cache(endpoint, data)

                return data
        except (URLError, json.JSONDecodeError, TimeoutError):
            return None

    def get_list(self, resource_type: str) -> List[Dict[str, str]]:
        """
        Get a list of resources of a given type.

        Args:
            resource_type: Type of resource (e.g., "monsters", "spells", "classes")

        Returns:
            List of resource info dictionaries with 'index', 'name', 'url'
        """
        data = self.get(f"/{resource_type}")
        if data and "results" in data:
            return data["results"]
        return []

    def get_monster(self, monster_index: str) -> Optional[Dict[str, Any]]:
        """Get monster data by index"""
        return self.get(f"/monsters/{monster_index}")

    def get_spell(self, spell_index: str) -> Optional[Dict[str, Any]]:
        """Get spell data by index"""
        return self.get(f"/spells/{spell_index}")

    def get_class(self, class_index: str) -> Optional[Dict[str, Any]]:
        """Get class data by index"""
        return self.get(f"/classes/{class_index}")

    def get_race(self, race_index: str) -> Optional[Dict[str, Any]]:
        """Get race data by index"""
        return self.get(f"/races/{race_index}")

    def get_equipment(self, equipment_index: str) -> Optional[Dict[str, Any]]:
        """Get equipment data by index"""
        return self.get(f"/equipment/{equipment_index}")

    def get_magic_item(self, item_index: str) -> Optional[Dict[str, Any]]:
        """Get magic item data by index"""
        return self.get(f"/magic-items/{item_index}")

    def search(
        self,
        resource_type: str,
        query: Optional[str] = None,
        **filters
    ) -> List[Dict[str, Any]]:
        """
        Search for resources with optional filters.

        Args:
            resource_type: Type of resource to search
            query: Search query string
            **filters: Additional filters (e.g., level=1, class="wizard")

        Returns:
            List of matching resources
        """
        all_resources = self.get_list(resource_type)

        if not query and not filters:
            return all_resources

        # Simple client-side filtering
        results = []
        for resource in all_resources:
            # Fetch full resource data for filtering
            full_data = self.get(resource.get("url", ""))
            if not full_data:
                continue

            # Apply query filter
            if query:
                query_lower = query.lower()
                name_match = query_lower in resource.get("name", "").lower()
                index_match = query_lower in resource.get("index", "").lower()
                if not (name_match or index_match):
                    continue

            # Apply additional filters
            match = True
            for key, value in filters.items():
                if key not in full_data:
                    match = False
                    break
                if full_data[key] != value:
                    match = False
                    break

            if match:
                results.append(full_data)

        return results


# Global default client instance
_default_client: Optional[DndApiClient] = None


def get_default_client() -> DndApiClient:
    """Get or create the default API client"""
    global _default_client
    if _default_client is None:
        _default_client = DndApiClient()
    return _default_client


def set_default_client(client: DndApiClient):
    """Set the default API client"""
    global _default_client
    _default_client = client

