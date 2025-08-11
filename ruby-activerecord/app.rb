require 'sinatra'
require 'active_record'
require 'json'

set :bind, '0.0.0.0'
set :port, 4567

ActiveRecord::Base.establish_connection(
  adapter:  'mysql2',
  host:     ENV['DB_HOST'] || 'db',
  database: ENV['DB_NAME'] || 'demo',
  username: ENV['DB_USER'] || 'app',
  password: ENV['DB_PASS'] || 'apppass',
  encoding: 'utf8mb4'
)

get '/health' do
  begin
    ActiveRecord::Base.connection.execute('SELECT 1')
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
  allowed = %w[id name color price]
  halt 400, { error: 'invalid column' }.to_json unless allowed.include?(col)
  sql = "SELECT `#{col}` AS val FROM fruit WHERE name = ?"
  rows = ActiveRecord::Base.connection.exec_query(ActiveRecord::Base.send(:sanitize_sql_array, [sql, name])).to_a
  content_type :json
  { rows: rows }.to_json
end

get '/vuln' do
  name = params['name'] || ''
  col = (params['col'] || 'name').to_s
  # VULN: naive backtick escaping; identifier interpolation
  sanitized = col.gsub('`', '``')
  sql = "SELECT `#{sanitized}` AS val FROM fruit WHERE name = ?"
  rows = ActiveRecord::Base.connection.exec_query(ActiveRecord::Base.send(:sanitize_sql_array, [sql, name])).to_a
  content_type :json
  { query: sql, rows: rows }.to_json
end


