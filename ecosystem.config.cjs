module.exports = {
  apps: [
    {
      name: 'raycast-backend-8000',
      cwd: __dirname,
      script: 'start.cjs',
      interpreter: '/opt/homebrew/bin/node',
      // Startup resilience
      listen_timeout: 10000,      // 10s startup grace period
      kill_timeout: 5000,         // Clean shutdown time
      // Restart limits (prevent infinite restart loops)
      max_restarts: 3,            // Limit restart attempts
      restart_delay: 2000,        // Wait 2s between restarts
      autorestart: true,          // Auto-restart on crash
      watch: false,               // Don't watch files (causes issues)
      // Logging
      error_file: '.logs/pm2-error.log',
      out_file: '.logs/pm2-out.log',
      time: true,                 // Timestamp logs
      env: {
        NODE_ENV: 'development',
        PYTHONUNBUFFERED: '1',
      },
    },
  ],
};
