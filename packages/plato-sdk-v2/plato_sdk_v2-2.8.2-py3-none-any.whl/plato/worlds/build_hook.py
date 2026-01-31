"""Hatch build hook for Plato worlds - generates schema.json from get_schema().

Usage in world package pyproject.toml:

    [build-system]
    requires = ["hatchling", "plato-sdk-v2"]
    build-backend = "hatchling.build"

    [tool.hatch.build.hooks.custom]
    path = "plato.worlds.build_hook"

This hook will:
1. Find the world class decorated with @register_world
2. Call its get_schema() method
3. Write schema.json to the package directory
4. Include it in the wheel
"""

import json
import sys
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class WorldSchemaHook(BuildHookInterface):
    """Generate schema.json during build by calling the world's get_schema()."""

    PLUGIN_NAME = "world-schema"

    def initialize(self, version: str, build_data: dict) -> None:
        """Generate schema.json before building."""
        # Find the source directory
        src_path = Path(self.root) / "src"
        if not src_path.exists():
            src_path = Path(self.root)

        # Add to path so we can import
        sys.path.insert(0, str(src_path))

        try:
            # Find the world module by looking for packages
            module_name = self._find_module_name(src_path)
            if not module_name:
                print("Warning: Could not determine module name for schema generation")
                return

            # Import the module to trigger @register_world decorator
            __import__(module_name)

            # Get registered worlds
            from plato.worlds.base import _WORLD_REGISTRY

            if not _WORLD_REGISTRY:
                print(f"Warning: No worlds registered after importing {module_name}")
                return

            # Get the first registered world
            world_name, world_cls = next(iter(_WORLD_REGISTRY.items()))
            schema = world_cls.get_schema()

            # Find the module directory
            module_dir = src_path / module_name
            if not module_dir.exists():
                # Module might be directly in src_path
                for item in src_path.iterdir():
                    if item.is_dir() and (item / "__init__.py").exists():
                        module_dir = item
                        module_name = item.name
                        break

            # Write schema.json
            schema_path = module_dir / "schema.json"
            schema_path.write_text(json.dumps(schema, indent=2))

            # Include schema.json in the wheel
            build_data.setdefault("force_include", {})
            build_data["force_include"][str(schema_path)] = f"{module_name}/schema.json"

            props = schema.get("properties", {})
            print(f"Generated schema.json: {len(props)} properties ({', '.join(props.keys())})")

        except Exception as e:
            print(f"Warning: Could not generate schema.json: {e}")
        finally:
            if str(src_path) in sys.path:
                sys.path.remove(str(src_path))

    def _find_module_name(self, src_path: Path) -> str | None:
        """Find the Python module name in the source directory."""
        # Look for directories with __init__.py
        for item in src_path.iterdir():
            if item.is_dir() and (item / "__init__.py").exists():
                # Skip common non-module directories
                if item.name not in ("tests", "test", "__pycache__"):
                    return item.name

        return None
