import importlib
import sys
from unittest.mock import patch, MagicMock
from bson.objectid import ObjectId
import pytest

MODULE_PATH = "opticedge_cloud_utils.mongo"


@pytest.fixture
def module():
    """
    Import a fresh copy of the module and ensure _mongo_client is cleared.
    """
    # Fully remove cached module
    sys.modules.pop(MODULE_PATH, None)

    mod = importlib.import_module(MODULE_PATH)

    # Ensure no cached client
    mod._mongo_client = None

    yield mod

    # Cleanup after test
    mod._mongo_client = None
    sys.modules.pop(MODULE_PATH, None)


@patch(f"{MODULE_PATH}.get_secret")
@patch(f"{MODULE_PATH}.MongoClient")
def test_get_mongo_client_creates_client_and_pings(mock_mongo_client_cls, mock_get_secret, module):
    fake_uri = "mongodb://user:pass@host:27017"
    mock_get_secret.return_value = fake_uri

    fake_client = MagicMock()
    fake_client.admin.command.return_value = {"ok": 1}
    mock_mongo_client_cls.return_value = fake_client

    client = module.get_mongo_client("test-project", "mongo-uri")

    mock_get_secret.assert_called_once_with("test-project", "mongo-uri")
    mock_mongo_client_cls.assert_called_once_with(fake_uri)
    fake_client.admin.command.assert_called_once_with("ping")

    assert client is fake_client
    assert module._mongo_client is fake_client


@patch(f"{MODULE_PATH}.get_secret")
@patch(f"{MODULE_PATH}.MongoClient")
def test_get_mongo_client_returns_cached_client_on_subsequent_calls(
    mock_mongo_client_cls, mock_get_secret, module
):
    fake_uri = "mongodb://user:pass@host:27017"
    mock_get_secret.return_value = fake_uri

    fake_client = MagicMock()
    fake_client.admin.command.return_value = {"ok": 1}
    mock_mongo_client_cls.return_value = fake_client

    first = module.get_mongo_client("test-project", "mongo-uri")
    second = module.get_mongo_client("test-project", "mongo-uri")

    mock_get_secret.assert_called_once()
    mock_mongo_client_cls.assert_called_once()
    assert first is second
    assert module._mongo_client is first


@patch(f"{MODULE_PATH}.get_secret")
@patch(f"{MODULE_PATH}.MongoClient")
def test_get_mongo_client_ping_failure_raises_and_does_not_cache(
    mock_mongo_client_cls, mock_get_secret, module
):
    fake_uri = "mongodb://user:pass@host:27017"
    mock_get_secret.return_value = fake_uri

    bad_client = MagicMock()
    bad_client.admin.command.side_effect = Exception("ping failed")
    mock_mongo_client_cls.return_value = bad_client

    with pytest.raises(Exception, match="ping failed"):
        module.get_mongo_client("test-project", "mongo-uri")

    assert module._mongo_client is None


@patch(f"{MODULE_PATH}.MongoClient")
def test_get_mongo_client_with_uri_creates_client_and_pings(mock_mongo_client_cls, module):
    fake_uri = "mongodb://user:pass@host:27017"

    fake_client = MagicMock()
    fake_client.admin.command.return_value = {"ok": 1}
    mock_mongo_client_cls.return_value = fake_client

    client = module.get_mongo_client_with_uri(fake_uri)

    mock_mongo_client_cls.assert_called_once_with(fake_uri)
    fake_client.admin.command.assert_called_once_with("ping")

    assert client is fake_client
    assert module._mongo_client is fake_client


@patch(f"{MODULE_PATH}.MongoClient")
def test_get_mongo_client_with_uri_returns_cached_client_on_subsequent_calls(
    mock_mongo_client_cls, module
):
    fake_uri = "mongodb://user:pass@host:27017"

    fake_client = MagicMock()
    fake_client.admin.command.return_value = {"ok": 1}
    mock_mongo_client_cls.return_value = fake_client

    first = module.get_mongo_client_with_uri(fake_uri)
    second = module.get_mongo_client_with_uri(fake_uri)

    mock_mongo_client_cls.assert_called_once()
    assert first is second
    assert module._mongo_client is first


@patch(f"{MODULE_PATH}.MongoClient")
def test_get_mongo_client_with_uri_ping_failure_raises_and_does_not_cache(
    mock_mongo_client_cls, module
):
    fake_uri = "mongodb://user:pass@host:27017"

    bad_client = MagicMock()
    bad_client.admin.command.side_effect = Exception("ping failed")
    mock_mongo_client_cls.return_value = bad_client

    with pytest.raises(Exception, match="ping failed"):
        module.get_mongo_client_with_uri(fake_uri)

    assert module._mongo_client is None


@patch(f"{MODULE_PATH}.get_secret")
@patch(f"{MODULE_PATH}.MongoClient")
def test_get_mongo_db_returns_database_object(mock_mongo_client_cls, mock_get_secret, module):
    fake_uri = "mongodb://user:pass@host:27017"
    mock_get_secret.return_value = fake_uri

    fake_db = MagicMock()
    fake_client = MagicMock()
    fake_client.admin.command.return_value = {"ok": 1}
    fake_client.__getitem__.return_value = fake_db
    mock_mongo_client_cls.return_value = fake_client

    db = module.get_mongo_db("test-project", "mongo-uri", "opticedge")

    assert db is fake_db
    fake_client.__getitem__.assert_called_once_with("opticedge")


@patch(f"{MODULE_PATH}.MongoClient")
def test_get_mongo_db_with_uri_returns_database_object(mock_mongo_client_cls, module):
    fake_uri = "mongodb://user:pass@host:27017"

    fake_db = MagicMock()
    fake_client = MagicMock()
    fake_client.admin.command.return_value = {"ok": 1}
    fake_client.__getitem__.return_value = fake_db
    mock_mongo_client_cls.return_value = fake_client

    db = module.get_mongo_db_with_uri(fake_uri, "opticedge")

    assert db is fake_db
    fake_client.__getitem__.assert_called_once_with("opticedge")


def test_cached_client_shared_between_secret_and_uri_calls(module):
    fake_client = MagicMock()
    module._mongo_client = fake_client

    with patch(f"{MODULE_PATH}.MongoClient") as mock_mongo_client_cls, \
         patch(f"{MODULE_PATH}.get_secret") as mock_get_secret:

        assert module.get_mongo_client("ignored", "ignored") is fake_client
        assert module.get_mongo_client_with_uri("ignored") is fake_client

        mock_mongo_client_cls.assert_not_called()
        mock_get_secret.assert_not_called()


# ------------------------------------------------------------------
# normalize_object_id tests
# ------------------------------------------------------------------

def test_normalize_object_id_with_objectid(module):
    oid = ObjectId()
    assert module.normalize_object_id(oid) is oid


def test_normalize_object_id_with_valid_objectid_string(module):
    oid = ObjectId()
    result = module.normalize_object_id(str(oid))

    assert isinstance(result, ObjectId)
    assert result == oid


def test_normalize_object_id_with_invalid_string(module):
    value = "not-a-valid-objectid"
    assert module.normalize_object_id(value) == value


def test_normalize_object_id_with_non_string_value(module):
    value = 12345
    assert module.normalize_object_id(value) == value
