"""Unit tests for scripts/verify_coverage_floors.py."""

from pathlib import Path
import tempfile
import unittest

from scripts.verify_coverage_floors import read_frontend_floors, validate_floors


class VerifyCoverageFloorsTests(unittest.TestCase):
    """Ensure threshold parsing ignores comments and rejects low floors."""

    def test_ignores_commented_fake_thresholds_outside_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pyproject = tmp_path / "pyproject.toml"
            vitest = tmp_path / "vitest.config.ts"
            pyproject.write_text("[tool.coverage.report]\nfail_under = 80\n", encoding="utf-8")
            vitest.write_text(
                "// lines: 95\n/* functions: 95 */\nexport default {\n"
                "  coverage: { thresholds: { lines: 79, functions: 80, branches: 80, statements: 80 } }\n"
                "};\n",
                encoding="utf-8",
            )

            _, floors, failures = validate_floors(pyproject, vitest)

            self.assertEqual(floors["lines"], 79)
            self.assertEqual(failures, ["frontend lines=79 < 80"])

    def test_raises_when_thresholds_block_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vitest = Path(tmp) / "vitest.config.ts"
            vitest.write_text("export default { test: {} };\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                read_frontend_floors(vitest)


if __name__ == "__main__":
    unittest.main()
