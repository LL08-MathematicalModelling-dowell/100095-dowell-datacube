"""Tests for ephemeral playground sessions."""

from datetime import datetime, timedelta, timezone

import pytest
from django.test import override_settings
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture(autouse=True)
def _stub_seed(mocker):
    """Avoid touching real tenant DBs during start-endpoint tests."""
    mocker.patch(
        "core.presentation.views.playground_views.seed_playground_database_sync",
        return_value=None,
    )


@pytest.mark.django_db
def test_playground_start_disabled_when_flag_off(api_client):
    with override_settings(PLAYGROUND_ENABLED=False):
        response = api_client.post("/core/api/v2/playground/start/", {}, format="json")
    assert response.status_code == 404


@pytest.mark.django_db
@override_settings(PLAYGROUND_ENABLED=True, PLAYGROUND_MAX_ACTIVE_SESSIONS=500)
def test_playground_start_creates_session(api_client):
    response = api_client.post("/core/api/v2/playground/start/", {}, format="json")
    assert response.status_code == 200
    body = response.json()
    assert body["access"]
    assert body["refresh"]
    assert body["is_playground"] is True
    assert body["reused_session"] is False
    assert body["playground_session_id"]
    assert "pg_session" in response.cookies


@pytest.mark.django_db
@override_settings(PLAYGROUND_ENABLED=True)
def test_playground_start_reuses_session(api_client):
    first = api_client.post("/core/api/v2/playground/start/", {}, format="json")
    session_id = first.json()["playground_session_id"]

    second = api_client.post(
        "/core/api/v2/playground/start/",
        {"session_id": session_id},
        format="json",
    )
    assert second.status_code == 200
    assert second.json()["reused_session"] is True
    assert second.json()["playground_session_id"] == session_id


@pytest.mark.django_db
@override_settings(PLAYGROUND_ENABLED=True, PLAYGROUND_MAX_ACTIVE_SESSIONS=1)
def test_playground_capacity_limit(api_client, mocker):
    mocker.patch(
        "core.application.playground_service.user_manager.count_live_playground_sessions",
        side_effect=[0, 1],
    )
    mocker.patch(
        "core.application.playground_service.user_manager.count_live_playground_sessions_by_ip",
        return_value=0,
    )
    first = api_client.post("/core/api/v2/playground/start/", {}, format="json")
    assert first.status_code == 200

    second_client = APIClient()
    second = second_client.post("/core/api/v2/playground/start/", {}, format="json")
    assert second.status_code == 503


def test_playground_is_live_respects_expiry():
    from core.infrastructure.playground import playground_is_live

    expired = {
        "is_playground": True,
        "playground_expires_at": datetime.now(timezone.utc) - timedelta(hours=1),
    }
    live = {
        "is_playground": True,
        "playground_expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    assert playground_is_live(expired) is False
    assert playground_is_live(live) is True


def test_playground_seeds_define_multiple_databases():
    from core.application.playground_service import PLAYGROUND_SEEDS

    assert len(PLAYGROUND_SEEDS) >= 2
    names = [s["db_name"] for s in PLAYGROUND_SEEDS]
    assert len(names) == len(set(names))
    for seed in PLAYGROUND_SEEDS:
        assert seed["collections"]
        assert seed["documents"]
        for coll in seed["collections"]:
            assert coll["name"] in seed["documents"]
            assert len(seed["documents"][coll["name"]]) >= 1


def test_seed_playground_database_sync_creates_all_templates(mocker):
    """Seed walks every PLAYGROUND_SEEDS entry via sync Mongo helpers."""
    from bson import ObjectId
    from core.application import playground_service as svc

    user_id = str(ObjectId())
    created_dbs: list[str] = []
    inserted_meta: list[dict] = []
    inserted_docs: dict[str, int] = {}

    class FakeInsertResult:
        def __init__(self):
            self.inserted_id = ObjectId()

    class FakeCollection:
        def __init__(self, name: str):
            self.name = name

        def insert_many(self, docs):
            inserted_docs[self.name] = inserted_docs.get(self.name, 0) + len(docs)

        def insert_one(self, doc):
            inserted_meta.append(doc)
            return FakeInsertResult()

    class FakePhysicalDb:
        def __init__(self, name: str):
            self.name = name
            self._collections: dict[str, FakeCollection] = {}

        def create_collection(self, name: str):
            self._collections[name] = FakeCollection(name)

        def __getitem__(self, name: str):
            return self._collections.setdefault(name, FakeCollection(name))

    class FakeClient:
        def __getitem__(self, name: str):
            if name == "meta_db":
                return {"meta_coll": FakeCollection("meta_coll")}
            created_dbs.append(name)
            return FakePhysicalDb(name)

    mocker.patch.object(svc.settings, "SYNC_MONGODB_CLIENT", FakeClient())
    mocker.patch.object(svc.settings, "MONGODB_DATABASE", "meta_db")
    mocker.patch.object(svc.settings, "MONGODB_COLLECTION", "meta_coll")
    mocker.patch.object(
        svc.user_manager, "increment_playground_document_usage", return_value=None
    )
    mocker.patch(
        "api.infrastructure.naming.generate_db_name",
        side_effect=lambda display, uid: f"pg_{display}_{uid[:6]}",
    )
    analytics = mocker.patch(
        "core.application.playground_service.seed_playground_analytics_sync",
        return_value={"http": 10, "ops": 5, "errors": 1, "slow": 1},
    )
    files = mocker.patch(
        "core.application.playground_service.seed_playground_sample_files_sync",
        return_value=3,
    )

    svc.seed_playground_database_sync(user_id)

    assert len(created_dbs) == len(svc.PLAYGROUND_SEEDS)
    assert len(inserted_meta) == len(svc.PLAYGROUND_SEEDS)
    assert sum(inserted_docs.values()) >= 8
    svc.user_manager.increment_playground_document_usage.assert_called_once()
    analytics.assert_called_once()
    files.assert_called_once_with(user_id)
    seeded_dbs = analytics.call_args.args[1]
    assert len(seeded_dbs) == len(svc.PLAYGROUND_SEEDS)
    assert all(db["id"] and db["collections"] for db in seeded_dbs)


def test_seed_playground_analytics_inserts_chart_data(mocker):
    from bson import ObjectId
    from core.application import playground_seed_analytics as seed

    user_id = str(ObjectId())
    buckets: dict[str, list] = {}

    class FakeColl:
        def __init__(self, name: str):
            self.name = name

        def insert_many(self, docs):
            buckets.setdefault(self.name, []).extend(docs)

        def delete_many(self, _query):
            buckets[self.name] = []

    class FakeDb:
        def __getitem__(self, name: str):
            return FakeColl(name)

    class FakeClient:
        def __getitem__(self, name: str):
            assert name == "datacube_analytics"
            return FakeDb()

    mocker.patch.object(seed.settings, "SYNC_MONGODB_CLIENT", FakeClient())
    mocker.patch.object(
        seed.user_manager,
        "users_collection",
        mocker.Mock(update_one=mocker.Mock()),
    )

    databases = [
        {"id": str(ObjectId()), "collections": ["products", "orders"]},
        {"id": str(ObjectId()), "collections": ["contacts"]},
    ]
    counts = seed.seed_playground_analytics_sync(user_id, databases, days=7)
    assert counts["http"] > 0
    assert counts["ops"] > 0
    assert len(buckets.get("http_requests", [])) == counts["http"]
    assert len(buckets.get("db_operations", [])) == counts["ops"]
    assert buckets.get("errors") is not None
    seed.user_manager.users_collection.update_one.assert_called_once()


def test_seed_playground_sample_files_uploads_gridfs(mocker, tmp_path):
    from bson import ObjectId
    from core.application import playground_seed_analytics as seed

    demo_dir = tmp_path / "playground_demo_files"
    demo_dir.mkdir()
    img = demo_dir / "beautiful-fall-nature-scenery-free-image.jpeg"
    vid = demo_dir / "file_test_demo.mp4"
    img.write_bytes(b"\xff\xd8\xfffake-jpeg")
    vid.write_bytes(b"\x00\x00\x00\x18ftypmp42fake")

    inserted: list[dict] = []
    uploaded: list[tuple[str, bytes]] = []

    class FakeBucket:
        def upload_from_stream(self, filename, handle, metadata=None):
            data = handle.read()
            uploaded.append((filename, data))
            return ObjectId()

    class FakeColl:
        def insert_many(self, docs):
            inserted.extend(docs)

    class FakeClient:
        def __getitem__(self, name: str):
            if name == "files_db":
                return object()
            return {"file_metadata": FakeColl()}

    mocker.patch.object(seed, "playground_demo_files_dir", return_value=demo_dir)
    mocker.patch.object(seed.settings, "SYNC_MONGODB_CLIENT", FakeClient())
    mocker.patch.object(seed.settings, "MONGODB_DATABASE", "meta_db")
    mocker.patch.object(seed.settings, "FILE_STORAGE_DB_NAME", "files_db")
    mocker.patch("gridfs.GridFSBucket", return_value=FakeBucket())

    n = seed.seed_playground_sample_files_sync(str(ObjectId()))
    assert n == 2
    assert len(uploaded) == 2
    assert {u[0] for u in uploaded} == {img.name, vid.name}
    assert len(inserted) == 2
    assert all(d.get("file_id") and d.get("storage_type") == "gridfs" for d in inserted)


def test_list_demo_media_files_prefers_known_names(tmp_path, mocker):
    from core.application import playground_seed_analytics as seed

    demo_dir = tmp_path / "playground_demo_files"
    demo_dir.mkdir()
    (demo_dir / "beautiful-fall-nature-scenery-free-image.jpeg").write_bytes(b"x")
    (demo_dir / "file_test_demo.mp4").write_bytes(b"y")
    (demo_dir / "other.png").write_bytes(b"z")
    mocker.patch.object(seed, "playground_demo_files_dir", return_value=demo_dir)

    names = [p.name for p in seed._list_demo_media_files()]
    assert names == [
        "beautiful-fall-nature-scenery-free-image.jpeg",
        "file_test_demo.mp4",
    ]
