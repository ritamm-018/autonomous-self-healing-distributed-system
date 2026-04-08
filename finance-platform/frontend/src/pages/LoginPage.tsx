import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Cpu, Lock, Mail, ArrowRight, ShieldCheck } from 'lucide-react';

const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    // Simulate authentication delay
    setTimeout(() => {
      localStorage.setItem('isAuthenticated', 'true');
      navigate('/');
      setIsLoading(false);
    }, 1500);
  };

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-[#0a0a0f] overflow-hidden">
      {/* Background Animation */}
      <div className="absolute inset-0 z-0">
        <div className="absolute inset-0 bg-[linear-gradient(rgba(0,240,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(0,240,255,0.03)_1px,transparent_1px)] bg-[size:60px_60px] opacity-20"></div>
        <motion.div 
          animate={{ 
            scale: [1, 1.2, 1],
            opacity: [0.1, 0.2, 0.1]
          }}
          transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-neon-cyan/10 rounded-full blur-[120px]"
        />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="relative z-10 w-full max-w-[450px] px-6"
      >
        <div className="glass-panel p-8 md:p-10">
          <div className="text-center mb-10">
            <motion.div 
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: "spring", stiffness: 260, damping: 20, delay: 0.2 }}
              className="w-16 h-16 bg-neon-cyan/20 border border-neon-cyan/30 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-[0_0_30px_rgba(0,240,255,0.2)]"
            >
              <Cpu className="text-neon-cyan" size={32} />
            </motion.div>
            <h1 className="text-3xl font-black tracking-tight mb-2">
              AEGIS <span className="text-gray-500 font-light">FINANCE</span>
            </h1>
            <p className="text-gray-400 text-sm font-medium">Secure Terminal Access Required</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-6">
            <div className="space-y-2">
              <label className="text-xs font-bold uppercase tracking-wider text-gray-500 ml-1">Identity Endpoint</label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500" size={18} />
                <input
                  type="email"
                  required
                  placeholder="admin@aegis.systems"
                  className="w-full bg-black/40 border border-white/10 rounded-xl py-3.5 pl-12 pr-4 text-white focus:outline-none focus:border-neon-cyan transition-all placeholder:text-gray-700"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold uppercase tracking-wider text-gray-500 ml-1">Access Cipher</label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500" size={18} />
                <input
                  type="password"
                  required
                  placeholder="••••••••••••"
                  className="w-full bg-black/40 border border-white/10 rounded-xl py-3.5 pl-12 pr-4 text-white focus:outline-none focus:border-neon-cyan transition-all placeholder:text-gray-700"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </div>

            <div className="flex items-center justify-between text-xs pt-1">
              <label className="flex items-center gap-2 text-gray-500 cursor-pointer hover:text-gray-300 transition-colors">
                <input type="checkbox" className="rounded border-white/10 bg-black/40 text-neon-cyan focus:ring-neon-cyan" />
                Persistent Session
              </label>
              <a href="#" className="text-neon-cyan hover:underline font-bold">Lost Cipher?</a>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full group relative overflow-hidden bg-white text-black font-black py-4 rounded-xl transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-70 disabled:grayscale"
            >
              <div className="relative z-10 flex items-center justify-center gap-2">
                {isLoading ? (
                  <>
                    <motion.div 
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                      className="w-5 h-5 border-2 border-black border-t-transparent rounded-full"
                    />
                    Verifying Access...
                  </>
                ) : (
                  <>
                    Initialize Terminal <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
                  </>
                )}
              </div>
            </button>
          </form>

          <div className="mt-8 pt-8 border-t border-white/5 flex items-center justify-center gap-6">
            <div className="flex items-center gap-2 text-[10px] text-gray-600 font-bold uppercase tracking-[0.2em]">
              <ShieldCheck size={14} className="text-gray-500" /> 256-bit Encrypted
            </div>
          </div>
        </div>
        
        <p className="mt-8 text-center text-gray-600 text-xs font-medium">
          Authorized Personnel Only. Access is monitored and logged.
        </p>
      </motion.div>
    </div>
  );
};

export default LoginPage;
