import React from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Stars, Environment, PerspectiveCamera } from '@react-three/drei'
import { useSystemStore } from '../store'
import { HexNode } from './ServiceNode'
import { EffectComposer, Bloom, Glitch } from '@react-three/postprocessing'

export const Scene = () => {
    const nodes = useSystemStore(state => state.nodes)
    const isAttackMode = useSystemStore(state => state.isAttackMode)

    return (
        <div className="w-full h-screen bg-cyber-dark">
            <Canvas>
                <PerspectiveCamera makeDefault position={[0, 8, 10]} fov={50} />
                <OrbitControls enablePan={true} enableZoom={true} enableRotate={true} />

                {/* Lighting */}
                <ambientLight intensity={0.5} />
                <pointLight position={[10, 10, 10]} intensity={1} color="#00f3ff" />
                <pointLight position={[-10, -10, -10]} intensity={0.5} color="#7000ff" />

                {/* Environment */}
                <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />
                <gridHelper args={[50, 50, 0x1a1a3a, 0x0a0a20]} position={[0, -2, 0]} />

                {/* Service Nodes */}
                {nodes.map(node => (
                    <HexNode key={node.id} node={node} />
                ))}

                {/* Post-Processing Effects */}
                <EffectComposer>
                    <Bloom luminanceThreshold={0.2} luminanceSmoothing={0.9} height={300} intensity={1.5} />
                    {isAttackMode && (
                        <Glitch
                            delay={[1.5, 3.5]}
                            duration={[0.6, 1.0]}
                            strength={[0.3, 1.0]}
                        />
                    )}
                </EffectComposer>
            </Canvas>
        </div>
    )
}
