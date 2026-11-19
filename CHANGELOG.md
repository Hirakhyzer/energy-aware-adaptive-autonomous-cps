# Changelog

## 0.1.1 — 2026-11-19

- Validate that all continuous scenario parameters are finite real numbers with appropriate bounds.
- Require integer-valued steps, sensor/control age limits, and nonnegative random seeds; reject booleans masquerading as numbers.
- Reject malformed, nonnumeric, or non-finite waypoint coordinates with clear configuration errors.
- Validate benchmark seed and policy inputs before running matched scenarios.
- Reject incomplete benchmark reports before creating output directories.
- Add parameterized regression tests for invalid JSON, routes, benchmark input, and report saving.
- Keep the synthetic kinematic, energy, and policy models unchanged; no new experimental evidence is claimed.

## 0.1.0 — 2026-11-06

- Initial simulation-first energy-aware adaptive autonomous CPS benchmark and CLI.
