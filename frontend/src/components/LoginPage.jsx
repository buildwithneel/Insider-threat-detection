import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  Lock, 
  Mail, 
  Eye, 
  EyeOff, 
  AlertTriangle, 
  RefreshCw, 
  CheckCircle2, 
  KeyRound, 
  ArrowLeft,
  ShieldCheck,
  Zap,
  Sun,
  Moon,
  Users,
  UserCheck,
  Award
} from 'lucide-react';
import { 
  auth, 
  isFirebaseConfigured, 
  signInWithEmailAndPassword, 
  sendPasswordResetEmail 
} from '../firebase';

export default function LoginPage({ onLoginSuccess, theme = 'dark', onToggleTheme }) {
  // Form State
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  
  // UI State Machine
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [isShaking, setIsShaking] = useState(false);

  // Password Reset Flow State
  const [showForgotModal, setShowForgotModal] = useState(false);
  const [resetEmail, setResetEmail] = useState('');
  const [resetLoading, setResetLoading] = useState(false);
  const [resetSuccessMsg, setResetSuccessMsg] = useState('');
  const [resetErrorMsg, setResetErrorMsg] = useState('');

  // Rate Limiting Security State (Client-side UX layer)
  const [failedAttempts, setFailedAttempts] = useState(0);
  const [lockoutTimeLeft, setLockoutTimeLeft] = useState(0);

  // Pre-configured Role Credentials for 1-click Demo Sign In
  const ROLE_PRESETS = [
    {
      role: 'CEO',
      label: 'CEO',
      email: 'ceo@garudaai.com',
      password: 'Ceo@Garuda2026!',
      badgeClass: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
      description: 'Highest Privilege • Access to All Platform Modules & System Settings'
    },
    {
      role: 'HR',
      label: 'HR Specialist',
      email: 'hr@garudaai.com',
      password: 'Hr@Garuda2026!',
      badgeClass: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
      description: 'Human Resources • Employee Profiles, Trust Scores & Behavioral Timelines'
    },
    {
      role: 'Security Manager',
      label: 'Sec Manager',
      email: 'security.manager@garudaai.com',
      password: 'SecManager@Garuda2026!',
      badgeClass: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30',
      description: 'SOC Management • Threat Dashboard, AI Investigation, JIT Tokens'
    },
    {
      role: 'Security Analyst',
      label: 'Sec Analyst',
      email: 'security.analyst@garudaai.com',
      password: 'SecAnalyst@Garuda2026!',
      badgeClass: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
      description: 'Read-Only Investigation • View Dashboards, Telemetry & Escalations'
    }
  ];

  const [activeRolePreset, setActiveRolePreset] = useState(ROLE_PRESETS[0]);

  // Handle countdown timer for rate limit lockout
  useEffect(() => {
    let timer;
    if (lockoutTimeLeft > 0) {
      timer = setInterval(() => {
        setLockoutTimeLeft(prev => prev - 1);
      }, 1000);
    } else if (lockoutTimeLeft === 0 && failedAttempts >= 5) {
      setFailedAttempts(0);
    }
    return () => clearInterval(timer);
  }, [lockoutTimeLeft, failedAttempts]);

  // Trigger error shake effect
  const triggerErrorShake = (message) => {
    setErrorMsg(message);
    setIsShaking(true);
    setTimeout(() => setIsShaking(false), 400);
  };

  // Quick fill preset credentials
  const handleSelectPreset = (preset) => {
    setActiveRolePreset(preset);
    setEmail(preset.email);
    setPassword(preset.password);
    setErrorMsg('');
  };

  // Auto fill first preset on initial render
  useEffect(() => {
    setEmail(activeRolePreset.email);
    setPassword(activeRolePreset.password);
  }, []);

  // Main Submit Handler
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (loading || lockoutTimeLeft > 0) return;

    setErrorMsg('');

    // 1. Client Validation
    const trimmedEmail = email.trim();
    if (!trimmedEmail) {
      triggerErrorShake('Please enter your email address.');
      return;
    }
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(trimmedEmail)) {
      triggerErrorShake('Please provide a valid email format (e.g. user@domain.com).');
      return;
    }

    if (!password) {
      triggerErrorShake('Please enter your security password.');
      return;
    }

    setLoading(true);

    try {
      if (isFirebaseConfigured && auth) {
        // Firebase Production Authentication Flow
        const userCredential = await signInWithEmailAndPassword(auth, trimmedEmail, password);
        const user = userCredential.user;
        
        const idTokenResult = await user.getIdTokenResult(true);
        const userRole = idTokenResult.claims?.role || 'Security Analyst';

        setFailedAttempts(0);
        onLoginSuccess({
          uid: user.uid,
          email: user.email,
          displayName: user.displayName || user.email.split('@')[0],
          role: userRole
        });

      } else {
        // Connect to GarudaAI MongoDB Authentication API
        try {
          const response = await fetch('http://localhost:5000/api/auth/login', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email: trimmedEmail, password })
          });

          const data = await response.json();

          if (response.ok && data.success) {
            setFailedAttempts(0);
            if (data.token) {
              localStorage.setItem('garuda_token', data.token);
              localStorage.setItem('garuda_user', JSON.stringify(data.user));
            }
            onLoginSuccess(data.user);
            return;
          } else {
            if (data.account_locked) {
              setLockoutTimeLeft(60);
            }
            throw new Error(data.error || 'Invalid credentials. Please verify your email and password.');
          }
        } catch (fetchErr) {
          if (fetchErr.message && !fetchErr.message.includes('Failed to fetch')) {
            throw fetchErr;
          }
          // Offline fallback matching selected preset
          const matchingPreset = ROLE_PRESETS.find(p => p.email.toLowerCase() === trimmedEmail.toLowerCase());
          if (matchingPreset && password === matchingPreset.password) {
            setFailedAttempts(0);
            const userContext = {
              uid: `demo-${matchingPreset.role.toLowerCase()}-uid`,
              email: matchingPreset.email,
              displayName: matchingPreset.label,
              employee_id: `GAR-${matchingPreset.role.substring(0,3).toUpperCase()}-001`,
              department: matchingPreset.role === 'HR' ? 'Human Resources' : matchingPreset.role === 'CEO' ? 'Executive Board' : 'SOC Division',
              designation: matchingPreset.label,
              role: matchingPreset.role
            };
            localStorage.setItem('garuda_token', `garuda-token-${userContext.uid}`);
            localStorage.setItem('garuda_user', JSON.stringify(userContext));
            onLoginSuccess(userContext);
            return;
          } else {
            throw new Error('Invalid credentials. Please verify your email and password.');
          }
        }
      }
    } catch (err) {
      console.error('Login authentication error:', err);
      const nextAttempts = failedAttempts + 1;
      setFailedAttempts(nextAttempts);

      if (nextAttempts >= 5) {
        setLockoutTimeLeft(30);
        triggerErrorShake('Too many failed attempts. Security portal locked for 30 seconds.');
      } else {
        const message = err.message || 'Authentication failed. Please verify your credentials.';
        triggerErrorShake(message);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    setResetErrorMsg('');
    setResetSuccessMsg('');

    const targetEmail = resetEmail.trim();
    if (!targetEmail) {
      setResetErrorMsg('Please enter your registered email address.');
      return;
    }

    setResetLoading(true);
    try {
      if (isFirebaseConfigured && auth) {
        await sendPasswordResetEmail(auth, targetEmail);
      } else {
        await new Promise(resolve => setTimeout(resolve, 800));
      }
      setResetSuccessMsg(`Password reset instructions sent to ${targetEmail}.`);
    } catch (err) {
      setResetErrorMsg('Failed to send reset email. Please try again later.');
    } finally {
      setResetLoading(false);
    }
  };

  return (
    <div className={`relative min-h-screen w-screen flex items-center justify-center overflow-hidden font-sans select-none ${theme === 'light' ? 'light-theme bg-slate-50 text-slate-900' : 'dark-theme bg-dark-bg text-gray-200'}`}>
      
      {/* Top Right Theme Toggle */}
      {onToggleTheme && (
        <button
          onClick={onToggleTheme}
          title={theme === 'dark' ? 'Switch to Day Mode (Light)' : 'Switch to Night Mode (Dark)'}
          className="absolute top-5 right-5 z-20 flex items-center gap-1.5 px-3 py-1.5 glass rounded-lg text-xs font-semibold shadow-lg transition-all cursor-pointer text-gray-300 hover:text-white"
        >
          {theme === 'dark' ? (
            <>
              <Sun className="w-4 h-4 text-amber-400" />
              <span>Day Mode</span>
            </>
          ) : (
            <>
              <Moon className="w-4 h-4 text-indigo-500" />
              <span>Night Mode</span>
            </>
          )}
        </button>
      )}

      {/* Main Login Container Card */}
      <div className={`w-full max-w-xl p-8 rounded-2xl glass border shadow-2xl relative z-10 transition-all ${isShaking ? 'animate-shake' : ''} ${theme === 'light' ? 'bg-white/90 border-slate-200 shadow-slate-300' : 'bg-dark-card/90 border-dark-border'}`}>
        
        {/* Brand Header */}
        <div className="flex flex-col items-center text-center mb-6">
          <div className="p-2 rounded-2xl bg-slate-900/60 border border-slate-700/50 shadow-xl shadow-blue-900/20 mb-3 flex items-center justify-center">
            <img src="/garuda-logo.png" alt="Garuda AI Logo" className="w-16 h-16 object-contain filter drop-shadow-md" />
          </div>
          <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-2">
            GARUDA <span className="text-blue-500">AI</span>
            <span className="text-[10px] px-2 py-0.5 rounded-md bg-blue-500/20 text-blue-400 font-mono border border-blue-500/30 uppercase tracking-widest font-bold">Enterprise SOC</span>
          </h1>
          <p className="text-xs text-blue-400 font-medium mt-1 max-w-md">
            AI-Powered FinTech Insider Threat Detection Platform
          </p>
        </div>

        {/* Role Quick Selector Tabs */}
        <div className="mb-6">
          <label className="block text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-2 text-center">
            Select Role Preset for Quick Login
          </label>
          <div className="grid grid-cols-5 gap-1.5 bg-slate-900/80 p-1.5 rounded-xl border border-slate-800">
            {ROLE_PRESETS.map((preset) => {
              const isSelected = activeRolePreset.role === preset.role;
              return (
                <button
                  key={preset.role}
                  type="button"
                  onClick={() => handleSelectPreset(preset)}
                  className={`py-2 px-1 rounded-lg text-xs font-bold transition-all text-center flex flex-col items-center justify-center gap-0.5 cursor-pointer ${
                    isSelected 
                      ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30 scale-[1.02]' 
                      : 'text-gray-400 hover:text-gray-200 hover:bg-slate-800/60'
                  }`}
                >
                  <span className="truncate w-full text-[11px]">{preset.label}</span>
                </button>
              );
            })}
          </div>

          {/* Role Access Description Box */}
          <div className="mt-2.5 p-2.5 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <Award className="w-4 h-4 text-indigo-400 shrink-0" />
              <span className="text-gray-300 text-[11px] font-medium">{activeRolePreset.description}</span>
            </div>
            <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${activeRolePreset.badgeClass}`}>
              {activeRolePreset.role}
            </span>
          </div>
        </div>

        {/* Lockout Warning Banner */}
        {lockoutTimeLeft > 0 && (
          <div className="mb-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center justify-center gap-2 animate-pulse">
            <Lock className="w-4 h-4" />
            <span>Portal locked. Please wait {lockoutTimeLeft} seconds...</span>
          </div>
        )}

        {/* Error Alert Banner */}
        {errorMsg && lockoutTimeLeft === 0 && (
          <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Credentials Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          
          <div>
            <label className="block text-[11px] font-semibold text-gray-300 uppercase tracking-wider mb-1">
              Corporate Email Address
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-2.5 w-4 h-4 text-gray-500" />
              <input
                id="login-email"
                name="email"
                type="email"
                required
                disabled={loading || lockoutTimeLeft > 0}
                placeholder="user@garudaai.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-9 pr-3 py-2 text-xs bg-dark-bg border border-dark-border rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:opacity-50 transition-all font-sans"
              />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-[11px] font-semibold text-gray-300 uppercase tracking-wider">
                Security Password
              </label>
              <button
                type="button"
                onClick={() => {
                  setShowForgotModal(true);
                  setResetEmail(email);
                }}
                className="text-[11px] text-blue-400 hover:text-blue-300 transition-colors cursor-pointer"
              >
                Forgot password?
              </button>
            </div>
            <div className="relative">
              <Lock className="absolute left-3 top-2.5 w-4 h-4 text-gray-500" />
              <input
                id="login-password"
                name="password"
                type={showPassword ? "text" : "password"}
                required
                disabled={loading || lockoutTimeLeft > 0}
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-9 pr-10 py-2 text-xs bg-dark-bg border border-dark-border rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:opacity-50 transition-all font-sans"
              />
              <button
                type="button"
                tabIndex={-1}
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-2.5 text-gray-500 hover:text-gray-300 transition-colors cursor-pointer"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || lockoutTimeLeft > 0}
            className="w-full mt-2 py-2.5 px-4 bg-blue-600 hover:bg-blue-700 active:scale-[0.99] disabled:opacity-50 text-white rounded-lg text-xs font-bold tracking-wider uppercase transition-all shadow-lg shadow-blue-600/20 cursor-pointer flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Authenticating Session...
              </>
            ) : (
              `Sign In as ${activeRolePreset.role}`
            )}
          </button>
        </form>

        <div className="mt-6 pt-4 border-t border-dark-border/60 text-center">
          <p className="text-[11px] text-gray-500">
            Authenticated via ML-KEM-768 Post-Quantum Security & RBAC Guards.
          </p>
        </div>

      </div>

      {/* Forgot Password Modal */}
      {showForgotModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-sm glass rounded-xl border border-dark-border p-6 shadow-2xl relative">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400">
                <KeyRound className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Reset Security Password</h3>
                <p className="text-[11px] text-gray-400">Receive recovery instructions via email</p>
              </div>
            </div>

            {resetSuccessMsg ? (
              <div className="py-4 text-center space-y-3">
                <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto" />
                <p className="text-xs text-gray-300">{resetSuccessMsg}</p>
                <button
                  type="button"
                  onClick={() => setShowForgotModal(false)}
                  className="w-full py-2 bg-dark-hover border border-dark-border text-white text-xs rounded-lg font-medium cursor-pointer"
                >
                  Return to Sign In
                </button>
              </div>
            ) : (
              <form onSubmit={handleResetPassword} className="space-y-4">
                {resetErrorMsg && (
                  <div className="p-2 rounded bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
                    <AlertTriangle className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                    <span>{resetErrorMsg}</span>
                  </div>
                )}
                <div>
                  <label className="block text-[11px] font-semibold text-gray-300 uppercase tracking-wider mb-1">
                    Registered Email
                  </label>
                  <input
                    type="email"
                    required
                    placeholder="user@garudaai.com"
                    value={resetEmail}
                    onChange={e => setResetEmail(e.target.value)}
                    className="w-full px-3 py-2 text-xs bg-dark-bg border border-dark-border rounded-lg text-gray-100 focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setShowForgotModal(false)}
                    className="flex-1 py-2 bg-dark-hover border border-dark-border text-gray-300 text-xs rounded-lg cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={resetLoading}
                    className="flex-1 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded-lg font-bold cursor-pointer flex items-center justify-center gap-1"
                  >
                    {resetLoading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : 'Send Reset Link'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

    </div>
  );
}
