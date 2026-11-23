"""Exporters for token telemetry reports (Markdown, CSV, JSON)."""
from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from typing import Any


def export_report(
    summary: dict[str, Any],
    sessions: list[dict[str, Any]],
    anomalies: list[dict[str, Any]],
    fmt: str = "md",
) -> tuple[str, str, str]:
    """Return (content_text, mime_type, filename_ext)."""
    fmt = (fmt or "md").strip().lower()
    if fmt == "json":
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": summary,
            "sessions": sessions,
            "anomalies": anomalies,
        }
        return json.dumps(payload, indent=2, ensure_ascii=False), "application/json; charset=utf-8", "json"

    if fmt == "csv":
        buf = io.StringIO()
        cols = [
            "session_id",
            "harness",
            "mode",
            "primary_model",
            "profile_active",
            "started_at",
            "ended_at",
            "calls_count",
            "input_uncached",
            "cache_read",
            "cache_write",
            "output_tokens",
            "reasoning_tokens",
            "total_tokens",
            "cache_hit_ratio",
            "cost_usd",
            "ai_credits",
            "anomaly_count",
            "title_sanitized",
        ]
        writer = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        for row in sessions:
            writer.writerow(row)
        return buf.getvalue(), "text/csv; charset=utf-8", "csv"

    # Default: Markdown report
    kpis = summary.get("kpis") or {}
    lines = [
        "# Reporte de Telemetría y Consumo de Tokens Cross-Agent",
        "",
        f"> **Generado:** `{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}`  ",
        f"> **Rango:** `{summary.get('range', 'all')}` | **Harness:** `{summary.get('harness', 'all')}`",
        "",
        "## 1. KPIs Globales",
        "",
        "| Métrica | Valor |",
        "| :--- | ---: |",
        f"| **Sesiones Analizadas** | {int(kpis.get('sessions_count', 0)):,} |",
        f"| **Llamadas LLM Totales** | {int(kpis.get('calls_count', 0)):,} |",
        f"| **Tokens Totales** | {int(kpis.get('total_tokens', 0)):,} |",
        f"| **Input Uncached** | {int(kpis.get('input_uncached', 0)):,} |",
        f"| **Cache Read** | {int(kpis.get('cache_read', 0)):,} |",
        f"| **Output + Reasoning** | {int(kpis.get('output_tokens', 0)) + int(kpis.get('reasoning_tokens', 0)):,} |",
        f"| **Cache Hit Ratio Global** | {float(kpis.get('cache_hit_ratio', 0.0)):.1f}% |",
        f"| **Costo Estimado (USD)** | ${float(kpis.get('cost_usd', 0.0)):.4f} |",
        f"| **AI Credits (Copilot)** | {float(kpis.get('ai_credits', 0.0)):.2f} |",
        f"| **Anomalías Detectadas** | {int(kpis.get('anomalies_count', 0)):,} |",
        "",
        "## 2. Desglose por Harness",
        "",
        "| Harness | Sesiones | Calls | Tokens Totales | Promedio/Call | Cache % | Costo USD |",
        "| :--- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for h in summary.get("by_harness") or []:
        lines.append(
            f"| `{h['harness']}` | {int(h['sessions']):,} | {int(h['calls']):,} | "
            f"{int(h['total_tokens']):,} | {int(h['avg_tokens_per_call']):,} | "
            f"{float(h['cache_hit_ratio']):.1f}% | ${float(h['cost_usd']):.4f} |"
        )

    lines.extend([
        "",
        "## 3. Alertas y Anomalías Recientes",
        "",
        "| Severidad | Regla | Sesión | Valor | Recomendación |",
        "| :---: | :--- | :--- | ---: | :--- |",
    ])
    for a in anomalies[:25]:
        lines.append(
            f"| **{a['severity']}** | `{a['rule_code']}` | `{a['session_id'][:24]}` | "
            f"{float(a['metric_value']):,.0f} | {a['recommendation']} |"
        )

    lines.extend([
        "",
        "## 4. Top Sesiones por Consumo",
        "",
        "| Harness | Modelo | Calls | Total Tokens | Cache % | Costo USD | Anomalías | Título |",
        "| :--- | :--- | ---: | ---: | ---: | ---: | :-: | :--- |",
    ])
    for s in sessions[:25]:
        lines.append(
            f"| `{s['harness']}` | `{s['primary_model']}` | {int(s['calls_count']):,} | "
            f"{int(s['total_tokens']):,} | {float(s['cache_hit_ratio']):.1f}% | "
            f"${float(s['cost_usd']):.4f} | {int(s['anomaly_count'])} | {s['title_sanitized'][:40]} |"
        )

    return "\n".join(lines) + "\n", "text/markdown; charset=utf-8", "md"
