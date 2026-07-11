#!/usr/bin/env python3
"""
github_stats.py

Fetches this account's public contribution history via the GitHub GraphQL
API (across every year since account creation) and renders a small stats
card -- total contributions, current streak, longest streak -- as an SVG,
styled to match the rest of the profile.

Regenerated daily via GitHub Actions. Self-hosted so it isn't at the mercy
of a third-party badge service's caching.

Requires a token with `read:user` scope in the GH_STATS_TOKEN env var --
the default Actions GITHUB_TOKEN does not have access to
`contributionsCollection`.
"""
import os
import sys
import json
import datetime
import urllib.request
import urllib.error

USERNAME = "Urvish-Kosta"
API_URL = "https://api.github.com/graphql"


def gql(token, query, variables=None):
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "github-stats-card",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode())
    if "errors" in payload:
        raise RuntimeError(f"GraphQL error: {payload['errors']}")
    return payload


def fetch_created_at(token):
    q = """
    query($login: String!) {
      user(login: $login) { createdAt }
    }
    """
    data = gql(token, q, {"login": USERNAME})
    return data["data"]["user"]["createdAt"]


def fetch_year_days(token, frm, to):
    q = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            weeks {
              contributionDays { date contributionCount }
            }
          }
        }
      }
    }
    """
    data = gql(token, q, {"login": USERNAME, "from": frm, "to": to})
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = {}
    for wk in cal["weeks"]:
        for d in wk["contributionDays"]:
            days[d["date"]] = d["contributionCount"]
    return days


def collect_all_days(token):
    created = fetch_created_at(token)
    start_year = int(created[:4])
    today = datetime.date.today()
    all_days = {}
    for year in range(start_year, today.year + 1):
        frm = datetime.datetime(year, 1, 1).isoformat() + "Z"
        if year == today.year:
            to = datetime.datetime.combine(today, datetime.time(23, 59, 59)).isoformat() + "Z"
        else:
            to = datetime.datetime(year, 12, 31, 23, 59, 59).isoformat() + "Z"
        all_days.update(fetch_year_days(token, frm, to))
    return all_days


def compute_stats(days):
    total = sum(days.values())
    dates_sorted = sorted(days.keys())
    today = datetime.date.today()

    current = 0
    cursor = today
    if days.get(today.isoformat(), 0) == 0:
        cursor = today - datetime.timedelta(days=1)
    while True:
        key = cursor.isoformat()
        if days.get(key, 0) > 0:
            current += 1
            cursor -= datetime.timedelta(days=1)
        else:
            break

    longest = 0
    run = 0
    for d in dates_sorted:
        if days[d] > 0:
            run += 1
            longest = max(longest, run)
        else:
            run = 0

    return total, current, longest


def make_svg(total, current, longest, updated):
    W, H = 700, 130
    p = []
    p.append(
        f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'xmlns="http://www.w3.org/2000/svg" font-family="\'Fira Code\',monospace">'
    )
    p.append(f'<rect x="0" y="0" width="{W}" height="{H}" rx="6" fill="#0d1117" stroke="#30363d" stroke-width="1"/>')
    p.append(f'<line x1="{W/3:.0f}" y1="18" x2="{W/3:.0f}" y2="{H-18}" stroke="#30363d" stroke-width="1"/>')
    p.append(f'<line x1="{2*W/3:.0f}" y1="18" x2="{2*W/3:.0f}" y2="{H-18}" stroke="#30363d" stroke-width="1"/>')

    cols = [
        (W / 6, str(total), "TOTAL CONTRIBUTIONS", "#58a6ff"),
        (W / 2, str(current), "CURRENT STREAK", "#d29922"),
        (5 * W / 6, str(longest), "LONGEST STREAK", "#3fb950"),
    ]
    for cx, value, label, color in cols:
        p.append(f'<text x="{cx:.0f}" y="58" text-anchor="middle" font-size="36" font-weight="700" fill="{color}">{value}</text>')
        p.append(f'<text x="{cx:.0f}" y="82" text-anchor="middle" font-size="10" letter-spacing="1.5" fill="#8b949e">{label}</text>')

    p.append(
        f'<text x="{W/2:.0f}" y="{H-14}" text-anchor="middle" font-size="9" fill="#484f58">'
        f'updated {updated} UTC &#183; self-hosted, regenerated daily</text>'
    )
    p.append('</svg>')
    return "\n".join(p)


if __name__ == "__main__":
    token = os.environ.get("GH_STATS_TOKEN")
    if not token:
        print(
            "GH_STATS_TOKEN is not set. Create a PAT with 'read:user' scope and "
            "add it as a repo secret named GH_STATS_TOKEN.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        days = collect_all_days(token)
    except urllib.error.HTTPError as e:
        print(f"GitHub API request failed: {e.code} {e.reason}", file=sys.stderr)
        sys.exit(1)

    total, current, longest = compute_stats(days)
    updated = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    svg = make_svg(total, current, longest, updated)
    with open("assets/github-stats.svg", "w") as f:
        f.write(svg)
    print(f"generated assets/github-stats.svg (total={total}, current={current}, longest={longest})")
