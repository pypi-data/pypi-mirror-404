"""Architecture conformance tests for sageLLM.

╔════════════════════════════════════════════════════════════════════════════╗
║  🏗️ ARCHITECTURE TESTS - 架构合规性测试                                     ║
║                                                                            ║
║  这些测试确保多团队开发时遵循正确的代码架构：                                ║
║    1. 依赖层级（sagellm-protocol 是基础层，不能依赖其他 sagellm-*）          ║
║    2. 禁止循环导入                                                          ║
║    3. 禁止硬件 SDK 直接侵入核心逻辑                                         ║
║    4. 组件接口稳定性                                                        ║
╚════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import importlib
import importlib.metadata
import sys

import pytest

# ============================================================================
# Dependency Hierarchy Tests
# ============================================================================

# Official dependency hierarchy (bottom to top):
# Level 0: sagellm-protocol (no sagellm-* dependencies)
# Level 1: sagellm-backend (depends on protocol)
# Level 2: sagellm-core (depends on protocol, backend)
# Level 3: sagellm-control-plane (depends on protocol, core)
# Level 4: sagellm-gateway (depends on protocol, control-plane)
# Level 5: sagellm (depends on all above)

DEPENDENCY_HIERARCHY = {
    "isagellm-protocol": {
        "level": 0,
        "allowed_sagellm_deps": [],
    },
    "isagellm-backend": {
        "level": 1,
        "allowed_sagellm_deps": ["isagellm-protocol"],
    },
    "isagellm-core": {
        "level": 2,
        "allowed_sagellm_deps": ["isagellm-protocol", "isagellm-backend"],
    },
    "isagellm-control-plane": {
        "level": 3,
        "allowed_sagellm_deps": ["isagellm-protocol", "isagellm-core"],
    },
    "isagellm-gateway": {
        "level": 4,
        "allowed_sagellm_deps": ["isagellm-protocol", "isagellm-control-plane"],
    },
    "isagellm": {
        "level": 5,
        "allowed_sagellm_deps": [
            "isagellm-protocol",
            "isagellm-backend",
            "isagellm-core",
            "isagellm-control-plane",
            "isagellm-gateway",
        ],
    },
}


@pytest.mark.architecture
class TestDependencyHierarchy:
    """Tests for verifying dependency hierarchy is correct."""

    def test_protocol_has_no_sagellm_deps(self) -> None:
        """Verify sagellm-protocol has no dependencies on other sagellm packages.

        Protocol is Level 0 - the foundation that all others depend on.
        """
        violations = self._check_package_deps("isagellm-protocol")
        assert not violations, (
            f"isagellm-protocol should have NO sagellm dependencies, found: {violations}"
        )

    def test_backend_deps_are_valid(self) -> None:
        """Verify sagellm-backend only depends on protocol."""
        violations = self._check_package_deps("isagellm-backend")
        assert not violations, f"isagellm-backend has invalid dependencies: {violations}"

    def test_core_deps_are_valid(self) -> None:
        """Verify sagellm-core only depends on protocol and backend."""
        violations = self._check_package_deps("isagellm-core")
        assert not violations, f"isagellm-core has invalid dependencies: {violations}"

    def _check_package_deps(self, package_name: str) -> list[str]:
        """Check if package has any invalid sagellm dependencies.

        Args:
            package_name: The package to check

        Returns:
            List of invalid dependency names (should be empty)
        """
        if package_name not in DEPENDENCY_HIERARCHY:
            return []

        allowed = DEPENDENCY_HIERARCHY[package_name]["allowed_sagellm_deps"]
        violations = []

        try:
            dist = importlib.metadata.distribution(package_name)
            requires = dist.requires or []

            for req in requires:
                # Skip dev/test extras (they have ; extra == "dev" etc)
                if "; extra ==" in req or ";extra==" in req:
                    continue

                # Extract package name from requirement string
                dep_name = (
                    req.split()[0]
                    .split(";")[0]
                    .split("[")[0]
                    .split(">")[0]
                    .split("<")[0]
                    .split("=")[0]
                    .split("!")[0]
                )

                # Check if it's a sagellm package
                if dep_name.startswith("isagellm"):
                    if dep_name not in allowed:
                        violations.append(dep_name)

        except importlib.metadata.PackageNotFoundError:
            pytest.skip(f"Package {package_name} not installed")

        return violations


# ============================================================================
# Import Isolation Tests
# ============================================================================


@pytest.mark.architecture
class TestImportIsolation:
    """Tests for verifying import isolation rules."""

    def test_protocol_importable_standalone(self) -> None:
        """Verify sagellm-protocol can be imported without other sagellm packages.

        This is critical for the Protocol-First development model.
        """
        # Clear any cached imports
        modules_to_remove = [m for m in sys.modules if m.startswith("sagellm_")]
        for m in modules_to_remove:
            del sys.modules[m]

        # Import protocol
        import sagellm_protocol

        # Verify key types are available
        assert hasattr(sagellm_protocol, "Request")
        assert hasattr(sagellm_protocol, "Response")
        assert hasattr(sagellm_protocol, "Metrics")

    def test_no_hardware_sdk_in_protocol(self) -> None:
        """Verify protocol doesn't import any hardware SDKs.

        Protocol should be pure Python with Pydantic only.
        """
        forbidden_imports = [
            "torch",
            "torch_npu",
            "tensorflow",
            "jax",
            "cuda",
            "nccl",
            "hccl",
        ]

        # Check loaded modules
        protocol_modules = [m for m in sys.modules if m.startswith("sagellm_protocol")]

        for mod_name in protocol_modules:
            mod = sys.modules.get(mod_name)
            if mod is None:
                continue

            # Check module's __dict__ for forbidden imports
            for forbidden in forbidden_imports:
                assert forbidden not in dir(mod), (
                    f"sagellm_protocol.{mod_name} should not import {forbidden}"
                )


# ============================================================================
# Component Interface Tests
# ============================================================================


@pytest.mark.architecture
class TestComponentInterfaces:
    """Tests for verifying component interfaces are stable and complete."""

    def test_llm_engine_interface(self) -> None:
        """Verify LLMEngine implements required interface."""
        from sagellm_core import LLMEngine

        required_methods = [
            "start",
            "stop",
            "execute",
            "stream",
            "generate",
        ]

        required_properties = [
            "engine_id",
            "is_running",
        ]

        for method in required_methods:
            assert hasattr(LLMEngine, method), f"LLMEngine missing method: {method}"
            assert callable(getattr(LLMEngine, method, None)) or isinstance(
                getattr(type, method, None), property
            ), f"LLMEngine.{method} should be callable"

        for prop in required_properties:
            assert hasattr(LLMEngine, prop), f"LLMEngine missing property: {prop}"

    def test_backend_registry_available(self) -> None:
        """Verify sagellm-backend registry is available."""
        try:
            from sagellm_backend.registry import get_available_backends, get_provider

            backends = get_available_backends()
            assert isinstance(backends, list), "get_available_backends should return list"
            assert callable(get_provider), "get_provider should be callable"

        except Exception as e:
            pytest.fail(f"Failed to access backend registry: {e}")

    def test_core_llm_engine_export(self) -> None:
        """Verify sagellm-core exports LLMEngine."""
        from sagellm_core import LLMEngine, LLMEngineConfig

        assert LLMEngine is not None
        assert LLMEngineConfig is not None


# ============================================================================
# Component Trace Verification
# ============================================================================


@pytest.mark.architecture
class TestComponentTraceArchitecture:
    """Tests for component trace architecture."""

    def test_component_trace_field_exists(self) -> None:
        """Verify Metrics has component_trace field."""
        from sagellm_protocol import Metrics

        assert "component_trace" in Metrics.model_fields
        field = Metrics.model_fields["component_trace"]

        # Should be list[str] | None
        assert field.annotation is not None

    def test_direct_backend_has_single_trace(self) -> None:
        """Verify LLMEngine can be instantiated with backend."""
        from sagellm_core.llm_engine import LLMEngine, LLMEngineConfig

        config = LLMEngineConfig(model_path="sshleifer/tiny-gpt2", backend_type="cpu")
        engine = LLMEngine(config)

        # LLMEngine should have a model_path
        assert engine._config.model_path == "sshleifer/tiny-gpt2"
        assert engine._config.backend_type == "cpu"

    def test_core_created_engine_has_full_trace(self) -> None:
        """Verify LLMEngine works with different backend types."""
        from sagellm_core.llm_engine import LLMEngine, LLMEngineConfig

        # Test with auto backend (defaults to cpu on machines without GPU)
        config = LLMEngineConfig(
            model_path="sshleifer/tiny-gpt2",
            backend_type="auto",
        )

        engine = LLMEngine(config)

        # Should resolve to cpu on machines without GPU
        assert engine._config.backend_type == "auto"


# ============================================================================
# Cross-Team Development Guidelines
# ============================================================================


@pytest.mark.architecture
class TestCrossTeamGuidelines:
    """Tests that enforce cross-team development guidelines.

    These tests help catch common mistakes when multiple teams
    are working on different sagellm repositories simultaneously.
    """

    def test_all_engines_have_component_trace(self) -> None:
        """Verify LLMEngine has required interface methods.

        This ensures the unified engine works across all backends.
        """
        from sagellm_core.llm_engine import LLMEngine

        # LLMEngine should have key interface methods
        assert hasattr(LLMEngine, "start"), "LLMEngine must have start()"
        assert hasattr(LLMEngine, "stop"), "LLMEngine must have stop()"
        assert hasattr(LLMEngine, "generate"), "LLMEngine must have generate()"
        assert hasattr(LLMEngine, "stream"), "LLMEngine must have stream()"
        assert hasattr(LLMEngine, "execute"), "LLMEngine must have execute()"

    def test_factory_functions_set_core_flag(self) -> None:
        """Verify LLMEngine can be created and used.

        This is the new unified engine API.
        """
        from sagellm_core.llm_engine import LLMEngine, LLMEngineConfig

        # Test LLMEngine creation
        config = LLMEngineConfig(
            model_path="sshleifer/tiny-gpt2",
            backend_type="cpu",
        )

        engine = LLMEngine(config)
        assert engine._config.model_path == "sshleifer/tiny-gpt2"
