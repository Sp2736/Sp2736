#!/usr/bin/env python3
"""Refreshes README sections: quote, projects (+gh-pages deploys), masteryOS usage, github stats SVGs."""
import os, json, re, time, datetime as dt, urllib.request, urllib.error
from pathlib import Path
from xml.sax.saxutils import escape as esc

USER = os.environ.get("GH_USER", "Sp2736")
TOKEN = os.environ.get("GH_TOKEN", "")
ROOT = Path(__file__).resolve().parent.parent
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
BG, BORDER, TEXT, MUTED, ACC = "#0d1117", "#30363d", "#c9d1d9", "#8b949e", "#58a6ff"
FONT = "Segoe UI,Ubuntu,Helvetica,Arial,sans-serif"

# ---------- http ----------
def http(url, payload=None, headers=None):
    h = {"User-Agent": "profile-readme", "Accept": "application/vnd.github+json"}
    if TOKEN and "api.github.com" in url:
        h["Authorization"] = f"Bearer {TOKEN}"
    h.update(headers or {})
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=h)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

# ---------- github data ----------
QUERY = """query($login:String!){user(login:$login){
 contributionsCollection{totalCommitContributions totalPullRequestContributions totalIssueContributions
  contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}
 repositoriesContributedTo(first:1,contributionTypes:[COMMIT,PULL_REQUEST,ISSUE,REPOSITORY]){totalCount}
 repositories(first:100,ownerAffiliations:OWNER,isFork:false,orderBy:{field:PUSHED_AT,direction:DESC}){nodes{
  name stargazerCount isPrivate languages(first:8,orderBy:{field:SIZE,direction:DESC}){edges{size node{name color}}}}}}}"""

def fetch_github():
    res = http("https://api.github.com/graphql", {"query": QUERY, "variables": {"login": USER}})
    u = res["data"]["user"]
    cc = u["contributionsCollection"]
    days = [(d["date"], d["contributionCount"])
            for w in cc["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    langs = {}
    for r in u["repositories"]["nodes"]:
        for e in r["languages"]["edges"]:
            n = e["node"]["name"]
            size, color = langs.get(n, (0, e["node"]["color"] or MUTED))
            langs[n] = (size + e["size"], color)
    return {
        "stars": sum(r["stargazerCount"] for r in u["repositories"]["nodes"]),
        "commits": cc["totalCommitContributions"], "prs": cc["totalPullRequestContributions"],
        "issues": cc["totalIssueContributions"], "contrib": u["repositoriesContributedTo"]["totalCount"],
        "total": cc["contributionCalendar"]["totalContributions"], "days": days, "langs": langs,
        "repos": [r["name"] for r in u["repositories"]["nodes"] if not r["isPrivate"]],
    }

def fetch_deploys(repos):
    """last gh-pages commit date per repo = last successful gh-pages deployment"""
    out = {}
    for n in repos:
        try:
            b = http(f"https://api.github.com/repos/{USER}/{n}/branches/gh-pages")
            out[n] = b["commit"]["commit"]["committer"]["date"][:10]
        except urllib.error.HTTPError:
            pass
    return out

def fetch_mastery():
    url = os.environ.get("MASTERYOS_STATS_URL")
    if not url:
        return None
    h = {}
    if os.environ.get("MASTERYOS_STATS_TOKEN"):
        h["Authorization"] = "Bearer " + os.environ["MASTERYOS_STATS_TOKEN"]
    try:
        return http(url, headers=h)
    except Exception as e:
        print("masteryOS fetch failed:", e)
        return None

# ---------- svg ----------
def card(w, h, inner):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<style>text{{font-family:{FONT}}}</style>'
            f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="6" fill="{BG}" stroke="{BORDER}"/>{inner}</svg>')

def t(x, y, s, size=14, fill=TEXT, weight=400, anchor="start"):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}">{esc(str(s))}</text>'

def stats_svg(d):
    rows = [("Total Stars", d["stars"]), ("Commits (past year)", d["commits"]), ("PRs (past year)", d["prs"]),
            ("Issues (past year)", d["issues"]), ("Contributed to", d["contrib"])]
    s = t(25, 36, f"{USER}'s GitHub Stats", 18, TEXT, 600)
    for i, (k, v) in enumerate(rows):
        y = 70 + i * 26
        s += f'<circle cx="31" cy="{y-5}" r="3" fill="{ACC}"/>' + t(44, y, k, 13, MUTED) + t(215, y, v, 13, TEXT, 600)
    frac = min(d["total"] / 1500, 1)
    r, c = 38, 2 * 3.14159 * 38
    s += (f'<circle cx="355" cy="105" r="{r}" fill="none" stroke="{BORDER}" stroke-width="7"/>'
          f'<circle cx="355" cy="105" r="{r}" fill="none" stroke="{ACC}" stroke-width="7" stroke-linecap="round" '
          f'stroke-dasharray="{c*frac:.1f} {c:.1f}" transform="rotate(-90 355 105)"/>')
    s += t(355, 110, d["total"], 17, TEXT, 700, "middle") + t(355, 163, "contributions / yr", 11, MUTED, 400, "middle")
    return card(430, 195, s)

def langs_svg(langs):
    items = sorted(langs.items(), key=lambda kv: -kv[1][0])[:6]
    total = sum(v[0] for _, v in items) or 1
    s = t(25, 36, "Most Used Languages", 18, TEXT, 600)
    x = 25
    s += '<clipPath id="b"><rect x="25" y="52" width="250" height="9" rx="4.5"/></clipPath><g clip-path="url(#b)">'
    for n, (sz, col) in items:
        w = 250 * sz / total
        s += f'<rect x="{x:.1f}" y="52" width="{w:.1f}" height="9" fill="{col}"/>'
        x += w
    s += "</g>"
    for i, (n, (sz, col)) in enumerate(items):
        cx, cy = 25 + (i % 2) * 130, 90 + (i // 2) * 27
        s += f'<circle cx="{cx+4}" cy="{cy-4}" r="4.5" fill="{col}"/>' + t(cx + 15, cy, f"{n} {100*sz/total:.1f}%", 11.5, MUTED)
    return card(300, 195, s)

def activity_svg(days):
    pts = days[-30:]
    W, H, L, R, T, B = 900, 300, 55, 25, 55, 45
    mx = max([c for _, c in pts] + [1])
    top = max(4, ((mx + 3) // 4) * 4)
    X = lambda i: L + (W - L - R) * i / max(len(pts) - 1, 1)
    Y = lambda v: T + (H - T - B) * (1 - v / top)
    s = t(W / 2, 30, "contribution activity (last 30 days)", 15, ACC, 600, "middle")
    for k in range(5):
        v = top * k / 4
        s += f'<line x1="{L}" x2="{W-R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="{BORDER}" stroke-dasharray="3 4"/>' + t(L - 10, Y(v) + 4, int(v), 11, MUTED, 400, "end")
    line = " ".join(f"{X(i):.1f},{Y(c):.1f}" for i, (_, c) in enumerate(pts))
    s += (f'<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{ACC}" stop-opacity=".35"/>'
          f'<stop offset="1" stop-color="{ACC}" stop-opacity="0"/></linearGradient></defs>'
          f'<polygon points="{X(0):.1f},{Y(0):.1f} {line} {X(len(pts)-1):.1f},{Y(0):.1f}" fill="url(#g)"/>'
          f'<polyline points="{line}" fill="none" stroke="{ACC}" stroke-width="2"/>')
    for i, (d, c) in enumerate(pts):
        s += f'<circle cx="{X(i):.1f}" cy="{Y(c):.1f}" r="3" fill="{BG}" stroke="{ACC}" stroke-width="1.5"/>'
        if i % 2 == 0:
            s += t(X(i), H - B + 20, d[8:], 11, MUTED, 400, "middle")
    return card(W, H, s)

def mastery_svg(m):
    W, H = 900, 230
    s = t(25, 34, (m or {}).get("title", "masteryOS utilisation"), 17, TEXT, 600)
    if not m:
        s += t(W / 2, 120, "masteryOS stats not connected yet - set MASTERYOS_STATS_URL", 14, MUTED, 400, "middle")
        return card(W, H, s)
    ms = m.get("metrics", [])[:5]
    for i, it in enumerate(ms):
        cx = 25 + (W - 50) * (i + .5) / max(len(ms), 1)
        s += t(cx, 82, it["value"], 26, ACC, 700, "middle") + t(cx, 102, it["label"], 12, MUTED, 400, "middle")
    ser = (m.get("series") or {}).get("points", [])[-30:]
    if len(ser) > 1:
        mx = max(p["value"] for p in ser) or 1
        X = lambda i: 40 + (W - 80) * i / (len(ser) - 1)
        Y = lambda v: 200 - 70 * v / mx
        line = " ".join(f"{X(i):.1f},{Y(p['value']):.1f}" for i, p in enumerate(ser))
        s += (f'<polygon points="40,200 {line} {W-40},200" fill="{ACC}" fill-opacity=".15"/>'
              f'<polyline points="{line}" fill="none" stroke="{ACC}" stroke-width="2"/>'
              + t(40, 220, (m["series"].get("label") or "") + " - last 30 days", 11, MUTED))
    return card(W, H, s)

# ---------- readme blocks ----------
def replace_block(text, name, body):
    pat = re.compile(rf"<!--{name}_START-->.*?<!--{name}_END-->", re.S)
    return pat.sub(lambda _: f"<!--{name}_START-->\n{body}\n<!--{name}_END-->", text)

def load(name, fallback):
    p = ROOT / "quotes" / name
    try:
        q = json.loads(p.read_text())
        return q if q else fallback
    except Exception:
        return fallback

def quote_md(now=None):
    now = now or dt.datetime.now(IST)
    morning = 6 <= now.hour < 18
    doy = (now - dt.timedelta(hours=6)).timetuple().tm_yday
    if morning:
        q, label = load("morning.json", ["Start before you feel ready."]), "morning"
    else:
        q, label = load("night.json", ["Rest is part of the work."]), "night"
    return f"> **{label}** - {q[(doy - 1) % len(q)]}"

def projects_md(deploys):
    cfg = json.loads((ROOT / "config" / "projects.json").read_text())
    lines, known = [], set()
    for p in cfg:
        repo = p.get("repo")
        known.add(repo)
        line = f"- **[{p['name']}]({p['url']})**"
        dep = deploys.get(repo)
        if p.get("demo") or dep:
            line += f" · [demo](https://{USER.lower()}.github.io/{repo})"
        if dep:
            line += f" <sub>deployed {dep}</sub>"
        lines.append(line)
    for repo, dep in sorted(deploys.items(), key=lambda kv: kv[1], reverse=True):
        if repo not in known and repo.lower() != USER.lower():
            lines.append(f"- **[{repo}](https://github.com/{USER}/{repo})** · [demo](https://{USER.lower()}.github.io/{repo}) <sub>deployed {dep}</sub>")
    return "\n".join(lines)

def main():
    gh = fetch_github()
    deploys = fetch_deploys(gh["repos"])
    v = int(time.time())
    (ROOT / "assets").mkdir(exist_ok=True)
    (ROOT / "assets" / "stats.svg").write_text(stats_svg(gh))
    (ROOT / "assets" / "langs.svg").write_text(langs_svg(gh["langs"]))
    (ROOT / "assets" / "activity.svg").write_text(activity_svg(gh["days"]))
    (ROOT / "assets" / "masteryos.svg").write_text(mastery_svg(fetch_mastery()))
    r = (ROOT / "README.md").read_text()
    r = replace_block(r, "QUOTE", quote_md())
    r = replace_block(r, "PROJECTS", projects_md(deploys))
    r = replace_block(r, "MASTERY", f'<p align="center"><img src="assets/masteryos.svg?v={v}" width="100%" /></p>')
    r = replace_block(r, "STATS",
        f'<p align="center"><img src="assets/stats.svg?v={v}" height="195" /> <img src="assets/langs.svg?v={v}" height="195" /></p>\n'
        f'<p align="center"><img src="assets/activity.svg?v={v}" width="100%" /></p>')
    (ROOT / "README.md").write_text(r)

if __name__ == "__main__":
    main()
