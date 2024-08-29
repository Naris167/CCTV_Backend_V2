const express = require('express');
const axios = require('axios');
const cron = require('node-cron');

const app = express();
const PORT = 8001;
const BASE_URL = "http://www.bmatraffic.com"; // Replace with the actual base URL

// CCTV ID list
const CCTV_LIST = ['7', '11', '481', '612', '1223'];

// Dictionary to store session IDs for each CCTV ID
const cctvSessions = {};

// Function to get session ID for a specific camera
async function getCCTVSessionID(cameraID) {
  try {
    const response = await axios.get(`${BASE_URL}`, { timeout: 60000 });
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
    await axios.get(url, { headers });
    console.log(`[${cameraID}] Playing video for session ID: ${sessionID}`);
  } catch (error) {
    console.error(`[${cameraID}] Error playing video: ${error.message}`);
  }
}

// Initialize sessions for all CCTV IDs concurrently
async function initializeSessions() {
  console.log('Initializing CCTV sessions...');
  
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
}

// Endpoint to return the session ID for a given CCTV ID
app.get('/session_id', (req, res) => {
  const cameraID = req.query.cctv_id;
  console.log(`user requested cctv: ${cameraID}`);
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
