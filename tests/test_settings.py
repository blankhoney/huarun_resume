import pytest

from huarun_app.settings import Settings, validate_production_settings


def test_production_settings_reject_default_weak_values():
    settings = Settings(
        app_env="production",
        database_url="postgresql+psycopg://huarun:huarun@postgres:5432/huarun",
        session_secret="replace-with-long-random-string",
        demo_password="Demo123456!",
    )

    with pytest.raises(RuntimeError) as exc:
        validate_production_settings(settings)

    message = str(exc.value)
    assert "DATABASE_URL" in message
    assert "SESSION_SECRET" in message
    assert "DEMO_PASSWORD" in message


def test_production_settings_reject_documentation_placeholders():
    settings = Settings(
        app_env="production",
        database_url=(
            "postgresql+psycopg://huarun:replace-with-strong-password@postgres:5432/huarun"
        ),
        session_secret="replace-with-32-plus-random-chars",
        demo_password="replace-with-demo-login-password",
    )

    with pytest.raises(RuntimeError) as exc:
        validate_production_settings(settings)

    message = str(exc.value)
    assert "DATABASE_URL" in message
    assert "SESSION_SECRET" in message
    assert "DEMO_PASSWORD" in message


def test_production_settings_accept_explicit_values():
    settings = Settings(
        app_env="production",
        database_url="postgresql+psycopg://huarun:strong-password@postgres:5432/huarun",
        session_secret="s" * 32,
        demo_password="HuarunDemo123456!",
    )

    validate_production_settings(settings)
