# Evolution Narrative

A chronological record of evolution decisions and outcomes.

### [2026-03-28 22:15:31] INNOVATE - failed
- Gene: gene_gep_optimize_prompt_and_assets | Score: 0.20 | Scope: 6 files, 67 lines
- Signals: [protocol_drift, repeated_tool_usage:exec, high_failure_ratio, force_innovation_after_repair_loop]
- Strategy:
  1. Extract signals and determine selection rationale via Selector JSON
  2. Prefer reusing existing Gene/Capsule; only create if no match exists
  3. Refactor prompt assembly to embed assets (genes, capsules, parent event)
