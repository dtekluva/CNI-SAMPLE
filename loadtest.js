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
                { duration: '30s', target: 300 }, // Ramp to 300 RPS
                { duration: '1m', target: 300 },  // Hold at 300 RPS
                { duration: '30s', target: 0 },   // Ramp down
            ],
        },
    },
    thresholds: {
        http_req_duration: ['p(95)<2000'], // Adjusted threshold based on observed latency
        http_req_failed: ['rate<0.05'],
    },
};

export default function () {
    const BASE_URL = 'https://swarm.getlinked.ai/api/v1/';
    const endpoint = 'candidate-answers';

    // JSON payload for the POST request
    const payload = JSON.stringify({
        candidate: "candidate_" + __VU,
        invite_id: "invite_" + __VU,
        question: "question_" + __VU,
        answer: "This is a test answer from load test",
        section_id: "section_id_1"
    });

    const params = {
        headers: {
            'Content-Type': 'application/json',
            'Proctor-Env': 'loadtest'
        },
    };

    // Send the POST request
    const res = http.post(`${BASE_URL}${endpoint}`, payload, params);

    // Assertions to check the response
    check(res, {
        'status is 200': (r) => r.status === 200, // Check for success response
        'response time < 1000ms': (r) => r.timings.duration < 1000, // Ensure quick response
    });
}

