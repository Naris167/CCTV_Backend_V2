// bun run ./src/backend.js

import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';
import { format } from 'date-fns';
import os from 'os';

// Configuration
const CONFIG = {
  PORT: 7000,
  CCTV: {
    jsonDirectory: './cctvSessionTemp/',
    jsonMaxAgeHours: 2400000000,
    updateCamInfoPath: './src/main.py',
    cctvDistance: 170,
    updateInterval: 10 * 60 * 1000, // 10 minutes
  },
  LOGGING: {
    directory: './logs',
    toConsole: true,
    toFile: true,
    rotationIntervalHours: 1,
    maxAgeHours: 2400000000,
  },
};

// CCTV setup
let cctvSessions = {};
let latestUpdateTime, latestRefreshTime;

// Logging setup
let currentLogFile, logStream, logStartTime;

function setupLogger() {
  const setupNewLogFile = () => {
    const timestamp = format(new Date(), 'yyyy-MM-dd_HH-mm-ss');
    currentLogFile = path.join(CONFIG.LOGGING.directory, `backend_${timestamp}.log`);
    fs.mkdirSync(CONFIG.LOGGING.directory, { recursive: true });
    if (logStream) logStream.end();
    logStream = fs.createWriteStream(currentLogFile, { flags: 'a' });
    logStartTime = Date.now();
  };

  const getFormattedLog = (args) => {
    const timestamp = format(new Date(), 'yyyy-MM-dd HH:mm:ss');
    return `${timestamp} ${args.map(arg => (typeof arg === 'string' ? arg : JSON.stringify(arg))).join(' ')}`;
  };

  setupNewLogFile();

  ['log', 'error'].forEach(method => {
    const original = console[method];
    console[method] = function (...args) {
      checkLogRotationAndCleanup();
      if (CONFIG.LOGGING.toConsole) original.apply(console, args);
      if (CONFIG.LOGGING.toFile && logStream) {
        logStream.write(getFormattedLog(args));
        logStream.write('\n');
      }
    };
  });
}

function checkLogRotationAndCleanup() {
  const now = Date.now();
  const rotationInterval = CONFIG.LOGGING.rotationIntervalHours * 60 * 60 * 1000;
  const maxAge = CONFIG.LOGGING.maxAgeHours * 60 * 60 * 1000;

  if (now - logStartTime >= rotationInterval) {
    setupLogger();
  }

  fs.readdirSync(CONFIG.LOGGING.directory).forEach(file => {
    const filePath = path.join(CONFIG.LOGGING.directory, file);
    if (now - fs.statSync(filePath).mtimeMs > maxAge) {
      fs.unlinkSync(filePath);
    }
  });
}

function startUpdate() {
  return new Promise((resolve, reject) => {
    console.log('\n############### Starting Python Script ###############\n');
    const pythonProcess = spawn('python', [CONFIG.CCTV.updateCamInfoPath, CONFIG.CCTV.cctvDistance]);

    pythonProcess.stdout.on('data', data => console.log('[PY]', data.toString()));
    pythonProcess.stderr.on('data', data => console.error('[PY]', data.toString()));

    pythonProcess.on('close', code => {
      console.log(`Python script exited with code ${code}`);
      console.log('\n############### End of Python Script ###############\n');
      code === 0 ? resolve() : reject(`Python process exited with code ${code}`);
    });
  });
}

function getLatestJsonFile() {
  const files = fs.readdirSync(CONFIG.CCTV.jsonDirectory)
    .filter(file => file.startsWith('cctv_sessions_') && file.endsWith('.json'));

  if (files.length === 0) {
    console.error('No JSON files found in the directory.');
    return null;
  }

  const latestFile = files.reduce((latest, file) => {
    return fs.statSync(path.join(CONFIG.CCTV.jsonDirectory, file)).mtime.getTime() >
           fs.statSync(path.join(CONFIG.CCTV.jsonDirectory, latest)).mtime.getTime() ? file : latest;
  });

  console.log(`Latest JSON file: ${latestFile}`);
  return path.join(CONFIG.CCTV.jsonDirectory, latestFile);
}

function deleteOldJsonFiles() {
  const now = Date.now();
  const maxAge = CONFIG.CCTV.jsonMaxAgeHours * 60 * 60 * 1000;

  fs.readdirSync(CONFIG.CCTV.jsonDirectory).forEach(file => {
    if (file.startsWith('cctv_sessions_') && file.endsWith('.json')) {
      const filePath = path.join(CONFIG.CCTV.jsonDirectory, file);
      if (now - fs.statSync(filePath).mtime.getTime() > maxAge) {
        fs.unlinkSync(filePath);
        console.log(`Deleted old JSON file: ${file}`);
      }
    }
  });
}

function loadCctvSessions() {
  deleteOldJsonFiles();
  const latestFile = getLatestJsonFile();

  if (latestFile) {
    try {
      const { cctvSessions: sessions, latestUpdateTime: updateTime, latestRefreshTime: refreshTime } = 
        JSON.parse(fs.readFileSync(latestFile, 'utf8'));

      cctvSessions = sessions;
      latestUpdateTime = updateTime;
      latestRefreshTime = refreshTime;

      console.log('Loaded CCTV sessions:', cctvSessions);
      console.log('Latest update time:', latestUpdateTime);
      console.log('Latest refresh time:', latestRefreshTime);
    } catch (error) {
      console.error('Failed to read or parse the latest JSON file:', error);
    }
  }
}

async function initializeSessions() {
  console.log('Initializing CCTV sessions...');
  try {
    checkLogRotationAndCleanup();
    await startUpdate();
    loadCctvSessions();
    console.log('All sessions initialized.');
  } catch (error) {
    console.error('Failed to initialize sessions:', error);
  }
}

function scheduleNextExecution() {
  setTimeout(async () => {
    console.log('Running scheduled session initialization...');
    await initializeSessions();
    scheduleNextExecution();
  }, CONFIG.CCTV.updateInterval);
}

// Start the server
Bun.serve({
  port: CONFIG.PORT,
  fetch(req) {
    const url = new URL(req.url);
    if (url.pathname === '/session_id') {
      const cameraID = url.searchParams.get('cctv_id');
      console.log(`User requested CCTV: ${cameraID}`);
      const sessionID = cctvSessions[cameraID];
      if (sessionID) {
        return new Response(JSON.stringify({ cctv_id: cameraID, session_id: sessionID }), {
          headers: { 'Content-Type': 'application/json' },
        });
      } else {
        console.log(`Session ID not found for the given CCTV ID`);
        return new Response(JSON.stringify({ error: 'Session ID not found for the given CCTV ID' }), { status: 404 });
      }
    }
    return new Response('Not found', { status: 404 });
  },
  error(err) {
    console.error(err);
  },
});

// Log all IP addresses where the server is running
Object.values(os.networkInterfaces()).flat().forEach(({ family, internal, address }) => {
  if (family === 'IPv4' && !internal) {
    console.log(`Server running on http://${address}:${CONFIG.PORT}`);
  }
});

// Initialize and start scheduling
setupLogger();
initializeSessions().then(() => {
  console.log('Session initialization completed.');
  scheduleNextExecution();
});