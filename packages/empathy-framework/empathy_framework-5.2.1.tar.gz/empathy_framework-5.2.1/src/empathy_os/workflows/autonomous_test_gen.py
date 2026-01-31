"""Autonomous Test Generation with Dashboard Integration - Enhanced Edition.

Generates behavioral tests with real-time monitoring via Agent Coordination Dashboard.

ENHANCEMENTS (Phase 1):
- Extended thinking mode for better test planning
- Prompt caching for 90% cost reduction
- Full source code (no truncation)
- Workflow-specific prompts with mocking templates
- Few-shot learning with examples

ENHANCEMENTS (Phase 2 - Multi-Turn Refinement):
- Iterative test generation with validation loop
- Automatic failure detection and fixing
- Conversation history for context preservation

ENHANCEMENTS (Phase 3 - Coverage-Guided Generation):
- Coverage analysis integration
- Iterative coverage improvement targeting uncovered lines
- Systematic path to 80%+ coverage

Copyright 2026 Smart-AI-Memory
Licensed under Apache 2.0
"""

import json
import logging
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from empathy_os.memory.short_term import RedisShortTermMemory
from empathy_os.telemetry.agent_tracking import HeartbeatCoordinator
from empathy_os.telemetry.event_streaming import EventStreamer
from empathy_os.telemetry.feedback_loop import FeedbackLoop

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of pytest validation."""
    passed: bool
    failures: str
    error_count: int
    output: str


@dataclass
class CoverageResult:
    """Result of coverage analysis."""
    coverage: float
    missing_lines: list[int]
    total_statements: int
    covered_statements: int


class AutonomousTestGenerator:
    """Generate tests autonomously with dashboard monitoring and Anthropic best practices."""

    def __init__(
        self,
        agent_id: str,
        batch_num: int,
        modules: list[dict[str, Any]],
        enable_refinement: bool = True,
        max_refinement_iterations: int = 3,
        enable_coverage_guided: bool = False,
        target_coverage: float = 0.80
    ):
        """Initialize generator.

        Args:
            agent_id: Unique agent identifier
            batch_num: Batch number (1-18)
            modules: List of modules to generate tests for
            enable_refinement: Enable Phase 2 multi-turn refinement (default: True)
            max_refinement_iterations: Max iterations for refinement (default: 3)
            enable_coverage_guided: Enable Phase 3 coverage-guided generation (default: False)
            target_coverage: Target coverage percentage (default: 0.80 = 80%)
        """
        self.agent_id = agent_id
        self.batch_num = batch_num
        self.modules = modules

        # Phase 2 & 3 configuration
        self.enable_refinement = enable_refinement
        self.max_refinement_iterations = max_refinement_iterations
        self.enable_coverage_guided = enable_coverage_guided
        self.target_coverage = target_coverage

        # Initialize memory backend for dashboard integration
        try:
            self.memory = RedisShortTermMemory()
            self.coordinator = HeartbeatCoordinator(memory=self.memory, enable_streaming=True)
            self.event_streamer = EventStreamer(memory=self.memory)
            self.feedback_loop = FeedbackLoop(memory=self.memory)
        except Exception as e:
            logger.warning(f"Failed to initialize memory backend: {e}")
            self.coordinator = HeartbeatCoordinator()
            self.event_streamer = None
            self.feedback_loop = None

        self.output_dir = Path(f"tests/behavioral/generated/batch{batch_num}")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Generator initialized: refinement={enable_refinement}, coverage_guided={enable_coverage_guided}")

    def generate_all(self) -> dict[str, Any]:
        """Generate tests for all modules with progress tracking.

        Returns:
            Summary of generation results
        """
        # Start tracking
        self.coordinator.start_heartbeat(
            agent_id=self.agent_id,
            metadata={
                "batch": self.batch_num,
                "total_modules": len(self.modules),
                "workflow": "autonomous_test_generation",
            }
        )

        try:
            results = {
                "batch": self.batch_num,
                "total_modules": len(self.modules),
                "completed": 0,
                "failed": 0,
                "tests_generated": 0,
                "files_created": [],
            }

            for i, module in enumerate(self.modules):
                progress = (i + 1) / len(self.modules)
                module_name = module["file"].replace("src/empathy_os/", "")

                # Update dashboard
                self.coordinator.beat(
                    status="running",
                    progress=progress,
                    current_task=f"Generating tests for {module_name}"
                )

                try:
                    # Generate tests for this module
                    test_file = self._generate_module_tests(module)
                    if test_file:
                        results["completed"] += 1
                        results["files_created"].append(str(test_file))
                        logger.info(f"✅ Generated tests for {module_name}")

                        # Send event to dashboard
                        if self.event_streamer:
                            self.event_streamer.publish_event(
                                event_type="test_file_created",
                                data={
                                    "agent_id": self.agent_id,
                                    "module": module_name,
                                    "test_file": str(test_file),
                                    "batch": self.batch_num
                                }
                            )

                        # Record quality feedback
                        if self.feedback_loop:
                            self.feedback_loop.record_feedback(
                                workflow_name="test-generation",
                                stage_name="generation",
                                tier="capable",
                                quality_score=1.0,  # Success
                                metadata={"module": module_name, "status": "success", "batch": self.batch_num}
                            )
                    else:
                        results["failed"] += 1
                        logger.warning(f"⚠️ Skipped {module_name} (validation failed)")

                        # Record failure feedback
                        if self.feedback_loop:
                            self.feedback_loop.record_feedback(
                                workflow_name="test-generation",
                                stage_name="validation",
                                tier="capable",
                                quality_score=0.0,  # Failure
                                metadata={"module": module_name, "status": "validation_failed", "batch": self.batch_num}
                            )

                except Exception as e:
                    results["failed"] += 1
                    logger.error(f"❌ Error generating tests for {module_name}: {e}")

                    # Send error event
                    if self.event_streamer:
                        self.event_streamer.publish_event(
                            event_type="test_generation_error",
                            data={
                                "agent_id": self.agent_id,
                                "module": module_name,
                                "error": str(e),
                                "batch": self.batch_num
                            }
                        )

            # Count total tests
            results["tests_generated"] = self._count_tests()

            # Final update
            self.coordinator.beat(
                status="completed",
                progress=1.0,
                current_task=f"Completed: {results['completed']}/{results['total_modules']} modules"
            )

            return results

        except Exception as e:
            # Error tracking
            self.coordinator.beat(
                status="failed",
                progress=0.0,
                current_task=f"Failed: {str(e)}"
            )
            raise

        finally:
            # Stop heartbeat
            self.coordinator.stop_heartbeat(
                final_status="completed" if results["completed"] > 0 else "failed"
            )

    def _generate_module_tests(self, module: dict[str, Any]) -> Path | None:
        """Generate tests for a single module using LLM agent.

        Args:
            module: Module info dict with 'file', 'total', 'missing', etc.

        Returns:
            Path to generated test file, or None if skipped
        """
        source_file = Path(module["file"])
        module_name = source_file.stem

        # Skip if module doesn't exist
        if not source_file.exists():
            logger.warning(f"Source file not found: {source_file}")
            return None

        # Read source to understand what needs testing
        try:
            source_code = source_file.read_text()
        except Exception as e:
            logger.error(f"Cannot read {source_file}: {e}")
            return None

        # Generate test file path
        test_file = self.output_dir / f"test_{module_name}_behavioral.py"

        # Extract module path for imports
        module_path = str(source_file).replace("src/", "").replace(".py", "").replace("/", ".")

        # Generate tests using LLM agent with Anthropic best practices
        # Phase 1: Basic generation
        # Phase 2: Multi-turn refinement (if enabled)
        # Phase 3: Coverage-guided improvement (if enabled)

        if self.enable_refinement:
            logger.info(f"🔄 Using Phase 2: Multi-turn refinement for {module_name}")
            test_content = self._generate_with_refinement(module_name, module_path, source_file, source_code, test_file)
        else:
            logger.info(f"📝 Using Phase 1: Basic generation for {module_name}")
            test_content = self._generate_with_llm(module_name, module_path, source_file, source_code)

        if not test_content:
            logger.warning(f"LLM generation failed for {module_name}")
            return None

        logger.info(f"LLM generated {len(test_content)} bytes for {module_name}")

        # Phase 3: Coverage-guided improvement (if enabled)
        if self.enable_coverage_guided:
            logger.info(f"📊 Applying Phase 3: Coverage-guided improvement for {module_name}")
            improved_content = self._generate_with_coverage_target(
                module_name, module_path, source_file, source_code, test_file, test_content
            )
            if improved_content:
                test_content = improved_content
                logger.info(f"✅ Coverage-guided improvement complete for {module_name}")
            else:
                logger.warning(f"⚠️  Coverage-guided improvement failed, using previous version for {module_name}")

        # Write final test file
        test_file.write_text(test_content)
        logger.info(f"Wrote test file: {test_file}")

        # Validate it can be imported
        if not self._validate_test_file(test_file):
            test_file.unlink()
            return None

        return test_file

    def _is_workflow_module(self, source_code: str, module_path: str) -> bool:
        """Detect if module is a workflow requiring special handling.

        Args:
            source_code: Source code content
            module_path: Python import path

        Returns:
            True if this is a workflow module needing LLM mocking
        """
        # Check for workflow indicators
        indicators = [
            r"class\s+\w+Workflow",
            r"async\s+def\s+execute",
            r"tier_routing",
            r"LLMProvider",
            r"TelemetryCollector",
            r"from\s+anthropic\s+import",
            r"messages\.create",
            r"client\.messages"
        ]

        return any(re.search(pattern, source_code) for pattern in indicators)

    def _get_example_tests(self) -> str:
        """Get few-shot examples of excellent tests for prompt learning."""
        return """EXAMPLE 1: Testing a utility function with mocking
```python
import pytest
from unittest.mock import Mock, patch
from mymodule import process_data

class TestProcessData:
    def test_processes_valid_data_successfully(self):
        \"\"\"Given valid input data, when processing, then returns expected result.\"\"\"
        # Given
        input_data = {"key": "value", "count": 42}

        # When
        result = process_data(input_data)

        # Then
        assert result is not None
        assert result["status"] == "success"
        assert result["processed"] is True

    def test_handles_invalid_data_with_error(self):
        \"\"\"Given invalid input, when processing, then raises ValueError.\"\"\"
        # Given
        invalid_data = {"missing": "key"}

        # When/Then
        with pytest.raises(ValueError, match="Required key 'key' not found"):
            process_data(invalid_data)
```

EXAMPLE 2: Testing a workflow with LLM mocking
```python
import pytest
from unittest.mock import Mock, AsyncMock, patch
from mymodule import MyWorkflow

@pytest.fixture
def mock_llm_client(mocker):
    \"\"\"Mock Anthropic LLM client.\"\"\"
    mock = mocker.patch('anthropic.Anthropic')
    mock_response = Mock()
    mock_response.content = [Mock(text="mock LLM response")]
    mock_response.usage = Mock(input_tokens=100, output_tokens=50)
    mock_response.stop_reason = "end_turn"
    mock.return_value.messages.create = AsyncMock(return_value=mock_response)
    return mock

class TestMyWorkflow:
    @pytest.mark.asyncio
    async def test_executes_successfully_with_mocked_llm(self, mock_llm_client):
        \"\"\"Given valid input, when executing workflow, then completes successfully.\"\"\"
        # Given
        workflow = MyWorkflow()
        input_data = {"prompt": "test prompt"}

        # When
        result = await workflow.execute(input_data)

        # Then
        assert result is not None
        assert "response" in result
        mock_llm_client.return_value.messages.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_api_error_gracefully(self, mock_llm_client):
        \"\"\"Given API failure, when executing, then handles error appropriately.\"\"\"
        # Given
        workflow = MyWorkflow()
        mock_llm_client.return_value.messages.create.side_effect = Exception("API Error")

        # When/Then
        with pytest.raises(Exception, match="API Error"):
            await workflow.execute({"prompt": "test"})
```
"""

    def _get_workflow_specific_prompt(self, module_name: str, module_path: str, source_code: str) -> str:
        """Get workflow-specific test generation prompt with comprehensive mocking guidance."""
        return f"""Generate comprehensive tests for this WORKFLOW module.

⚠️ CRITICAL: This module makes LLM API calls and requires proper mocking.

MODULE: {module_name}
IMPORT PATH: {module_path}

SOURCE CODE (COMPLETE - NO TRUNCATION):
```python
{source_code}
```

WORKFLOW TESTING REQUIREMENTS:

1. **Mock LLM API calls** - NEVER make real API calls in tests
   ```python
   @pytest.fixture
   def mock_llm_client(mocker):
       mock = mocker.patch('anthropic.Anthropic')
       mock_response = Mock()
       mock_response.content = [Mock(text="mock response")]
       mock_response.usage = Mock(input_tokens=100, output_tokens=50)
       mock_response.stop_reason = "end_turn"
       mock.return_value.messages.create = AsyncMock(return_value=mock_response)
       return mock
   ```

2. **Test tier routing** - Verify correct model selection (cheap/capable/premium)
3. **Test telemetry** - Mock and verify telemetry recording
4. **Test cost calculation** - Verify token usage and cost tracking
5. **Test error handling** - Mock API failures, timeouts, rate limits
6. **Test caching** - Mock cache hits/misses if applicable

TARGET COVERAGE: 40-50% (realistic for workflow classes with proper mocking)

Generate a complete test file with:
- Copyright header: "Generated by enhanced autonomous test generation system."
- Proper imports (from {module_path})
- Mock fixtures for ALL external dependencies (LLM, databases, APIs, file I/O)
- Given/When/Then structure in docstrings
- Both success and failure test cases
- Edge case handling
- Docstrings for all tests describing behavior

Return ONLY the complete Python test file, no explanations."""

    def _generate_with_llm(self, module_name: str, module_path: str, source_file: Path, source_code: str) -> str | None:
        """Generate comprehensive tests using LLM with Anthropic best practices.

        ENHANCEMENTS (Phase 1):
        - Extended thinking (20K token budget) for thorough test planning
        - Prompt caching for 90% cost reduction
        - Full source code (NO TRUNCATION)
        - Workflow-specific prompts when detected

        Args:
            module_name: Name of module being tested
            module_path: Python import path (e.g., empathy_os.config)
            source_file: Path to source file
            source_code: Source code content (FULL, not truncated)

        Returns:
            Test file content with comprehensive tests, or None if generation failed
        """
        import os

        try:
            import anthropic
        except ImportError:
            logger.error("anthropic package not installed")
            return None

        # Get API key
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("ANTHROPIC_API_KEY not set")
            return None

        # Detect if this is a workflow module
        is_workflow = self._is_workflow_module(source_code, module_path)
        logger.info(f"Module {module_name}: workflow={is_workflow}, size={len(source_code)} bytes (FULL)")

        # Build appropriate prompt based on module type
        if is_workflow:
            generation_prompt = self._get_workflow_specific_prompt(module_name, module_path, source_code)
        else:
            generation_prompt = f"""Generate comprehensive behavioral tests for this Python module.

SOURCE FILE: {source_file}
MODULE PATH: {module_path}

SOURCE CODE (COMPLETE):
```python
{source_code}
```

Generate a complete test file that:
1. Uses Given/When/Then behavioral test structure
2. Tests all public functions and classes
3. Includes edge cases and error handling
4. Uses proper mocking for external dependencies
5. Targets 80%+ code coverage for this module
6. Follows pytest conventions

Requirements:
- Import from {module_path} (not from src/)
- Use pytest fixtures where appropriate
- Mock external dependencies (APIs, databases, file I/O)
- Test both success and failure paths
- Include docstrings for all tests
- Use descriptive test names
- Start with copyright header:
\"\"\"Behavioral tests for {module_name}.

Generated by enhanced autonomous test generation system.

Copyright 2026 Smart-AI-Memory
Licensed under Apache 2.0
\"\"\"

Return ONLY the complete Python test file content, no explanations."""

        # Build messages with prompt caching (90% cost reduction on retries)
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "You are an expert Python test engineer. Here are examples of excellent tests:",
                        "cache_control": {"type": "ephemeral"}
                    },
                    {
                        "type": "text",
                        "text": self._get_example_tests(),
                        "cache_control": {"type": "ephemeral"}
                    },
                    {
                        "type": "text",
                        "text": generation_prompt
                    }
                ]
            }
        ]

        try:
            # Call Anthropic API with extended thinking and caching
            logger.info(f"Calling LLM with extended thinking for {module_name} (workflow={is_workflow})")
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-sonnet-4-5",  # capable tier
                max_tokens=40000,  # Very generous total budget for comprehensive tests
                thinking={
                    "type": "enabled",
                    "budget_tokens": 20000  # Generous thinking budget for thorough planning
                },
                messages=messages,
                timeout=900.0,  # 15 minutes timeout for extended thinking + generation
            )

            if not response.content:
                logger.warning(f"Empty LLM response for {module_name}")
                return None

            # Extract test content (thinking comes first, then text)
            test_content = None
            for block in response.content:
                if block.type == "text":
                    test_content = block.text.strip()
                    break

            if not test_content:
                logger.warning(f"No text content in LLM response for {module_name}")
                return None

            logger.info(f"LLM returned {len(test_content)} bytes for {module_name}")

            if len(test_content) < 100:
                logger.warning(f"LLM response too short for {module_name}: {test_content[:200]}")
                return None

            # Clean up response (remove markdown fences if present)
            if test_content.startswith("```python"):
                test_content = test_content[len("```python"):].strip()
            if test_content.endswith("```"):
                test_content = test_content[:-3].strip()

            # Check for truncation indicators
            if response.stop_reason == "max_tokens":
                logger.warning(f"⚠️  LLM response truncated for {module_name} (hit max_tokens)")
                # Response might be incomplete but let validation catch it

            # Quick syntax pre-check before returning
            try:
                import ast
                ast.parse(test_content)
                logger.info(f"✓ Quick syntax check passed for {module_name}")
            except SyntaxError as e:
                logger.error(f"❌ LLM generated invalid syntax for {module_name}: {e.msg} at line {e.lineno}")
                return None

            logger.info(f"Test content cleaned, final size: {len(test_content)} bytes")
            return test_content

        except Exception as e:
            logger.error(f"LLM generation error for {module_name}: {e}", exc_info=True)
            return None

    def _run_pytest_validation(self, test_file: Path) -> ValidationResult:
        """Run pytest on generated tests and collect failures.

        Args:
            test_file: Path to test file to validate

        Returns:
            ValidationResult with test outcomes and failure details
        """
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_file), "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            passed = result.returncode == 0
            output = result.stdout + "\n" + result.stderr

            # Count errors
            error_count = output.count("FAILED") + output.count("ERROR")

            # Extract failure details
            failures = ""
            if not passed:
                # Extract relevant failure information
                lines = output.split("\n")
                failure_lines = []
                in_failure = False
                for line in lines:
                    if "FAILED" in line or "ERROR" in line:
                        in_failure = True
                    if in_failure:
                        failure_lines.append(line)
                        if line.startswith("="):  # End of failure section
                            in_failure = False
                failures = "\n".join(failure_lines[:100])  # Limit to 100 lines

            logger.info(f"Pytest validation: passed={passed}, errors={error_count}")

            return ValidationResult(
                passed=passed,
                failures=failures,
                error_count=error_count,
                output=output
            )

        except subprocess.TimeoutExpired:
            logger.error(f"Pytest validation timeout for {test_file}")
            return ValidationResult(
                passed=False,
                failures="Validation timeout after 60 seconds",
                error_count=1,
                output="Timeout"
            )
        except Exception as e:
            logger.error(f"Pytest validation exception: {e}")
            return ValidationResult(
                passed=False,
                failures=f"Validation exception: {e}",
                error_count=1,
                output=str(e)
            )

    def _call_llm_with_history(
        self,
        conversation_history: list[dict[str, Any]],
        api_key: str
    ) -> str | None:
        """Call LLM with conversation history for refinement.

        Args:
            conversation_history: List of messages (role + content)
            api_key: Anthropic API key

        Returns:
            Refined test content or None if failed
        """
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=40000,  # Very generous total budget for iterative refinement
                thinking={
                    "type": "enabled",
                    "budget_tokens": 20000  # Generous thinking budget for thorough analysis
                },
                messages=conversation_history,
                timeout=900.0,  # 15 minutes timeout for refinement iterations
            )

            if not response.content:
                logger.warning("Empty LLM response during refinement")
                return None

            # Extract text content
            test_content = None
            for block in response.content:
                if block.type == "text":
                    test_content = block.text.strip()
                    break

            if not test_content:
                logger.warning("No text content in refinement response")
                return None

            # Clean up response
            if test_content.startswith("```python"):
                test_content = test_content[len("```python"):].strip()
            if test_content.endswith("```"):
                test_content = test_content[:-3].strip()

            return test_content

        except Exception as e:
            logger.error(f"LLM refinement error: {e}", exc_info=True)
            return None

    def _generate_with_refinement(
        self,
        module_name: str,
        module_path: str,
        source_file: Path,
        source_code: str,
        test_file: Path
    ) -> str | None:
        """Generate tests with iterative refinement (Phase 2).

        Process:
        1. Generate initial tests
        2. Run pytest validation
        3. If failures, ask Claude to fix
        4. Repeat until tests pass or max iterations

        Args:
            module_name: Name of module being tested
            module_path: Python import path
            source_file: Path to source file
            source_code: Source code content
            test_file: Path where tests will be written

        Returns:
            Final test content or None if all attempts failed
        """
        import os

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("ANTHROPIC_API_KEY not set")
            return None

        logger.info(f"🔄 Phase 2: Multi-turn refinement enabled for {module_name} (max {self.max_refinement_iterations} iterations)")

        # Step 1: Generate initial tests
        test_content = self._generate_with_llm(module_name, module_path, source_file, source_code)
        if not test_content:
            logger.warning("Initial generation failed")
            return None

        # Build conversation history for subsequent refinements
        is_workflow = self._is_workflow_module(source_code, module_path)

        # Initial prompt (for history tracking)
        if is_workflow:
            initial_prompt = self._get_workflow_specific_prompt(module_name, module_path, source_code)
        else:
            initial_prompt = f"""Generate comprehensive behavioral tests for {module_name}.

SOURCE CODE:
```python
{source_code}
```"""

        conversation_history = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "You are an expert Python test engineer. Examples:", "cache_control": {"type": "ephemeral"}},
                    {"type": "text", "text": self._get_example_tests(), "cache_control": {"type": "ephemeral"}},
                    {"type": "text", "text": initial_prompt}
                ]
            },
            {
                "role": "assistant",
                "content": test_content
            }
        ]

        # Step 2: Iterative refinement loop
        for iteration in range(self.max_refinement_iterations):
            logger.info(f"📝 Refinement iteration {iteration + 1}/{self.max_refinement_iterations} for {module_name}")

            # Write current version to temp file
            temp_test_file = test_file.parent / f"_temp_{test_file.name}"
            temp_test_file.write_text(test_content)

            # Validate with pytest
            validation_result = self._run_pytest_validation(temp_test_file)

            if validation_result.passed:
                logger.info(f"✅ Tests passed on iteration {iteration + 1} for {module_name}")
                temp_test_file.unlink()  # Clean up
                return test_content

            # Tests failed - ask Claude to fix
            logger.warning(f"⚠️  Tests failed on iteration {iteration + 1}: {validation_result.error_count} errors")

            refinement_prompt = f"""The tests you generated have failures. Please fix these specific issues:

FAILURES:
{validation_result.failures[:2000]}

Requirements:
1. Fix ONLY the failing tests - don't rewrite everything
2. Ensure imports are correct
3. Ensure mocking is properly configured
4. Return the COMPLETE corrected test file (not just the fixes)
5. Keep the same structure and copyright header

Return ONLY the complete Python test file, no explanations."""

            # Add to conversation history
            conversation_history.append({
                "role": "user",
                "content": refinement_prompt
            })

            # Call LLM for refinement
            refined_content = self._call_llm_with_history(conversation_history, api_key)

            if not refined_content:
                logger.error(f"❌ Refinement failed on iteration {iteration + 1}")
                temp_test_file.unlink()
                break

            # Update content and history
            test_content = refined_content
            conversation_history.append({
                "role": "assistant",
                "content": test_content
            })

            logger.info(f"🔄 Refinement iteration {iteration + 1} complete, retrying validation...")

        # Max iterations reached
        logger.warning(f"⚠️  Max refinement iterations reached for {module_name} - returning best attempt")
        return test_content

    def _run_coverage_analysis(self, test_file: Path, source_file: Path) -> CoverageResult:
        """Run coverage analysis on tests.

        Args:
            test_file: Path to test file
            source_file: Path to source file being tested

        Returns:
            CoverageResult with coverage metrics and missing lines
        """
        try:
            # Run pytest with coverage
            result = subprocess.run(
                [
                    sys.executable, "-m", "pytest",
                    str(test_file),
                    f"--cov={source_file.parent}",
                    "--cov-report=term-missing",
                    "--cov-report=json",
                    "-v"
                ],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=Path.cwd()
            )

            # Parse coverage from JSON report
            coverage_json_path = Path(".coverage.json")
            if not coverage_json_path.exists():
                logger.warning("Coverage JSON not generated")
                return CoverageResult(
                    coverage=0.0,
                    missing_lines=[],
                    total_statements=0,
                    covered_statements=0
                )

            with open(coverage_json_path) as f:
                coverage_data = json.load(f)

            # Find coverage for our specific source file
            source_key = str(source_file)
            file_coverage = None
            for key in coverage_data.get("files", {}).keys():
                if source_file.name in key or source_key in key:
                    file_coverage = coverage_data["files"][key]
                    break

            if not file_coverage:
                logger.warning(f"No coverage data found for {source_file}")
                return CoverageResult(
                    coverage=0.0,
                    missing_lines=[],
                    total_statements=0,
                    covered_statements=0
                )

            # Extract metrics
            total_statements = file_coverage["summary"]["num_statements"]
            covered_statements = file_coverage["summary"]["covered_lines"]
            coverage_pct = file_coverage["summary"]["percent_covered"] / 100.0
            missing_lines = file_coverage["missing_lines"]

            logger.info(f"Coverage: {coverage_pct:.1%} ({covered_statements}/{total_statements} statements)")

            return CoverageResult(
                coverage=coverage_pct,
                missing_lines=missing_lines,
                total_statements=total_statements,
                covered_statements=covered_statements
            )

        except subprocess.TimeoutExpired:
            logger.error("Coverage analysis timeout")
            return CoverageResult(coverage=0.0, missing_lines=[], total_statements=0, covered_statements=0)
        except Exception as e:
            logger.error(f"Coverage analysis error: {e}", exc_info=True)
            return CoverageResult(coverage=0.0, missing_lines=[], total_statements=0, covered_statements=0)

    def _extract_uncovered_lines(self, source_file: Path, missing_lines: list[int]) -> str:
        """Extract source code for uncovered lines.

        Args:
            source_file: Path to source file
            missing_lines: List of uncovered line numbers

        Returns:
            Formatted string with uncovered code sections
        """
        if not missing_lines:
            return "No uncovered lines"

        try:
            source_lines = source_file.read_text().split("\n")

            # Group consecutive lines into ranges
            ranges = []
            start = missing_lines[0]
            end = start

            for line_num in missing_lines[1:]:
                if line_num == end + 1:
                    end = line_num
                else:
                    ranges.append((start, end))
                    start = line_num
                    end = start
            ranges.append((start, end))

            # Extract code for each range with context
            uncovered_sections = []
            for start, end in ranges[:10]:  # Limit to 10 ranges
                context_start = max(0, start - 3)
                context_end = min(len(source_lines), end + 2)

                section = []
                section.append(f"Lines {start}-{end}:")
                for i in range(context_start, context_end):
                    line_marker = ">>>" if start <= i + 1 <= end else "   "
                    section.append(f"{line_marker} {i + 1:4d}: {source_lines[i]}")

                uncovered_sections.append("\n".join(section))

            return "\n\n".join(uncovered_sections)

        except Exception as e:
            logger.error(f"Error extracting uncovered lines: {e}")
            return f"Error extracting lines: {e}"

    def _generate_with_coverage_target(
        self,
        module_name: str,
        module_path: str,
        source_file: Path,
        source_code: str,
        test_file: Path,
        initial_test_content: str
    ) -> str | None:
        """Generate tests iteratively until coverage target met (Phase 3).

        Process:
        1. Start with initial tests
        2. Run coverage analysis
        3. If target not met, identify uncovered lines
        4. Ask Claude to add tests for uncovered code
        5. Repeat until target coverage reached or max iterations

        Args:
            module_name: Name of module being tested
            module_path: Python import path
            source_file: Path to source file
            source_code: Source code content
            test_file: Path to test file
            initial_test_content: Initial test content from Phase 1/2

        Returns:
            Final test content with improved coverage or None if failed
        """
        import os

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("ANTHROPIC_API_KEY not set")
            return None

        logger.info(f"📊 Phase 3: Coverage-guided generation enabled (target: {self.target_coverage:.0%})")

        test_content = initial_test_content
        max_coverage_iterations = 5

        for iteration in range(max_coverage_iterations):
            logger.info(f"📈 Coverage iteration {iteration + 1}/{max_coverage_iterations} for {module_name}")

            # Write current tests
            test_file.write_text(test_content)

            # Run coverage analysis
            coverage_result = self._run_coverage_analysis(test_file, source_file)

            logger.info(f"Current coverage: {coverage_result.coverage:.1%}, target: {self.target_coverage:.0%}")

            # Check if target reached
            if coverage_result.coverage >= self.target_coverage:
                logger.info(f"✅ Coverage target reached: {coverage_result.coverage:.1%}")
                return test_content

            # Not enough progress
            if iteration > 0 and coverage_result.coverage <= 0.05:
                logger.warning("⚠️  Coverage not improving, stopping")
                break

            # Identify uncovered code
            uncovered_code = self._extract_uncovered_lines(source_file, coverage_result.missing_lines)

            # Ask Claude to add tests for uncovered lines
            refinement_prompt = f"""Current coverage: {coverage_result.coverage:.1%}
Target coverage: {self.target_coverage:.0%}
Missing: {len(coverage_result.missing_lines)} lines

UNCOVERED CODE:
{uncovered_code[:3000]}

Please ADD tests to cover these specific uncovered lines. Requirements:
1. Focus ONLY on the uncovered lines shown above
2. Add new test methods to the existing test classes
3. Return the COMPLETE test file with additions (not just new tests)
4. Use appropriate mocking for external dependencies
5. Keep existing tests intact - just add new ones

Return ONLY the complete Python test file with additions, no explanations."""

            # Build conversation with caching
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "You are an expert Python test engineer. Examples:", "cache_control": {"type": "ephemeral"}},
                        {"type": "text", "text": self._get_example_tests(), "cache_control": {"type": "ephemeral"}},
                        {"type": "text", "text": f"Source code:\n```python\n{source_code}\n```", "cache_control": {"type": "ephemeral"}},
                        {"type": "text", "text": f"Current tests:\n```python\n{test_content}\n```"},
                        {"type": "text", "text": refinement_prompt}
                    ]
                }
            ]

            # Call LLM for coverage improvement
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=api_key)
                response = client.messages.create(
                    model="claude-sonnet-4-5",
                    max_tokens=40000,  # Very generous total budget for coverage improvement
                    thinking={"type": "enabled", "budget_tokens": 20000},  # Thorough thinking for coverage gaps
                    messages=messages,
                    timeout=900.0,  # 15 minutes timeout for coverage-guided iterations
                )

                refined_content = None
                for block in response.content:
                    if block.type == "text":
                        refined_content = block.text.strip()
                        break

                if not refined_content:
                    logger.warning(f"No content in coverage refinement iteration {iteration + 1}")
                    break

                # Clean up
                if refined_content.startswith("```python"):
                    refined_content = refined_content[len("```python"):].strip()
                if refined_content.endswith("```"):
                    refined_content = refined_content[:-3].strip()

                test_content = refined_content
                logger.info(f"🔄 Coverage iteration {iteration + 1} complete, retrying analysis...")

            except Exception as e:
                logger.error(f"Coverage refinement error on iteration {iteration + 1}: {e}")
                break

        # Return best attempt
        logger.info(f"Coverage-guided generation complete: final coverage ~{coverage_result.coverage:.1%}")
        return test_content

    def _validate_test_file(self, test_file: Path) -> bool:
        """Validate test file can be imported and has valid syntax.

        Args:
            test_file: Path to test file

        Returns:
            True if valid, False otherwise
        """
        # Step 1: Check for syntax errors with ast.parse (fast)
        try:
            import ast
            content = test_file.read_text()
            ast.parse(content)
            logger.info(f"✓ Syntax check passed for {test_file.name}")
        except SyntaxError as e:
            logger.error(f"❌ Syntax error in {test_file.name} at line {e.lineno}: {e.msg}")
            return False
        except Exception as e:
            logger.error(f"❌ Cannot parse {test_file.name}: {e}")
            return False

        # Step 2: Check if pytest can collect the tests
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "--collect-only", str(test_file)],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                logger.error(f"❌ Pytest collection failed for {test_file.name}")
                logger.error(f"   Error: {result.stderr[:500]}")
                return False

            logger.info(f"✓ Pytest collection passed for {test_file.name}")
            return True

        except subprocess.TimeoutExpired:
            logger.error(f"❌ Validation timeout for {test_file.name}")
            return False
        except Exception as e:
            logger.error(f"❌ Validation exception for {test_file}: {e}")
            return False

    def _count_tests(self) -> int:
        """Count total tests in generated files.

        Returns:
            Number of tests
        """
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "--collect-only", "-q", str(self.output_dir)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            # Parse output like "123 tests collected"
            for line in result.stdout.split("\n"):
                if "tests collected" in line:
                    return int(line.split()[0])
            return 0
        except Exception:
            return 0


def run_batch_generation(
    batch_num: int,
    modules_json: str,
    enable_refinement: bool = True,
    enable_coverage_guided: bool = False
) -> None:
    """Run test generation for a batch.

    Args:
        batch_num: Batch number
        modules_json: JSON string of modules to process
        enable_refinement: Enable Phase 2 multi-turn refinement (default: True)
        enable_coverage_guided: Enable Phase 3 coverage-guided generation (default: False)
    """
    # Parse modules
    modules = json.loads(modules_json)

    # Create agent with Phase 2 & 3 configuration
    agent_id = f"test-gen-batch{batch_num}"
    generator = AutonomousTestGenerator(
        agent_id,
        batch_num,
        modules,
        enable_refinement=enable_refinement,
        enable_coverage_guided=enable_coverage_guided
    )

    # Generate tests
    print(f"Starting autonomous test generation for batch {batch_num}")
    print(f"Modules to process: {len(modules)}")
    print(f"Agent ID: {agent_id}")
    print("\nENHANCEMENTS:")
    print("  Phase 1: Extended thinking + Prompt caching + Workflow detection")
    print(f"  Phase 2: Multi-turn refinement = {'ENABLED' if enable_refinement else 'DISABLED'}")
    print(f"  Phase 3: Coverage-guided = {'ENABLED' if enable_coverage_guided else 'DISABLED'}")
    print("\nMonitor at: http://localhost:8000\n")

    results = generator.generate_all()

    # Report results
    print(f"\n{'='*60}")
    print(f"Batch {batch_num} Complete!")
    print(f"{'='*60}")
    print(f"Modules processed: {results['completed']}/{results['total_modules']}")
    print(f"Tests generated: {results['tests_generated']}")
    print(f"Files created: {len(results['files_created'])}")
    print(f"Failed: {results['failed']}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python -m empathy_os.workflows.autonomous_test_gen <batch_num> <modules_json> [--no-refinement] [--coverage-guided]")
        print("\nOptions:")
        print("  --no-refinement     Disable Phase 2 multi-turn refinement")
        print("  --coverage-guided   Enable Phase 3 coverage-guided generation (slower)")
        sys.exit(1)

    batch_num = int(sys.argv[1])
    modules_json = sys.argv[2]

    # Parse optional flags
    enable_refinement = "--no-refinement" not in sys.argv
    enable_coverage_guided = "--coverage-guided" in sys.argv

    run_batch_generation(batch_num, modules_json, enable_refinement, enable_coverage_guided)
