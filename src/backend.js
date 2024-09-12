// bun run ./src/backend.js

import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';
import { format } from 'date-fns';
import { schedule } from 'node-cron';
import os from 'os';

// Server port
const PORT = 8001;

// CCTV Set up
let cctvSessions = {};
let latestUpdateTime;
let latestRefreshTime;
const jsonDirectory = './cctvSessionTemp/';
const jsonMaxAgeHours = 24;
const updateCamInfoPath = './src/main.py';
const cctvDistance = 170;

// Set up logging
let currentLogFile;
let logStream;
let logStartTime;
const logToConsole = true;
const logToFile = true;
const logRotationIntervalHours = 1;
const logMaxAgeHours = 24;
const logDirectory = './logs';

function setupLogger() {
  setupNewLogFile(logDirectory);

  const originalLog = console.log;
  const originalError = console.error;

  console.log = function (...args) {
    checkLogRotationAndCleanup();
    if (logToConsole) {
      originalLog.apply(console, args);
    }
    if (logToFile && logStream) {
      logStream.write(getFormattedLog(args) + '\n');
    }
  };

  console.error = function (...args) {
    checkLogRotationAndCleanup();
    if (logToConsole) {
      originalError.apply(console, args);
    }
    if (logToFile && logStream) {
      logStream.write(getFormattedLog(args) + '\n');
    }
  };

  function setupNewLogFile(directory) {
    const timestamp = format(new Date(), 'yyyy-MM-dd_HH-mm-ss');
    currentLogFile = path.join(directory, `backend_${timestamp}.log`);
    if (!fs.existsSync(directory)) {
      fs.mkdirSync(directory, { recursive: true });
    }
    if (logStream) logStream.end();
    logStream = fs.createWriteStream(currentLogFile, { flags: 'a' });
    logStartTime = Date.now();
  }

  function getFormattedLog(args) {
    const timestamp = format(new Date(), 'yyyy-MM-dd HH:mm:ss');
    return `${timestamp} ${args.map(arg => (typeof arg === 'string' ? arg : JSON.stringify(arg))).join(' ')}`;
  }
}

function checkLogRotationAndCleanup(directory = logDirectory, rotationIntervalMilliseconds = logRotationIntervalHours * 60 * 60 * 1000, logMaxAgeMilliseconds = logMaxAgeHours * 60 * 60 * 1000) {
  checkLogRotation(directory, rotationIntervalMilliseconds);
  deleteOldLogFiles(directory, logMaxAgeMilliseconds);
}

function checkLogRotation(directory, rotationInterval) {
  const now = Date.now();
  const elapsed = now - logStartTime;

  if (elapsed >= rotationInterval) {
    setupNewLogFile(directory);
  }
}

function deleteOldLogFiles(directory, deletionInterval) {
  const files = fs.readdirSync(directory);
  const now = Date.now();

  files.forEach(file => {
    const filePath = path.join(directory, file);
    const stats = fs.statSync(filePath);
    const fileAge = now - stats.mtimeMs;

    if (fileAge > deletionInterval) {
      fs.unlinkSync(filePath);
    }
  });
}

// Initialize logging setup
setupLogger();



// Function to start the Python script and get CCTV IDs
function startUpdate() {
  return new Promise((resolve, reject) => {
    console.log(`\n############### Starting Python Script ###############\n\n`);
    const pythonProcess = spawn('python', [updateCamInfoPath, cctvDistance]);

    pythonProcess.stdout.on('data', (data) => {
      console.log('[PY]', data.toString());
    });

    pythonProcess.stderr.on('data', (data) => {
      console.error('[PY]', data.toString());
    });

    pythonProcess.on('close', (code) => {
      console.log(`Python script exited with code ${code}`);
      console.log(`\n\n############### End of Python Script ###############\n\n`);

      if (code === 0) {
        resolve();
      } else {
        reject(`Python process exited with code ${code}`);
      }
    });
  });
}

// Function to find and read the latest JSON file from the directory
function getLatestJsonFile(directory = jsonDirectory) {
  const files = fs.readdirSync(directory);
  const jsonFiles = files.filter(file => file.startsWith('cctv_sessions_') && file.endsWith('.json'));

  if (jsonFiles.length === 0) {
    console.error('No JSON files found in the directory.');
    return null;
  }

  const latestFile = jsonFiles.reduce((latest, file) => {
    const currentTime = fs.statSync(path.join(directory, file)).mtime.getTime();
    const latestTime = fs.statSync(path.join(directory, latest)).mtime.getTime();
    return currentTime > latestTime ? file : latest;
  });

  console.log(`Latest JSON file: ${latestFile}`);
  return path.join(directory, latestFile);
}

// Function to delete JSON files older than a specified number of hours
function deleteOldJsonFiles(directory = jsonDirectory, maxAgeHours = jsonMaxAgeHours) {
  const files = fs.readdirSync(directory);
  const now = Date.now();
  const maxAgeMilliseconds = maxAgeHours * 60 * 60 * 1000; // Convert hours to milliseconds

  files.forEach(file => {
    if (file.startsWith('cctv_sessions_') && file.endsWith('.json')) {
      const filePath = path.join(directory, file);
      const fileAge = now - fs.statSync(filePath).mtime.getTime();

      if (fileAge > maxAgeMilliseconds) {
        fs.unlinkSync(filePath);
        console.log(`Deleted old JSON file: ${file}`);
      }
    }
  });
}

// Function to load JSON data from the latest file into cctvSessions, latestUpdateTime, and latestRefreshTime
function loadCctvSessions() {
  deleteOldJsonFiles(); // Call the function to delete old files

  const latestFile = getLatestJsonFile();

  if (latestFile) {
    try {
      const data = fs.readFileSync(latestFile, 'utf8');
      const jsonData = JSON.parse(data);

      // Extract values from JSON data
      cctvSessions = jsonData.cctvSessions;
      latestUpdateTime = jsonData.latestUpdateTime;
      latestRefreshTime = jsonData.latestRefreshTime;

      console.log('Loaded CCTV sessions:', cctvSessions);
      console.log('Latest update time:', latestUpdateTime);
      console.log('Latest refresh time:', latestRefreshTime);

      // You can use cctvSessions, latestUpdateTime, and latestRefreshTime as needed in your code

    } catch (error) {
      console.error('Failed to read or parse the latest JSON file:', error);
    }
  }
}

// Initialize sessions for all CCTV IDs
async function initializeSessions() {
  console.log('Initializing CCTV sessions...');

  try {
    checkLogRotationAndCleanup();  // Check log rotation and cleanup before the operation
    await startUpdate();
    loadCctvSessions();
    console.log('All sessions initialized.');
  } catch (error) {
    console.error('Failed to initialize sessions:', error);
  }
}

// Start the server using Bun's `Bun.serve`
Bun.serve({
  port: PORT,
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
const interfaces = os.networkInterfaces();
Object.keys(interfaces).forEach((interfaceName) => {
  interfaces[interfaceName].forEach((iface) => {
    if ('IPv4' === iface.family && !iface.internal) {
      console.log(`Server running on http://${iface.address}:${PORT}`);
    }
  });
});

initializeSessions().then(() => {
  console.log('Session initialization completed.');
});

// Schedule the initializeSessions function to run every 15 minutes
schedule('*/10 * * * *', async () => {
  console.log('Running scheduled session initialization...');
  await initializeSessions();
});
