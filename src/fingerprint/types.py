"""Two-axis question labelling for CSC662: Topic x Task.

Topic = subject area; Task = what the candidate must do. Machine-verifiable is
DEFINED BY CODE: task == "compute" AND concrete inputs AND a code solver for
that topic is feasible. ACM/ACL/capability-list construction and BLP/Biba
rule application count as compute for the access-control topic (owner rule).

All rules are deterministic keyword/structure based - no LLM is used for
labelling. Sub-part rows inherit their topic and (for public-key parameters)
their inputs from siblings in the same question group; both are flagged.
"""
from __future__ import annotations

import re

TOPICS: list[tuple[str, str]] = [
    ("classical ciphers",
     r"caesar|vigenere|vigene|rail fence|transposition|one.?time pad|\botp\b|"
     r"columnar|substitution cipher|shift cipher|playfair|monoalphabetic|"
     r"hill cipher|affine cipher|vernam|poly.?alphabetic|scytale"),
    ("block ciphers",
     r"\bdes\b|\baes\b|block cipher|permuted key|subkey|round key|byte substitution|"
     r"shift rows?|mix columns?|s[- ]?box|feistel|3des|triple des|initial state|"
     r"subbytes|mixcolumns|shiftrows|rijndael|\bidea\b|pc.?1|pc.?2"),
    ("public-key",
     r"\brsa\b|diffie|key exchange|public key|private key|digital signature|"
     r"certificate authority|\bca\b|\bpki\b"),
    ("hashing/signatures",
     r"hash|md5|sha-?1|message digest|checksum|signature scheme"),
    ("general cryptography",
     r"symmetric|asymmetr|cryptosystem|cryptograph|encryption algorithm"),
    ("access control models",
     r"access control matrix|access matrix|\bacl\b|capabilit|bell[- ]?lapadula|"
     r"chinese wall|biba|blp\b|access control|authoriz|least privilege|"
     r"\bprivilege\b|formal security model"),
    ("authentication/biometrics",
     r"biometric|authenticat|two.?factor|multi.?factor|password|pass.?phrase"),
    ("software/OS security",
     r"windows|unix|linux|operating system|\bos\b|security identifier|\bsid\b|"
     r"user account|permission"),
    ("attacks/malware",
     r"virus|worm|trojan|malware|malicious code|attack|intrusion|denial of service|"
     r"\bdos\b|\bddos\b|threat|vulnerabilit|exploit|salami|ping of death|\bxss\b|"
     r"sql injection|buffer overflow|spoof|phishing|botnet|payload|ransomware|"
     r"keylogger|backdoor|sniffing|zero.?day|reconnaissan"),
    ("network security",
     r"network|firewall|router|ipsec|\bvpn\b|\btls\b|\bssl\b|protocol|packet|"
     r"ip address|internet|telnet|\bssh\b|\bweb\b|\bhttp\b|cookie|session|topology|"
     r"\bids\b|idps|intrusion detection"),
    ("risk/management",
     r"risk|policy|management|security objective|security goal|ethic|"
     r"moral|privacy|audit|recovery|contingency|business continuity|asset|"
     r"valuation|copyright|patent|\blaw\b|legal|drm|digital rights|standard|"
     r"guideline|piracy"),
    ("trusted computing/blockchain",
     r"trusted computing|\btpm\b|ngscb|trusted platform|blockchain|cryptocurrency|"
     r"bitcoin|double spending|smart contract"),
]
TOPIC_NAMES = [name for name, _ in TOPICS] + ["other"]

COMPUTE_CUES = re.compile(
    r"encrypt|decrypt|encipher|decipher|comput|calculat|\bfind\b|generate|derive|"
    r"\bsolve\b|convert|evaluate|produce|obtain|show (your )?work", re.I)
# with concrete inputs present, these words also imply the candidate must compute
COMPUTE_CONTEXT = re.compile(r"given|provided|\busing\b|\bapply\b|perform|\bfind\b",
                             re.I)
# owner rule: draw only if the row's OWN text says so
DRAW_CUES = re.compile(r"\bdraw(?:s|n|ing)?\b|\bsketch\b|"
                       r"with (?:the )?aid of (?:a |an )?diagram|with a diagram", re.I)
# owner rule: compare only if the row's own text has these words
COMPARE_CUES = re.compile(r"differentiat|\bdifference\b|differ|compar|versus|\bvs\b", re.I)
# owner rule: list needs a count word or "list"/"enumerate"
LIST_CUES = re.compile(
    r"\b(list|enumerate)\b|"
    r"\b(state|give|identify|name)\s+(one|two|three|four|five|six|seven|eight|"
    r"nine|ten|eleven|twelve|\d+|several|various|any)\b", re.I)
SCENARIO_CUES = re.compile(
    r"\bscenario\b|\bjustify\b|\bsuggest\b|\brecommend\b|support your answer|"
    r"in your opinion|\badvise\b|would you|\bsituation\b|"
    r"based on the (above|following|given)", re.I)
DEFINE_CUES = re.compile(r"define|what is|meaning of|describe|explain|discuss", re.I)
PART_A_PAT = re.compile(r"^A\d+$")


def _norm(s: str) -> str:
    return re.sub(r"\s+", "", str(s))

TASK_NAMES = ["compute", "draw/diagram", "compare", "list/enumerate",
              "scenario/justify", "short objective", "define/explain"]

# topics where a deterministic solver is feasible
SOLVER_TOPICS = {"classical ciphers", "block ciphers", "public-key",
                 "hashing/signatures", "access control models"}

# owner rule: ACM/ACL/capability-list construction and BLP/Biba rule application
# are compute + machine-verifiable for access control
AC_CONSTRUCT_PAT = re.compile(
    r"access control matrix|access matrix|\bacm\b|\bacl\b|capabilit(?:y|ies)\s+list", re.I)
AC_RULE_PAT = re.compile(r"bell[- ]?lapadula|\bbiba\b|\bblp\b|simple security|"
                         r"star property", re.I)
AC_RULE_APPLY_PAT = re.compile(r"\b(read|write|execute|access)\b", re.I)


def classify_topic(text: str) -> str:
    low = str(text).lower()
    for name, pattern in TOPICS:
        if pattern and re.search(pattern, low):
            return name
    return "other"


def has_concrete_inputs(text: str) -> bool:
    """Concrete inputs the candidate must operate on: RSA params, keys,
    ciphertext/plaintext, hex blocks, DES tables, number streams, shifts."""
    low = str(text).lower()
    if re.search(r"\b[pqned]\s*=\s*\d+", low):        # RSA params (p=7, q=11, e=9)
        return True
    if re.search(r"\bkey[\w\s]{0,20}?[:=]\s*\S", low):  # "Key =", "key sequence:"
        return True
    if re.search(r"\bkeys?\s+(?:as|is|are)\s*[:=]", low):
        return True
    if re.search(r"\bkeyword\b", low):
        return True
    if re.search(r"\bshift\s+of\s+\d+|\bshift\s*\d+|\bkey\s+of\s+\d+", low):
        return True
    if re.search(r"following.{0,40}(plaintext|plain[- ]?text|ciphertext|"
                 r"cipher[- ]?text|message)", low):
        return True
    if re.search(r"\bplaintext\b.{0,120}\bkey\b", low):
        return True
    if re.search(r"pc.?1|pc.?2|s-?box|table\s+pc", low):  # DES key-schedule tables
        return True
    if re.search(r"\b[0-9A-F]{2}(?:\s+[0-9A-F]{2}){3,}\b", text):  # hex pairs
        return True
    if re.search(r"\b[0-9A-F]{8,}\b", text):                 # hex word
        return True
    if re.search(r"\d{2}(?:,\s*\d{2}){2,}", low):            # number stream (OTP)
        return True
    return False


def is_ac_construction(text: str, topic: str) -> bool:
    """ACM/ACL/capability-list construction or BLP/Biba rule application."""
    if topic != "access control models":
        return False
    low = str(text).lower()
    if AC_CONSTRUCT_PAT.search(low):
        return True
    return bool(AC_RULE_PAT.search(low) and AC_RULE_APPLY_PAT.search(low))


def classify_task(text: str, q_no: str = "", llm_type: str = "",
                  has_inputs: bool | None = None) -> str:
    if has_inputs is None:
        has_inputs = has_concrete_inputs(text)
    low = str(text).lower()
    if has_inputs and (COMPUTE_CUES.search(low) or COMPUTE_CONTEXT.search(low)):
        return "compute"
    if DRAW_CUES.search(low):
        return "draw/diagram"
    if COMPARE_CUES.search(low):
        return "compare"
    if LIST_CUES.search(low):
        return "list/enumerate"
    if SCENARIO_CUES.search(low):
        return "scenario/justify"
    if PART_A_PAT.match(str(q_no)) or llm_type == "Objective (MCQ)":
        return "short objective"
    if DEFINE_CUES.search(low):
        return "define/explain"
    return "define/explain"


def machine_verifiable(topic: str, task: str, has_inputs: bool) -> bool:
    return task == "compute" and has_inputs and topic in SOLVER_TOPICS


def classify_row(original_text: str, q_no: str = "", llm_type: str = "") -> dict:
    text = str(original_text)
    topic = classify_topic(text)
    inputs = has_concrete_inputs(text)
    task = classify_task(text, q_no, llm_type, has_inputs=inputs)
    # owner rule: model construction / rule application is compute + verifiable
    if is_ac_construction(text, topic) and task in ("draw/diagram", "define/explain",
                                                    "scenario/justify", "short objective"):
        task = "compute"
        inputs = True
    return {"topic": topic, "task": task, "has_inputs": inputs,
            "machine_verifiable": machine_verifiable(topic, task, inputs)}


def is_whole_block_row(row: dict) -> bool:
    return "whole block" in str(row.get("Wording note", "")) or \
        "verbatim check failed" in str(row.get("Wording note", ""))


def label_group(rows: list[dict]) -> list[dict]:
    """Label all rows of one question group, with sibling inheritance:
    - topic: sub-parts with topic 'other' inherit the group's dominant topic
    - inputs: public-key parameters propagate to compute-cue sub-parts
    Both are flagged in row['label_flags']."""
    texts = [str(r["Original question text"]) for r in rows]
    group_has_inputs = any(has_concrete_inputs(t) for t in texts)

    dominant: str | None = None
    for name, _ in TOPICS:  # first topic in priority order that appears
        if any(classify_topic(t) == name and not is_whole_block_row(r)
               for t, r in zip(texts, rows)):
            dominant = name
            break

    out = []
    for r, t in zip(rows, texts):
        lab = classify_row(t, r["Q no."], str(r.get("Question type", "")))
        flags: list[str] = []

        if (not lab["has_inputs"] and group_has_inputs
                and COMPUTE_CUES.search(t.lower())
                and lab["task"] in ("define/explain", "short objective",
                                    "scenario/justify")):
            lab["has_inputs"] = True
            lab["task"] = "compute"
            lab["machine_verifiable"] = machine_verifiable(lab["topic"], "compute", True)
            flags.append("inputs inherited from sibling")

        if lab["topic"] == "other" and dominant and not is_whole_block_row(r):
            lab["topic"] = dominant
            flags.append("topic inherited from sibling")

        # tiny fragments ("ii) ANAKTIKUSRED") belong to the group's computation
        if (len(_norm(t)) < 30 and lab["task"] != "compute"
                and any(has_concrete_inputs(tt) and COMPUTE_CUES.search(tt.lower())
                        for tt in texts)):
            lab["task"] = "compute"
            lab["has_inputs"] = True
            lab["machine_verifiable"] = machine_verifiable(lab["topic"], "compute", True)
            flags.append("compute task inherited from sibling")

        lab["flags"] = flags
        out.append(lab)
    return out
