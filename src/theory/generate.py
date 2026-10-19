"""Generate theory questions from lecture decks with BM25 + verifier.

Run:
  uv run python -m src.theory.generate --plan outputs/planner_revised_realistic.json
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path

from pydantic import ValidationError

from src import config
from src.llm import Usage, chat_json_result
from src.planner.fingerprint_data import load_modern_stats
from src.theory.bm25 import BM25Index, TOPIC_DECKS, topic_query
from src.theory.decks import DeckChunk, coverage, load_chunks
from src.theory.models import Placeholder, TheoryDraft, VerifiedQuestion
from src.theory.verify import near_copy, verify_draft

MAX_ATTEMPTS = 4  # initial + up to 3 retries

ANGLE_REQUIRED = {
    "A8": ["malware", "trojan", "worm", "virus", "ransomware", "spyware"],
    "A9": ["password", "kerberos", "smartcard", "smart card"],
}
ANGLE_FORBIDDEN = {
    "A8": ["class of threat", "classes of threats", "threat class",
           "password"],
    "A9": ["biometric", "single sign-on", "sso", "password threat",
           "brute force", "dictionary attack", "keylogging",
           "shoulder surfing"],
}

SLOT_ANGLE_HINTS = {
    "A8a": "List two malware types (Trojan, worm, virus, spyware).",
    "A8b": "Describe six characteristics or impacts of malware; use at least "
           "two slides and do not just list types.",
    "A9a": "Explain two password security controls (hashed password storage, "
           "access control on password files, account lockout, last-login "
           "display). Do not discuss password threats (A6b).",
    "A9b": "Discuss six authentication mechanisms/controls based on smartcards, "
           "Kerberos tickets, or password security controls; do not discuss "
           "password threats (A6b), biometrics (A4b) or SSO (A4a).",
}

ANGLE_HINTS = {
    "A1": "NIDS architecture, sensor placement, packet analysis and evidence "
          "preservation; avoid generic network threats.",
    "A2": "classical cipher families and transposition/substitution; keep it "
          "to material on the classical-cryptography slides.",
    "A3": "TPM, Nexus/NCA and the chain of trust; explain how the components "
          "interact.",
    "A4": "biometric identification/authentication stages and mechanisms; do "
          "not use passwords, Kerberos or SSO (covered by A9).",
    "A5": "software insecurity, buffer overflows and mitigation techniques.",
    "A6": "malware types and their characteristics; do not use the classes-of-"
          "threats angle (covered by A8).",
    "A7": "formal access-control models (e.g. Chinese Wall, BLP, Biba); do not "
          "repeat the generic ACL/classification angle (covered by A10).",
    "A8": "malware types and characteristics (Trojan, worm, virus, spyware); "
          "do not use classes of threats (A6a) or password threats (A6b).",
    "A9": "password security controls, smartcards or Kerberos; do not use "
          "password threats (A6b), biometrics (A4b) or SSO (A4a).",
    "A10": "access-control structures, classification and reference monitors; "
           "do not repeat the Chinese Wall model (covered by A7).",
    "B1": "morals, ethics, laws and the professional code of ethics.",
    "B2": "malware impact and compromise mechanisms; do not repeat A6's "
          "definition/characteristics angle.",
}


@dataclass
class GroupResult:
    question: str
    slots: list[str]
    topic: str
    tasks: list[str]
    dependent: bool
    attempts: int = 0
    accepted: bool = False
    errors: list[list[str]] = field(default_factory=list)
    retrieved: list[dict] = field(default_factory=list)
    fallback_retrieval: bool = False
    usage: dict = field(default_factory=dict)


def _theory_slots(plan: dict) -> list[dict]:
    return [s for s in plan["slots"] if s["kind"] == "theory"]


def _groups(slots: list[dict]) -> list[list[dict]]:
    by_q: dict[str, list[dict]] = defaultdict(list)
    order: list[str] = []
    for s in slots:
        if s["question"] not in by_q:
            order.append(s["question"])
        by_q[s["question"]].append(s)
    groups: list[list[dict]] = []
    for q in order:
        qslots = by_q[q]
        if len(qslots) > 1:
            # (a)/(b) share a topic.  Generate them together so the pair has
            # distinct angles; dependent pairs additionally make (b) build on
            # (a).
            groups.append(qslots)
        else:
            groups.append(qslots)
    return groups


def _retrieve(index: BM25Index, group: list[dict]) -> tuple[list, bool]:
    topic = group[0]["topic"]
    qid = group[0]["question"]
    extra = " ".join(str(s["task"]) for s in group) + " " + ANGLE_HINTS.get(qid, "")
    query = topic_query(topic, extra)
    allowed = TOPIC_DECKS.get(topic)
    hits = index.search(query, k=10, max_per_deck=4,
                        allowed_prefixes=allowed)
    fallback = False
    if len(hits) < 3:
        fallback = True
        hits = index.search(query, k=10, max_per_deck=4)
    return hits, fallback


def _style_examples(group: list[dict], limit: int = 5) -> list[dict]:
    out: list[dict] = []
    seen = set()
    for s in group:
        for ex in s.get("style_examples", []):
            key = (ex.get("paper"), ex.get("q"))
            if key in seen:
                continue
            seen.add(key)
            out.append(ex)
            if len(out) >= limit:
                return out
    return out


def _prompt(group: list[dict], hits: list, errors: list[str] | None) -> str:
    topic = group[0]["topic"]
    specs = []
    for s in group:
        specs.append({
            "slot": s["slot"],
            "marks": s["marks"],
            "topic": s["topic"],
            "command": s["task"],
            "part": s["part"],
            "dependent": bool(s.get("dependent")),
            "dependent_on": s.get("dependent_on", ""),
            "angle_hint": SLOT_ANGLE_HINTS.get(s["slot"], ""),
        })
    examples = _style_examples(group)
    example_text = "\n".join(
        f"- {e['paper']} {e['q']} ({e['marks']} marks): {e['text']}"
        for e in examples) or "(none available)"
    chunks = "\n\n".join(
        f"[{h.chunk.chunk_id}] {h.chunk.deck} | slide {h.chunk.slide}\n"
        f"{h.chunk.text}" for h in hits)
    qid = group[0]["question"]
    angle = ANGLE_HINTS.get(qid, "")
    pair = len(group) > 1
    dependent = any(s.get("dependent") for s in group)
    if pair and dependent:
        pair_rule = (
            "\nDEPENDENT PAIR: the two questions must be generated together. "
            "Question (b) must begin with 'Refer to your answer in (a)' (or "
            "'Based on the scenario in (a)') and must build on the answer/"
            "scenario of (a); it must not merely repeat (a). Both must stay "
            "on the same topic.\n")
    elif pair:
        pair_rule = (
            "\nSIBLING PAIR: both questions share one topic but must test "
            "different aspects. Do not duplicate each other's question angle "
            "or marking points; the verifier rejects a near-duplicate pair. "
            "Each question has its own mark count and points.\n")
    else:
        pair_rule = ""
    retry = ""
    if errors:
        retry = (
            "\nPREVIOUS ATTEMPT FAILED. Fix every listed error and return a "
            "new draft; do not reuse the same question wording:\n"
            + "\n".join(f"- {e}" for e in errors) + "\n")
    schema = json.dumps({
        "questions": [{
            "slot": "A1a",
            "question": "Explain ...",
            "marking_points": [{
                "point": "one mark point",
                "quote": "verbatim contiguous text from the cited chunk",
                "chunk_id": "exact chunk id from the evidence list",
            }],
        }]
    }, indent=2)
    return f"""Draft original CSC662 Computer Security exam questions.

SLOTS
{json.dumps(specs, indent=2)}

ANGLE HINT (follow this; it prevents repeating another question)
{angle or '(none)'}

RULES
- Use ONLY the lecture evidence below. Do not use outside facts.
- The question must start with the specified command word ({', '.join(s['task'] for s in group)}) and be answerable from the evidence.
- One marking point per mark: exactly the number of points shown in "marks". Each point is worth 1 mark. Phrase the question so it naturally requires that many distinct points (e.g. "Describe six ..." for 6 marks); do not ask for only two items and then pad.
- Every marking point must cite one chunk_id from the evidence list and include a quote copied character-for-character from that chunk. The quote must be a contiguous passage of at least 20 characters (a full clause or sentence, not a single word or bare heading); no ellipses (never write "..." or "…"), no paraphrase, no line-break changes.
- Do not split one fact into several points. For 5/6-mark questions, use at least two different slides and give distinct, non-overlapping points.
- The question and marking points must stay on the slot topic.
- Do NOT copy a style example or any past paper question. Use the style examples only for length and tone. Change the scenario and wording.
- Do not repeat a question angle already used in the paper; the verifier rejects near-duplicates of accepted slots.
- Do not print marks, numbering, "(a)/(b)", or a marking scheme in the question text.
- Question length: about 12-70 words.
- Return one JSON object only, with exactly {len(group)} question(s), matching the slot ids.
{pair_rule}{retry}
STYLE EXAMPLES (real past questions; style only, never copy)
{example_text}

LECTURE EVIDENCE (authoritative; cite chunk_id and quote verbatim)
{chunks}

OUTPUT JSON (this shape)
{schema}
"""


SYSTEM = (
    "You are a university examiner for CSC662 Computer Security. You write "
    "original, grounded exam questions. You never copy past questions. Every "
    "factual marking point is supported by a verbatim quote from the supplied "
    "lecture-slide chunks. Return JSON only."
)


def _slot_record(s: dict) -> dict:
    qid = s.get("question", "")
    return {
        "slot": s["slot"],
        "marks": s["marks"],
        "topic": s["topic"],
        "task": s["task"],
        "part": s["part"],
        "dependent": bool(s.get("dependent")),
        "dependent_on": s.get("dependent_on", ""),
        "style_examples": s.get("style_examples", []),
        "style_mode": s.get("style_mode", ""),
        "low_style_confidence": bool(s.get("low_style_confidence")),
        "angle_required": ANGLE_REQUIRED.get(qid, []),
        "angle_forbidden": ANGLE_FORBIDDEN.get(qid, []),
    }


def generate(plan_path: Path, limit: int = 0, model: str | None = None,
             refresh_decks: bool = False,
             previous: dict | None = None) -> dict:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    slots = _theory_slots(plan)
    groups = _groups(slots)
    accepted: list[VerifiedQuestion] = []
    placeholders: list[Placeholder] = []
    previous_groups: list[dict] = []
    usage = Usage()
    if previous:
        accepted = [VerifiedQuestion.model_validate(q)
                    for q in previous.get("accepted", [])]
        placeholders = [Placeholder.model_validate(p)
                        for p in previous.get("placeholders", [])]
        retry_slots = {p.slot for p in placeholders}
        # Keep a group if any of its slots is a placeholder.
        groups = [g for g in groups
                  if any(s["slot"] in retry_slots for s in g)]
        retry_slots_all = {s["slot"] for g in groups for s in g}
        accepted = [q for q in accepted if q.slot not in retry_slots_all]
        placeholders = [p for p in placeholders
                        if p.slot not in retry_slots_all]
        retry_questions = {g[0]["question"] for g in groups}
        previous_groups = [g for g in previous.get("groups", [])
                           if g.get("question") not in retry_questions]
        # Carry the earlier token spend into the final cost report.
        u = previous.get("usage", {})
        usage = Usage(
            prompt_tokens=int(u.get("prompt_tokens", 0)),
            completion_tokens=int(u.get("completion_tokens", 0)),
            total_tokens=int(u.get("total_tokens", 0)),
            calls=int(u.get("calls", 0)))
    if limit:
        groups = groups[:limit]
    chunks = load_chunks(refresh=refresh_decks)
    index = BM25Index(chunks)
    results: list[GroupResult] = []
    for gi, group in enumerate(groups, 1):
        topic = group[0]["topic"]
        qid = group[0]["question"]
        result = GroupResult(
            question=qid, slots=[s["slot"] for s in group], topic=topic,
            tasks=[s["task"] for s in group],
            dependent=bool(group[0].get("dependent")))
        hits, fallback = _retrieve(index, group)
        result.fallback_retrieval = fallback
        result.retrieved = [{
            "chunk_id": h.chunk.chunk_id, "deck": h.chunk.deck,
            "slide": h.chunk.slide, "score": round(h.score, 2),
            "chars": h.chunk.chars,
        } for h in hits]
        before_calls, before_tokens = usage.calls, usage.total_tokens
        errors: list[str] = []
        verified: list[VerifiedQuestion] = []
        for attempt in range(1, MAX_ATTEMPTS + 1):
            result.attempts = attempt
            user = _prompt(group, hits, errors if attempt > 1 else None)
            try:
                llm = chat_json_result(
                    SYSTEM, user, model=model or config.QWEN_CHEAP_MODEL,
                    temperature=0.25, usage=usage)
            except Exception as e:
                errors = [f"LLM/API error: {e}"]
                result.errors.append(errors)
                continue
            try:
                draft = TheoryDraft.model_validate(llm.data)
            except ValidationError as e:
                errors = [f"JSON schema error: {e.errors()[:4]}"]
                result.errors.append(errors)
                continue
            verified, errors = verify_draft(
                draft, [_slot_record(s) for s in group],
                [h.chunk for h in hits],
                [q.model_dump() for q in accepted])
            result.errors.append(errors)
            if not errors and len(verified) == len(group):
                break
        result.usage = {
            "calls": usage.calls - before_calls,
            "tokens": usage.total_tokens - before_tokens,
        }
        if not errors and len(verified) == len(group):
            accepted.extend(verified)
            result.accepted = True
            print(f"[{gi}/{len(groups)}] {qid} accepted "
                  f"({len(verified)} question(s), attempt {result.attempts})",
                  flush=True)
        else:
            reason = "; ".join(errors[-8:]) if errors else "unknown error"
            for s in group:
                placeholders.append(Placeholder(
                    slot=s["slot"], marks=s["marks"], topic=s["topic"],
                    task=s["task"],
                    reason=reason[:1500], attempts=result.attempts,
                    low_style_confidence=bool(s.get("low_style_confidence"))))
            print(f"[{gi}/{len(groups)}] {qid} PLACEHOLDER after "
                  f"{result.attempts} attempts: {reason[:160]}", flush=True)
        results.append(result)

    accepted.sort(key=lambda q: q.slot)
    placeholders.sort(key=lambda p: p.slot)
    total_usage = usage.as_dict()
    cost = total_usage["cost_usd"]
    accepted_count = len(accepted)
    payload = {
        "model": model or config.QWEN_CHEAP_MODEL,
        "plan": str(plan_path),
        "attempt_limit": MAX_ATTEMPTS,
        "accepted": [q.model_dump() for q in accepted],
        "placeholders": [p.model_dump() for p in placeholders],
        "groups": sorted(previous_groups + [asdict(r) for r in results],
                         key=lambda g: g.get("question", "")),
        "usage": total_usage,
        "accepted_count": accepted_count,
        "placeholder_count": len(placeholders),
        "cost_per_accepted_question_usd": round(
            cost / accepted_count, 6) if accepted_count else None,
        "deck_coverage": coverage(chunks),
        "eth_deck_coverage": coverage(
            [c for c in chunks if c.deck.startswith("071")]),
    }
    return payload


def report(payload: dict) -> str:
    lines = [
        "# Theory module report",
        "",
        f"- model: **{payload['model']}**; attempt limit: "
        f"{payload['attempt_limit']} (initial + up to 3 retries)",
        f"- accepted questions: **{payload['accepted_count']}**; "
        f"placeholders: **{payload['placeholder_count']}**",
        f"- tokens: {payload['usage']['prompt_tokens']} prompt + "
        f"{payload['usage']['completion_tokens']} completion = "
        f"{payload['usage']['total_tokens']} across "
        f"{payload['usage']['calls']} calls",
        f"- estimated cost: **${payload['usage']['cost_usd']:.4f}** "
        f"(input ${payload['usage']['input_price_per_1m']}/M, output "
        f"${payload['usage']['output_price_per_1m']}/M; public qwen-flash "
        "list-price estimate, not an invoice)",
        f"- cost per accepted question: "
        f"**${payload['cost_per_accepted_question_usd'] or 0:.4f}**",
        "",
        "## Accepted questions",
        "",
        "| Slot | Marks | Topic | Command | Sources | Style |",
        "|---|---:|---|---|---|---|",
    ]
    for q in payload["accepted"]:
        style = q["style_mode"] + ("; LOW" if q["low_style_confidence"] else "")
        lines.append(f"| {q['slot']} | {q['marks']} | {q['topic']} | "
                     f"{q['task']} | {'; '.join(q['citations'])} | {style} |")
    lines += [
        "",
        "## Placeholders",
        "",
        "| Slot | Marks | Topic | Command | Attempts | Reason |",
        "|---|---:|---|---|---:|---|",
    ]
    for p in payload["placeholders"]:
        lines.append(f"| {p['slot']} | {p['marks']} | {p['topic']} | "
                     f"{p['task']} | {p['attempts']} | "
                     f"{p['reason'].replace('|', '/')} |")
    lines += [
        "",
        "## Group attempts and retrieval",
        "",
        "| Question | Slots | Attempts | Result | Fallback retrieval | Top sources |",
        "|---|---|---:|---|---|---|",
    ]
    for g in payload["groups"]:
        top = "; ".join(f"{r['deck']} s{r['slide']}"
                        for r in g["retrieved"][:3]) or "none"
        lines.append(f"| {g['question']} | {', '.join(g['slots'])} | "
                     f"{g['attempts']} | "
                     f"{'accepted' if g['accepted'] else 'placeholder'} | "
                     f"{'yes' if g['fallback_retrieval'] else 'no'} | {top} |")
    lines += [
        "",
        "## Deck coverage",
        "",
        f"- 071 Ethics: {payload['eth_deck_coverage']}",
        f"- total decks with text: {len(payload['deck_coverage'])}; "
        f"total chunks: {sum(v['chunks'] for v in payload['deck_coverage'].values())}",
        "",
        "## Verification rules applied",
        "",
        "- quote must be a verbatim contiguous substring of the cited retrieved "
        "chunk (whitespace-normalised); ellipses rejected;",
        "- exactly one marking point per mark;",
        "- near-copy rejected at fuzzy similarity >= 0.80 against all 35 papers;",
        "- command word must appear in the question; dependent (b) must refer "
        "back to (a);",
        "- no retrieval evidence => placeholder, never an unsourced answer.",
    ]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan",
                    default=str(config.OUTPUTS_DIR / "planner_revised_realistic.json"))
    ap.add_argument("--out-prefix", default="theory_drafts_realistic")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--model", default=config.QWEN_CHEAP_MODEL)
    ap.add_argument("--refresh-decks", action="store_true")
    ap.add_argument("--retry-placeholders", action="store_true",
                    help="keep prior accepted questions and retry only the "
                         "groups that ended as placeholders")
    args = ap.parse_args()
    if not config.QWEN_API_KEY:
        raise SystemExit("QWEN_API_KEY is not set")
    prefix = args.out_prefix.split("/")[-1]
    jp = config.OUTPUTS_DIR / f"{prefix}.json"
    mp = config.OUTPUTS_DIR / f"{prefix}.md"
    previous = None
    if args.retry_placeholders:
        if not jp.exists():
            raise SystemExit(f"no previous payload at {jp}")
        previous = json.loads(jp.read_text(encoding="utf-8"))
    payload = generate(Path(args.plan), args.limit, args.model,
                       args.refresh_decks, previous)
    if previous:
        payload["retried_placeholders"] = True
    jp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md = report(payload)
    mp.write_text(md, encoding="utf-8")
    print(md)
    print(f"\nwrote {jp} and {mp}")


if __name__ == "__main__":
    main()
