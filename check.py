#!/usr/bin/env python3
"""Independent checker for the Afterlife Test registry.

Works without afterlifetest.com. Needs only Python 3 (no extra packages).

    python3 check.py chain registry.json
        Recomputes both hash chains and reports any broken link.

    python3 check.py append previous.json registry.json
        Checks that the new copy only ADDS entries: every seal and change log
        entry in the older copy must still be there, unchanged, in the same order.

    python3 check.py strip registry.json
        Removes names, death report sources and the text of opening accounts,
        so the public copy holds no personal details. The chains still check out.

    python3 check.py phrase registry.json <seal number> "<phrase>"
        Checks a phrase against one seal, entirely on this computer.

Exit code 0 = OK, 1 = a problem was found, 2 = wrong usage.
"""
import hashlib
import json
import sys
import unicodedata

GENESIS = "0" * 64


def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not str(data.get("format", "")).startswith("afterlifetest-registry"):
        raise SystemExit(f"{path}: not an Afterlife Test registry export")
    return data


def normalize_phrase(text):
    # Same rules as the website: Unicode NFC, lower case, single spaces, trimmed.
    return " ".join(unicodedata.normalize("NFC", text).lower().split())


def check_chain(data):
    problems = []
    prev = GENESIS
    for s in data.get("seals", []):
        expected = sha256("|".join([prev, s["id"], s["name_hash"], s["salt"], s["hash"], str(s["iterations"]), s["created_at_raw"]]))
        if s.get("prev_chain") != prev:
            problems.append(f"seal {s['id']}: previous link is {s.get('prev_chain')}, expected {prev}")
        if s.get("chain") != expected:
            problems.append(f"seal {s['id']}: link does not match its content")
        if s.get("name") is not None and sha256(s["salt"] + "|" + s["name"]) != s["name_hash"]:
            problems.append(f"seal {s['id']}: name does not match its fingerprint")
        prev = s.get("chain", "")
    prev = GENESIS
    for c in data.get("changes", []):
        expected = sha256("|".join([prev, str(c["id"]), c["seal_id"], c["action"], c["reason"], c["created_at_raw"]]))
        if c.get("prev_chain") != prev:
            problems.append(f"change {c['id']}: previous link is {c.get('prev_chain')}, expected {prev}")
        if c.get("chain") != expected:
            problems.append(f"change {c['id']}: link does not match its content")
        prev = c.get("chain", "")
    return problems


# Fields that may never change once written. Counters and statuses (attempts,
# opened, sign of life, death report, hidden name) change legitimately and are
# protected by the change log instead.
FIXED_SEAL = ("id", "name_hash", "salt", "hash", "iterations", "created_at_raw", "prev_chain", "chain")
FIXED_CHANGE = ("id", "seal_id", "action", "reason", "created_at_raw", "prev_chain", "chain")


def check_append(old, new):
    problems = []
    for key, fields, label in (("seals", FIXED_SEAL, "seal"), ("changes", FIXED_CHANGE, "change")):
        a, b = old.get(key, []), new.get(key, [])
        if len(b) < len(a):
            problems.append(f"{key}: {len(a) - len(b)} entries disappeared")
        for i, x in enumerate(a[: len(b)]):
            y = b[i]
            for f in fields:
                if x.get(f) != y.get(f):
                    problems.append(f"{label} {x.get('id')}: field '{f}' changed")
                    break
    return problems


def strip(data):
    # The copy needs only what proves a phrase: number, date, salt, fingerprint
    # and the chains. Names stay on the live site, where their creators can hide them.
    for s in data.get("seals", []):
        s["name"] = None
        s["death_source"] = None
    data["openings"] = [
        {k: o.get(k) for k in ("id", "seal_id", "filed_at", "content_fingerprint")}
        for o in data.get("openings", [])
    ]
    data["mirror_note"] = ("Independent copy without names or personal details. "
                           "Names, death report sources and opening accounts are on the live site only.")
    return data


def check_phrase(data, seal_id, phrase):
    seal = next((s for s in data.get("seals", []) if s["id"].lower() == seal_id.lower()), None)
    if seal is None:
        raise SystemExit(f"Seal {seal_id} is not in this file.")
    got = hashlib.pbkdf2_hmac("sha256", normalize_phrase(phrase).encode("utf-8"), bytes.fromhex(seal["salt"]), int(seal["iterations"])).hex()
    return got == seal["hash"], seal


def main(argv):
    if len(argv) >= 3 and argv[1] == "chain":
        data = load(argv[2])
        problems = check_chain(data)
        print(f"{len(data.get('seals', []))} seals, {len(data.get('changes', []))} change log entries, exported {data.get('exported_at')}")
    elif len(argv) >= 4 and argv[1] == "append":
        old, new = load(argv[2]), load(argv[3])
        problems = check_chain(new) + check_append(old, new)
        print(f"Old copy: {len(old.get('seals', []))} seals. New copy: {len(new.get('seals', []))} seals.")
    elif len(argv) >= 3 and argv[1] == "strip":
        data = strip(load(argv[2]))
        with open(argv[2], "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
            f.write("\n")
        print(f"Removed personal details from {argv[2]}.")
        return 0
    elif len(argv) >= 5 and argv[1] == "phrase":
        ok, seal = check_phrase(load(argv[2]), argv[3], " ".join(argv[4:]))
        name = seal.get("name") or "name not kept in this copy"
        if ok:
            print(f"MATCH. The phrase matches seal {seal['id']} ({name}).")
            print("Nothing was sent anywhere. To record the opening publicly, enter the phrase on the seal's page as well.")
            return 0
        print(f"No match for seal {seal['id']} ({name}).")
        return 1
    else:
        print(__doc__)
        return 2
    if problems:
        print("PROBLEMS FOUND:")
        for p in problems:
            print("  - " + p)
        return 1
    print("OK: every link checks out.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
