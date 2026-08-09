import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, ShieldCheck, Clock, AlertTriangle, Lock, Key, Sliders, 
  CheckCircle2, Activity, User, Copy, Check, AlertCircle, Terminal, RefreshCw,
  Search, Filter, PlusCircle, Eye, XCircle, ChevronRight, BarChart3, Database,
  Settings, Layers, Users, FileText, Cpu, AlertOctagon, History, Shield, Zap
} from 'lucide-react';

const ALL_PERMISSIONS = [
  "Dashboard",
  "Employee List",
  "Investigations",
  "AI Investigation",
  "Reports",
  "Analytics",
  "Activity Timeline",
  "Trust Score",
  "Alerts",
  "User Management",
  "Settings",
  "Export Data",
  "Audit Logs",
  "Model Management",
  "Dataset Upload",
  "System Configuration"
];

const PRESET_DURATIONS = [
  "15 Minutes",
  "30 Minutes",
  "1 Hour",
  "2 Hours",
  "4 Hours",
  "8 Hours",
  "12 Hours",
  "24 Hours",
  "Custom Duration"
];

const API_BASE = 'http://localhost:5000/api';

const fetchJitApi = async (endpoint, options = {}) => {
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : '/' + endpoint;
  const primaryUrl = `${API_BASE}${cleanEndpoint}`;
  const relativeUrl = `/api${cleanEndpoint}`;

  const token = localStorage.getItem('garuda_token') || localStorage.getItem('token') || 'garuda-admin-demo-token';
  const customHeaders = options.headers || {};
  const reqOptions = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      'X-Access-Token': token,
      ...customHeaders
    }
  };

  let res;
  let networkErr;

  try {
    res = await fetch(primaryUrl, reqOptions);
  } catch (e1) {
    try {
      res = await fetch(relativeUrl, reqOptions);
    } catch (e2) {
      networkErr = e1.message || e2.message || 'Connection refused';
      throw new Error(`[Network Connection Error] Unable to connect to backend server at ${primaryUrl} or ${relativeUrl} (${networkErr}). Please verify Flask server (app.py) is running on port 5000.`);
    }
  }

  if (!res.ok) {
    let message = '';
    try {
      const rawText = await res.text();
      try {
        const errJson = JSON.parse(rawText);
        message = errJson.error || errJson.message || JSON.stringify(errJson);
      } catch (parseErr) {
        message = rawText;
      }
    } catch (readErr) {
      message = res.statusText;
    }
    throw new Error(`[HTTP ${res.status} ${res.statusText}] ${message || 'Server Error'}`);
  }

  return await res.json();
};

export default function JitPamDashboard({ 
  selectedEmp, 
  criticalThreshold = 30, 
  setCriticalThreshold,
  employeeLocks = {},
  onGenerateToken,
  onVerifyToken,
  timeline = []
}) {
  // Navigation sub-tabs inside JIT Command Center
  const [activeSubTab, setActiveSubTab] = useState('overview'); // 'overview', 'issue', 'tokens', 'audit_logs'

  // Threshold config
  const [tempThreshold, setTempThreshold] = useState(criticalThreshold);
  const [savedMsg, setSavedMsg] = useState('');

  // Token unlock verification state
  const [tokenInput, setTokenInput] = useState('');
  const [verifyErr, setVerifyErr] = useState('');
  const [verifySuccess, setVerifySuccess] = useState(false);
  const [copiedToken, setCopiedToken] = useState('');

  // Issue JIT Token Form State
  const [issueAccessType, setIssueAccessType] = useState('Full Access'); // 'Full Access' | 'Limited Access'
  const [selectedPermissions, setSelectedPermissions] = useState([...ALL_PERMISSIONS]);
  const [selectedDurationPreset, setSelectedDurationPreset] = useState('1 Hour');
  const [customDays, setCustomDays] = useState(0);
  const [customHours, setCustomHours] = useState(1);
  const [customMinutes, setCustomMinutes] = useState(0);
  const [customSeconds, setCustomSeconds] = useState(0);
  const [issuing, setIssuing] = useState(false);
  const [issueError, setIssueError] = useState('');
  const [newlyIssuedToken, setNewlyIssuedToken] = useState(null);

  // DB persistent tokens list & audit logs state
  const [dbTokens, setDbTokens] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [stats, setStats] = useState({
    total_tokens: 0,
    active_tokens: 0,
    expired_tokens: 0,
    revoked_tokens: 0,
    average_session_duration_minutes: 0,
    recently_issued: [],
    recently_used: [],
    permission_distribution: {}
  });
  const [loadingDb, setLoadingDb] = useState(false);

  // Search and Filter controls
  const [statusFilter, setStatusFilter] = useState('All');
  const [tokenSearchQuery, setTokenSearchQuery] = useState('');
  const [auditEventFilter, setAuditEventFilter] = useState('All');
  const [auditSearchQuery, setAuditSearchQuery] = useState('');

  // Action Modals State
  const [selectedTokenDetails, setSelectedTokenDetails] = useState(null);
  const [extendModalToken, setExtendModalToken] = useState(null);
  const [extendMinutes, setExtendMinutes] = useState(30);
  const [revokeModalToken, setRevokeModalToken] = useState(null);
  const [revokeReason, setRevokeReason] = useState('Admin Manual Revocation');
  const [actionLoading, setActionLoading] = useState(false);
  const [actionMsg, setActionMsg] = useState('');

  const currentLock = selectedEmp ? (employeeLocks[selectedEmp.employee_id] || { status: 'NORMAL', countdown: 30, lockTime: null, token: null }) : { status: 'NORMAL', countdown: 30, lockTime: null, token: null };
  const lockStatus = currentLock.status;
  const countdown = currentLock.countdown;

  // Fetch MongoDB Persistent JIT Tokens & Audit Logs
  const fetchJitData = async () => {
    setLoadingDb(true);
    try {
      const empParam = selectedEmp?.employee_id ? `?employee_id=${encodeURIComponent(selectedEmp.employee_id)}` : '';
      const [tokData, logData, statData] = await Promise.all([
        fetchJitApi(`/jit/tokens${empParam}`),
        fetchJitApi(`/jit/audit-logs${empParam}`),
        fetchJitApi(`/jit/dashboard/stats${empParam}`)
      ]);

      if (tokData.success) setDbTokens(tokData.tokens || []);
      if (logData.success) setAuditLogs(logData.audit_logs || []);
      if (statData.success) setStats(statData.stats || {});
    } catch (e) {
      console.error("Error fetching JIT persistent data:", e);
    } finally {
      setLoadingDb(false);
    }
  };

  useEffect(() => {
    fetchJitData();
    const interval = setInterval(fetchJitData, 15000);
    return () => clearInterval(interval);
  }, [selectedEmp?.employee_id]);

  // Update selected permissions when Access Type toggles
  useEffect(() => {
    if (issueAccessType === 'Full Access') {
      setSelectedPermissions([...ALL_PERMISSIONS]);
    }
  }, [issueAccessType]);

  const handleSaveThreshold = (e) => {
    e.preventDefault();
    const val = Number(tempThreshold);
    if (!isNaN(val) && val >= 10 && val <= 80) {
      setCriticalThreshold(val);
      setSavedMsg(`Threshold set to ${val}`);
      setTimeout(() => setSavedMsg(''), 2500);
    }
  };

  const handleCopyText = (text) => {
    navigator.clipboard.writeText(text);
    setCopiedToken(text);
    setTimeout(() => setCopiedToken(''), 2000);
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    setVerifyErr('');
    setVerifySuccess(false);

    if (!tokenInput.trim()) {
      setVerifyErr('Token string cannot be empty');
      return;
    }

    try {
      const data = await fetchJitApi('/jit/tokens/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token: tokenInput.trim(),
          employee_id: selectedEmp?.employee_id
        })
      });

      if (data.success) {
        setVerifySuccess(true);
        setTokenInput('');
        if (onVerifyToken && selectedEmp) {
          onVerifyToken(selectedEmp.employee_id, tokenInput.trim());
        }
        fetchJitData();
      } else {
        setVerifyErr(data.error || 'Token Verification Failed');
      }
    } catch (err) {
      setVerifyErr(err.message || 'Failed to connect to verification server');
    }
  };

  const togglePermission = (perm) => {
    if (selectedPermissions.includes(perm)) {
      setSelectedPermissions(selectedPermissions.filter(p => p !== perm));
    } else {
      setSelectedPermissions([...selectedPermissions, perm]);
    }
  };

  const handleIssueTokenSubmit = async (e) => {
    e.preventDefault();
    if (!selectedEmp) {
      setIssueError("Please select an employee from the workspace first.");
      return;
    }

    if (issueAccessType === 'Limited Access' && selectedPermissions.length === 0) {
      setIssueError("Please select at least one permission scope for Limited Access.");
      return;
    }

    // Frontend validation: ensure mutual exclusivity
    if (issueAccessType !== 'Limited Access' && issueAccessType !== 'Full Access') {
      setIssueError("Invalid permission configuration: An employee cannot have Limited and Full Access simultaneously.");
      return;
    }

    setIssuing(true);
    setIssueError('');

    try {
      const payload = {
        employee_id: selectedEmp.employee_id,
        employee_name: selectedEmp.full_name,
        department: selectedEmp.functional_unit || selectedEmp.department || 'SOC Division',
        admin_id: 'GAR-0001',
        admin_name: 'Lead Security Administrator',
        access_type: issueAccessType,
        accessLevel: issueAccessType === 'Full Access' ? 'FULL' : 'LIMITED',
        granted_permissions: issueAccessType === 'Full Access' ? ALL_PERMISSIONS : selectedPermissions,
        preset_duration: selectedDurationPreset,
        custom_duration: selectedDurationPreset === 'Custom Duration' ? {
          days: Number(customDays),
          hours: Number(customHours),
          minutes: Number(customMinutes),
          seconds: Number(customSeconds)
        } : null
      };

      console.log("[DEBUG_JIT_FRONTEND] Issuing Token Payload ->", payload);

      const data = await fetchJitApi('/jit/tokens/issue', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      console.log("[DEBUG_JIT_FRONTEND] Token Issue Response ->", data);

      if (data.success) {
        setNewlyIssuedToken({
          ...data.token,
          secure_token: data.secure_token
        });
        if (onGenerateToken) {
          onGenerateToken(selectedEmp.employee_id, {
            ...data.token,
            secure_token: data.secure_token
          });
        }
        fetchJitData();
      } else {
        setIssueError(data.error || 'Failed to issue token');
      }
    } catch (err) {
      setIssueError(err.message || 'Error while issuing JIT token');
    } finally {
      setIssuing(false);
    }
  };

  const handleRevokeConfirm = async () => {
    if (!revokeModalToken) return;
    setActionLoading(true);
    try {
      const data = await fetchJitApi(`/jit/tokens/${revokeModalToken.token_id}/revoke`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          admin_id: 'GAR-0001',
          admin_name: 'Lead Security Administrator',
          reason: revokeReason
        })
      });
      if (data.success) {
        setRevokeModalToken(null);
        fetchJitData();
      } else {
        setActionMsg(data.error || 'Revocation failed');
      }
    } catch (e) {
      setActionMsg(e.message || 'Error calling revocation API');
    } finally {
      setActionLoading(false);
    }
  };

  const handleExtendConfirm = async () => {
    if (!extendModalToken) return;
    setActionLoading(true);
    try {
      const data = await fetchJitApi(`/jit/tokens/${extendModalToken.token_id}/extend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          additional_minutes: Number(extendMinutes),
          admin_id: 'GAR-0001',
          admin_name: 'Lead Security Administrator'
        })
      });
      if (data.success) {
        setExtendModalToken(null);
        fetchJitData();
      } else {
        setActionMsg(data.error || 'Extension failed');
      }
    } catch (e) {
      setActionMsg('Error extending expiry');
    } finally {
      setActionLoading(false);
    }
  };

  const getDurationDisplay = (t) => {
    if (t.duration != null) return `${t.duration} Minutes`;
    if (t.duration_minutes != null) return `${t.duration_minutes} Minutes`;
    if (t.expires_at && t.issued_at) {
      const mins = Math.round((new Date(t.expires_at) - new Date(t.issued_at)) / 60000);
      return `${mins} Minutes`;
    }
    return 'N/A';
  };

  const getRemainingTimeDisplay = (t) => {
    if (t.status !== 'Active' || !t.expires_at) return '0m';
    const now = new Date();
    const exp = new Date(t.expires_at);
    const diffMs = exp - now;
    if (diffMs <= 0) return '0m';
    const mins = Math.floor(diffMs / 60000);
    const secs = Math.floor((diffMs % 60000) / 1000);
    if (mins >= 60) {
      const hrs = Math.floor(mins / 60);
      const remMins = mins % 60;
      return `${hrs}h ${remMins}m`;
    }
    return `${mins}m ${secs}s`;
  };

  // Filtered lists for Admin Table & Audit Logs
  const filteredTokens = dbTokens.filter(t => {
    const matchesStatus = statusFilter === 'All' || t.status === statusFilter;
    const matchesSearch = !tokenSearchQuery || (
      (t.token_id && t.token_id.toLowerCase().includes(tokenSearchQuery.toLowerCase())) ||
      (t.employee_id && t.employee_id.toLowerCase().includes(tokenSearchQuery.toLowerCase())) ||
      (t.employee_name && t.employee_name.toLowerCase().includes(tokenSearchQuery.toLowerCase())) ||
      (t.admin_name && t.admin_name.toLowerCase().includes(tokenSearchQuery.toLowerCase()))
    );
    return matchesStatus && matchesSearch;
  });

  const filteredLogs = auditLogs.filter(l => {
    const matchesEvent = auditEventFilter === 'All' || l.event_type === auditEventFilter;
    const empName = l.employee?.name || '';
    const empId = l.employee?.id || '';
    const adminName = l.admin?.name || '';
    const notes = l.notes || '';
    const matchesSearch = !auditSearchQuery || (
      l.token_id?.toLowerCase().includes(auditSearchQuery.toLowerCase()) ||
      empName.toLowerCase().includes(auditSearchQuery.toLowerCase()) ||
      empId.toLowerCase().includes(auditSearchQuery.toLowerCase()) ||
      adminName.toLowerCase().includes(auditSearchQuery.toLowerCase()) ||
      notes.toLowerCase().includes(auditSearchQuery.toLowerCase())
    );
    return matchesEvent && matchesSearch;
  });

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-[#090D16] text-gray-200 font-sans">
      
      {/* Header Card */}
      <div className="glass p-6 rounded-xl border border-dark-border flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-dark-card/40 backdrop-blur-md">
        <div className="flex items-center gap-4">
          <div className={`p-3.5 rounded-xl border ${
            lockStatus === 'LOCKED' 
              ? 'bg-rose-500/10 border-rose-500/30 text-rose-400' 
              : lockStatus === 'WARNING' 
                ? 'bg-amber-500/10 border-amber-500/30 text-amber-400 animate-pulse'
                : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
          }`}>
            {lockStatus === 'LOCKED' ? (
              <Lock className="w-8 h-8" />
            ) : lockStatus === 'WARNING' ? (
              <ShieldAlert className="w-8 h-8 animate-bounce" />
            ) : (
              <ShieldCheck className="w-8 h-8" />
            )}
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-3">
              JIT Enterprise Security Command
              <span className="text-xs bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2 py-0.5 rounded font-mono font-semibold">
                MongoDB Persistent Edition
              </span>
            </h1>
            <p className="text-xs text-gray-400 mt-1">
              Zero-Trust Just-In-Time access governance. Configurable scope permissions, expiration timers, cryptographically hashed tokens, and permanent audit logs.
            </p>
          </div>
        </div>

        {/* Global lock badge & Refresh */}
        <div className="flex items-center gap-3">
          <button 
            onClick={fetchJitData} 
            title="Refresh JIT Data"
            className="p-2 bg-dark-hover hover:bg-gray-800 text-gray-400 hover:text-white rounded-lg border border-dark-border transition-all"
          >
            <RefreshCw className={`w-4 h-4 ${loadingDb ? 'animate-spin text-blue-400' : ''}`} />
          </button>
          {lockStatus === 'WARNING' && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold bg-amber-500/20 text-amber-400 border border-amber-500/40 rounded-full animate-pulse">
              <AlertTriangle className="w-3.5 h-3.5" />
              MITIGATION WARNING ({countdown}s)
            </span>
          )}
          {lockStatus === 'LOCKED' && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold bg-rose-500/20 text-rose-400 border border-rose-500/40 rounded-full animate-pulse">
              <Lock className="w-3.5 h-3.5" />
              WORKSTATION SECURED
            </span>
          )}
          {lockStatus === 'UNLOCKED' && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 rounded-full">
              <CheckCircle2 className="w-3.5 h-3.5" />
              JIT ACCESS ACTIVE
            </span>
          )}
          {lockStatus === 'NORMAL' && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold bg-blue-500/20 text-blue-400 border border-blue-500/40 rounded-full">
              <ShieldCheck className="w-3.5 h-3.5" />
              MONITORING ACTIVE
            </span>
          )}
        </div>
      </div>

      {/* Sub-Navigation Tabs */}
      <div className="flex border-b border-dark-border/80 gap-2">
        <button
          onClick={() => setActiveSubTab('overview')}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold transition-all border-b-2 cursor-pointer ${
            activeSubTab === 'overview'
              ? 'border-blue-500 text-blue-400 bg-blue-500/10'
              : 'border-transparent text-gray-400 hover:text-gray-200 hover:bg-dark-hover'
          }`}
        >
          <Activity className="w-4 h-4" />
          Overview & Unlock
        </button>
        <button
          onClick={() => setActiveSubTab('issue')}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold transition-all border-b-2 cursor-pointer ${
            activeSubTab === 'issue'
              ? 'border-blue-500 text-blue-400 bg-blue-500/10'
              : 'border-transparent text-gray-400 hover:text-gray-200 hover:bg-dark-hover'
          }`}
        >
          <PlusCircle className="w-4 h-4" />
          Issue JIT Token
        </button>
        <button
          onClick={() => {
            setActiveSubTab('tokens');
            setStatusFilter('Active');
          }}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold transition-all border-b-2 cursor-pointer ${
            activeSubTab === 'tokens'
              ? 'border-blue-500 text-blue-400 bg-blue-500/10'
              : 'border-transparent text-gray-400 hover:text-gray-200 hover:bg-dark-hover'
          }`}
        >
          <Key className="w-4 h-4" />
          Active Tokens ({stats.active_tokens || 0})
        </button>
        <button
          onClick={() => setActiveSubTab('audit_logs')}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold transition-all border-b-2 cursor-pointer ${
            activeSubTab === 'audit_logs'
              ? 'border-blue-500 text-blue-400 bg-blue-500/10'
              : 'border-transparent text-gray-400 hover:text-gray-200 hover:bg-dark-hover'
          }`}
        >
          <History className="w-4 h-4" />
          Permanent Audit Trail ({auditLogs.length})
        </button>
      </div>

      {/* METRICS METRIC CARDS */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="glass p-4 rounded-xl border border-dark-border bg-dark-card/30">
          <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
            <span>Total Tokens</span>
            <Database className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-white">{stats.total_tokens || 0}</div>
          <span className="text-[10px] text-gray-500">MongoDB Hashed Tokens</span>
        </div>

        <div className="glass p-4 rounded-xl border border-dark-border bg-dark-card/30">
          <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
            <span>Active Tokens</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400">{stats.active_tokens || 0}</div>
          <span className="text-[10px] text-emerald-500/80">Valid JIT Sessions</span>
        </div>

        <div className="glass p-4 rounded-xl border border-dark-border bg-dark-card/30">
          <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
            <span>Expired Tokens</span>
            <Clock className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-400">{stats.expired_tokens || 0}</div>
          <span className="text-[10px] text-amber-500/80">Timer Elapsed</span>
        </div>

        <div className="glass p-4 rounded-xl border border-dark-border bg-dark-card/30">
          <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
            <span>Revoked Tokens</span>
            <XCircle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold text-rose-400">{stats.revoked_tokens || 0}</div>
          <span className="text-[10px] text-rose-500/80">Admin Revocations</span>
        </div>

        <div className="glass p-4 rounded-xl border border-dark-border bg-dark-card/30">
          <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
            <span>Avg Duration</span>
            <Zap className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-purple-400">{stats.average_session_duration_minutes || 0}m</div>
          <span className="text-[10px] text-purple-500/80">Per JIT Grant</span>
        </div>

        <div className="glass p-4 rounded-xl border border-dark-border bg-dark-card/30">
          <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
            <span>Avg Remaining</span>
            <Clock className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-cyan-400">{stats.average_remaining_time_minutes || 0}m</div>
          <span className="text-[10px] text-cyan-500/80">Active Sessions</span>
        </div>
      </div>

      {/* OVERVIEW SUBTAB */}
      {activeSubTab === 'overview' && (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          
          {/* Left Panel: Threshold & Selected Employee */}
          <div className="xl:col-span-1 space-y-6">
            
            {/* Threshold Settings */}
            <div className="glass p-5 rounded-xl border border-dark-border bg-dark-card/30">
              <div className="flex items-center gap-2 text-xs font-bold text-white uppercase tracking-wider mb-3">
                <Sliders className="w-4 h-4 text-blue-400" />
                <span>Critical Risk Threshold</span>
              </div>
              <form onSubmit={handleSaveThreshold} className="space-y-3">
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Trigger Threshold Score ({tempThreshold})</label>
                  <input
                    type="range"
                    min="10"
                    max="80"
                    value={tempThreshold}
                    onChange={(e) => setTempThreshold(e.target.value)}
                    className="w-full h-2 bg-dark-hover rounded-lg appearance-none cursor-pointer accent-blue-500"
                  />
                  <div className="flex justify-between text-[10px] text-gray-500 mt-1">
                    <span>10 (Strict)</span>
                    <span>30 (Default)</span>
                    <span>80 (Relaxed)</span>
                  </div>
                </div>
                <button
                  type="submit"
                  className="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-bold transition-all cursor-pointer"
                >
                  Save Threshold
                </button>
                {savedMsg && (
                  <p className="text-xs text-emerald-400 text-center animate-fade-in">{savedMsg}</p>
                )}
              </form>
            </div>

            {/* Selected Employee Card */}
            <div className="glass p-5 rounded-xl border border-dark-border bg-dark-card/30 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Target Workstation</span>
                {selectedEmp?.is_privileged_user && (
                  <span className="text-[10px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30 px-2 py-0.5 rounded-full">
                    Privileged
                  </span>
                )}
              </div>

              {selectedEmp ? (
                <div className="flex items-center gap-3 p-3 bg-dark-hover/50 rounded-lg border border-dark-border/50">
                  <div className="w-10 h-10 bg-blue-500/20 border border-blue-500/40 rounded-lg flex items-center justify-center font-bold text-blue-400 font-mono">
                    {selectedEmp.employee_id.slice(-3)}
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white">{selectedEmp.full_name}</h3>
                    <p className="text-xs text-gray-400">{selectedEmp.employee_id} &middot; {selectedEmp.department || selectedEmp.functional_unit || 'SOC'}</p>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-amber-400/80 bg-amber-500/10 p-3 rounded-lg border border-amber-500/20">
                  No employee currently selected. Select an employee from the workspace header or navigation list.
                </p>
              )}
            </div>

            {/* Quick Actions Card */}
            <div className="glass p-5 rounded-xl border border-dark-border bg-dark-card/30 space-y-3">
              <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Quick Actions</span>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => setActiveSubTab('issue')}
                  className="p-3 bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/30 rounded-lg text-left transition-all"
                >
                  <PlusCircle className="w-5 h-5 text-blue-400 mb-1" />
                  <div className="text-xs font-bold text-white">Issue Token</div>
                  <div className="text-[10px] text-gray-400">Scoped access token</div>
                </button>

                <button
                  onClick={() => setActiveSubTab('audit_logs')}
                  className="p-3 bg-purple-600/20 hover:bg-purple-600/30 border border-purple-500/30 rounded-lg text-left transition-all"
                >
                  <History className="w-5 h-5 text-purple-400 mb-1" />
                  <div className="text-xs font-bold text-white">Audit Trail</div>
                  <div className="text-[10px] text-gray-400">Permanent security logs</div>
                </button>
              </div>
            </div>

          </div>

          {/* Right Panel: Workstation Unlock & Permission Distribution */}
          <div className="xl:col-span-2 space-y-6">

            {/* Workstation Token Unlock Form */}
            <div className="glass p-6 rounded-xl border border-dark-border bg-dark-card/30 space-y-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-lg">
                  <Key className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-white">Workstation Unlock Verification</h2>
                  <p className="text-xs text-gray-400">Validate JIT token string against MongoDB SHA-256 store to restore workspace access.</p>
                </div>
              </div>

              <form onSubmit={handleVerify} className="space-y-4">
                <div>
                  <label className="text-xs font-semibold text-gray-300 block mb-1.5">Enter JIT Token (e.g. JIT-XXXX-YYYY-ZZZZ)</label>
                  <div className="flex gap-3">
                    <input
                      type="text"
                      placeholder="JIT-XXXX-YYYY-ZZZZ"
                      value={tokenInput}
                      onChange={(e) => setTokenInput(e.target.value.toUpperCase())}
                      className="flex-1 px-4 py-2.5 bg-dark-hover border border-dark-border rounded-lg text-sm text-white font-mono tracking-widest focus:border-blue-500 focus:outline-none"
                    />
                    <button
                      type="submit"
                      className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold transition-all cursor-pointer flex items-center gap-2"
                    >
                      <ShieldCheck className="w-4 h-4" />
                      Verify & Unlock
                    </button>
                  </div>
                </div>

                {verifyErr && (
                  <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg text-xs text-rose-400 flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    <span>{verifyErr}</span>
                  </div>
                )}

                {verifySuccess && (
                  <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-xs text-emerald-400 flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 shrink-0" />
                    <span>Token verified successfully! JIT access granted. Workstation unlocked.</span>
                  </div>
                )}
              </form>
            </div>

            {/* Permission Scope Breakdown Visualizer */}
            <div className="glass p-6 rounded-xl border border-dark-border bg-dark-card/30 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-dark-border/40 pb-3">
                <div className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-blue-400" />
                  <h2 className="text-base font-bold text-white">Active Permission Scope Distribution</h2>
                </div>
                <div className="flex items-center gap-2">
                  {selectedEmp && (
                    <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full border ${
                      (selectedEmp.current_score ?? 100) >= criticalThreshold
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                        : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                    }`}>
                      {(selectedEmp.current_score ?? 100) >= criticalThreshold
                        ? '🟢 STANDARD ACCESS ACTIVE (ABOVE THRESHOLD)'
                        : '🔴 JIT CONTAINMENT ENFORCED (BELOW THRESHOLD)'
                      }
                    </span>
                  )}
                  <span className="text-xs text-gray-400">Total 16 Scope Modules</span>
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {ALL_PERMISSIONS.map((perm) => {
                  const count = stats.permission_distribution?.[perm] ?? 0;
                  const pct = count > 0 ? 100 : 0;
                  return (
                    <div key={perm} className={`p-3 border rounded-lg flex flex-col justify-between transition-all ${
                      count > 0 ? 'bg-blue-500/10 border-blue-500/30' : 'bg-dark-hover/40 border-dark-border/40 opacity-60'
                    }`}>
                      <span className="text-xs font-medium text-gray-300 truncate" title={perm}>{perm}</span>
                      <div className="flex items-center justify-between mt-2">
                        <div className="h-1.5 flex-1 bg-dark-border rounded-full overflow-hidden mr-2">
                          <div 
                            className={`h-full rounded-full transition-all duration-500 ${count > 0 ? 'bg-blue-500' : 'bg-transparent'}`} 
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                        <span className={`text-[10px] font-mono font-bold ${count > 0 ? 'text-blue-400' : 'text-gray-500'}`}>{count}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

          </div>

        </div>
      )}

      {/* ISSUE TOKEN SUBTAB */}
      {activeSubTab === 'issue' && (
        <div className="glass p-6 rounded-xl border border-dark-border bg-dark-card/30 max-w-4xl mx-auto space-y-6">
          <div className="flex items-center gap-3 border-b border-dark-border pb-4">
            <div className="p-3 bg-blue-500/10 border border-blue-500/30 text-blue-400 rounded-xl">
              <PlusCircle className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Issue New JIT Access Token</h2>
              <p className="text-xs text-gray-400">Grant temporary access tokens with custom expiration timers and individual permission scope selection.</p>
            </div>
          </div>

          <form onSubmit={handleIssueTokenSubmit} className="space-y-6">
            
            {/* Target Employee Info */}
            <div className="p-4 bg-dark-hover/50 rounded-xl border border-dark-border/60 flex items-center justify-between">
              <div>
                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider block">Target Employee</span>
                <span className="text-sm font-bold text-white">{selectedEmp?.full_name || "No employee selected"}</span>
                <span className="text-xs text-gray-400 ml-2">({selectedEmp?.employee_id || "N/A"})</span>
              </div>
              <span className="text-xs px-2.5 py-1 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-md">
                {selectedEmp?.department || selectedEmp?.functional_unit || "SOC"}
              </span>
            </div>

            {/* Access Level Selector with Radio Buttons */}
            <div className="space-y-3 p-4 bg-dark-hover/30 rounded-xl border border-dark-border/60">
              <label className="text-xs font-bold text-gray-200 uppercase tracking-wider block">Access Level</label>
              <div className="space-y-3">
                <label 
                  className={`flex items-start gap-3 p-4 rounded-xl border cursor-pointer transition-all ${
                    issueAccessType === 'Limited Access' 
                      ? 'bg-blue-500/10 border-blue-500/60 text-white ring-1 ring-blue-500/40' 
                      : 'bg-dark-hover/40 border-dark-border/50 text-gray-400 hover:bg-dark-hover'
                  }`}
                >
                  <input
                    type="radio"
                    name="accessLevelRadio"
                    id="accessLevelLimited"
                    value="Limited Access"
                    checked={issueAccessType === 'Limited Access'}
                    onChange={() => setIssueAccessType('Limited Access')}
                    className="mt-1 w-4 h-4 text-blue-500 focus:ring-blue-500 bg-dark-card border-gray-600 cursor-pointer"
                  />
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-bold text-white flex items-center gap-2">
                        <Sliders className="w-4 h-4 text-blue-400" />
                        Limited Access
                      </span>
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/20 text-blue-300 border border-blue-500/30">
                        🟦 LIMITED ACCESS
                      </span>
                    </div>
                    <p className="text-xs text-gray-400 mt-1">Grants only selected limited permission set for the module.</p>
                  </div>
                </label>

                <label 
                  className={`flex items-start gap-3 p-4 rounded-xl border cursor-pointer transition-all ${
                    issueAccessType === 'Full Access' 
                      ? 'bg-rose-500/10 border-rose-500/60 text-white ring-1 ring-rose-500/40' 
                      : 'bg-dark-hover/40 border-dark-border/50 text-gray-400 hover:bg-dark-hover'
                  }`}
                >
                  <input
                    type="radio"
                    name="accessLevelRadio"
                    id="accessLevelFull"
                    value="Full Access"
                    checked={issueAccessType === 'Full Access'}
                    onChange={() => setIssueAccessType('Full Access')}
                    className="mt-1 w-4 h-4 text-rose-500 focus:ring-rose-500 bg-dark-card border-gray-600 cursor-pointer"
                  />
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-bold text-white flex items-center gap-2">
                        <ShieldCheck className="w-4 h-4 text-rose-400" />
                        Full Access
                      </span>
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                        🟥 FULL ACCESS
                      </span>
                    </div>
                    <p className="text-xs text-gray-400 mt-1">Grants complete unrestricted permission set for the module.</p>
                  </div>
                </label>
              </div>
            </div>

            {/* Granular Permission Checkboxes */}
            {issueAccessType === 'Limited Access' && (
              <div className="space-y-3 p-4 bg-dark-hover/30 rounded-xl border border-dark-border/50">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold text-purple-300 uppercase tracking-wider">Configure Granular Permissions ({selectedPermissions.length}/16 Selected)</label>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => setSelectedPermissions([...ALL_PERMISSIONS])}
                      className="text-[10px] text-blue-400 hover:underline"
                    >
                      Select All
                    </button>
                    <span className="text-gray-600">|</span>
                    <button
                      type="button"
                      onClick={() => setSelectedPermissions([])}
                      className="text-[10px] text-rose-400 hover:underline"
                    >
                      Clear All
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {ALL_PERMISSIONS.map((perm) => {
                    const isChecked = selectedPermissions.includes(perm);
                    return (
                      <label 
                        key={perm} 
                        className={`flex items-center gap-2.5 p-2.5 rounded-lg border text-xs font-medium cursor-pointer transition-all ${
                          isChecked 
                            ? 'bg-purple-500/20 border-purple-500/40 text-purple-200' 
                            : 'bg-dark-hover/40 border-dark-border/40 text-gray-400 hover:text-gray-200'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => togglePermission(perm)}
                          className="rounded border-dark-border text-purple-600 focus:ring-purple-500 bg-dark-card"
                        />
                        <span className="truncate">{perm}</span>
                      </label>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Expiration Timer Selector */}
            <div className="space-y-3">
              <label className="text-xs font-bold text-gray-200 uppercase tracking-wider block">2. Select Token Expiration Duration</label>
              
              <div className="grid grid-cols-3 sm:grid-cols-5 gap-2">
                {PRESET_DURATIONS.map((preset) => (
                  <button
                    key={preset}
                    type="button"
                    onClick={() => setSelectedDurationPreset(preset)}
                    className={`py-2 px-3 rounded-lg text-xs font-semibold border transition-all cursor-pointer ${
                      selectedDurationPreset === preset
                        ? 'bg-blue-600 border-blue-500 text-white shadow-md'
                        : 'bg-dark-hover/60 border-dark-border text-gray-300 hover:bg-dark-hover'
                    }`}
                  >
                    {preset}
                  </button>
                ))}
              </div>

              {/* Custom Duration Fields */}
              {selectedDurationPreset === 'Custom Duration' && (
                <div className="p-4 bg-dark-hover/40 rounded-xl border border-dark-border/50 grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3">
                  <div>
                    <label className="text-[10px] text-gray-400 block mb-1">Days</label>
                    <input
                      type="number"
                      min="0"
                      value={customDays}
                      onChange={(e) => setCustomDays(e.target.value)}
                      className="w-full px-3 py-1.5 bg-dark-card border border-dark-border rounded text-xs text-white"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-gray-400 block mb-1">Hours</label>
                    <input
                      type="number"
                      min="0"
                      max="23"
                      value={customHours}
                      onChange={(e) => setCustomHours(e.target.value)}
                      className="w-full px-3 py-1.5 bg-dark-card border border-dark-border rounded text-xs text-white"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-gray-400 block mb-1">Minutes</label>
                    <input
                      type="number"
                      min="0"
                      max="59"
                      value={customMinutes}
                      onChange={(e) => setCustomMinutes(e.target.value)}
                      className="w-full px-3 py-1.5 bg-dark-card border border-dark-border rounded text-xs text-white"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-gray-400 block mb-1">Seconds</label>
                    <input
                      type="number"
                      min="0"
                      max="59"
                      value={customSeconds}
                      onChange={(e) => setCustomSeconds(e.target.value)}
                      className="w-full px-3 py-1.5 bg-dark-card border border-dark-border rounded text-xs text-white"
                    />
                  </div>
                </div>
              )}
            </div>

            {issueError && (
              <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg text-xs text-rose-400 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{issueError}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={issuing}
              className="w-full py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-xl font-bold text-sm transition-all shadow-lg cursor-pointer flex items-center justify-center gap-2"
            >
              {issuing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Key className="w-4 h-4" />}
              <span>Issue & Hashed-Store JIT Access Token</span>
            </button>
          </form>

          {/* Newly Issued Token Display Modal */}
          {newlyIssuedToken && (
            <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
              <div className="glass p-6 rounded-2xl border border-emerald-500/40 bg-dark-card max-w-lg w-full space-y-4 shadow-2xl">
                <div className="flex items-center gap-3 text-emerald-400 border-b border-dark-border pb-3">
                  <CheckCircle2 className="w-6 h-6" />
                  <h3 className="text-lg font-bold text-white">JIT Token Issued Successfully</h3>
                </div>

                <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl text-xs text-amber-300">
                  <span className="font-bold block mb-1">IMPORTANT SECURITY NOTICE:</span>
                  This plaintext token string is displayed ONLY ONCE. In MongoDB, only the SHA-256 cryptographic hash is stored.
                </div>

                <div className="space-y-2">
                  <label className="text-xs text-gray-400 block">Generated Plaintext Token</label>
                  <div className="flex items-center justify-between p-3 bg-dark-hover border border-emerald-500/50 rounded-xl font-mono text-emerald-400 font-bold text-base">
                    <span>{newlyIssuedToken.secure_token}</span>
                    <button
                      onClick={() => handleCopyText(newlyIssuedToken.secure_token)}
                      className="p-1.5 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 rounded-lg text-xs font-sans flex items-center gap-1 cursor-pointer"
                    >
                      {copiedToken === newlyIssuedToken.secure_token ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                      <span>{copiedToken === newlyIssuedToken.secure_token ? 'Copied!' : 'Copy'}</span>
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs text-gray-300 bg-dark-hover/40 p-3 rounded-lg">
                  <div><span className="text-gray-500">Token ID:</span> {newlyIssuedToken.token_id}</div>
                  <div><span className="text-gray-500">Scope:</span> {newlyIssuedToken.access_type}</div>
                  <div><span className="text-gray-500">Permissions:</span> {newlyIssuedToken.granted_permissions?.length || 0} Modules</div>
                  <div><span className="text-gray-500">Expires At:</span> {new Date(newlyIssuedToken.expires_at).toLocaleTimeString()}</div>
                </div>

                <button
                  onClick={() => setNewlyIssuedToken(null)}
                  className="w-full py-2.5 bg-dark-hover hover:bg-gray-800 text-white rounded-xl text-xs font-bold border border-dark-border cursor-pointer"
                >
                  Close & Dismiss
                </button>
              </div>
            </div>
          )}

        </div>
      )}

      {/* ACTIVE TOKENS TABLE SUBTAB */}
      {activeSubTab === 'tokens' && (
        <div className="glass p-6 rounded-xl border border-dark-border bg-dark-card/30 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-dark-border pb-4">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Key className="w-5 h-5 text-blue-400" />
                Persistent JIT Tokens Registry
              </h2>
              <p className="text-xs text-gray-400">Manage issued tokens, extend expiration timers, or revoke active access scopes.</p>
            </div>

            {/* Filter and Search controls */}
            <div className="flex items-center gap-3">
              <div className="relative">
                <Search className="w-4 h-4 text-gray-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Search Token ID / Employee..."
                  value={tokenSearchQuery}
                  onChange={(e) => setTokenSearchQuery(e.target.value)}
                  className="pl-9 pr-3 py-1.5 bg-dark-hover border border-dark-border rounded-lg text-xs text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-1.5 bg-dark-hover border border-dark-border rounded-lg text-xs text-gray-200 focus:outline-none"
              >
                <option value="All">All Statuses</option>
                <option value="Active">Active Only</option>
                <option value="Expired">Expired Only</option>
                <option value="Revoked">Revoked Only</option>
              </select>
            </div>
          </div>

          {/* Tokens Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-gray-300">
              <thead className="bg-dark-hover/60 text-gray-400 uppercase tracking-wider font-semibold border-b border-dark-border">
                <tr>
                  <th className="p-3">Token ID</th>
                  <th className="p-3">Employee</th>
                  <th className="p-3">Permission Scope</th>
                  <th className="p-3">Duration</th>
                  <th className="p-3">Issued At</th>
                  <th className="p-3">Expires At</th>
                  <th className="p-3">Remaining Time</th>
                  <th className="p-3">Status</th>
                  <th className="p-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-border/40">
                {filteredTokens.length > 0 ? filteredTokens.map((t) => (
                  <tr key={t.token_id} className="hover:bg-dark-hover/30 transition-all">
                    <td className="p-3 font-mono font-bold text-blue-400">{t.token_id}</td>
                    <td className="p-3">
                      <div className="font-bold text-white">{t.employee_name}</div>
                      <div className="text-[10px] text-gray-500">{t.employee_id} &middot; {t.department}</div>
                    </td>
                    <td className="p-3">
                      {(t.accessLevel === 'FULL' || t.access_type === 'Full Access') ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                          🟥 FULL ACCESS ({t.granted_permissions?.length || 0})
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/20 text-blue-300 border border-blue-500/30">
                          🟦 LIMITED ACCESS ({t.granted_permissions?.length || 0})
                        </span>
                      )}
                    </td>
                    <td className="p-3 font-semibold text-gray-300">{getDurationDisplay(t)}</td>
                    <td className="p-3 text-gray-400">{new Date(t.issued_at).toLocaleTimeString()}</td>
                    <td className="p-3 text-gray-400">{new Date(t.expires_at).toLocaleTimeString()}</td>
                    <td className="p-3 font-mono font-bold text-cyan-400">{getRemainingTimeDisplay(t)}</td>
                    <td className="p-3">
                      <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                        t.status === 'Active' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                        t.status === 'Expired' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                        'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                      }`}>
                        {t.status}
                      </span>
                    </td>
                    <td className="p-3 text-right space-x-2">
                      <button
                        onClick={() => setSelectedTokenDetails(t)}
                        className="px-2 py-1 bg-dark-hover hover:bg-gray-800 text-gray-300 rounded border border-dark-border text-[10px]"
                      >
                        Details
                      </button>
                      {t.status === 'Active' && (
                        <>
                          <button
                            onClick={() => setExtendModalToken(t)}
                            className="px-2 py-1 bg-blue-600/20 hover:bg-blue-600/40 text-blue-300 rounded border border-blue-500/30 text-[10px]"
                          >
                            Extend
                          </button>
                          <button
                            onClick={() => setRevokeModalToken(t)}
                            className="px-2 py-1 bg-rose-600/20 hover:bg-rose-600/40 text-rose-300 rounded border border-rose-500/30 text-[10px]"
                          >
                            Revoke
                          </button>
                        </>
                      )}
                    </td>
                  </tr>
                )) : (
                  <tr>
                    <td colSpan="9" className="p-8 text-center text-gray-500">
                      No JIT tokens found matching the filter criteria.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* AUDIT LOGS SUBTAB */}
      {activeSubTab === 'audit_logs' && (
        <div className="glass p-6 rounded-xl border border-dark-border bg-dark-card/30 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-dark-border pb-4">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <History className="w-5 h-5 text-purple-400" />
                Permanent JIT Security Audit Trail
              </h2>
              <p className="text-xs text-gray-400">Immutable, append-only logs of all JIT issuing, unlock attempts, extensions, and revocations.</p>
            </div>

            <div className="flex items-center gap-3">
              <div className="relative">
                <Search className="w-4 h-4 text-gray-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Search logs..."
                  value={auditSearchQuery}
                  onChange={(e) => setAuditSearchQuery(e.target.value)}
                  className="pl-9 pr-3 py-1.5 bg-dark-hover border border-dark-border rounded-lg text-xs text-white focus:outline-none"
                />
              </div>

              <select
                value={auditEventFilter}
                onChange={(e) => setAuditEventFilter(e.target.value)}
                className="px-3 py-1.5 bg-dark-hover border border-dark-border rounded-lg text-xs text-gray-200 focus:outline-none"
              >
                <option value="All">All Events</option>
                <option value="Token Issued">Token Issued</option>
                <option value="Token Used">Token Used</option>
                <option value="Unlock Attempt">Unlock Attempt</option>
                <option value="Failed Unlock">Failed Unlock</option>
                <option value="Token Revoked">Token Revoked</option>
                <option value="Timer Extended">Timer Extended</option>
                <option value="Token Expired">Token Expired</option>
              </select>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-gray-300">
              <thead className="bg-dark-hover/60 text-gray-400 uppercase tracking-wider font-semibold border-b border-dark-border">
                <tr>
                  <th className="p-3">Timestamp</th>
                  <th className="p-3">Event Type</th>
                  <th className="p-3">Employee</th>
                  <th className="p-3">Admin</th>
                  <th className="p-3">Token ID</th>
                  <th className="p-3">IP / Device</th>
                  <th className="p-3">Notes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-border/40">
                {filteredLogs.length > 0 ? filteredLogs.map((l, i) => (
                  <tr key={i} className="hover:bg-dark-hover/30 transition-all">
                    <td className="p-3 text-gray-400 font-mono text-[11px]">{new Date(l.timestamp).toLocaleString()}</td>
                    <td className="p-3">
                      <span className={`inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                        l.event_type === 'Token Issued' ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30' :
                        l.event_type === 'Token Used' || l.event_type === 'Unlock Attempt' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' :
                        l.event_type === 'Failed Unlock' ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' :
                        l.event_type === 'Token Revoked' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' :
                        'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                      }`}>
                        {l.event_type}
                      </span>
                    </td>
                    <td className="p-3 font-semibold text-white">{l.employee?.name || l.employee?.id || 'System'}</td>
                    <td className="p-3 text-gray-400">{l.admin?.name || 'System'}</td>
                    <td className="p-3 font-mono text-blue-400">{l.token_id}</td>
                    <td className="p-3 text-gray-400 text-[11px]">
                      <div>{l.ip_address}</div>
                      <div className="text-[9px] text-gray-500 truncate max-w-[120px]">{l.device_info}</div>
                    </td>
                    <td className="p-3 text-gray-300 text-xs max-w-xs truncate">{l.notes}</td>
                  </tr>
                )) : (
                  <tr>
                    <td colSpan="7" className="p-8 text-center text-gray-500">
                      No audit logs match current filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* EXTEND EXPIRY MODAL */}
      {extendModalToken && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="glass p-6 rounded-2xl border border-blue-500/40 bg-dark-card max-w-md w-full space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Clock className="w-5 h-5 text-blue-400" />
              Extend Token Expiration Timer
            </h3>
            <p className="text-xs text-gray-400">Token ID: <span className="font-mono text-blue-400">{extendModalToken.token_id}</span></p>

            <div>
              <label className="text-xs text-gray-300 block mb-1">Additional Duration (Minutes)</label>
              <input
                type="number"
                min="1"
                max="1440"
                value={extendMinutes}
                onChange={(e) => setExtendMinutes(e.target.value)}
                className="w-full px-3 py-2 bg-dark-hover border border-dark-border rounded text-sm text-white"
              />
            </div>

            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setExtendModalToken(null)}
                className="px-4 py-2 bg-dark-hover text-gray-300 rounded text-xs"
              >
                Cancel
              </button>
              <button
                onClick={handleExtendConfirm}
                disabled={actionLoading}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded text-xs"
              >
                {actionLoading ? 'Extending...' : 'Extend Expiry'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* REVOKE TOKEN MODAL */}
      {revokeModalToken && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="glass p-6 rounded-2xl border border-rose-500/40 bg-dark-card max-w-md w-full space-y-4">
            <h3 className="text-base font-bold text-rose-400 flex items-center gap-2">
              <AlertOctagon className="w-5 h-5" />
              Revoke Active JIT Token
            </h3>
            <p className="text-xs text-gray-400">Revoking token <span className="font-mono text-rose-400">{revokeModalToken.token_id}</span> for employee <span className="text-white font-bold">{revokeModalToken.employee_name}</span> will immediately terminate access.</p>

            <div>
              <label className="text-xs text-gray-300 block mb-1">Revocation Reason</label>
              <input
                type="text"
                value={revokeReason}
                onChange={(e) => setRevokeReason(e.target.value)}
                className="w-full px-3 py-2 bg-dark-hover border border-dark-border rounded text-sm text-white"
              />
            </div>

            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setRevokeModalToken(null)}
                className="px-4 py-2 bg-dark-hover text-gray-300 rounded text-xs"
              >
                Cancel
              </button>
              <button
                onClick={handleRevokeConfirm}
                disabled={actionLoading}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white font-bold rounded text-xs"
              >
                {actionLoading ? 'Revoking...' : 'Revoke Token Now'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* TOKEN DETAILS MODAL */}
      {selectedTokenDetails && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="glass p-6 rounded-2xl border border-dark-border bg-dark-card max-w-lg w-full space-y-4">
            <div className="flex items-center justify-between border-b border-dark-border pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <FileText className="w-5 h-5 text-blue-400" />
                JIT Token Metadata
              </h3>
              <button onClick={() => setSelectedTokenDetails(null)} className="text-gray-400 hover:text-white">
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-2 text-xs text-gray-300">
              <div className="flex justify-between py-1 border-b border-dark-border/40">
                <span className="text-gray-500">Token ID:</span>
                <span className="font-mono text-blue-400 font-bold">{selectedTokenDetails.token_id}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-dark-border/40">
                <span className="text-gray-500">Employee:</span>
                <span>{selectedTokenDetails.employee_name} ({selectedTokenDetails.employee_id})</span>
              </div>
              <div className="flex justify-between py-1 border-b border-dark-border/40">
                <span className="text-gray-500">Department:</span>
                <span>{selectedTokenDetails.department}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-dark-border/40">
                <span className="text-gray-500">Issuer Admin:</span>
                <span>{selectedTokenDetails.admin_name} ({selectedTokenDetails.admin_id})</span>
              </div>
              <div className="flex justify-between py-1 border-b border-dark-border/40">
                <span className="text-gray-500">Access Level:</span>
                {(selectedTokenDetails.accessLevel === 'FULL' || selectedTokenDetails.access_type === 'Full Access') ? (
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                    🟥 FULL ACCESS
                  </span>
                ) : (
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/20 text-blue-300 border border-blue-500/30">
                    🟦 LIMITED ACCESS
                  </span>
                )}
              </div>
              <div className="flex justify-between py-1 border-b border-dark-border/40">
                <span className="text-gray-500">Status:</span>
                <span className="font-bold text-emerald-400">{selectedTokenDetails.status}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-dark-border/40">
                <span className="text-gray-500">Issued At:</span>
                <span>{new Date(selectedTokenDetails.issued_at).toLocaleString()}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-dark-border/40">
                <span className="text-gray-500">Expires At:</span>
                <span>{new Date(selectedTokenDetails.expires_at).toLocaleString()}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-dark-border/40">
                <span className="text-gray-500">Last Used:</span>
                <span>{selectedTokenDetails.last_used ? new Date(selectedTokenDetails.last_used).toLocaleString() : 'Never'}</span>
              </div>
            </div>

            <div>
              <span className="text-xs font-bold text-gray-400 block mb-2">Granted Permission Modules ({selectedTokenDetails.granted_permissions?.length || 0}):</span>
              <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto p-2 bg-dark-hover/40 rounded-lg">
                {selectedTokenDetails.granted_permissions?.map(p => (
                  <span key={p} className="px-2 py-0.5 bg-blue-500/10 text-blue-300 border border-blue-500/20 text-[10px] rounded">
                    {p}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
