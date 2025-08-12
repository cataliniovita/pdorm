require 'sinatra'
require 'pg'
require 'json'

set :bind, '0.0.0.0'
set :port, 4567

def pg_conn
  PG.connect(
    host: ENV['PG_HOST'] || 'pg',
    dbname: ENV['PG_DB'] || 'demopg',
    user: ENV['PG_USER'] || 'app',
    password: ENV['PG_PASS'] || 'apppass'
  )
end

get '/health' do
  begin
    conn = pg_conn
    conn.exec('SELECT 1')
    conn.close
    content_type :json
    { ok: true }.to_json
  rescue => e
    status 500
    { ok: false, error: e.message }.to_json
  end
end

get '/safe' do
  name = params['name'] || ''
  col = params['col'] || 'name'
  allowed = %w[id name email role]
  halt 400, { error: 'invalid column' }.to_json unless allowed.include?(col)
  sql = "SELECT \"#{col}\" AS val FROM users WHERE name = $1"
  conn = pg_conn
  rows = conn.exec_params(sql, [name]).to_a
  conn.close
  content_type :json
  { rows: rows }.to_json
end

get '/vuln' do
  name = params['name'] || ''
  col = (params['col'] || 'name').to_s
  
  quoted_col = '"' + col.gsub('"', '""') + '"'
  sql = "SELECT #{quoted_col} AS val FROM users WHERE name = $1"

  conn = pg_conn
  begin
    rows = conn.exec_params(sql, [name]).to_a
    payload = { query: sql, rows: rows }
  rescue => e
    status 500
    payload = { query: sql, error: e.message }
  ensure
    conn.close
  end
  content_type :json
  payload.to_json
end


