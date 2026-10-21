import { describe, expect, test } from "bun:test";
import {
  contentType,
  disposition,
  normaliseShare,
  pageKey,
} from "../src/index.js";

describe("static routing", () => {
  test("maps public routes to bundle files", () => {
    expect(pageKey("/")).toBe("index.html");
    expect(pageKey("/csc662")).toBe("csc662/index.html");
    expect(pageKey("/csc662/library")).toBe("csc662/library/index.html");
    expect(pageKey("/gallery/")).toBe("gallery/index.html");
    expect(pageKey("/assets/style.css")).toBe("assets/style.css");
    expect(pageKey("/library/CSC662/manifest.json"))
      .toBe("library/CSC662/manifest.json");
  });

  test("rejects traversal and unknown paths", () => {
    expect(pageKey("/../.env")).toBeNull();
    expect(pageKey("/%2e%2e/secret")).toBeNull();
    expect(pageKey("/admin")).toBeNull();
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
    expect(normaliseShare({ subject: "CSC662", mode: "realistic", seed: 7 }))
      .toEqual({ subject: "CSC662", mode: "realistic", seed: 7 });
    expect(() => normaliseShare({
      subject: "CSC662", mode: "realistic", seed: 7, text: "hello",
    })).toThrow("unexpected field");
    expect(() => normaliseShare({
      subject: "CSC662", mode: "practice", seed: 7,
    })).toThrow("realistic");
    expect(() => normaliseShare({
      subject: "CSC662", mode: "realistic", seed: 0,
    })).toThrow("1 to 20");
    expect(() => normaliseShare({
      subject: "OTHER", mode: "realistic", seed: 7,
    })).toThrow("unknown subject");
    expect(() => normaliseShare(null)).toThrow("invalid request");
  });
});
