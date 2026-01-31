import os

import pytest
from pydantic_settings_manager import load_user_configs

import kiarina.utils.file as kf


@pytest.fixture(scope="session")
def load_settings():
    env_var = "KIARINA_LIB_FIREBASE_AUTH_TEST_SETTINGS_FILE"

    if env_var not in os.environ:
        pytest.skip(f"Environment variable {env_var} not set, skipping tests.")

    test_settings_file = os.environ[env_var]
    test_settings_file = os.path.expanduser(test_settings_file)

    if not os.path.exists(test_settings_file):
        raise FileNotFoundError(f"Settings file not found: {test_settings_file}")

    user_configs = kf.read_yaml_dict(test_settings_file)

    if not user_configs:
        raise ValueError(f"Settings file is empty or invalid: {test_settings_file}")

    load_user_configs(user_configs)


@pytest.fixture(scope="session")
def firebase_app(load_settings):
    """Initialize Firebase Admin SDK once per test session."""
    firebase_admin = pytest.importorskip("firebase_admin")
    credentials = pytest.importorskip("firebase_admin.credentials")

    import kiarina.lib.google.auth

    service_account_file = (
        kiarina.lib.google.auth.settings_manager.get_settings().service_account_file
    )
    assert service_account_file is not None

    # Initialize Firebase Admin SDK (only once per session)
    app = firebase_admin.initialize_app(credentials.Certificate(service_account_file))

    yield app

    # Cleanup after all tests
    firebase_admin.delete_app(app)
