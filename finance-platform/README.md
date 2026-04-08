# Aegis Finance Platform - Stress Testing Interface

This is an advanced, visually stunning Financial Simulation Platform designed explicitly to act as a **Load Generator and testing bench** for the **Autonomous Self-Healing Distributed System**.

## Why does this exist?
The core Java microservices system is a backend powerhouse that detects and heals its own failures. However, to see it in action, you need **traffic**, **real-world scenarios**, and a **Chaos Engineering** control panel. This project provides that.

## Features
- **Trading Dashboard**: Simulates thousands of real-time transactions to hammer the `Data Service`.
- **Chaos Engineering Control Panel**: Direct buttons to assassinate the Java `Data Service`, inject latency, and crash nodes.
- **Autonomous Recovery Timeline**: A live 3D visualized dashboard connecting straight to the `Health Monitor` to watch the self-healing algorithm kick in.

## Architecture & Integration
### 1. The Gateway Mandate
*This is the most critical feature.* The React Frontend **never** talks to the microservices directly. 
Frontend `<--->` Node.js Proxy Simulator `<--->` Java Gateway (Port 8080) `<--->` Protected Microservices.

Every trade, payment, and simulated user flows strictly through `http://localhost:8080`.

## How to Run
1. **Ensure the Java Backend is Running** (`docker compose up -d` in the root).
2. **Start the Node Load Simulator (Backend)**:
   ```bash
   cd backend
   npm install
   node server.js
   ```
   *Runs on port 5000*
3. **Start the React Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   *Runs on Vite's default port (usually 5173).*

Open your browser to the local Vite address and begin triggering Chaos!
