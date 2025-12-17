# Documentation

This directory contains project documentation (mostly static HTML) plus a few markdown files that are easier to maintain alongside code.

## Contents

- `index.html`: Documentation landing page
- `prd.html`: Product requirements document
- `architecture.html`: System architecture (star topology, data flow, stack)
- `agent-flow.html`: Agent flow diagrams (routing + streaming)
- `functional-spec.html`: Functional specification
- `technical-spec.html`: Technical specification
- `project-management.html`: Project management notes / lessons learned

Markdown docs:

- `docs/data-storage.md`: Data & storage model for the Tech Ops dashboard + investigations (runtime model + suggested DB schema)
- `docs/tech-ops-implementation-backlog.md`: Living backlog for the Tech Ops dashboard effort

## Viewing

Open `docs/index.html` in a browser and navigate via links.

## Updating

- Prefer updating markdown sources first when possible.
- If you regenerate HTML docs, verify links still work from `docs/index.html`.
