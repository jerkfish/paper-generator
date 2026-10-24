# Live-mode Container Worker

This Worker is the optional Phase 4.2 deployment. It fronts the FastAPI
generator running in a Cloudflare Container. It is **not deployed**; the
library-only Worker at `../worker/` remains the live public site.

## What it does

- Starts one `standard-1` container (4 GiB) from `../../Dockerfile`.
- Waits for the FastAPI `/health` endpoint.
- Proxies requests to `0.0.0.0:8000` in the container.
- Runs the container with:

```text
PUBLIC_BUILD=1
MOCKGEN_PDF_ENGINE=libreoffice
MOCKGEN_MODEL=gemini-3.5-flash
GEMINI_API_KEY=<Worker secret>
MOCKGEN_COST_CAP_USD=0.05
```

## Prerequisites

- A **Workers Paid** plan. Cloudflare Containers has no free tier. The plan is
  **$5 USD/month** and includes 25 GiB-hours of memory, 375 vCPU-minutes and
  200 GB-hours of disk per month; overages are billed per 10 ms of active use.
- Docker (or another Docker-compatible engine) on the machine running
  `wrangler deploy`.
- The live Worker needs the private `data/` folder in the Docker build context:
  CSC662 theory generation reads lecture decks/past-paper chunks and the
  planner spreadsheet. Uploading that private material to Cloudflare is a
  privacy and legal decision; do not deploy this Worker unless you accept it.
- A Cloudflare API token with Workers Scripts Write, Workers R2 Storage Read,
  Containers Write and D1 Write (or `wrangler login`).
- `GEMINI_API_KEY` as a Worker secret:

```bash
cd cloudflare/container-worker
bun x wrangler secret put GEMINI_API_KEY
```

`.dev.vars.example` contains only `REPLACE_WITH_GEMINI_API_KEY`. The Worker
refuses to start the container while the key is missing or still a
placeholder; it never falls back to a key in the repository.

## Deploy

```bash
cd cloudflare/container-worker
bun x wrangler deploy
```

`wrangler deploy` builds and pushes the image. The first build is the slowest.
Add the optional `live.uitmpapergen.download` route in `wrangler.toml` after
the apex library Worker is confirmed stable.

## Cost and resource notes

- The container only runs while handling a request and goes to sleep after
  five idle minutes (`INACTIVITY_TIMEOUT_MS`).
- `standard-1` is 1/2 vCPU, 4 GiB memory and 8 GB disk. `basic` (1/4 vCPU,
  1 GiB) may be too small for LibreOffice plus matplotlib; use `standard-1`
  for reliable conversion.
- Memory and disk are billed on provisioned resources while the container is
  active; CPU is billed on active use.
- The library-only deployment remains $0 and continues to serve papers,
  schemes and the gallery from R2/D1.

## LibreOffice cover caveat

The Windows pipeline uses Word COM. The Linux container uses LibreOffice
headless. LibreOffice currently produces one extra page on the MAT133 cover
(8 pages instead of 7 in the seed-01 check), matching the cover-pagination
issue noted in the original phase plan. Until the template is tuned for
LibreOffice, the live deployment should either:

- serve DOCX only for generated papers, or
- accept the extra cover page and document it in the UI.

The library-only bundle is unaffected because its PDFs were built with Word COM.
