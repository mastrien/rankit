"""Verify that backend and frontend minimum coverage floors remain >= 80%."""

from pathlib import Path
import re
import sys
import tomllib

MINIMUM_FLOOR = 80
ROOT = Path(__file__).resolve().parent.parent
COMMENT_PATTERN = re.compile(r"//[^\n]*|/\*.*?\*/", re.DOTALL)
THRESHOLDS_BLOCK_PATTERN = re.compile(r"\bthresholds\s*:\s*\{([^}]*)\}", re.DOTALL)


def read_backend_floor(pyproject_path: Path) -> int:
    """Return configured pytest-cov fail_under integer from backend/pyproject.toml."""
    with pyproject_path.open("rb") as handle:
        data = tomllib.load(handle)
    raw = data["tool"]["coverage"]["report"]["fail_under"]
    return int(raw)


def _strip_js_comments(source: str) -> str:
    return COMMENT_PATTERN.sub("", source)


def _extract_thresholds_block(vitest_path: Path) -> str:
    stripped = _strip_js_comments(vitest_path.read_text(encoding="utf-8"))
    match = THRESHOLDS_BLOCK_PATTERN.search(stripped)
    if not match:
        raise ValueError(f"Missing coverage thresholds block in {vitest_path}.")
    return match.group(1)


def read_frontend_floors(vitest_path: Path) -> dict[str, int]:
    """Return configured Vitest coverage threshold integers from frontend/vitest.config.ts."""
    block = _extract_thresholds_block(vitest_path)
    metrics = ("lines", "functions", "branches", "statements")
    floors: dict[str, int] = {}
    for metric in metrics:
        match = re.search(rf"\b{metric}\s*:\s*(\d+)", block)
        if not match:
            raise ValueError(f"Missing coverage threshold for {metric!r} in {vitest_path}.")
        floors[metric] = int(match.group(1))
    return floors


def validate_floors(pyproject_path: Path, vitest_path: Path) -> tuple[int, dict[str, int], list[str]]:
    """Compare configured backend and frontend floors against MINIMUM_FLOOR."""
    backend_floor = read_backend_floor(pyproject_path)
    frontend_floors = read_frontend_floors(vitest_path)
    failures: list[str] = []
    if backend_floor < MINIMUM_FLOOR:
        failures.append(f"backend fail_under={backend_floor} < {MINIMUM_FLOOR}")
    for metric, value in frontend_floors.items():
        if value < MINIMUM_FLOOR:
            failures.append(f"frontend {metric}={value} < {MINIMUM_FLOOR}")
    return backend_floor, frontend_floors, failures


def main() -> int:
    """Validate that all coverage minimum thresholds are at least 80%."""
    backend_floor, frontend_floors, failures = validate_floors(
        ROOT / "backend" / "pyproject.toml",
        ROOT / "frontend" / "vitest.config.ts",
    )
    if failures:
        print(f"Coverage floor violation: {', '.join(failures)}")
        return 1

    print(
        f"Coverage floors verified (>= {MINIMUM_FLOOR}%): "
        f"backend={backend_floor}%, frontend={frontend_floors}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
