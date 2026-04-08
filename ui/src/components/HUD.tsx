import React from 'react'
import { useSystemStore } from '../store'
import { ShieldAlert, Activity, Cpu, Server, Play, Zap } from 'lucide-react'
import clsx from 'clsx'
import { motion, AnimatePresence } from 'framer-motion'

export const HUD = () => {
    const { systemHealth, selectedNode, nodes, isAttackMode, toggleAttackMode } = useSystemStore()
    const activeNode = nodes.find(n => n.id === selectedNode)

    return (
        <div className="absolute inset-0 pointer-events-none">
            {/* Top Bar - System Status */}
            <div className="absolute top-0 left-0 w-full p-4 flex justify-between items-start bg-gradient-to-b from-cyber-dark/90 to-transparent">
                <div className="flex items-center gap-4">
                    <div className="text-4xl font-display text-cyber-primary font-bold tracking-widest">
                        CYBER<span className="text-white">COMMAND</span>
                    </div>
                    <div className={clsx(
                        "px-3 py-1 border rounded text-xs font-mono uppercase tracking-widest",
                        systemHealth > 80 ? "border-cyber-primary text-cyber-primary" : "border-cyber-danger text-cyber-danger"
                    )}>
                        DEFCON {systemHealth > 80 ? '5' : '1'}
                    </div>
                </div>

                <div className="flex flex-col items-end">
                    <div className="text-cyber-primary font-mono text-xl">
                        UPTIME: 99.98%
                    </div>
                    <div className="text-gray-400 font-mono text-xs">
                        SYSTEM INTEGRITY: {systemHealth}%
                    </div>
                </div>
            </div>

            {/* Bottom Left - Controls */}
            <div className="absolute bottom-8 left-8 pointer-events-auto">
                <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={toggleAttackMode}
                    className={clsx(
                        "flex items-center gap-2 px-6 py-3 rounded border-2 backdrop-blur-sm font-display font-bold uppercase transition-all",
                        isAttackMode
                            ? "border-cyber-danger bg-cyber-danger/20 text-cyber-danger shadow-[0_0_20px_rgba(255,0,60,0.5)]"
                            : "border-cyber-primary bg-cyber-primary/10 text-cyber-primary hover:bg-cyber-primary/20"
                    )}
                >
                    {isAttackMode ? <ShieldAlert className="animate-pulse" /> : <Zap />}
                    {isAttackMode ? "STOP SIMULATION" : "SIMULATE ATTACK"}
                </motion.button>
            </div>

            {/* Right Panel - Detail View */}
            <AnimatePresence>
                {activeNode && (
                    <motion.div
                        initial={{ x: 300, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        exit={{ x: 300, opacity: 0 }}
                        className="absolute top-24 right-8 w-80 bg-cyber-dark/80 backdrop-blur-md border border-cyber-primary/30 p-6 rounded-lg pointer-events-auto"
                    >
                        <div className="flex justify-between items-center mb-6 border-b border-cyber-primary/30 pb-2">
                            <h2 className="text-xl font-display text-cyber-primary">{activeNode.name}</h2>
                            <div className={clsx(
                                "w-3 h-3 rounded-full shadow-[0_0_10px]",
                                activeNode.status === 'healthy' ? "bg-cyber-primary shadow-cyber-primary" : "bg-cyber-danger shadow-cyber-danger"
                            )} />
                        </div>

                        <div className="space-y-6 font-mono text-sm">
                            <div className="flex items-center justify-between">
                                <span className="text-gray-400 flex items-center gap-2"><Cpu size={16} /> CPU Load</span>
                                <div className="w-32 h-2 bg-gray-800 rounded overflow-hidden">
                                    <div
                                        className="h-full bg-cyber-secondary"
                                        style={{ width: `${activeNode.cpu}%` }}
                                    />
                                </div>
                                <span>{activeNode.cpu}%</span>
                            </div>

                            <div className="flex items-center justify-between">
                                <span className="text-gray-400 flex items-center gap-2"><Server size={16} /> Memory</span>
                                <div className="w-32 h-2 bg-gray-800 rounded overflow-hidden">
                                    <div
                                        className="h-full bg-cyber-warning"
                                        style={{ width: `${activeNode.memory}%` }}
                                    />
                                </div>
                                <span>{activeNode.memory}%</span>
                            </div>

                            <div className="p-4 bg-black/40 rounded border border-gray-700">
                                <h3 className="text-xs text-gray-400 uppercase mb-2">Live Logs</h3>
                                <div className="text-green-500 text-xs font-mono space-y-1">
                                    <p>{`> [INFO] Service running...`}</p>
                                    <p>{`> [METRIC] RPS: ${Math.floor(Math.random() * 500)}`}</p>
                                    {activeNode.status === 'critical' && <p className="text-red-500">{`> [ERR] Connection timeout!`}</p>}
                                    {activeNode.status === 'healing' && <p className="text-cyber-primary">{`> [SYS] Healing sequence init...`}</p>}
                                </div>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    )
}
