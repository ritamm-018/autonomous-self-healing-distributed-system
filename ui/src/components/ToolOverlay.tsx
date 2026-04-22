import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useSystemStore } from '../store'
import { 
    X, Shield, Database, Activity, 
    RefreshCcw, FileText, AlertTriangle,
    CheckCircle2, Terminal, Bug
} from 'lucide-react'

export const ToolOverlay = () => {
    const { activeTool, setActiveTool } = useSystemStore()

    if (!activeTool) return null

    const getContent = () => {
        switch (activeTool) {
            case 'auth':
                return (
                    <div className="space-y-4">
                        <div className="flex items-center gap-3 text-blue-400 mb-4">
                            <Shield size={24} />
                            <h2 className="text-xl font-display uppercase tracking-wider">Auth Intelligence</h2>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="bg-white/5 p-3 rounded border border-white/10 text-center">
                                <div className="text-xs text-gray-400 uppercase">Active Sessions</div>
                                <div className="text-2xl font-mono text-blue-400">1,284</div>
                            </div>
                            <div className="bg-white/5 p-3 rounded border border-white/10 text-center">
                                <div className="text-xs text-gray-400 uppercase">Auth Success</div>
                                <div className="text-2xl font-mono text-green-400">99.9%</div>
                            </div>
                        </div>
                        <div className="p-4 bg-black/40 rounded border border-blue-500/30">
                            <h3 className="text-sm font-display mb-2 text-blue-400">Recent Challenges</h3>
                            <div className="text-xs font-mono space-y-2 opacity-80">
                                <p className="text-green-400">[PASS] User: admin_root login successful</p>
                                <p className="text-yellow-400">[WARN] Multiple failed attempts from 192.168.1.105</p>
                                <p className="text-green-400">[PASS] JWT rotation complete</p>
                            </div>
                        </div>
                    </div>
                )
            case 'data':
                return (
                    <div className="space-y-4">
                        <div className="flex items-center gap-3 text-amber-400 mb-4">
                            <Database size={24} />
                            <h2 className="text-xl font-display uppercase tracking-wider">Data Core</h2>
                        </div>
                        <div className="flex flex-col gap-3">
                            <div className="flex justify-between items-end border-b border-white/10 pb-2">
                                <span className="text-xs text-gray-400 uppercase">Throughput</span>
                                <span className="font-mono text-lg text-amber-400">45.2 MB/s</span>
                            </div>
                            <div className="flex justify-between items-end border-b border-white/10 pb-2">
                                <span className="text-xs text-gray-400 uppercase">Latency</span>
                                <span className="font-mono text-lg text-green-400">14ms</span>
                            </div>
                            <div className="flex justify-between items-end border-b border-white/10 pb-2">
                                <span className="text-xs text-gray-400 uppercase">Query Load</span>
                                <span className="font-mono text-lg text-amber-500">Normal</span>
                            </div>
                        </div>
                    </div>
                )
            case 'chaos':
                return (
                    <div className="space-y-4">
                        <div className="flex items-center gap-3 text-red-500 mb-4">
                            <Bug size={24} />
                            <h2 className="text-xl font-display uppercase tracking-wider">Failure Injection</h2>
                        </div>
                        <p className="text-xs text-gray-400 mb-4 font-mono italic">"Test resilience by breaking things intentionally."</p>
                        <div className="grid grid-cols-1 gap-2">
                            {['Network Latency', 'Packet Loss', 'CPU Spike', 'Process Kill'].map(chaos => (
                                <button key={chaos} className="w-full py-2 px-4 bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-display hover:bg-red-500/20 transition-colors uppercase tracking-widest text-left">
                                    Execute: {chaos}
                                </button>
                            ))}
                        </div>
                    </div>
                )
            case 'health':
                return (
                    <div className="space-y-4">
                        <div className="flex items-center gap-3 text-green-400 mb-4">
                            <Activity size={24} />
                            <h2 className="text-xl font-display uppercase tracking-wider">Health Monitor</h2>
                        </div>
                        <div className="space-y-3">
                            {['SLA', 'Availability', 'MTBF'].map(metric => (
                                <div key={metric} className="flex flex-col gap-1">
                                    <div className="flex justify-between text-[10px] uppercase text-gray-500">
                                        <span>{metric}</span>
                                        <span>99.99%</span>
                                    </div>
                                    <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                                        <div className="h-full bg-green-500 w-[99%]" />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )
            case 'recovery':
                return (
                    <div className="space-y-4">
                        <div className="flex items-center gap-3 text-purple-400 mb-4">
                            <RefreshCcw size={24} />
                            <h2 className="text-xl font-display uppercase tracking-wider">Recovery Manager</h2>
                        </div>
                        <div className="p-4 bg-purple-500/10 border border-purple-500/30 rounded">
                            <h3 className="text-xs font-display tracking-widest mb-3 opacity-70">Heuristic Engine</h3>
                            <div className="flex items-center gap-2 text-sm text-purple-400 mb-1">
                                <CheckCircle2 size={16} />
                                <span>Self-Healing: Enabled</span>
                            </div>
                            <div className="flex items-center gap-2 text-sm text-purple-400">
                                <Terminal size={16} />
                                <span>Auto-Restart: Active</span>
                            </div>
                        </div>
                    </div>
                )
            case 'logging':
                return (
                    <div className="space-y-4">
                        <div className="flex items-center gap-3 text-cyan-400 mb-4">
                            <FileText size={24} />
                            <h2 className="text-xl font-display uppercase tracking-wider">Logging Hub</h2>
                        </div>
                        <div className="h-48 overflow-y-auto bg-black/60 p-3 rounded border border-cyan-500/20 font-mono text-[10px] space-y-1">
                            <p className="text-gray-500">[2024-04-22 07:15:00] INFO: Log aggregator initialized</p>
                            <p className="text-cyan-400">[2024-04-22 07:15:05] DATA: Received flow from auth-service</p>
                            <p className="text-gray-500">[2024-04-22 07:15:10] INFO: Cleaning old records...</p>
                            <p className="text-cyan-400">[2024-04-22 07:15:15] DATA: Trace ID: xa-772-bb9-22</p>
                            <p className="text-gray-500">[2024-04-22 07:15:20] INFO: Heartbeat normal</p>
                            <p className="text-cyan-600 animate-pulse">_</p>
                        </div>
                    </div>
                )
            default:
                return null
        }
    }

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0, x: -50, scale: 0.95 }}
                animate={{ opacity: 1, x: 0, scale: 1 }}
                exit={{ opacity: 0, x: -50, scale: 0.95 }}
                className="absolute left-24 top-1/2 -translate-y-1/2 w-[400px] bg-cyber-dark/90 backdrop-blur-xl border border-cyber-primary/30 p-8 rounded-2xl pointer-events-auto z-40 shadow-[0_20px_50px_rgba(0,0,0,0.5)]"
            >
                <button 
                    onClick={() => setActiveTool(null)}
                    className="absolute top-4 right-4 text-gray-500 hover:text-white transition-colors"
                >
                    <X size={20} />
                </button>

                {getContent()}
            </motion.div>
        </AnimatePresence>
    )
}
