const express = require('express');
const router = express.Router();
const gatewayClient = require('../services/gatewayClient');

router.post('/', async (req, res) => {
    try {
        // Simulated payment logic mapping to data-service items
        const paymentData = {
            name: `PAYMENT-${req.body.recipient}`,
            description: `Transferred ${req.body.amount} USD`
        };
        const response = await gatewayClient.post('/data/items', paymentData);
        res.status(201).json({ message: "Payment sent", transaction: response.data });
    } catch (error) {
        res.status(error.response?.status || 500).json({ error: "Payment failed", details: error.message });
    }
});

router.get('/', async (req, res) => {
    try {
        const response = await gatewayClient.get('/data/items');
        res.status(200).json({ payments: response.data });
    } catch (error) {
        res.status(error.response?.status || 500).json({ error: "Failed to fetch payments", details: error.message });
    }
});

module.exports = router;
