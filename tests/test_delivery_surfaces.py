from __future__ import annotations

import importlib
import tomllib
from pathlib import Path

from benchmarks.release_readiness import _offline_provider_diagnostic
from minicode.release_readiness import ReleaseCheck
from minicode.structure_check import (
    CURRENT_DOCUMENTS,
    _check_documentation_consistency,
    check_material_inventory,
)


ROOT = Path(__file__).resolve().parents[1]


def test_all_console_entrypoints_resolve() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    scripts = project["project"]["scripts"]
    assert project["project"]["name"] == "minicode-loop"
    assert set(scripts) == {
        "minicode-py",
        "minicode-headless",
        "minicode-readiness",
        "minicode-structure-check",
        "minicode-provider-smoke",
    }
    for target in scripts.values():
        module_name, attribute = target.split(":", 1)
        assert callable(getattr(importlib.import_module(module_name), attribute))


def test_docker_image_copies_all_runtime_packages() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert 'org.opencontainers.image.title="MiniCode Loop"' in dockerfile
    assert "COPY minicode/ ./minicode/" in dockerfile
    assert "COPY Main/ ./Main/" in dockerfile
    assert "COPY Package/ ./Package/" in dockerfile
    assert 'CMD ["--help"]' not in dockerfile


def test_compose_only_exposes_supported_modes() -> None:
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert "image: minicode-loop:latest" in compose
    assert "minicode-loop-home:" in compose
    assert "  cli:" in compose
    assert "  headless:" in compose
    assert "  gateway:" not in compose
    assert "  cron:" not in compose
    assert "minicode.cron_runner" not in compose


def test_release_evidence_missing_diagnostic_stays_offline() -> None:
    failed_eval = ReleaseCheck(
        label="runtime-profile-eval",
        command="python benchmarks/runtime_profile_eval.py",
        exit_code=1,
        status="failed",
        summary="offline evaluation failed",
        stderr="failure details",
    )

    diagnostic = _offline_provider_diagnostic(failed_eval)

    assert diagnostic["outcome"] == "provider_channel_unavailable"
    assert diagnostic["command"] == "offline release readiness"
    assert diagnostic["failure_category"] == "configuration"
    assert diagnostic["stderr"] == "failure details"
    release_source = (ROOT / "benchmarks" / "release_readiness.py").read_text(
        encoding="utf-8"
    )
    assert '"headless-provider-smoke"' not in release_source


def test_release_evidence_uses_project_local_state() -> None:
    release_source = (ROOT / "benchmarks" / "release_readiness.py").read_text(
        encoding="utf-8"
    )
    runtime_source = (ROOT / "benchmarks" / "runtime_profile_eval.py").read_text(
        encoding="utf-8"
    )

    assert 'REPO_ROOT / ".temp" / "release-home"' in release_source
    assert 'env["USERPROFILE"] = str(RELEASE_STATE_HOME)' in release_source
    assert 'runtime={"model": "offline-release-evidence"}' in release_source
    assert 'REPO_ROOT / ".temp" / "runtime-profile-home"' in runtime_source


def test_current_material_and_documentation_inventory_is_consistent() -> None:
    result = check_material_inventory(ROOT)
    assert result["passed"] is True, result["findings"]


def test_documentation_gate_rejects_retired_command_claim(tmp_path: Path) -> None:
    public_entries = " ".join(
        (
            "minicode-py",
            "minicode-headless",
            "minicode-readiness",
            "minicode-structure-check",
            "minicode-provider-smoke",
        )
    )
    for relative_path in CURRENT_DOCUMENTS:
        path = tmp_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(public_entries, encoding="utf-8")
    (tmp_path / "README.md").write_text(
        public_entries + " minicode-gateway",
        encoding="utf-8",
    )
    (tmp_path / "docker-compose.yml").write_text(
        "services:\n  cli:\n  headless:\n",
        encoding="utf-8",
    )

    findings: list[dict[str, str]] = []
    _check_documentation_consistency(tmp_path, findings)

    assert any(item["ruleId"] == "DocumentationRetiredSurface" for item in findings)
