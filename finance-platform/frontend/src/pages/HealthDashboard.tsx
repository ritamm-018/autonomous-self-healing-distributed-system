import React, { useRef, useState, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Stars, Text } from '@react-three/drei';
import { Server, Activity, ArrowRight, CheckCircle, XCircle } from 'lucide-react';
import { motion } from 'framer-motion';

// --- 3D Server Node Component ---
const ServerNode = ({ position, color, label }: { position: [number,number,number], color: string, label: string }) => {
  const meshRef = useRef<any>();
  useFrame(() => { if (meshRef.current) meshRef.current.rotation.y += 0.01; });

  return (
    <group position={position}>
      <mesh ref={meshRef}>
        <boxGeometry args={[1, 1.5, 1]} />
        <meshStandardMaterial color={color} wireframe={true} />
        <meshStandardMaterial color={color} transparent opacity={0.3} />
      </mesh>
      <Text position={[0, -1.2, 0]} fontSize={0.3} color="white" anchorX="center" anchorY="middle">
        {label}
      </Text>
    </group>
  );
};

// --- Main Dashboard Component ---
const HealthDashboard = () => {
    // We simulate fetching health state from our Node.js load simulator, OR directly from Java if we proxied it.
    // For the UI, we'll setup states. In a real integration, this polls the Data Service health via Gateway.
    const [gatewayHealth, setGatewayHealth] = useState('UP');
    const [authHealth, setAuthHealth] = useState('UP');
    const [dataHealth, setDataHealth] = useState('UP'); // This will toggle when Chaos is used

    // Poll via /gateway proxy (Vite forwards /gateway/* -> localhost:8080) - no CORS issues
    useEffect(() => {
        const checkHealth = async () => {
            try {
                const res = await fetch('/gateway/actuator/health');
                if (res.ok) {
                    setGatewayHealth('UP');
                    setAuthHealth('UP');
                } else {
                    setGatewayHealth('DOWN');
                }
            } catch (err) {
                setGatewayHealth('DOWN');
            }

            try {
                const dataRes = await fetch('/gateway/data/items');
                if (dataRes.ok) setDataHealth('UP');
                else setDataHealth('DOWN');
            } catch(e) {
                setDataHealth('DOWN');
            }
        };

        const interval = setInterval(checkHealth, 3000);
        checkHealth();
        return () => clearInterval(interval);
    }, []);

    // Determine 3D color based on health
    const getColor = (status: string) => {
        if (status === 'UP') return '#00ff00';
        if (status === 'RECOVERING') return '#ffff00';
        return '#ff0000';
    };

    return (
        <div className="space-y-6 pt-6 h-[calc(100vh-100px)] flex flex-col">
            <header>
                <h2 className="text-3xl font-bold flex items-center gap-3">
                    <Activity className="text-green-500"/> Infrastructure Health & Recovery Timeline
                </h2>
                <p className="text-gray-400 mt-2">Visually track the state of the JVM Microservices, Kubernetes orchestrations, and automated healing events.</p>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 flex-grow">
                
                {/* Status Sidebar */}
                <motion.div initial={{x:-20, opacity:0}} animate={{x:0, opacity:1}} className="glass-panel p-6 flex flex-col gap-6">
                    <h3 className="text-xl font-bold flex items-center gap-2 border-b border-gray-700 pb-2"><Server size={20}/> Service Registry</h3>
                    
                    <div className={`p-4 rounded-lg flex items-center justify-between border ${gatewayHealth === 'UP' ? 'bg-green-900/20 border-green-500/30' : 'bg-red-900/20 border-red-500/30'}`}>
                        <div>
                            <div className="font-bold">API Gateway</div>
                            <div className="text-xs text-gray-400">Port: 8080</div>
                        </div>
                        {gatewayHealth === 'UP' ? <CheckCircle className="text-green-500"/> : <XCircle className="text-red-500"/>}
                    </div>

                    <div className={`p-4 rounded-lg flex items-center justify-between border ${authHealth === 'UP' ? 'bg-green-900/20 border-green-500/30' : 'bg-red-900/20 border-red-500/30'}`}>
                        <div>
                            <div className="font-bold">Auth Service</div>
                            <div className="text-xs text-gray-400">Port: 8081</div>
                        </div>
                        {authHealth === 'UP' ? <CheckCircle className="text-green-500"/> : <XCircle className="text-red-500"/>}
                    </div>

                    <div className={`p-4 rounded-lg flex items-center justify-between border ${dataHealth === 'UP' ? 'bg-green-900/20 border-green-500/30' : 'bg-red-900/20 border-red-500/30'}`}>
                        <div>
                            <div className="font-bold">Data Service</div>
                            <div className="text-xs text-gray-400">Port: 8082</div>
                        </div>
                        {dataHealth === 'UP' ? <CheckCircle className="text-green-500"/> : <XCircle className="text-red-500"/>}
                    </div>

                    <div className="mt-auto pt-4 border-t border-gray-700">
                        <div className="text-xs text-gray-400 uppercase tracking-wider mb-2">Self-Healing Pipeline</div>
                        <div className="flex flex-col gap-2 text-sm font-mono text-gray-300">
                            <span className="flex items-center gap-2"><ArrowRight size={12} className="text-blue-400"/> Health Monitor (8083) Active</span>
                            <span className="flex items-center gap-2"><ArrowRight size={12} className="text-blue-400"/> Recovery Manager (8084) Active</span>
                        </div>
                    </div>
                </motion.div>

                {/* 3D Visualizer */}
                <motion.div initial={{scale:0.95, opacity:0}} animate={{scale:1, opacity:1}} transition={{delay:0.2}} className="col-span-1 lg:col-span-3 glass-panel relative overflow-hidden bg-[#020205]">
                    {/* Overlay Label */}
                    <div className="absolute top-4 left-4 z-10 font-mono text-sm tracking-widest text-[#00f0ff] uppercase bg-black/50 px-3 py-1 rounded">
                        Neural Network Topography
                    </div>

                    <Canvas camera={{ position: [0, 2, 8] }}>
                        <ambientLight intensity={0.5} />
                        <pointLight position={[10, 10, 10]} intensity={1.5} color="#00f0ff"/>
                        <pointLight position={[-10, -10, -10]} intensity={1} color="#b026ff"/>
                        <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />
                        
                        {/* Gateway at center front */}
                        <ServerNode position={[0, -1, 2]} color={getColor(gatewayHealth)} label="GATEWAY :8080" />
                        
                        {/* Auth Service left */}
                        <ServerNode position={[-3, 0, -2]} color={getColor(authHealth)} label="AUTH :8081" />
                        
                        {/* Data Service right */}
                        <ServerNode position={[3, 0, -2]} color={getColor(dataHealth)} label="DATA :8082" />

                        {/* Monitor & Recovery back */}
                        <ServerNode position={[-1.5, 2, -5]} color="#00f0ff" label="MONITOR :8083" />
                        <ServerNode position={[1.5, 2, -5]} color="#b026ff" label="RECOVERY :8084" />

                        <OrbitControls enablePan={true} enableZoom={true} enableRotate={true} />
                    </Canvas>
                </motion.div>

            </div>
        </div>
    );
};

export default HealthDashboard;
