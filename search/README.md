# GitHub code search helper

`search_github.py` is a small CLI to:
- Run GitHub Code Search queries
- Group matches by repository and fetch star counts
- Optionally scan the full repository (default branch) for your own regex patterns

## Prereqs
- Python 3.10+
- A GitHub Personal Access Token (classic) with public repo read access

## Usage

Basic search (interactive prompt if `-q` omitted):
```bash
python search_github.py -k YOUR_GITHUB_TOKEN -q "language:php PDO::prepare"
```

Search and then scan matching repos for additional regex patterns:
```bash
python search_github.py \
  -k YOUR_GITHUB_TOKEN \
  -q "language:js knex.raw \"\${\"" \
  -p "knex\.raw\s*\(`.*\$\{.*\`" \
  -p "SELECT\s+\$\{col\}\s+FROM" \
  --min-stars 200 --max-files 1500 --max-bytes 200000
```

Flags:
- `-k, --api-key` (required): GitHub token
- `-q, --query`: GitHub code search query (see GitHub search syntax)
- `-p, --pattern` (repeatable): Regex(es) to scan within repos (after search)
- `--min-stars` (default 500): Only include repositories with at least this many stars
- `--max-files` (default 2000): Max files to scan per repo when patterns are provided
- `--max-bytes` (default 200000): Skip files larger than this size

Notes:
- The tool paginates GitHub search results and handles basic rate limits (waits until reset).
- For full-repo scans, it fetches the tree of the default branch and downloads raw files (skips likely binaries).
- Output shows per‑repo matches with short context snippets.

## Example queries
- PDO emulation/prepare usage (PHP):
```bash
python search_github.py -k $GHTOKEN -q "language:php PDO::prepare"
```
- Knex raw with template literals (JS/TS):
```bash
python search_github.py -k $GHTOKEN -q "language:js knex.raw \"\${\""
```

## Tips
- Use precise language filters and keywords to reduce rate‑limit impact.
- Add multiple `-p` patterns to catch variants (identifiers, comments, null bytes, etc.).