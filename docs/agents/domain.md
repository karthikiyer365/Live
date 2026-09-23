# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Layout: multi-context

This repo is a collection of independent projects, one per top-level folder. Each project is its own context.

```
/
├── CONTEXT-MAP.md                 ← points at each project's CONTEXT.md
├── docs/adr/                      ← repo-wide decisions
├── google-playstore-analysis/
│   ├── CONTEXT.md
│   └── docs/adr/                  ← project-specific decisions
├── indian-ecopolitical-growth/
│   ├── CONTEXT.md
│   └── docs/adr/
└── topic-classification/
    ├── CONTEXT.md
    └── docs/adr/
```

A new project folder gets its own `CONTEXT.md` and `docs/adr/` and an entry in `CONTEXT-MAP.md`.

## Before exploring, read these

- **`CONTEXT-MAP.md`** at the repo root: it points at one `CONTEXT.md` per project. Read the one for the project you're working in.
- **`<project>/docs/adr/`**: read ADRs that touch the area you're about to work in. Also check root `docs/adr/` for repo-wide decisions.

If any of these files don't exist, **proceed silently**. Don't flag their absence; don't suggest creating them upfront. The `/domain-modeling` skill (reached via `/grill-with-docs` and `/improve-codebase-architecture`) creates them lazily when terms or decisions actually get resolved.

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis, a test name), use the term as defined in that project's `CONTEXT.md`. Don't drift to synonyms the glossary explicitly avoids. Don't carry one project's vocabulary into another.

If the concept you need isn't in the glossary yet, that's a signal: either you're inventing language the project doesn't use (reconsider) or there's a real gap (note it for `/domain-modeling`).

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding:

> _Contradicts ADR-0007 (event-sourced orders), but worth reopening because…_
