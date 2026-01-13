import json
from pathlib import Path
from runtime.db import connect, migrate
from runtime.store import upsert_catalog, CatalogItem, list_catalog


def test_catalog_roundtrip(tmp_path: Path):
    db = tmp_path / "x.sqlite3"
    con = connect(db)
    migrate(con)

    upsert_catalog(con, "2026-01-01T00:00:00Z", [
        CatalogItem(content_id="drill_alt_picking_1", kind="drill", title="Alt Picking 1",
                   summary="Basics", tags=["picking"], updated_at_utc="2026-01-01T00:00:00Z")
    ])

    items = list_catalog(con)
    assert len(items) == 1
    assert items[0]["content_id"] == "drill_alt_picking_1"
