# Generated Playfair and columnar answers (convention check)

These are the generated answers used in the mock paper and scheme.
Playfair uses I/J merge and X padding and remains the convention to confirm
(no lecture slide). Columnar uses a 3 rows x 4 columns grid, fill rows
left-to-right, read columns left-to-right, pad X; this is verified against
lecture slides 20-21/24.

## Q2(b) - Playfair encrypt (6 marks)

Question: Encrypt the message below using Playfair encryption with the key REDFOX. Use a 5 x 5 grid, merge I and J, and use X as the filler between repeated letters and at the end if needed.
REVIEW ACCESS PERMISSIONS
(6 marks)

```
Answer: EDEPDVBGAFNCTQDEHKNCPLRTNC

Working:
  Grid (I/J merged):
    R E D F O
    X A B C G
    H I K L M
    N P Q S T
    U V W Y Z
  Padded pairs: RE  VI  EW  AC  CE  SX  SP  ER  MI  SX  SI  ON  SX
  RE -> ED   (same row 1: shift right)
  VI -> EP   (same column 2: shift down)
  EW -> DV   (rectangle (1,2)-(5,3): swap columns)
  AC -> BG   (same row 2: shift right)
  CE -> AF   (rectangle (2,4)-(1,2): swap columns)
  SX -> NC   (rectangle (4,4)-(2,1): swap columns)
  SP -> TQ   (same row 4: shift right)
  ER -> DE   (same row 1: shift right)
  MI -> HK   (same row 3: shift right)
  SX -> NC   (rectangle (4,4)-(2,1): swap columns)
  SI -> PL   (rectangle (4,4)-(3,2): swap columns)
  ON -> RT   (rectangle (1,5)-(4,1): swap columns)
  SX -> NC   (rectangle (4,4)-(2,1): swap columns)
  Ciphertext: EDEPDVBGAFNCTQDEHKNCPLRTNC
```

## Q4(b) - Playfair encrypt (6 marks)

Question: Encrypt the message below using Playfair encryption with the key REDFOX. Use a 5 x 5 grid, merge I and J, and use X as the filler between repeated letters and at the end if needed.
CONTAINER SECURITY CHECKS
(6 marks)

```
Answer: GFPNIPPRFNFARXMPFLIRBLNC

Working:
  Grid (I/J merged):
    R E D F O
    X A B C G
    H I K L M
    N P Q S T
    U V W Y Z
  Padded pairs: CO  NT  AI  NE  RS  EC  UR  IT  YC  HE  CK  SX
  CO -> GF   (rectangle (2,4)-(1,5): swap columns)
  NT -> PN   (same row 4: shift right)
  AI -> IP   (same column 2: shift down)
  NE -> PR   (rectangle (4,1)-(1,2): swap columns)
  RS -> FN   (rectangle (1,1)-(4,4): swap columns)
  EC -> FA   (rectangle (1,2)-(2,4): swap columns)
  UR -> RX   (same column 1: shift down)
  IT -> MP   (rectangle (3,2)-(4,5): swap columns)
  YC -> FL   (same column 4: shift down)
  HE -> IR   (rectangle (3,1)-(1,2): swap columns)
  CK -> BL   (rectangle (2,4)-(3,3): swap columns)
  SX -> NC   (rectangle (4,4)-(2,1): swap columns)
  Ciphertext: GFPNIPPRFNFARXMPFLIRBLNC
```

## Q5(b) - columnar decrypt, 3x4 grid (6 marks)

Question: Decrypt the following ciphertext using columnar transposition with a 3 x 4 matrix (3 rows, 4 columns). Put the ciphertext into the columns, read the plaintext out of the rows, and ignore the filler X at the end. The key is the column size, 4.
LNIOATGUXIDX
(6 marks)

```
Answer: LOGINAUDIT

Working:
  Numeric key: 4 columns; grid 3 rows x 4 columns; read order: col 1, col 2, col 3, col 4
  Grid: 4 columns x 3 rows (12 cells; ciphertext 12 chars; transport pad 0)
  Ciphertext split in read order:
    col 1: LNI
    col 2: OAT
    col 3: GUX
    col 4: IDX
  Reconstructed rows:
    row 1: LOGI
    row 2: NAUD
    row 3: ITXX
  Row-wise: LOGINAUDITXX
  Remove 2 trailing pad 'X': LOGINAUDIT
```
