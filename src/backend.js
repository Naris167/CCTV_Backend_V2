const express = require('express');
const cron = require('node-cron');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const { format } = require('date-fns'); // Library for date formatting

const app = express();
const PORT = 8001;

// Dictionary to store session IDs for each CCTV ID
let cctvSessions = {};

// Function to set up logging to both console and a file
function setupLogger() {
    // Define the directory and log file path
    const logDirectory = path.join(__dirname, 'logs');
    const timestamp = format(new Date(), 'yyyy-MM-dd_HH-mm-ss');
    const logFile = path.join(logDirectory, `backend_${timestamp}.log`);

    // Check if the directory exists, if not, create it
    if (!fs.existsSync(logDirectory)) {
        fs.mkdirSync(logDirectory, { recursive: true });
    }

    // Create a write stream (append mode) for logging
    const logStream = fs.createWriteStream(logFile, { flags: 'a' });

    // Save original console methods
    const originalLog = console.log;
    const originalError = console.error;

    // Override console.log
    console.log = function (...args) {
        originalLog.apply(console, args); // Output to console
        logStream.write(getFormattedLog(args) + '\n'); // Write to log file
    };

    // Override console.error
    console.error = function (...args) {
        originalError.apply(console, args); // Output to console
        logStream.write(getFormattedLog(args) + '\n'); // Write to log file
    };

    // Helper function to format log messages with a timestamp
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
    console.log(`Calling Python script...`);
    const pythonProcess = spawn('python', ['./src/updateCamInfo.py', '170']); // Run Python script with argument

    pythonProcess.stdout.on('data', (data) => {
      console.log('Python script output:', data.toString()); // Output log messages to stdout
    });

    pythonProcess.stderr.on('data', (data) => {
      console.error('[PY]', data.toString()); // Handles actual errors
    });

    pythonProcess.on('close', (code) => {
      console.log(`\n\nPython script exited with code ${code}`);
      console.log(`\n############### End of Python script ###############\n\n`);

      if (code === 0) {
        resolve(); // Resolve once the Python script has completed
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
    await startUpdate(); // Wait for Python script to complete
    loadCctvSessions(); // Load the latest CCTV sessions from the JSON file
    console.log('All sessions initialized.');
  } catch (error) {
    console.error('Failed to initialize sessions:', error);
  }
}

// Endpoint to return the session ID for a given CCTV ID
app.get('/session_id', (req, res) => {
  const cameraID = req.query.cctv_id;
  console.log(`User requested CCTV: ${cameraID}`);
  const sessionID = cctvSessions[cameraID];
  if (sessionID) {
    res.json({ cctv_id: cameraID, session_id: sessionID });
  } else {
    console.log(`Session ID not found for the given CCTV ID`);
    res.status(404).json({ error: 'Session ID not found for the given CCTV ID' });
  }
});

// Start the server
app.listen(PORT, async () => {
  console.log(`Server running on http://127.0.0.1:${PORT}`);
  await initializeSessions(); // Initial session initialization
  console.log('Session initialization completed.');
});

// Schedule the initializeSessions function to run every 15 minutes
cron.schedule('*/15 * * * *', async () => {
  console.log('Running scheduled session initialization...');
  await initializeSessions();
});
