"""Small BM25 index over lecture-slide chunks."""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from src.theory.decks import DeckChunk

_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9+#.-]*")

TOPIC_DECKS = {
    "attacks/malware": ("011", "022", "041", "042", "051", "052", "061", "062"),
    "authentication/biometrics": ("022", "023", "041", "042", "072"),
    "access control models": ("023", "024", "041", "042", "073"),
    "trusted computing/blockchain": ("038", "073", "074", "074B"),
    "software/OS security": ("041", "042", "051", "052"),
    "network security": ("052", "061", "062"),
    "risk/management (ethics)": ("071",),
    "classical ciphers": ("031",),
}

TOPIC_QUERIES = {
    "attacks/malware": (
        "malware virus worm trojan attack threat denial of service phishing "
        "social engineering injection xss buffer overflow spyware ransomware "
        "exploit vulnerability confidentiality integrity availability"),
    "authentication/biometrics": (
        "authentication identification password biometrics fingerprint iris "
        "smartcard kerberos token single sign-on multi-factor challenge "
        "shared secret zero knowledge"),
    "access control models": (
        "access control ACL capability access control matrix DAC MAC RBAC "
        "Bell-LaPadula Biba Clark-Wilson Chinese wall least privilege "
        "authorization subject object permission"),
    "trusted computing/blockchain": (
        "trusted computing TPM trusted platform module blockchain bitcoin "
        "cryptocurrency distributed ledger trust attestation"),
    "software/OS security": (
        "software security operating system Windows Linux buffer overflow "
        "stack canary ASLR DEP hardening patch privilege malware"),
    "network security": (
        "network security firewall intrusion detection IDS IPS VPN TLS "
        "packet sniffing spoofing denial of service wireless"),
    "risk/management (ethics)": (
        "ethics morals laws ACM code of ethics professional conduct privacy "
        "software piracy acceptable use risk management security policy "
        "awareness training cyber ethics"),
    "classical ciphers": (
        "classical cryptography substitution Caesar Vigenere Playfair "
        "transposition columnar rail fence one time pad cipher plaintext "
        "ciphertext key"),
}


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


@dataclass
class Hit:
    score: float
    chunk: DeckChunk


class BM25Index:
    def __init__(self, chunks: list[DeckChunk], k1: float = 1.5,
                 b: float = 0.75):
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        self.docs = [Counter(tokenize(c.text)) for c in chunks]
        self.lengths = [sum(d.values()) for d in self.docs]
        self.avgdl = (sum(self.lengths) / len(self.lengths)) if chunks else 0.0
        self.df: Counter = Counter()
        for doc in self.docs:
            for term in doc:
                self.df[term] += 1
        self.n = len(chunks)

    def idf(self, term: str) -> float:
        df = self.df.get(term, 0)
        return math.log(1 + (self.n - df + 0.5) / (df + 0.5))

    def search(self, query: str, k: int = 10,
               max_per_deck: int | None = None,
               allowed_prefixes: tuple[str, ...] | None = None) -> list[Hit]:
        q = Counter(tokenize(query))
        if not q:
            return []
        scored: list[Hit] = []
        for i, doc in enumerate(self.docs):
            chunk = self.chunks[i]
            if allowed_prefixes and not chunk.deck.startswith(allowed_prefixes):
                continue
            dl = self.lengths[i] or 1
            score = 0.0
            for term, qn in q.items():
                tf = doc.get(term, 0)
                if not tf:
                    continue
                denom = tf + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
                score += self.idf(term) * (tf * (self.k1 + 1) / denom) * qn
            if score > 0:
                scored.append(Hit(score, chunk))
        scored.sort(key=lambda h: (-h.score, h.chunk.deck, h.chunk.slide))
        if max_per_deck:
            out: list[Hit] = []
            counts: Counter = Counter()
            for h in scored:
                if counts[h.chunk.deck] >= max_per_deck:
                    continue
                out.append(h)
                counts[h.chunk.deck] += 1
                if len(out) >= k:
                    break
            return out
        return scored[:k]


def topic_query(topic: str, extra: str = "") -> str:
    base = TOPIC_QUERIES.get(topic, topic)
    return f"{base} {extra}".strip()
