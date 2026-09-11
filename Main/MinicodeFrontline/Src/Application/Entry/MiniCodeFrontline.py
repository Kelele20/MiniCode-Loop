from __future__ import annotations

from Main.MinicodeFrontline.Src.Application.Dto.AppProjection import (
    ENTRY_SURFACES,
)


def entry_surface_names() -> tuple[str, ...]:
    return tuple(surface.name for surface in ENTRY_SURFACES)
