"""sageLLM: Modular LLM inference engine for domestic computing power.

Ollama-like experience for Chinese hardware ecosystems (Huawei Ascend, NVIDIA).

Quick Start:
    # Install
    pip install isagellm

    # CLI usage (like ollama)
    sage-llm serve                  # Start CPU engine server
    sage-llm run -p "Hello world"   # Single inference
    sage-llm demo --workload m1     # Run M1 validation
    sage-llm info                   # Show system info

    # Python API (async)
    import asyncio
    from sagellm import BackendConfig, EngineConfig, Request, create_backend, create_engine

__version__ = "0.4.0.35"

    async def main() -> None:
        backend = create_backend(BackendConfig(kind="cpu", device="cpu"))
        engine = create_engine(
            EngineConfig(kind="cpu", model="sshleifer/tiny-gpt2", model_path="sshleifer/tiny-gpt2"),
            backend,
        )
        await engine.start()
        try:
            response = await engine.execute(Request(prompt="Hello", max_tokens=128, stream=False))
            print(response.output_text)
        finally:
            await engine.stop()

    asyncio.run(main())

Architecture:
    sagellm (umbrella)
    ├── sagellm-protocol  # Protocol v0.1 types (Request, Response, Metrics, Error)
    ├── sagellm-core      # Runtime (config, engine factory, demo runner)
    └── sagellm-backend   # Hardware abstraction (CUDA, Ascend, CPU)
"""

from __future__ import annotations

__version__ = "0.4.0.35"

# Lazy imports to handle installation order
_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    # Protocol types
    "Request": ("sagellm_protocol", "Request"),
    "Response": ("sagellm_protocol", "Response"),
    "Metrics": ("sagellm_protocol", "Metrics"),
    "Error": ("sagellm_protocol", "Error"),
    "ErrorCode": ("sagellm_protocol", "ErrorCode"),
    "Timestamps": ("sagellm_protocol", "Timestamps"),
    "StreamEvent": ("sagellm_protocol", "StreamEvent"),
    "StreamEventStart": ("sagellm_protocol", "StreamEventStart"),
    "StreamEventDelta": ("sagellm_protocol", "StreamEventDelta"),
    "StreamEventEnd": ("sagellm_protocol", "StreamEventEnd"),
    # KV hooks
    "KVAllocateParams": ("sagellm_protocol", "KVAllocateParams"),
    "KVHandle": ("sagellm_protocol", "KVHandle"),
    "KVMigrateParams": ("sagellm_protocol", "KVMigrateParams"),
    # Backend
    "BackendProvider": ("sagellm_backend", "BackendProvider"),
    "CapabilityDescriptor": ("sagellm_backend", "CapabilityDescriptor"),
    "DType": ("sagellm_backend", "DType"),
    "KernelKind": ("sagellm_backend", "KernelKind"),
    # Core - Config
    "BackendConfig": ("sagellm_core", "BackendConfig"),
    "EngineConfig": ("sagellm_core", "EngineConfig"),
    "DemoConfig": ("sagellm_core", "DemoConfig"),
    "WorkloadConfig": ("sagellm_core", "WorkloadConfig"),
    "WorkloadSegment": ("sagellm_core", "WorkloadSegment"),
    "load_config": ("sagellm_core", "load_config"),
    # Core - Engine (BaseEngine for type hints only, not for direct instantiation)
    "BaseEngine": ("sagellm_core", "BaseEngine"),
    # Core - Demo
    "DemoRunner": ("sagellm_core", "DemoRunner"),
    "demo_main": ("sagellm_core", "demo_main"),
    # Control Plane (optional - install with isagellm[control-plane])
    "ControlPlaneManager": ("sagellm_control", "ControlPlaneManager"),
    "EngineInfo": ("sagellm_control", "EngineInfo"),
    "EngineState": ("sagellm_control", "EngineState"),
    "SchedulingDecision": ("sagellm_control", "SchedulingDecision"),
}


def __getattr__(name: str) -> object:
    """Lazy import for all exported symbols."""
    if name in _LAZY_IMPORTS:
        module_name, attr_name = _LAZY_IMPORTS[name]
        import importlib

        try:
            module = importlib.import_module(module_name)
            return getattr(module, attr_name)
        except ImportError as e:
            # Provide helpful error for optional dependencies
            if module_name == "sagellm_control":
                raise ImportError(
                    f"{name} requires sagellm-control-plane. "
                    "Install with: pip install 'isagellm[control-plane]'"
                ) from e
            if module_name == "sagellm_gateway":
                raise ImportError(
                    f"{name} requires sagellm-gateway. "
                    "Install with: pip install 'isagellm[gateway]'"
                ) from e
            raise
    raise AttributeError(f"module 'sagellm' has no attribute {name!r}")


def __dir__() -> list[str]:
    """Return all public symbols."""
    return list(__all__)


__all__ = [
    # Version
    "__version__",
    # Protocol - Core types
    "Request",
    "Response",
    "Metrics",
    "Error",
    "ErrorCode",
    "Timestamps",
    # Protocol - Streaming
    "StreamEvent",
    "StreamEventStart",
    "StreamEventDelta",
    "StreamEventEnd",
    # Protocol - KV hooks
    "KVAllocateParams",
    "KVHandle",
    "KVMigrateParams",
    # Backend
    "BackendProvider",
    "CapabilityDescriptor",
    "DType",
    "KernelKind",
    # Core - Config
    "BackendConfig",
    "EngineConfig",
    "DemoConfig",
    "WorkloadConfig",
    "WorkloadSegment",
    "load_config",
    # Core - Engine (BaseEngine for type hints only)
    "BaseEngine",
    # Core - Demo
    "DemoRunner",
    "demo_main",
    # Control Plane (optional)
    "ControlPlaneManager",
    "EngineInfo",
    "EngineState",
    "SchedulingDecision",
]
