import React from "react";
import { 
  ShieldAlert, 
  LayoutDashboard, 
  Users, 
  ShieldCheck, 
  Swords, 
  BarChart3, 
  Sliders, 
  Cpu, 
  Database, 
  BookOpen 
} from "lucide-react";
import { AnimatedBackground } from "../core/AnimatedBackground";

export type NavPage = "overview" | "clients" | "defense" | "attacks" | "analytics" | "config" | "arena";

interface SidebarProps {
  currentPage: NavPage;
  onSelectPage: (page: NavPage) => void;
  activeRounds: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentPage, onSelectPage, activeRounds }) => {
  const navItems = [
    { id: "arena", label: "Live Attack Arena", icon: ShieldAlert, isLive: true },
    { id: "overview", label: "Overview", icon: LayoutDashboard },
    { id: "clients", label: "Client Profiling", icon: Users },
    { id: "defense", label: "3-Layer Defense", icon: ShieldCheck },
    { id: "attacks", label: "Attack Playground", icon: Swords },
    { id: "analytics", label: "Comparative Analytics", icon: BarChart3 },
    { id: "config", label: "System Configuration", icon: Sliders },
  ];

  return (
    <aside className="w-72 bg-surface border-r border-border flex flex-col justify-between h-screen select-none shrink-0 threat-card z-20">
      {/* Brand Header */}
      <div>
        <div className="p-6 border-b border-border flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-surface-elevated border border-border flex items-center justify-center shadow-glow-red">
            <ShieldAlert className="w-6 h-6 text-accent-red" />
          </div>
          <div>
            <div className="text-xs font-mono tracking-widest text-accent-red uppercase font-bold">
              FedSanitize
            </div>
            <div className="text-[11px] font-mono text-text-secondary">
              Threat-Defense Console
            </div>
          </div>
        </div>

        {/* Navigation Items with AnimatedBackground */}
        <div className="p-4 space-y-1.5">
          <div className="text-[10px] font-mono uppercase tracking-wider text-text-secondary px-3 py-1 font-semibold">
            Security Telemetry
          </div>

          <div className="flex flex-col space-y-1">
            <AnimatedBackground
              defaultValue={currentPage}
              onValueChange={(id) => id && onSelectPage(id as NavPage)}
              className="bg-surface-elevated border-l-[3px] border-accent-red rounded-lg shadow-glow-red"
              transition={{
                type: "spring",
                bounce: 0.15,
                duration: 0.32,
              }}
            >
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = currentPage === item.id;
                return (
                  <button
                    key={item.id}
                    data-id={item.id}
                    type="button"
                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-mono text-left group transition-all duration-200 ${
                      isActive 
                        ? "text-white font-bold" 
                        : "text-zinc-400 hover:text-red-300 hover:bg-red-950/20"
                    }`}
                  >
                    <Icon className={`w-4 h-4 shrink-0 transition-colors duration-200 ${
                      isActive 
                        ? "text-accent-red" 
                        : "text-zinc-500 group-hover:text-red-400"
                    }`} />
                    <span className="truncate">{item.label}</span>
                    {item.id === "arena" && (
                      <span className="ml-auto text-[9px] bg-red-600/30 text-accent-red border border-red-500/50 px-1.5 py-0.2 rounded font-bold shrink-0 flex items-center gap-1 animate-pulse">
                        <span className="w-1.5 h-1.5 rounded-full bg-accent-red" />
                        LIVE
                      </span>
                    )}
                    {item.id === "overview" && activeRounds > 0 && (
                      <span className="ml-auto text-[10px] bg-accent-red/20 text-accent-red border border-accent-red/40 px-1.5 py-0.5 rounded font-bold shrink-0">
                        R{activeRounds}
                      </span>
                    )}
                  </button>
                );
              })}
            </AnimatedBackground>
          </div>
        </div>
      </div>

      {/* System Telemetry Sidebar Card */}
      <div className="p-4 border-t border-border">
        <div className="bg-surface-elevated border border-border rounded-lg p-3 space-y-2 text-[11px] font-mono shadow-sm">
          <div className="flex items-center justify-between text-text-secondary border-b border-border/50 pb-1.5">
            <span className="text-[10px] uppercase tracking-wider font-semibold text-accent-red">
              System Telemetry
            </span>
            <span className="flex items-center gap-1.5 text-accent-safe text-[10px]">
              <span className="w-1.5 h-1.5 rounded-full bg-accent-safe animate-pulse" />
              ONLINE
            </span>
          </div>

          <div className="space-y-1 text-text-secondary">
            <div className="flex items-center gap-1.5">
              <Cpu className="w-3 h-3 text-accent-red" />
              <span className="text-text-primary font-medium">SmallCNN</span> (2 Conv, 2 FC)
            </div>
            <div className="flex items-center gap-1.5">
              <Database className="w-3 h-3 text-accent-red" />
              <span>MNIST Dirichlet (α=0.5)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <ShieldCheck className="w-3 h-3 text-accent-safe" />
              <span className="text-text-primary">3-Layer Firewall</span>
            </div>
          </div>

          <div className="pt-1.5 border-t border-border/50 text-[10px] text-text-secondary">
            <div className="flex items-center gap-1 text-accent-warning">
              <BookOpen className="w-3 h-3" />
              <span>MARS (NeurIPS 2025)</span>
            </div>
            <div className="truncate text-text-secondary/70">arXiv:2509.20383</div>
          </div>
        </div>
        <div className="mt-3 text-[10px] font-mono text-text-secondary/50 text-center tracking-tight">
          © 2026 FedSanitize. All rights reserved.
        </div>
      </div>
    </aside>
  );
};
