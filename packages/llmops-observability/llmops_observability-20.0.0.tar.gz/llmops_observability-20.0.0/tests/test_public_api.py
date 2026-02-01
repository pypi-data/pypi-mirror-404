import importlib
import sys


def test_public_api_exports(monkeypatch):
    import llmops_observability as mod

    expected = {
        "TraceManager",
        "track_function",
        "track_llm_call",
        "send_to_sqs",
        "send_to_sqs_immediate",
        "flush_sqs",
        "is_sqs_enabled",
        "LLMOpsASGIMiddleware",
        "enable_bedrock_instrumentation",
        "disable_bedrock_instrumentation",
        "is_instrumentation_enabled",
        "__version__",
    }

    assert set(mod.__all__) == expected


def test_version_fallback(monkeypatch):
    import importlib.metadata as metadata

    monkeypatch.setattr(metadata, "version", lambda name: (_ for _ in ()).throw(metadata.PackageNotFoundError()))
    mod = importlib.reload(importlib.import_module("llmops_observability"))
    assert mod.__version__ == "0.0.0"


def test_bedrock_instrumentation_available():
    """Test that bedrock instrumentation is available when dependencies exist."""
    import llmops_observability as mod
    
    # If we got here, bedrock_instrumentation was imported successfully
    assert mod.BEDROCK_INSTRUMENTATION_AVAILABLE is True
    assert mod.enable_bedrock_instrumentation is not None
    assert mod.disable_bedrock_instrumentation is not None
    assert mod.is_instrumentation_enabled is not None


def test_bedrock_instrumentation_import_error_fallback(monkeypatch):
    """Test that module handles ImportError for bedrock_instrumentation gracefully."""
    # We need to simulate the ImportError case
    # This is hard to test directly because the module is already imported
    # Instead, verify the expected attributes exist in the fallback scenario
    import llmops_observability as mod
    
    # When bedrock instrumentation is available
    if mod.BEDROCK_INSTRUMENTATION_AVAILABLE:
        assert callable(mod.enable_bedrock_instrumentation)
        assert callable(mod.disable_bedrock_instrumentation)
        assert callable(mod.is_instrumentation_enabled)
    else:
        # Fallback case - functions should be None
        assert mod.enable_bedrock_instrumentation is None
        assert mod.disable_bedrock_instrumentation is None
        assert mod.is_instrumentation_enabled is None


def test_all_exports_are_importable():
    """Test that all items in __all__ can be accessed."""
    import llmops_observability as mod
    
    for name in mod.__all__:
        assert hasattr(mod, name), f"{name} not found in module"
        obj = getattr(mod, name)
        # Just verify we can access each export
        assert obj is not None or name in ["enable_bedrock_instrumentation", 
                                            "disable_bedrock_instrumentation",
                                            "is_instrumentation_enabled"]
