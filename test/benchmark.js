import http from 'k6/http';
import { sleep } from 'k6';

export let options = {
  stages: [
    { duration: '30s', target: 6000 }, // Ramp-up to 100 users over 30 seconds
    { duration: '10s', target: 0 },  // Stay at 100 users for 1 minute
    { duration: '30s', target: 0 },   // Ramp-down to 0 users
  ],
};

export default function () {
  http.get('http://127.0.0.1:8001/session_id?cctv_id=77');  // Replace with your server's endpoint
  sleep(1);
}

//k6 run ./test/benchmark.js