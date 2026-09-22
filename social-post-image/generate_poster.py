"""CLI: generate one social-media ad poster via Nano Banana on Vertex AI.

Normal workflow = exactly ONE API call. Edit is a separate explicit correction
on an existing poster (never chained after generate).

Usage (from repo root):
  .\\.venv\\Scripts\\python.exe social-post-image\\generate_poster.py
  .\\.venv\\Scripts\\python.exe social-post-image\\generate_poster.py --ref path\\to\\a.jpg
  .\\.venv\\Scripts\\python.exe social-post-image\\generate_poster.py --ref product.jpg:product --ref style.jpg:style
  .\\.venv\\Scripts\\python.exe social-post-image\\generate_poster.py --edit --image outputs\\poster.jpg
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DIR = Path(__file__).resolve().parent
ROOT = DIR.parent
if str(DIR) not in sys.path:
    sys.path.insert(0, str(DIR))

from image_client import (  # noqa: E402
    MAX_REFS,
    edit_poster_image,
    generate_poster_image,
    get_settings,
    load_role_reference_parts,
)
from prompt import (  # noqa: E402
    STORE_BRAND_DEFAULT,
    build_edit_prompt,
    build_poster_prompt,
    build_user_prompt_poster,
)

OUT_DIR = DIR / "outputs"
DEFAULT_PROMO = DIR / "promotion.json"
EXAMPLE_PROMO = DIR / "promotion.example.json"
LOCAL_REFS = DIR / "references"
SELECTION_PATH = LOCAL_REFS / "selection.json"
VALID_ROLES = frozenset({"product", "brand", "background", "style", "auto"})
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def resolve_promotion_path(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit
    if DEFAULT_PROMO.exists():
        return DEFAULT_PROMO
    if EXAMPLE_PROMO.exists():
        return EXAMPLE_PROMO
    raise FileNotFoundError(
        f"No promotion file found. Copy {EXAMPLE_PROMO.name} to {DEFAULT_PROMO.name}."
    )


def classify_role_from_name(name: str) -> str:
    n = name.lower()
    if n.startswith("product_") or "/product_" in n:
        return "product"
    if n.startswith("brand_") or "/brand_" in n:
        return "brand"
    if (
        n.startswith("background_")
        or n.startswith("bg_")
        or "/background_" in n
        or "/bg_" in n
    ):
        return "background"
    if n.startswith("style_") or "/style_" in n:
        return "style"
    return "auto"


def parse_ref_token(token: str, *, refs_dir: Path) -> dict[str, Any]:
    """Parse 'path', 'path:role', or 'path=role' into a role_ref dict."""
    raw = token.strip()
    role: str | None = None
    path_str = raw
    for sep in (":", "="):
        if sep in raw:
            # Only split on the last sep so Windows drive letters stay intact
            # when using path:role with relative paths. For "C:\\a.jpg:product"
            # last sep works; for relative "a.jpg:product" also works.
            left, right = raw.rsplit(sep, 1)
            right_l = right.strip().lower()
            if right_l in VALID_ROLES:
                path_str, role = left.strip(), right_l
            break

    path = Path(path_str)
    if not path.is_absolute():
        candidates = [
            ROOT / path,
            refs_dir / path,
            refs_dir / path.name,
            DIR / path,
        ]
        path = next((c for c in candidates if c.exists()), ROOT / path)

    if not path.exists():
        raise FileNotFoundError(f"Reference image not found: {path_str}")

    if role is None:
        role = classify_role_from_name(path.name)

    if role not in VALID_ROLES:
        raise ValueError(f"Invalid role '{role}'. Expected one of: {sorted(VALID_ROLES)}")

    return {"path": path.resolve(), "role": role, "name": path.name}


def load_selection_file(path: Path, *, refs_dir: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("refs") if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise ValueError(f"{path} must contain a 'refs' list")
    out: list[dict[str, Any]] = []
    for item in items:
        if isinstance(item, str):
            out.append(parse_ref_token(item, refs_dir=refs_dir))
            continue
        if not isinstance(item, dict) or "path" not in item:
            raise ValueError(f"Invalid selection entry: {item}")
        role = (item.get("role") or "auto").strip().lower()
        token = f"{item['path']}:{role}" if role in VALID_ROLES else str(item["path"])
        out.append(parse_ref_token(token, refs_dir=refs_dir))
    return out


def resolve_role_refs(
    *,
    cli_refs: list[str] | None,
    refs_dir: Path,
    selection_path: Path = SELECTION_PATH,
    max_refs: int = MAX_REFS,
) -> list[dict[str, Any]]:
    """User-selected refs only. Never auto-dumps the whole folder."""
    if cli_refs:
        role_refs = [parse_ref_token(t, refs_dir=refs_dir) for t in cli_refs]
    else:
        role_refs = load_selection_file(selection_path, refs_dir=refs_dir)

    if len(role_refs) > max_refs:
        raise ValueError(
            f"At most {max_refs} reference images allowed, got {len(role_refs)}. "
            "Remove extras from --ref / selection.json."
        )
    return role_refs


def resolve_existing_image(path: Path) -> Path:
    candidates = [
        path if path.is_absolute() else ROOT / path,
        DIR / path,
        OUT_DIR / path.name,
    ]
    resolved = next((c for c in candidates if c.exists() and c.is_file()), None)
    if resolved is None:
        raise FileNotFoundError(
            f"Image not found: {path}. Pass --image PATH to an existing poster."
        )
    if resolved.suffix.lower() not in IMAGE_EXTS:
        raise ValueError(
            f"Unsupported image type '{resolved.suffix}'. Expected one of: {sorted(IMAGE_EXTS)}"
        )
    return resolved.resolve()


def save_image(data: bytes, stem: str) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    suffix = ".png" if data[:8] == b"\x89PNG\r\n\x1a\n" else ".jpg"
    path = OUT_DIR / f"{stem}{suffix}"
    path.write_bytes(data)
    return path


def save_meta(
    *,
    stem: str,
    promotion: dict,
    prompt: str,
    usage: dict,
    role_refs: list[dict[str, Any]],
    image_path: Path,
    model_text: str,
) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    meta_path = OUT_DIR / f"{stem}_meta.json"
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "image_file": image_path.name,
        "settings": get_settings(),
        "store_brand": promotion.get("store_brand") or STORE_BRAND_DEFAULT,
        "promotion": promotion,
        "references": [
            {"name": r["name"], "role": r["role"], "path": str(r["path"])}
            for r in role_refs
        ],
        "prompt": prompt,
        "model_text": model_text,
        "usage": usage,
    }
    meta_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return meta_path


def run_edit(
    *,
    promotion: dict[str, Any],
    image_path: Path,
    edit_notes: str,
    person_generation: str,
) -> int:
    """Explicit correction only — one edit API call, no generate."""
    settings = get_settings()
    print(f"project={settings['project']}")
    print(f"location={settings['location']}  model={settings['model']}")
    print(f"aspect={settings['aspect_ratio']}  size={settings['image_size']}")
    print(f"store_brand={promotion.get('store_brand')}")
    print(f"mode=edit (single API call)")
    print(f"source image={image_path}")

    image_bytes = image_path.read_bytes()
    mime = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"
    edit_prompt = build_edit_prompt(promotion, fix_notes=edit_notes)

    print("Editing poster…")
    edited, edit_usage, edit_text = edit_poster_image(
        edit_prompt=edit_prompt,
        previous_image=image_bytes,
        previous_mime=mime,
        source="edit_poster",
        person_generation=person_generation,
    )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stem = f"poster_{stamp}_edited"
    out_path = save_image(edited, stem)
    meta_path = save_meta(
        stem=stem,
        promotion=promotion,
        prompt=edit_prompt,
        usage=edit_usage,
        role_refs=[],
        image_path=out_path,
        model_text=edit_text,
    )
    print(f"saved edited image: {out_path}")
    print(f"saved edited meta:  {meta_path}")
    if edit_text:
        print(f"model text: {edit_text[:400]}")
    return 0


def run_generate(
    *,
    promotion: dict[str, Any],
    promo_path: Path,
    role_refs: list[dict[str, Any]],
    person_generation: str,
) -> int:
    """Normal workflow — exactly one generate API call."""
    settings = get_settings()
    print(f"project={settings['project']}")
    print(f"location={settings['location']}  model={settings['model']}")
    print(f"aspect={settings['aspect_ratio']}  size={settings['image_size']}")
    print(f"store_brand={promotion.get('store_brand')}")
    print(f"mode=generate (single API call)")
    print(f"promotion={promo_path}")
    print(f"refs count={len(role_refs)} (max {MAX_REFS})")
    for r in role_refs:
        print(f"  - [{r['role']}] {r['name']}")

    if not role_refs:
        print(
            "No reference images selected — generating from promotion text + "
            f"{STORE_BRAND_DEFAULT} rules only. "
            f"Pass --ref (max {MAX_REFS}) or edit {SELECTION_PATH.name}."
        )

    user_brief = (promotion.get("user_prompt") or "").strip()
    if user_brief:
        print("prompt_source=user_prompt (primary)")
        prompt = build_user_prompt_poster(
            user_brief,
            aspect_ratio=settings["aspect_ratio"],
            role_refs=role_refs,
            store_brand=(promotion.get("store_brand") or STORE_BRAND_DEFAULT),
        )
    else:
        print("prompt_source=structured promotion fields")
        prompt = build_poster_prompt(
            promotion,
            aspect_ratio=settings["aspect_ratio"],
            role_refs=role_refs,
        )
    ref_parts = load_role_reference_parts(role_refs, max_refs=MAX_REFS)

    print("Generating poster…")
    image_bytes, usage, model_text = generate_poster_image(
        prompt=prompt,
        reference_parts=ref_parts,
        source="generate_poster",
        person_generation=person_generation,
    )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stem = f"poster_{stamp}"
    image_path = save_image(image_bytes, stem)
    meta_path = save_meta(
        stem=stem,
        promotion=promotion,
        prompt=prompt,
        usage=usage,
        role_refs=role_refs,
        image_path=image_path,
        model_text=model_text,
    )
    print(f"saved image: {image_path}")
    print(f"saved meta:  {meta_path}")
    if model_text:
        print(f"model text: {model_text[:400]}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate an AMPM Woodstock social-media ad poster in ONE API call "
            "(0–3 user-selected reference images). "
            "Use --edit --image for a separate correction pass."
        )
    )
    parser.add_argument(
        "--promotion",
        type=Path,
        default=None,
        help="Path to promotion.json (default: social-post-image/promotion.json)",
    )
    parser.add_argument(
        "--refs-dir",
        type=Path,
        default=LOCAL_REFS,
        help="Folder used to resolve relative --ref / selection paths",
    )
    parser.add_argument(
        "--ref",
        dest="ref_tokens",
        action="append",
        default=None,
        help=(
            "Reference image (repeatable, max 3). "
            "Forms: path  |  path:role  |  path=role  "
            f"Roles: {', '.join(sorted(VALID_ROLES))}"
        ),
    )
    parser.add_argument(
        "--selection",
        type=Path,
        default=SELECTION_PATH,
        help="JSON selection file used when --ref is omitted",
    )
    parser.add_argument(
        "--edit",
        action="store_true",
        help=(
            "Explicit correction mode: edit an existing poster only "
            "(requires --image). Does NOT generate first."
        ),
    )
    parser.add_argument(
        "--image",
        type=Path,
        default=None,
        help="Existing poster to correct (required with --edit)",
    )
    parser.add_argument(
        "--edit-notes",
        type=str,
        default="",
        help="Optional extra notes for --edit",
    )
    parser.add_argument(
        "--allow-people",
        action="store_true",
        help="Allow people in the image (default: ALLOW_NONE)",
    )
    args = parser.parse_args()

    if args.edit and args.image is None:
        parser.error(
            "--edit requires --image PATH to an existing poster. "
            "Normal generate is a single API call; edit is a separate correction."
        )
    if args.image is not None and not args.edit:
        parser.error("--image is only valid with --edit")

    promo_path = resolve_promotion_path(args.promotion)
    promotion = json.loads(promo_path.read_text(encoding="utf-8"))
    if not (promotion.get("store_brand") or "").strip():
        promotion["store_brand"] = STORE_BRAND_DEFAULT

    person = "ALLOW_ADULT" if args.allow_people else "ALLOW_NONE"

    if args.edit:
        image_path = resolve_existing_image(args.image)
        return run_edit(
            promotion=promotion,
            image_path=image_path,
            edit_notes=args.edit_notes,
            person_generation=person,
        )

    refs_dir = args.refs_dir if args.refs_dir.is_absolute() else (ROOT / args.refs_dir)
    if not refs_dir.exists():
        refs_dir = LOCAL_REFS

    role_refs = resolve_role_refs(
        cli_refs=args.ref_tokens,
        refs_dir=refs_dir,
        selection_path=args.selection,
        max_refs=MAX_REFS,
    )
    return run_generate(
        promotion=promotion,
        promo_path=promo_path,
        role_refs=role_refs,
        person_generation=person,
    )


if __name__ == "__main__":
    raise SystemExit(main())
