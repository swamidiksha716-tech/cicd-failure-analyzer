// server.test.js
// Standard supertest + jest pattern: spin up the Express app in-memory
// (no real network port) and send it fake HTTP requests.

const request = require('supertest');
const app = require('../server');

describe('GET /', () => {
  it('returns 200', async () => {
    const res = await request(app).get('/');
    expect(res.statusCode).toBe(200);
    
  });
});

describe('GET /health', () => {
  it('returns ok', async () => {
    const res = await request(app).get('/health');
    expect(res.statusCode).toBe(200);
    expect(res.body.status).toBe('ok');
  });
});

// --- DEMO_FAILURE ---
// This test is intentionally commented out. Uncomment it, commit, and
// push to deliberately break the pipeline so you can watch the whole
// Failure Analyzer flow run end-to-end (see README "Triggering a demo
// failure"). Leave it commented out for normal/healthy builds.
//
// describe('GET /nonexistent', () => {
//   it('should not exist, but we assert it does (forces a failure)', async () => {
//     const res = await request(app).get('/nonexistent');
//     expect(res.statusCode).toBe(200); // will actually be 404 -> fails
//   });
// });