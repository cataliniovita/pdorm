import express from 'express';
import knexFactory from 'knex';
import config from './knexfile.js';

const app = express();
const port = 3000;
const knex = knexFactory(config);

app.get('/health', async (req, res) => {
  try {
    await knex.raw('SELECT 1');
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message });
  }
});

app.get('/safe', async (req, res) => {
  const name = req.query.name || '';
  const col = req.query.col || 'name';
  const allowed = ['id', 'name', 'color', 'price'];
  if (!allowed.includes(col)) return res.status(400).json({ error: 'invalid column' });
  try {
    const rows = await knex('fruit').select({ val: col }).where({ name });
    res.json({ rows });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.get('/vuln', async (req, res) => {
  const name = req.query.name || '';
  const col = String(req.query.col || 'name');
  // VULN: raw with naive identifier interpolation
  const sanitized = col.replace(/`/g, '``');
  const sql = `SELECT \`${sanitized}\` AS val FROM fruit WHERE name = ?`;
  try {
    const rows = await knex.raw(sql, [name]);
    res.json({ query: sql, rows: rows[0] });
  } catch (e) {
    res.status(500).json({ query: sql, error: e.message });
  }
});

app.listen(port, '0.0.0.0', () => console.log(`node-knex ${port}`));


