import logging
import os

import pytest
from pydantic_settings_manager import load_user_configs

import kiarina.utils.file as kf


@pytest.fixture(scope="session", autouse=True)
def setup_logger():
    logger = logging.getLogger("kiarina.lib.firebase.rtdb")
    logger.handlers.clear()
    logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


@pytest.fixture
def database_url() -> str:
    env_var = "KIARINA_LIB_FIREBASE_RTDB_TEST_DATABASE_URL"

    if env_var not in os.environ:
        pytest.skip(f"Environment variable {env_var} not set, skipping tests.")

    return os.environ[env_var]


@pytest.fixture(scope="session")
def load_settings():
    env_var = "KIARINA_LIB_FIREBASE_RTDB_TEST_SETTINGS_FILE"

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

    # Get database URL from environment
    env_var = "KIARINA_LIB_FIREBASE_RTDB_TEST_DATABASE_URL"
    if env_var not in os.environ:
        pytest.skip(f"Environment variable {env_var} not set, skipping tests.")

    database_url = os.environ[env_var]

    # Initialize Firebase Admin SDK (only once per session)
    app = firebase_admin.initialize_app(
        credentials.Certificate(service_account_file), {"databaseURL": database_url}
    )

    yield app

    # Cleanup after all tests
    firebase_admin.delete_app(app)


@pytest.fixture
def user_id() -> str:
    return "test_user"


@pytest.fixture
def custom_token(firebase_app, user_id) -> str:
    auth = pytest.importorskip("firebase_admin.auth")
    return auth.create_custom_token(user_id).decode("utf-8")


@pytest.fixture
async def token_response(custom_token):
    from kiarina.lib.firebase.auth import exchange_custom_token, settings_manager

    settings = settings_manager.get_settings()

    return await exchange_custom_token(
        custom_token=custom_token,
        api_key=settings.api_key.get_secret_value(),
    )


@pytest.fixture
def refresh_token(token_response) -> str:
    return token_response.refresh_token


@pytest.fixture
def id_token(token_response) -> str:
    return token_response.id_token


@pytest.fixture
def token_manager(refresh_token):
    from kiarina.lib.firebase.auth import TokenManager, settings_manager

    settings = settings_manager.get_settings()
    return TokenManager(refresh_token, settings.api_key.get_secret_value())
