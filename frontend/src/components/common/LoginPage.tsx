import React, { useState } from "react";
import {
  ShieldCheck, Key, Lock, User, Server,
  AlertCircle, CheckCircle2, Eye, EyeOff,
} from "lucide-react";
import { loginAdmin, loginClient } from "../../api/auth";

interface LoginPageProps {
  onAuthenticated: () => void;
  onGuest: () => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onAuthenticated, onGuest }) => {
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setSuccessMsg(null);
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
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex" style={{ fontFamily: "Inter, system-ui, sans-serif" }}>

      {/* LEFT PANEL */}
      <div
        className="hidden lg:flex flex-col items-center justify-center flex-1 relative overflow-hidden"
        style={{ background: "linear-gradient(145deg, #080d1a 0%, #0a1628 50%, #060c1e 100%)" }}
      >
        <div className="absolute inset-0 opacity-20" style={{
          backgroundImage: "radial-gradient(circle, #38fbdb22 1px, transparent 1px)",
          backgroundSize: "32px 32px",
        }} />
        <div className="absolute top-1/4 left-1/4 w-80 h-80 rounded-full opacity-15 blur-3xl"
          style={{ background: "radial-gradient(circle, #38fbdb, transparent)" }} />
        <div className="absolute bottom-1/4 right-1/4 w-64 h-64 rounded-full opacity-10 blur-3xl"
          style={{ background: "radial-gradient(circle, #7c3aed, transparent)" }} />

        <div className="relative z-10 flex flex-col items-center gap-10 px-12 text-center max-w-md">
          <div className="flex flex-col items-center gap-5">
            <div className="w-28 h-28 rounded-2xl flex items-center justify-center shadow-2xl overflow-hidden"
              style={{
                background: "linear-gradient(135deg, #0f2a4a 0%, #0d2040 100%)",
                boxShadow: "0 0 60px rgba(56,251,219,0.25), 0 0 0 1px rgba(56,251,219,0.15)",
              }}>
              <img src="/logo.png" alt="FedSanitize" className="w-full h-full object-cover"
                onError={(e) => {
                  const img = e.target as HTMLImageElement;
                  img.style.display = "none";
                  const next = img.nextElementSibling as HTMLElement | null;
                  if (next) next.style.display = "flex";
                }}
              />
              <div className="w-full h-full items-center justify-center" style={{ display: "none" }}>
                <ShieldCheck className="w-14 h-14" style={{ color: "#38fbdb", filter: "drop-shadow(0 0 12px #38fbdb88)" }} />
              </div>
            </div>
            <div>
              <h1 className="text-4xl font-black tracking-tight mb-1" style={{ color: "#f0fdfd", letterSpacing: "-0.02em" }}>
                FedSanitize
              </h1>
              <p className="text-sm font-medium" style={{ color: "#38fbdb", opacity: 0.9 }}>
                Zero-Trust Federated Learning Defense
              </p>
            </div>
          </div>

          <div className="flex flex-col gap-3 w-full">
            {[
              { icon: "???", text: "Multi-Layer Byzantine Defense" },
              { icon: "??", text: "MARS Backdoor Forensics" },
              { icon: "??", text: "JWT Role-Based Access Control" },
            ].map((f) => (
              <div key={f.text} className="flex items-center gap-3 px-4 py-3 rounded-xl text-left text-sm"
                style={{ background: "rgba(56,251,219,0.06)", border: "1px solid rgba(56,251,219,0.12)", color: "#b0c8d4" }}>
                <span className="text-lg">{f.icon}</span>
                <span>{f.text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* RIGHT PANEL */}
      <div className="flex flex-col items-center justify-center w-full lg:w-[460px] xl:w-[500px] p-8 lg:p-12 relative"
        style={{ background: "#f8fafc" }}>

        {/* Mobile logo */}
        <div className="lg:hidden mb-8 flex flex-col items-center gap-2">
          <div className="w-14 h-14 rounded-xl flex items-center justify-center overflow-hidden"
            style={{ background: "#0d2040", boxShadow: "0 0 24px rgba(56,251,219,0.3)" }}>
            <img src="/logo.png" alt="FedSanitize" className="w-full h-full object-cover"
              onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }} />
          </div>
          <span className="font-black text-xl" style={{ color: "#0d2040" }}>FedSanitize</span>
        </div>

        <div className="w-full max-w-sm">
          <div className="mb-8">
            <h2 className="text-2xl font-bold mb-1" style={{ color: "#0f172a" }}>Welcome back</h2>
            <p className="text-sm" style={{ color: "#64748b" }}>Sign in to your FedSanitize console</p>
          </div>

          {/* Mode toggle */}
          <div className="flex p-1 rounded-xl mb-6" style={{ background: "#e2e8f0" }}>
            {(["admin", "client"] as const).map((m) => (
              <button key={m} type="button"
                onClick={() => { setMode(m); setError(null); }}
                className="flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-semibold transition-all duration-200"
                style={mode === m
                  ? { background: "#fff", color: "#0f172a", boxShadow: "0 1px 4px rgba(0,0,0,0.12)" }
                  : { color: "#64748b" }}>
                {m === "admin" ? <User className="w-4 h-4" /> : <Server className="w-4 h-4" />}
                {m === "admin" ? "Admin" : "Edge Client"}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {mode === "admin" ? (
              <>
                <div>
                  <label className="block text-xs font-semibold mb-1.5" style={{ color: "#374151" }}>Username</label>
                  <input type="text" value={adminUser} onChange={(e) => setAdminUser(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-lg text-sm outline-none"
                    style={{ border: "1.5px solid #e2e8f0", background: "#fff", color: "#0f172a" }}
                    onFocus={(e) => (e.target.style.borderColor = "#38fbdb")}
                    onBlur={(e) => (e.target.style.borderColor = "#e2e8f0")}
                    placeholder="admin" autoComplete="username" />
                </div>
                <div>
                  <label className="block text-xs font-semibold mb-1.5" style={{ color: "#374151" }}>Password</label>
                  <div className="relative">
                    <input type={showAdminPass ? "text" : "password"} value={adminPass} onChange={(e) => setAdminPass(e.target.value)}
                      className="w-full px-3.5 py-2.5 pr-10 rounded-lg text-sm outline-none"
                      style={{ border: "1.5px solid #e2e8f0", background: "#fff", color: "#0f172a" }}
                      onFocus={(e) => (e.target.style.borderColor = "#38fbdb")}
                      onBlur={(e) => (e.target.style.borderColor = "#e2e8f0")}
                      placeholder="••••••••" autoComplete="current-password" />
                    <button type="button" onClick={() => setShowAdminPass((v) => !v)}
                      className="absolute right-3 top-1/2 -translate-y-1/2" style={{ color: "#94a3b8" }}>
                      {showAdminPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <>
                <div>
                  <label className="block text-xs font-semibold mb-1.5" style={{ color: "#374151" }}>Client ID</label>
                  <input type="text" value={clientId} onChange={(e) => setClientId(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-lg text-sm outline-none"
                    style={{ border: "1.5px solid #e2e8f0", background: "#fff", color: "#0f172a" }}
                    onFocus={(e) => (e.target.style.borderColor = "#38fbdb")}
                    onBlur={(e) => (e.target.style.borderColor = "#e2e8f0")}
                    placeholder="C0" />
                </div>
                <div>
                  <label className="block text-xs font-semibold mb-1.5" style={{ color: "#374151" }}>Client Secret</label>
                  <div className="relative">
                    <input type={showClientSecret ? "text" : "password"} value={clientSecret} onChange={(e) => setClientSecret(e.target.value)}
                      className="w-full px-3.5 py-2.5 pr-10 rounded-lg text-sm outline-none"
                      style={{ border: "1.5px solid #e2e8f0", background: "#fff", color: "#0f172a" }}
                      onFocus={(e) => (e.target.style.borderColor = "#38fbdb")}
                      onBlur={(e) => (e.target.style.borderColor = "#e2e8f0")}
                      placeholder="••••••••••••••" />
                    <button type="button" onClick={() => setShowClientSecret((v) => !v)}
                      className="absolute right-3 top-1/2 -translate-y-1/2" style={{ color: "#94a3b8" }}>
                      {showClientSecret ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
              </>
            )}

            {error && (
              <div className="flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm"
                style={{ background: "#fef2f2", border: "1px solid #fecaca", color: "#dc2626" }}>
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}
            {successMsg && (
              <div className="flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm"
                style={{ background: "#f0fdf4", border: "1px solid #86efac", color: "#16a34a" }}>
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>{successMsg}</span>
              </div>
            )}

            <button type="submit" disabled={isLoading}
              className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-bold transition-all duration-200 mt-1 disabled:opacity-60"
              style={{
                background: "linear-gradient(135deg, #0d2040, #1a3a6e)",
                color: "#fff",
                boxShadow: "0 0 20px rgba(56,251,219,0.2)",
              }}>
              {isLoading ? (
                <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Authenticating...</>
              ) : (
                <><Key className="w-4 h-4" />Sign In</>
              )}
            </button>
          </form>

          <div className="flex items-center gap-3 my-5">
            <div className="flex-1 h-px" style={{ background: "#e2e8f0" }} />
            <span className="text-xs" style={{ color: "#94a3b8" }}>or</span>
            <div className="flex-1 h-px" style={{ background: "#e2e8f0" }} />
          </div>

          <button type="button" onClick={onGuest}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200"
            style={{ border: "1.5px solid #e2e8f0", background: "#fff", color: "#475569" }}
            onMouseEnter={(e) => {
              (e.currentTarget).style.borderColor = "#38fbdb";
              (e.currentTarget).style.color = "#0f172a";
            }}
            onMouseLeave={(e) => {
              (e.currentTarget).style.borderColor = "#e2e8f0";
              (e.currentTarget).style.color = "#475569";
            }}>
            <Lock className="w-4 h-4" />
            Continue as Guest
          </button>

          <p className="text-center text-xs mt-6" style={{ color: "#94a3b8" }}>
            Default demo credentials are pre-filled above.
          </p>
        </div>
      </div>
    </div>
  );
};
