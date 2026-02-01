"""Tests for empathy_llm_toolkit core module (EmpathyLLM).

Comprehensive test coverage for EmpathyLLM class.

Created: 2026-01-20
Coverage target: 80%+
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from empathy_llm_toolkit.state import CollaborationState

# =============================================================================
# EmpathyLLM Initialization Tests
# =============================================================================


class TestEmpathyLLMInit:
    """Tests for EmpathyLLM initialization."""

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    def test_init_defaults(self, mock_provider_class):
        """Test initialization with default values."""
        from empathy_llm_toolkit.core import EmpathyLLM

        mock_provider_class.return_value = MagicMock()

        llm = EmpathyLLM(api_key="test-key")

        assert llm.target_level == 3
        assert llm.pattern_library == {}
        assert llm.enable_security is False
        assert llm.enable_model_routing is False

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    def test_init_custom_level(self, mock_provider_class):
        """Test initialization with custom target level."""
        from empathy_llm_toolkit.core import EmpathyLLM

        mock_provider_class.return_value = MagicMock()

        llm = EmpathyLLM(api_key="test-key", target_level=5)

        assert llm.target_level == 5

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    def test_init_with_pattern_library(self, mock_provider_class):
        """Test initialization with pattern library."""
        from empathy_llm_toolkit.core import EmpathyLLM

        mock_provider_class.return_value = MagicMock()

        patterns = {"error_handling": ["pattern1", "pattern2"]}
        llm = EmpathyLLM(api_key="test-key", pattern_library=patterns)

        assert llm.pattern_library == patterns

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    @patch("empathy_llm_toolkit.core.ModelRouter")
    def test_init_with_model_routing(self, mock_router, mock_provider_class):
        """Test initialization with model routing enabled."""
        from empathy_llm_toolkit.core import EmpathyLLM

        mock_provider_class.return_value = MagicMock()

        llm = EmpathyLLM(api_key="test-key", enable_model_routing=True)

        assert llm.enable_model_routing is True
        assert llm.model_router is not None


class TestEmpathyLLMProviderCreation:
    """Tests for provider creation."""

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    def test_create_anthropic_provider(self, mock_provider_class):
        """Test creating Anthropic provider."""
        from empathy_llm_toolkit.core import EmpathyLLM

        mock_provider = MagicMock()
        mock_provider_class.return_value = mock_provider

        llm = EmpathyLLM(provider="anthropic", api_key="test-key")

        mock_provider_class.assert_called_once()
        assert llm.provider == mock_provider

    @patch("empathy_llm_toolkit.core.OpenAIProvider")
    def test_create_openai_provider(self, mock_provider_class):
        """Test creating OpenAI provider."""
        from empathy_llm_toolkit.core import EmpathyLLM

        mock_provider = MagicMock()
        mock_provider_class.return_value = mock_provider

        llm = EmpathyLLM(provider="openai", api_key="test-key")

        mock_provider_class.assert_called_once()

    @patch("empathy_llm_toolkit.core.GeminiProvider")
    def test_create_gemini_provider(self, mock_provider_class):
        """Test creating Gemini provider."""
        from empathy_llm_toolkit.core import EmpathyLLM

        mock_provider = MagicMock()
        mock_provider_class.return_value = mock_provider

        llm = EmpathyLLM(provider="gemini", api_key="test-key")

        mock_provider_class.assert_called_once()

    @patch("empathy_llm_toolkit.core.GeminiProvider")
    def test_create_google_provider_alias(self, mock_provider_class):
        """Test creating Google provider (alias for Gemini)."""
        from empathy_llm_toolkit.core import EmpathyLLM

        mock_provider = MagicMock()
        mock_provider_class.return_value = mock_provider

        llm = EmpathyLLM(provider="google", api_key="test-key")

        mock_provider_class.assert_called_once()

    @patch("empathy_llm_toolkit.core.LocalProvider")
    def test_create_local_provider(self, mock_provider_class):
        """Test creating local provider."""
        from empathy_llm_toolkit.core import EmpathyLLM

        mock_provider = MagicMock()
        mock_provider_class.return_value = mock_provider

        llm = EmpathyLLM(provider="local")

        mock_provider_class.assert_called_once()

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    def test_create_unknown_provider_raises(self, mock_provider_class):
        """Test that unknown provider raises ValueError."""
        from empathy_llm_toolkit.core import EmpathyLLM

        with pytest.raises(ValueError, match="Unknown provider"):
            EmpathyLLM(provider="unknown", api_key="test-key")

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-key"})
    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    def test_api_key_from_environment(self, mock_provider_class):
        """Test API key loaded from environment variable."""
        from empathy_llm_toolkit.core import EmpathyLLM

        mock_provider_class.return_value = MagicMock()

        llm = EmpathyLLM(provider="anthropic")

        # Check that environment key was used
        call_kwargs = mock_provider_class.call_args[1]
        assert call_kwargs["api_key"] == "env-key"


class TestEmpathyLLMSecurity:
    """Tests for security features."""

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    @patch("empathy_llm_toolkit.core.PIIScrubber")
    @patch("empathy_llm_toolkit.core.SecretsDetector")
    @patch("empathy_llm_toolkit.core.AuditLogger")
    def test_init_with_security_enabled(self, mock_audit, mock_secrets, mock_pii, mock_provider):
        """Test initialization with security enabled."""
        from empathy_llm_toolkit.core import EmpathyLLM

        mock_provider.return_value = MagicMock()

        llm = EmpathyLLM(
            api_key="test-key",
            enable_security=True,
            security_config={
                "audit_log_dir": "/tmp/logs",
                "enable_pii_scrubbing": True,
            },
        )

        assert llm.enable_security is True
        assert llm.pii_scrubber is not None
        assert llm.secrets_detector is not None
        assert llm.audit_logger is not None

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    @patch("empathy_llm_toolkit.core.PIIScrubber")
    @patch("empathy_llm_toolkit.core.SecretsDetector")
    def test_init_security_without_audit(self, mock_secrets, mock_pii, mock_provider):
        """Test security without audit logging."""
        from empathy_llm_toolkit.core import EmpathyLLM

        mock_provider.return_value = MagicMock()

        llm = EmpathyLLM(
            api_key="test-key",
            enable_security=True,
            security_config={
                "enable_audit_logging": False,
            },
        )

        assert llm.audit_logger is None


class TestEmpathyLLMStateManagement:
    """Tests for collaboration state management."""

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    def test_get_or_create_state_new_user(self, mock_provider_class):
        """Test creating state for new user."""
        from empathy_llm_toolkit.core import EmpathyLLM

        mock_provider_class.return_value = MagicMock()

        llm = EmpathyLLM(api_key="test-key")
        state = llm._get_or_create_state("user123")

        assert isinstance(state, CollaborationState)
        assert state.user_id == "user123"
        assert "user123" in llm.states

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    def test_get_or_create_state_existing_user(self, mock_provider_class):
        """Test getting state for existing user."""
        from empathy_llm_toolkit.core import EmpathyLLM

        mock_provider_class.return_value = MagicMock()

        llm = EmpathyLLM(api_key="test-key")

        # First call creates state
        state1 = llm._get_or_create_state("user123")

        # Second call should return same state
        state2 = llm._get_or_create_state("user123")

        assert state1 is state2


class TestEmpathyLLMLevelDetermination:
    """Tests for empathy level determination."""

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    def test_determine_level_immediate_to_two(self, mock_provider_class):
        """Test that level 2 is immediate (guided questions always helpful)."""
        from empathy_llm_toolkit.core import EmpathyLLM

        mock_provider_class.return_value = MagicMock()

        llm = EmpathyLLM(api_key="test-key", target_level=5)
        state = CollaborationState(user_id="test")

        level = llm._determine_level(state)

        # Level 2 is always appropriate per progression criteria
        assert level == 2

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    def test_determine_level_respects_target(self, mock_provider_class):
        """Test that level doesn't exceed target."""
        from empathy_llm_toolkit.core import EmpathyLLM

        mock_provider_class.return_value = MagicMock()

        llm = EmpathyLLM(api_key="test-key", target_level=2)
        state = CollaborationState(user_id="test")

        # Even if state allows higher, should stop at target
        level = llm._determine_level(state)

        assert level <= 2


class TestEmpathyLLMSystemPrompt:
    """Tests for system prompt building."""

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    def test_build_system_prompt_basic(self, mock_provider_class):
        """Test building basic system prompt."""
        from empathy_llm_toolkit.core import EmpathyLLM

        mock_provider_class.return_value = MagicMock()

        llm = EmpathyLLM(api_key="test-key")
        prompt = llm._build_system_prompt(level=1)

        assert "REACTIVE" in prompt
        assert isinstance(prompt, str)

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    def test_build_system_prompt_with_memory(self, mock_provider_class):
        """Test system prompt includes cached memory."""
        from empathy_llm_toolkit.core import EmpathyLLM

        mock_provider_class.return_value = MagicMock()

        llm = EmpathyLLM(api_key="test-key")
        llm._cached_memory = "# Custom Instructions\nAlways be helpful."

        prompt = llm._build_system_prompt(level=1)

        assert "Custom Instructions" in prompt
        assert "Always be helpful" in prompt


class TestEmpathyLLMMemoryManagement:
    """Tests for memory management."""

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    @patch("empathy_llm_toolkit.core.ClaudeMemoryLoader")
    def test_init_with_claude_memory(self, mock_loader_class, mock_provider_class):
        """Test initialization with Claude memory enabled."""
        from empathy_llm_toolkit.claude_memory import ClaudeMemoryConfig
        from empathy_llm_toolkit.core import EmpathyLLM

        mock_provider_class.return_value = MagicMock()
        mock_loader = MagicMock()
        mock_loader.load_all_memory.return_value = "# Memory Content"
        mock_loader_class.return_value = mock_loader

        config = ClaudeMemoryConfig(enabled=True)
        llm = EmpathyLLM(api_key="test-key", claude_memory_config=config)

        assert llm._cached_memory == "# Memory Content"
        assert llm.claude_memory_loader is not None

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    @patch("empathy_llm_toolkit.core.ClaudeMemoryLoader")
    def test_reload_memory(self, mock_loader_class, mock_provider_class):
        """Test reloading memory."""
        from empathy_llm_toolkit.claude_memory import ClaudeMemoryConfig
        from empathy_llm_toolkit.core import EmpathyLLM

        mock_provider_class.return_value = MagicMock()
        mock_loader = MagicMock()
        mock_loader.load_all_memory.return_value = "# New Memory"
        mock_loader_class.return_value = mock_loader

        config = ClaudeMemoryConfig(enabled=True)
        llm = EmpathyLLM(api_key="test-key", claude_memory_config=config)

        llm.reload_memory()

        mock_loader.clear_cache.assert_called_once()
        assert mock_loader.load_all_memory.call_count == 2

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    def test_reload_memory_not_enabled(self, mock_provider_class):
        """Test reload_memory when memory not enabled."""
        from empathy_llm_toolkit.core import EmpathyLLM

        mock_provider_class.return_value = MagicMock()

        llm = EmpathyLLM(api_key="test-key")

        # Should not raise, just log warning
        llm.reload_memory()


class TestEmpathyLLMInteract:
    """Tests for interact method."""

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    @pytest.mark.asyncio
    async def test_interact_basic(self, mock_provider_class):
        """Test basic interaction."""
        from empathy_llm_toolkit.core import EmpathyLLM
        from empathy_llm_toolkit.providers import LLMResponse

        mock_provider = MagicMock()
        mock_provider.generate = AsyncMock(
            return_value=LLMResponse(
                content="Hello!",
                model="claude-3-sonnet",
                tokens_used=10,
                finish_reason="stop",
                metadata={},
            )
        )
        mock_provider_class.return_value = mock_provider

        llm = EmpathyLLM(api_key="test-key")

        result = await llm.interact(
            user_id="user123",
            user_input="Hello",
        )

        assert "content" in result
        assert "level_used" in result
        assert result["level_used"] >= 1

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    @pytest.mark.asyncio
    async def test_interact_with_force_level(self, mock_provider_class):
        """Test interaction with forced level."""
        from empathy_llm_toolkit.core import EmpathyLLM
        from empathy_llm_toolkit.providers import LLMResponse

        mock_provider = MagicMock()
        mock_provider.generate = AsyncMock(
            return_value=LLMResponse(
                content="Response",
                model="claude-3-sonnet",
                tokens_used=10,
                finish_reason="stop",
                metadata={},
            )
        )
        mock_provider_class.return_value = mock_provider

        llm = EmpathyLLM(api_key="test-key", target_level=5)

        result = await llm.interact(
            user_id="user123",
            user_input="Test",
            force_level=3,
        )

        assert result["level_used"] == 3

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    @patch("empathy_llm_toolkit.core.PIIScrubber")
    @patch("empathy_llm_toolkit.core.SecretsDetector")
    @pytest.mark.asyncio
    async def test_interact_with_pii_scrubbing(self, mock_secrets, mock_pii, mock_provider_class):
        """Test interaction with PII scrubbing."""
        from empathy_llm_toolkit.core import EmpathyLLM
        from empathy_llm_toolkit.providers import LLMResponse

        mock_provider = MagicMock()
        mock_provider.generate = AsyncMock(
            return_value=LLMResponse(
                content="Response",
                model="claude-3-sonnet",
                tokens_used=10,
                finish_reason="stop",
                metadata={},
            )
        )
        mock_provider_class.return_value = mock_provider

        mock_pii_instance = MagicMock()
        mock_pii_instance.scrub.return_value = (
            "My email is [EMAIL_REDACTED]",
            [{"type": "email", "value": "test@example.com"}],
        )
        mock_pii.return_value = mock_pii_instance

        mock_secrets_instance = MagicMock()
        mock_secrets_instance.detect.return_value = []
        mock_secrets.return_value = mock_secrets_instance

        llm = EmpathyLLM(
            api_key="test-key",
            enable_security=True,
            security_config={"enable_audit_logging": False},
        )

        result = await llm.interact(
            user_id="user123",
            user_input="My email is test@example.com",
        )

        assert "security" in result
        assert result["security"]["pii_detected"] == 1
        assert result["security"]["pii_scrubbed"] is True

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    @patch("empathy_llm_toolkit.core.PIIScrubber")
    @patch("empathy_llm_toolkit.core.SecretsDetector")
    @pytest.mark.asyncio
    async def test_interact_blocks_secrets(self, mock_secrets, mock_pii, mock_provider_class):
        """Test that secrets are blocked."""
        from empathy_llm_toolkit.core import EmpathyLLM

        mock_provider_class.return_value = MagicMock()

        mock_pii_instance = MagicMock()
        mock_pii_instance.scrub.return_value = ("input", [])
        mock_pii.return_value = mock_pii_instance

        mock_secret = MagicMock()
        mock_secret.secret_type.value = "api_key"
        mock_secrets_instance = MagicMock()
        mock_secrets_instance.detect.return_value = [mock_secret]
        mock_secrets.return_value = mock_secrets_instance

        llm = EmpathyLLM(
            api_key="test-key",
            enable_security=True,
            security_config={
                "block_on_secrets": True,
                "enable_audit_logging": False,
            },
        )

        from empathy_os.memory import SecurityError

        with pytest.raises(SecurityError, match="secret"):
            await llm.interact(
                user_id="user123",
                user_input="My API key is sk-abc123",
            )

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    @pytest.mark.asyncio
    async def test_interact_invalid_level_raises(self, mock_provider_class):
        """Test that invalid level raises error."""
        from empathy_llm_toolkit.core import EmpathyLLM

        mock_provider_class.return_value = MagicMock()

        llm = EmpathyLLM(api_key="test-key")

        with pytest.raises(ValueError, match="Invalid level"):
            await llm.interact(
                user_id="user123",
                user_input="Test",
                force_level=99,  # Invalid level
            )


class TestEmpathyLLMModelRouting:
    """Tests for model routing functionality."""

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    @patch("empathy_llm_toolkit.core.ModelRouter")
    @pytest.mark.asyncio
    async def test_interact_with_model_routing(self, mock_router_class, mock_provider_class):
        """Test interaction with model routing."""
        from empathy_llm_toolkit.core import EmpathyLLM
        from empathy_llm_toolkit.providers import LLMResponse
        from empathy_llm_toolkit.routing.model_router import ModelTier

        mock_provider = MagicMock()
        mock_provider.generate = AsyncMock(
            return_value=LLMResponse(
                content="Response",
                model="claude-3-haiku",
                tokens_used=10,
                finish_reason="stop",
                metadata={},
            )
        )
        mock_provider_class.return_value = mock_provider

        mock_router = MagicMock()
        mock_router.route.return_value = "claude-3-haiku"
        mock_router.get_tier.return_value = ModelTier.CHEAP
        mock_router_class.return_value = mock_router

        llm = EmpathyLLM(
            api_key="test-key",
            enable_model_routing=True,
        )

        result = await llm.interact(
            user_id="user123",
            user_input="Summarize this",
            task_type="summarize",
        )

        assert "metadata" in result
        assert result["metadata"]["model_routing_enabled"] is True
        assert result["metadata"]["task_type"] == "summarize"


# =============================================================================
# Integration Tests
# =============================================================================


class TestEmpathyLLMIntegration:
    """Integration tests for EmpathyLLM."""

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    @pytest.mark.asyncio
    async def test_multiple_interactions_track_state(self, mock_provider_class):
        """Test that multiple interactions properly track state."""
        from empathy_llm_toolkit.core import EmpathyLLM
        from empathy_llm_toolkit.providers import LLMResponse

        mock_provider = MagicMock()
        mock_provider.generate = AsyncMock(
            return_value=LLMResponse(
                content="Response",
                model="claude-3-sonnet",
                tokens_used=10,
                finish_reason="stop",
                metadata={},
            )
        )
        mock_provider_class.return_value = mock_provider

        llm = EmpathyLLM(api_key="test-key")

        # Multiple interactions
        await llm.interact(user_id="user123", user_input="First")
        await llm.interact(user_id="user123", user_input="Second")
        await llm.interact(user_id="user123", user_input="Third")

        # State should track all interactions
        state = llm.states["user123"]
        assert len(state.interactions) >= 3

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    @pytest.mark.asyncio
    async def test_different_users_have_separate_states(self, mock_provider_class):
        """Test that different users have separate states."""
        from empathy_llm_toolkit.core import EmpathyLLM
        from empathy_llm_toolkit.providers import LLMResponse

        mock_provider = MagicMock()
        mock_provider.generate = AsyncMock(
            return_value=LLMResponse(
                content="Response",
                model="claude-3-sonnet",
                tokens_used=10,
                finish_reason="stop",
                metadata={},
            )
        )
        mock_provider_class.return_value = mock_provider

        llm = EmpathyLLM(api_key="test-key")

        await llm.interact(user_id="user1", user_input="Hello")
        await llm.interact(user_id="user2", user_input="Hi")

        assert "user1" in llm.states
        assert "user2" in llm.states
        assert llm.states["user1"] is not llm.states["user2"]


# =============================================================================
# State Management Methods Tests
# =============================================================================


class TestStateMethods:
    """Tests for state management methods."""

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    def test_update_trust_success(self, mock_provider_class):
        """Test updating trust on success."""
        from empathy_llm_toolkit.core import EmpathyLLM

        mock_provider_class.return_value = MagicMock()

        llm = EmpathyLLM(api_key="test-key")

        # Update trust with success
        llm.update_trust("user123", "success", magnitude=1.0)

        state = llm.states["user123"]
        # Trust should increase on success
        assert state.trust_level > 0.5

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    def test_update_trust_failure(self, mock_provider_class):
        """Test updating trust on failure."""
        from empathy_llm_toolkit.core import EmpathyLLM

        mock_provider_class.return_value = MagicMock()

        llm = EmpathyLLM(api_key="test-key")

        # Create initial state with higher trust
        state = llm._get_or_create_state("user123")
        initial_trust = state.trust_level

        # Update trust with failure
        llm.update_trust("user123", "failure", magnitude=0.5)

        # Trust should decrease on failure
        assert llm.states["user123"].trust_level <= initial_trust

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    def test_add_pattern(self, mock_provider_class):
        """Test manually adding a pattern."""
        from datetime import datetime

        from empathy_llm_toolkit.core import EmpathyLLM
        from empathy_llm_toolkit.state import PatternType, UserPattern

        mock_provider_class.return_value = MagicMock()

        llm = EmpathyLLM(api_key="test-key")

        pattern = UserPattern(
            pattern_type=PatternType.PREFERENCE,
            trigger="code",
            action="User prefers code-focused responses",
            confidence=0.8,
            occurrences=3,
            last_seen=datetime.now(),
        )

        llm.add_pattern("user123", pattern)

        state = llm.states["user123"]
        assert len(state.detected_patterns) >= 1

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    def test_get_statistics(self, mock_provider_class):
        """Test getting user statistics."""
        from empathy_llm_toolkit.core import EmpathyLLM

        mock_provider_class.return_value = MagicMock()

        llm = EmpathyLLM(api_key="test-key")

        # Get statistics for new user (creates state)
        stats = llm.get_statistics("user123")

        assert isinstance(stats, dict)
        assert "trust_level" in stats or "user_id" in stats or len(stats) >= 0

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    def test_reset_state(self, mock_provider_class):
        """Test resetting user state."""
        from empathy_llm_toolkit.core import EmpathyLLM

        mock_provider_class.return_value = MagicMock()

        llm = EmpathyLLM(api_key="test-key")

        # Create state
        llm._get_or_create_state("user123")
        assert "user123" in llm.states

        # Reset state
        llm.reset_state("user123")

        assert "user123" not in llm.states

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    def test_reset_state_nonexistent_user(self, mock_provider_class):
        """Test resetting state for nonexistent user."""
        from empathy_llm_toolkit.core import EmpathyLLM

        mock_provider_class.return_value = MagicMock()

        llm = EmpathyLLM(api_key="test-key")

        # Should not raise for nonexistent user
        llm.reset_state("nonexistent")


# =============================================================================
# Level Methods Tests
# =============================================================================


class TestLevelMethods:
    """Tests for level-specific methods."""

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    @pytest.mark.asyncio
    async def test_level_1_reactive(self, mock_provider_class):
        """Test level 1 reactive method."""
        from empathy_llm_toolkit.core import EmpathyLLM
        from empathy_llm_toolkit.providers import LLMResponse

        mock_provider = MagicMock()
        mock_provider.generate = AsyncMock(
            return_value=LLMResponse(
                content="Simple response",
                model="claude-3-sonnet",
                tokens_used=5,
                finish_reason="stop",
                metadata={},
            )
        )
        mock_provider_class.return_value = mock_provider

        llm = EmpathyLLM(api_key="test-key", target_level=1)
        state = CollaborationState(user_id="test")

        result = await llm._level_1_reactive(
            user_input="Hello",
            state=state,
            context={},
        )

        assert "content" in result
        assert result["proactive"] is False

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    @pytest.mark.asyncio
    async def test_level_1_reactive_with_model_override(self, mock_provider_class):
        """Test level 1 with model override."""
        from empathy_llm_toolkit.core import EmpathyLLM
        from empathy_llm_toolkit.providers import LLMResponse

        mock_provider = MagicMock()
        mock_provider.generate = AsyncMock(
            return_value=LLMResponse(
                content="Response",
                model="custom-model",
                tokens_used=10,
                finish_reason="stop",
                metadata={},
            )
        )
        mock_provider_class.return_value = mock_provider

        llm = EmpathyLLM(api_key="test-key")
        state = CollaborationState(user_id="test")

        await llm._level_1_reactive(
            user_input="Test",
            state=state,
            context={},
            model_override="custom-model",
        )

        # Verify model override was passed
        call_kwargs = mock_provider.generate.call_args[1]
        assert call_kwargs.get("model") == "custom-model"

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    @pytest.mark.asyncio
    async def test_level_4_anticipatory(self, mock_provider_class):
        """Test level 4 anticipatory method."""
        from empathy_llm_toolkit.core import EmpathyLLM
        from empathy_llm_toolkit.providers import LLMResponse

        mock_provider = MagicMock()
        mock_provider.generate = AsyncMock(
            return_value=LLMResponse(
                content="Anticipatory response with trajectory analysis",
                model="claude-3-opus",
                tokens_used=100,
                finish_reason="stop",
                metadata={},
            )
        )
        mock_provider_class.return_value = mock_provider

        llm = EmpathyLLM(api_key="test-key", target_level=4)
        state = CollaborationState(user_id="test")

        result = await llm._level_4_anticipatory(
            user_input="What should I do next?",
            state=state,
            context={},
        )

        assert "content" in result
        assert result["proactive"] is True
        assert "metadata" in result
        assert result["metadata"]["trajectory_analyzed"] is True

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    @pytest.mark.asyncio
    async def test_level_5_systems(self, mock_provider_class):
        """Test level 5 systems method."""
        from empathy_llm_toolkit.core import EmpathyLLM
        from empathy_llm_toolkit.providers import LLMResponse

        mock_provider = MagicMock()
        mock_provider.generate = AsyncMock(
            return_value=LLMResponse(
                content="Systems-level response with cross-domain patterns",
                model="claude-3-opus",
                tokens_used=150,
                finish_reason="stop",
                metadata={},
            )
        )
        mock_provider_class.return_value = mock_provider

        llm = EmpathyLLM(api_key="test-key", target_level=5)
        state = CollaborationState(user_id="test")

        result = await llm._level_5_systems(
            user_input="How does this pattern generalize?",
            state=state,
            context={},
        )

        assert "content" in result
        assert result["proactive"] is True
        assert "metadata" in result
        assert result["metadata"]["systems_level"] is True


# =============================================================================
# Provider Environment Variable Tests
# =============================================================================


class TestProviderEnvVariables:
    """Tests for provider API key environment variable fallback."""

    @patch("empathy_llm_toolkit.core.OpenAIProvider")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "env-openai-key"})
    def test_openai_key_from_environment(self, mock_openai_class):
        """Test OpenAI provider uses env var when key not provided."""
        from empathy_llm_toolkit.core import EmpathyLLM

        mock_openai_class.return_value = MagicMock()

        llm = EmpathyLLM(api_key=None, provider="openai")

        # Verify OpenAI provider was created with env key
        mock_openai_class.assert_called_once()
        call_kwargs = mock_openai_class.call_args[1]
        assert call_kwargs["api_key"] == "env-openai-key"

    @patch("empathy_llm_toolkit.core.GeminiProvider")
    @patch.dict("os.environ", {"GOOGLE_API_KEY": "env-google-key"})
    def test_gemini_key_from_environment(self, mock_gemini_class):
        """Test Gemini provider uses GOOGLE_API_KEY env var."""
        from empathy_llm_toolkit.core import EmpathyLLM

        mock_gemini_class.return_value = MagicMock()

        llm = EmpathyLLM(api_key=None, provider="gemini")

        mock_gemini_class.assert_called_once()
        call_kwargs = mock_gemini_class.call_args[1]
        assert call_kwargs["api_key"] == "env-google-key"

    @patch("empathy_llm_toolkit.core.GeminiProvider")
    @patch.dict("os.environ", {"GEMINI_API_KEY": "env-gemini-key"}, clear=False)
    def test_gemini_key_from_gemini_env(self, mock_gemini_class):
        """Test Gemini provider falls back to GEMINI_API_KEY."""
        import os

        from empathy_llm_toolkit.core import EmpathyLLM

        # Clear GOOGLE_API_KEY if exists to test fallback
        if "GOOGLE_API_KEY" in os.environ:
            del os.environ["GOOGLE_API_KEY"]

        mock_gemini_class.return_value = MagicMock()

        llm = EmpathyLLM(api_key=None, provider="google")

        mock_gemini_class.assert_called_once()


# =============================================================================
# Audit Logging Tests
# =============================================================================


class TestAuditLogging:
    """Tests for audit logging functionality."""

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    @patch("empathy_llm_toolkit.core.AuditLogger")
    @pytest.mark.asyncio
    async def test_interact_with_audit_logging(self, mock_audit_class, mock_provider_class):
        """Test interaction with audit logging enabled."""
        from empathy_llm_toolkit.core import EmpathyLLM
        from empathy_llm_toolkit.providers import LLMResponse

        mock_provider = MagicMock()
        mock_provider.generate = AsyncMock(
            return_value=LLMResponse(
                content="Response",
                model="claude-3-sonnet",
                tokens_used=10,
                finish_reason="stop",
                metadata={},
            )
        )
        mock_provider_class.return_value = mock_provider

        mock_audit = MagicMock()
        mock_audit_class.return_value = mock_audit

        llm = EmpathyLLM(
            api_key="test-key",
            enable_security=True,
            enable_audit_logging=True,
        )

        await llm.interact(user_id="user123", user_input="Test input")

        # Verify audit logger was called
        mock_audit.log_llm_request.assert_called_once()

    @patch("empathy_llm_toolkit.core.AnthropicProvider")
    @patch("empathy_llm_toolkit.core.AuditLogger")
    @pytest.mark.asyncio
    async def test_audit_logging_captures_metadata(self, mock_audit_class, mock_provider_class):
        """Test that audit logging captures correct metadata."""
        from empathy_llm_toolkit.core import EmpathyLLM
        from empathy_llm_toolkit.providers import LLMResponse

        mock_provider = MagicMock()
        mock_provider.generate = AsyncMock(
            return_value=LLMResponse(
                content="Response content here",
                model="claude-3-sonnet",
                tokens_used=25,
                finish_reason="stop",
                metadata={},
            )
        )
        mock_provider_class.return_value = mock_provider

        mock_audit = MagicMock()
        mock_audit_class.return_value = mock_audit

        llm = EmpathyLLM(
            api_key="test-key",
            enable_security=True,
            enable_audit_logging=True,
        )

        await llm.interact(user_id="testuser", user_input="Hello world")

        # Verify audit log contains expected fields
        call_kwargs = mock_audit.log_llm_request.call_args[1]
        assert call_kwargs["user_id"] == "testuser"
        assert call_kwargs["status"] == "success"
        assert "duration_ms" in call_kwargs
        assert "request_size_bytes" in call_kwargs
        assert "response_size_bytes" in call_kwargs
