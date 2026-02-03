import http from 'k6/http';
import { check } from 'k6';

export let options = {
    scenarios: {
        stress_test: {
            executor: 'ramping-arrival-rate',
            startRate: 10,
            timeUnit: '1s',
            preAllocatedVUs: 10000,
            maxVUs: 15000,
            stages: [
                { duration: '30s', target: 600 }, // Ramp to 600 RPS
                { duration: '1m', target: 600 },  // Hold at 600 RPS
                { duration: '30s', target: 0 },   // Ramp down
            ],
        },
    },
    thresholds: {
        http_req_duration: ['p(95)<2000'],
        http_req_failed: ['rate<0.05'],
    },
};

export default function () {
    const BASE_URL = 'https://swarm.getlinked.ai/api/v1/';
    const endpoint = 'candidate-answers';

    // Optional: Add query params to verify filtering performance
    // const params = ?candidate=candidate_${__VU};
    // const res = http.get(${BASE_URL}${endpoint}${params}, {

    const params = {
        headers: {
            'Content-Type': 'application/json',
            'Proctor-Env': 'loadtest'
        },
    };

    // Send the GET request
    const res = http.get(`${BASE_URL}${endpoint}`, params);

    // Assertions to check the response
    check(res, {
        'status is 200': (r) => r.status === 200,
        'response time < 2000ms': (r) => r.timings.duration < 2000,
    });
}

