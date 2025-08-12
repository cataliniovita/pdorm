#!/usr/bin/env bash
set -euo pipefail

# This script runs inside the attacker container after services are healthy
BASES=(
  "php-pdo-emulate:8080"
  "php-pdo-native:8080"
  "node-mysql2:3000"
  "node-knex:3000"
  "node-sequelize:3000"
  "python-mysql-connector:5000"
  "python-sqlalchemy:5000"
  "java-jdbc:8080"
  "java-spring-boot:8080"
  "ruby-activerecord:4567"
  "ruby-pg:4567"
)

PAYLOADS=(
  "col=name&name=apple"                 # benign
  "col=%00&name=apple"                  # null byte
  "col=?%23%00&name=apple"              # ?#\0 (comment + NUL) — Assetnote-style
  "col=name?%23%00&name=apple"          # identifier with ?#\0
  "col=%3F%3B%23%00&name=apple"         # ?;#\0
  "col=name%60&name=apple"              # stray backtick
)

mkdir -p /workspace/out
REPORT_JSON=/workspace/out/vuln-report.json
REPORT_MD=/workspace/out/report.md
echo "{}" > "$REPORT_JSON"
echo "# SQLi Test Report" > "$REPORT_MD"
echo "" >> "$REPORT_MD"

http_json() {
  local base=$1
  local path=$2
  local payload=$3
  local url="http://$base$path?$payload"
  http_code=0
  curl -sS -w "\n%{http_code}" "$url" -o /tmp/resp.body || true
  http_code=$(tail -n1 /tmp/resp.body)
  sed -n '$d' /tmp/resp.body > /tmp/resp.json || true
  if [[ ! -s /tmp/resp.json ]]; then
    echo "{}" > /tmp/resp.json
  fi
  echo "${http_code}" > /tmp/resp.code
  cat /tmp/resp.json
}

record() {
  local service=$1
  local endpoint=$2
  local payload=$3
  local _unused_response=$4
  local key="${service}_${endpoint//\//_}_${payload}"
  # shrink key
  key=$(echo "$key" | tr -cd '[:alnum:]_-' | cut -c1-80)
  local code="0"
  [[ -f /tmp/resp.code ]] && code=$(cat /tmp/resp.code)
  tmp=$(mktemp)
  # Store raw body regardless of JSON validity and the HTTP status code
  if jq --arg k "$key" --arg code "$code" --rawfile body /tmp/resp.json \
       '. + {($k): {http_code: ($code|tonumber), body: $body}}' \
       "$REPORT_JSON" > "$tmp"; then
    mv "$tmp" "$REPORT_JSON"
  else
    # Fallback: do not break the run, append a line-delimited JSON entry
    echo "{\"key\":\"$key\",\"http_code\":$code,\"body\":$(jq -Rs . /tmp/resp.json)}" >> /workspace/out/vuln-report.ndjson || true
    rm -f "$tmp" || true
  fi
}

assess() {
  # Heuristic: if /vuln returns HTTP >= 400 or contains an 'error' key for a malicious payload (non-benign), mark as vulnerable.
  # If /safe returns 400 invalid column for malicious payloads, mark as safe.
  local endpoint=$1
  local payload=$2
  local http_code=$(cat /tmp/resp.code)
  local has_error=$(jq -r 'has("error")' /tmp/resp.json 2>/dev/null || echo false)
  local is_benign=false
  [[ "$payload" == "col=name&name=apple" ]] && is_benign=true

  local verdict="unknown"
  if [[ "$endpoint" == "/vuln" ]]; then
    if [[ "$is_benign" == false && ( "$http_code" -ge 400 || "$has_error" == "true" ) ]]; then
      verdict="vulnerable"
    else
      verdict="no_indicator"
    fi
  else
    # /safe
    if [[ "$http_code" -eq 400 ]]; then
      verdict="safe_rejected"
    elif [[ "$http_code" -ge 400 || "$has_error" == "true" ]]; then
      verdict="error"
    else
      verdict="ok"
    fi
  fi
  echo "$verdict" > /tmp/verdict
}

summarize() {
  echo "## Summary" >> "$REPORT_MD"
  echo "" >> "$REPORT_MD"
  for base in "${BASES[@]}"; do
    service=${base%%:*}
    echo "- ${service}:" >> "$REPORT_MD"
    echo "  - /vuln tested with ${#PAYLOADS[@]} payloads" >> "$REPORT_MD"
    echo "  - /safe tested with ${#PAYLOADS[@]} payloads" >> "$REPORT_MD"
  done
}

for base in "${BASES[@]}"; do
  service=${base%%:*}
  for endpoint in /vuln /safe; do
    for payload in "${PAYLOADS[@]}"; do
      echo "Testing ${service} ${endpoint} ${payload}" >&2
      resp_json=$(http_json "$base" "$endpoint" "$payload")
      # Determine success heuristic: errors containing SQL syntax issues or rows from information_schema (not implemented here), record raw
      record "$service" "$endpoint" "$payload" "$resp_json"
      assess "$endpoint" "$payload"
      verdict=$(cat /tmp/verdict)
      echo "${service} ${endpoint} ${payload} => ${verdict}" >> "$REPORT_MD"
    done
  done
done

summarize
echo "Done. Wrote $REPORT_JSON and $REPORT_MD" >&2


