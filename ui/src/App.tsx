import React from 'react'
import { Scene } from './components/Scene'
import { HUD } from './components/HUD'

function App() {
    return (
        <div className="relative w-full h-screen overflow-hidden">
            <Scene />
            <HUD />
        </div>
    )
}

export default App
