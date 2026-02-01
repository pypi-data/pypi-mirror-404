from pathlib import Path
import json, yaml
from typing import Dict, Any, Tuple

def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def dataset_paths(repo_root: Path, dataset: str, version: str = "v1") -> Tuple[Path, Path, Path]:
    """
    Return (nodes.json, edges.json, probs.json) for a given dataset folder.
    Works with your existing layout:
      repo_root/<dataset>/<version>/data/{nodes,edges,probs}.json
    Example:
      dataset_paths(Path('.'), 'toynet-11edges', 'v1')
    """
    base = repo_root / dataset / version / "data"
    return base/"nodes.json", base/"edges.json", base/"probs.json"
