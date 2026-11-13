#!/usr/bin/env python3
"""One-off: writes quotes/morning.json and quotes/night.json (366 original quotes each) via the Anthropic API."""
import os, json, urllib.request
from pathlib import Path

KEY, MODEL = os.environ["ANTHROPIC_API_KEY"], os.environ.get("QUOTE_MODEL", "claude-sonnet-5-5")
OUT = Path(__file__).resolve().parent.parent / "quotes"
KINDS = {
    "morning": "morning motivation: energising, forward-looking, about starting, discipline, building, courage",
    "night": "night life lesson: reflective, calm, about rest, gratitude, mistakes, relationships, time, perspective",
}
THEMES = ["focus and discipline", "resilience and failure", "learning and curiosity", "people and kindness",
          "time and patience", "craft, building and shipping work"]

def ask(kind, theme, n, avoid):
    prompt = (f"Write {n} original one-sentence quotes (max 140 characters each) for a {KINDS[kind]}. "
              f"Theme focus: {theme}. They must be original (no real quotes, no attribution), plain, concrete, no hashtags, "
              f"no emojis, all different from each other and from these starts: {avoid[-40:]}. "
              "Return ONLY a JSON array of strings.")
    body = json.dumps({"model": MODEL, "max_tokens": 8000, "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", body,
        {"x-api-key": KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    txt = json.load(urllib.request.urlopen(req, timeout=120))["content"][0]["text"]
    return json.loads(txt[txt.index("["): txt.rindex("]") + 1])

for kind in KINDS:
    out, seen, i = [], set(), 0
    while len(out) < 366 and i < 30:
        for q in ask(kind, THEMES[i % len(THEMES)], 70, out):
            k = q.strip().lower()
            if k not in seen and len(q) <= 160:
                seen.add(k); out.append(q.strip())
        i += 1
    (OUT / f"{kind}.json").write_text(json.dumps(out[:366], indent=1, ensure_ascii=False))
    print(kind, len(out[:366]))
