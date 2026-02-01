from __future__ import annotations
from pathlib import Path
import pytest, json
from typing import Dict, Any, Tuple

import networkx as nx
from ndtools import graphs
import numpy as np

# ---------- helpers ----------

def load_dataset_any(data_dir: str | Path) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    Load nodes/edges[/probs] from a dataset directory and NORMALISE shapes.

    Accepted node formats:
      1) Dict: { "n1": {...}, "n2": {...}, ... }
      2) List: [ {"id":"n1", ...}, {"id":"n2", ...}, ... ]

    Accepted edge formats:
      1) Dict: { "e1": {"from":"n1","to":"n2", ...}, ... }
      2) List: [ {"eid":"e1","source":"n1","target":"n2", ...}, ... ]

    Returns:
      nodes: {node_id: attrs}
      edges: {eid: {"from": u, "to": v, ...}}
      probs: {} if probs.json missing
    """
    data_dir = Path(data_dir)

    # ---- nodes ----
    nodes_raw = json.loads((data_dir / "nodes.json").read_text(encoding="utf-8"))
    if isinstance(nodes_raw, dict):
        # already {id: attrs}
        nodes = nodes_raw
    elif isinstance(nodes_raw, list):
        # list of {"id": "...", ...}
        nodes = {n["id"]: {k: v for k, v in n.items() if k != "id"} for n in nodes_raw}
    else:
        raise TypeError("nodes.json must be dict or list")

    # ---- edges ----
    edges_raw = json.loads((data_dir / "edges.json").read_text(encoding="utf-8"))
    edges: Dict[str, Any] = {}

    if isinstance(edges_raw, dict):
        # already keyed by eid; ensure 'from'/'to' exist (or map source/target)
        for eid, e in edges_raw.items():
            if "from" in e and "to" in e:
                edges[eid] = e
            elif "source" in e and "target" in e:
                edges[eid] = {"from": e["source"], "to": e["target"],
                              **{k: v for k, v in e.items() if k not in ("source", "target")}}
            else:
                raise KeyError(f"Edge {eid} missing 'from'/'to' or 'source'/'target'")
    elif isinstance(edges_raw, list):
        # list of {"eid": "...", "source": "...", "target": "...", ...}
        for e in edges_raw:
            eid = e.get("eid")
            if not eid:
                raise KeyError("Edge entry in list missing 'eid'")
            if "from" in e and "to" in e:
                edges[eid] = {k: v for k, v in e.items() if k != "eid"}
            elif "source" in e and "target" in e:
                edges[eid] = {"from": e["source"], "to": e["target"],
                              **{k: v for k, v in e.items() if k not in ("eid", "source", "target")}}
            else:
                raise KeyError(f"Edge {eid} missing 'from'/'to' or 'source'/'target'")
    else:
        raise TypeError("edges.json must be dict or list")

    # ---- probs ----
    probs_path = data_dir / "probs.json"
    if probs_path.exists():
        probs = json.loads(probs_path.read_text(encoding="utf-8"))
    else:
        probs = {}

    return nodes, edges, probs

def build_base_graph(nodes: Dict[str, Dict[str, Any]],
                     edges: Dict[str, Dict[str, Any]]) -> nx.Graph:
    G = nx.Graph()
    for nid, attrs in nodes.items():
        G.add_node(nid, **attrs)
    for eid, e in edges.items():
        u, v = e["from"], e["to"]
        attr = {"eid": eid, **{k: v for k, v in e.items() if k not in ("from", "to")}}
        G.add_edge(u, v, **attr)
    return G

# ---------- tests ----------

def test_draw_graph_from_data1():
    data_dir = Path("datasets/ema_highway/v1/data")   # adjust if relative path differs
    assert data_dir.exists(), f"Data dir not found: {data_dir}"

    out_path = graphs.draw_graph_from_data(
        data_dir,
        output_name="graph.png",
        with_node_labels=True,
        with_edge_labels=True
    )

    # check the file is created
    assert out_path.exists(), f"Graph image not created: {out_path}"
    assert out_path.stat().st_size > 0, "Output image is empty"

    print(f"[ok] Graph created at {out_path.resolve()}")

def test_compute_edge_lengths1():
    nodes, edges, probs = load_dataset_any("datasets/toynet_11edges/v1/data")

    lengths = graphs.compute_edge_lengths(nodes, edges)

    expected = {'e01': np.sqrt(2), 'e02': 1.0, 'e03': np.sqrt(2), 'e04': 1.0,
                'e05': np.sqrt(2), 'e06': np.sqrt(2), 'e07': 1.0, 'e08': 1.0,
                'e09': np.sqrt(2), 'e10': 1.0, 'e11': np.sqrt(2)}
    
    for eid, val in expected.items():
        assert eid in lengths, f"{eid} missing from computed lengths"
        assert np.isclose(lengths[eid], val, rtol=1e-5, atol=1e-8), \
            f"{eid}: got {lengths[eid]}, expected {val}"

