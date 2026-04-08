const express = require('express');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 8082;

app.use(cors());
app.use(express.json());

// Mock Products Database
const products = [
    { id: 1, name: "Neural Interface Headset", price: 299.99, stock: 45, image: "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=500&q=80" },
    { id: 2, name: "Quantum Processing Unit", price: 899.00, stock: 12, image: "https://images.unsplash.com/photo-1518770660439-4636190af475?w=500&q=80" },
    { id: 3, name: "Holographic Display Monitor", price: 450.50, stock: 30, image: "https://images.unsplash.com/photo-1527443154391-507e9dc6c5cc?w=500&q=80" },
    { id: 4, name: "Cybernetic Exo-Glove", price: 150.00, stock: 100, image: "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=500&q=80" },
    { id: 5, name: "Optical Data Drive", price: 89.99, stock: 200, image: "https://images.unsplash.com/photo-1600861194942-f883de0dfe96?w=500&q=80" },
    { id: 6, name: "Plasma Battery Pack", price: 120.00, stock: 85, image: "https://images.unsplash.com/photo-1593941707882-a5bba14938c7?w=500&q=80" }
];

// 1. Core Business Logic - Get all products
app.get('/api/products', (req, res) => {
    console.log("[INFO] Fetched product catalog.");
    res.json(products);
});

// 2. HEALTH ENDPOINT - CRITICAL FOR SELF-HEALING
app.get('/actuator/health', (req, res) => {
    // We use /actuator/health so the Health Monitor checks it like the Java services
    res.status(200).json({ status: "UP", service: "product-service" });
});

// 3. CHAOS ENDPOINT - intentionally crash the service to trigger the recovery manager
app.get('/api/products/crash', (req, res) => {
    console.error("[FATAL] Memory Overflow Simulation! Crashing the product-service IMMEDIATELY.");
    res.status(500).send("Crashing...");
    // Simulate a hard crash that exits the Node.js process (kills the container)
    setTimeout(() => {
        process.exit(1);
    }, 500);
});

app.listen(PORT, () => {
    console.log(`[READY] E-Commerce Product Service is running on port ${PORT}`);
});
