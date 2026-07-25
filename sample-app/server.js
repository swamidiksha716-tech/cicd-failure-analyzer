// server.js
// A minimal Express app. This is the thing our CI/CD pipeline builds,
// tests, and deploys. It's deliberately simple — the point of this
// project is the pipeline and failure-analysis around it, not the app.

const express = require('express');
const app = express();

app.get('/', (req, res) => {
  res.status(200).json({
    message: 'CI/CD Failure Analyzer demo app is running',
    status: 'healthy',
  });
});

// A health check endpoint — real deployment pipelines almost always
// have one of these, so a load balancer / Amplify can confirm the
// app actually started before routing traffic to it.
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok' });
});

const PORT = process.env.PORT || 3000;

// Only start listening if this file is run directly (not when required
// by a test file) — a common Node pattern so tests can import the app
// without accidentally binding a port.
if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
  });
}

module.exports = app;
