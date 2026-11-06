"""Deterministic Stage-6 generators for CSC429 non-diagram questions.

Only parameterisable data-representation slots are generated.  Descriptive,
diagram, I/O, memory, parallel and assembly slots keep the real past-paper
resolver.  Every generated answer is computed independently; no model is
called.

    uv run python -m src.subjects.csc429.generators --seed 1
    uv run python -m src.subjects.csc429.generators --validate
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import struct
from pathlib import Path

from src import config

SUBJECT = "CSC429"
TRACKING = config.TRACKING_DIR / "csc429"
SAMPLE_PATH = TRACKING / "generator_sample_seed_01.json"
VALIDATION_PATH = TRACKING / "generator_validation.json"
PLAN_PATH = TRACKING / "planner_seed_01.json"

GENERATOR_IDS = (
    "csc429.number_base_conversion",
    "csc429.signed_arithmetic",
    "csc429.ieee754_single",
)

BASE_NAMES = {
    2: ("binary", "2"),
    8: ("octal", "8"),
    16: ("hexadecimal", "16"),
}


def _rng(seed: int, slot: str, salt: str) -> random.Random:
    digest = hashlib.sha256(
        f"csc429:{seed}:{slot}:{salt}".encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def choose_generator(seed: int, slot: str, marks: int) -> str:
    number = int(slot[1:]) if slot[1:].isdigit() else 0
    index = (int(seed) + number) % len(GENERATOR_IDS)
    return GENERATOR_IDS[index]


def _question(seed: int, slot: str, marks: int, topic: str,
              generator_id: str, text: str, subparts: list[dict],
              answer: str, marking: list[str], metadata: dict) -> dict:
    return {
        "question_id": f"CSC429-GEN-{int(seed):02d}-{slot}",
        "paper_id": f"CSC429-GEN-{int(seed):02d}",
        "part": slot[0],
        "question_no": int(slot[1:]) if slot[1:].isdigit() else 1,
        "slot": slot,
        "marks": marks,
        "topic": topic,
        "topic_label": "Data representation and number systems",
        "kind": "generated",
        "generator_id": generator_id,
        "variant_policy": "controlled_numeric",
        "text": text,
        "text_sha256": _sha(text),
        "subparts": subparts,
        "answer": answer,
        "marking": marking,
        "metadata": metadata,
        "assets": [],
        "source_file": "",
        "pages": [],
        "review_flags": [],
    }


def _number_base(seed: int, slot: str, marks: int, topic: str) -> dict:
    rng = _rng(seed, slot, "number_base")
    if marks == 5:
        base = rng.choice((2, 8, 16))
        value = rng.randint(120, 4095)
        name, suffix = BASE_NAMES[base]
        converted = format(value, {2: "b", 8: "o", 16: "X"}[base])
        text = (f"Convert {value}10 to {name}. Show your complete workflow.")
        subparts = []
        answer = f"{value}10 = {converted}{suffix}"
        marking = [
            "1 mark for identifying the target base.",
            "1 mark for a correct repeated-division or place-value method.",
            "1 mark for the correct digit sequence.",
            "1 mark for the correct base subscript.",
            "1 mark for a complete, consistent workflow.",
        ]
    else:
        dec_value = rng.randint(250, 4095)
        hex_value = rng.randint(0x100, 0xFFF)
        converted = format(dec_value, "X")
        text = ("Answer both parts. Show your complete workflow.\n"
                f"a) Convert {dec_value}10 to hexadecimal.\n"
                f"b) Convert {hex_value:X}16 to decimal.")
        subparts = [
            {"label": "a", "text": f"Convert {dec_value}10 to hexadecimal.",
             "marks": 5,
             "answer": f"{dec_value}10 = {converted}16",
             "marking": [
                 "1 mark for repeated division by 16.",
                 "1 mark for correct remainders.",
                 "1 mark for reading remainders in reverse order.",
                 "1 mark for the correct hexadecimal digits.",
                 "1 mark for the base subscript.",
             ]},
            {"label": "b", "text": f"Convert {hex_value:X}16 to decimal.",
             "marks": 5,
             "answer": f"{hex_value:X}16 = {hex_value}10",
             "marking": [
                 "1 mark for place values 16^2, 16^1 and 16^0.",
                 "1 mark for correct digit values.",
                 "1 mark for correct products.",
                 "1 mark for correct addition.",
                 "1 mark for the final decimal value.",
             ]},
        ]
        answer = (f"a) {dec_value}10 = {converted}16; "
                  f"b) {hex_value:X}16 = {hex_value}10")
        marking = ["Part a: 5 marks.", "Part b: 5 marks."]
    return _question(
        seed, slot, marks, topic, "csc429.number_base_conversion", text,
        subparts, answer, marking,
        {"base": base if marks == 5 else None,
         "converted": converted if marks == 5 else None,
         "dec_value": value if marks == 5 else dec_value,
         "hex_value": hex_value if marks == 10 else None})


def _sm_byte(value: int) -> str:
    sign = 1 if value < 0 else 0
    return f"{sign} {abs(value):07b}"


def _ones_byte(value: int) -> str:
    if value < 0:
        return format((~abs(value)) & 0xFF, "08b")
    return format(value & 0xFF, "08b")


def _twos_byte(value: int) -> str:
    if value < 0:
        return format((~abs(value) + 1) & 0xFF, "08b")
    return format(value & 0xFF, "08b")


def _signed_values(rng: random.Random) -> tuple[int, int, int]:
    for _ in range(1000):
        left = rng.randint(-100, 100)
        right = rng.randint(-100, 100)
        result = left - right
        if (left < 0 or right < 0) and abs(left) >= 10 and abs(right) >= 10:
            if -127 <= result <= 127 and abs(result) >= 10:
                return left, right, result
    raise RuntimeError("could not generate a signed 8-bit subtraction")


def _signed_arithmetic(seed: int, slot: str, marks: int, topic: str) -> dict:
    rng = _rng(seed, slot, "signed")
    left, right, result = _signed_values(rng)
    expression = f"{left} - ({right})" if right < 0 else f"{left} - {right}"
    left_sm = _sm_byte(left)
    right_sm = _sm_byte(right)
    result_sm = _sm_byte(result)
    result_ones = _ones_byte(result)
    result_twos = _twos_byte(result)
    if marks == 5:
        text = (f"Calculate {expression} using the sign-and-magnitude method. "
                "Assume an 8-bit byte. Show your complete workflow.")
        subparts = []
        answer = (f"left {left} -> {left_sm}; right {right} -> {right_sm}; "
                  f"{expression} = {result} -> sign-magnitude {result_sm}")
        marking = [
            "1 mark for converting both operands to sign-magnitude.",
            "1 mark for applying the sign rule for subtraction.",
            "1 mark for the correct magnitude operation.",
            "1 mark for the correct sign bit.",
            "1 mark for the final decimal and byte representation.",
        ]
    else:
        text = ("Answer both parts for the same expression. Assume an 8-bit "
                f"byte.\nExpression: {expression}")
        subparts = [
            {"label": "a", "text": f"Calculate {expression} using sign and magnitude.",
             "marks": 5,
             "answer": (f"left {left} -> {left_sm}; right {right} -> {right_sm}; "
                        f"{expression} = {result} -> sign-magnitude {result_sm}"),
             "marking": [
                 "1 mark for operand representations.",
                 "1 mark for sign handling.",
                 "1 mark for magnitude arithmetic.",
                 "1 mark for the result sign bit.",
                 "1 mark for the final byte.",
             ]},
            {"label": "b", "text": f"Calculate {expression} using 1's and 2's complement.",
             "marks": 5,
             "answer": (f"left {left} -> 1's {_ones_byte(left)}, 2's {_twos_byte(left)}; "
                        f"right {right} -> 1's {_ones_byte(right)}, 2's {_twos_byte(right)}; "
                        f"{expression} = {result} -> 1's {result_ones}, 2's {result_twos}"),
             "marking": [
                 "1 mark for the positive operand in binary.",
                 "1 mark for the 1's complement of the negative operand.",
                 "1 mark for adding 1 to form the 2's complement.",
                 "1 mark for the correct 8-bit result.",
                 "1 mark for converting the result back to decimal.",
             ]},
        ]
        answer = (f"left {left} -> SM {left_sm}, 2's {_twos_byte(left)}; "
                  f"right {right} -> SM {right_sm}, 2's {_twos_byte(right)}; "
                  f"{expression} = {result} -> SM {result_sm}, "
                  f"1's {result_ones}, 2's {result_twos}")
        marking = ["Part a: 5 marks.", "Part b: 5 marks."]
    return _question(
        seed, slot, marks, topic, "csc429.signed_arithmetic", text, subparts,
        answer, marking,
        {"left": left, "right": right, "result": result,
         "sign_magnitude": result_sm, "ones": result_ones, "twos": result_twos})


def _ieee(value: float) -> dict:
    packed = struct.pack(">f", value)
    bits = int.from_bytes(packed, "big")
    sign = (bits >> 31) & 1
    exponent = (bits >> 23) & 0xFF
    fraction = bits & 0x7FFFFF
    return {
        "value": value,
        "hex": f"{bits:08X}",
        "binary": f"{bits:032b}",
        "sign": sign,
        "exponent": exponent,
        "fraction": fraction,
        "exponent_bits": f"{exponent:08b}",
        "fraction_bits": f"{fraction:023b}",
    }


def _ieee_value(rng: random.Random, *, decode: bool = False) -> float:
    pool = [12.5, -6.75, 3.25, -20.125, 0.375, 100.5, -0.625, 18.75,
            2.5, -11.375, 44.25, -31.5]
    return rng.choice(pool)


def _ieee_answer(fields: dict) -> str:
    return (f"{fields['value']}10 = 0x{fields['hex']} "
            f"(sign={fields['sign']}, exponent={fields['exponent_bits']}, "
            f"fraction={fields['fraction_bits']})")


def _ieee754(seed: int, slot: str, marks: int, topic: str) -> dict:
    rng = _rng(seed, slot, "ieee")
    if marks == 5:
        value = _ieee_value(rng)
        fields = _ieee(value)
        text = (f"Convert {value} to IEEE 754 single-precision format. "
                "Give the answer in hexadecimal and show the sign, exponent "
                "and mantissa fields.")
        subparts = []
        answer = _ieee_answer(fields)
        marking = [
            "1 mark for the sign bit.",
            "1 mark for the biased exponent.",
            "1 mark for the 23-bit fraction.",
            "1 mark for the correct 32-bit grouping.",
            "1 mark for the final hexadecimal value.",
        ]
        metadata = fields
    else:
        encode_value = _ieee_value(rng)
        decode_value = _ieee_value(rng)
        encode = _ieee(encode_value)
        decode = _ieee(decode_value)
        text = "Answer both parts. Show your complete workflow."
        subparts = [
            {"label": "a",
             "text": (f"Convert {encode_value} to IEEE 754 single precision. "
                      "Give the answer in hexadecimal."),
             "marks": 5, "answer": _ieee_answer(encode),
             "marking": [
                 "1 mark for sign, exponent and mantissa.",
                 "1 mark for the biased exponent.",
                 "1 mark for the 23-bit fraction.",
                 "1 mark for the 32-bit binary grouping.",
                 "1 mark for the hexadecimal result.",
             ]},
            {"label": "b",
             "text": (f"Convert the IEEE 754 single-precision value "
                      f"0x{decode['hex']} to decimal."),
             "marks": 5,
             "answer": f"0x{decode['hex']} = {decode['value']}10",
             "marking": [
                 "1 mark for the sign bit.",
                 "1 mark for the exponent field.",
                 "1 mark for the fraction field.",
                 "1 mark for applying the bias and significand.",
                 "1 mark for the final decimal value.",
             ]},
        ]
        answer = (f"a) {_ieee_answer(encode)}; "
                  f"b) 0x{decode['hex']} = {decode['value']}10")
        marking = ["Part a: 5 marks.", "Part b: 5 marks."]
        metadata = {"encode": encode, "decode": decode}
    return _question(
        seed, slot, marks, topic, "csc429.ieee754_single", text, subparts,
        answer, marking, metadata)


GENERATORS = {
    "csc429.number_base_conversion": _number_base,
    "csc429.signed_arithmetic": _signed_arithmetic,
    "csc429.ieee754_single": _ieee754,
}


def generate_for_slot(seed: int, slot: str, topic: str, marks: int) -> dict | None:
    if topic != "data_representation":
        return None
    generator_id = choose_generator(seed, slot, marks)
    generator = GENERATORS.get(generator_id)
    if generator is None:
        raise ValueError(f"missing generator: {generator_id}")
    question = generator(seed, slot, marks, topic)
    if sum(subpart["marks"] for subpart in question["subparts"]) not in (0, marks):
        raise AssertionError(f"subpart marks do not sum to {marks}")
    return question


def verify_question(question: dict) -> list[str]:
    """Independently recompute the generated answer."""
    errors = []
    gid = question["generator_id"]
    meta = question["metadata"]
    if gid == "csc429.number_base_conversion":
        if question["marks"] == 5:
            value = int(meta["dec_value"])
            base = int(meta["base"])
            expected = format(value, {2: "b", 8: "o", 16: "X"}[base])
            if expected != meta["converted"]:
                errors.append("number-base conversion mismatch")
            if f"{expected}{base}" not in question["answer"]:
                errors.append("number-base answer mismatch")
        else:
            if f"{int(meta['dec_value']):X}" not in question["answer"]:
                errors.append("part-a answer mismatch")
            if str(int(meta["hex_value"])) not in question["answer"]:
                errors.append("part-b answer mismatch")
    elif gid == "csc429.signed_arithmetic":
        result = int(meta["result"])
        if result != int(meta["left"]) - int(meta["right"]):
            errors.append("signed result mismatch")
        if _sm_byte(result) != meta["sign_magnitude"]:
            errors.append("sign-magnitude mismatch")
        if _ones_byte(result) != meta["ones"]:
            errors.append("1's complement mismatch")
        if _twos_byte(result) != meta["twos"]:
            errors.append("2's complement mismatch")
    elif gid == "csc429.ieee754_single":
        if question["marks"] == 5:
            fields = _ieee(float(meta["value"]))
            if fields["hex"] != meta["hex"]:
                errors.append("IEEE encode mismatch")
        else:
            encode = _ieee(float(meta["encode"]["value"]))
            decode = _ieee(float(meta["decode"]["value"]))
            if encode["hex"] != meta["encode"]["hex"]:
                errors.append("IEEE part-a mismatch")
            if decode["hex"] != meta["decode"]["hex"]:
                errors.append("IEEE part-b mismatch")
            decoded = struct.unpack(">f", bytes.fromhex(meta["decode"]["hex"]))[0]
            if decoded != float(meta["decode"]["value"]):
                errors.append("IEEE decode mismatch")
    else:
        errors.append(f"unknown generator: {gid}")
    return errors


def validate_all(seed_count: int = 20) -> dict:
    from src.subjects.csc429.planner import build_plan
    coverage = {
        gid: {"slots": 0, "seeds": set(), "errors": []}
        for gid in GENERATOR_IDS
    }
    sample = []
    total = 0
    for seed in range(1, seed_count + 1):
        plan = build_plan(seed)
        generated = []
        for slot in plan["slots"]:
            if slot["resolver"] != "csc429.generator":
                continue
            question = generate_for_slot(
                seed, slot["slot"], slot["topic"], slot["marks"])
            if question is None:
                raise AssertionError(f"missing generated slot {seed} {slot['slot']}")
            errors = verify_question(question)
            coverage[question["generator_id"]]["slots"] += 1
            coverage[question["generator_id"]]["seeds"].add(seed)
            if errors:
                coverage[question["generator_id"]]["errors"].extend(
                    f"{seed}/{slot['slot']}: {error}" for error in errors)
            generated.append(question)
            total += 1
        if seed == 1:
            sample = generated
    payload = {
        "subject": SUBJECT,
        "generated_by": "src.subjects.csc429.generators",
        "model": "deterministic",
        "cost_usd": 0.0,
        "seeds": seed_count,
        "generated_slots": total,
        "generators": {
            gid: {
                "slots": value["slots"],
                "seeds": sorted(value["seeds"]),
                "errors": value["errors"],
            }
            for gid, value in coverage.items()
        },
        "errors": [
            error for value in coverage.values() for error in value["errors"]
        ],
    }
    sample_payload = {
        "subject": SUBJECT,
        "seed": 1,
        "generated_slots": len(sample),
        "questions": sample,
    }
    SAMPLE_PATH.write_text(
        json.dumps(sample_payload, indent=2, ensure_ascii=False),
        encoding="utf-8")
    VALIDATION_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()
    if args.validate:
        print(json.dumps(validate_all(20), indent=2))
        return
    plan_path = TRACKING / f"planner_seed_{int(args.seed):02d}.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    generated = []
    for slot in plan["slots"]:
        question = generate_for_slot(
            int(args.seed), slot["slot"], slot["topic"], slot["marks"])
        if question is not None:
            generated.append(question)
    print(json.dumps({
        "seed": int(args.seed),
        "generated_slots": len(generated),
        "generators": [q["generator_id"] for q in generated],
        "questions": generated,
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
