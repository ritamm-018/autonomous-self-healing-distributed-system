import React from 'react'
import { motion } from 'framer-motion'
import { 
    Lock, 
    Database, 
    Zap, 
    Activity, 
    RotateCcw, 
    FileText,
    ShieldCheck,
    Cpu,
    Search
} from 'lucide-react'
import { useSystemStore } from '../store'
import clsx from 'clsx'

const TOOLS = [
    { id: 'auth', name: 'Authentication Service', icon: Lock, color: 'text-blue-400' },
    { id: 'data', name: 'Data Service', icon: Database, color: 'text-amber-400' },
    { id: 'chaos', name: 'Failure Injection', icon: Zap, color: 'text-red-500' },
    { id: 'health', name: 'Health Monitoring', icon: Activity, color: 'text-green-400' },
    { id: 'recovery', name: 'Recovery Manager', icon: RotateCcw, color: 'text-purple-400' },
    { id: 'logging', name: 'Logging Service', icon: FileText, color: 'text-cyan-400' },
]

export const Navigation = () => {
    const { activeTool, setActiveTool, selectNode } = useSystemStore()

    const handleToolClick = (toolId: string) => {
        setActiveTool(toolId === activeTool ? null : toolId)
        // Optionally select the corresponding node if it exists
        if (toolId !== 'chaos') {
            selectNode(toolId === 'auth' ? 'auth' : toolId === 'data' ? 'data' : toolId === 'health' ? 'monitor' : toolId === 'recovery' ? 'recovery' : toolId === 'logging' ? 'logging' : null)
        }
    }

    return (
        <div className="absolute left-0 top-1/2 -translate-y-1/2 p-4 flex flex-col gap-4 pointer-events-auto">
            {TOOLS.map((tool) => {
                const Icon = tool.icon
                const isActive = activeTool === tool.id

                return (
                    <motion.button
                        key={tool.id}
                        whileHover={{ scale: 1.1, x: 10 }}
                        whileTap={{ scale: 0.9 }}
                        onClick={() => handleToolClick(tool.id)}
                        className={clsx(
                            "group relative flex items-center justify-center w-14 h-14 rounded-xl border backdrop-blur-md transition-all duration-300",
                            isActive 
                                ? "bg-cyber-primary/20 border-cyber-primary shadow-[0_0_20px_rgba(0,243,255,0.3)]" 
                                : "bg-cyber-dark/60 border-white/10 hover:border-cyber-primary/50"
                        )}
                    >
                        <Icon className={clsx("w-6 h-6 transition-colors", isActive ? "text-cyber-primary" : "text-gray-400 group-hover:text-white")} />
                        
                        {/* Tooltip */}
                        <div className="absolute left-full ml-4 px-3 py-1 bg-cyber-dark border border-cyber-primary/30 rounded text-xs text-white opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap transition-opacity font-display tracking-widest z-50">
                            {tool.name}
                        </div>

                        {/* Active Indicator */}
                        {isActive && (
                            <motion.div 
                                layoutId="active-pill"
                                className="absolute -left-1 w-1 h-8 bg-cyber-primary rounded-full"
                            />
                        )}
                    </motion.button>
                )
            })}
        </div>
    )
}
