import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Activity, ShieldAlert, Cpu, LineChart, LogOut } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import ChaosPanel from './pages/ChaosPanel';
import HealthDashboard from './pages/HealthDashboard';
import LoginPage from './pages/LoginPage';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(
    localStorage.getItem('isAuthenticated') === 'true'
  );

  // Sync state with localStorage changes (e.g., from LoginPage)
  useEffect(() => {
    const handleStorageChange = () => {
      setIsAuthenticated(localStorage.getItem('isAuthenticated') === 'true');
    };
    window.addEventListener('storage', handleStorageChange);
    // Intersection observer or interval to check for changes within the same tab
    const interval = setInterval(handleStorageChange, 500);
    return () => {
      window.removeEventListener('storage', handleStorageChange);
      clearInterval(interval);
    };
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('isAuthenticated');
    setIsAuthenticated(false);
  };

  if (!isAuthenticated) {
    return (
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LoginPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    );
  }

  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col pt-16">
        {/* Navigation Bar */}
        <nav className="fixed top-0 left-0 right-0 h-16 glass-panel z-50 flex items-center justify-between px-6 rounded-none border-t-0 border-l-0 border-r-0">
          <div className="flex items-center gap-3">
            <Cpu className="text-neon-cyan" size={28} />
            <h1 className="text-xl font-bold tracking-wider">AEGIS <span className="font-light text-gray-400">FINANCE</span></h1>
          </div>
          <div className="flex items-center gap-6">
            <NavigateButton to="/" icon={<LineChart size={18} />} label="Market & Trade" />
            <NavigateButton to="/health" icon={<Activity size={18} />} label="System Health" />
            <NavigateButton to="/chaos" icon={<ShieldAlert size={18} />} label="Chaos Control" />
            
            <button 
              onClick={handleLogout}
              className="flex items-center gap-2 text-gray-400 hover:text-red-400 transition-colors text-sm font-medium ml-4 border-l border-white/10 pl-6"
            >
              <LogOut size={18} /> Exit
            </button>
          </div>
        </nav>

        {/* Main Content Area */}
        <main className="flex-grow p-6">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/chaos" element={<ChaosPanel />} />
            <Route path="/health" element={<HealthDashboard />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

// Helper component for cleaner nav links
const NavigateButton = ({ to, icon, label }: { to: string, icon: React.ReactNode, label: string }) => (
  <a href={to} onClick={(e) => {
    e.preventDefault();
    window.location.href = to; // Using full page load for route cleanup if needed, or Link
  }} className="flex items-center gap-2 hover:text-neon-cyan transition-colors text-sm font-medium">
    {icon} {label}
  </a>
);

export default App;
