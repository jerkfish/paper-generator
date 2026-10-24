# Phase 4 deployment: library-only and live mode

Status: the **library-only** deployment is live at
**https://uitmpapergen.download**. The **live container mode** is scaffolded
but not deployed.

## 1. Library-only mode (live)

- Static HTML/CSS/JS pages are built by `scripts/build_public_bundle.py`.
- Papers and schemes are in R2 under `library/<SUBJECT>/`.
- The Worker serves R2 objects and the D1-backed gallery.
- No Python process and no LLM API key exist in this mode.
- Cost: $0 on the R2 free tier, within the project's stricter internal
  budgets (1 GiB storage, 10,000 Class A/month, 100,000 Class B/month).

Publish:

```bash
uv run python -m scripts.build_public_bundle --out outputs/public_bundle
uv run --with boto3 python -m scripts.r2_sync --bundle outputs/public_bundle --upload
cd cloudflare/worker && bun run deploy
```

## 2. Live mode (scaffolded, not deployed)

Live mode runs the existing FastAPI app in a Linux container and puts a Worker
in front of it.

Files:

- `Dockerfile` — Python 3.12, uv, LibreOffice Writer, Graphviz, fonts.
- `.dockerignore` — excludes `.env`, `.git`, `CSC662/`, `outputs/`, tests.
- `cloudflare/container-worker/` — Worker, Durable Object container
  lifecycle, Wrangler config, deployment notes.
- `src/assemble/pdf_export.py` — Word COM on Windows; LibreOffice headless
  when `MOCKGEN_PDF_ENGINE=libreoffice` or on a non-Windows host.
- `GET /health` — container readiness endpoint.

### Requirements

- **Cloudflare Workers Paid plan: $5 USD/month.** Containers has no free tier.
- Docker (or a Docker-compatible engine) on the deploying machine. Without it,
  use a prebuilt registry image instead of a local Dockerfile.
- A Gemini API key stored as a Worker secret. Never put it in the image,
  `.env`, or the bundle. `cloudflare/container-worker/.dev.vars.example`
  contains only the placeholder `REPLACE_WITH_GEMINI_API_KEY`; the Worker
  refuses to start the container while that placeholder is still in place.
  `PUBLIC_BUILD=1` also fails closed: it selects Gemini and will not fall back
  to DeepSeek when the Gemini key is missing or a placeholder.
- The container needs the private `data/` folder: deck chunks, templates,
  planner spreadsheet and past-paper text. Deploying it uploads that material
  to Cloudflare. Only do this if you accept that privacy/legal trade-off.

### Build and run locally

```bash
docker build -t papergen-live .
docker run --rm -p 8000:8000 \
  -e PUBLIC_BUILD=1 \
  -e MOCKGEN_MODEL=gemini-3.5-flash \
  -e MOCKGEN_PDF_ENGINE=libreoffice \
  -e GEMINI_API_KEY=REPLACE_WITH_GEMINI_API_KEY \
  papergen-live
# http://127.0.0.1:8000/health
```

Replace the placeholder with a real key only in your local shell or a
gitignored `.env.live`; never bake it into the image. The container starts
but live generation reports a missing/placeholder key.

On Windows, the local FastAPI app still uses Word COM by default. Set
`MOCKGEN_PDF_ENGINE=libreoffice` to test the container path locally.

### Deploy

```bash
cd cloudflare/container-worker
bun x wrangler secret put GEMINI_API_KEY
bun x wrangler deploy
```

Then optionally enable the `live.uitmpapergen.download` route in
`wrangler.toml`. Keep the apex library-only Worker unchanged.

### Containers pricing (checked 2026-10-23)

Source: https://developers.cloudflare.com/containers/platform/pricing/

| Resource | Workers Paid included | Overage |
|---|---:|---:|
| Memory | 25 GiB-hours/month | $0.0000025 per GiB-second |
| CPU | 375 vCPU-minutes/month | $0.000020 per vCPU-second |
| Disk | 200 GB-hours/month | $0.00000007 per GB-second |
| Egress (NA/EU) | 1 TB/month | $0.025/GB |

Instance types (from the Containers limits page):

| Type | vCPU | Memory | Disk |
|---|---:|---:|---:|
| lite | 1/16 | 256 MiB | 2 GB |
| basic | 1/4 | 1 GiB | 4 GB |
| standard-1 | 1/2 | 4 GiB | 8 GB |

The scaffold uses `standard-1` (4 GiB, 1/2 vCPU) and sleeps after five idle
minutes. A typical one-paper run is active for roughly 1–3 minutes; the
included monthly memory/CPU allowance covers several hundred runs. `basic`
(1 GiB) is cheaper but may be too small for LibreOffice plus matplotlib. The
Gemini API cost is separate and remains capped per run by
`MOCKGEN_COST_CAP_USD`.

### LibreOffice cover caveat

The Windows pipeline uses Word COM. On Linux, LibreOffice headless currently
renders the MAT133 cover one page longer (8 pages vs 7 for seed 01). Until the
cover is tuned for LibreOffice, live mode should either serve DOCX only or
document the extra page. The library-only bundle is unaffected because its
PDFs were produced with Word COM.

## 3. What must never be uploaded

For the library-only bundle:

- `.env`, API keys, Wrangler secrets.
- `CSC662/` originals.
- `data/reference/`, `data/papers/`, lecture decks, OCR caches.
- `outputs/web_cache/`, raw planner/theory JSON, tests, internal reports.

For the live container:

- Never bake `.env` or API keys into the image; use Worker secrets.
- The private `data/` folder is required at runtime. Upload it only with
  explicit acceptance of the privacy/legal trade-off.
- Do not put `CSC662/` originals in the image; the read-only copies under
  `data/papers/` are sufficient for the generator.

## 4. Legal note

This is a personal study aid, not an official university paper. The generated
questions and marking schemes are not lecturer-marked. You are responsible for
confirming that you may process and host the past papers, lecture slides and
templates used by the generator. If you do not have that right, use the
library-only deployment and do not build the live container.
