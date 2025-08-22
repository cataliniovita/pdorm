from flask import Flask, request, jsonify
from sqlalchemy import create_engine, text
import os
import psycopg2

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST', 'db')
DB_USER = os.getenv('DB_USER', 'app')
DB_PASS = os.getenv('DB_PASS', 'apppass')
DB_NAME = os.getenv('DB_NAME', 'demo')

engine = create_engine(f"mysql+mysqldb://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}?charset=utf8mb4", pool_pre_ping=True)

DB_HOST_pg = os.getenv('DB_HOST_pg', 'pg')
DB_NAME_pg = os.getenv('DB_NAME_pg', 'demopg')

engine_pg = create_engine(f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST_pg}/{DB_NAME_pg}", pool_pre_ping=True)

@app.get('/health')
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        return jsonify(ok=True)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500

@app.get('/safe')
def safe():
    name = request.args.get('name', '')
    col = request.args.get('col', 'name')
    allowed = ['id', 'name', 'color', 'price']
    if col not in allowed:
        return jsonify(error='invalid column'), 400
    sql = text(f"SELECT `{col}` AS val FROM fruit WHERE name = :name")
    try:
        with engine.connect() as conn:
            rows = conn.execute(sql, { 'name': name }).mappings().all()
        return jsonify(rows=list(rows))
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.get('/vuln')
def vuln():
    name = request.args.get('name', '')
    col = request.args.get('col', '')
    col = '`' + col.replace('`', '``') + '`'

    sql = text(f"SELECT {col} AS val FROM fruit WHERE name = :name")
    try:
        with engine.connect() as conn:
            rows = conn.execute(sql, { 'name': name }).mappings().all()
        return jsonify(query=str(sql), rows=list(rows))
    except Exception as e:
        return jsonify(query=str(sql), error=str(e)), 500

@app.get('/vuln_pg')
def vuln_pg():
    name = request.args.get('name', '')
    col = request.args.get('col', '')
#    col = '`' + col.replace('`', '``') + '`'
    col = '"' + col.replace('"', '\\"') + '"'

    sql = text(f"SELECT {col} FROM users WHERE name = :name")
    try:
        with engine_pg.connect() as conn:
            rows = conn.execute(sql, { 'name': name }).mappings().all()
        return jsonify(query=str(sql), rows=list(rows)) ### Change this
    except Exception as e:
        return jsonify(query=str(sql), error=str(e)), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)