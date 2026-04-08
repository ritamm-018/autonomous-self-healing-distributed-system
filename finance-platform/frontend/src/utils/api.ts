import axios from 'axios';

// With Vite proxy configured, all /api calls go to Node.js automatically (no CORS)
const api = axios.create({
    baseURL: '/api',
    timeout: 30000,
});

export const tradeApi = {
    executeTrade: (data: { symbol: string, amount: number, price: number }) => api.post('/trade', data),
    getPortfolio: () => api.get('/trade/portfolio'),
    getTransactions: () => api.get('/trade/transactions'),
};

export const paymentApi = {
    sendPayment: (data: { recipient: string, amount: number }) => api.post('/payment', data),
    getPayments: () => api.get('/payment'),
};

export const chaosApi = {
    killDataService: () => api.post('/chaos/kill-data'),
    addLatency: () => api.post('/chaos/latency-data'),
    apiStorm: () => api.post('/chaos/api-storm'),
    crashRandom: () => api.post('/chaos/crash-random'),
};

export const loadApi = {
    generateUsers: (count: number) => api.post('/load/users', { count }),
    startContinuousLoad: (rate: number) => api.post('/load/continuous', { rate }),
    stopContinuousLoad: () => api.post('/load/stop'),
};

// Health checks go through the /gateway proxy -> Java directly
export const healthApi = {
    checkGateway: () => fetch('/gateway/actuator/health').then(r => r.json()),
    checkDataService: () => fetch('/gateway/data/items').then(r => r.ok ? 'UP' : 'DOWN').catch(() => 'DOWN'),
};

export default api;
