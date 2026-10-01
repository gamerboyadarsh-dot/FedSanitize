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
import { SecurityIntelligence } from "./pages/SecurityIntelligence";
import { LiveAttackArena } from "./pages/LiveAttackArena";
import { StartupScreen } from "./components/common/StartupScreen";
import { LoginPage } from "./components/common/LoginPage";
import { TransitionPanel } from "./components/core/TransitionPanel";
import type { RoundRecord, ClientSummary } from "./types/telemetry";
import { getAuth } from "./api/auth";
import { 
  fetchHistory, 
  fetchClients, 
  runRound, 
  resetSimulation, 
  loadDemo 
} from "./api/client";

const pageOrder: NavPage[] = ["overview", "clients", "defense", "attacks", "analytics", "arena", "security-intelligence", "config"];

export function App() {
  const [currentPage, setCurrentPage] = useState<NavPage>("overview");
  const [history, setHistory] = useState<RoundRecord[]>([]);
  const [clients, setClients] = useState<ClientSummary[]>([]);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isInitializing, setIsInitializing] = useState<boolean>(true);
  // Always show login page on fresh app load
  const [showLogin, setShowLogin] = useState<boolean>(true);
  // Incremented after login/guest so AuthBadgeModal in Header remounts and re-reads auth
  const [authVersion, setAuthVersion] = useState<number>(0);

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
      const activeApi = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/+$/, "") || "http://127.0.0.1:8000";
      setErrorMsg(`Connecting to FedSanitize API gateway at ${activeApi}...`);
    }
  };

  useEffect(() => {
    const startTime = Date.now();
    refreshData().finally(() => {
      // Allow startup screen to display smoothly for 2.6 seconds
      const elapsed = Date.now() - startTime;
      const remaining = Math.max(0, 2600 - elapsed);
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
      {/* Full-page login — shown before dashboard if not authenticated */}
      {showLogin && !isInitializing && (
        <LoginPage
          onAuthenticated={() => { setShowLogin(false); setAuthVersion((v) => v + 1); }}
          onGuest={() => { setShowLogin(false); setAuthVersion((v) => v + 1); }}
        />
      )}

      <AnimatePresence mode="wait">
        {isInitializing && (
          <StartupScreen statusText={errorMsg ? "Connecting to backend gateway..." : "Cohort telemetry synchronized. Launching console..."} />
        )}
      </AnimatePresence>

      {/* Root Layout Wrapper — uses app-bg utility from index.css */}
      <div className="app-bg h-screen w-full text-text-primary overflow-hidden font-sans selection:bg-primary selection:text-black relative">
        {/* App Container */}
        <div className="flex w-full h-full relative">
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
              authVersion={authVersion}
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
            <main className="flex-1 overflow-y-auto p-8 pb-8">
              <TransitionPanel activeIndex={activePageIndex}>
                <Overview history={history} latestRound={latestRound} />
                <ClientProfiling clients={clients} latestRound={latestRound} />
                <DefensePipeline latestRound={latestRound} isRunning={isRunning} />
                <AttackPlayground clients={clients} onRefreshClients={refreshData} />
                <Analytics history={history} latestRound={latestRound} />
                <LiveAttackArena />
                <SecurityIntelligence latestRound={latestRound} />
                <Configuration />
              </TransitionPanel>
            </main>

            {/* Global Footer */}
            <footer className="shrink-0 h-10 border-t border-[rgba(148,163,184,0.08)] px-7 flex items-center justify-between text-[11px] text-[#667796] bg-[#0A1330]/60">
              <span>© 2026 FedSanitize — Multi-Layer Byzantine &amp; Backdoor Defense Framework</span>
              <span>NeurIPS 2025 MARS Forensics</span>
            </footer>
          </div>
        </div>
      </div>
    </>
  );
}

export default App;
