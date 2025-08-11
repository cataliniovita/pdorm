export default {
  client: 'mysql2',
  connection: {
    host: process.env.DB_HOST || 'db',
    user: process.env.DB_USER || 'app',
    password: process.env.DB_PASS || 'apppass',
    database: process.env.DB_NAME || 'demo'
  },
  pool: { min: 0, max: 5 }
};


