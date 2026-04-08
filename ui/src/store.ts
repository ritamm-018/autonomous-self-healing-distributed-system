import { create } from 'zustand'

export interface ServiceNode {
    id: string;
    name: string;
    status: 'healthy' | 'warning' | 'critical' | 'healing';
    cpu: number;
    memory: number;
    position: [number, number, number];
}

interface SystemState {
    nodes: ServiceNode[];
    selectedNode: string | null;
    systemHealth: number;
    isAttackMode: boolean;

    // Actions
    setNodes: (nodes: ServiceNode[]) => void;
    selectNode: (id: string | null) => void;
    toggleAttackMode: () => void;
    updateNodeStatus: (id: string, status: ServiceNode['status']) => void;
}

// Initial Mock Data
const INITIAL_NODES: ServiceNode[] = [
    { id: 'gateway', name: 'Gateway Service', status: 'healthy', cpu: 12, memory: 34, position: [0, 0, 0] },
    { id: 'auth', name: 'Auth Service', status: 'healthy', cpu: 45, memory: 22, position: [-2, 0, 1.5] },
    { id: 'data', name: 'Data Service', status: 'healthy', cpu: 28, memory: 60, position: [2, 0, 1.5] },
    { id: 'decision', name: 'Decision Engine', status: 'healthy', cpu: 15, memory: 40, position: [0, 0, 3] },
    { id: 'anomaly', name: 'Anomaly Detector', status: 'healthy', cpu: 65, memory: 70, position: [0, 0, -3] },
    { id: 'monitor', name: 'Health Monitor', status: 'healthy', cpu: 10, memory: 15, position: [-2, 0, -1.5] },
    { id: 'recovery', name: 'Recovery Manager', status: 'healthy', cpu: 5, memory: 12, position: [2, 0, -1.5] },
]

export const useSystemStore = create<SystemState>((set) => ({
    nodes: INITIAL_NODES,
    selectedNode: null,
    systemHealth: 100,
    isAttackMode: false,

    setNodes: (nodes) => set({ nodes }),
    selectNode: (id) => set({ selectedNode: id }),
    toggleAttackMode: () => set((state) => ({ isAttackMode: !state.isAttackMode })),
    updateNodeStatus: (id, status) => set((state) => ({
        nodes: state.nodes.map(n => n.id === id ? { ...n, status } : n)
    }))
}))
