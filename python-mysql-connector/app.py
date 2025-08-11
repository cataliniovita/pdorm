from flask import Flask, request, jsonify
import pymysql

app = Flask(__name__)

def get_conn():
    return pymysql.connect(
        host = os.getenv('DB_HOST', 'db'),
        user = os.getenv('DB_USER', 'app'),
        password = os.getenv('DB_PASS', 'apppass'),
        db = os.getenv('DB_NAME', 'demo'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

import os

@app.get('/health')
def health():
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.fetchall()
        cur.close()
        conn.close()
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
    sql = f"SELECT `{col}` AS val FROM fruit WHERE name = %s"
    try:
        conn = get_conn()
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, (name,))
        rows = cur.fetchall()
        cur.close(); conn.close()
        return jsonify(rows=rows)
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.get('/vuln')
def vuln():
    name = request.args.get('name', '')
    col = str(request.args.get('col', 'name'))
    # VULN: naive backtick escaping; leaves '?' and comments that may affect parsers or cause injection when concatenated elsewhere
    sanitized = col.replace('`', '``')
    sql = f"SELECT `{sanitized}` AS val FROM fruit WHERE name = %s"
    try:
        conn = get_conn()
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, (name,))
        rows = cur.fetchall()
        cur.close(); conn.close()
        return jsonify(query=sql, rows=rows)
    except Exception as e:
        return jsonify(query=sql, error=str(e)), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


