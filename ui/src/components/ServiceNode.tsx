import React, { useRef, useState } from 'react'
import { useFrame } from '@react-three/fiber'
import { Text, Html } from '@react-three/drei'
import { useSystemStore, ServiceNode } from '../store'
import * as THREE from 'three'

const COLOR_MAP = {
    healthy: '#00f3ff', // Cyan
    warning: '#fcee0a', // Yellow
    critical: '#ff003c', // Red
    healing: '#00ff9f', // Green
}

export const HexNode = ({ node }: { node: ServiceNode }) => {
    const meshRef = useRef<THREE.Mesh>(null)
    const selectNode = useSystemStore(state => state.selectNode)
    const selectedNode = useSystemStore(state => state.selectedNode)
    const [hovered, setHover] = useState(false)

    // Animation loop
    useFrame((state, delta) => {
        if (meshRef.current) {
            // Idle float
            meshRef.current.position.y = Math.sin(state.clock.elapsedTime + node.position[0]) * 0.2

            // Rotate on hover or select
            if (hovered || selectedNode === node.id) {
                meshRef.current.rotation.y += delta
            }
        }
    })

    const isSelected = selectedNode === node.id
    const color = COLOR_MAP[node.status]

    return (
        <group position={new THREE.Vector3(...node.position)}>
            {/* The Hexagon */}
            <mesh
                ref={meshRef}
                onClick={(e) => { e.stopPropagation(); selectNode(node.id) }}
                onPointerOver={() => setHover(true)}
                onPointerOut={() => setHover(false)}
            >
                <cylinderGeometry args={[1, 1, 0.5, 6]} />
                <meshStandardMaterial
                    color={color}
                    emissive={color}
                    emissiveIntensity={isSelected || hovered ? 2 : 0.5}
                    wireframe={node.status === 'healing'} // Wireframe effect when healing
                    transparent
                    opacity={0.8}
                />
            </mesh>

            {/* Label */}
            <Text
                position={[0, 1.2, 0]}
                fontSize={0.3}
                color="white"
                anchorX="center"
                anchorY="middle"
            >
                {node.name}
            </Text>

            {/* Status Status Ring */}
            {node.status === 'critical' && (
                <mesh rotation={[Math.PI / 2, 0, 0]} position={[0, -0.5, 0]}>
                    <ringGeometry args={[1.2, 1.3, 32]} />
                    <meshBasicMaterial color="#ff003c" side={THREE.DoubleSide} />
                </mesh>
            )}
        </group>
    )
}
