# Mock Paper Generator mockups (v2)

Static design mockups only. No Phase 0-4 code is implemented.

Open `index.html` directly, or:

```bash
uv run python -m http.server 8090 --directory design/mockups
# http://127.0.0.1:8090
```

## Pages

- `index.html` - home / subject table
- `subject-csc662.html` - subject hub with three paths
- `library.html` - filter form + details table list
- `generate.html` - form + real-event job status table
- `gallery.html` - public 7-day gallery table + takedown
- `paused.html` - daily-cap fallback

## Footer

Every page ends with contact and Git-repository placeholders (`contact@example.com`, `github.com/your-username/paper-generator`). Replace them with the real details before deployment.

## Style

Plain document UI: Verdana 12 px, 1 px table borders, blue underlined links,
no cards, no shadows, no gradients, no icons, no animation. The CSS file is
deliberately small.

## Notes

- The job outline is updated from real events in the live app. The mockup is a
  static snapshot; there is no fake timer or typewriter.
- Library filtering is HTMX in the live app. The mockup shows the filter form
  and the full 20-row table.
- Downloads in the mockup are `#` links. Filename rules are in
  `design/DESIGN.md`.
