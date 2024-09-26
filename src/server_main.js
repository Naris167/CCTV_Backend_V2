// bun run ./src/server_main.js

import { spawn } from 'child_process';
import os from 'os';
import fs from 'fs';
import path from 'path';
import { setupLogger, getLogger, resetLogger } from './server_logger.js';
import { getLatestJsonFile, deleteOldJsonFiles } from './server_json.js';
import { formatDate, calculateRuntime } from './server_utils.js';

const CONFIG = {
  PORT: 7000,
  CCTV: {
    jsonDirectory: './cctvSessionTemp/',
    jsonMaxAgeHours: 2400000000,
    updateCamInfoPath: './src/BMATraffic/main.py',
    cctvDistance: 170,
    updateInterval: 10 * 1 * 60 * 1000, // 10 minutes
  },
  LOGGING: {
    directory: './logs',
    toConsole: true,
    toFile: true,
    rotationInterval: 1 * 60 * 60 * 1000, // 1 hour
    logMaxAgeHours: 2400000000,
  },
};

// Global variables
let cctvSessions = {};
let latestUpdateTime, latestRefreshTime;
let logger, logStartTime;
let scheduledTimeout;
const serverAddressMap = new Map();

// Logger functions
function initializeLogger() {
  ({ logger, logStartTime } = setupLogger(CONFIG.LOGGING));
}

function checkLogRotationAndCleanup() {
  const now = Date.now();
  const rotationInterval = CONFIG.LOGGING.rotationInterval;
  const maxAge = CONFIG.LOGGING.logMaxAgeHours * 60 * 60 * 1000;

  if (now - logStartTime >= rotationInterval) {
    ({ logger, logStartTime } = resetLogger(CONFIG.LOGGING));
    logger.log('Logger reset at:', formatDate(logStartTime));
    printServerAddresses();
  }

  fs.readdirSync(CONFIG.LOGGING.directory).forEach(file => {
    const filePath = path.join(CONFIG.LOGGING.directory, file);
    if (now - fs.statSync(filePath).mtimeMs > maxAge) {
      fs.unlinkSync(filePath);
      logger.log(`Deleted old log file: ${file}`);
    }
  });
}

// CCTV functions
async function initializeSessions() {
  logger.log('Initializing CCTV sessions...');
  try {
    checkLogRotationAndCleanup();
    await startUpdate();
    loadCctvSessions();
    logger.log('All sessions initialized.');
  } catch (error) {
    logger.error('Failed to initialize sessions:', error);
  }
}

function startUpdate() {
  return new Promise((resolve, reject) => {
    logger.log('\n############### Starting Python Script ###############\n');
    const pythonProcess = spawn('python', [CONFIG.CCTV.updateCamInfoPath, CONFIG.CCTV.cctvDistance]);

    pythonProcess.stdout.on('data', data => logger.log('[PY]', data.toString()));
    pythonProcess.stderr.on('data', data => logger.error('[PY]', data.toString()));

    pythonProcess.on('close', code => {
      logger.log(`Python script exited with code ${code}`);
      logger.log('\n############### End of Python Script ###############\n');
      code === 0 ? resolve() : reject(`Python process exited with code ${code}`);
    });
  });
}

function loadCctvSessions() {
  deleteOldJsonFiles(CONFIG.CCTV, logger);
  const latestFile = getLatestJsonFile(CONFIG.CCTV, logger);

  if (latestFile) {
    try {
      const { cctvSessions: sessions, latestUpdateTime: updateTime, latestRefreshTime: refreshTime } = 
        JSON.parse(fs.readFileSync(latestFile, 'utf8'));

      cctvSessions = sessions;
      latestUpdateTime = updateTime;
      latestRefreshTime = refreshTime;

      logger.log('Loaded CCTV sessions:', cctvSessions);
      logger.log('Latest update time:', latestUpdateTime);
      logger.log('Latest refresh time:', latestRefreshTime);
    } catch (error) {
      logger.error('Failed to read or parse the latest JSON file:', error);
    }
  }
}

function scheduleNextExecution() {
  if (scheduledTimeout) {
    clearTimeout(scheduledTimeout);
  }

  scheduledTimeout = setTimeout(async () => {
    logger.log('Running scheduled session initialization...');
    await initializeSessions();
    scheduleNextExecution();
  }, CONFIG.CCTV.updateInterval);
}

// Server functions
function startServer() {
  Bun.serve({
    port: CONFIG.PORT,
    fetch: handleRequest,
    error: handleError,
  });

  function handleRequest(req) {
    const url = new URL(req.url);

    // https://flood-innotech.gistda.or.th/cctv_session?cctv_id=7
    if (url.pathname === '/session_id') {
      return handleSessionIdRequest(url);
    }

    // https://flood-innotech.gistda.or.th/cctv_data?cctv_id=7
    // if (url.pathname === '/cctv_data') {
    //   return handleCCTVDataRequest(url);
    // }

    return new Response('Not found', { status: 404 });
  }
  
  // This is old function to handle request for BMA CCTV
  function handleSessionIdRequest(url) {
    const cameraID = url.searchParams.get('cctv_id');
    logger.log(`User requested CCTV: ${cameraID}`);
    const sessionID = cctvSessions[cameraID];
    if (sessionID) {
      return new Response(JSON.stringify({ cctv_id: cameraID, session_id: sessionID }), {
        headers: { 'Content-Type': 'application/json' },
      });
    } else {
      logger.log(`Session ID not found for the given CCTV ID: ${cameraID}`);
      return new Response(JSON.stringify({ error: 'Session ID not found for the given CCTV ID' }), { status: 404 });
    }
  }

  // Updated function to handle request
  // https://flood-innotech.gistda.or.th/cctv_data?id=7&owner=BMA&host=BMA
  // function handleCCTVDataRequest(url) {
  //   const cameraID = url.searchParams.get('id');
  //   const owner = url.searchParams.get('owner');
  //   const host = url.searchParams.get('host');
    
  //   logger.log(`User requested CCTV ID: ${cameraID}, Owner: ${owner}, Host: ${host}`);
    

  //   const sessionID = cctvSessions[cameraID];
    
  //   if (sessionID) {
  //     return new Response(JSON.stringify({ cctv_id: cameraID, session_id: sessionID }), {
  //       headers: { 'Content-Type': 'application/json' },
  //     });
  //   } else {
  //     logger.log(`Session ID not found for the given CCTV ID: ${cameraID}`);
  //     return new Response(JSON.stringify({ error: 'Session ID not found for the given CCTV ID' }), { status: 404 });
  //   }

  // }

  
  function handleError(err) {
    logger.error(err);
  }

  collectServerAddresses(CONFIG.PORT);
  printServerAddresses();

}



// Address tracking functions
function collectServerAddresses(port) {
  const now = Date.now();
  Object.values(os.networkInterfaces()).flat().forEach(({ family, internal, address }) => {
    if (family === 'IPv4' && !internal) {
      const fullAddress = `http://${address}:${port}`;
      serverAddressMap.set(fullAddress, now);
    }
  });
}

function printServerAddresses() {
  if (serverAddressMap.size === 0) {
    logger.log('No external IPv4 addresses found.');
  } else {
    serverAddressMap.forEach((startTime, address) => {
      const formattedStartTime = formatDate(startTime);
      const runtime = calculateRuntime(startTime);
      logger.log(`Server running on: ${address} (started at ${formattedStartTime}, running for ${runtime})`);
    });
  }
}

// Main execution
async function main() {
  initializeLogger();
  
  try {
    await initializeSessions();
    logger.log('Session initialization completed.');
    scheduleNextExecution();
    
    startServer();
    logger.log('Server started successfully.');
  } catch (error) {
    logger.error('Failed to initialize sessions:', error);
    logger.log('Server start aborted due to initialization failure.');
    process.exit(1);
  }
}

// Using top-level await (assuming your environment supports it)
await main();