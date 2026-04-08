const gatewayClient = require('../services/gatewayClient');

class LoadSimulator {
    constructor() {
        this.activeSimulations = false;
        this.intervals = [];
    }

    async generateUsers(count) {
        console.log(`Generating ${count} simulated users...`);
        const promises = [];
        for (let i = 0; i < count; i++) {
            // Send requests concurrently across Auth and Data endpoints
            promises.push(gatewayClient.get('/data/items').catch(() => {}));
            if (i % 2 === 0) {
                promises.push(gatewayClient.post('/auth/token', { username: `user_${i}` }).catch(() => {}));
            }
        }
        await Promise.all(promises);
        console.log(`Generated ${count} users successfully.`);
    }

    startContinuousLoad(ratePerSecond = 10) {
        this.activeSimulations = true;
        
        const interval = setInterval(async () => {
            const promises = [];
            for(let i=0; i < ratePerSecond; i++) {
                promises.push(gatewayClient.get('/data/items').catch(()=>{}));
            }
            await Promise.all(promises);
            console.log(`Sent ${ratePerSecond} background requests`);
        }, 1000);

        this.intervals.push(interval);
    }

    stopAll() {
        this.activeSimulations = false;
        this.intervals.forEach(clearInterval);
        this.intervals = [];
        console.log("Stopped all simulations.");
    }
}

module.exports = new LoadSimulator();
