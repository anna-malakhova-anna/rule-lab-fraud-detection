import pytest

from scripts.common import DB


@pytest.fixture(scope="session")
def con():
    if not DB.exists():
        pytest.skip("warehouse not built: run `make all` first")
    import duckdb
    c = duckdb.connect(str(DB), read_only=True)
    yield c
    c.close()
