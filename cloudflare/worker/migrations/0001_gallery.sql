-- Public gallery index. Times are ISO-8601 UTC strings.
CREATE TABLE IF NOT EXISTS gallery (
  id               TEXT PRIMARY KEY,
  subject          TEXT NOT NULL,
  seed             INTEGER NOT NULL,
  mode             TEXT NOT NULL,
  computed_marks   INTEGER,
  created_at       TEXT NOT NULL,
  expires_at       TEXT NOT NULL,
  paper_pdf_key    TEXT NOT NULL,
  paper_docx_key   TEXT NOT NULL,
  scheme_pdf_key   TEXT NOT NULL,
  scheme_docx_key  TEXT NOT NULL,
  paper_pdf_name   TEXT NOT NULL,
  paper_docx_name  TEXT NOT NULL,
  scheme_pdf_name  TEXT NOT NULL,
  scheme_docx_name TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_gallery_expires
  ON gallery (expires_at);

CREATE INDEX IF NOT EXISTS idx_gallery_reuse
  ON gallery (subject, mode, seed, expires_at);
