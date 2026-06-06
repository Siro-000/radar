import pytest

from radar.engine.index import build, load, SearchResult
from radar.engine.models import Function

DIM = 8


def make_fn(name: str, file: str = "Foo.java", line: int = 1) -> Function:
    return Function(name=name, file=file, start_line=line, end_line=line + 5,
                    source_code=f"public void {name}() {{}}", signature=f"public void {name}()")


def make_vec(*values: float) -> list[float]:
    """Build a DIM-length vector from leading values, rest zero."""
    v = list(values) + [0.0] * (DIM - len(values))
    return v[:DIM]


def test_build_and_search(tmp_path):
    fns = [make_fn("alpha"), make_fn("beta")]
    # alpha points along dim-0, beta along dim-1 — cosine query along dim-0 → alpha wins
    embeddings = [make_vec(1.0), make_vec(0.0, 1.0)]
    index = build(fns, embeddings, tmp_path)
    results = index.search(make_vec(1.0), k=2)
    assert len(results) == 2
    assert results[0].function.name == "alpha"
    assert isinstance(results[0], SearchResult)


def test_score_between_0_and_1(tmp_path):
    index = build([make_fn("x")], [make_vec(1.0)], tmp_path)
    results = index.search(make_vec(1.0), k=1)
    assert 0.0 <= results[0].score <= 1.0


def test_most_similar_ranked_first(tmp_path):
    fns = [make_fn("near"), make_fn("far")]
    # near: mostly dim-0; far: mostly dim-1; query along dim-0 → near ranks first
    index = build(fns, [make_vec(1.0, 0.1), make_vec(0.1, 1.0)], tmp_path)
    results = index.search(make_vec(1.0), k=2)
    assert results[0].function.name == "near"
    assert results[0].score > results[1].score


def test_persist_and_reload(tmp_path):
    fns = [make_fn("persist_me")]
    index = build(fns, [make_vec(1.0)], tmp_path)
    reloaded = load(tmp_path)
    assert reloaded.count() == 1
    results = reloaded.search(make_vec(1.0), k=1)
    assert results[0].function.name == "persist_me"


def test_empty_index_returns_empty(tmp_path):
    index = build([], [], tmp_path)
    results = index.search(make_vec(0.5), k=3)
    assert results == []


def test_metadata_json_written(tmp_path):
    build([make_fn("meta_test")], [make_vec(0.5)], tmp_path)
    assert (tmp_path / "metadata.json").exists()
    assert (tmp_path / "index.faiss").exists()
