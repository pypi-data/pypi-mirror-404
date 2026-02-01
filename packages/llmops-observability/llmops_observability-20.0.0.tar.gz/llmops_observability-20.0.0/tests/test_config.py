import llmops_observability.config as config


def test_get_sqs_config_defaults(monkeypatch):
    monkeypatch.delenv("AWS_SQS_URL", raising=False)
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    monkeypatch.delenv("AWS_REGION", raising=False)

    cfg = config.get_sqs_config()
    assert cfg["aws_sqs_url"] is None
    assert cfg["aws_profile"] == "default"
    assert cfg["aws_region"] == "us-east-1"


def test_get_sqs_config_reads_env(monkeypatch):
    monkeypatch.setenv("AWS_SQS_URL", "https://example.com/queue")
    monkeypatch.setenv("AWS_PROFILE", "my_profile")
    monkeypatch.setenv("AWS_REGION", "us-west-2")

    cfg = config.get_sqs_config()
    assert cfg["aws_sqs_url"] == "https://example.com/queue"
    assert cfg["aws_profile"] == "my_profile"
    assert cfg["aws_region"] == "us-west-2"


def test_get_project_id_and_environment_strip(monkeypatch):
    monkeypatch.setenv("PROJECT_ID", "  proj  ")
    monkeypatch.setenv("ENV", "  staging ")

    assert config.get_project_id() == "proj"
    assert config.get_environment() == "staging"


def test_get_trace_context(monkeypatch):
    monkeypatch.setenv("PROJECT_ID", "trace_proj")
    monkeypatch.setenv("ENV", "uat")

    ctx = config.get_trace_context()
    assert ctx == {"project_id": "trace_proj", "environment": "uat"}


def test_get_default_model_env_override(monkeypatch):
    monkeypatch.setenv("MODEL_ID", "custom-model")
    assert config.get_default_model() == "custom-model"


def test_get_default_model_fallback_when_empty(monkeypatch):
    monkeypatch.setenv("MODEL_ID", "   ")
    model_id = config.get_default_model()
    assert model_id

