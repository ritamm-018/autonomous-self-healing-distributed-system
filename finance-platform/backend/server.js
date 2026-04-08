const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const authRoutes = require('./routes/auth');
const tradeRoutes = require('./routes/trade');
const paymentRoutes = require('./routes/payment');
const chaosRoutes = require('./routes/chaos');
const simulator = require('./load-generator/simulator');

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

// Main Routes
app.use('/api/auth', authRoutes);
app.use('/api/trade', tradeRoutes);
app.use('/api/payment', paymentRoutes);
app.use('/api/chaos', chaosRoutes);

// Load Generator Endpoints
app.post('/api/load/users', async (req, res) => {
    const { count } = req.body;
    simulator.generateUsers(count || 100);
    res.status(200).json({ message: `Generating ${count} users in background...` });
});

app.post('/api/load/continuous', (req, res) => {
    const { rate } = req.body;
    simulator.startContinuousLoad(rate || 10);
    res.status(200).json({ message: `Started continuous load at ${rate} req/sec` });
});

app.post('/api/load/stop', (req, res) => {
    simulator.stopAll();
    res.status(200).json({ message: 'Stopped all background load tasks' });
});

// Basic Health Check
app.get('/health', (req, res) => {
    res.status(200).json({ status: 'Load Simulator Backend is Running' });
});

app.listen(PORT, () => {
    console.log(`Finance Platform Backend running on http://localhost:${PORT}`);
    console.log(`Routing traffic to Gateway at: ${process.env.API_BASE_URL || 'http://localhost:8080'}`);
});
