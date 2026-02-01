from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))


@dataclass(frozen=True)
class IdeaContext:
    input_file: str
    dataset_id: str
    region: str
    delay: int
    template: str
    idea: str
    expression_list: list[str]


_FILENAME_RE = re.compile(
    r"^(?P<dataset>[^_]+)_(?P<region>[A-Za-z]+)_(?P<delay>[01])_idea_\d+\.json$"
)


def parse_filename_metadata(path: Path) -> tuple[str, str, int]:
    m = _FILENAME_RE.match(path.name)
    if not m:
        raise ValueError(
            "Unsupported filename format. Expected like: fundamental28_GLB_1_idea_<ts>.json; "
            f"got: {path.name}"
        )
    dataset = m.group("dataset")
    region = m.group("region")
    delay = int(m.group("delay"))
    return dataset, region, delay


def load_idea_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_context(path: Path) -> IdeaContext:
    dataset, region, delay = parse_filename_metadata(path)
    data = load_idea_json(path)

    template = str(data.get("template") or "")
    idea = str(data.get("idea") or "")
    expression_list = data.get("expression_list") or []
    if not isinstance(expression_list, list) or not all(isinstance(x, str) for x in expression_list):
        raise ValueError("expression_list must be a list of strings")

    return IdeaContext(
        input_file=str(path),
        dataset_id=dataset,
        region=region,
        delay=delay,
        template=template,
        idea=idea,
        expression_list=expression_list,
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Path to idea JSON")
    ap.add_argument("--out", required=True, help="Output idea_context.json")
    args = ap.parse_args()

    input_path = Path(args.input).resolve()
    out_path = Path(args.out).resolve()

    ctx = build_context(input_path)
    out_path.write_text(json.dumps(asdict(ctx), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote idea context: {out_path}")


if __name__ == "__main__":
    main()
