#!/usr/bin/env python3
"""Content validator for Kitchen Substitute (docs/SPEC.md §3, README 'Content rules').

Runs on every PR (CI) and before every pack build. Exit 1 on any violation.
Mirrors vocabularies in KitchenSubstitute/Models.swift — keep in sync.
"""
import json
import re
import sys
from pathlib import Path

DIET_TAGS = {"vegan", "dairy-free", "gluten-free", "egg-free", "nut-free",
             "peanut-free", "soy-free", "fish-free", "shellfish-free",
             "low-sodium", "alcohol-free"}
ALLERGENS = {"dairy", "gluten", "egg", "nut", "peanut", "soy", "fish", "shellfish",
             "alcohol", "meat"}
DECIMAL_RE = re.compile(r"\d+\.\d+")  # kitchen units must be fractions, never decimals
SLUG_RE = re.compile(r"^[a-z0-9-]+$")

errors: list[str] = []
warns: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def main() -> int:
    path = Path(__file__).resolve().parent.parent / "content" / "kitchen_subs.json"
    try:
        pack = json.loads(path.read_text())
    except Exception as e:
        print(f"FATAL: cannot parse {path}: {e}")
        return 1

    meta = pack.get("meta", {})
    if meta.get("schema_version") != 1:
        err(f"meta.schema_version must be 1, got {meta.get('schema_version')}")
    if not isinstance(meta.get("pack_version"), int) or meta["pack_version"] < 1:
        err(f"meta.pack_version must be a positive int, got {meta.get('pack_version')}")
    if not meta.get("released"):
        err("meta.released is required (ISO date)")

    entries = pack.get("entries", [])
    if len(entries) < 50:
        err(f"MVP requires >= 50 entries, found {len(entries)}")

    seen_entry_ids: set[str] = set()
    seen_names: dict[str, str] = {}      # lowercase name/alias -> owner entry id
    seen_sub_ids: set[str] = set()

    for e in entries:
        eid = e.get("id", "<missing>")
        ctx = f"[entry {eid}]"

        if eid in seen_entry_ids:
            err(f"{ctx} duplicate entry id")
        seen_entry_ids.add(eid)
        if not SLUG_RE.match(eid):
            err(f"{ctx} id must be a lowercase slug")

        name = e.get("name")
        if not name:
            err(f"{ctx} missing name")
            continue
        for term in [name] + list(e.get("aliases", [])):
            low = term.lower()
            if low in seen_names and seen_names[low] != eid:
                err(f"{ctx} name/alias '{term}' already owned by entry {seen_names[low]}")
            seen_names[low] = eid

        if not e.get("category"):
            err(f"{ctx} missing category")
        if not e.get("role_in_recipes"):
            err(f"{ctx} missing role_in_recipes")

        contains = e.get("contains", [])
        for c in contains:
            if c not in ALLERGENS:
                err(f"{ctx} unknown allergen '{c}'")

        subs = e.get("subs", [])
        if not subs:
            err(f"{ctx} has no substitutes")
        for s in subs:
            sid = s.get("id", "<missing>")
            sctx = f"{ctx}[sub {sid}]"
            if sid in seen_sub_ids:
                err(f"{sctx} duplicate sub id")
            seen_sub_ids.add(sid)

            for field in ("name", "use", "metric_use", "basis", "function_note"):
                if not str(s.get(field, "")).strip():
                    err(f"{sctx} missing/empty '{field}'")

            for field in ("use", "metric_use", "basis"):
                if DECIMAL_RE.search(str(s.get(field, ""))):
                    err(f"{sctx} '{field}' contains a decimal — use fractions, never decimals")

            tier = s.get("pantry_tier")
            if tier not in (1, 2, 3):
                err(f"{sctx} pantry_tier must be 1, 2 or 3, got {tier}")

            for field in ("tradeoffs", "best_for"):
                if field in s and not str(s[field]).strip():
                    err(f"{sctx} '{field}' present but empty")

            if not isinstance(s.get("baking_safe"), bool):
                err(f"{sctx} baking_safe must be boolean")
            elif s["baking_safe"] is False and not str(s.get("safety_note", "")).strip():
                err(f"{sctx} baking_safe=false requires a safety_note")

            tags = s.get("diet_tags", [])
            unknown = [t for t in tags if t not in DIET_TAGS]
            if unknown:
                err(f"{sctx} unknown diet tags: {unknown}")
            tagset = set(tags)
            if "vegan" in tagset and not {"dairy-free", "egg-free"} <= tagset:
                err(f"{sctx} vegan implies dairy-free and egg-free")
            if "vegan" in tagset and set(s.get("contains", [])) & {"dairy", "egg", "fish", "shellfish", "meat"}:
                err(f"{sctx} vegan conflicts with contains")
            # Free-tags XOR contains: a sub either is free of an allergen (tag) or
            # contains it (positive data) — the badge UI depends on this never guessing.
            contains = set(s.get("contains", []))
            if "contains" not in s:
                err(f"{sctx} missing 'contains' list (positive allergen data required)")
            else:
                for allergen, free in [("dairy","dairy-free"),("gluten","gluten-free"),
                                       ("egg","egg-free"),("nut","nut-free"),
                                       ("peanut","peanut-free"),("soy","soy-free"),
                                       ("fish","fish-free"),("shellfish","shellfish-free"),
                                       ("alcohol","alcohol-free")]:
                    if allergen in contains and free in tagset:
                        err(f"{sctx} has '{free}' tag but contains lists '{allergen}'")
            if "dairy" in contains and "dairy-free" in tagset and s.get("baking_safe") is None:
                warns.append(f"{sctx} swaps a dairy ingredient with a dairy-free tag (verify intent)")

    for w in warns:
        print(f"WARN: {w}")
    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        print(f"\nFAILED: {len(errors)} error(s), {len(warns)} warning(s)")
        return 1
    total_subs = sum(len(e.get("subs", [])) for e in entries)
    print(f"OK: {len(entries)} entries, {total_subs} substitutes, pack_version {meta.get('pack_version')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
