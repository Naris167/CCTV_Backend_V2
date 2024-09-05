// bun run ./src/backend.js


import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';
import { format } from 'date-fns'; // Library for date formatting
import { schedule } from 'node-cron';

// Define the server port
const PORT = 8001;

// Dictionary to store session IDs for each CCTV ID
let cctvSessions = {};

// Function to set up logging to both console and a file
function setupLogger({ logToConsole = true, logToFile = true } = {}) {
  const logDirectory = './logs';
  const timestamp = format(new Date(), 'yyyy-MM-dd_HH-mm-ss');
  const logFile = path.join(logDirectory, `backend_${timestamp}.log`);

  if (logToFile && !fs.existsSync(logDirectory)) {
    fs.mkdirSync(logDirectory, { recursive: true });
  }

  const logStream = logToFile ? fs.createWriteStream(logFile, { flags: 'a' }) : null;
  const originalLog = console.log;
  const originalError = console.error;

  console.log = function (...args) {
    if (logToConsole) {
      originalLog.apply(console, args);
    }
    if (logToFile && logStream) {
      logStream.write(getFormattedLog(args) + '\n');
    }
  };

  console.error = function (...args) {
    if (logToConsole) {
      originalError.apply(console, args);
    }
    if (logToFile && logStream) {
      logStream.write(getFormattedLog(args) + '\n');
    }
  };

  function getFormattedLog(args) {
    const timestamp = format(new Date(), 'yyyy-MM-dd HH:mm:ss');
    return `${timestamp} ${args.map(arg => (typeof arg === 'string' ? arg : JSON.stringify(arg))).join(' ')}`;
  }
}

// Initialize logging setup
setupLogger();

// Function to start the Python script and get CCTV IDs
function startUpdate() {
  return new Promise((resolve, reject) => {
    console.log(`\n############### Starting Python Script ###############\n\n`);
    const pythonProcess = spawn('python', ['./src/updateCamInfo.py', '170']);

    pythonProcess.stdout.on('data', (data) => {
      console.log('Python script output:', data.toString());
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
function getLatestJsonFile(directory) {
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

// Function to load JSON data from the latest file into cctvSessions
function loadCctvSessions() {
  const directory = './cctvSessionTemp/';
  const latestFile = getLatestJsonFile(directory);

  if (latestFile) {
    try {
      const data = fs.readFileSync(latestFile, 'utf8');
      cctvSessions = JSON.parse(data);
      console.log('Loaded CCTV sessions:', cctvSessions);
    } catch (error) {
      console.error('Failed to read or parse the latest JSON file:', error);
    }
  }
}

// Initialize sessions for all CCTV IDs
async function initializeSessions() {
  console.log('Initializing CCTV sessions...');

  try {
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

// Log server start and initialize sessions
console.log(`Server running on http://127.0.0.1:${PORT}`);
initializeSessions().then(() => {
  console.log('Session initialization completed.');
});

// Schedule the initializeSessions function to run every 15 minutes
schedule('*/15 * * * *', async () => {
  console.log('Running scheduled session initialization...');
  await initializeSessions();
});
