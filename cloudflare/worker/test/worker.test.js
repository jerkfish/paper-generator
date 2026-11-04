import { describe, expect, test } from "bun:test";
import {
  contentType,
  disposition,
  normaliseShare,
  pageKey,
  subjectEntries,
} from "../src/index.js";

const GENERATED = [
  { code: "CSC662", route: "csc662", available: true, papers: 20 },
  { code: "MAT133", route: "mat133", available: true, papers: 20 },
];

describe("static routing", () => {
  test("maps public routes to bundle files", () => {
    expect(pageKey("/")).toBe("index.html");
    expect(pageKey("/csc662", GENERATED)).toBe("csc662/index.html");
    expect(pageKey("/csc662/library", GENERATED))
      .toBe("csc662/library/index.html");
    expect(pageKey("/mat133", GENERATED)).toBe("mat133/index.html");
    expect(pageKey("/mat133/library", GENERATED))
      .toBe("mat133/library/index.html");
    expect(pageKey("/mat133/generate/", GENERATED))
      .toBe("mat133/generate/index.html");
    expect(pageKey("/test000", [{ code: "TEST000", route: "test000" }]))
      .toBe("test000/index.html");
    expect(pageKey("/gallery/")).toBe("gallery/index.html");
    expect(pageKey("/assets/style.css")).toBe("assets/style.css");
    expect(pageKey("/library/CSC662/manifest.json"))
      .toBe("library/CSC662/manifest.json");
    expect(pageKey("/library/MAT133/manifest.json"))
      .toBe("library/MAT133/manifest.json");
  });

  test("rejects traversal and unknown paths", () => {
    expect(pageKey("/../.env")).toBeNull();
    expect(pageKey("/%2e%2e/secret")).toBeNull();
    expect(pageKey("/admin")).toBeNull();
    expect(pageKey("/csc662")).toBeNull(); // routes are generated, not fixed
  });
});

test("content disposition has ascii and RFC 5987 forms", () => {
  const value = disposition("CSC662 Seed 07 2026.pdf");
  expect(value).toContain('filename="CSC662 Seed 07 2026.pdf"');
  expect(value).toContain(
    "filename*=UTF-8''CSC662%20Seed%2007%202026.pdf");
});

test("content types cover the bundle", () => {
  expect(contentType("index.html")).toContain("text/html");
  expect(contentType("paper.pdf")).toBe("application/pdf");
  expect(contentType("paper.docx")).toContain("wordprocessingml");
});

describe("share request", () => {
  test("accepts only subject, realistic mode and seed 1-20", () => {
    expect(normaliseShare(
      { subject: "CSC662", mode: "realistic", seed: 7 }, GENERATED))
      .toEqual({ subject: "CSC662", mode: "realistic", seed: 7 });
    expect(normaliseShare(
      { subject: "MAT133", mode: "realistic", seed: 7 }, GENERATED))
      .toEqual({ subject: "MAT133", mode: "realistic", seed: 7 });
    expect(normaliseShare(
      { subject: "TEST000", mode: "realistic", seed: 7 },
      [{ code: "TEST000", route: "test000" }]))
      .toEqual({ subject: "TEST000", mode: "realistic", seed: 7 });
    expect(() => normaliseShare({
      subject: "CSC662", mode: "realistic", seed: 7, text: "hello",
    }, GENERATED)).toThrow("unexpected field");
    expect(() => normaliseShare({
      subject: "CSC662", mode: "practice", seed: 7,
    }, GENERATED)).toThrow("realistic");
    expect(() => normaliseShare({
      subject: "CSC662", mode: "realistic", seed: 0,
    }, GENERATED)).toThrow("1 to 20");
    expect(() => normaliseShare({
      subject: "OTHER", mode: "realistic", seed: 7,
    }, GENERATED)).toThrow("unknown subject");
    expect(() => normaliseShare(null, GENERATED)).toThrow("invalid request");
  });
});

test("subject entries come from the generated list", () => {
  const entries = subjectEntries([
    { code: "TEST000", route: "test000", available: true },
    { code: "HIDDEN", route: "hidden", available: false },
    "PLAIN1",
  ]);
  expect(entries.map((entry) => entry.code)).toEqual(["TEST000", "PLAIN1"]);
  expect(entries[0].route).toBe("test000");
});
