from __future__ import annotations

from collections import defaultdict
from typing import Dict, FrozenSet, Iterable, List, Tuple


def resolve_imports(
    imports: FrozenSet[Tuple[str, str]] | Iterable[Tuple[str, str]],
) -> Tuple[List[str], Dict[Tuple[str, str], str]]:
    """Resolve import collisions and generate import lines."""
    import_pairs = {pair for pair in imports if pair and pair[0] and pair[1]}

    # Filter out builtins and None modules
    filtered = [
        (module, name)
        for module, name in import_pairs
        if module not in (None, "builtins")
    ]

    name_to_modules = defaultdict(list)
    for module, name in filtered:
        name_to_modules[name].append(module)

    import_lines: List[str] = []
    name_mappings: Dict[Tuple[str, str], str] = {}

    for module, name in sorted(filtered):
        if len(name_to_modules[name]) > 1:
            alias = f"{name}_{module.split('.')[-1]}"
            import_lines.append(f"from {module} import {name} as {alias}")
            name_mappings[(module, name)] = alias
        else:
            import_lines.append(f"from {module} import {name}")
            name_mappings[(module, name)] = name

    return import_lines, name_mappings
