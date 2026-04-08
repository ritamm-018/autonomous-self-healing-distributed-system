import React, { useState, useEffect, useCallback } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler
} from 'chart.js';
import { tradeApi, paymentApi } from '../utils/api';
import { ArrowUpRight, DollarSign, Wallet, TrendingUp, CreditCard, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

// ─── Toast Notification ──────────────────────────────────────────────────────
type ToastType = 'success' | 'error' | 'loading';
interface Toast { id: number; type: ToastType; message: string; sub?: string; }

let toastId = 0;
const useToasts = () => {
    const [toasts, setToasts] = useState<Toast[]>([]);
    const addToast = (type: ToastType, message: string, sub?: string) => {
        const id = ++toastId;
        setToasts(prev => [...prev, { id, type, message, sub }]);
        if (type !== 'loading') setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4000);
        return id;
    };
    const removeToast = (id: number) => setToasts(prev => prev.filter(t => t.id !== id));
    return { toasts, addToast, removeToast };
};

const ToastContainer = ({ toasts }: { toasts: Toast[] }) => (
    <div className="fixed top-5 right-5 z-50 flex flex-col gap-2 pointer-events-none">
        <AnimatePresence>
            {toasts.map(t => (
                <motion.div
                    key={t.id}
                    initial={{ opacity: 0, x: 50 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 50 }}
                    className={`flex items-start gap-3 px-4 py-3 rounded-xl border backdrop-blur-md shadow-2xl min-w-[280px] ${
                        t.type === 'success' ? 'bg-green-900/80 border-green-500/50 text-green-100' :
                        t.type === 'error'   ? 'bg-red-900/80 border-red-500/50 text-red-100' :
                                               'bg-slate-800/90 border-cyan-500/50 text-cyan-100'
                    }`}
                >
                    {t.type === 'success' && <CheckCircle size={18} className="text-green-400 mt-0.5 shrink-0" />}
                    {t.type === 'error'   && <XCircle    size={18} className="text-red-400 mt-0.5 shrink-0" />}
                    {t.type === 'loading' && <Loader2    size={18} className="text-cyan-400 mt-0.5 shrink-0 animate-spin" />}
                    <div>
                        <p className="font-semibold text-sm">{t.message}</p>
                        {t.sub && <p className="text-xs opacity-70 mt-0.5">{t.sub}</p>}
                    </div>
                </motion.div>
            ))}
        </AnimatePresence>
    </div>
);

// ─── Simulated local transaction (when Gateway is offline) ───────────────────
const simulateLocal = (type: 'TRADE' | 'PAYMENT', detail: string) => ({
    name: `${type}-${Date.now()}`,
    description: detail,
    simulated: true,
});

// ─── Main Dashboard ──────────────────────────────────────────────────────────
const Dashboard = () => {
    const [balance, setBalance]           = useState(128453.22);
    const [transactions, setTransactions] = useState<any[]>([]);
    const [tradeLoading, setTradeLoading] = useState(false);
    const [payLoading,   setPayLoading]   = useState(false);
    const { toasts, addToast, removeToast } = useToasts();

    const [chartData] = useState({
        labels: ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00'],
        datasets: [{
            label: 'Portfolio Value',
            data: [124000, 125500, 123800, 126000, 127200, 126800, 128453],
            borderColor: '#00f0ff',
            backgroundColor: 'rgba(0, 240, 255, 0.1)',
            fill: true,
            tension: 0.4
        }]
    });

    // ── Execute Block Trade ─────────────────────────────────────────────────
    const handleQuickTrade = async () => {
        if (tradeLoading) return;
        setTradeLoading(true);
        const loadId = addToast('loading', 'Executing Block Trade…', 'Routing via Gateway → Data Service');

        try {
            await tradeApi.executeTrade({ symbol: 'AAPL', amount: 10, price: 150 });
            removeToast(loadId);
            addToast('success', 'Block Trade Executed!', 'BUY 10x AAPL @ $150 — settled via Gateway');
            setBalance(b => b - 1500);
            // Prepend a local record immediately so something appears in the feed
            setTransactions(prev => [
                { name: 'TRADE-AAPL', description: 'BUY 10 at 150' },
                ...prev.slice(0, 9)
            ]);
            fetchTransactions();
        } catch (error: any) {
            removeToast(loadId);
            // Java Gateway offline → fall back to local simulation
            const sim = simulateLocal('TRADE', 'BUY 10 AAPL at $150 (simulated)');
            setTransactions(prev => [sim, ...prev.slice(0, 9)]);
            setBalance(b => b - 1500);
            addToast('success', 'Block Trade Simulated', 'Gateway offline — trade recorded locally');
            console.warn('Gateway unreachable, simulated trade:', error.message);
        } finally {
            setTradeLoading(false);
        }
    };

    // ── Wire Transfer ───────────────────────────────────────────────────────
    const handleWireTransfer = async () => {
        if (payLoading) return;
        setPayLoading(true);
        const loadId = addToast('loading', 'Processing Wire Transfer…', '$50,000 → HedgeFundX');

        try {
            await paymentApi.sendPayment({ recipient: 'HedgeFundX', amount: 50000 });
            removeToast(loadId);
            addToast('success', 'Wire Transfer Sent!', '$50,000 wired to HedgeFundX via Gateway');
            setBalance(b => b - 50000);
            setTransactions(prev => [
                { name: 'PAYMENT-HedgeFundX', description: 'Transferred 50000 USD' },
                ...prev.slice(0, 9)
            ]);
            fetchTransactions();
        } catch (error: any) {
            removeToast(loadId);
            // Java Gateway offline → fall back to local simulation
            const sim = simulateLocal('PAYMENT', 'Transferred 50000 USD to HedgeFundX (simulated)');
            setTransactions(prev => [sim, ...prev.slice(0, 9)]);
            setBalance(b => b - 50000);
            addToast('success', 'Transfer Simulated', 'Gateway offline — payment recorded locally');
            console.warn('Gateway unreachable, simulated payment:', error.message);
        } finally {
            setPayLoading(false);
        }
    };

    // ── Live Transaction Feed ───────────────────────────────────────────────
    const fetchTransactions = useCallback(async () => {
        try {
            const res = await tradeApi.getTransactions();
            const data = res.data.transactions || [];
            setTransactions(data.reverse().slice(0, 10));
        } catch {
            // Gateway offline — keep whatever we have locally
        }
    }, []);

    useEffect(() => {
        fetchTransactions();
        const interval = setInterval(fetchTransactions, 5000);
        return () => clearInterval(interval);
    }, [fetchTransactions]);

    return (
        <div className="space-y-6 pt-6">
            <ToastContainer toasts={toasts} />

            <header className="flex justify-between items-end">
                <div>
                    <h2 className="text-3xl font-bold">Trading Terminal</h2>
                    <p className="text-gray-400">Welcome back, Institution Alpha.</p>
                </div>
                <div className="text-right">
                    <p className="text-sm text-gray-400">Total Net Worth</p>
                    <h2 className="text-4xl font-mono text-neon-cyan">${balance.toLocaleString()}</h2>
                    <p className="text-green-400 flex items-center justify-end gap-1">
                        <ArrowUpRight size={16}/> +$4,453.22 (3.5%) Today
                    </p>
                </div>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* Chart */}
                <motion.div initial={{opacity:0, y:20}} animate={{opacity:1, y:0}} className="lg:col-span-2 glass-panel p-6">
                    <div className="flex justify-between items-center mb-4">
                        <h3 className="text-lg font-semibold flex items-center gap-2">
                            <TrendingUp size={20} className="text-neon-cyan"/> Market Overview
                        </h3>
                    </div>
                    <div className="h-80 w-full">
                        <Line
                            data={chartData}
                            options={{
                                responsive: true,
                                maintainAspectRatio: false,
                                scales: {
                                    y: { grid: { color: 'rgba(255,255,255,0.05)' } },
                                    x: { grid: { color: 'rgba(255,255,255,0.05)' } }
                                },
                                plugins: { legend: { display: false } }
                            }}
                        />
                    </div>
                </motion.div>

                {/* Quick Actions */}
                <motion.div initial={{opacity:0, y:20}} animate={{opacity:1, y:0}} transition={{delay:0.1}} className="glass-panel p-6 flex flex-col gap-4">
                    <h3 className="text-lg font-semibold flex items-center gap-2">
                        <Wallet size={20} className="text-neon-purple"/> Quick Actions
                    </h3>

                    {/* Execute Block Trade */}
                    <button
                        onClick={handleQuickTrade}
                        disabled={tradeLoading}
                        className="w-full bg-blue-600/20 hover:bg-blue-600/40 active:scale-95 border border-blue-500/50 rounded-lg p-4 flex flex-col items-center justify-center transition-all duration-150 disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer"
                    >
                        {tradeLoading
                            ? <Loader2 className="text-blue-400 mb-2 animate-spin" />
                            : <DollarSign className="text-blue-400 mb-2" />
                        }
                        <span className="font-semibold text-blue-100">
                            {tradeLoading ? 'Executing…' : 'Execute Block Trade'}
                        </span>
                        <span className="text-xs text-blue-300 mt-1">Triggers POST /trade</span>
                    </button>

                    {/* Wire Transfer */}
                    <button
                        onClick={handleWireTransfer}
                        disabled={payLoading}
                        className="w-full bg-purple-600/20 hover:bg-purple-600/40 active:scale-95 border border-purple-500/50 rounded-lg p-4 flex flex-col items-center justify-center transition-all duration-150 disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer"
                    >
                        {payLoading
                            ? <Loader2 className="text-purple-400 mb-2 animate-spin" />
                            : <CreditCard className="text-purple-400 mb-2" />
                        }
                        <span className="font-semibold text-purple-100">
                            {payLoading ? 'Transferring…' : 'Wire Transfer'}
                        </span>
                        <span className="text-xs text-purple-300 mt-1">Triggers POST /payment</span>
                    </button>
                </motion.div>

                {/* Live Transaction Feed */}
                <motion.div initial={{opacity:0, y:20}} animate={{opacity:1, y:0}} transition={{delay:0.2}} className="lg:col-span-3 glass-panel p-6">
                    <h3 className="text-lg font-semibold mb-4">Live Transaction Feed</h3>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="border-b border-gray-700 text-gray-400">
                                    <th className="p-3 font-medium">Type</th>
                                    <th className="p-3 font-medium">Description</th>
                                    <th className="p-3 font-medium">Status</th>
                                    <th className="p-3 font-medium">Network Latency</th>
                                </tr>
                            </thead>
                            <tbody>
                                {transactions.length === 0 && (
                                    <tr>
                                        <td colSpan={4} className="p-4 text-center text-gray-500">
                                            No recent transactions. Click a button above to get started!
                                        </td>
                                    </tr>
                                )}
                                {transactions.map((tx, idx) => (
                                    <motion.tr
                                        key={idx}
                                        initial={{ opacity: 0, x: -10 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        className="border-b border-gray-800/50 hover:bg-white/5 transition-colors"
                                    >
                                        <td className="p-3 font-mono text-neon-cyan">{tx.name || 'UNKNOWN_TX'}</td>
                                        <td className="p-3">{tx.description || 'N/A'}</td>
                                        <td className="p-3">
                                            <span className={`px-2 py-1 rounded text-xs border ${
                                                tx.simulated
                                                    ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
                                                    : 'bg-green-500/20 text-green-400 border-green-500/30'
                                            }`}>
                                                {tx.simulated ? 'SIMULATED' : 'SETTLED'}
                                            </span>
                                        </td>
                                        <td className="p-3 font-mono text-gray-400">
                                            {tx.simulated ? 'N/A (local)' : `~${Math.floor(Math.random() * 40 + 10)}ms`}
                                        </td>
                                    </motion.tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </motion.div>
            </div>
        </div>
    );
};

export default Dashboard;
