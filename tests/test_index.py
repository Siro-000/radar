import pytest

from radar.models import Function
from radar.index import VectorIndex, SearchResult

DIM = 8


def make_function(name: str, file: str = "test.py", line: int = 1) -> Function:
    return Function(name=name, file=file, start_line=line, end_line=line + 4, source_code=f"def {name}(): pass")


def make_embedding(value: float) -> list[float]:
    return [value] * DIM


@pytest.fixture
def index():
    import uuid
    return VectorIndex(collection_name=f"test_{uuid.uuid4().hex}")


def test_add_and_count(index):
    fn = make_function("foo")
    index.add(fn, make_embedding(0.1))
    assert index.count() == 1


def test_search_returns_results(index):
    fn = make_function("foo")
    index.add(fn, make_embedding(0.5))
    results = index.search(make_embedding(0.5), k=1)
    assert len(results) == 1
    assert isinstance(results[0], SearchResult)
    assert results[0].function.name == "foo"


def test_search_score_between_0_and_1(index):
    fn = make_function("foo")
    index.add(fn, make_embedding(0.5))
    results = index.search(make_embedding(0.5), k=1)
    assert 0.0 <= results[0].score <= 1.0


def test_most_similar_ranked_first(index):
    fn_similar = make_function("similar", line=1)
    fn_different = make_function("different", line=10)
    query = make_embedding(1.0)
    index.add(fn_similar, make_embedding(0.99))
    index.add(fn_different, make_embedding(0.0))
    results = index.search(query, k=2)
    assert results[0].function.name == "similar"
    assert results[0].score > results[1].score


def test_add_batch(index):
    fns = [make_function(f"fn_{i}", line=i * 10) for i in range(5)]
    embeddings = [make_embedding(float(i) / 10) for i in range(5)]
    index.add_batch(fns, embeddings)
    assert index.count() == 5


def test_persist_and_reload(tmp_path):
    index = VectorIndex(persist_path=tmp_path)
    fn = make_function("persist_me")
    index.add(fn, make_embedding(0.7))

    reloaded = VectorIndex(persist_path=tmp_path)
    assert reloaded.count() == 1
    results = reloaded.search(make_embedding(0.7), k=1)
    assert results[0].function.name == "persist_me"
