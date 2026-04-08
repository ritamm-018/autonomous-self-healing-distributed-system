const axios = require('axios');
const dotenv = require('dotenv');

dotenv.config();

// The core requirement: ALL requests MUST go through the Gateway at port 8080
const GATEWAY_URL = process.env.API_BASE_URL || 'http://localhost:8080';

const gatewayClient = axios.create({
    baseURL: GATEWAY_URL,
    timeout: 10000, 
});

// Interceptor to attach JWT token if present
gatewayClient.interceptors.request.use((config) => {
    // In a real app, you'd extract from auth context. For the simulator, 
    // we can just optionally pass it in headers manually or from req.headers.authorization
    return config;
});

module.exports = gatewayClient;
