"""Integration tests for sageLLM full component chain.

╔════════════════════════════════════════════════════════════════════════════╗
║  🔗 INTEGRATION TESTS - 集成测试                                            ║
║                                                                            ║
║  这些测试验证完整的组件调用链：                                             ║
║    sagellm (CLI) → sagellm-core → sagellm-backend → sagellm-protocol       ║
║                                                                            ║
║  与 sagellm-backend 中的直接单元测试不同，这里测试的是：                    ║
║    1. 组件间的集成是否正确                                                  ║
║    2. 插件系统（entry points）是否工作                                      ║
║    3. component_trace 是否正确记录调用链                                    ║
╚════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import asyncio
import os

import pytest

# ============================================================================
# Skip conditions
# ============================================================================


def _cuda_available() -> bool:
    """Check if CUDA is available."""
    try:
        import torch

        return torch.cuda.is_available()
    except ImportError:
        return False


def _model_available(model_id: str) -> bool:
    """Check if model is available."""
    try:
        from transformers import AutoConfig

        AutoConfig.from_pretrained(model_id, trust_remote_code=True)
        return True
    except Exception:
        return False


TEST_MODEL = os.environ.get("SAGELLM_TEST_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")
SKIP_NO_CUDA = "CUDA not available (requires NVIDIA GPU)"
SKIP_NO_MODEL = f"Model {TEST_MODEL} not available"


# ============================================================================
# Integration Tests - Full Chain via sagellm-core
# ============================================================================


@pytest.mark.integration
@pytest.mark.gpu
@pytest.mark.skipif(not _cuda_available(), reason=SKIP_NO_CUDA)
class TestFullChainIntegration:
    """Integration tests that verify the complete component chain.

    These tests create engines via sagellm-core's plugin system (entry points),
    ensuring the full stack works together correctly.
    """

    def test_create_engine_via_core(self) -> None:
        """Test creating engine through sagellm-core plugin system.

        Verifies:
        - sagellm-core can discover sagellm-backend via entry points
        - Engine is created correctly
        - _created_via_core flag is set
        """
        from sagellm_core import BackendConfig, EngineConfig, create_backend, create_engine

        backend_cfg = BackendConfig(kind="cuda", device="cuda:0")
        backend = create_backend(backend_cfg)

        config = EngineConfig(
            kind="cuda",
            model=TEST_MODEL,
            model_path=TEST_MODEL,
            device="cuda:0",
            max_output_tokens=32,
        )

        engine = create_engine(config, backend)
        assert engine is not None

        # Verify it was created via core (has the flag)
        assert getattr(engine, "_created_via_core", False), (
            "Engine should have _created_via_core=True when created via sagellm-core"
        )

    @pytest.mark.skipif(not _model_available(TEST_MODEL), reason=SKIP_NO_MODEL)
    @pytest.mark.slow
    def test_full_inference_chain(self) -> None:
        """Test full inference through sagellm-core → sagellm-backend.

        Verifies:
        - Engine can load model
        - Inference works end-to-end
        - component_trace shows both sagellm-core and sagellm-backend
        """
        from sagellm_core import BackendConfig, EngineConfig, create_backend, create_engine
        from sagellm_protocol import Request

        backend_cfg = BackendConfig(kind="cuda", device="cuda:0")
        backend = create_backend(backend_cfg)

        config = EngineConfig(
            kind="cuda",
            model=TEST_MODEL,
            model_path=TEST_MODEL,
            device="cuda:0",
            max_output_tokens=32,
        )

        engine = create_engine(config, backend)

        async def run_inference() -> None:
            await engine.start()
            try:
                request = Request(
                    request_id="integration-test-001",
                    trace_id="trace-integration-001",
                    prompt="Hello, I am",
                    max_tokens=16,
                )
                response = await engine.execute(request)

                # Verify response
                assert response is not None
                assert response.output_text is not None
                assert len(response.output_text) > 0

                # Verify component trace
                assert response.metrics is not None
                assert response.metrics.component_trace is not None, (
                    "Metrics should have component_trace"
                )

                trace = response.metrics.component_trace
                assert "sagellm-core" in trace, (
                    f"component_trace should include 'sagellm-core', got: {trace}"
                )
                assert any("sagellm-backend" in c for c in trace), (
                    f"component_trace should include 'sagellm-backend:*', got: {trace}"
                )

            finally:
                await engine.stop()

        asyncio.run(run_inference())


# ============================================================================
# Protocol Compliance Tests
# ============================================================================


@pytest.mark.integration
class TestProtocolCompliance:
    """Tests that verify protocol compliance across components."""

    def test_metrics_has_required_fields(self) -> None:
        """Test that Metrics has all Demo Contract required fields."""
        from sagellm_protocol import Metrics

        # Demo Contract required fields
        required_fields = [
            "ttft_ms",
            "tbt_ms",
            "tpot_ms",
            "throughput_tps",
            "peak_mem_mb",
            "error_rate",
            # KV Cache fields (Task2)
            "kv_used_tokens",
            "kv_used_bytes",
            "prefix_hit_rate",
            "evict_count",
            "evict_ms",
            # Compression fields (Task3)
            "spec_accept_rate",
            # Observability
            "component_trace",
        ]

        for field in required_fields:
            assert hasattr(Metrics, "model_fields"), "Metrics should be a Pydantic model"
            assert field in Metrics.model_fields, f"Metrics is missing required field: {field}"

    def test_response_has_required_fields(self) -> None:
        """Test that Response has all required fields."""
        from sagellm_protocol import Response

        required_fields = [
            "request_id",
            "trace_id",
            "output_text",
            "output_tokens",
            "finish_reason",
            "metrics",
        ]

        for field in required_fields:
            assert field in Response.model_fields, f"Response is missing required field: {field}"
