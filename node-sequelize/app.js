import express from 'express';
import { Sequelize, QueryTypes } from 'sequelize';

const app = express();
const port = 3000;

const sequelize = new Sequelize(process.env.DB_NAME || 'demo', process.env.DB_USER || 'app', process.env.DB_PASS || 'apppass', {
  host: process.env.DB_HOST || 'db',
  dialect: 'mysql',
  logging: false
});

app.get('/health', async (req, res) => {
  try { await sequelize.authenticate(); res.json({ ok: true }); }
  catch (e) { res.status(500).json({ ok: false, error: e.message }); }
});

app.get('/safe', async (req, res) => {
  const name = req.query.name || '';
  const col = req.query.col || 'name';
  const allowed = ['id', 'name', 'color', 'price'];
  if (!allowed.includes(col)) return res.status(400).json({ error: 'invalid column' });
  try {
    // Safe: whitelist identifier, then bind value via replacements
    const sql = `SELECT \`${col}\` AS val FROM fruit WHERE name = :name`;
    const rows = await sequelize.query(sql, { replacements: { name }, type: QueryTypes.SELECT });
    res.json({ rows });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.get('/vuln', async (req, res) => {
  const name = req.query.name || '';
  const col = String(req.query.col || 'name');
  // VULN: direct string interpolation for identifiers before replacements
  const sanitized = col.replace(/`/g, '``');
  const sql = `SELECT \`${sanitized}\` AS val FROM fruit WHERE name = :name`;
  try {
    const rows = await sequelize.query(sql, { replacements: { name }, type: QueryTypes.SELECT });
    res.json({ query: sql, rows });
  } catch (e) {
    res.status(500).json({ query: sql, error: e.message });
  }
});

app.listen(port, '0.0.0.0', () => console.log(`node-sequelize ${port}`));


