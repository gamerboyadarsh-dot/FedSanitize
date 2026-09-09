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
          onAuthenticated={() => setShowLogin(false)}
          onGuest={() => setShowLogin(false)}
        />
      )}

      <AnimatePresence mode="wait">
        {isInitializing && (
          <StartupScreen statusText={errorMsg ? "Connecting to backend gateway..." : "Cohort telemetry synchronized. Launching console..."} />
        )}
      </AnimatePresence>

      {/* Root Layout Wrapper with Ambient Gradient Background */}
      <div 
        className="h-screen w-full text-text-primary overflow-hidden font-sans selection:bg-primary selection:text-black relative"
        style={{
          backgroundColor: "#050508",
          backgroundImage: `
            radial-gradient(ellipse 60% 45% at 15% 10%, hsl(262 75% 60% / 0.35), transparent 70%),
            radial-gradient(ellipse 65% 50% at 85% 90%, hsl(217 85% 45% / 0.30), transparent 70%)
          `,
          backgroundAttachment: "fixed"
        }}
      >
        {/* SVG Noise Texture Layer */}
        <div className="pointer-events-none absolute inset-0 z-0 opacity-5 mix-blend-overlay">
          <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
            <filter id="noiseFilter">
              <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="3" stitchTiles="stitch" />
            </filter>
            <rect width="100%" height="100%" filter="url(#noiseFilter)" />
          </svg>
        </div>

        {/* Existing App Container (z-10 to sit above background layer) */}
        <div className="flex w-full h-full relative z-10">
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
                <SecurityIntelligence latestRound={latestRound} />
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
      </div>
    </>
  );
}

export default App;
