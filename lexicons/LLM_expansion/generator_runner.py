"""
Theory-driven lexicon generation runner (LLM-as-Lexicographer).

Compatible with both GPT-4 family (gpt-4o-mini etc.) and GPT-5 family
(gpt-5.4-mini, gpt-5.5 etc.). The runner auto-detects which token-limit
parameter the model expects:
    - GPT-5.x and reasoning models  -> max_completion_tokens
    - GPT-4.x and earlier           -> max_tokens

For each (category, slice) pair, calls the LLM with a strict-JSON
generation prompt, validates the output, and streams every generated
item to a JSONL file.

Usage
-----
    export OPENAI_API_KEY=sk-...
    export OPENAI_BASE_URL=https://us.api.openai.com/v1   # if you're on UMD enterprise

    python generator_runner.py \\
        --theory theory_definitions.json \\
        --output gen_smoke.jsonl \\
        --only-categories "LOGIC_CAUSAL,IMPACT_GAIN" \\
        --model gpt-5.4-mini-2026-03-17 \\
        --concurrency 6 --yes

Resume
------
The runner is resumable. On startup it scans the output JSONL and skips
any (category, slice) pair already completed successfully. Pairs that
previously failed are automatically retried.
"""
import argparse
import asyncio
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Literal, Optional, Tuple

from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError, BadRequestError
from pydantic import BaseModel, Field, ValidationError, field_validator
from tqdm.asyncio import tqdm_asyncio

from generation_prompts import (
    SLICE_SPECS,
    all_slice_names,
    build_messages,
    is_hard_negative_slice,
)


# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------
RegisterLiteral = Literal["formal", "colloquial", "domain", "archaic", "neutral"]
TypeLiteral = Literal["single", "phrase", "inflection", "antonym", "boundary"]
ConfidenceLiteral = Literal["high", "medium", "low"]


class GeneratedItem(BaseModel):
    word: str = Field(min_length=1, max_length=80)
    register: RegisterLiteral
    type: TypeLiteral
    confidence: ConfidenceLiteral
    rationale: str = Field(min_length=1, max_length=500)

    @field_validator("word")
    @classmethod
    def strip_word(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Empty word after strip")
        return v


class SliceOutput(BaseModel):
    items: List[GeneratedItem]


# ---------------------------------------------------------------------------
# Model-family detection
# ---------------------------------------------------------------------------
# Models that require max_completion_tokens (GPT-5 family + o-series reasoning).
_NEW_TOKEN_PARAM_PATTERNS = (
    re.compile(r"^gpt-5"),
    re.compile(r"^o1"),
    re.compile(r"^o3"),
    re.compile(r"^o4"),
)

def model_uses_new_token_param(model: str) -> bool:
    return any(p.match(model) for p in _NEW_TOKEN_PARAM_PATTERNS)


def model_supports_temperature(model: str) -> bool:
    """GPT-5 reasoning models reject temperature != 1.0 / sometimes the field
    altogether. Detect and skip the parameter."""
    return not any(p.match(model) for p in _NEW_TOKEN_PARAM_PATTERNS)


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------
def slice_key(category: str, slice_name: str) -> str:
    return f"{category}\t{slice_name}"


def load_done_slices(path: Path) -> set:
    """A (category, slice) pair is 'done' if a slice_ok meta record exists.
    slice_failed records do NOT mark the pair as done — they are retried."""
    seen_ok = set()
    if not path.exists():
        return seen_ok
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("_meta_status") == "slice_ok":
                seen_ok.add(slice_key(rec.get("category", ""), rec.get("slice", "")))
    return seen_ok


# ---------------------------------------------------------------------------
# Build kwargs for chat.completions.create — model-aware
# ---------------------------------------------------------------------------
def build_request_kwargs(model: str, system_msg: str, user_msg: str,
                         max_output_tokens: int, timeout: float) -> Dict:
    kwargs: Dict = {
        "model": model,
        "timeout": timeout,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
    }
    if model_uses_new_token_param(model):
        kwargs["max_completion_tokens"] = max_output_tokens
        # GPT-5 reasoning models: do not set temperature
        # (default of 1.0 is the only supported value in many cases)
    else:
        kwargs["max_tokens"] = max_output_tokens
        kwargs["temperature"] = 0.4   # diversity for generation
    return kwargs


# ---------------------------------------------------------------------------
# Single-slice call with retry
# ---------------------------------------------------------------------------
async def generate_slice(
    client: AsyncOpenAI,
    semaphore: asyncio.Semaphore,
    category: str,
    theory_def: Dict,
    slice_name: str,
    model: str,
    max_retries: int = 4,
    timeout: float = 120.0,
    max_output_tokens: int = 4000,
) -> Tuple[str, List[Dict]]:
    """Returns (status, records). status in {"ok", "failed"}.

    On success: records is per-item dicts plus one slice_ok meta at end.
    On failure: records is exactly one slice_failed meta with the error.
    """
    system_msg, user_msg = build_messages(category, theory_def, slice_name)
    is_hn = is_hard_negative_slice(slice_name)

    # GPT-5 reasoning models often consume a chunk of completion-token
    # budget on internal reasoning before producing visible output.
    # Bump the budget if we're on such a model.
    effective_max = max_output_tokens
    if model_uses_new_token_param(model):
        effective_max = max(max_output_tokens, 8000)

    last_err = None
    async with semaphore:
        for attempt in range(max_retries):
            try:
                kwargs = build_request_kwargs(
                    model=model,
                    system_msg=system_msg,
                    user_msg=user_msg,
                    max_output_tokens=effective_max,
                    timeout=timeout,
                )
                resp = await client.chat.completions.create(**kwargs)
                raw = resp.choices[0].message.content
                if raw is None:
                    raise ValueError("Empty response content (likely truncated by token limit)")

                raw_clean = raw.strip()
                if raw_clean.startswith("```"):
                    raw_clean = raw_clean.strip("`")
                    if raw_clean.lower().startswith("json"):
                        raw_clean = raw_clean[4:].strip()

                parsed = SliceOutput.model_validate_json(raw_clean)

                records = []
                for item in parsed.items:
                    records.append({
                        "category": category,
                        "slice": slice_name,
                        "word": item.word,
                        "register": item.register,
                        "type": item.type,
                        "confidence": item.confidence,
                        "rationale": item.rationale,
                        "is_hard_negative": is_hn,
                        "model": model,
                    })
                records.append({
                    "_meta_status": "slice_ok",
                    "category": category,
                    "slice": slice_name,
                    "n_items": len(parsed.items),
                    "model": model,
                })
                return "ok", records

            except BadRequestError as e:
                # Specific 400s — usually parameter incompatibility.
                # Don't retry; surface immediately so user sees the cause.
                last_err = f"bad_request: {e}"
                break
            except (json.JSONDecodeError, ValidationError, ValueError) as e:
                last_err = f"parse_error: {type(e).__name__}: {e}"
                await asyncio.sleep(0.5 * (attempt + 1))
            except (RateLimitError, APITimeoutError) as e:
                last_err = f"rate_or_timeout: {type(e).__name__}: {e}"
                await asyncio.sleep(min(60, 2 ** attempt))
            except APIError as e:
                last_err = f"api_error: {type(e).__name__}: {e}"
                await asyncio.sleep(min(30, 2 ** attempt))
            except Exception as e:
                last_err = f"unexpected: {type(e).__name__}: {e}"
                await asyncio.sleep(min(15, 2 ** attempt))

    return "failed", [{
        "_meta_status": "slice_failed",
        "category": category,
        "slice": slice_name,
        "error": last_err or "max_retries_exhausted",
        "model": model,
    }]


# ---------------------------------------------------------------------------
# Pre-flight check — cheap one-call test before launching N×9 calls
# ---------------------------------------------------------------------------
async def preflight(client: AsyncOpenAI, model: str) -> Optional[str]:
    """Returns None on success, error string on failure."""
    try:
        kwargs = build_request_kwargs(
            model=model,
            system_msg="You return strict JSON.",
            user_msg='Return exactly: {"items":[{"word":"ok","register":"neutral",'
                     '"type":"single","confidence":"high","rationale":"preflight ok"}]}',
            max_output_tokens=2000,
            timeout=30.0,
        )
        resp = await client.chat.completions.create(**kwargs)
        if not resp.choices[0].message.content:
            return "preflight: empty response"
        return None
    except BadRequestError as e:
        return f"preflight bad_request: {e}"
    except Exception as e:
        return f"preflight {type(e).__name__}: {e}"


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------
async def run(args: argparse.Namespace) -> None:
    theory = json.loads(Path(args.theory).read_text(encoding="utf-8"))

    cats = sorted(theory.keys())
    if args.only_categories:
        wanted = [c.strip() for c in args.only_categories.split(",") if c.strip()]
        missing = [c for c in wanted if c not in theory]
        if missing:
            raise SystemExit(f"Unknown categories: {missing}")
        cats = wanted

    slices = all_slice_names()
    if args.only_slices:
        wanted_s = [s.strip() for s in args.only_slices.split(",") if s.strip()]
        missing_s = [s for s in wanted_s if s not in SLICE_SPECS]
        if missing_s:
            raise SystemExit(f"Unknown slices: {missing_s}")
        slices = wanted_s

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = load_done_slices(out_path)

    todo: List[Tuple[str, str]] = [
        (c, s) for c in cats for s in slices
        if slice_key(c, s) not in done
    ]

    print(f"[runner] base_url:          {os.environ.get('OPENAI_BASE_URL', '<default>')}")
    print(f"[runner] model:             {args.model}")
    print(f"[runner] token-param:       {'max_completion_tokens' if model_uses_new_token_param(args.model) else 'max_tokens'}")
    print(f"[runner] temperature:       {'(omitted; reasoning model)' if not model_supports_temperature(args.model) else '0.4'}")
    print(f"[runner] categories:        {len(cats)}")
    print(f"[runner] slices/category:   {len(slices)}")
    print(f"[runner] total slice calls: {len(cats) * len(slices)}")
    print(f"[runner] already done:      {len(done)}")
    print(f"[runner] to process:        {len(todo)}")
    print(f"[runner] concurrency:       {args.concurrency}")
    print(f"[runner] output:            {out_path}")

    if not todo:
        print("[runner] nothing to do.")
        return

    client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    # Preflight: catch param mismatches BEFORE launching N tasks.
    if not args.skip_preflight:
        print("[runner] running preflight check...")
        err = await preflight(client, args.model)
        if err:
            print(f"[runner] PREFLIGHT FAILED: {err}", file=sys.stderr)
            print(f"[runner] aborting — fix the model/endpoint and retry.", file=sys.stderr)
            return
        print("[runner] preflight ok")

    if not args.yes:
        ans = input("Proceed? [y/N] ").strip().lower()
        if ans != "y":
            print("[runner] aborted.")
            return

    semaphore = asyncio.Semaphore(args.concurrency)

    started = time.time()
    n_slice_ok, n_slice_fail, n_items = 0, 0, 0

    with out_path.open("a", encoding="utf-8") as f_out:
        chunk = args.flush_every
        for i in range(0, len(todo), chunk):
            batch = todo[i:i + chunk]
            tasks = [
                generate_slice(
                    client, semaphore, category, theory[category], slice_name,
                    model=args.model, max_retries=args.max_retries,
                )
                for (category, slice_name) in batch
            ]
            results = await tqdm_asyncio.gather(
                *tasks,
                desc=f"batch {i // chunk + 1}/{(len(todo) + chunk - 1) // chunk}",
                total=len(tasks),
            )
            for status, records in results:
                for rec in records:
                    f_out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                if status == "ok":
                    n_slice_ok += 1
                    n_items += sum(1 for r in records if "_meta_status" not in r)
                else:
                    n_slice_fail += 1
            f_out.flush()

    elapsed = time.time() - started
    print(f"\n[runner] done. slices_ok={n_slice_ok} slices_failed={n_slice_fail} "
          f"items_generated={n_items} elapsed={elapsed:.1f}s")
    print(f"[runner] output: {out_path}")


def main() -> None:
    p = argparse.ArgumentParser(description="Theory-driven lexicon generation runner.")
    p.add_argument("--theory", default="theory_definitions.json")
    p.add_argument("--output", required=True, help="Output JSONL path (resumable)")
    p.add_argument("--model", default="gpt-5.4-mini-2026-03-17",
                   help="OpenAI model id; auto-detects max_tokens vs "
                        "max_completion_tokens based on model name")
    p.add_argument("--concurrency", type=int, default=8)
    p.add_argument("--max-retries", type=int, default=4)
    p.add_argument("--flush-every", type=int, default=50)
    p.add_argument("--only-categories", default=None,
                   help="Comma-separated category list "
                        "(e.g. 'LOGIC_CAUSAL,IMPACT_GAIN')")
    p.add_argument("--only-slices", default=None,
                   help="Comma-separated slice list")
    p.add_argument("--skip-preflight", action="store_true",
                   help="Skip the 1-call sanity check")
    p.add_argument("--yes", action="store_true",
                   help="Skip the cost-estimate confirmation prompt")
    args = p.parse_args()

    if "OPENAI_API_KEY" not in os.environ:
        print("ERROR: OPENAI_API_KEY env var not set.", file=sys.stderr)
        sys.exit(1)

    asyncio.run(run(args))


if __name__ == "__main__":
    main()