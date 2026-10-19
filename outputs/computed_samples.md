# Computed sample questions - classical ciphers

Drafted by the LLM (cipher/key/task/marks only, model qwen3.7-flash); plaintexts picked from the offline phrase bank (data/phrases.json, seeded). Ciphertext, answers and working are all computed by code.

Conventions:

- Playfair I/J merge + X padding: **convention unverified** (pending lecture-slide confirmation).

- Columnar explicit-rows grid (3 x 4 style): **convention unverified**.

- Encrypt-only answers: **convention unverified** (no official keys exist).

- Decrypt answers: readable plaintext; solvers validated on real past papers (7 cases, see src/generators/validate_solvers.py).

## Question 1 (2 marks)

```
Using Caesar Cipher technique, decrypt the following ciphertext.
KLCPJLYLABYULKHUKDPWLKVUL
(2 marks)
```
```
Answer: DEVICERETURNEDANDWIPEDONE

Working:
  K (10) -7 mod 26 -> D
  L (11) -7 mod 26 -> E
  C ( 2) -7 mod 26 -> V
  P (15) -7 mod 26 -> I
  J ( 9) -7 mod 26 -> C
  L (11) -7 mod 26 -> E
  Y (24) -7 mod 26 -> R
  L (11) -7 mod 26 -> E
  A ( 0) -7 mod 26 -> T
  B ( 1) -7 mod 26 -> U
  Y (24) -7 mod 26 -> R
  U (20) -7 mod 26 -> N
  L (11) -7 mod 26 -> E
  K (10) -7 mod 26 -> D
  H ( 7) -7 mod 26 -> A
  U (20) -7 mod 26 -> N
  K (10) -7 mod 26 -> D
  D ( 3) -7 mod 26 -> W
  P (15) -7 mod 26 -> I
  W (22) -7 mod 26 -> P
  L (11) -7 mod 26 -> E
  K (10) -7 mod 26 -> D
  V (21) -7 mod 26 -> O
  U (20) -7 mod 26 -> N
  L (11) -7 mod 26 -> E
```

## Question 2 (2 marks)

```
Using Caesar Cipher technique, decrypt the following ciphertext.
AYHPULTWSVFLLZVUZLJBYPAF
(2 marks)
```
```
Answer: TRAINEMPLOYEESONSECURITY

Working:
  A ( 0) -7 mod 26 -> T
  Y (24) -7 mod 26 -> R
  H ( 7) -7 mod 26 -> A
  P (15) -7 mod 26 -> I
  U (20) -7 mod 26 -> N
  L (11) -7 mod 26 -> E
  T (19) -7 mod 26 -> M
  W (22) -7 mod 26 -> P
  S (18) -7 mod 26 -> L
  V (21) -7 mod 26 -> O
  F ( 5) -7 mod 26 -> Y
  L (11) -7 mod 26 -> E
  L (11) -7 mod 26 -> E
  Z (25) -7 mod 26 -> S
  V (21) -7 mod 26 -> O
  U (20) -7 mod 26 -> N
  Z (25) -7 mod 26 -> S
  L (11) -7 mod 26 -> E
  J ( 9) -7 mod 26 -> C
  B ( 1) -7 mod 26 -> U
  Y (24) -7 mod 26 -> R
  P (15) -7 mod 26 -> I
  A ( 0) -7 mod 26 -> T
  F ( 5) -7 mod 26 -> Y
```

## Question 3 (6 marks)

```
Decrypt the following ciphertext using the Vigenere cipher with the key secret.
ULGTOYGVXRPBVHQDEBFRCDIL
(6 marks)
```
```
Answer: CHECKFORVALIDDOMAINNAMES

Working:
  U(20) -18 mod 26 -> C
  L(11) - 4 mod 26 -> H
  G( 6) - 2 mod 26 -> E
  T(19) -17 mod 26 -> C
  O(14) - 4 mod 26 -> K
  Y(24) -19 mod 26 -> F
  G( 6) -18 mod 26 -> O
  V(21) - 4 mod 26 -> R
  X(23) - 2 mod 26 -> V
  R(17) -17 mod 26 -> A
  P(15) - 4 mod 26 -> L
  B( 1) -19 mod 26 -> I
  V(21) -18 mod 26 -> D
  H( 7) - 4 mod 26 -> D
  Q(16) - 2 mod 26 -> O
  D( 3) -17 mod 26 -> M
  E( 4) - 4 mod 26 -> A
  B( 1) -19 mod 26 -> I
  F( 5) -18 mod 26 -> N
  R(17) - 4 mod 26 -> N
  C( 2) - 2 mod 26 -> A
  D( 3) -17 mod 26 -> M
  I( 8) - 4 mod 26 -> E
  L(11) -19 mod 26 -> S
```

## Question 4 (6 marks)

```
Decrypt the following ciphertext using the Vigenere cipher with the key secret.
AHGEXBXCCESFSPQLWUWLCMMHJ
(6 marks)
```
```
Answer: IDENTIFYANOMALOUSBEHAVIOR

Working:
  A( 0) -18 mod 26 -> I
  H( 7) - 4 mod 26 -> D
  G( 6) - 2 mod 26 -> E
  E( 4) -17 mod 26 -> N
  X(23) - 4 mod 26 -> T
  B( 1) -19 mod 26 -> I
  X(23) -18 mod 26 -> F
  C( 2) - 4 mod 26 -> Y
  C( 2) - 2 mod 26 -> A
  E( 4) -17 mod 26 -> N
  S(18) - 4 mod 26 -> O
  F( 5) -19 mod 26 -> M
  S(18) -18 mod 26 -> A
  P(15) - 4 mod 26 -> L
  Q(16) - 2 mod 26 -> O
  L(11) -17 mod 26 -> U
  W(22) - 4 mod 26 -> S
  U(20) -19 mod 26 -> B
  W(22) -18 mod 26 -> E
  L(11) - 4 mod 26 -> H
  C( 2) - 2 mod 26 -> A
  M(12) -17 mod 26 -> V
  M(12) - 4 mod 26 -> I
  H( 7) -19 mod 26 -> O
  J( 9) -18 mod 26 -> R
```

## Question 5 (6 marks)

```
Encrypt the message below using Playfair encryption with the key REDFOX.
REVIEW ACCESS PERMISSIONS
(6 marks)
```
```
Answer: EDEPDVBGAFNCTQDEHKNCPLRTNC

Working:
  Grid (I/J merged):
  R E D F O X A B C G H I K L M N P Q S T U V W Y Z
  encrypt result: EDEPDVBGAFNCTQDEHKNCPLRTNC
```
> Convention note: encrypt-only - convention unverified; Playfair I/J merge + X padding: convention unverified.

## Question 6 (6 marks)

```
Encrypt the message below using Playfair encryption with the key REDFOX.
CONTAINER SECURITY CHECKS
(6 marks)
```
```
Answer: GFPNIPPRFNFARXMPFLIRBLNC

Working:
  Grid (I/J merged):
  R E D F O X A B C G H I K L M N P Q S T U V W Y Z
  encrypt result: GFPNIPPRFNFARXMPFLIRBLNC
```
> Convention note: encrypt-only - convention unverified; Playfair I/J merge + X padding: convention unverified.

## Question 7 (6 marks)

```
Decrypt the following ciphertext using the affine cipher with key (17,20).
ZAQAFZYSAHUFFKQPFOPKXJYWX
(6 marks)
```
```
Answer: LIMITLOGINATTEMPTSPERHOUR

Working:
  23*(25 - 20) mod 26 = 11 -> L
  23*(0 - 20) mod 26 = 8 -> I
  23*(16 - 20) mod 26 = 12 -> M
  23*(0 - 20) mod 26 = 8 -> I
  23*(5 - 20) mod 26 = 19 -> T
  23*(25 - 20) mod 26 = 11 -> L
  23*(24 - 20) mod 26 = 14 -> O
  23*(18 - 20) mod 26 = 6 -> G
  23*(0 - 20) mod 26 = 8 -> I
  23*(7 - 20) mod 26 = 13 -> N
  23*(20 - 20) mod 26 = 0 -> A
  23*(5 - 20) mod 26 = 19 -> T
  23*(5 - 20) mod 26 = 19 -> T
  23*(10 - 20) mod 26 = 4 -> E
  23*(16 - 20) mod 26 = 12 -> M
  23*(15 - 20) mod 26 = 15 -> P
  23*(5 - 20) mod 26 = 19 -> T
  23*(14 - 20) mod 26 = 18 -> S
  23*(15 - 20) mod 26 = 15 -> P
  23*(10 - 20) mod 26 = 4 -> E
  23*(23 - 20) mod 26 = 17 -> R
  23*(9 - 20) mod 26 = 7 -> H
  23*(24 - 20) mod 26 = 14 -> O
  23*(22 - 20) mod 26 = 20 -> U
  23*(23 - 20) mod 26 = 17 -> R
```

## Question 8 (6 marks)

```
Decrypt the following ciphertext using one-time pad with the key numbers 3 6 12 9 4 15 20 1.
SANUMREFBOZOVPMUUAOCYGY
(6 marks)
```
```
Answer: PUBLICKEYINFRASTRUCTURE

Working:
  S(18) - 3 mod 26 -> P
  A( 0) - 6 mod 26 -> U
  N(13) -12 mod 26 -> B
  U(20) - 9 mod 26 -> L
  M(12) - 4 mod 26 -> I
  R(17) -15 mod 26 -> C
  E( 4) -20 mod 26 -> K
  F( 5) - 1 mod 26 -> E
  B( 1) - 3 mod 26 -> Y
  O(14) - 6 mod 26 -> I
  Z(25) -12 mod 26 -> N
  O(14) - 9 mod 26 -> F
  V(21) - 4 mod 26 -> R
  P(15) -15 mod 26 -> A
  M(12) -20 mod 26 -> S
  U(20) - 1 mod 26 -> T
  U(20) - 3 mod 26 -> R
  A( 0) - 6 mod 26 -> U
  O(14) -12 mod 26 -> C
  C( 2) - 9 mod 26 -> T
  Y(24) - 4 mod 26 -> U
  G( 6) -15 mod 26 -> R
  Y(24) -20 mod 26 -> E
```

## Question 9 (6 marks)

```
Decrypt the following ciphertext using columnar transposition with the key secret.
FOIENCXLRPYXOMTSEEEUCLRX
(6 marks)
```
```
Answer: ENFORCECOMPLEXITYRULES

Working:
  Key: SECRET; convention: fill rows, read columns (keyword: alphabetical rank order; pad X)
  decrypt result: ENFORCECOMPLEXITYRULES
```

## Question 10 (6 marks)

```
Decrypt the following ciphertext using columnar transposition with the key ZEBRA.
LTUXNDNEIUOTAIDDFACC
(6 marks)
```
```
Answer: FINALAUDITCONDUCTED

Working:
  Key: ZEBRA; convention: fill rows, read columns (keyword: alphabetical rank order; pad X)
  decrypt result: FINALAUDITCONDUCTED
```
