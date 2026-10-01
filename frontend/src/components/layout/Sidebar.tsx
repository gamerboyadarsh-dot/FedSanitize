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
  BookOpen,
  Award
} from "lucide-react";
import { AnimatedBackground } from "../core/AnimatedBackground";

export type NavPage = "overview" | "clients" | "defense" | "attacks" | "analytics" | "arena" | "security-intelligence" | "config";

interface SidebarProps {
  currentPage: NavPage;
  onSelectPage: (page: NavPage) => void;
  activeRounds: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentPage, onSelectPage, activeRounds }) => {
  const navGroups = [
    {
      title: "Core Dashboards",
      items: [
        { id: "overview", label: "Overview", icon: LayoutDashboard },
        { id: "analytics", label: "Comparative Analytics", icon: BarChart3 },
      ]
    },
    {
      title: "Threat Pipeline",
      items: [
        { id: "clients", label: "Client Profiling", icon: Users },
        { id: "defense", label: "3-Layer Defense", icon: ShieldCheck },
        { id: "security-intelligence", label: "Security Intelligence", icon: Award },
      ]
    },
    {
      title: "Adversarial Arena",
      items: [
        { id: "attacks", label: "Attack Playground", icon: Swords },
        { id: "arena", label: "Live Attack Arena", icon: ShieldAlert },
      ]
    },
    {
      title: "System Settings",
      items: [
        { id: "config", label: "System Configuration", icon: Sliders },
      ]
    }
  ];

  return (
    <aside className="w-72 bg-surface border-r border-border flex flex-col justify-between h-screen select-none shrink-0 z-20 group">
      {/* Brand Header — no patchy gradient, clean flat surface */}
      <div>
        <div className="p-6 border-b border-border flex items-center gap-3">
          <div className="w-10 h-10 flex items-center justify-center">
            <img src="/logo.png" alt="FedSanitize Logo" className="w-full h-full object-contain drop-shadow-[0_0_12px_rgba(56,251,219,0.45)] group-hover:drop-shadow-[0_0_20px_rgba(56,251,219,0.7)] transition-all duration-300" />
          </div>
          <div>
            <div className="text-xs font-mono tracking-widest bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent uppercase font-bold">
              FedSanitize
            </div>
            <div className="text-[11px] font-mono text-text-secondary">
              Threat-Defense Console
            </div>
          </div>
        </div>

        {/* Navigation Groups */}
        <div className="p-4 space-y-5 overflow-y-auto custom-scrollbar" style={{ maxHeight: "calc(100vh - 220px)" }}>
          {navGroups.map((group) => (
            <div key={group.title} className="flex flex-col space-y-1">
              {/* Eyebrow group label — uses .eyebrow CSS class from index.css */}
              <div className="eyebrow px-3 py-1 mb-0.5">
                {group.title}
              </div>

              <div className="flex flex-col space-y-0.5">
                <AnimatedBackground
                  defaultValue={group.items.some(i => i.id === currentPage) ? currentPage : undefined}
                  onValueChange={(id) => id && onSelectPage(id as NavPage)}
                  className="bg-[rgba(34,211,238,0.10)] border-l-[3px] border-[#22D3EE] rounded-lg shadow-glow-cyan"
                  transition={{
                    type: "spring",
                    bounce: 0.15,
                    duration: 0.32,
                  }}
                >
                  {group.items.map((item) => {
                    const Icon = item.icon;
                    const isActive = currentPage === item.id;
                    return (
                      <button
                        key={item.id}
                        data-id={item.id}
                        type="button"
                        /* Use nav-item CSS class; add .active when selected for the 3px left-bar pseudo-element */
                        className={`nav-item text-xs font-sans${isActive ? " active" : ""}`}
                        onClick={() => onSelectPage(item.id as NavPage)}
                      >
                        <Icon className={`w-4 h-4 shrink-0 transition-colors duration-200 ${
                          isActive 
                            ? "text-[#22D3EE]" 
                            : "text-zinc-500 group-hover:text-primary"
                        }`} />
                        <span className="truncate">{item.label}</span>
                        {item.id === "overview" && activeRounds > 0 && (
                          <span className="ml-auto text-[10px] bg-primary/20 text-primary border border-primary/40 px-1.5 py-0.5 rounded font-bold shrink-0">
                            R{activeRounds}
                          </span>
                        )}
                      </button>
                    );
                  })}
                </AnimatedBackground>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* System Telemetry Card — compact, font-sans labels */}
      <div className="p-4 border-t border-border">
        <div className="bg-surface-elevated border border-border rounded-lg p-3 space-y-2 shadow-sm">
          {/* Header row */}
          <div className="flex items-center justify-between border-b border-border/50 pb-1.5">
            <span className="text-[10px] uppercase tracking-wider font-semibold text-primary">
              System Telemetry
            </span>
            <span className="flex items-center gap-1.5 text-accent-safe text-[10px]">
              <span className="w-1.5 h-1.5 rounded-full bg-accent-safe animate-pulse" />
              ONLINE
            </span>
          </div>

          {/* Spec rows — font-sans, text-[11px] */}
          <div className="space-y-1 text-[11px] font-sans text-text-secondary">
            <div className="flex items-center gap-1.5">
              <Cpu className="w-3 h-3 text-primary shrink-0" />
              <span className="text-text-primary font-medium">SmallCNN</span>
              <span>(2 Conv, 2 FC)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Database className="w-3 h-3 text-primary shrink-0" />
              <span>MNIST Dirichlet (α=0.5)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <ShieldCheck className="w-3 h-3 text-accent-safe shrink-0" />
              <span className="text-text-primary">3-Layer Firewall</span>
            </div>
          </div>

          {/* Citation line — NeurIPS 2025 arXiv */}
          <div className="pt-1.5 border-t border-border/50">
            <div className="flex items-center gap-1 text-[11px] font-sans text-text-secondary/70">
              <BookOpen className="w-3 h-3 shrink-0" />
              <span className="truncate">NeurIPS 2025 - arXiv:2509.20383</span>
            </div>
          </div>
        </div>
        {/* Copyright removed from sidebar — moved to footer in App.tsx */}
      </div>
    </aside>
  );
};
