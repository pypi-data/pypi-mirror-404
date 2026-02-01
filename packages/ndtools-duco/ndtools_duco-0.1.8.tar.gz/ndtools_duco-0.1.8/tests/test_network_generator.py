# tests/test_network_generator.py
from __future__ import annotations
import json
from pathlib import Path

import pytest

from ndtools import network_generator as ng


@pytest.fixture
def tmp_out(tmp_path: Path) -> Path:
    return tmp_path / "generated"


@pytest.fixture
def no_validate(monkeypatch):
    """Disable schema validation to keep tests lightweight."""
    monkeypatch.setattr(ng, "validate", lambda *args, **kwargs: None)


def _read_dataset(root: Path):
    data_dir = root / "data"
    nodes = json.loads((data_dir / "nodes.json").read_text())
    edges = json.loads((data_dir / "edges.json").read_text())
    probs = json.loads((data_dir / "probs.json").read_text())
    return nodes, edges, probs


def _common_asserts(ds_root: Path):
    assert ds_root.exists()
    data_dir = ds_root / "data"
    for fn in ("nodes.json", "edges.json", "probs.json"):
        assert (data_dir / fn).exists(), f"missing {fn}"
    assert (ds_root / "README.md").exists()
    assert (ds_root / "metadata.json").exists()


def test_grid1(tmp_out: Path, no_validate):
    cfg = ng.GenConfig(
        name="grid_4x3",
        generator="grid",
        description="test grid",
        generator_params={"rows": 4, "cols": 3, "p_fail": 0.2},
        seed=None,  # grid is deterministic here
    )
    ds_root = ng.generate_and_save(tmp_out, schema_dir=tmp_out, config=cfg, draw_graph=False)
    _common_asserts(ds_root)

    nodes, edges, probs = _read_dataset(ds_root)
    # nodes: dict of size rows*cols with integer coordinates
    assert isinstance(nodes, dict)
    assert len(nodes) == 4 * 3
    for nid, attrs in nodes.items():
        assert set(attrs.keys()) == {"x", "y"}
        assert isinstance(attrs["x"], int)
        assert isinstance(attrs["y"], int)

    # edges: horizontal + vertical
    expected_edges = 4 * (3 - 1) + 3 * (4 - 1)
    assert isinstance(edges, dict)
    assert len(edges) == expected_edges

    # probs: keys match edges; p0+p1==1
    assert set(probs.keys()) == set(edges.keys())
    for e in probs.values():
        p0 = e["0"]["p"]
        p1 = e["1"]["p"]
        assert abs((p0 + p1) - 1.0) < 1e-9


def test_erdos_renyi1(tmp_out: Path, no_validate):
    n = 20
    p = 0.3
    cfg = ng.GenConfig(
        name="er_n20_p03",
        generator="er",
        description="test er",
        generator_params={"n_nodes": n, "p": p, "p_fail": 0.1},
        seed=7,
    )
    ds_root = ng.generate_and_save(tmp_out, schema_dir=tmp_out, config=cfg, draw_graph=False)
    _common_asserts(ds_root)
    nodes, edges, probs = _read_dataset(ds_root)

    assert len(nodes) == n
    # edge count should be within [0, n*(n-1)/2]
    max_e = n * (n - 1) // 2
    assert 0 <= len(edges) <= max_e
    # nodes have x,y (None allowed)
    for attrs in nodes.values():
        assert "x" in attrs and "y" in attrs
    # probs exist for all edges
    assert set(probs.keys()) == set(edges.keys())


def test_watts_strogatz1(tmp_out: Path, no_validate):
    n, k, beta = 60, 6, 0.15
    cfg = ng.GenConfig(
        name="ws_n60_k6_b015",
        generator="ws",
        description="test ws",
        generator_params={"n_nodes": n, "k": k, "p_ws": beta, "p_fail": 0.1},
        seed=7,
    )
    ds_root = ng.generate_and_save(tmp_out, schema_dir=tmp_out, config=cfg, draw_graph=False)
    nodes, edges, _ = _read_dataset(ds_root)
    assert len(nodes) == n
    # WS preserves number of edges exactly: E = n*k/2
    assert len(edges) == n * k // 2


def test_barabasi_albert1(tmp_out: Path, no_validate):
    n, m = 60, 3
    cfg = ng.GenConfig(
        name="ba_n60_m3",
        generator="ba",
        description="test ba",
        generator_params={"n_nodes": n, "m": m, "p_fail": 0.05},
        seed=7,
    )
    ds_root = ng.generate_and_save(tmp_out, schema_dir=tmp_out, config=cfg, draw_graph=False)
    nodes, edges, _ = _read_dataset(ds_root)
    assert len(nodes) == n

    # Expected number of edges:
    expected_classic = m * n - (m * (m + 1)) // 2   # 174 if starting from K_m
    expected_variant = m * (n - m)                   # 171 if starting from m isolated nodes
    assert len(edges) in (expected_classic, expected_variant)

def test_configuration1(tmp_out: Path, no_validate):
    n = 60
    avg_deg = 3.2
    cfg = ng.GenConfig(
        name="config_n60_deg3p2",
        generator="config",
        description="test config",
        generator_params={"n_nodes": n, "avg_deg": avg_deg, "p_fail": 0.1},
        seed=7,
    )
    ds_root = ng.generate_and_save(tmp_out, schema_dir=tmp_out, config=cfg, draw_graph=False)
    nodes, edges, _ = _read_dataset(ds_root)
    assert len(nodes) == n
    # Expect around n*avg_deg/2 edges, allow a reasonable tolerance
    target = n * avg_deg / 2.0
    assert abs(len(edges) - target) <= n  # ±n is a generous tolerance for synthesis/randomization


def test_random_geometric1(tmp_out: Path, no_validate):
    n = 60
    radius = 0.17
    cfg = ng.GenConfig(
        name="rg_n60_r017",
        generator="rg",
        description="test rg",
        generator_params={"n_nodes": n, "radius": radius, "p_fail": 0.1},
        seed=7,
    )
    ds_root = ng.generate_and_save(tmp_out, schema_dir=tmp_out, config=cfg, draw_graph=False)
    nodes, edges, _ = _read_dataset(ds_root)
    assert len(nodes) == n
    # All nodes should have numeric x,y in [0,1]
    for attrs in nodes.values():
        x, y = attrs["x"], attrs["y"]
        assert isinstance(x, (int, float)) and isinstance(y, (int, float))
        assert 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0
    # Some edges should exist (radius not too small)
    assert len(edges) > 0
