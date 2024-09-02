const express = require('express');
const axios = require('axios');
const cron = require('node-cron');
const { spawn } = require('child_process');
const http = require('http');
const https = require('https');

const app = express();
const PORT = 8001;
const BASE_URL = "http://www.bmatraffic.com"; // Replace with the actual base URL

// Disable connection reuse by creating custom agents
const httpAgent = new http.Agent({ keepAlive: false });
const httpsAgent = new https.Agent({ keepAlive: false });

// Dictionary to store session IDs for each CCTV ID
const cctvSessions = {};

// Function to start the Python script and get CCTV IDs
function startUpdate() {
  return new Promise((resolve, reject) => {
      console.error(`Calling Python script...`);
      const pythonProcess = spawn('python', ['./src/updateCamInfo.py', '170']); // Run Python script with argument

      let result = '';
      pythonProcess.stdout.on('data', (data) => {
          result += data.toString();
      });

      pythonProcess.stderr.on('data', (data) => {
          console.error('Error from Python script:', data.toString());
      });

      pythonProcess.on('close', (code) => {
          console.log(`\n\nPython script exited with code ${code}`);
          console.log(`Full result from Python script:\n${result}`); // Debug print to see the full result
          console.log(`\n############### Ended of Python script ###############\n\n`);

          if (code === 0) {
              try {
                  // Split the output by newlines and take the last non-empty line
                  const lines = result.trim().split('\n');
                  const jsonString = lines[lines.length - 1]; // Get the last line
                  
                  // console.log(`Extracted JSON string: ${jsonString}`); // Debug print to check the extracted JSON string

                  const cctvList = JSON.parse(jsonString);  // Attempt to parse the JSON string to an array
                  resolve(cctvList);
              } catch (error) {
                  console.error('Failed to parse CCTV IDs:', error);
                  reject('Failed to parse CCTV IDs');
              }
          } else {
              reject(`Python process exited with code ${code}`);
          }
      });
  });
}

// Function to get session ID for a specific camera
async function getCCTVSessionID(cameraID) {
  try {
    // Make a request with a new connection every time
    const response = await axios.get(`${BASE_URL}`, {
      timeout: 60000,
      httpAgent,  // Use custom HTTP agent
      httpsAgent, // Use custom HTTPS agent
    });
    const cookie = response.headers['set-cookie'];
    if (cookie) {
      const sessionID = cookie[0].split('=')[1].split(';')[0];
      console.log(`[${cameraID}] Obtained session ID: ${sessionID}`);
      return sessionID;
    }
    return null;
  } catch (error) {
    console.error(`[${cameraID}] Error getting session ID: ${error.message}`);
    return null;
  }
}

// Function to play video for a camera session
async function playVideo(cameraID, sessionID) {
  const url = `${BASE_URL}/PlayVideo.aspx?ID=${cameraID}`;
  const headers = {
    'Referer': `${BASE_URL}/index.aspx`,
    'Cookie': `ASP.NET_SessionId=${sessionID};`,
    'Priority': 'u=4'
  };

  try {
    // Make a request with a new connection every time
    await axios.get(url, {
      headers,
      httpAgent,  // Use custom HTTP agent
      httpsAgent, // Use custom HTTPS agent
    });
    console.log(`[${cameraID}] Playing video for session ID: ${sessionID}`);
  } catch (error) {
    console.error(`[${cameraID}] Error playing video: ${error.message}`);
  }
}

// Initialize sessions for all CCTV IDs concurrently
async function initializeSessions() {
  console.log('Initializing CCTV sessions...');

  try {
    const CCTV_LIST = await startUpdate(); // Dynamically fetch the CCTV list using the Python script
    console.log('CCTV IDs fetched from Python script:', CCTV_LIST);
    console.log(`\n\nStart scraping...\n`);
    
    // Create an array of promises for session initialization
    const sessionPromises = CCTV_LIST.map(async (cameraID) => {
      const sessionID = await getCCTVSessionID(cameraID);
      if (sessionID) {
        await playVideo(cameraID, sessionID);
        cctvSessions[cameraID] = sessionID;
      }
    });

    // Wait for all promises to resolve
    await Promise.all(sessionPromises);
    
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
