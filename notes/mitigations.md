### Mitigations (by stack)

- PHP PDO
  - Set `PDO::ATTR_EMULATE_PREPARES = false` to avoid client-side parsing quirks.
  - Never interpolate identifiers from user input; whitelist expected columns/tables.
  - Do not attempt manual backtick escaping for identifiers.

- Node.js (mysql2/knex/sequelize)
  - Prefer whitelisting identifiers; avoid template-string interpolation.
  - For raw queries, use parameter binding for values only and compose identifiers from whitelisted sets.

- Python (mysql-connector, SQLAlchemy)
  - Use bound parameters for values and whitelist identifiers.
  - Avoid f-strings in `text()` queries.

- Java (JDBC, Spring/JPA)
  - Use `PreparedStatement` for values; never concatenate identifiers.
  - For dynamic identifiers, map from enums or whitelists.

- Ruby (ActiveRecord)
  - Use `where("col = ?", val)` for values.
  - Use `connection.quote_column_name` or whitelists rather than interpolating raw params.


