import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { TextEffect } from "../core/TextEffect";
import { AnimatedGroup } from "../core/AnimatedGroup";

interface StartupScreenProps {
  statusText?: string;
}

const BOOT_LOGS = [
  "INIT_KERNEL :: FedSanitize v1.0.0",
  "NET_PROBE   :: Handshake http://127.0.0.1:8000 [OK]",
  "SEC_PIPELINE:: L1_MAD + MARS (NeurIPS 2025) + TrimmedMean [ARMED]",
  "TELEMETRY   :: Cohort C0-C9 synchronized [READY]",
];

export const StartupScreen: React.FC<StartupScreenProps> = ({ 
  statusText = "Authenticating edge cohort telemetry..."
}) => {
  const [logIndex, setLogIndex] = useState<number>(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setLogIndex((prev) => (prev < BOOT_LOGS.length - 1 ? prev + 1 : prev));
    }, 180);
    return () => clearInterval(interval);
  }, []);

  return (
    <motion.div 
      initial={{ opacity: 1 }}
      exit={{ opacity: 0, filter: "blur(8px)", transition: { duration: 0.45, ease: [0.16, 1, 0.3, 1] } }}
      className="fixed inset-0 bg-[#080404] z-50 flex flex-col items-center justify-center font-mono selection:bg-accent-red selection:text-white bg-grid-pattern overflow-hidden"
    >
      {/* Background ambient CRT scanline sweep */}
      <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(ellipse_at_center,rgba(225,29,46,0.08)_0%,transparent_70%)]" />

      <AnimatedGroup className="flex flex-col items-center space-y-5 max-w-md text-center px-4 relative z-10">
        {/* Animated Shield Logo SVG with Stroke Drawing and Pulsing Red Halo */}
        <div className="relative w-20 h-20 rounded-2xl bg-[#150a0a] border border-[#3d1414] flex items-center justify-center shadow-glow-red threat-card-elevated">
          {/* Subtle radar pulse ring */}
          <div className="absolute inset-0 rounded-2xl border border-accent-red/30 animate-ping opacity-25" />

          <svg
            className="w-10 h-10 text-accent-red"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <motion.path
              d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{ pathLength: 1, opacity: 1 }}
              transition={{ duration: 0.75, ease: "easeInOut" }}
            />
            <motion.path
              d="M12 8v4"
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{ pathLength: 1, opacity: 1 }}
              transition={{ duration: 0.35, delay: 0.45, ease: "easeOut" }}
            />
            <motion.path
              d="M12 16h.01"
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ duration: 0.2, delay: 0.65 }}
            />
          </svg>
        </div>

        {/* Wordmark revealed via TextEffect */}
        <div className="space-y-1">
          <div className="text-xl font-bold tracking-widest text-[#f2e8e8] uppercase flex items-center justify-center gap-1">
            <span className="text-accent-red">FED</span>
            <TextEffect per="char" delay={0.25}>
              SANITIZE
            </TextEffect>
          </div>
          <div className="text-[11px] text-[#a88888] tracking-widest uppercase">
            Federated Threat-Defense Console
          </div>
        </div>

        {/* Terminal Boot Sequence Logs */}
        <div className="w-full bg-[#0d0606] border border-[#2d1212] rounded-lg p-3 text-left shadow-inner max-w-sm">
          <div className="flex items-center justify-between border-b border-[#251010] pb-1.5 mb-2 text-[10px] text-zinc-500 uppercase tracking-wider">
            <span>Terminal Boot Log</span>
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-accent-red animate-pulse" />
              <span>LIVE</span>
            </span>
          </div>
          <div className="space-y-1 font-mono text-[11px] text-zinc-400">
            {BOOT_LOGS.slice(0, logIndex + 1).map((log, i) => (
              <motion.div 
                key={i}
                initial={{ opacity: 0, x: -6 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.2 }}
                className={i === logIndex ? "text-red-400 font-semibold flex items-center justify-between" : "text-zinc-500"}
              >
                <span>{log}</span>
                {i === logIndex && <span className="animate-pulse text-accent-red">_</span>}
              </motion.div>
            ))}
          </div>
        </div>

        {/* Status Indicator Floor */}
        <div className="flex items-center gap-2 text-[11px] text-zinc-400 font-mono">
          <span className="w-2 h-2 rounded-full bg-accent-safe animate-pulse" />
          <span>{statusText}</span>
        </div>
      </AnimatedGroup>
    </motion.div>
  );
};
