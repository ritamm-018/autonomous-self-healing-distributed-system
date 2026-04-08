const express = require('express');
const router = express.Router();
const gatewayClient = require('../services/gatewayClient');

// These endpoints directly hammer the Java Chaos endpoints on the backend data-service

// Kill Data Service
router.post('/kill-data', async (req, res) => {
    try {
        await gatewayClient.get('/data/kill');
        res.status(200).json({ message: "Kill signal sent to data service" });
    } catch (error) {
        // We expect it to fail/timeout since the service gets killed
        res.status(200).json({ message: "Kill signal sent to data service (service is now down)" });
    }
});

// Add 5s Latency
router.post('/latency-data', async (req, res) => {
    try {
        const response = await gatewayClient.get('/data/latency');
        res.status(200).json(response.data);
    } catch (error) {
        res.status(500).json({ error: "Failed to apply latency", details: error.message });
    }
});

// Simulate API Storm (10,000 requests)
router.post('/api-storm', async (req, res) => {
    const promises = [];
    // Sending 1,000 requests concurrently to stress the gateway (adjusting to 1k locally for memory safety, can be triggered 10x)
    for (let i = 0; i < 1000; i++) {
        promises.push(gatewayClient.get('/data/items').catch(() => {}));
    }
    
    // Don't wait for all to finish, respond immediately
    Promise.all(promises);
    res.status(200).json({ message: "Triggered 1000 concurrent API requests to /data/items" });
});

// Crash random service (we'll just target data service for now, as it has the kill endpoint)
router.post('/crash-random', async (req, res) => {
    try {
        await gatewayClient.get('/data/kill');
        res.status(200).json({ message: "Random service crash signal sent" });
    } catch (error) {
        res.status(200).json({ message: "Random service crash signal sent (service is down)" });
    }
});

module.exports = router;
