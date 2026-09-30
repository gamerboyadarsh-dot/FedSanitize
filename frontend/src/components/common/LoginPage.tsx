import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  ShieldCheck, Key, Lock, User, Server,
  AlertCircle, CheckCircle2, Eye, EyeOff,
  ShieldAlert, Activity, Cpu, Info,
} from "lucide-react";
import { loginAdmin, loginClient } from "../../api/auth";

interface LoginPageProps {
  onAuthenticated: () => void;
  onGuest: () => void;
}

const STATS = [
  { label: "Clean Accuracy", value: 97.85, suffix: "%", decimals: 2 },
  { label: "Backdoor ASR",   value: 0.21,  suffix: "%", decimals: 2 },
  { label: "Attackers Isolated", value: 100, suffix: "%", decimals: 0 },
];

const FEATURES = [
  {
    icon: ShieldCheck,
    title: "Multi-Layer Byzantine Defense",
    desc: "MAD + MARS + TrimmedMean stacked firewall pipeline",
  },
  {
    icon: Activity,
    title: "MARS Backdoor Forensics",
    desc: "NeurIPS 2025 robust aggregation with live threat telemetry",
  },
  {
    icon: Cpu,
    title: "JWT Role-Based Access Control",
    desc: "Zero-trust auth with admin, edge-client, and guest tiers",
  },
];

interface CanvasNode {
  x: number; y: number; vx: number; vy: number; r: number;
  malicious: boolean; quarantined: boolean; quarantineTimer: number; pulsePhase: number;
}
interface CanvasEdge { a: number; b: number; pulsePos: number; }

function NetworkCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const stateRef = useRef<{ nodes: CanvasNode[]; edges: CanvasEdge[]; frame: number }>(
    { nodes: [], edges: [], frame: 0 }
  );
  const rafRef = useRef<number>(0);
  const prefersReduced = useRef(
    typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );

  const initNodes = useCallback((w: number, h: number) => {
    const cx = w * 0.5, cy = h * 0.5;
    const nodes: CanvasNode[] = [
      { x: cx, y: cy, vx: 0, vy: 0, r: 18, malicious: false, quarantined: false, quarantineTimer: 0, pulsePhase: 0 },
    ];
    const count = 9;
    for (let i = 0; i < count; i++) {
      const angle = (i / count) * Math.PI * 2 + Math.random() * 0.4;
      const dist = Math.min(w, h) * (0.28 + Math.random() * 0.1);
      nodes.push({
        x: cx + Math.cos(angle) * dist,
        y: cy + Math.sin(angle) * dist,
        vx: (Math.random() - 0.5) * 0.18,
        vy: (Math.random() - 0.5) * 0.18,
        r: 7 + Math.random() * 5,
        malicious: i >= count - 2,
        quarantined: false,
        quarantineTimer: 0,
        pulsePhase: Math.random() * Math.PI * 2,
      });
    }
    const edges: CanvasEdge[] = nodes.slice(1).map((_: CanvasNode, i: number) => ({
      a: 0, b: i + 1, pulsePos: Math.random(),
    }));
    stateRef.current = { nodes, edges, frame: 0 };
  }, []);

  useEffect(() => {
    if (prefersReduced.current) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dpr = window.devicePixelRatio || 1;
    const resize = () => {
      canvas.width = canvas.offsetWidth * dpr;
      canvas.height = canvas.offsetHeight * dpr;
      initNodes(canvas.offsetWidth, canvas.offsetHeight);
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);

    const draw = () => {
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      const { nodes, edges } = stateRef.current;
      const W = canvas.width / dpr, H = canvas.height / dpr;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.save();
      ctx.scale(dpr, dpr);

      stateRef.current.frame++;
      const frame = stateRef.current.frame;
      if (frame % 320 === 0) {
        nodes.forEach((n: CanvasNode) => {
          if (n.malicious) { n.quarantined = true; n.quarantineTimer = 70; }
        });
      }
      nodes.forEach((n: CanvasNode) => {
        if (n.quarantineTimer > 0) { n.quarantineTimer--; if (n.quarantineTimer === 0) n.quarantined = false; }
      });
      nodes.slice(1).forEach((n: CanvasNode) => {
        n.x += n.vx; n.y += n.vy;
        if (n.x < 30 || n.x > W - 30) n.vx *= -1;
        if (n.y < 30 || n.y > H - 30) n.vy *= -1;
      });

      edges.forEach((e: CanvasEdge) => {
        const a = nodes[e.a], b = nodes[e.b];
        if (b.quarantined) return;
        ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y);
        ctx.strokeStyle = "rgba(56,251,219,0.07)"; ctx.lineWidth = 1; ctx.stroke();
        e.pulsePos = (e.pulsePos + 0.004) % 1;
        const px = a.x + (b.x - a.x) * e.pulsePos;
        const py = a.y + (b.y - a.y) * e.pulsePos;
        ctx.beginPath(); ctx.arc(px, py, 2.5, 0, Math.PI * 2);
        ctx.fillStyle = b.malicious ? "rgba(255,59,92,0.7)" : "rgba(56,251,219,0.7)";
        ctx.fill();
      });

      nodes.forEach((n: CanvasNode, i: number) => {
        n.pulsePhase += 0.04;
        const alpha = n.quarantined ? (0.2 + Math.sin(n.pulsePhase * 4) * 0.2) : 1;
        if (i === 0) {
          const glowR = n.r + 10 + Math.sin(n.pulsePhase) * 4;
          const glow = ctx.createRadialGradient(n.x, n.y, n.r, n.x, n.y, glowR);
          glow.addColorStop(0, "rgba(56,251,219,0.25)");
          glow.addColorStop(1, "rgba(56,251,219,0)");
          ctx.beginPath(); ctx.arc(n.x, n.y, glowR, 0, Math.PI * 2);
          ctx.fillStyle = glow; ctx.fill();
          ctx.beginPath(); ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
          ctx.fillStyle = "rgba(13,32,64,0.9)"; ctx.fill();
          ctx.strokeStyle = "rgba(56,251,219,0.6)"; ctx.lineWidth = 1.5; ctx.stroke();
        } else {
          const isMal = n.malicious;
          ctx.beginPath(); ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
          ctx.fillStyle = isMal
            ? `rgba(255,59,92,${0.15 * alpha})`
            : `rgba(56,251,219,${0.15 * alpha})`;
          ctx.fill();
          ctx.strokeStyle = isMal
            ? `rgba(255,59,92,${0.5 * alpha})`
            : `rgba(56,251,219,${0.5 * alpha})`;
          ctx.lineWidth = 1; ctx.stroke();
          if (n.quarantined) {
            ctx.beginPath(); ctx.arc(n.x, n.y, n.r + 6, 0, Math.PI * 2);
            ctx.strokeStyle = "rgba(255,59,92,0.5)"; ctx.lineWidth = 1.5; ctx.stroke();
          }
        }
      });
      ctx.restore();
      rafRef.current = requestAnimationFrame(draw);
    };
    rafRef.current = requestAnimationFrame(draw);
    return () => { cancelAnimationFrame(rafRef.current); ro.disconnect(); };
  }, [initNodes]);

  if (prefersReduced.current) return null;
  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full opacity-55 pointer-events-none"
      aria-hidden="true"
    />
  );
}

function useCountUp(target: number, decimals: number, duration = 1800): number {
  const [val, setVal] = useState(0);
  const prefersReduced =
    typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  useEffect(() => {
    if (prefersReduced) { setVal(target); return; }
    let start: number | null = null;
    const step = (ts: number) => {
      if (!start) start = ts;
      const prog = Math.min((ts - start) / duration, 1);
      const eased = 1 - Math.pow(1 - prog, 3);
      setVal(parseFloat((eased * target).toFixed(decimals)));
      if (prog < 1) requestAnimationFrame(step);
    };
    const raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [target, decimals, duration, prefersReduced]);
  return val;
}

function StatItem({
  label, value, suffix, decimals,
}: { label: string; value: number; suffix: string; decimals: number }) {
  const displayed = useCountUp(value, decimals);
  return (
    <div className="flex flex-col items-center gap-0.5">
      <span className="text-lg font-bold font-mono" style={{ color: "#38fbdb" }}>
        {displayed.toFixed(decimals)}{suffix}
      </span>
      <span className="text-[10px] uppercase tracking-widest" style={{ color: "#7B8AA3" }}>
        {label}
      </span>
    </div>
  );
}

export const LoginPage: React.FC<LoginPageProps> = ({ onAuthenticated, onGuest }) => {
  // --- Existing state (unchanged) ---
  const [mode, setMode] = useState<"admin" | "client">("admin");
  const [adminUser, setAdminUser] = useState("admin");
  const [adminPass, setAdminPass] = useState("admin123");
  const [showAdminPass, setShowAdminPass] = useState(false);
  const [clientId, setClientId] = useState("C0");
  const [clientSecret, setClientSecret] = useState("clientsecret123");
  const [showClientSecret, setShowClientSecret] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // --- Visual-only state ---
  const [shake, setShake] = useState(false);
  const [visible, setVisible] = useState(false);
  useEffect(() => { const t = setTimeout(() => setVisible(true), 50); return () => clearTimeout(t); }, []);

  // --- Existing handler (unchanged) ---
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true); setError(null); setSuccessMsg(null);
    try {
      if (mode === "admin") {
        await loginAdmin(adminUser, adminPass);
        setSuccessMsg("Authenticated as Admin");
      } else {
        await loginClient(clientId, clientSecret);
        setSuccessMsg("Authenticated as Edge Client " + clientId);
      }
      setTimeout(() => onAuthenticated(), 800);
    } catch (err: any) {
      setError(err.message || "Authentication failed");
      setShake(true); setTimeout(() => setShake(false), 600);
    } finally { setIsLoading(false); }
  };

  const inputCls =
    "w-full pl-10 pr-4 py-3 rounded-xl text-sm outline-none transition-all duration-200 font-mono";
  const inputStyle: React.CSSProperties = {
    background: "rgba(13,32,64,0.6)",
    border: "1px solid rgba(56,251,219,0.15)",
    color: "#E8F1F5",
  };
  const onFocusInput = (e: React.FocusEvent<HTMLInputElement>) => {
    e.target.style.borderColor = "rgba(56,251,219,0.6)";
    e.target.style.boxShadow = "0 0 0 3px rgba(56,251,219,0.08)";
  };
  const onBlurInput = (e: React.FocusEvent<HTMLInputElement>) => {
    e.target.style.borderColor = "rgba(56,251,219,0.15)";
    e.target.style.boxShadow = "none";
  };

  const bgGradient =
    "radial-gradient(ellipse 70% 60% at 20% 40%, rgba(56,251,219,0.06) 0%, transparent 65%), " +
    "radial-gradient(ellipse 60% 50% at 80% 70%, rgba(99,102,241,0.07) 0%, transparent 65%), " +
    "linear-gradient(135deg, #020510 0%, #050a1a 40%, #030610 100%)";

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center overflow-hidden"
      style={{ fontFamily: "Inter, system-ui, sans-serif", background: bgGradient }}
    >
      {/* Grid overlay */}
      <div
        className="absolute inset-0 pointer-events-none opacity-[0.025]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(56,251,219,1) 1px, transparent 1px), " +
            "linear-gradient(90deg, rgba(56,251,219,1) 1px, transparent 1px)",
          backgroundSize: "48px 48px",
        }}
        aria-hidden="true"
      />

      {/* LEFT HERO */}
      <div
        className="hidden lg:flex flex-1 flex-col justify-between h-full px-14 py-12 relative overflow-hidden"
        style={{
          opacity: visible ? 1 : 0,
          transform: visible ? "translateX(0)" : "translateX(-24px)",
          transition: "opacity 0.6s ease, transform 0.6s ease",
        }}
      >
        <NetworkCanvas />

        {/* Brand */}
        <div className="relative z-10">
          <div className="flex items-center gap-4 mb-5">
            <div className="relative w-14 h-14 flex items-center justify-center">
              <div
                className="absolute inset-0 rounded-full animate-pulse"
                style={{
                  background: "radial-gradient(circle, rgba(56,251,219,0.25) 0%, transparent 70%)",
                  transform: "scale(1.6)",
                }}
                aria-hidden="true"
              />
              <div
                className="w-14 h-14 rounded-2xl flex items-center justify-center relative z-10"
                style={{
                  background: "rgba(13,32,64,0.9)",
                  border: "1px solid rgba(56,251,219,0.35)",
                  boxShadow: "0 0 28px rgba(56,251,219,0.2)",
                }}
              >
                <img
                  src="/logo.png"
                  alt="FedSanitize Logo"
                  className="w-9 h-9 object-contain"
                  onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                />
              </div>
            </div>
            <div>
              <h1
                className="text-3xl font-black tracking-tight"
                style={{
                  background: "linear-gradient(135deg, #38fbdb 0%, #5effe3 40%, #a78bfa 100%)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                FedSanitize
              </h1>
              <p
                className="text-sm font-mono tracking-widest mt-0.5"
                style={{ color: "#38d9c0" }}
              >
                Zero-Trust Federated Learning Defense
              </p>
            </div>
          </div>
          <p className="text-base max-w-sm leading-relaxed" style={{ color: "#7B8AA3" }}>
            A production-grade 3-layer security firewall safeguarding distributed ML systems against
            Byzantine poisoning and backdoor attacks.
          </p>
        </div>

        {/* Feature cards */}
        <div
          className="relative z-10 flex flex-col gap-3 my-6"
          style={{
            opacity: visible ? 1 : 0,
            transform: visible ? "translateY(0)" : "translateY(16px)",
            transition: "opacity 0.6s ease 0.15s, transform 0.6s ease 0.15s",
          }}
        >
          {FEATURES.map(({ icon: Icon, title, desc }) => (
            <div
              key={title}
              className="flex items-start gap-4 p-4 rounded-2xl cursor-default"
              style={{
                background: "rgba(13,32,64,0.45)",
                border: "1px solid rgba(56,251,219,0.10)",
                backdropFilter: "blur(10px)",
                transition: "transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = "translateY(-3px)";
                e.currentTarget.style.borderColor = "rgba(56,251,219,0.35)";
                e.currentTarget.style.boxShadow = "0 8px 30px rgba(56,251,219,0.08)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = "translateY(0)";
                e.currentTarget.style.borderColor = "rgba(56,251,219,0.10)";
                e.currentTarget.style.boxShadow = "none";
              }}
            >
              <div
                className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0"
                style={{ background: "rgba(56,251,219,0.08)", border: "1px solid rgba(56,251,219,0.2)" }}
              >
                <Icon className="w-4 h-4" style={{ color: "#38fbdb" }} />
              </div>
              <div>
                <div className="text-sm font-semibold mb-0.5" style={{ color: "#E8F1F5" }}>
                  {title}
                </div>
                <div className="text-xs" style={{ color: "#7B8AA3" }}>{desc}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Live stats strip */}
        <div
          className="relative z-10"
          style={{ opacity: visible ? 1 : 0, transition: "opacity 0.6s ease 0.3s" }}
        >
          <div
            className="flex items-center justify-between px-6 py-4 rounded-2xl"
            style={{
              background: "rgba(13,32,64,0.5)",
              border: "1px solid rgba(56,251,219,0.12)",
              backdropFilter: "blur(10px)",
            }}
          >
            {STATS.map((s, i) => (
              <React.Fragment key={s.label}>
                <StatItem {...s} />
                {i < STATS.length - 1 && (
                  <div className="w-px h-8" style={{ background: "rgba(56,251,219,0.12)" }} />
                )}
              </React.Fragment>
            ))}
          </div>
          <p className="text-center text-[11px] mt-3 font-mono" style={{ color: "#4B5563" }}>
            Built on MARS (NeurIPS 2025) robust aggregation
          </p>
        </div>
      </div>

      {/* RIGHT LOGIN CARD */}
      <div
        className="flex items-center justify-center w-full lg:w-auto lg:min-w-[520px] h-full px-4 py-8 lg:px-14"
        style={{
          opacity: visible ? 1 : 0,
          transform: visible ? "translateX(0)" : "translateX(24px)",
          transition: "opacity 0.6s ease 0.1s, transform 0.6s ease 0.1s",
        }}
      >
        <div
          className="w-full max-w-[440px]"
          style={{ animation: shake ? "loginShake 0.5s ease" : "none" }}
        >
          <style>
            {`@keyframes loginShake{0%,100%{transform:translateX(0)}15%{transform:translateX(-8px)}30%{transform:translateX(8px)}45%{transform:translateX(-5px)}60%{transform:translateX(5px)}75%{transform:translateX(-2px)}}`}
          </style>

          <div
            className="rounded-3xl p-8"
            style={{
              background: "rgba(8,16,38,0.78)",
              border: "1px solid rgba(56,251,219,0.18)",
              backdropFilter: "blur(24px)",
              boxShadow:
                "0 0 60px rgba(56,251,219,0.06), 0 24px 60px rgba(0,0,0,0.5), inset 0 1px 0 rgba(56,251,219,0.08)",
            }}
          >
            {/* Mobile logo */}
            <div className="flex lg:hidden items-center gap-3 mb-6">
              <div
                className="w-9 h-9 rounded-xl flex items-center justify-center"
                style={{ background: "rgba(13,32,64,0.9)", border: "1px solid rgba(56,251,219,0.3)" }}
              >
                <img
                  src="/logo.png" alt="FedSanitize" className="w-6 h-6 object-contain"
                  onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                />
              </div>
              <span
                className="font-black text-base"
                style={{
                  background: "linear-gradient(135deg,#38fbdb,#a78bfa)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                FedSanitize
              </span>
            </div>

            {/* Heading */}
            <div className="mb-7">
              <h2 className="text-2xl font-bold mb-1" style={{ color: "#F0F6FF" }}>
                Welcome back
              </h2>
              <p className="text-sm" style={{ color: "#7B8AA3" }}>
                Sign in to your FedSanitize console
              </p>
            </div>

            {/* Role switcher */}
            <div
              className="flex p-1 rounded-2xl mb-6"
              style={{
                background: "rgba(13,32,64,0.7)",
                border: "1px solid rgba(56,251,219,0.1)",
              }}
              role="tablist"
              aria-label="Authentication mode"
            >
              {(["admin", "client"] as const).map((m) => (
                <button
                  key={m}
                  type="button"
                  role="tab"
                  aria-selected={mode === m}
                  onClick={() => { setMode(m); setError(null); }}
                  className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200"
                  style={
                    mode === m
                      ? {
                          background: "linear-gradient(135deg, rgba(56,251,219,0.18), rgba(99,102,241,0.12))",
                          color: "#38fbdb",
                          border: "1px solid rgba(56,251,219,0.3)",
                          boxShadow: "0 0 16px rgba(56,251,219,0.1)",
                        }
                      : { color: "#7B8AA3", border: "1px solid transparent" }
                  }
                >
                  {m === "admin" ? <User className="w-4 h-4" /> : <Server className="w-4 h-4" />}
                  {m === "admin" ? "Admin" : "Edge Client"}
                </button>
              ))}
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
              {mode === "admin" ? (
                <>
                  <div>
                    <label
                      htmlFor="lp-admin-user"
                      className="block text-xs font-semibold mb-2"
                      style={{ color: "#94a3b8" }}
                    >
                      Username
                    </label>
                    <div className="relative">
                      <User
                        className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none"
                        style={{ color: "#38fbdb" }}
                      />
                      <input
                        id="lp-admin-user"
                        type="text"
                        value={adminUser}
                        onChange={(e) => setAdminUser(e.target.value)}
                        className={inputCls}
                        style={inputStyle}
                        onFocus={onFocusInput}
                        onBlur={onBlurInput}
                        placeholder="admin"
                        autoComplete="username"
                        aria-label="Admin username"
                      />
                    </div>
                  </div>
                  <div>
                    <label
                      htmlFor="lp-admin-pass"
                      className="block text-xs font-semibold mb-2"
                      style={{ color: "#94a3b8" }}
                    >
                      Password
                    </label>
                    <div className="relative">
                      <Lock
                        className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none"
                        style={{ color: "#38fbdb" }}
                      />
                      <input
                        id="lp-admin-pass"
                        type={showAdminPass ? "text" : "password"}
                        value={adminPass}
                        onChange={(e) => setAdminPass(e.target.value)}
                        className={inputCls}
                        style={{ ...inputStyle, paddingRight: "2.75rem" }}
                        onFocus={onFocusInput}
                        onBlur={onBlurInput}
                        placeholder="Password"
                        autoComplete="current-password"
                        aria-label="Admin password"
                      />
                      <button
                        type="button"
                        onClick={() => setShowAdminPass((v) => !v)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 transition-colors duration-150"
                        style={{ color: "#7B8AA3" }}
                        aria-label={showAdminPass ? "Hide password" : "Show password"}
                      >
                        {showAdminPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                </>
              ) : (
                <>
                  <div>
                    <label
                      htmlFor="lp-client-id"
                      className="block text-xs font-semibold mb-2"
                      style={{ color: "#94a3b8" }}
                    >
                      Client ID
                    </label>
                    <div className="relative">
                      <Server
                        className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none"
                        style={{ color: "#38fbdb" }}
                      />
                      <input
                        id="lp-client-id"
                        type="text"
                        value={clientId}
                        onChange={(e) => setClientId(e.target.value)}
                        className={inputCls}
                        style={inputStyle}
                        onFocus={onFocusInput}
                        onBlur={onBlurInput}
                        placeholder="C0"
                        aria-label="Edge client ID"
                      />
                    </div>
                  </div>
                  <div>
                    <label
                      htmlFor="lp-client-secret"
                      className="block text-xs font-semibold mb-2"
                      style={{ color: "#94a3b8" }}
                    >
                      Client Secret
                    </label>
                    <div className="relative">
                      <Lock
                        className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none"
                        style={{ color: "#38fbdb" }}
                      />
                      <input
                        id="lp-client-secret"
                        type={showClientSecret ? "text" : "password"}
                        value={clientSecret}
                        onChange={(e) => setClientSecret(e.target.value)}
                        className={inputCls}
                        style={{ ...inputStyle, paddingRight: "2.75rem" }}
                        onFocus={onFocusInput}
                        onBlur={onBlurInput}
                        placeholder="Client secret"
                        aria-label="Edge client secret"
                      />
                      <button
                        type="button"
                        onClick={() => setShowClientSecret((v) => !v)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 transition-colors duration-150"
                        style={{ color: "#7B8AA3" }}
                        aria-label={showClientSecret ? "Hide secret" : "Show secret"}
                      >
                        {showClientSecret ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                </>
              )}

              {error && (
                <div
                  className="flex items-center gap-2.5 px-4 py-3 rounded-xl text-sm"
                  style={{
                    background: "rgba(255,59,92,0.08)",
                    border: "1px solid rgba(255,59,92,0.3)",
                    color: "#ff6b6b",
                  }}
                  role="alert"
                >
                  <ShieldAlert className="w-4 h-4 shrink-0" />
                  <span>{error}</span>
                </div>
              )}
              {successMsg && (
                <div
                  className="flex items-center gap-2.5 px-4 py-3 rounded-xl text-sm"
                  style={{
                    background: "rgba(32,217,160,0.08)",
                    border: "1px solid rgba(32,217,160,0.3)",
                    color: "#20d9a0",
                  }}
                  role="status"
                >
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  <span>{successMsg}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={isLoading}
                className="w-full flex items-center justify-center gap-2.5 py-3 rounded-xl text-sm font-bold transition-all duration-200 mt-1 disabled:opacity-60"
                style={{
                  background: isLoading
                    ? "rgba(56,251,219,0.1)"
                    : "linear-gradient(135deg, #0d4f6e 0%, #0a3d5c 40%, #1a1a6e 100%)",
                  color: "#38fbdb",
                  border: "1px solid rgba(56,251,219,0.35)",
                  boxShadow: "0 0 24px rgba(56,251,219,0.18)",
                }}
                onMouseEnter={(e) => {
                  if (!isLoading) {
                    e.currentTarget.style.boxShadow = "0 0 36px rgba(56,251,219,0.35)";
                    e.currentTarget.style.transform = "translateY(-1px)";
                  }
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.boxShadow = "0 0 24px rgba(56,251,219,0.18)";
                  e.currentTarget.style.transform = "translateY(0)";
                }}
                onMouseDown={(e) => { e.currentTarget.style.transform = "translateY(1px)"; }}
                onMouseUp={(e)   => { e.currentTarget.style.transform = "translateY(-1px)"; }}
              >
                {isLoading ? (
                  <>
                    <span
                      className="w-4 h-4 border-2 rounded-full animate-spin"
                      style={{ borderColor: "rgba(56,251,219,0.3)", borderTopColor: "#38fbdb" }}
                    />
                    Authenticating...
                  </>
                ) : (
                  <>
                    <Key className="w-4 h-4" />
                    Sign In
                  </>
                )}
              </button>
            </form>

            {/* Divider */}
            <div className="flex items-center gap-3 my-5">
              <div className="flex-1 h-px" style={{ background: "rgba(56,251,219,0.08)" }} />
              <span className="text-xs font-mono" style={{ color: "#4B5563" }}>or</span>
              <div className="flex-1 h-px" style={{ background: "rgba(56,251,219,0.08)" }} />
            </div>

            {/* Guest */}
            <button
              type="button"
              onClick={onGuest}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold transition-all duration-200"
              style={{
                border: "1px solid rgba(56,251,219,0.15)",
                background: "rgba(56,251,219,0.03)",
                color: "#7B8AA3",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = "rgba(56,251,219,0.35)";
                e.currentTarget.style.background = "rgba(56,251,219,0.07)";
                e.currentTarget.style.color = "#E8F1F5";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "rgba(56,251,219,0.15)";
                e.currentTarget.style.background = "rgba(56,251,219,0.03)";
                e.currentTarget.style.color = "#7B8AA3";
              }}
            >
              <Lock className="w-4 h-4" />
              Continue as Guest
            </button>

            {/* Demo badge */}
            <div className="flex items-center justify-center gap-1.5 mt-4">
              <span
                className="flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-mono"
                style={{
                  background: "rgba(56,251,219,0.06)",
                  border: "1px solid rgba(56,251,219,0.12)",
                  color: "#7B8AA3",
                }}
              >
                <Info className="w-3 h-3" style={{ color: "#38fbdb" }} />
                Demo mode - credentials pre-filled
              </span>
            </div>

            {/* Trust row */}
            <div className="flex items-center justify-center gap-1.5 mt-3">
              <Lock className="w-3 h-3" style={{ color: "#4B5563" }} />
              <span className="text-[11px] font-mono" style={{ color: "#4B5563" }}>
                Secured with JWT - Role-based access
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
