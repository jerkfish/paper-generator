# CSC429 — local public bundle

Status: **local bundle built; not published**

- Path: `outputs/public_bundle`
- Build command: `uv run python -m scripts.build_public_bundle --out outputs/public_bundle --subject CSC429 --seeds 1-20 --local-only --force`
- Seeds: **20**
- Paper files: **40** (DOCX + PDF)
- Scheme files: **40** (DOCX + PDF)
- Library manifest count: **20**
- Bundle validation problems: **0**
- R2 upload: **no**
- Worker deployment: **no**
- Publication permission after build: **false**

The `--local-only` flag includes available subjects without changing publication permission. It never uploads or deploys.
