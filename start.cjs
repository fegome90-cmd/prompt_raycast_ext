/**
 * PM2 wrapper for FastAPI backend
 * Spawns uvicorn with the DSPy Prompt Improver API
 */
const { spawn } = require('child_process');

const proc = spawn(
  'uv',
  [
    'run',
    'uvicorn',
    'api.main:app',
    '--host',
    '0.0.0.0',
    '--port',
    '8000',
    '--reload',
  ],
  {
    cwd: __dirname,
    stdio: 'inherit',
    windowsHide: true,
  }
);

proc.on('close', (code) => process.exit(code));
proc.on('error', (err) => {
  console.error('Failed to start uvicorn:', err);
  process.exit(1);
});
