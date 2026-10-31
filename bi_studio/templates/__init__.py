"""Template registry.

Every module in this folder that defines `TEMPLATE = Template(...)` is a BI Studio template.
To add one, create a new file here; nothing else needs to change.
"""
from __future__ import annotations

import importlib
import logging
import pkgutil

from ..fields import Template

logger = logging.getLogger(__name__)


def load_templates_with_errors() -> tuple[list[Template], dict[str, str]]:
    """All templates, plus {module name: error} for template files that failed to import.

    A broken template file is skipped instead of breaking the others.
    """
    found, errors = [], {}
    for mod_info in pkgutil.iter_modules(__path__):
        try:
            module = importlib.import_module(f"{__name__}.{mod_info.name}")
        except Exception as e:  # noqa: BLE001 - any error in one template must not hide the others
            logger.exception("Template %s failed to load", mod_info.name)
            errors[mod_info.name] = f"{type(e).__name__}: {e}"
            continue
        template = getattr(module, "TEMPLATE", None)
        if isinstance(template, Template):
            found.append(template)
    keys = [t.key for t in found]
    duplicates = {k for k in keys if keys.count(k) > 1}
    if duplicates:
        raise ValueError(f"Duplicate template key(s): {sorted(duplicates)}")
    return sorted(found, key=lambda t: (t.order, t.name)), errors


def load_templates() -> list[Template]:
    return load_templates_with_errors()[0]
