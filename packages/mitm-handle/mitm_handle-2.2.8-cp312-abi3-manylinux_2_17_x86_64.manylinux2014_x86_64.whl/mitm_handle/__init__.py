from .mitm_handle import MitmHandle

INJECT_HEAD_SLOT = "<!--g.mitm.head.inject-->"
INJECT_BODY_SLOT = "<!--g.mitm.body.inject-->"

__all__ = [
    "MitmHandle",
    "INJECT_HEAD_SLOT",
    "INJECT_BODY_SLOT",
]
