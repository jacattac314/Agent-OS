# Agent OS - Vault Constitution

This vault is Jack's autonomous local memory layer. Treat it as the source of
truth for agent context, project history, decisions, and long-running personal
operating state.

## Authority Model
- Raw captures are immutable evidence. Do not edit or delete raw inputs in
  `Inbox/`, `Journal/`, `Tasks/inbox.md`, or raw `Research/` notes during
  synthesis.
- Canonical notes may be rewritten, merged, split, or retired autonomously when
  new evidence improves the vault.
- Deletes are banned. Retire obsolete canonical notes by moving them into
  `Archive/` and preserving their source history.
- Every durable canonical claim should cite a source path, heading, or audit
  entry. If evidence conflicts, preserve the strongest current claim and log the
  unresolved conflict in `System/contradictions.md`.
- Secrets, credentials, private tokens, and auth URLs must never be copied into
  tracked canonical notes or audit entries.

## Vault Layout
- `Index.md` - generated map of active projects, people, organizations,
  decisions, research, open questions, and tasks.
- `Inbox/` - raw freeform capture files. These are evidence, not canonical
  notes.
- `Journal/` - daily notes (`YYYY-MM-DD.md`). Check today's file for active
  focus and blockers.
- `Projects/` - canonical project notes.
- `People/` - canonical person notes.
- `Organizations/` - canonical company, customer, vendor, and institution notes.
- `Research/` - source-backed research notes and captured references.
- `Tasks/` - active task lists. `inbox.md` is raw capture.
- `Memory/` - durable decisions, preferences, operating rules, and patterns.
- `Output/` - finished artifacts.
- `System/` - synthesis state, audit ledger, contradiction ledger, and prompts.
- `Archive/` - retired canonical notes. Do not delete archived notes.
- `Templates/` - note templates. Do not modify unless explicitly asked.

## Canonical Note Contract
Use YAML frontmatter for canonical notes where practical:

```yaml
---
type: project | person | organization | decision | research | memory | task
aliases: []
status: active | paused | retired | reference
updated: YYYY-MM-DD
sources: []
---
```

Keep canonical notes concise, current, and evidence-linked. Prefer updating an
existing note over creating a near-duplicate. Use kebab-case filenames.

## Autonomous Synthesis Workflow
1. Scan raw inputs from `Inbox/`, `Tasks/inbox.md`, `Journal/*.md`, and raw
   `Research/*.md`.
2. Read `Index.md`, `System/synthesis-state.json`, and relevant canonical notes.
3. Rewrite canonical notes to absorb new evidence.
4. Update `Index.md`, `System/audit.jsonl`, and `System/contradictions.md` in
   the same run.
5. Preserve raw input files exactly.
6. Let the synthesis runner validate raw preservation, scan for secrets, and
   commit valid changes.

## Task Workflow
1. Before coding or planning, check `Journal/{{today}}.md`, `Index.md`, and any
   relevant canonical project note.
2. After completing meaningful work, update the relevant canonical note and add
   a short journal or audit entry.
3. New durable context belongs in canonical notes, not scattered one-off files.
