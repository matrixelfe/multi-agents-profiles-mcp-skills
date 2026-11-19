"""Tests for OAC V3.4 reader, ECC contextual recommender (T01-T20), and safe UI updates."""
from __future__ import annotations

from pathlib import Path
import pytest

from agent_tooling.oac.reader import load_oac_snapshot, parse_agent_markdown, update_oac_assignment
from agent_tooling.resolver.recommend import recommend


def _write_rec_policy(root: Path) -> None:
    (root / "recommendations.yaml").write_text(
        """
schema_version: 1
agent_skill_recommendations:
  defaults:
    load_on_discovery: false
    auto_install: false
  agents:
    auto-orchestrator:
      recommended:
        - resource: ecc/agentic-engineering
          when: complex_orchestrated_task
          policy: RECOMMENDED
        - resource: ecc/iterative-retrieval
          when: missing_codebase_context
          policy: RECOMMENDED
      allowed_subagents:
        - code-explorer
        - code-implementer
        - code-specialist
    opencoder:
      recommended:
        - resource: ecc/agent-introspection-debugging
          when: repeated_failure_no_progress
          policy: RECOMMENDED
""",
        encoding="utf-8",
    )


def test_t01_ask_simple_question_no_skills(tmp_path: Path) -> None:
    _write_rec_policy(tmp_path)
    res = recommend("ask", "What is a closure in JavaScript?", tooling_root=tmp_path, skills_root=tmp_path)
    assert res["skills"] == []
    assert res["subagents"] == []


def test_t02_empty_repo_core_profile(tmp_path: Path) -> None:
    _write_rec_policy(tmp_path)
    res = recommend("auto-orchestrator", "hello", project_profile="core", tooling_root=tmp_path, skills_root=tmp_path)
    assert res["project_profile"] == "core"
    assert len(res["skills"]) <= 3


def test_t07_t08_t09_contextual_signals_and_allowlist(tmp_path: Path) -> None:
    _write_rec_policy(tmp_path)
    # T07: missing codebase context -> iterative-retrieval & code-explorer
    r1 = recommend("auto-orchestrator", "explore and find where routing lives", tooling_root=tmp_path, skills_root=tmp_path)
    assert any(s["resource_id"] == "ecc/iterative-retrieval" for s in r1["skills"])
    assert any(sa["recommended_agent"] == "code-explorer" and sa["invocation_allowed"] for sa in r1["subagents"])

    # T08: repeated failure -> introspection
    r2 = recommend("opencoder", "tests keep failing in a retry loop", tooling_root=tmp_path, skills_root=tmp_path)
    assert any(s["resource_id"] == "ecc/agent-introspection-debugging" for s in r2["skills"])

    # T09: code-qa blocked if not in allowlist
    r3 = recommend(
        "auto-orchestrator",
        "review and audit security",
        tooling_root=tmp_path,
        skills_root=tmp_path,
        agent_permissions={"allowed_subagents": ["code-explorer", "code-implementer", "code-specialist"]},
    )
    qa = [sa for sa in r3["subagents"] if sa["recommended_agent"] == "code-qa"]
    assert qa and qa[0]["invocation_allowed"] is False


def test_t11_missing_skill_never_marked_available(tmp_path: Path) -> None:
    _write_rec_policy(tmp_path)
    res = recommend("opencoder", "stuck in a retry loop", tooling_root=tmp_path, skills_root=tmp_path)
    assert res["skills"][0]["available"] is False
    assert res["skills"][0]["permission"] == "install_required"
    assert res["skills"][0]["load_now"] is False


def test_t15_incompatible_client_surface_blocks_skills(tmp_path: Path) -> None:
    _write_rec_policy(tmp_path)
    res = recommend(
        "auto-orchestrator",
        "plan complex refactor",
        client_target="claude:code-cloud",
        tooling_root=tmp_path,
        skills_root=tmp_path,
    )
    assert res["surface_status"] == "UNSUPPORTED"
    assert all(s["decision"] == "BLOCKED" for s in res["skills"])


def test_t13_spend_guard_blocks_payg_model_assignment(tmp_path: Path) -> None:
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "oac-routing.yaml").write_text("assignments:\n  agent/ask.md: opencode/deepseek-v4.1-flash-free\n", encoding="utf-8")
    with pytest.raises(ValueError, match="spend-guard blocked provider"):
        update_oac_assignment("agent/ask.md", "alibaba/deepseek-v4.1-flash-1017", opencode_root=tmp_path)


def test_parse_agent_markdown_permissions(tmp_path: Path) -> None:
    ad = tmp_path / "agents"
    ad.mkdir()
    md = ad / "auto-orchestrator.md"
    md.write_text(
        "---\nmode: primary\nmodel: opencode-go/glm-5.3\npermissions:\n  - action: subagent\n    resource: code-explorer\n    effect: allow\n  - action: bash\n    resource: '*'\n    effect: deny\n---\n# Body\n",
        encoding="utf-8",
    )
    parsed = parse_agent_markdown(md, tmp_path)
    assert parsed["allowed_subagents"] == ["code-explorer"]
    assert "bash:*" in parsed["denied_tools"]
