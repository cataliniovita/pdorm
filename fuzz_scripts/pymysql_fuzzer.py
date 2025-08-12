#!/usr/bin/env python3
import argparse
import json
import sys
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path


def http_get(url: str):
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=15) as resp:
            code = resp.getcode()
            body = resp.read()
            return code, body
    except urllib.error.HTTPError as e:
        try:
            body = e.read()
        except Exception:
            body = b""
        return e.code, body
    except Exception as e:
        # Network/timeout error; use 0 status
        return 0, (str(e)).encode()


def fuzz(base: str, endpoint: str, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    ndjson_path = out_dir / "fuzz-pymysql.ndjson"
    json_path = out_dir / "fuzz-pymysql.json"
    md_path = out_dir / "fuzz-pymysql.md"

    entries = []
    with ndjson_path.open("w", encoding="utf-8") as nd:
        for b in range(0, 256):
            hex_byte = f"{b:02X}"
            for variant in ("raw", "suffix"):
                if variant == "raw":
                    qs = {"col": f"%{hex_byte}", "name": "apple"}
                else:
                    qs = {"col": f"name%{hex_byte}", "name": "apple"}
                # We want literal %XX in query, so build manually
                query = f"col={qs['col']}&name={urllib.parse.quote(qs['name'])}"
                url = f"http://{base}{endpoint}?{query}"
                code, body = http_get(url)
                record = {
                    "hex": hex_byte,
                    "variant": variant,
                    "http_code": code,
                    "body": body.decode(errors="replace"),
                }
                nd.write(json.dumps(record, ensure_ascii=False) + "\n")
                entries.append(record)

    # Write JSON array
    with json_path.open("w", encoding="utf-8") as jf:
        json.dump(entries, jf, ensure_ascii=False, indent=2)

    # Write a simple markdown summary
    def dist(variant_name: str):
        counts = {}
        for r in entries:
            if r["variant"] != variant_name:
                continue
            counts[r["http_code"]] = counts.get(r["http_code"], 0) + 1
        lines = []
        for code in sorted(counts.keys()):
            lines.append(f"- {code}: {counts[code]}")
        return "\n".join(lines)

    with md_path.open("w", encoding="utf-8") as md:
        md.write("# PyMySQL fuzz summary\n\n")
        md.write(f"- Target: http://{base}{endpoint}\n")
        md.write("- Cases: 512 (256 bytes x 2 variants)\n\n")
        md.write("## HTTP code distribution (raw)\n")
        md.write(dist("raw") + "\n\n")
        md.write("## HTTP code distribution (suffix)\n")
        md.write(dist("suffix") + "\n")

    print(f"Wrote: {ndjson_path}, {json_path}, {md_path}")


def main():
    parser = argparse.ArgumentParser(description="Fuzz PyMySQL vuln endpoint with bytes 0x00..0xFF")
    parser.add_argument("--base", default="python-mysql-connector:5000", help="host:port inside Docker network")
    parser.add_argument("--endpoint", default="/vuln", help="endpoint path")
    parser.add_argument("--out-dir", default="/workspace/out", help="output directory path")
    args = parser.parse_args()

    fuzz(args.base, args.endpoint, Path(args.out_dir))


if __name__ == "__main__":
    main()


