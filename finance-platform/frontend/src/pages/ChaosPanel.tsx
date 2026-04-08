import React, { useState } from 'react';
import { chaosApi, loadApi } from '../utils/api';
import { AlertOctagon, Skull, Zap, Activity, Bug } from 'lucide-react';
import { motion } from 'framer-motion';

const ChaosPanel = () => {
    const [loading, setLoading] = useState<string | null>(null);
    const [logs, setLogs] = useState<string[]>([]);

    const addLog = (msg: string) => setLogs(prev => [msg, ...prev].slice(0, 10));

    const handleChaos = async (action: string, apiCall: () => Promise<any>) => {
        setLoading(action);
        addLog(`[SENT] Triggering ${action}...`);
        try {
            const res = await apiCall();
            addLog(`[RECV] ${res.data.message || 'Success'}`);
        } catch (err: any) {
            addLog(`[ERROR] ${err.message}. Connection refused or timeout (Expected during chaos)`);
        } finally {
            setLoading(null);
        }
    };

    return (
        <div className="space-y-6 pt-6">
            <header>
                <h2 className="text-3xl font-bold flex items-center gap-3">
                    <ShieldAlert className="text-red-500"/> Chaos Engineering Protocol
                </h2>
                <p className="text-gray-400 mt-2">Intentionally fracture the system to demonstrate Autonomous Self-Healing capabilities.</p>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                
                {/* DESTRUCTIVE ACTIONS */}
                <motion.div initial={{scale:0.95, opacity:0}} animate={{scale:1, opacity:1}} className="glass-panel border-red-500/30 p-6 flex flex-col gap-4 relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-red-500/10 rounded-full blur-3xl -mr-10 -mt-10"></div>
                    <h3 className="text-xl font-bold text-red-400 flex items-center gap-2"><Skull size={20}/> Destructive Interventions</h3>
                    
                    <button 
                        onClick={() => handleChaos('Kill Data Service', chaosApi.killDataService)}
                        disabled={loading !== null}
                        className="bg-red-950/40 hover:bg-red-900/60 border border-red-500/50 p-4 rounded text-left transition-all"
                    >
                        <div className="font-bold text-red-200">Kill Data Service Container</div>
                        <div className="text-xs text-red-400/80 mt-1">Executes System.exit(1) on the backend worker. Health monitor will detect.</div>
                    </button>
                    
                    <button 
                        onClick={() => handleChaos('Crash Random Service', chaosApi.crashRandom)}
                        disabled={loading !== null}
                        className="bg-orange-950/40 hover:bg-orange-900/60 border border-orange-500/50 p-4 rounded text-left transition-all"
                    >
                        <div className="font-bold text-orange-200">Terminate Random Node</div>
                        <div className="text-xs text-orange-400/80 mt-1">Simulates unexpected SIGKILL on a random active microservice.</div>
                    </button>
                </motion.div>

                {/* NETWORK CHAOS */}
                <motion.div initial={{scale:0.95, opacity:0}} animate={{scale:1, opacity:1}} transition={{delay:0.1}} className="glass-panel border-yellow-500/30 p-6 flex flex-col gap-4 relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-yellow-500/10 rounded-full blur-3xl -mr-10 -mt-10"></div>
                    <h3 className="text-xl font-bold text-yellow-400 flex items-center gap-2"><Activity size={20}/> Network Anomalies</h3>
                    
                    <button 
                        onClick={() => handleChaos('Inject 5s Latency', chaosApi.addLatency)}
                        disabled={loading !== null}
                        className="bg-yellow-950/40 hover:bg-yellow-900/60 border border-yellow-500/50 p-4 rounded text-left transition-all"
                    >
                        <div className="font-bold text-yellow-200">Inject 5000ms Latency Map</div>
                        <div className="text-xs text-yellow-400/80 mt-1">Forces HTTP requests to timeout against the Istio/Gateway configurations.</div>
                    </button>
                </motion.div>

                {/* LOAD SIMULATION */}
                <motion.div initial={{scale:0.95, opacity:0}} animate={{scale:1, opacity:1}} transition={{delay:0.2}} className="glass-panel border-blue-500/30 p-6 flex flex-col gap-4 relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/10 rounded-full blur-3xl -mr-10 -mt-10"></div>
                    <h3 className="text-xl font-bold text-blue-400 flex items-center gap-2"><Zap size={20}/> Stress Generators</h3>
                    
                    <button 
                        onClick={() => handleChaos('Simulate API Storm', chaosApi.apiStorm)}
                        disabled={loading !== null}
                        className="bg-blue-950/40 hover:bg-blue-900/60 border border-blue-500/50 p-4 rounded text-left transition-all"
                    >
                        <div className="font-bold text-blue-200">Gateway Request Storm</div>
                        <div className="text-xs text-blue-400/80 mt-1">Hammer the Gateway port 8080 with thousands of immediate concurrent requests.</div>
                    </button>
                    
                    <div className="grid grid-cols-2 gap-2 mt-2">
                        <button onClick={() => handleChaos('Gen 1K Traffic', () => loadApi.generateUsers(1000))} className="bg-cyan-950/40 border border-cyan-500/30 p-2 rounded text-sm text-center hover:bg-cyan-900/60 transition-all text-cyan-200">Spike 1K Users</button>
                        <button onClick={() => handleChaos('Continuous Load', () => loadApi.startContinuousLoad(25))} className="bg-cyan-950/40 border border-cyan-500/30 p-2 rounded text-sm text-center hover:bg-cyan-900/60 transition-all text-cyan-200">Cont. Load (25/s)</button>
                        <button onClick={() => handleChaos('Stop Load', loadApi.stopContinuousLoad)} className="col-span-2 bg-slate-800/80 border border-slate-600 p-2 rounded text-sm text-center hover:bg-slate-700 transition-all">Halt Background Traffic</button>
                    </div>
                </motion.div>

                {/* TERMINAL LOG */}
                <motion.div initial={{opacity:0}} animate={{opacity:1}} transition={{delay:0.3}} className="lg:col-span-3 glass-panel p-4 bg-[#050505]">
                    <h3 className="text-sm font-mono text-gray-400 mb-2 flex items-center gap-2"><Bug size={14}/> Node.js Proxy Execute Logs</h3>
                    <div className="h-48 overflow-y-auto font-mono text-sm space-y-1">
                        {logs.map((log, i) => (
                            <div key={i} className={`${log.includes('ERROR') ? 'text-red-400' : 'text-green-400'}`}>
                                <span className="text-gray-600">[{new Date().toLocaleTimeString()}]</span> {log}
                            </div>
                        ))}
                    </div>
                </motion.div>

            </div>
        </div>
    );
};

// Add ShieldAlert since it's used in the header 
import { ShieldAlert } from 'lucide-react';
export default ChaosPanel;
