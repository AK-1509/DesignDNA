---
name: export-to-figma
description: Push a design-dna design system into Figma through the Figma MCP server. It creates variable collections (Primitives, semantic Color with Light/Dark modes, Typography, Spacing), text and effect styles, and a Foundations page bound to those variables. Use it when the user wants the generated design system, tokens or styles in Figma.
argument-hint: "[figma file URL]"
---

# Export to Figma

The generator already wrote everything Figma needs into `.design-dna/output/<slug>/figma/`:

| File | What it does in Figma |
|---|---|
| `01-variables.js` | Collections **Primitives** (hidden from publishing, no scopes), **Color** (Light + Dark modes, aliases to primitives, scoped to fill/text/stroke), **Typography** and **Spacing**. Each variable has WEB code syntax `var(--…)` matching `tokens.css`. |
| `02-styles.js` | Text styles (`Display/XL` … `Code`) with font size bound to variables, and effect styles `Shadow/SM|MD|LG`. It picks the closest available weight of the brand face, then the Google substitute, then Inter, and reports any substitution. |
| `03-foundations.js` | A **Foundations** page: light and dark semantic swatches side by side (explicit variable modes), palette ramps, type specimens and spacing bars, all bound to variables and styles. |
| `variables.json` | The data the scripts embed, for inspection or other tools. |

Every script is idempotent: it updates by name, so re-running after a regenerate updates the file in place.

## Workflow

1. **Make sure outputs are current.** If `.design-dna/output/<slug>/figma/` is missing or older than `overrides.json` or `profile.json`, run the `generate-design-system` skill first.

2. **Figma MCP.** The Figma MCP server's `use_figma` tool must be connected and authorized. If Figma tools report that auth is required, tell the user to authorize the Figma connector (claude.ai connector settings, or `/mcp` in an interactive Claude Code terminal), then stop.

3. **Pick the target file.** Use the Figma URL the user gave. Otherwise ask whether to use an existing file or create a new Design file. To create one, load the `figma:figma-create-new-file` skill first, as it requires.

4. **Load the `figma:figma-use` skill before any `use_figma` call.** It is mandatory and documents the tool's calling conventions. The scripts use top-level `await` and end with `return {…}`. If figma-use says the code must be wrapped differently, adapt the wrapper but keep the body unchanged.

5. **Run the scripts in order**, one `use_figma` call each, passing the file contents as the code:
   1. `01-variables.js`, then check the returned `created/updated` counts and `warnings`. A "Mode 'Dark' not added" warning means the Figma plan limits modes. Tell the user that dark values were skipped and are still in `tokens/color.dark.tokens.json`.
   2. `02-styles.js`, then report `substitutions` (brand face → font actually used) so the user knows what to install or license.
   3. `03-foundations.js`, then take a screenshot of the returned frame (`get_screenshot`) and show it.
   If a script errors, read the message, fix the smallest thing (usually an API name mismatch described in figma-use), and retry. Don't rewrite the data.

6. **Optional next steps** to offer:
   - Build components on these variables with the `figma:figma-generate-library` skill. Use `DESIGN.md` → *Components* as the recipe list, since it maps every component to semantic tokens.
   - Native import: Figma can also import DTCG JSON (`tokens/*.tokens.json`) through its variables import. Use `--format 2025` if the importer expects spec-2025 values.
   - Code Connect (`figma:figma-code-connect`) once components exist in code.

## Rules

- Don't delete user content. `03-foundations.js` only replaces the frame it created itself, which is marked with plugin data.
- Variables are created in the open file (local variables). Publishing them as a library is the user's call.
