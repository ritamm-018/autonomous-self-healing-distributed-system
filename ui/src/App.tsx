import React from 'react'
import { Scene } from './components/Scene'
import { HUD } from './components/HUD'
import { Navigation } from './components/Navigation'
import { ToolOverlay } from './components/ToolOverlay'

function App() {
    return (
        <div className="relative w-full h-screen overflow-hidden bg-cyber-dark">
            <Scene />
            <HUD />
            <Navigation />
            <ToolOverlay />
        </div>
    )
}

export default App

