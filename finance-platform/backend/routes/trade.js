const express = require('express');
const router = express.Router();
const gatewayClient = require('../services/gatewayClient');

// Since our original Data Service is just a basic CRUD (/data/items), 
// we will map trading concepts to it for the simulation.
// e.g., POST /data/trade -> creates an "item" representing a trade
// GET /data/portfolio -> gets all "items" 

router.post('/trade', async (req, res) => {
    try {
        // Creating a simulated trade record
        const tradeData = {
            name: `TRADE-${req.body.symbol}`,
            description: `BUY ${req.body.amount} at ${req.body.price}`
        };
        const response = await gatewayClient.post('/data/items', tradeData);
        res.status(201).json({ message: "Trade executed", data: response.data });
    } catch (error) {
        res.status(error.response?.status || 500).json({ error: "Trade failed", details: error.message });
    }
});

router.get('/portfolio', async (req, res) => {
    try {
        const response = await gatewayClient.get('/data/items');
        res.status(200).json({ portfolio: response.data });
    } catch (error) {
        res.status(error.response?.status || 500).json({ error: "Failed to fetch portfolio", details: error.message });
    }
});

router.get('/transactions', async (req, res) => {
    try {
        const response = await gatewayClient.get('/data/items');
        res.status(200).json({ transactions: response.data });
    } catch (error) {
        res.status(error.response?.status || 500).json({ error: "Failed to fetch transactions", details: error.message });
    }
});

module.exports = router;
