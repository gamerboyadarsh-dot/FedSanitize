import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  Lock, 
  Key, 
  LogOut, 
  User, 
  CheckCircle2, 
  AlertCircle, 
  X,
  Server,
  Fingerprint
} from 'lucide-react';
import { 
  getAuth, 
  loginAdmin, 
  loginClient, 
  logout, 
  fetchMe,
  type StoredAuth 
} from '../../api/auth';

interface AuthBadgeModalProps {
  onAuthChange?: () => void;
}

export const AuthBadgeModal: React.FC<AuthBadgeModalProps> = ({ onAuthChange }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [auth, setAuth] = useState<StoredAuth | null>(null);
  const [me, setMe] = useState<{ subject: string; role: string; client_id?: string; auth_type: string } | null>(null);
  const [activeTab, setActiveTab] = useState<'admin' | 'client'>('admin');
  const [adminUser, setAdminUser] = useState('admin');
  const [adminPass, setAdminPass] = useState('admin123');
  const [clientId, setClientId] = useState('C0');
  const [clientSecret, setClientSecret] = useState('clientsecret123');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const refreshState = async () => {
    const current = getAuth();
    setAuth(current);
    if (current) {
      const meData = await fetchMe();
      setMe(meData);
    } else {
      setMe(null);
    }
  };

  useEffect(() => {
    refreshState();
  }, []);

  const handleAdminLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setIsLoading(true);
    setError(null);
    setSuccessMsg(null);
    try {
      await loginAdmin(adminUser, adminPass);
      await refreshState();
      setSuccessMsg('Authenticated as Admin (' + adminUser + ')');
      if (onAuthChange) onAuthChange();
      setTimeout(() => {
        setSuccessMsg(null);
        setIsOpen(false);
      }, 1000);
    } catch (err: any) {
      setError(err.message || 'Admin login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClientLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setIsLoading(true);
    setError(null);
    setSuccessMsg(null);
    try {
      await loginClient(clientId, clientSecret);
      await refreshState();
      setSuccessMsg('Authenticated as Edge Client ' + clientId);
      if (onAuthChange) onAuthChange();
      setTimeout(() => {
        setSuccessMsg(null);
        setIsOpen(false);
      }, 1000);
    } catch (err: any) {
      setError(err.message || 'Client login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    refreshState();
    if (onAuthChange) onAuthChange();
  };

  return (
    <>
      <button
        type='button'
        onClick={() => {
          setError(null);
          setSuccessMsg(null);
          setIsOpen(true);
        }}
        className={'h-9 px-3.5 rounded-lg border font-mono text-xs flex items-center gap-2 transition-all duration-200 select-none shadow-sm ' + (
          auth
            ? auth.role === 'admin'
              ? 'border-accent-safe/60 text-accent-safe bg-accent-safe/10 hover:bg-accent-safe/20'
              : 'border-primary/60 text-primary bg-primary/10 hover:bg-primary/20'
            : 'border-border text-text-secondary hover:text-text-primary hover:border-text-secondary/40'
        )}
        title='Zero-Trust Authentication Gateway'
      >
        {auth ? (
          <>
            <span className='w-2 h-2 rounded-full bg-accent-safe animate-pulse' />
            <ShieldCheck className='w-3.5 h-3.5' />
            <span className='font-bold uppercase tracking-wider'>
              {auth.role === 'admin' ? 'ADMIN' : ('CLIENT: ' + (auth.clientId || 'EDGE'))}
            </span>
          </>
        ) : (
          <>
            <Lock className='w-3.5 h-3.5 text-accent-warning' />
            <span className='font-medium'>AUTH: GUEST</span>
          </>
        )}
      </button>

      {isOpen && (
        <div className='fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-md'>
          <div className='bg-surface border border-border rounded-xl shadow-2xl max-w-lg w-full p-6 relative flex flex-col gap-5 text-text-primary threat-card'>
            <div className='flex items-center justify-between border-b border-border pb-4'>
              <div className='flex items-center gap-3'>
                <div className='w-10 h-10 rounded-lg bg-surface-elevated border border-border flex items-center justify-center text-primary'>
                  <Fingerprint className='w-5 h-5' />
                </div>
                <div>
                  <h3 className='font-mono text-sm font-bold text-text-primary uppercase tracking-wider'>
                    Zero-Trust Access Gateway
                  </h3>
                  <p className='font-mono text-xs text-text-secondary'>
                    JWT Auth and Role-Based Access Control
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className='p-1.5 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-colors'
              >
                <X className='w-4 h-4' />
              </button>
            </div>

            {auth ? (
              <div className='bg-surface-elevated/70 border border-border/80 rounded-lg p-4 font-mono flex flex-col gap-3'>
                <div className='flex items-center justify-between'>
                  <div className='flex items-center gap-2'>
                    <span className='w-2.5 h-2.5 rounded-full bg-accent-safe animate-pulse' />
                    <span className='text-xs font-bold text-accent-safe uppercase tracking-wider'>
                      Active JWT Session
                    </span>
                  </div>
                  <span className='text-[10px] px-2 py-0.5 rounded bg-surface border border-border text-text-secondary uppercase'>
                    Role: {auth.role}
                  </span>
                </div>

                <div className='grid grid-cols-2 gap-2 text-xs pt-1 border-t border-border/40'>
                  <div>
                    <span className='text-text-secondary block text-[10px] uppercase'>Subject</span>
                    <span className='font-semibold text-text-primary'>
                      {me?.subject || (auth.role === 'admin' ? 'admin' : (auth.clientId || 'client'))}
                    </span>
                  </div>
                  <div>
                    <span className='text-text-secondary block text-[10px] uppercase'>Client ID</span>
                    <span className='font-semibold text-text-primary'>
                      {auth.clientId || 'Central Server'}
                    </span>
                  </div>
                  <div className='col-span-2'>
                    <span className='text-text-secondary block text-[10px] uppercase'>Token Preview</span>
                    <span className='text-[10px] text-primary/80 truncate block font-mono bg-background/50 px-2 py-1 rounded mt-0.5'>
                      {auth.accessToken.slice(0, 32)}...
                    </span>
                  </div>
                </div>

                <div className='pt-2 border-t border-border/40 flex items-center justify-between gap-3'>
                  <span className='text-[11px] text-text-secondary'>
                    {auth.role === 'admin' 
                      ? 'Permissions: Full telemetry, quarantine override, orchestrator tuning' 
                      : 'Permissions: Edge model weights submission, local trust telemetry'}
                  </span>
                  <button
                    onClick={handleLogout}
                    className='threat-btn-secondary h-8 px-3 rounded flex items-center gap-1.5 text-accent-danger border-accent-danger/30 hover:bg-accent-danger/10 text-xs shrink-0'
                  >
                    <LogOut className='w-3.5 h-3.5' />
                    Logout
                  </button>
                </div>
              </div>
            ) : (
              <div className='bg-accent-warning/10 border border-accent-warning/30 rounded-lg p-3 text-xs font-mono text-accent-warning flex items-center gap-2.5'>
                <AlertCircle className='w-4 h-4 shrink-0' />
                <span>Operating as unauthenticated guest. Sign in to issue administrative overrides or edge client gradients.</span>
              </div>
            )}

            {error && (
              <div className='bg-accent-danger/10 border border-accent-danger/30 p-2.5 rounded text-xs font-mono text-accent-danger flex items-center gap-2'>
                <AlertCircle className='w-4 h-4 shrink-0' />
                <span>{error}</span>
              </div>
            )}
            {successMsg && (
              <div className='bg-accent-safe/10 border border-accent-safe/30 p-2.5 rounded text-xs font-mono text-accent-safe flex items-center gap-2'>
                <CheckCircle2 className='w-4 h-4 shrink-0' />
                <span>{successMsg}</span>
              </div>
            )}

            <div className='flex border-b border-border font-mono text-xs'>
              <button
                type='button'
                onClick={() => { setActiveTab('admin'); setError(null); }}
                className={'flex-1 pb-2 font-bold transition-colors border-b-2 flex items-center justify-center gap-1.5 ' + (
                  activeTab === 'admin'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-text-secondary hover:text-text-primary'
                )}
              >
                <User className='w-3.5 h-3.5' />
                Admin Credentials
              </button>
              <button
                type='button'
                onClick={() => { setActiveTab('client'); setError(null); }}
                className={'flex-1 pb-2 font-bold transition-colors border-b-2 flex items-center justify-center gap-1.5 ' + (
                  activeTab === 'client'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-text-secondary hover:text-text-primary'
                )}
              >
                <Server className='w-3.5 h-3.5' />
                Edge Client Credentials
              </button>
            </div>

            {activeTab === 'admin' && (
              <form onSubmit={handleAdminLogin} className='flex flex-col gap-3 font-mono text-xs'>
                <div>
                  <label className='block text-[11px] text-text-secondary mb-1 uppercase'>Username</label>
                  <input
                    type='text'
                    value={adminUser}
                    onChange={(e) => setAdminUser(e.target.value)}
                    className='w-full bg-surface-elevated border border-border rounded px-3 py-2 text-text-primary focus:outline-none focus:border-primary'
                    placeholder='admin'
                  />
                </div>
                <div>
                  <label className='block text-[11px] text-text-secondary mb-1 uppercase'>Password</label>
                  <input
                    type='password'
                    value={adminPass}
                    onChange={(e) => setAdminPass(e.target.value)}
                    className='w-full bg-surface-elevated border border-border rounded px-3 py-2 text-text-primary focus:outline-none focus:border-primary'
                    placeholder='password'
                  />
                </div>

                <div className='flex items-center gap-2 pt-2'>
                  <button
                    type='submit'
                    disabled={isLoading}
                    className='threat-btn-primary flex-1 h-9 rounded font-bold flex items-center justify-center gap-2 disabled:opacity-50'
                  >
                    <Key className='w-3.5 h-3.5' />
                    {isLoading ? 'Authenticating...' : 'Sign In as Admin'}
                  </button>
                  <button
                    type='button'
                    onClick={() => {
                      setAdminUser('admin');
                      setAdminPass('admin123');
                      handleAdminLogin();
                    }}
                    className='threat-btn-secondary h-9 px-3 rounded font-medium text-text-secondary hover:text-primary whitespace-nowrap'
                  >
                    Quick Demo Admin
                  </button>
                </div>
              </form>
            )}

            {activeTab === 'client' && (
              <form onSubmit={handleClientLogin} className='flex flex-col gap-3 font-mono text-xs'>
                <div>
                  <label className='block text-[11px] text-text-secondary mb-1 uppercase'>Client ID</label>
                  <input
                    type='text'
                    value={clientId}
                    onChange={(e) => setClientId(e.target.value)}
                    className='w-full bg-surface-elevated border border-border rounded px-3 py-2 text-text-primary focus:outline-none focus:border-primary'
                    placeholder='C0'
                  />
                </div>
                <div>
                  <label className='block text-[11px] text-text-secondary mb-1 uppercase'>Client Shared Secret</label>
                  <input
                    type='password'
                    value={clientSecret}
                    onChange={(e) => setClientSecret(e.target.value)}
                    className='w-full bg-surface-elevated border border-border rounded px-3 py-2 text-text-primary focus:outline-none focus:border-primary'
                    placeholder='secret'
                  />
                </div>

                <div className='flex items-center gap-2 pt-2'>
                  <button
                    type='submit'
                    disabled={isLoading}
                    className='threat-btn-primary flex-1 h-9 rounded font-bold flex items-center justify-center gap-2 disabled:opacity-50'
                  >
                    <Key className='w-3.5 h-3.5' />
                    {isLoading ? 'Authenticating...' : 'Sign In as Client'}
                  </button>
                  <button
                    type='button'
                    onClick={() => {
                      setClientId('C0');
                      setClientSecret('clientsecret123');
                      handleClientLogin();
                    }}
                    className='threat-btn-secondary h-9 px-3 rounded font-medium text-text-secondary hover:text-primary whitespace-nowrap'
                  >
                    Quick Demo Client (C0)
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </>
  );
};
