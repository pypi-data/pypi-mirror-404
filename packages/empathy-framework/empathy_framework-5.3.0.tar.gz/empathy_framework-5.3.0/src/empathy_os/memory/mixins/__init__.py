"""Memory mixins for UnifiedMemory composition.

Provides modular capabilities through mixin composition pattern.

Copyright 2025 Smart AI Memory, LLC
Licensed under Fair Source 0.9
"""

from .backend_init_mixin import BackendInitMixin
from .capabilities_mixin import CapabilitiesMixin
from .handoff_mixin import HandoffAndExportMixin
from .lifecycle_mixin import LifecycleMixin
from .long_term_mixin import LongTermOperationsMixin
from .promotion_mixin import PatternPromotionMixin
from .short_term_mixin import ShortTermOperationsMixin

__all__ = [
    "BackendInitMixin",
    "CapabilitiesMixin",
    "HandoffAndExportMixin",
    "LifecycleMixin",
    "LongTermOperationsMixin",
    "PatternPromotionMixin",
    "ShortTermOperationsMixin",
]
