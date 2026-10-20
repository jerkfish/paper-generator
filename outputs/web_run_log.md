# Web UI - one live run

Job: `cbcbc5ea3af7`
Mode: **practice**; seed **23**; computed marks **22**.
Cost cap: **$0.05**.

## Log

```text
status: done
slots: 17 theory accepted + 5 computed; 2 placeholders
model: deepseek-flash
calls: 51
tokens: 104,405 prompt + 11,406 completion = 115,811
estimated cost: $0.045009
per accepted theory question: $0.00265
placeholders:
  A1b  marking point is a verbatim copy of its quote
  A6a  sub-angle not followed (ACL/ACM/capability)
artifacts:
  paper.docx / paper.pdf   (5 pages)
  scheme.docx / scheme.pdf (13 pages)
```

The run completed under the $0.05 cap. The practice plan had 22 computed marks
(5 computed slots: Caesar, Vigenere, columnar 3x4, ACM, columnar keyword) and
19 theory slots. The page shows the background progress grid, cost so far,
accepted count, placeholders and download links.

Screenshots:

- `app_screenshot.png` - initial Generate tab.
- `app_screenshot_library.png` - Library tab (prebuild in progress).
- `app_screenshot_running.png` - live job in progress.
- `app_screenshot_job.png` - live job complete.
- `app_screenshot_cache.png` - cached seed 12 (no LLM call, run cost $0).
- `app_screenshot_final.png` - final cached seed 12 with the 20-entry library
  available in the other tab.
