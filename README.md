# pdorm
This repository provides a reproducible, multi-service environment to demonstrate subtle SQL injection issues across languages and libraries, including the PDO emulated-prepares parser trick described by Assetnote.
## SQL Injection Multi-language Testbed (Docker Compose)

This repository provides a reproducible, multi-service environment to demonstrate subtle SQL injection issues across languages and libraries, including the PDO emulated-prepares parser trick described by Assetnote.

Reference: Assetnote — Abusing Emulated Prepared Statements in PHP PDO to Achieve SQLi: `https://slcyber.io/assetnote-security-research-center/a-novel-technique-for-sql-injection-in-pdos-prepared-statements`

### What it includes

- One MySQL service pre-seeded with tables: `users`, `fruit`, `products` (see `db/init.sql`).
- Web services, each exposing:
  - `/health` for readiness
  - `/safe` showing correct parameter binding and identifier whitelisting
  - `/vuln` intentionally vulnerable patterns (identifier interpolation, emulated prepares, raw queries)
- An attacker container that runs an automated test harness and writes `report.md` and `vuln-report.json` into the project root.

### Services

- `php-pdo-emulate` and `php-pdo-native` (PDO with `ATTR_EMULATE_PREPARES` on/off)
- `node-mysql2`, `node-knex`, `node-sequelize`
- `python-mysql-connector`, `python-sqlalchemy`
- `java-jdbc`, `java-spring-boot` (coming in this scaffold)
- `ruby-activerecord`

All services bind only on the internal Docker network; no ports are published by default.

### Run

```bash
docker compose up --build
```

The attacker will start after all services are healthy and execute tests against each `/safe` and `/vuln` endpoint using a matrix of payloads (null byte, `?`, comments, etc.).

Outputs will be written to:

- `report.md`
- `vuln-report.json`

### Add a new service

Create a folder, add a `Dockerfile` and minimal app exposing `/health`, `/safe`, and `/vuln`. Use env vars `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASS` for the database. Add the service to `docker-compose.yml` and the test harness list in `tests/run_tests.sh`.

### Safety and disclaimer

This environment is for legitimate security research and education only. Run it on isolated networks. Do not expose the services publicly.

### Mitigation notes

See `notes/` for brief guidance per stack (identifier whitelisting, server-side prepares, avoiding raw string interpolation, proper quoting helpers like `quote_column_name`, and disabling PDO emulation when possible).

