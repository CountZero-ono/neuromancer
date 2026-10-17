# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-10-17

### Added
- **Gemini 4 Argon Dedicated Quota Support**: Added dynamic bucket resolution for Google's separate weekly Argon allowance (`[ARGON 7D]`), preventing deep reasoning and agentic coding loops from masking Flash limits.
- **Adaptive Quota Engine**: Intelligent bucket discovery matching active models (Gemini 4 Argon, standard Gemini Flash/Pro, 3P models like Claude/Sonnet) with automatic fallback to arbitrary backend pools if Google renames telemetry keys.

### Changed
- Refactored quota parser from hardcoded static keys (`gemini-5h`, `3p-5h`) to model-aware heuristic matcher with null-safe numeric guards.

## [1.1.0] - 2026-08-09

### Added
- **Project Telemetry Badge**: Auto-detects project workspace from telemetry JSON, Git repository root, or directory fallback (`📦 neuromancer`).

## [1.0.1] - 2026-08-04

### Added
- **Context Ceiling & Token Ratio**: Exact context window ceiling (`132k / 1M`) with input/output token breakdown indicators (`(↑120k ↓12k)`).
- **Responsive Adaptive HUD**: Automatically wraps into a 3-line tree layout on narrow terminals (<100 columns).

### Fixed
- Type-safe numeric casts for resumed sessions with `null` or `'N/A'` quota attributes.

## [1.0.0] - 2026-08-02

### Added
- Initial release of Neuromancer Cyberpunk Telemetry Deck & Statusline for Antigravity CLI.
- High-density Onyx deck HUD with dynamic Amber indicator gauges for Context Window and rolling quotas (`5H` and `7D`).
- Battery and AC mains power diagnostics via `/sys/class/power_supply` and macOS `pmset`.
- 1-step installation script auto-configuring `settings.json`.
