import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { ShieldCheck, Cpu, Terminal, Sparkles } from "lucide-react";
import { TextEffect } from "../core/TextEffect";
import { AnimatedGroup } from "../core/AnimatedGroup";

interface StartupScreenProps {
  statusText?: string;
}

const BOOT_LOGS = [
  "INIT_KERNEL :: FedSanitize v1.0.0 [Multi-Layer Threat Defense]",
  "NET_PROBE   :: Handshake http://127.0.0.1:8000 [OK]",
  "SEC_PIPELINE:: L1_MAD + MARS (NeurIPS 2025) + TrimmedMean [ARMED]",
  "ZERO_TRUST  :: JWT RBAC + Reversible Quarantine Manager [INITIALIZED]",
  "TELEMETRY   :: Cohort C0-C9 synchronized [READY]",
];

export const StartupScreen: React.FC<StartupScreenProps> = ({ 
  statusText = "Authenticating edge cohort telemetry..."
}) => {
  const [logIndex, setLogIndex] = useState<number>(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setLogIndex((prev) => (prev < BOOT_LOGS.length - 1 ? prev + 1 : prev));
    }, 140);
    return () => clearInterval(interval);
  }, []);

  return (
    <motion.div 
      initial={{ opacity: 1 }}
      exit={{ opacity: 0, filter: "blur(10px)", transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1] } }}
      className="fixed inset-0 bg-[#050508] z-50 flex flex-col items-center justify-center font-mono selection:bg-primary selection:text-black bg-grid-pattern overflow-hidden"
    >
      {/* Background ambient cyan & purple cyber-glow sweep */}
      <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(ellipse_at_center,rgba(56,251,219,0.08)_0%,rgba(142,82,245,0.04)_45%,transparent_70%)]" />

      <AnimatedGroup className="flex flex-col items-center space-y-6 max-w-md text-center px-4 relative z-10">
        {/* Animated Brand Shield Container with Cyan Glow */}
        <div className="relative w-20 h-20 rounded-2xl bg-gradient-to-br from-[#0C1E3E] to-[#07152b] border border-primary/40 flex items-center justify-center shadow-[0_0_30px_rgba(56,251,219,0.3)]">
          {/* Subtle radar pulse ring */}
          <div className="absolute inset-0 rounded-2xl border border-primary/30 animate-ping opacity-20" />

          {/* Logo icon */}
          <div className="w-11 h-11 flex items-center justify-center">
            <img 
              src="/logo.png" 
              alt="FedSanitize Logo" 
              className="w-full h-full object-contain drop-shadow-[0_0_12px_rgba(56,251,219,0.6)]" 
              onError={(e) => {
                // Fallback icon if image path differs
                (e.target as HTMLElement).style.display = "none";
              }}
            />
            <ShieldCheck className="w-10 h-10 text-primary hidden only:block" />
          </div>
        </div>

        {/* Wordmark revealed via TextEffect */}
        <div className="space-y-1.5">
          <div className="text-2xl font-bold tracking-widest uppercase flex items-center justify-center gap-1">
            <span className="text-primary drop-shadow-[0_0_12px_rgba(56,251,219,0.5)]">FED</span>
            <span className="text-secondary drop-shadow-[0_0_12px_rgba(142,82,245,0.5)]">
              <TextEffect per="char" delay={0.15}>
                SANITIZE
              </TextEffect>
            </span>
          </div>
          <div className="text-[11px] text-[#7B8AA3] tracking-widest uppercase font-semibold">
            Federated Threat-Defense Console
          </div>
        </div>

        {/* Terminal Boot Sequence Logs */}
        <div className="w-full bg-[#0C1E3E]/90 border border-primary/25 rounded-xl p-3.5 text-left shadow-[0_4px_24px_rgba(0,0,0,0.6)] max-w-sm backdrop-blur-sm">
          <div className="flex items-center justify-between border-b border-border/80 pb-2 mb-2.5 text-[10px] text-[#7B8AA3] uppercase tracking-wider">
            <span className="flex items-center gap-1.5 text-primary font-bold">
              <Terminal className="w-3 h-3" />
              Terminal Boot Log
            </span>
            <span className="flex items-center gap-1 text-accent-safe font-bold">
              <span className="w-1.5 h-1.5 rounded-full bg-accent-safe animate-pulse" />
              <span>LIVE</span>
            </span>
          </div>
          <div className="space-y-1.5 font-mono text-[11px]">
            {BOOT_LOGS.slice(0, logIndex + 1).map((log, i) => (
              <motion.div 
                key={i}
                initial={{ opacity: 0, x: -6 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.18 }}
                className={i === logIndex ? "text-primary font-semibold flex items-center justify-between" : "text-[#7B8AA3]"}
              >
                <span className="truncate pr-1">{log}</span>
                {i === logIndex && <span className="animate-pulse text-secondary">_</span>}
              </motion.div>
            ))}
          </div>
        </div>

        {/* Status Indicator Floor */}
        <div className="flex items-center gap-2 text-xs text-[#7B8AA3] font-mono">
          <span className="w-2 h-2 rounded-full bg-accent-safe shadow-[0_0_8px_#20D9A0]" />
          <span>{statusText}</span>
        </div>
      </AnimatedGroup>
    </motion.div>
  );
};
