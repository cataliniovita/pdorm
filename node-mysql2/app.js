import express from 'express';
import mysql from 'mysql2/promise';

const app = express();
const port = 3000;

const pool = mysql.createPool({
  host: process.env.DB_HOST || 'db',
  user: process.env.DB_USER || 'app',
  password: process.env.DB_PASS || 'apppass',
  database: process.env.DB_NAME || 'demo',
  waitForConnections: true,
  connectionLimit: 5
});

app.get('/health', async (req, res) => {
  try {
    const conn = await pool.getConnection();
    await conn.ping();
    conn.release();
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message });
  }
});

app.get('/safe', async (req, res) => {
  const name = req.query.name || '';
  const col = req.query.col || 'name';
  const allowed = ['id', 'name', 'color', 'price'];
  if (!allowed.includes(col)) {
    return res.status(400).json({ error: 'invalid column' });
  }
  try {
    // Use whitelisted identifier, still quoted for clarity
    const sql = `SELECT \`${col}\` AS val FROM fruit WHERE name = ?`;
    const [rows] = await pool.execute(sql, [name]);
    res.json({ rows });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.get('/vuln', async (req, res) => {
  const name = req.query.name || '';
  const col = String(req.query.col || 'name');
  // VULN: naive backtick escaping allows special chars like '?' and comment/null-byte tricks
  const sanitized = col.replace(/`/g, '``');
  const sql = `SELECT \`${sanitized}\` AS val FROM fruit WHERE name = ?`;
  try {
    const [rows] = await pool.execute(sql, [name]);
    res.json({ query: sql, rows });
  } catch (e) {
    res.status(500).json({ query: sql, error: e.message });
  }
});

app.listen(port, '0.0.0.0', () => {
  console.log(`node-mysql2 listening on ${port}`);
});


