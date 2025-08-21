# Assetnote-style parser fuzzer

`assetnote_fuzzer.py` runs crafted identifier payloads (e.g., `?%00`, `?#%00`) against each service `/vuln` endpoint to surface client-side parsing/binding issues (like PDO emulation) and identifier interpolation flaws.

## Run (inside attacker container)
- Internal (container network; uses service names + container ports):
```bash
docker compose run --rm attacker \
  python /workspace/fuzz_scripts/assetnote_fuzzer.py
```
- Host (host-exposed ports from docker-compose):
```bash
docker compose run --rm attacker \
  python /workspace/fuzz_scripts/assetnote_fuzzer.py --ports host
```

Outputs are written to the repo root (mounted as `/workspace/out`):
- `assetnote-fuzz.ndjson` — line-delimited records per request
- `assetnote-fuzz.json` — full JSON array of results
- `assetnote-fuzz.md` — short summary per service

## Options
```text
--ports {internal|host}   Select container-internal or host-exposed ports (default: internal)
--out-dir PATH            Output directory (default: /workspace/out)
```

## What it flags
- HTTP ≥ 400 or common binding/syntax error patterns on `/vuln` for non-benign payloads
- Note: “no_indicator” does not prove safety; it only means no obvious error signal was observed.

## Tips
- Use `docker compose logs -f attacker` to watch progress.
- For host mode, ensure compose is started with ports published (default compose.yml already exposes localhost ports).
- Extend payloads or detection heuristics in `assetnote_fuzzer.py` to fit new stacks.
