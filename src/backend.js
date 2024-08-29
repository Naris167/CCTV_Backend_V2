const express = require('express');
const axios = require('axios');

const app = express();
const port = 8001;

// Constants
const BASE_URL = 'http://www.bmatraffic.com';
const CCTV_LIST = ['7', '11', '481', '612', '1223']; // Example CCTV list

// Dictionary to store session IDs
const cctvSessions = {};

// Function to get a session ID for a specific CCTV ID
async function getCCTVSessionId(cctvId) {
    try {
        const response = await axios.get(BASE_URL);
        const cookie = response.headers['set-cookie'];
        if (cookie) {
            const sessionId = cookie[0].split('=')[1].split(';')[0];
            console.log(`[${cctvId}] Obtained session ID: ${sessionId}`);
            return sessionId;
        }
    } catch (error) {
        console.error(`[${cctvId}] Error getting session ID: ${error.message}`);
    }
    return null;
}

// Function to play video for a specific CCTV ID and session ID
async function playVideo(cctvId, sessionId) {
    const url = `${BASE_URL}/PlayVideo.aspx?ID=${cctvId}`;
    const headers = {
        'Referer': `${BASE_URL}/index.aspx`,
        'Cookie': `ASP.NET_SessionId=${sessionId};`,
        'Priority': 'u=4'
    };
    try {
        const response = await axios.get(url, { headers });
        console.log(`[${cctvId}] Playing video for session ID: ${sessionId}`);
    } catch (error) {
        console.error(`[${cctvId}] Error playing video: ${error.message}`);
    }
}

// Function to initialize session IDs for all CCTV IDs
async function initializeCCTVSessions() {
    for (const cctvId of CCTV_LIST) {
        const sessionId = await getCCTVSessionId(cctvId);
        if (sessionId) {
            cctvSessions[cctvId] = sessionId;
            await playVideo(cctvId, sessionId);
        }
    }
    console.log('All CCTV sessions initialized.');
}

// Endpoint to get session ID for a specific CCTV ID
app.get('/session_id', (req, res) => {
    const cctvId = req.query.cctv_id;
    const sessionId = cctvSessions[cctvId];
    if (sessionId) {
        res.json({ cctv_id: cctvId, session_id: sessionId });
    } else {
        res.status(404).json({ error: 'Session ID not found for the provided CCTV ID.' });
    }
});

// Initialize CCTV sessions and start the server
initializeCCTVSessions().then(() => {
    app.listen(port, () => {
        console.log(`Backend service running on http://127.0.0.1:${port}`);
    });
});
