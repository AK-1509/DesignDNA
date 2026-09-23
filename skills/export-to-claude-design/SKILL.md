---
name: export-to-claude-design
description: Package a design-dna design system for Claude Design (claude.ai/design) so designs, decks and prototypes made there follow it. Use it when the user wants the learned system available in Claude Design, wants a shareable specimen page, or asks to sync the system to a claude.ai design-system project.
---

# Export to Claude Design

`generate` writes a ready-made bundle at `.design-dna/output/<slug>/claude-design/`:

```
claude-design/
  README.md          the full system guide (the same content as DESIGN.md), which Claude Design reads first
  tokens.css         CSS variables + light/dark semantics + .text-* classes
  tokens.json        combined DTCG tokens (semantic colors carry light/dark in $extensions.mode)
  index.html         the full specimen
  preview/*.html     one card per group (Brand, Colors, Type, Spacing, Components). Each file's first line is
                     <!-- @dsCard group="…" -->, which the Design System pane indexes
```

## Workflow

1. **Make sure the bundle is current.** If it's missing or older than `profile.json` or `overrides.json`, run the `generate-design-system` skill first.

2. **Choose the route.** Ask the user if it's unclear:

   **A. Sync into a claude.ai/design design-system project (recommended).** The user runs the `/design-sync` skill themselves and points it at the bundle folder, e.g.
   `/design-sync .design-dna/output/<slug>/claude-design`.
   That skill lists or creates the design-system project, shows a plan of exactly which paths will be written, and uploads after the user approves. Don't call the design-sync tooling yourself outside that skill; hand off with the exact command and folder path. When `/design-sync` isn't available in this client, use route B or C.

   **B. Start a design system from an Artifact type.** If this client has the Artifact tool, call it with `action: "quickstart"` and `intent: "other"`. If the result lists a **Design System** type, create the design system from that type with the system's name, and follow the type's own instructions for filling it. Use `README.md` as the guide, `tokens.css` as the stylesheet and the `preview/*.html` cards as specimens. The type's instructions win over this skill where they differ.

   **C. Manual.** Tell the user to create a design system in Claude Design and upload the contents of the `claude-design/` folder. README.md and tokens.css are the essential files.

3. **Shareable specimen (optional).** If the user wants a link to show the team, publish `claude-design/index.html` as an artifact. It is self-contained and supports light and dark themes. It's private until they share it.

4. **Confirm what the system tells Claude Design.** Summarise the three things that most shape generated designs: the palette and its proportion (for example "vermilion sparingly on warm paper"), the type pairing and scale, and the top principles and don'ts from README.md. If any of these are generic because the corpus was thin, say so and suggest adding sources.

## Keeping it in sync

After new sources are learned or overrides change: run `learn`, then `generate`, then re-run route A. `/design-sync` diffs the project and only uploads what changed.
