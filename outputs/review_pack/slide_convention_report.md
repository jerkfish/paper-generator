# CSC662 lecture-slide convention check

Date: 2026-10-19. Source: knowledge base `CSC662`
(`c2713c33-83d4-4658-b2d0-641ca074bab7`), deck
`031 - Classical Cryptography.pptx` (31 slides), plus the other decks in the
same KB folder for coverage. The decks were treated as read-only local study
material.

Extraction method: python-pptx text extraction, PowerPoint COM export of the
slides at 1920 x 1080, and WinRT OCR on the exported images. The OTP table on
slide 17 is an image; its values were read from the image (OCR plus visual
check). The columnar/rail-fence diagrams are images; their values are also
stated in the slide text, and the images were OCRed to confirm the layout.
The Vigenere tableau on slides 14-15 is an image; OCR confirms a standard
26 x 26 tableau.

## 1. Which deck/slide covers each cipher

| Cipher | Deck and slides | Worked example? |
|---|---|---|
| Caesar shift | `031 - Classical Cryptography.pptx`, slides 5-9 | Yes: slides 5, 6, 9 |
| Vigenere | same deck, slides 14-15 | Yes: slide 15 |
| Playfair | **not covered in any deck** | No |
| Columnar, numeric 3 x 4 | same deck, slides 19-21 | Yes: slides 20-21 |
| Columnar, keyword / "double transposition" | same deck, slide 24 | Yes: slide 24 |
| Rail fence | same deck, slides 25-26 | Yes: slides 25-26 |
| Affine | **not covered in any deck** | No |
| One-time pad / Vernam | same deck, slides 16-17 | Yes: slide 17 (image table) |
| Single transposition | **not covered in any deck** (paper-only convention) | No |
| Homophonic substitution | same deck, slides 12-13 (not in solver scope) | Yes: slides 12-13 |

Deck `035 - General Model of Cryptography.pptx` mentions the one-time pad
(slide 13) and transposition/confusion-diffusion (slide 14), but gives no
worked example. No deck text mentions Playfair or affine, and no worked
example for either was found in the KB decks. The folder also contains
`Chapter 1 - Fundamentals of Computer Security.pdf`, but it is a textbook
chapter, not a lecture deck; it is not part of the KB and was not used as a
slide source.

## 2. Worked examples in the slides

| Slide | Cipher | Key | Plaintext | Ciphertext as printed | Method notes / source |
|---|---|---|---|---|---|
| 5 | Caesar shift | shift 3 (right for encryption) | `ATTACK` | `DWWDFN` | Diagram: plaintext ATTACK -> encryption -> ciphertext DWWDFN, decryption back. Text boxes; diagram is images. |
| 6 | Caesar shift | shift 3 | `ATTACK` | `DWWDFN` | "Replace each letter with the one three positions to the right" (encryption); left for decryption. Example is text: A T T A C K -> D W W D F N. |
| 9 | Caesar decryption / brute force | shifts 1, 2, 3 | `DWWDFN` (ciphertext) -> `ATTACK` at shift 3 | `CVVCEM` (shift 1), `BUUBDL` (shift 2), `ATTACK` (shift 3) | The slide lists the three shift attempts; the shift table image is OCRed. Key space <= 26. |
| 15 | Vigenere | `UNITUEUN` | `ATTACK` | `UGBTWO` | Write the key over the message, repeating as necessary; substitute using the appropriate column of the Vigenere tableau; decryption uses a row instead of a column. Standard 26 x 26 tableau image. |
| 17 | One-time pad / Vernam | numeric `18 6 3 9 18 6`; key row is labelled `T H E K T H` | `ATTACK` (numeric row `0 18 18 0 2 9`) | `S Y V J U Q` (numeric row `18 24 21 9 20 15`) | Encryption = addition modulo 26; decryption = subtraction. **Image table**, read by OCR/visual check. The table is internally inconsistent; see section 3. |
| 20 | Columnar (numeric) | column size 4 | `ATTACK` | `ACXTKXTXXAXX` | Matrix is 3 x 4; put plaintext into rows, read ciphertext out of columns; filler X. Text plus matrix image. |
| 21 | Columnar decryption | column size 4 | ciphertext `ACXTKXTXXAXX` -> `ATTACK` | `ACXTKXTXXAXX` | Divide by 4 -> group size 3; groups `{ACX}`, `{TKX}`, `{TXX}`, `{CXX}`; put into columns, reconstruct matrix, read rows, ignore trailing X. Text plus matrix image. |
| 24 | Keyword columnar / "double transposition" | keyword `MATH`, key-space 4 | `ATTACK` | `TKXAXXACXTXX` | Normal columnar 3 x 4 matrix, then sort the keyword to `AHMT` and read the columns in that order. Text plus matrix image. |
| 25 | Rail fence encryption | 3 rails | `ATTACK` | `ACTAKT` | Write plaintext in a 3-row zigzag; concatenate non-empty rows. Text plus diagram. |
| 26 | Rail fence decryption | 3 rails | ciphertext `ACTAKT` -> `ATTACK` | `ACTAKT` | Recreate the empty rail table, write ciphertext in rows, read in zigzag. Text plus diagram. |

Additional (not in solver scope): slides 12-13 give a keyed 2-digit
homophonic substitution example, key `THEK`, plaintext `ATTACK`, ciphertext
`06 00 37 43 08 16` (slide 12) and `06 00 37 43 45 16` (slide 13, reverse
frequency table). Slides 7, 8, 14, 16, 19, 22 and 23 are method/theory only
(no worked example).

## 3. Solver results

"Match" means the solver reproduces the printed ciphertext (or printed
plaintext for a decryption example) exactly.

| Slide/example | Result | Solver output vs slide |
|---|---|---|
| 5/6 Caesar encrypt `ATTACK`, shift 3 | **MATCH** | `caesar_encrypt("ATTACK", 3)` -> `DWWDFN` |
| 9 Caesar decrypt `DWWDFN`, shifts 1/2/3 | **MATCH** | `caesar_decrypt("DWWDFN", k)` -> `CVVCEM` / `BUUBDL` / `ATTACK` |
| 15 Vigenere `ATTACK`, key `UNITUEUN` | **MATCH** | `vigenere_encrypt("ATTACK", "UNITUEUN")` -> `UGBTWO`; decrypt -> `ATTACK` |
| 20/21 Columnar `ATTACK`, key 4, 3 x 4 | **MATCH** | `columnar_encrypt("ATTACK", 4, rows=3)` -> `ACXTKXTXXAXX`; decrypt -> `ATTACK` |
| 24 Keyword columnar `ATTACK`, key `MATH`, 3 x 4 | **MATCH after fix** | Before: `columnar_encrypt("ATTACK", "MATH", rows=3)` ignored `rows` for a keyword key and produced `TKAXACTX` (8 letters). After adding explicit-rows support: `TKXAXXACXTXX` (12 letters), exactly the slide; decrypt -> `ATTACK`. |
| 25/26 Rail fence `ATTACK`, 3 rails | **MATCH** | `railfence_encrypt("ATTACK", 3)` -> `ACTAKT`; decrypt -> `ATTACK` |
| 17 OTP `ATTACK`, key `18 6 3 9 18 6` | **MISMATCH / internally inconsistent** | 26-letter solver: `SZWJUQ`; 25-letter I/J-merged option: `TZWKVQ`; slide prints `SYVJUQ`. No single convention reproduces the row. |
| Playfair | **NO EXAMPLE** | No lecture slide; solver's I/J merge + X padding remains unverified. |
| Affine | **NO EXAMPLE** | No lecture slide; solver's `E(x)=(a x+b) mod 26` remains unverified. |
| Single transposition | **NO EXAMPLE** | Paper-only convention (validated against APR 2010 Q13); no slide. |

### Why the OTP slide does not verify

The slide 17 table mixes conventions:

- Plaintext indices use a 25-letter I/J-merged alphabet: T = 18, K = 9,
  A = 0, C = 2. In the ordinary 26-letter alphabet T would be 19 and K 10.
- The key row is labelled `T H E K T H`, but its numbers are
  `18 6 3 9 18 6`; in the I/J-merged alphabet H/E are 7/4, not 6/3.
- The ciphertext letters `S Y V J U Q` are the ordinary 26-letter letters
  for the sums 18, 24, 21, 9, 20, 15; the last sum 15 is P, not Q, so the
  printed last letter is also inconsistent.

We therefore list both readings and keep OTP **unverified**. The solver
default remains the ordinary 26-letter alphabet (the real DEC 2019 paper's
convention); `ij_merge=True` exposes the 25-letter reading for comparison.
No silent choice was made.

## 4. Convention variants found

1. **Columnar, numeric 3 x 4** (slides 20-21): 3 rows, 4 columns, fill rows,
   read columns, pad X, ignore trailing X. Solver: `key=4, rows=3`.
2. **Columnar, keyword / "double transposition"** (slide 24): same 3 x 4
   fill/read rule, but columns are read in the alphabetical rank order of the
   keyword (`MATH` -> `AHMT`). Solver: `key="MATH", rows=3` after the fix.
3. **OTP/Vernam**: slide 17 mixes a 25-letter plaintext alphabet with
   26-letter ciphertext letters; the real DEC 2019 paper uses the ordinary
   26-letter alphabet. Both are listed; the slide does not verify a single
   convention.
4. **Playfair / affine**: no slide examples; the solver conventions remain
   unverified.
5. **Single transposition**: paper convention (APR 2010 Q13), not a slide
   convention.

## 5. Project changes

- `src/generators/ciphers.py`:
  - `columnar_encrypt` / `columnar_decrypt` now honor an explicit `rows` value
    for **keyword** keys as well as numeric keys. Default behavior (rows
    derived from the message length) is unchanged when `rows` is omitted.
  - `vernam_encrypt` / `vernam_decrypt` gained an `ij_merge` option. The
    default stays the ordinary 26-letter alphabet; `ij_merge=True` is the
    25-letter slide reading. The docstring/convention text records the slide
    inconsistency.
  - `SOLVER_CONVENTIONS` now states the slide evidence and the remaining
    unverified items.
- `tests/test_ciphers.py`: lecture-slide regression tests for Caesar (slides
  5/6/9), Vigenere (slide 15), columnar numeric 3 x 4 (slides 20/21), keyword
  columnar 3 x 4 (slide 24), rail fence (slides 25/26), and a documentation
  test for the inconsistent OTP table (both solver readings).
- `tests/test_question_wording.py`: the paper stem must state the key/table,
  grid, filler and fill/read order.
- `src/assemble/build_docx_paper.py`: new `paper_question()` used by the paper
  and scheme. Stems now say:
  - Q2(a)/Q4(a): shift 7, "replace each letter with the one 7 positions to the
    left";
  - Q2(b)/Q4(b): key REDFOX, 5 x 5 grid, I/J merge, X filler between repeated
    letters and at the end;
  - Q5(b): 3 x 4 matrix (3 rows, 4 columns), put ciphertext into columns, read
    plaintext out of rows, ignore filler X, key = column size 4.
- `src/assemble/scheme_working.py`: confidence labels updated:
  - Caesar: computed - matches lecture slides 5-9.
  - Columnar: computed - 3 x 4 fill-rows/read-columns verified against slides
    20-21 and 24.
  - Playfair: convention unverified - no lecture slide.
  - Affine: convention unverified - no lecture slide (if used).
  - OTP: convention unverified - slide 17 mixes alphabets.
  - Vigenere/rail fence: computed - slide match.

## 6. Regenerated mock paper and scheme

`mock_paper_01.docx/.pdf` and `mock_scheme_01.docx/.pdf` were rebuilt after the
wording and solver changes. All six computed answers are **unchanged**:

| Slot | Answer before | Answer after |
|---|---|---|
| Q2(a) | `DEVICERETURNEDANDWIPEDONE` | `DEVICERETURNEDANDWIPEDONE` |
| Q2(b) | `EDEPDVBGAFNCTQDEHKNCPLRTNC` | `EDEPDVBGAFNCTQDEHKNCPLRTNC` |
| Q3(b) | matrix/ACL/CL as before | matrix/ACL/CL as before |
| Q4(a) | `TRAINEMPLOYEESONSECURITY` | `TRAINEMPLOYEESONSECURITY` |
| Q4(b) | `GFPNIPPRFNFARXMPFLIRBLNC` | `GFPNIPPRFNFARXMPFLIRBLNC` |
| Q5(b) | `LOGINAUDIT` | `LOGINAUDIT` |

The paper grew from 4 to 5 pages because the stems now state the conventions;
the printed-pages line and scheme page-count line were recomputed
(paper 5, scheme 5). The scheme's confidence labels changed for Caesar and
columnar; no answer text changed. The review-pack checklist and Step 8 layout
numbers were refreshed for the 5-page paper.

## 7. Remaining unverified conventions

- **Playfair**: no lecture slide; I/J merge + X padding still to be confirmed.
- **Affine**: no lecture slide; `E(x)=(a x+b) mod 26` still to be confirmed.
- **OTP/Vernam**: slide 17 is internally inconsistent; keep unverified and
  confirm with the lecturer whether the course uses the 25-letter I/J-merged
  alphabet or the 26-letter alphabet.
- **Single transposition**: paper-only validation (APR 2010 Q13); no slide.
- Columnar pad alternatives (`z`) and explicit row counts in past papers are
  paper-validated; the slide's 3 x 4 fill/read order is verified.
