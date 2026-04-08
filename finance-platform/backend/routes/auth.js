const express = require('express');
const router = express.Router();
const gatewayClient = require('../services/gatewayClient');

router.post('/login', async (req, res) => {
    try {
        const response = await gatewayClient.post('/auth/login', req.body);
        res.status(200).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json({ error: error.message });
    }
});

router.post('/register', async (req, res) => {
    try {
        // Since Auth Service in the original only has login/token (simulated), 
        // we'll hit the same or simulate registration
        // We will default to calling /auth/token for the token generation
        const response = await gatewayClient.post('/auth/token', { username: req.body.username });
        res.status(200).json({ message: "Registration successful", token: response.data });
    } catch (error) {
        res.status(error.response?.status || 500).json({ error: error.message });
    }
});

module.exports = router;
