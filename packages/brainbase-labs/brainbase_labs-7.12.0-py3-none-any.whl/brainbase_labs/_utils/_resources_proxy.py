from __future__ import annotations

from typing import Any
from typing_extensions import override

from ._proxy import LazyProxy


class ResourcesProxy(LazyProxy[Any]):
    """A proxy for the `brainbase_labs.resources` module.

    This is used so that we can lazily import `brainbase_labs.resources` only when
    needed *and* so that users can just import `brainbase_labs` and reference `brainbase_labs.resources`
    """

    @override
    def __load__(self) -> Any:
        import importlib

        mod = importlib.import_module("brainbase_labs.resources")
        return mod


resources = ResourcesProxy().__as_proxied__()
