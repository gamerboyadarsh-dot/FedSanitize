import React, { useState, useEffect } from "react";
import { AnimatePresence } from "framer-motion";
import { Sidebar, type NavPage } from "./components/layout/Sidebar";
import { Header } from "./components/layout/Header";
import { Overview } from "./pages/Overview";
import { ClientProfiling } from "./pages/ClientProfiling";
import { DefensePipeline } from "./pages/DefensePipeline";
import { AttackPlayground } from "./pages/AttackPlayground";
import { Analytics } from "./pages/Analytics";
import { Configuration } from "./pages/Configuration";
import { LiveAttackArena } from "./pages/LiveAttackArena";
import { StartupScreen } from "./components/common/StartupScreen";
import { TransitionPanel } from "./components/core/TransitionPanel";
import type { RoundRecord, ClientSummary } from "./types/telemetry";
import { 
  fetchHistory, 
  fetchClients, 
  runRound, 
  resetSimulation, 
  loadDemo 
} from "./api/client";

const pageOrder: NavPage[] = ["overview", "clients", "defense", "attacks", "analytics", "arena", "config"];

export function App() {
  const [currentPage, setCurrentPage] = useState<NavPage>("overview");
  const [history, setHistory] = useState<RoundRecord[]>([]);
  const [clients, setClients] = useState<ClientSummary[]>([]);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isInitializing, setIsInitializing] = useState<boolean>(true);

  const refreshData = async () => {
    try {
      const [histData, clientsData] = await Promise.all([
        fetchHistory(),
        fetchClients(),
      ]);
      setHistory(histData);
      setClients(clientsData);
      setErrorMsg(null);
    } catch (err: any) {
      console.warn("Backend API not reachable:", err.message);
      setErrorMsg("Connecting to FedSanitize API gateway at http://127.0.0.1:8000...");
    }
  };

  useEffect(() => {
    const startTime = Date.now();
    refreshData().finally(() => {
      // Respect the minimum ~500ms startup screen floor so logo animation finishes cleanly
      const elapsed = Date.now() - startTime;
      const remaining = Math.max(0, 750 - elapsed);
      setTimeout(() => {
        setIsInitializing(false);
      }, remaining);
    });
  }, []);

  const handleRunRound = async () => {
    try {
      setIsRunning(true);
      const newRound = await runRound();
      setHistory((prev) => [...prev, newRound]);
      const updatedClients = await fetchClients();
      setClients(updatedClients);
    } catch (err: any) {
      alert(`Error running round: ${err.message}`);
    } finally {
      setIsRunning(false);
    }
  };

  const handleReset = async () => {
    try {
      setIsRunning(true);
      await resetSimulation();
      setHistory([]);
      const updatedClients = await fetchClients();
      setClients(updatedClients);
    } catch (err: any) {
      alert(`Error resetting: ${err.message}`);
    } finally {
      setIsRunning(false);
    }
  };

  const handleLoadDemo = async () => {
    try {
      setIsRunning(true);
      const res = await loadDemo();
      setHistory(res.history);
      const updatedClients = await fetchClients();
      setClients(updatedClients);
    } catch (err: any) {
      alert(`Error loading demo: ${err.message}`);
    } finally {
      setIsRunning(false);
    }
  };

  const latestRound = history.length > 0 ? history[history.length - 1] : null;
  const activePageIndex = pageOrder.indexOf(currentPage);

  return (
    <>
      <AnimatePresence mode="wait">
        {isInitializing && (
          <StartupScreen statusText={errorMsg ? "Connecting to backend gateway..." : "Cohort telemetry synchronized. Launching console..."} />
        )}
      </AnimatePresence>

      <div className="flex h-screen bg-background text-text-primary overflow-hidden font-sans bg-grid-pattern selection:bg-accent-red selection:text-white">
      {/* Persistent Left Sidebar with AnimatedBackground */}
      <Sidebar 
        currentPage={currentPage} 
        onSelectPage={setCurrentPage} 
        activeRounds={history.length} 
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header Controls with Stacked Stats & No-Wrap */}
        <Header 
          currentRoundData={latestRound}
          isRunning={isRunning}
          onRunRound={handleRunRound}
          onReset={handleReset}
          onLoadDemo={handleLoadDemo}
        />

        {errorMsg && (
          <div className="bg-accent-warning/10 border-b border-accent-warning/30 px-6 py-2 text-xs font-mono text-accent-warning flex items-center justify-between shrink-0">
            <span>{errorMsg}</span>
            <button onClick={refreshData} className="underline hover:text-white">
              Retry Connection
            </button>
          </div>
        )}

        {/* Scrollable Page Body animated with TransitionPanel */}
        <main className="flex-1 overflow-y-auto p-8">
          <TransitionPanel activeIndex={activePageIndex}>
            <Overview history={history} latestRound={latestRound} />
            <ClientProfiling clients={clients} latestRound={latestRound} />
            <DefensePipeline latestRound={latestRound} isRunning={isRunning} />
            <AttackPlayground clients={clients} onRefreshClients={refreshData} />
            <Analytics history={history} latestRound={latestRound} />
            <LiveAttackArena />
            <Configuration />
          </TransitionPanel>
        </main>

        {/* Global Copyright & Architecture Footer */}
        <footer className="border-t border-border/40 py-2 px-8 text-xs font-mono text-text-secondary/60 flex items-center justify-between shrink-0 bg-surface/30 backdrop-blur-sm select-none">
          <span>© 2026 FedSanitize · Multi-Layer Byzantine &amp; Backdoor Defense Framework</span>
          <span className="text-[11px] text-text-secondary/50">NeurIPS 2025 MARS Forensics · All rights reserved.</span>
        </footer>
      </div>
    </div>
    </>
  );
}

export default App;
