# Agent OS

A unified, agentic personal-computing environment that consolidates LLM endpoints, a persistent Markdown knowledge base, system-level CLI tools, and real-time screen/audio context into a single autonomous loop. This repository holds the Obsidian-style vault and configuration that drives the setup.

## Overview

Agent OS replaces manual, application-siloed workflows with a continuous "second brain" loop: context is captured, written to Markdown, parsed by an LLM planner, executed by background agents, and the results are written back to the vault as historical context for future runs.

It uses a hybrid model: heavy cognitive work (planning, reasoning) is offloaded to cloud LLM APIs, while the local machine handles lightweight automation, Markdown indexing, and background OCR. This keeps the system usable on memory-constrained hardware.

## Architecture (7 Layers)

| Layer | Name | Component | Function |
|-------|------|-----------|----------|
| 1 | Hardware | Local Mac (energy-efficient SoC) | Compute, background NPU processing, low-power standby |
| 2 | Memory | Obsidian-style Markdown vault | Shared local "second brain" for persistent context |
| 3 | Brain | Cloud LLM via OpenRouter | High-speed, cost-effective planning and reasoning |
| 4 | Agents | Background agents + Claude Code | Autonomous goal execution and systems-level coding |
| 5 | Command Center | Next.js dashboard + GUI | Monitor and control parallel agent streams |
| 6 | Production | CLI tools (video, deploy) | Programmatic outputs and deployments |
| 7 | The Loop | Feedback flywheel | Coordinates capture and execution into a self-improving cycle |

## Repository Structure

- `Journal/` — Date-slugged daily logs and captured conversations
- `Memory/` — Persistent memories and long-term context
- `Output/` — Build artifacts and deployment output
- `Projects/` — Active project notes
- `Research/` — Reference material and research notes
- `Tasks/` — Extracted action items and task logs
- `Templates/` — Note templates
- `CLAUDE.md` — Project instructions for Claude Code

## The Feedback Loop

1. Capture — Real-time audio/screen context is captured throughout the day.
2. Sync — Transcripts are summarized and written to the vault as Markdown.
3. Extract — The LLM planner parses new notes and extracts tasks.
4. Execute — Background agents run the outstanding tasks autonomously.
5. Deploy — Results are compiled into artifacts and published.
6. Re-entry — A structured summary is written back to the vault, becoming context for the next cycle.

## Setup

High-level steps (see `CLAUDE.md` for the full machine-readable spec):

1. Install host dependencies (Node, Git, package manager, ripgrep, ffmpeg) and Claude Code.
2. Create the workspace and the vault directory structure.
3. Configure a cloud LLM router (e.g. OpenRouter) as the external "brain" via environment variables.
4. Install and configure the background agents and command-center dashboard.
5. Wire up production services for output and deployment.

## Notes

- Designed for memory-constrained machines (~8GB RAM): heavy inference is intentionally kept off-device.
- API keys are read from environment variables and should never be committed to this repository.
- Some components referenced in the setup are experimental or third-party; verify each tool before installing.

## License

No license specified yet.
