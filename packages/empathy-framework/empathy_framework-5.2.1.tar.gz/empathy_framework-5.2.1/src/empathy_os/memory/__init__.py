"""Empathy Framework Memory Module

Unified two-tier memory system for AI agent collaboration:

SHORT-TERM MEMORY (Redis):
    - Agent coordination and working memory
    - TTL-based automatic expiration (5 min - 7 days)
    - Role-based access control (Observer → Steward)
    - Pattern staging before validation

LONG-TERM MEMORY (Persistent):
    - Cross-session pattern storage
    - Classification-based access (PUBLIC/INTERNAL/SENSITIVE)
    - PII scrubbing and secrets detection
    - AES-256-GCM encryption for SENSITIVE patterns
    - Compliance: GDPR, HIPAA, SOC2

RECOMMENDED USAGE (Unified API):
    from empathy_os.memory import UnifiedMemory

    # Initialize with environment auto-detection
    memory = UnifiedMemory(user_id="agent@company.com")

    # Short-term operations
    memory.stash("working_data", {"key": "value"})
    data = memory.retrieve("working_data")

    # Long-term operations
    result = memory.persist_pattern(
        content="Algorithm for X",
        pattern_type="algorithm",
    )
    pattern = memory.recall_pattern(result["pattern_id"])

    # Pattern promotion (short-term → long-term)
    staged_id = memory.stage_pattern({"content": "..."})
    memory.promote_pattern(staged_id)

ADVANCED USAGE (Direct Access):
    from empathy_os.memory import (
        # Short-term (Redis)
        RedisShortTermMemory,
        AccessTier,
        get_redis_memory,

        # Long-term (Persistent)
        SecureMemDocsIntegration,
        Classification,

        # Security
        PIIScrubber,
        SecretsDetector,
        AuditLogger,
    )

Copyright 2025 Smart AI Memory, LLC
Licensed under Fair Source 0.9
"""

# Short-term memory (Redis)
# Claude Memory integration
from .claude_memory import ClaudeMemoryConfig, ClaudeMemoryLoader

# Memory configuration
from .config import check_redis_connection, get_railway_redis, get_redis_config, get_redis_memory

# Control Panel
from .control_panel import ControlPanelConfig, MemoryControlPanel, MemoryStats

# Cross-session communication
from .cross_session import (
    BackgroundService,
    ConflictResult,
    ConflictStrategy,
    CrossSessionCoordinator,
    SessionInfo,
    SessionType,
    check_redis_cross_session_support,
    generate_agent_id,
)

# Memory Graph (Cross-Workflow Intelligence)
from .edges import REVERSE_EDGE_TYPES, WORKFLOW_EDGE_PATTERNS, Edge, EdgeType

# File-based session memory (always available, no Redis required)
from .file_session import FileSessionConfig, FileSessionMemory, get_file_session_memory
from .graph import MemoryGraph

# Long-term memory (Persistent patterns)
from .long_term import (
    Classification,
    ClassificationRules,
    EncryptionManager,
    MemDocsStorage,
    PatternMetadata,
    SecureMemDocsIntegration,
    SecurePattern,
    SecurityError,
)
from .long_term import PermissionError as MemoryPermissionError
from .nodes import BugNode, Node, NodeType, PatternNode, PerformanceNode, VulnerabilityNode

# Redis Bootstrap
from .redis_bootstrap import (
    RedisStartMethod,
    RedisStatus,
    ensure_redis,
    get_redis_or_mock,
    stop_redis,
)

# Security components
from .security import (  # Audit Logging; PII Scrubbing; Secrets Detection
    AuditEvent,
    AuditLogger,
    PIIDetection,
    PIIPattern,
    PIIScrubber,
    SecretDetection,
    SecretsDetector,
    SecretType,
    SecurityViolation,
    Severity,
    detect_secrets,
)
from .short_term import RedisShortTermMemory

# Conversation Summary Index
from .summary_index import AgentContext, ConversationSummaryIndex

# Types (extracted to types.py for cleaner separation)
from .types import (
    AccessTier,
    AgentCredentials,
    ConflictContext,
    PaginatedResult,
    RedisConfig,
    RedisMetrics,
    StagedPattern,
    TimeWindowQuery,
    TTLStrategy,
)
from .types import SecurityError as ShortTermSecurityError

# Unified memory interface
from .unified import Environment, MemoryConfig, UnifiedMemory

__all__ = [
    "REVERSE_EDGE_TYPES",
    "WORKFLOW_EDGE_PATTERNS",
    "AccessTier",
    "AgentContext",
    "AgentCredentials",
    "AuditEvent",
    # Security - Audit
    "AuditLogger",
    # Cross-session communication
    "BackgroundService",
    "BugNode",
    "Classification",
    "ClassificationRules",
    # Claude Memory
    "ClaudeMemoryConfig",
    "ClaudeMemoryLoader",
    # File Session Memory (always available)
    "FileSessionConfig",
    "FileSessionMemory",
    "get_file_session_memory",
    "ConflictContext",
    "ConflictResult",
    "ConflictStrategy",
    "ControlPanelConfig",
    # Conversation Summary Index
    "ConversationSummaryIndex",
    "CrossSessionCoordinator",
    "Edge",
    "EdgeType",
    "EncryptionManager",
    "Environment",
    "MemDocsStorage",
    "MemoryConfig",
    # Control Panel
    "MemoryControlPanel",
    # Memory Graph (Cross-Workflow Intelligence)
    "MemoryGraph",
    "MemoryPermissionError",
    "MemoryStats",
    "Node",
    "NodeType",
    # Pagination and Query Types
    "PaginatedResult",
    "PIIDetection",
    "PIIPattern",
    # Security - PII
    "PIIScrubber",
    "PatternMetadata",
    "PatternNode",
    "PerformanceNode",
    # Redis Configuration and Metrics
    "RedisConfig",
    "RedisMetrics",
    # Short-term Memory
    "RedisShortTermMemory",
    "RedisStartMethod",
    "RedisStatus",
    "SecretDetection",
    "SecretType",
    # Security - Secrets
    "SecretsDetector",
    # Long-term Memory
    "SecureMemDocsIntegration",
    "SecurePattern",
    "SecurityError",
    "SecurityViolation",
    "SessionInfo",
    "SessionType",
    "Severity",
    "ShortTermSecurityError",
    "StagedPattern",
    "TTLStrategy",
    "TimeWindowQuery",
    # Unified Memory Interface (recommended)
    "UnifiedMemory",
    "VulnerabilityNode",
    "check_redis_connection",
    "check_redis_cross_session_support",
    "detect_secrets",
    # Redis Bootstrap
    "ensure_redis",
    "generate_agent_id",
    "get_railway_redis",
    "get_redis_config",
    # Configuration
    "get_redis_memory",
    "get_redis_or_mock",
    "stop_redis",
]
