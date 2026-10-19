"""Topic x Task classifier tests, incl. the owner's rules: tight task cues,
access-control construction as compute, new topics, sibling inheritance."""
from __future__ import annotations

from src.fingerprint.types import (classify_row, classify_task, classify_topic,
                                   has_concrete_inputs, is_whole_block_row,
                                   label_group, machine_verifiable)


def test_hash_properties_is_theory_not_compute():
    text = ("Explain THREE (3) desirable properties that the hash function H(x) "
            "must possess in order to guarantee the security of the signature scheme.")
    lab = classify_row(text)
    assert lab["topic"] == "hashing/signatures"
    assert lab["task"] == "define/explain"
    assert not lab["machine_verifiable"]


def test_numberless_prose_is_not_compute():
    text = ("Describe FIVE (5) steps on how to determine if your computer system "
            "has been compromised.")
    lab = classify_row(text)
    assert lab["task"] != "compute"
    assert not has_concrete_inputs(text)


def test_compare_question_stays_compare():
    text = "Differentiate between substitution cipher and transposition cipher."
    lab = classify_row(text)
    assert lab["topic"] == "classical ciphers"
    assert lab["task"] == "compare"
    assert not lab["machine_verifiable"]


def test_caesar_decrypt_is_compute_and_verifiable():
    text = ("Using Caesar Cipher technique, decrypt the following ciphertext. "
            "wuhdwblpsrvvleoh")
    lab = classify_row(text)
    assert lab["topic"] == "classical ciphers"
    assert lab["task"] == "compute"
    assert lab["machine_verifiable"]


def test_rsa_params_is_compute_and_verifiable():
    text = ("Zetty wants to send the message using RSA. She selects p = 7, q = 11 "
            "and e = 9. Show how Zetty encrypt this message.")
    lab = classify_row(text)
    assert lab["topic"] == "public-key"
    assert lab["task"] == "compute"
    assert lab["machine_verifiable"]


def test_des_key_schedule_is_compute_and_verifiable():
    text = ("Figure 1 shows table PC-1 for Data Encryption Standard (DES) "
            "algorithm. Find: i) Permuted key, K+ (in hexadecimal)")
    lab = classify_row(text)
    assert lab["topic"] == "block ciphers"
    assert lab["task"] == "compute"
    assert lab["machine_verifiable"]


def test_compute_without_solver_topic_is_not_verifiable():
    text = "Given the IP packet and Key = 7A1F, calculate the CRC value."
    lab = classify_row(text)
    assert lab["topic"] == "network security"
    assert lab["task"] == "compute"
    assert not lab["machine_verifiable"]


def test_acm_construction_is_compute_and_verifiable():
    text = ("Write a access control matrix (ACM). Write a set of access control "
            "lists (ACL). Write a set of capability lists (CL).")
    lab = classify_row(text)
    assert lab["topic"] == "access control models"
    assert lab["task"] == "compute"
    assert lab["machine_verifiable"]


def test_blp_rule_application_is_compute_and_verifiable():
    text = ("Based on Biba's rule, explain the condition when read and write "
            "activities can be conducted simultaneously.")
    lab = classify_row(text)
    assert lab["topic"] == "access control models"
    assert lab["task"] == "compute"
    assert lab["machine_verifiable"]


def test_draw_chinese_wall_is_diagram_not_compute():
    text = "Draw a Chinese Wall security model diagram."
    lab = classify_row(text)
    assert lab["topic"] == "access control models"
    assert lab["task"] == "draw/diagram"
    assert not lab["machine_verifiable"]


def test_list_needs_count_word():
    lab = classify_row("Identify the purpose of Digital Right Management (DRM).")
    assert lab["topic"] == "risk/management"
    assert lab["task"] == "define/explain"
    lab2 = classify_row("Identify TWO (2) categories sectors of biometric applications.")
    assert lab2["task"] == "list/enumerate"


def test_scenario_beats_define():
    text = ("Based on the following scenario, state a suitable security objective "
            "and suggest a suitable security mechanism:")
    lab = classify_row(text)
    assert lab["topic"] == "risk/management"
    assert lab["task"] == "scenario/justify"


def test_new_topics():
    assert classify_topic("Differentiate between Asymmetric encryption and "
                          "Symmetric encryption.") == "general cryptography"
    assert classify_topic("State TWO (2) examples of behavioral biometrics.") == \
        "authentication/biometrics"
    assert classify_topic("List TWO (2) files containing information about user "
                          "accounts.") == "software/OS security"
    assert classify_topic("What is the blockchain?") == "trusted computing/blockchain"
    assert classify_topic("Explain the process of PKI framework.") == "public-key"


def test_part_a_short_objective():
    lab = classify_row("What is the blockchain?", q_no="A1")
    assert lab["task"] == "short objective"


def test_machine_verifiable_definition():
    assert machine_verifiable("classical ciphers", "compute", True)
    assert not machine_verifiable("classical ciphers", "compute", False)
    assert not machine_verifiable("classical ciphers", "compare", True)
    assert not machine_verifiable("network security", "compute", True)


def test_classify_task_default_is_define_explain():
    assert classify_task("Random vague stem with no cue words") == "define/explain"


def test_label_group_inherits_topic():
    rows = [
        {"Original question text": "Based on Vigene're Tableau given in Figure 1, "
         "encrypt the following plaintext: GOODLUCKBABY",
         "Q no.": "2", "Question type": "", "Wording note": ""},
        {"Original question text": "ii) Using the key gasing, encrypt the following "
         "plaintext to ciphertext. TIMANG TINGGI",
         "Q no.": "2", "Question type": "", "Wording note": ""},
    ]
    labs = label_group(rows)
    assert labs[1]["topic"] == "classical ciphers"
    assert any("topic inherited" in f for f in labs[1]["flags"])


def test_label_group_propagates_rsa_params():
    rows = [
        {"Original question text": "Zetty sends a message using RSA. She selects "
         "p = 7, q = 11 and e = 9.",
         "Q no.": "6", "Question type": "", "Wording note": ""},
        {"Original question text": "Show how Zetty encrypt this message using RSA.",
         "Q no.": "6", "Question type": "", "Wording note": ""},
    ]
    labs = label_group(rows)
    assert labs[1]["task"] == "compute"
    assert labs[1]["machine_verifiable"]
    assert any("inputs inherited" in f for f in labs[1]["flags"])


def test_whole_block_detection():
    assert is_whole_block_row({"Wording note": "verbatim check failed; whole block stored"})
    assert not is_whole_block_row({"Wording note": ""})
