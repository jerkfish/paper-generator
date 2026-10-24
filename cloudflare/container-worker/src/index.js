/* Live-mode Worker fronting the FastAPI generator container.
 *
 * The library-only Worker stays at the apex. This Worker is intended for a
 * separate hostname such as live.uitmpapergen.download. It starts one
 * container, waits for /health, then proxies requests to the FastAPI app.
 */
import { DurableObject } from "cloudflare:workers";

const CONTAINER_PORT = 8000;
const INACTIVITY_TIMEOUT_MS = 5 * 60 * 1000;
const START_ATTEMPTS = 100;

export class Backend extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    this.starting = undefined;
    const container = ctx.container;
    if (container.running) {
      void ctx.blockConcurrencyWhile(() =>
        container.setInactivityTimeout(INACTIVITY_TIMEOUT_MS),
      );
    }
  }

  async fetch(request) {
    this.starting ??= this.startAndWaitForPort().finally(() => {
      this.starting = undefined;
    });
    await this.starting;

    const url = new URL(request.url);
    url.protocol = "http:";
    url.host = "container";
    const forwarded = new Request(url, request);
    forwarded.headers.delete("host");
    return this.ctx.container.getTcpPort(CONTAINER_PORT).fetch(forwarded);
  }

  async startAndWaitForPort() {
    const container = this.ctx.container;
    const apiKey = String(this.env.GEMINI_API_KEY || "").trim();
    if (!apiKey || /^(REPLACE|YOUR_|CHANGE_)/i.test(apiKey)
        || apiKey.toUpperCase().includes("PLACEHOLDER")) {
      throw new Error(
        "GEMINI_API_KEY is a placeholder; run " +
        "`wrangler secret put GEMINI_API_KEY` before starting the container",
      );
    }
    if (!container.running) {
      container.start({
        image: container.images.base,
        // LibreOffice plus matplotlib needs more than the 1 GiB basic tier
        // in practice; standard-1 provides 4 GiB for one paper at a time.
        instance: "standard-1",
        enableInternet: true,
        env: {
          PUBLIC_BUILD: "1",
          MOCKGEN_PDF_ENGINE: "libreoffice",
          MOCKGEN_MODEL: this.env.MOCKGEN_MODEL || "gemini-3.5-flash",
          MOCKGEN_GEMINI_MODEL:
            this.env.MOCKGEN_GEMINI_MODEL || "gemini-3.5-flash",
          MOCKGEN_COST_CAP_USD: this.env.MOCKGEN_COST_CAP_USD || "0.05",
          GEMINI_API_KEY: apiKey,
        },
      });
    }
    await container.setInactivityTimeout(INACTIVITY_TIMEOUT_MS);

    const port = container.getTcpPort(CONTAINER_PORT);
    let lastError;
    for (let attempt = 0; attempt < START_ATTEMPTS; attempt += 1) {
      try {
        const response = await port.fetch("http://container/health", {
          signal: AbortSignal.timeout(1000),
        });
        await response.body?.cancel();
        if (!response.ok) {
          throw new Error(`health returned ${response.status}`);
        }
        return;
      } catch (error) {
        lastError = error;
        await scheduler.wait(200);
      }
    }
    throw new Error("container did not become ready on port 8000", {
      cause: lastError,
    });
  }
}

export default {
  async fetch(request, env) {
    return env.BACKEND.getByName("papergen").fetch(request);
  },
};
