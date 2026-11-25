"""Verify that backend and frontend minimum coverage floors remain >= 80%."""

from pathlib import Path
import re
import sys
import tomllib

MINIMUM_FLOOR = 80
ROOT = Path(__file__).resolve().parent.parent


def read_backend_floor(pyproject_path: Path) -> int:
    """Return configured pytest-cov fail_under integer from backend/pyproject.toml."""
    with pyproject_path.open("rb") as handle:
        data = tomllib.load(handle)
    raw = data["tool"]["coverage"]["report"]["fail_under"]
    return int(raw)


def read_frontend_floors(vitest_path: Path) -> dict[str, int]:
    """Return configured Vitest coverage threshold integers from frontend/vitest.config.ts."""
    content = vitest_path.read_text(encoding="utf-8")
    metrics = ("lines", "functions", "branches", "statements")
    floors: dict[str, int] = {}
    for metric in metrics:
        match = re.search(rf"{metric}\s*:\s*(\d+)", content)
        if not match:
            raise ValueError(f"Missing coverage threshold for {metric!r} in {vitest_path}.")
        floors[metric] = int(match.group(1))
    return floors


def main() -> int:
    """Validate that all coverage minimum thresholds are at least 80%."""
    backend_floor = read_backend_floor(ROOT / "backend" / "pyproject.toml")
    frontend_floors = read_frontend_floors(ROOT / "frontend" / "vitest.config.ts")

    failures: list[str] = []
    if backend_floor < MINIMUM_FLOOR:
        failures.append(f"backend fail_under={backend_floor} < {MINIMUM_FLOOR}")
    for metric, value in frontend_floors.items():
        if value < MINIMUM_FLOOR:
            failures.append(f"frontend {metric}={value} < {MINIMUM_FLOOR}")

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
