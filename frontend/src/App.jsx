import React, { useState, useEffect, useRef } from 'react';
import { 
  Shield, ShieldAlert, ShieldCheck, Search, Users, User, Clock, 
  AlertTriangle, FileText, HardDrive, Mail, Globe, Key, KeyRound, Lock, CheckCircle2, Terminal, 
  RefreshCw, Send, Brain, ChevronRight, Activity, Cpu, AlertCircle, Info, LogOut, Sun, Moon, Box, Fingerprint, Server
} from 'lucide-react';
import { Chart } from 'chart.js/auto';
import LoginPage from './components/LoginPage';
import JitPamDashboard from './components/JitPamDashboard';
import SandboxDashboard from './components/SandboxDashboard';
import HumanIdentityDashboard from './components/HumanIdentityDashboard';
import RbacUserManagementModal from './components/RbacUserManagementModal';
import AuditLogsView from './components/AuditLogsView';
import { auth, signOut, onAuthStateChanged, isFirebaseConfigured } from './firebase';

const API_BASE = 'http://localhost:5000/api';

export default function App() {
  // Authentication State
  const [authUser, setAuthUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);

  // RBAC User Management & Escalation Modal States
  const [showUserMgmtModal, setShowUserMgmtModal] = useState(false);
  const [showEscalateModal, setShowEscalateModal] = useState(false);
  const [escalateSummary, setEscalateSummary] = useState('');
  const [escalateThreatLevel, setEscalateThreatLevel] = useState('High');
  const [escalateLoading, setEscalateLoading] = useState(false);
  const [escalateMsg, setEscalateMsg] = useState('');

  // Change Password Modal State
  const [showChangePassModal, setShowChangePassModal] = useState(false);
  const [currPass, setCurrPass] = useState('');
  const [newPass, setNewPass] = useState('');
  const [confirmPass, setConfirmPass] = useState('');
  const [passLoading, setPassLoading] = useState(false);
  const [passMsg, setPassMsg] = useState('');
  const [passErr, setPassErr] = useState('');

  // Theme State ('dark' | 'light')
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('garuda_theme') || 'dark';
  });

  const toggleTheme = () => {
    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
    localStorage.setItem('garuda_theme', nextTheme);
  };

  // Navigation Tab State ('threat_console' | 'jit_pam')
  const [activeTab, setActiveTab] = useState('threat_console');

  // NEW JIT WORKFLOW STATE (Employee Workstation Lock Simulation)
  const [criticalThreshold, setCriticalThreshold] = useState(30);
  const [employeeLocks, setEmployeeLocks] = useState({}); // { [empId]: { status, countdown, lockTime, token } }
  const [triggeredEmps, setTriggeredEmps] = useState(new Set());

  // Application State
  const [employees, setEmployees] = useState([]);
  const [selectedEmp, setSelectedEmp] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [scoreHistory, setScoreHistory] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [health, setHealth] = useState(null);
  
  // Interactive Controls state
  const [search, setSearch] = useState('');
  const [deptFilter, setDeptFilter] = useState('All Units');
  const [departmentsList, setDepartmentsList] = useState(['All Units']);
  const [selectedScenario, setSelectedScenario] = useState('usb_theft');
  const [simulating, setSimulating] = useState(false);
  const [resetting, setResetting] = useState(false);
  
  // AI Investigation & Chat State
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [aiReport, setAiReport] = useState('');
  const [loadingReport, setLoadingReport] = useState(false);
  const [chatMessage, setChatMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([
    { role: 'assistant', text: "Hi! I'm Garuda AI, your AI-powered cybersecurity and FinTech assistant. How can I help you today?" }
  ]);
  const [sendingChat, setSendingChat] = useState(false);
  
  // Loading & Error States
  const [loadingEmployees, setLoadingEmployees] = useState(true);
  const [loadingTimeline, setLoadingTimeline] = useState(false);

  const cleanDept = (deptStr) => {
    if (!deptStr) return '';
    let s = String(deptStr);
    if (s.includes(' - ')) {
      s = s.split(' - ')[1].trim();
    } else {
      s = s.trim();
    }
    if (!s || /^\d+$/.test(s)) return '';
    return s;
  };

  const chartRef = useRef(null);
  const chartInstance = useRef(null);
  const chatBottomRef = useRef(null);

  // Monitor Auth session persistence
  useEffect(() => {
    if (isFirebaseConfigured && auth) {
      const unsubscribe = onAuthStateChanged(auth, async (user) => {
        if (user) {
          try {
            const tokenResult = await user.getIdTokenResult();
            const role = tokenResult.claims?.role || 'analyst';
            setAuthUser({
              uid: user.uid,
              email: user.email,
              displayName: user.displayName || user.email.split('@')[0],
              role: role
            });
          } catch (e) {
            setAuthUser({
              uid: user.uid,
              email: user.email,
              displayName: user.email.split('@')[0],
              role: 'analyst'
            });
          }
        } else {
          setAuthUser(null);
        }
        setAuthLoading(false);
      });
      return () => unsubscribe();
    } else {
      const storedUser = localStorage.getItem('garuda_user');
      if (storedUser) {
        try {
          setAuthUser(JSON.parse(storedUser));
        } catch (e) {
          localStorage.removeItem('garuda_user');
        }
      }
      setAuthLoading(false);
    }
  }, []);

  const handleLogout = async () => {
    if (isFirebaseConfigured && auth) {
      await signOut(auth);
    }
    localStorage.removeItem('garuda_user');
    localStorage.removeItem('garuda_token');
    setAuthUser(null);
  };

  const handleChangePasswordSubmit = async (e) => {
    e.preventDefault();
    setPassErr('');
    setPassMsg('');

    const targetEmail = authUser?.email || (localStorage.getItem('garuda_user') ? JSON.parse(localStorage.getItem('garuda_user')).email : 'admin@garuda.ai');

    if (!currPass || !newPass || !confirmPass) {
      setPassErr('All fields are required.');
      return;
    }

    if (newPass !== confirmPass) {
      setPassErr('New password and confirm password do not match.');
      return;
    }

    if (newPass.length < 6) {
      setPassErr('New password must be at least 6 characters.');
      return;
    }

    setPassLoading(true);

    try {
      const response = await fetch(`${API_BASE}/auth/change-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: targetEmail,
          current_password: currPass,
          new_password: newPass
        })
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setPassMsg('Password updated with ML-KEM-768 Post-Quantum Protection!');
        setCurrPass('');
        setNewPass('');
        setConfirmPass('');
        setTimeout(() => {
          setShowChangePassModal(false);
          setPassMsg('');
        }, 1800);
      } else {
        setPassErr(data.error || 'Failed to change password. Please check your current password.');
      }
    } catch (err) {
      console.error("Change password connection error:", err);
      // If backend Flask server is offline or unreachable
      setPassErr('Backend server offline. Please ensure "python backend/app.py" is running on port 5000.');
    } finally {
      setPassLoading(false);
    }
  };

  // Initialize and Fetch Initial Dashboard Data
  useEffect(() => {
    if (authUser) {
      fetchHealth();
      fetchDepartments();
      fetchEmployees();
      fetchAlerts();
    }
  }, [authUser]);

  // Auto select first matching employee if currently selected employee is filtered out
  useEffect(() => {
    const list = (employees || []).filter(e => {
      if (!e) return false;
      const name = e.full_name || '';
      const matchesSearch = name.toLowerCase().includes((search || '').toLowerCase());
      const matchesDept = deptFilter === 'All' || deptFilter === 'All Units' || cleanDept(e.department) === deptFilter;
      return matchesSearch && matchesDept;
    });
    if (list.length > 0 && (!selectedEmp || !list.some(e => e && e.employee_id === selectedEmp.employee_id))) {
      setSelectedEmp(list[0]);
    }
  }, [deptFilter, search, employees]);

  // Fetch employee details when selection changes
  useEffect(() => {
    if (selectedEmp) {
      fetchEmployeeDetails(selectedEmp.employee_id);
    }
  }, [selectedEmp]);

  // Scroll Chat to bottom on history change
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  // 1. JIT Warning Countdown & Expiration Timer Effect
  useEffect(() => {
    const timer = setInterval(() => {
      let logsToTrigger = [];

      setEmployeeLocks(prev => {
        const updated = { ...prev };
        let changed = false;

        Object.keys(updated).forEach(empId => {
          const lock = updated[empId];
          if (lock.status === 'WARNING' && lock.countdown > 0) {
            changed = true;
            const newCount = lock.countdown - 1;
            updated[empId] = {
              ...lock,
              countdown: newCount,
              status: newCount === 0 ? 'LOCKED' : 'WARNING'
            };

            if (newCount === 0) {
              logsToTrigger.push(empId);
            }
          }

          // Handle Token Expiration Timer
          if (lock.token && lock.token.status === 'Active') {
            const elapsed = Math.floor((Date.now() - lock.token.createdAt) / 1000);
            const remaining = Math.max(0, 60 - elapsed);
            if (remaining !== lock.token.timeLeft) {
              changed = true;
              updated[empId] = {
                ...lock,
                token: {
                  ...lock.token,
                  timeLeft: remaining,
                  status: remaining === 0 ? 'Expired' : 'Active'
                }
              };
            }
          }
        });

        return changed ? updated : prev;
      });

      // Trigger automatic lock event logging if timer reaches 0
      logsToTrigger.forEach(empId => {
        logTimelineEvent(empId, "• Countdown Reached Zero", "Critical");
        logTimelineEvent(empId, "• Workstation Automatically Locked", "Critical");
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  // 2. Critical Threshold Trust Score Monitor Effect
  useEffect(() => {
    if (!selectedEmp) return;
    const empId = selectedEmp.employee_id;
    const score = selectedEmp.current_score;

    if (typeof score === 'number' && score < criticalThreshold) {
      if (!triggeredEmps.has(empId)) {
        setTriggeredEmps(prev => new Set([...prev, empId]));

        setEmployeeLocks(prev => ({
          ...prev,
          [empId]: {
            status: 'WARNING',
            countdown: 30,
            lockTime: new Date().toLocaleTimeString(),
            token: null
          }
        }));

        logTimelineEvent(empId, "Critical Trust Threshold Reached", "Critical");
      }
    }
  }, [selectedEmp?.current_score, criticalThreshold, employeeLocks]);

  // Admin Just-in-Time Access Token Generation (MongoDB API & Fallback)
  const handleGenerateJitToken = async (empId, tokenDataOrAccessType = 'Full Access', grantedPermissions = null, presetDuration = '1 Hour', customDuration = null) => {
    if (!selectedEmp && !empId) return;

    // If a complete issued token document was passed from JitPamDashboard, register it in state directly
    if (typeof tokenDataOrAccessType === 'object' && tokenDataOrAccessType !== null) {
      const existingDoc = tokenDataOrAccessType;
      const tokenObj = {
        tokenId: existingDoc.token_id || existingDoc.tokenId,
        token: existingDoc.secure_token || existingDoc.plain_token || existingDoc.token,
        createdAt: Date.now(),
        expiresAt: new Date(existingDoc.expires_at || Date.now() + 3600000).getTime(),
        generatedTime: new Date(existingDoc.issued_at || Date.now()).toLocaleTimeString(),
        expiryTime: new Date(existingDoc.expires_at || Date.now() + 3600000).toLocaleTimeString(),
        generatedBy: existingDoc.admin_name || existingDoc.generated_by || 'Admin',
        employeeName: existingDoc.employee_name || selectedEmp?.full_name,
        employeeId: empId || existingDoc.employee_id,
        accessLevel: existingDoc.accessLevel || (existingDoc.access_type === 'Limited Access' ? 'LIMITED' : 'FULL'),
        access_type: existingDoc.access_type || 'Full Access',
        riskLevel: 'Critical',
        score: selectedEmp?.current_score ?? 100,
        status: existingDoc.status || 'Active',
        grantedPermissions: existingDoc.granted_permissions || []
      };

      setEmployeeLocks(prev => ({
        ...prev,
        [empId]: {
          ...prev[empId],
          token: tokenObj
        }
      }));

      logTimelineEvent(empId, "• JIT Token Issued (MongoDB Persistent)", "Info");
      return { success: true, token: tokenObj.token };
    }

    const requestedAccessType = typeof tokenDataOrAccessType === 'string' ? tokenDataOrAccessType : 'Full Access';
    const levelStr = requestedAccessType === 'Limited Access' ? 'LIMITED' : 'FULL';
    const permissionsToGrant = grantedPermissions || (levelStr === 'FULL' ? [
      "Dashboard", "Employee List", "Investigations", "AI Investigation", 
      "Reports", "Analytics", "Activity Timeline", "Trust Score", 
      "Alerts", "User Management", "Settings", "Export Data", 
      "Audit Logs", "Model Management", "Dataset Upload", "System Configuration"
    ] : ["Dashboard", "AI Investigation"]);

    try {
      const response = await fetch(`${API_BASE}/jit/tokens/issue`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          employee_id: empId,
          employee_name: selectedEmp?.full_name || `Employee ${empId}`,
          department: selectedEmp?.functional_unit || selectedEmp?.department || 'SOC Division',
          admin_id: authUser?.uid || 'GAR-0001',
          admin_name: authUser?.displayName || 'Lead Security Administrator',
          access_type: requestedAccessType,
          accessLevel: levelStr,
          granted_permissions: permissionsToGrant,
          preset_duration: presetDuration,
          custom_duration: customDuration
        })
      });

      const data = await response.json();
      if (data.success) {
        const tokenObj = {
          tokenId: data.token.token_id,
          token: data.secure_token,
          createdAt: Date.now(),
          expiresAt: new Date(data.token.expires_at).getTime(),
          generatedTime: new Date(data.token.issued_at).toLocaleTimeString(),
          expiryTime: new Date(data.token.expires_at).toLocaleTimeString(),
          generatedBy: data.token.admin_name,
          employeeName: data.token.employee_name,
          employeeId: empId,
          accessLevel: data.token.accessLevel || levelStr,
          access_type: data.token.access_type || requestedAccessType,
          riskLevel: 'Critical',
          score: selectedEmp?.current_score ?? 100,
          status: 'Active',
          grantedPermissions: data.token.granted_permissions
        };

        setEmployeeLocks(prev => ({
          ...prev,
          [empId]: {
            ...prev[empId],
            token: tokenObj
          }
        }));

        logTimelineEvent(empId, "• JIT Token Generated (MongoDB Persistent)", "Info");
        return { success: true, token: data.secure_token };
      }
    } catch (e) {
      console.warn("Backend JIT API fallback to local generation:", e);
    }

    // Local in-memory fallback
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    const p1 = Array.from({ length: 4 }, () => chars[Math.floor(Math.random() * chars.length)]).join('');
    const p2 = Array.from({ length: 4 }, () => chars[Math.floor(Math.random() * chars.length)]).join('');
    const tokenStr = `JIT-${p1}-${p2}`;
    const tokenId = `TK-${Math.floor(100000 + Math.random() * 900000)}`;
    const now = new Date();
    const expiresAtMs = Date.now() + 3600000;
    const expiry = new Date(expiresAtMs);

    const tokenObj = {
      tokenId: tokenId,
      token: tokenStr,
      createdAt: Date.now(),
      expiresAt: expiresAtMs,
      generatedTime: now.toLocaleTimeString(),
      expiryTime: expiry.toLocaleTimeString(),
      generatedBy: authUser?.displayName || 'Admin',
      employeeName: selectedEmp.full_name,
      employeeId: empId,
      riskLevel: 'Critical',
      score: selectedEmp?.current_score ?? 100,
      status: 'Active'
    };

    setEmployeeLocks(prev => ({
      ...prev,
      [empId]: {
        ...prev[empId],
        token: tokenObj
      }
    }));

    logTimelineEvent(empId, "• JIT Token Generated", "Info");
    return { success: true, token: tokenStr };
  };

  // Employee Unlock Verification (MongoDB API & Fallback)
  const handleVerifyJitToken = async (empId, inputVal) => {
    try {
      const response = await fetch(`${API_BASE}/jit/tokens/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token: inputVal.trim(),
          employee_id: empId
        })
      });

      const data = await response.json();
      if (data.success) {
        setEmployeeLocks(prev => ({
          ...prev,
          [empId]: {
            ...prev[empId],
            status: 'UNLOCKED',
            token: {
              ...prev[empId]?.token,
              status: 'Used',
              grantedPermissions: data.token?.granted_permissions || []
            }
          }
        }));

        logTimelineEvent(empId, "• Employee Entered Token", "Low");
        logTimelineEvent(empId, "• Token Verified (MongoDB Security Check)", "Low");
        logTimelineEvent(empId, "• Employee Access Restored", "Low");

        return { success: true, token: data.token };
      } else {
        return { success: false, error: data.error || 'Invalid Token' };
      }
    } catch (e) {
      console.warn("Backend JIT verification fallback:", e);
    }

    // Local fallback check
    const currentLock = employeeLocks[empId];
    if (!currentLock || !currentLock.token) {
      return { success: false, error: 'Invalid Token' };
    }

    const tokenObj = currentLock.token;
    if (tokenObj.status === 'Used') {
      return { success: false, error: 'Token already used.' };
    }

    if (inputVal.trim().toUpperCase() !== tokenObj.token) {
      return { success: false, error: 'Invalid Token' };
    }

    setEmployeeLocks(prev => ({
      ...prev,
      [empId]: {
        ...prev[empId],
        status: 'UNLOCKED',
        token: {
          ...tokenObj,
          status: 'Used'
        }
      }
    }));

    logTimelineEvent(empId, "• Employee Entered Token", "Low");
    logTimelineEvent(empId, "• Token Verified", "Low");
    logTimelineEvent(empId, "• Employee Access Restored", "Low");

    return { success: true };
  };


  // Render History Chart.js Line Chart with Red Vertical Threshold Line Marker
  useEffect(() => {
    try {
      if (scoreHistory && scoreHistory.length > 0 && chartRef.current) {
        if (chartInstance.current) {
          chartInstance.current.destroy();
        }
        
        const ctx = chartRef.current.getContext('2d');
        const labels = scoreHistory.map(h => (h.timestamp ? h.timestamp.split(' ')[0] : ''));
        const scores = scoreHistory.map(h => h.score);

        // Custom Plugin for Vertical Red Marker "Critical Threshold Reached"
        const criticalMarkerPlugin = {
          id: 'criticalMarkerPlugin',
          afterDraw: (chart) => {
            try {
              const thresholdIdx = scoreHistory.findIndex(h => Number(h.score) <= criticalThreshold);
              if (thresholdIdx !== -1) {
                const meta = chart.getDatasetMeta(0);
                const point = meta.data[thresholdIdx];
                if (point) {
                  const { ctx, chartArea } = chart;
                  const x = point.x;

                  ctx.save();
                  ctx.beginPath();
                  ctx.moveTo(x, chartArea.top);
                  ctx.lineTo(x, chartArea.bottom);
                  ctx.lineWidth = 2;
                  ctx.setLineDash([4, 4]);
                  ctx.strokeStyle = '#EF4444';
                  ctx.stroke();

                  const labelText = 'Critical Threshold Reached';
                  ctx.font = 'bold 10px sans-serif';
                  const textWidth = ctx.measureText(labelText).width;
                  ctx.fillStyle = '#EF4444';
                  ctx.fillRect(x - textWidth / 2 - 4, chartArea.top + 4, textWidth + 8, 16);

                  ctx.fillStyle = '#FFFFFF';
                  ctx.textAlign = 'center';
                  ctx.textBaseline = 'middle';
                  ctx.fillText(labelText, x, chartArea.top + 12);

                  ctx.restore();
                }
              }
            } catch (err) {
              console.error("Plugin draw error:", err);
            }
          }
        };

        chartInstance.current = new Chart(ctx, {
          type: 'line',
          data: {
            labels: labels,
            datasets: [{
              label: 'Behavior Trust Score',
              data: scores,
              borderColor: '#3B82F6',
              backgroundColor: 'rgba(59, 130, 246, 0.05)',
              borderWidth: 2,
              tension: 0.3,
              fill: true,
              pointBackgroundColor: '#3B82F6',
              pointBorderColor: '#090D16',
              pointHoverRadius: 6,
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false },
              tooltip: {
                backgroundColor: theme === 'light' ? '#FFFFFF' : '#121826',
                titleColor: theme === 'light' ? '#0F172A' : '#94A3B8',
                bodyColor: theme === 'light' ? '#1E293B' : '#F3F4F6',
                borderColor: theme === 'light' ? '#E2E8F0' : '#1F293D',
                borderWidth: 1,
                callbacks: {
                  label: function(context) {
                    const idx = context.dataIndex;
                    const reason = scoreHistory[idx]?.reason || 'Standard update';
                    return ` Score: ${context.raw} (${reason})`;
                  }
                }
              }
            },
            scales: {
              x: {
                grid: { color: theme === 'light' ? 'rgba(203, 213, 225, 0.6)' : 'rgba(31, 41, 61, 0.2)' },
                ticks: { color: theme === 'light' ? '#475569' : '#64748B', font: { size: 10 } }
              },
              y: {
                min: 0,
                max: 100,
                grid: { color: theme === 'light' ? 'rgba(203, 213, 225, 0.6)' : 'rgba(31, 41, 61, 0.2)' },
                ticks: { color: theme === 'light' ? '#475569' : '#64748B', font: { size: 10 } }
              }
            }
          },
          plugins: [criticalMarkerPlugin]
        });
      }
    } catch (e) {
      console.error('Error rendering Chart.js instance:', e);
    }
  }, [scoreHistory, theme, criticalThreshold]);

  const logTimelineEvent = async (empId, description, severity = 'Low') => {
    try {
      const token = localStorage.getItem('garuda_token');
      const headers = { 'Content-Type': 'application/json' };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const res = await fetch(`${API_BASE}/employees/${empId}/events`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          description: description,
          type: 'jit_sim',
          severity: severity
        })
      });
      
      if (res.ok) {
        if (selectedEmp && selectedEmp.employee_id === empId) {
          fetchEmployeeDetails(empId);
        }
      }
    } catch (e) {
      console.error('Error logging JIT timeline event to backend', e);
    }
  };

  // API Call Implementations
  const getHeaders = () => {
    const headers = { 'Content-Type': 'application/json' };
    const token = localStorage.getItem('garuda_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  };

  const fetchHealth = async () => {
    try {
      const res = await fetch(`${API_BASE}/health`);
      const data = await res.json();
      setHealth(data);
    } catch (e) {
      console.error('Health check failed', e);
    }
  };

  const fetchDepartments = async () => {
    try {
      const res = await fetch(`${API_BASE}/departments`, { headers: getHeaders() });
      const data = await res.json();
      if (Array.isArray(data)) {
        const cleaned = Array.from(new Set(data.map(item => cleanDept(item)).filter(Boolean)));
        setDepartmentsList(cleaned);
      }
    } catch (e) {
      console.error('Error fetching departments', e);
    }
  };

  const fetchEmployees = async () => {
    setLoadingEmployees(true);
    try {
      const res = await fetch(`${API_BASE}/employees`, { headers: getHeaders() });
      const data = await res.json();
      const empList = Array.isArray(data) ? data : (data.employees || []);
      setEmployees(empList);
      if (empList.length > 0 && !selectedEmp) {
        setSelectedEmp(empList[0]);
      }
    } catch (e) {
      console.error('Error fetching employees', e);
      setEmployees([]);
    } finally {
      setLoadingEmployees(false);
    }
  };

  const fetchAlerts = async () => {
    try {
      const res = await fetch(`${API_BASE}/alerts`, { headers: getHeaders() });
      const data = await res.json();
      const alertList = Array.isArray(data) ? data : (data.alerts || []);
      setAlerts(alertList);
      if (alertList.length > 0 && !selectedAlert) {
        setSelectedAlert(alertList[0]);
        fetchAIExplanation(alertList[0].alert_id);
      }
    } catch (e) {
      console.error('Error fetching alerts', e);
      setAlerts([]);
    }
  };

  const fetchEmployeeDetails = async (empId) => {
    setLoadingTimeline(true);
    try {
      // Fetch timeline
      const tRes = await fetch(`${API_BASE}/employees/${empId}/timeline`, { headers: getHeaders() });
      const tData = await tRes.json();
      setTimeline(Array.isArray(tData) ? tData : []);

      // Fetch history
      const hRes = await fetch(`${API_BASE}/employees/${empId}/trust-score/history`, { headers: getHeaders() });
      const hData = await hRes.json();
      setScoreHistory(Array.isArray(hData) ? hData : []);
    } catch (e) {
      console.error('Error fetching employee details', e);
      setTimeline([]);
      setScoreHistory([]);
    } finally {
      setLoadingTimeline(false);
    }
  };

  const fetchAIExplanation = async (alertId) => {
    setLoadingReport(true);
    setAiReport('');
    try {
      const res = await fetch(`${API_BASE}/alerts/${alertId}/explanation`, { headers: getHeaders() });
      const data = await res.json();
      setAiReport(data.explanation);
    } catch (e) {
      setAiReport('Failed to generate AI investigation narrative.');
      console.error('Error generating explanation', e);
    } finally {
      setLoadingReport(false);
    }
  };

  const fetchEmployeeInvestigation = async (empId) => {
    setLoadingReport(true);
    setAiReport('');
    try {
      const res = await fetch(`${API_BASE}/employees/${empId}/investigation`, { headers: getHeaders() });
      const data = await res.json();
      setAiReport(data.report);
    } catch (e) {
      setAiReport('Failed to generate CERT Release 4.2 evidence-based investigation report.');
      console.error('Error generating employee investigation', e);
    } finally {
      setLoadingReport(false);
    }
  };

  // Action Handlers
  const handleSimulate = async () => {
    if (!selectedEmp) return;
    setSimulating(true);
    try {
      const res = await fetch(`${API_BASE}/simulate`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
          scenario: selectedScenario,
          employee_id: selectedEmp.employee_id
        })
      });
      const data = await res.json();
      console.log('[DEV_LOG] Simulation API Response:', data);
      console.log('[DEV_LOG] Frontend Received Value (Trust Score):', data.new_score);
      
      // Update UI components
      await fetchEmployees();
      await fetchAlerts();
      
      // Reload current selected employee details
      if (selectedEmp.employee_id === data.employee_id) {
        await fetchEmployeeDetails(data.employee_id);
      }
      
      // Auto select the newly generated simulation alert
      if (data.alert_id) {
        const simAlert = {
          alert_id: data.alert_id,
          employee_id: data.employee_id,
          type: selectedScenario === 'usb_theft' ? 'USB Theft' : selectedScenario === 'mass_download' ? 'Mass File Download' : selectedScenario === 'impossible_travel' ? 'Impossible Travel' : 'Privilege Escalation',
          severity: 'Critical'
        };
        setSelectedAlert(simAlert);
        fetchAIExplanation(data.alert_id);
      }
    } catch (e) {
      console.error('Simulation failed', e);
    } finally {
      setSimulating(false);
    }
  };

  const handleResetDemo = async () => {
    setResetting(true);
    try {
      await fetch(`${API_BASE}/reset`, { method: 'POST', headers: getHeaders() });
      await fetchEmployees();
      await fetchAlerts();
      if (selectedEmp) {
        await fetchEmployeeDetails(selectedEmp.employee_id);
      }
      setEmployeeLocks({});
      setAiReport('Demo database successfully reset to standard baseline state.');
    } catch (e) {
      console.error('Database reset failed', e);
    } finally {
      setResetting(false);
    }
  };

  const handleSendChat = async (e) => {
    e.preventDefault();
    if (!chatMessage.trim()) return;
    
    const userMsg = chatMessage;
    setChatMessage('');
    setChatHistory(prev => [...prev, { role: 'user', text: userMsg }]);
    setSendingChat(true);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ message: userMsg })
      });
      const data = await res.json();
      setChatHistory(prev => [...prev, { role: 'assistant', text: data.response }]);
    } catch (e) {
      setChatHistory(prev => [...prev, { role: 'assistant', text: 'Error contacting security assistant server.' }]);
    } finally {
      setSendingChat(false);
    }
  };

  // Helper styling calculators
  const getScoreColorClass = (score) => {
    if (score >= 80) return 'text-low border-low';
    if (score >= 60) return 'text-medium border-medium';
    if (score >= 40) return 'text-high border-high';
    return 'text-critical border-critical';
  };

  const getScoreProgressClass = (score) => {
    if (score >= 80) return 'bg-emerald-500';
    if (score >= 60) return 'bg-amber-500';
    if (score >= 40) return 'bg-rose-500';
    return 'bg-fuchsia-500';
  };

  const getTimelineIcon = (type) => {
    switch (type) {
      case 'logon': return <Key className="w-4 h-4 text-blue-400" />;
      case 'file': return <FileText className="w-4 h-4 text-amber-400" />;
      case 'device': return <HardDrive className="w-4 h-4 text-purple-400" />;
      case 'http': return <Globe className="w-4 h-4 text-emerald-400" />;
      case 'email': return <Mail className="w-4 h-4 text-indigo-400" />;
      case 'privilege': return <Terminal className="w-4 h-4 text-rose-400" />;
      case 'sandbox': return <Box className="w-4 h-4 text-cyan-400" />;
      default: return <Info className="w-4 h-4 text-gray-400" />;
    }
  };

  // Filters calculation
  const filteredEmployees = (employees || []).filter(emp => {
    if (!emp) return false;
    const name = (emp.full_name || '').toLowerCase();
    const empId = (emp.employee_id || '').toLowerCase();
    const q = (search || '').toLowerCase();
    const matchesSearch = name.includes(q) || empId.includes(q);
    const matchesDept = deptFilter === 'All' || deptFilter === 'All Units' || 
                        emp.department === deptFilter || emp.functional_unit === deptFilter || emp.business_unit === deptFilter ||
                        (emp.department && emp.department.endsWith(` - ${deptFilter}`)) ||
                        (emp.functional_unit && emp.functional_unit.endsWith(` - ${deptFilter}`)) ||
                        (emp.business_unit && emp.business_unit.endsWith(` - ${deptFilter}`));
    return matchesSearch && matchesDept;
  });

  // Unauthenticated Guard
  if (authLoading) {
    return (
      <div className="flex flex-col h-screen w-screen items-center justify-center bg-dark-bg text-blue-500 font-sans gap-3">
        <img src="/garuda-logo.png" alt="Garuda AI Logo" className="w-16 h-16 object-contain animate-pulse" />
        <span className="text-xs text-gray-400 font-semibold tracking-widest uppercase">Initializing Garuda AI Platform...</span>
      </div>
    );
  }

  if (!authUser) {
    return <LoginPage theme={theme} onToggleTheme={toggleTheme} onLoginSuccess={(userProfile) => setAuthUser(userProfile)} />;
  }

  return (
    <div className={`flex h-screen w-screen overflow-hidden ${theme === 'light' ? 'light-theme bg-slate-50 text-slate-900' : 'dark-theme bg-dark-bg text-gray-200'}`}>
      
      {/* Sidebar: Identity panel */}
      <aside className="w-80 flex flex-col border-r border-dark-border bg-dark-card/50">
        
        {/* Branding header */}
        <div className="p-4 border-b border-dark-border flex items-center gap-3">
          <img src="/garuda-logo.png" alt="Garuda AI Logo" className="w-10 h-10 object-contain filter drop-shadow-sm shrink-0" />
          <div>
            <h1 className="text-lg font-black tracking-wider text-white">GARUDA<span className="text-blue-500">AI</span></h1>
            <p className="text-[10px] text-gray-500 uppercase tracking-widest font-semibold">Insider Threat Intelligence</p>
          </div>
        </div>

        {/* Global status summary */}
        <div className="p-4 mx-4 my-3 bg-dark-bg/60 rounded-lg border border-dark-border/50 flex flex-col gap-2">
          <div className="flex justify-between items-center text-xs text-gray-400">
            <span>Database Connection:</span>
            <span className="flex items-center gap-1.5 font-medium text-emerald-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span>
              {health?.database || 'Checking...'}
            </span>
          </div>
          <div className="flex justify-between items-center text-xs text-gray-400">
            <span>AI Processing:</span>
            <span className="text-blue-400 font-medium">{health?.gemini_api || 'Offline'}</span>
          </div>
        </div>

        {/* Filters */}
        <div className="p-4 flex flex-col gap-3 border-b border-dark-border/40">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-500" />
            <input 
              type="text" 
              placeholder="Search employee id or name..."
              className="w-full pl-9 pr-8 py-2 text-sm bg-dark-bg border border-dark-border rounded-md text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
            {search && (
              <button 
                onClick={() => setSearch('')}
                className="absolute right-2.5 top-2.5 text-xs text-gray-500 hover:text-gray-300"
              >
                ✕
              </button>
            )}
          </div>
          
          <select
            className="w-full py-2 px-3 text-sm bg-dark-bg border border-dark-border rounded-md text-gray-300 focus:outline-none focus:border-blue-500 cursor-pointer"
            value={deptFilter}
            onChange={e => setDeptFilter(e.target.value)}
          >
            {departmentsList.map((unit, idx) => (
              <option key={idx} value={unit}>{unit}</option>
            ))}
          </select>

          {/* Clear Filter */}
          {(deptFilter !== 'All Units' || search !== '') && (
            <div className="flex justify-end text-[11px] px-1">
              <button 
                onClick={() => { setDeptFilter('All Units'); setSearch(''); }}
                className="text-blue-400 hover:underline font-medium cursor-pointer"
              >
                Reset Filters
              </button>
            </div>
          )}
        </div>

        {/* Employee List container */}
        <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-2">
          {loadingEmployees ? (
            <div className="flex justify-center p-8">
              <RefreshCw className="w-6 h-6 animate-spin text-blue-500" />
            </div>
          ) : filteredEmployees.length === 0 ? (
            <div className="text-center p-8 text-gray-500 text-sm">No employees found.</div>
          ) : (
            filteredEmployees.map(emp => {
              const isSelected = selectedEmp?.employee_id === emp.employee_id;
              const hasAlert = Array.isArray(alerts) && alerts.some(a => a && a.employee_id === emp.employee_id);
              
              return (
                <button
                  key={emp.employee_id}
                  onClick={() => setSelectedEmp(emp)}
                  className={`w-full text-left p-3 rounded-lg border transition-all flex flex-col gap-1.5 cursor-pointer ${
                    isSelected 
                      ? 'bg-dark-hover/80 border-blue-500/80' 
                      : 'bg-dark-card border-dark-border/40 hover:bg-dark-hover/40'
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <div className="font-semibold text-sm text-gray-200 flex items-center gap-1.5">
                      {emp.full_name}
                      {hasAlert && <span className="w-2 h-2 rounded-full bg-rose-500" title="Active Security Alert"></span>}
                    </div>
                    <span className="text-[10px] bg-dark-bg/80 text-gray-500 px-1.5 py-0.5 rounded font-mono">
                      {emp.employee_id}
                    </span>
                  </div>

                  <div className="flex justify-between items-center text-xs text-gray-500">
                    <span>{emp.role}</span>
                    <span className={`font-semibold font-mono ${
                      emp.current_score >= 80 ? 'text-emerald-400' : emp.current_score >= 50 ? 'text-amber-500' : 'text-rose-500'
                    }`}>
                      {emp.current_score}/100
                    </span>
                  </div>

                  {/* Tiny progress bar */}
                  <div className="w-full bg-dark-bg rounded-full h-1">
                    <div 
                      className={`h-1 rounded-full ${getScoreProgressClass(emp.current_score)}`}
                      style={{ width: `${emp.current_score}%` }}
                    ></div>
                  </div>
                </button>
              );
            })
          )}
        </div>
      </aside>

      {/* Main Panel: Analysis dashboard */}
      <main className="flex-1 flex flex-col overflow-hidden">
        
        {/* Top Header controls */}
        <header className="p-4 border-b border-dark-border bg-dark-card/30 flex justify-between items-center">
          <div className="flex items-center gap-1 bg-dark-bg/80 p-1 rounded-lg border border-dark-border overflow-x-auto max-w-4xl">
            {(authUser?.role === 'CEO' || authUser?.role === 'Security Manager' || authUser?.role === 'Security Analyst' || authUser?.role === 'HR' || (authUser?.permissions || []).includes('view_dashboard') || (authUser?.permissions || []).includes('view_employees')) && (
              <button
                onClick={() => setActiveTab('threat_console')}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-semibold tracking-wide transition-all cursor-pointer whitespace-nowrap ${
                  activeTab === 'threat_console' 
                    ? 'bg-blue-600 text-white shadow-md' 
                    : 'text-gray-400 hover:text-gray-200 hover:bg-dark-hover/50'
                }`}
              >
                <Activity className="w-3.5 h-3.5" />
                {authUser?.role === 'HR' ? 'Employee Profiles & Trust Scores' : 'Threat Analysis Console'}
              </button>
            )}

            {(authUser?.role === 'CEO' || authUser?.role === 'Security Manager' || (authUser?.permissions || []).includes('generate_jit_tokens')) && (
              <button
                onClick={() => setActiveTab('jit_pam')}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-semibold tracking-wide transition-all cursor-pointer whitespace-nowrap ${
                  activeTab === 'jit_pam' 
                    ? 'bg-blue-600 text-white shadow-md' 
                    : 'text-gray-400 hover:text-gray-200 hover:bg-dark-hover/50'
                }`}
              >
                <Key className="w-3.5 h-3.5" />
                JIT Security Governance
              </button>
            )}

            {(authUser?.role === 'CEO' || authUser?.role === 'Security Manager' || authUser?.role === 'Security Analyst' || (authUser?.permissions || []).includes('sandbox')) && (
              <button
                onClick={() => setActiveTab('sandbox')}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-semibold tracking-wide transition-all cursor-pointer whitespace-nowrap ${
                  activeTab === 'sandbox' 
                    ? 'bg-blue-600 text-white shadow-md' 
                    : 'text-gray-400 hover:text-gray-200 hover:bg-dark-hover/50'
                }`}
              >
                <Box className="w-3.5 h-3.5 text-cyan-400" />
                AI Sandbox Verification
              </button>
            )}

            {(authUser?.role === 'CEO' || authUser?.role === 'Security Manager' || authUser?.role === 'Security Analyst' || (authUser?.permissions || []).includes('identity_monitoring')) && (
              <button
                onClick={() => setActiveTab('human_identity')}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-semibold tracking-wide transition-all cursor-pointer whitespace-nowrap ${
                  activeTab === 'human_identity' 
                    ? 'bg-blue-600 text-white shadow-md' 
                    : 'text-gray-400 hover:text-gray-200 hover:bg-dark-hover/50'
                }`}
              >
                <Fingerprint className="w-3.5 h-3.5 text-emerald-400" />
                Human Identity Monitoring
              </button>
            )}

            {(authUser?.role === 'CEO' || authUser?.role === 'Security Manager' || (authUser?.permissions || []).includes('audit_logs')) && (
              <button
                onClick={() => setActiveTab('audit_logs')}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-semibold tracking-wide transition-all cursor-pointer whitespace-nowrap ${
                  activeTab === 'audit_logs' 
                    ? 'bg-amber-600 text-white shadow-md' 
                    : 'text-gray-400 hover:text-gray-200 hover:bg-dark-hover/50'
                }`}
              >
                <FileText className="w-3.5 h-3.5 text-amber-300" />
                Security Audit Logs
              </button>
            )}
          </div>

          <div className="flex items-center gap-3">
            {/* Active User Identity & Role Badge */}
            {authUser && (
              <div className="flex items-center gap-2 px-3 py-1.5 bg-dark-card border border-dark-border/80 rounded-md text-xs">
                <User className="w-3.5 h-3.5 text-blue-400" />
                <div className="flex flex-col text-left leading-tight">
                  <span className="font-semibold text-gray-200">{authUser.displayName || authUser.email}</span>
                  <span className="text-[10px] text-gray-400">{authUser.department || 'Garuda AI'}</span>
                </div>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                  authUser.role === 'CEO' ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' :
                  authUser.role === 'Security Manager' ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30' :
                  authUser.role === 'HR' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' :
                  'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                }`}>
                  {authUser.role || 'ANALYST'}
                </span>
              </div>
            )}

            {/* CEO Administrative User Management Trigger */}
            {(authUser?.role === 'CEO' || authUser?.role === 'admin') && (
              <button
                onClick={() => setShowUserMgmtModal(true)}
                title="Manage Users & Roles"
                className="flex items-center gap-1.5 text-xs font-semibold py-2 px-3 border border-purple-500/40 bg-purple-500/10 hover:bg-purple-500/20 text-purple-300 rounded-md transition-all cursor-pointer shadow-md"
              >
                <Users className="w-3.5 h-3.5" />
                <span>Users & Roles</span>
              </button>
            )}

            {/* Day / Night Mode Toggle Button */}
            <button
              onClick={toggleTheme}
              title={theme === 'dark' ? 'Switch to Day Mode (Light)' : 'Switch to Night Mode (Dark)'}
              className="flex items-center gap-1.5 text-xs font-semibold py-2 px-3 border border-dark-border hover:bg-dark-hover rounded-md transition-all cursor-pointer text-gray-300"
            >
              {theme === 'dark' ? (
                <>
                  <Sun className="w-3.5 h-3.5 text-amber-400" />
                  <span>Day Mode</span>
                </>
              ) : (
                <>
                  <Moon className="w-3.5 h-3.5 text-indigo-500" />
                  <span>Night Mode</span>
                </>
              )}
            </button>

            {/* Change Password Button */}
            <button
              onClick={() => {
                setShowChangePassModal(true);
                setPassErr('');
                setPassMsg('');
              }}
              title="Change Security Password"
              className="flex items-center gap-1.5 text-xs font-semibold py-2 px-3 border border-blue-500/30 bg-blue-500/10 hover:bg-blue-500/20 text-blue-300 rounded-md transition-all cursor-pointer"
            >
              <KeyRound className="w-3.5 h-3.5" />
              <span>Change Password</span>
            </button>

            {/* Logout Action Button */}
            <button
              onClick={handleLogout}
              title="Sign Out of GarudaAI"
              className="flex items-center gap-1.5 text-xs font-semibold py-2 px-3 border border-rose-500/30 bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 rounded-md transition-all cursor-pointer"
            >
              <LogOut className="w-3.5 h-3.5" />
              Sign Out
            </button>
          </div>
        </header>

        {/* Console Tab Content Split */}
        {activeTab === 'sandbox' ? (
          <SandboxDashboard
            employees={employees}
            selectedEmp={selectedEmp}
            setSelectedEmp={setSelectedEmp}
            criticalThreshold={criticalThreshold}
            onRunSandboxComplete={() => {
              // Refresh employee list and timeline
              if (selectedEmp) {
                fetchEmployeeDetails(selectedEmp.employee_id);
              }
              fetchEmployees();
            }}
          />
        ) : activeTab === 'human_identity' ? (
          <HumanIdentityDashboard
            selectedEmp={selectedEmp}
            onRefreshData={async () => {
              await fetchEmployees();
              await fetchAlerts();
              if (selectedEmp?.employee_id) {
                await fetchEmployeeDetails(selectedEmp.employee_id);
              }
            }}
            onTriggerLock={(empId) => {
              setEmployeeLocks(prev => ({
                ...prev,
                [empId]: {
                  status: 'WARNING',
                  countdown: 30,
                  lockTime: new Date().toLocaleTimeString(),
                  token: null
                }
              }));
            }}
            API_BASE={API_BASE}
          />
        ) : activeTab === 'audit_logs' ? (
          <div className="flex-1 overflow-y-auto p-6">
            <AuditLogsView currentUserToken={localStorage.getItem('garuda_token')} theme={theme} />
          </div>
        ) : activeTab === 'jit_pam' ? (
          <JitPamDashboard 
            selectedEmp={selectedEmp} 
            criticalThreshold={criticalThreshold}
            setCriticalThreshold={setCriticalThreshold}
            employeeLocks={employeeLocks}
            onGenerateToken={handleGenerateJitToken}
            onVerifyToken={handleVerifyJitToken}
            timeline={timeline}
          />
        ) : (
          /* Layout split pane for Threat Analysis */
          <div className="flex-1 flex overflow-hidden">
          
          {/* Left panel: Deep Dive employee info */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            
            {selectedEmp ? (
              <>
                {/* Employee Info Header */}
                <div className="glass p-6 rounded-xl flex flex-col gap-4 glow-card">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-5">
                      <div className="w-14 h-14 bg-dark-hover border border-dark-border rounded-xl flex items-center justify-center text-blue-500 font-mono font-bold text-lg">
                        {selectedEmp.employee_id.slice(0, 3)}
                      </div>
                      <div>
                        <div className="flex items-center gap-2.5">
                          <h2 className="text-2xl font-bold text-white leading-tight">{selectedEmp.full_name}</h2>
                          <span className="text-xs bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2 py-0.5 rounded font-mono font-semibold">
                            {selectedEmp.employee_id}
                          </span>
                          {selectedEmp.is_privileged_user && (
                            <span className="flex items-center gap-1 text-[9px] font-bold text-rose-400 border border-rose-500/30 bg-rose-500/5 px-2 py-0.5 rounded-full uppercase tracking-wider">
                              <ShieldAlert className="w-2.5 h-2.5 text-rose-400 animate-pulse" />
                              Privileged
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-400 font-medium mt-1">
                          {selectedEmp.role} &middot; <span className="text-gray-300 font-semibold">{cleanDept(selectedEmp.functional_unit || selectedEmp.department)}</span> &middot; <span className="text-gray-500">Supervisor: {selectedEmp.supervisor || 'Executive Management'}</span>
                        </p>
                      </div>
                    </div>
                    
                    {/* Trust score badge & AI Investigation / Escalation trigger */}
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => fetchEmployeeInvestigation(selectedEmp.employee_id)}
                        className="flex items-center gap-2 px-3.5 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-lg text-xs font-bold tracking-wide transition-all shadow-md cursor-pointer"
                      >
                        <FileText className="w-4 h-4" />
                        AI Investigation Report
                      </button>

                      {authUser?.role === 'Security Analyst' && (
                        <button
                          onClick={() => {
                            setShowEscalateModal(true);
                            setEscalateSummary(`Analyst investigation notes for ${selectedEmp.full_name} (${selectedEmp.employee_id}). Current Trust Score: ${selectedEmp.current_score}/100.`);
                          }}
                          className="flex items-center gap-1.5 px-3.5 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-xs font-bold tracking-wide transition-all shadow-md cursor-pointer"
                        >
                          <AlertTriangle className="w-4 h-4" />
                          Escalate to Security Manager
                        </button>
                      )}

                      <div className="flex flex-col items-center">
                        <div className={`w-14 h-14 rounded-full border-2 flex items-center justify-center font-mono font-bold text-xl ${getScoreColorClass(selectedEmp.current_score)}`}>
                          {selectedEmp.current_score}
                        </div>
                        <span className="text-[10px] text-gray-500 uppercase tracking-widest mt-1 font-bold">Trust Index</span>
                      </div>
                    </div>
                  </div>

                  {/* Psychometrics & Explainable Score Factors */}
                  <div className="grid grid-cols-12 gap-4 pt-3 border-t border-dark-border/40">
                    {/* Big Five Traits */}
                    <div className="col-span-5 bg-dark-bg/60 p-3 rounded-lg border border-dark-border/40 flex flex-col gap-1.5">
                      <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Big Five Psychometrics (CERT 4.2)</span>
                      <div className="flex items-center gap-2 text-xs font-mono font-semibold text-gray-300">
                        <span className="bg-blue-500/10 text-blue-400 px-1.5 py-0.5 rounded" title="Openness">O: {selectedEmp.psychometrics?.O || 30}</span>
                        <span className="bg-emerald-500/10 text-emerald-400 px-1.5 py-0.5 rounded" title="Conscientiousness">C: {selectedEmp.psychometrics?.C || 30}</span>
                        <span className="bg-purple-500/10 text-purple-400 px-1.5 py-0.5 rounded" title="Extraversion">E: {selectedEmp.psychometrics?.E || 30}</span>
                        <span className="bg-amber-500/10 text-amber-400 px-1.5 py-0.5 rounded" title="Agreeableness">A: {selectedEmp.psychometrics?.A || 30}</span>
                        <span className="bg-rose-500/10 text-rose-400 px-1.5 py-0.5 rounded" title="Neuroticism">N: {selectedEmp.psychometrics?.N || 30}</span>
                      </div>
                    </div>

                    {/* Deterministic Score Reasons */}
                    <div className="col-span-7 bg-dark-bg/60 p-3 rounded-lg border border-dark-border/40 flex flex-col gap-1">
                      <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Score Assignment Factors (Explainable)</span>
                      <div className="text-xs text-gray-300 flex flex-wrap gap-1.5">
                        {selectedEmp.score_reasons && selectedEmp.score_reasons.length > 0 ? (
                          selectedEmp.score_reasons.map((r, i) => (
                            <span key={i} className="bg-dark-card border border-dark-border/60 text-gray-300 px-2 py-0.5 rounded text-[11px]">
                              {r}
                            </span>
                          ))
                        ) : (
                          <span className="text-emerald-400 font-semibold text-[11px]">Clean behavioral baseline (100/100)</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Score Trend & Simulator split grid */}
                <div className="grid grid-cols-12 gap-6">
                  
                  {/* Trend chart */}
                  <div className="col-span-8 glass p-5 rounded-xl flex flex-col gap-3 min-h-[220px]">
                    <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Score Trend History</span>
                    <div className="flex-1 relative">
                      <canvas ref={chartRef}></canvas>
                    </div>
                  </div>

                  {/* Simulator widget */}
                  <div className="col-span-4 glass p-5 rounded-xl flex flex-col gap-4">
                    <span className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1">
                      <Cpu className="w-3.5 h-3.5 text-blue-500" />
                      Attack Simulator
                    </span>
                    <p className="text-xs text-gray-500 leading-normal">Inject a mock threat activity pattern to test behavioral detection rules and AI models.</p>
                    
                    <select
                      className="w-full py-2 px-3 text-xs bg-dark-bg border border-dark-border rounded-md text-gray-300 focus:outline-none focus:border-blue-500 disabled:opacity-50"
                      value={selectedScenario}
                      onChange={e => setSelectedScenario(e.target.value)}
                      disabled={simulating}
                    >
                      <option value="usb_theft">Midnight Login & USB Copy</option>
                      <option value="mass_download">Mass File Download Spike</option>
                      <option value="impossible_travel">Impossible Travel Auth</option>
                      <option value="privilege_escalation">Privilege Escalation Access</option>
                    </select>

                    <button
                      onClick={handleSimulate}
                      disabled={simulating}
                      className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-md text-xs font-semibold tracking-wide transition-all shadow-lg shadow-blue-600/10 cursor-pointer text-center"
                    >
                      {simulating ? 'Injecting Threat...' : 'Inject Simulation Scenario'}
                    </button>
                  </div>
                </div>

                {/* Event timeline */}
                <div className="glass p-6 rounded-xl flex flex-col gap-4">
                  <span className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-blue-500" />
                    Interactive Incident Timeline
                  </span>
                  
                  {loadingTimeline ? (
                    <div className="flex justify-center p-8">
                      <RefreshCw className="w-6 h-6 animate-spin text-blue-500" />
                    </div>
                  ) : timeline.length === 0 ? (
                    <div className="text-center p-8 text-gray-500 text-sm">No activity logs recorded.</div>
                  ) : (
                    <div className="relative border-l border-dark-border/60 ml-3.5 space-y-4">
                      {timeline.map((entry, idx) => {
                        const isAnom = entry.is_anomaly;
                        const isSbx = entry.type === 'sandbox' || entry.is_sandbox || entry.description?.includes('Sandbox') || entry.description?.includes('Observation');
                        const verdict = entry.sandbox_verdict || (entry.description?.includes('Blocked') ? 'MALICIOUS' : entry.description?.includes('Observation') ? 'SUSPICIOUS' : 'SAFE');

                        // Determine colors for Sandbox events
                        let bulletColor = isAnom 
                          ? entry.severity === 'Critical' ? 'border-fuchsia-500 text-fuchsia-500' : entry.severity === 'High' ? 'border-red-500 text-red-500' : 'border-amber-500 text-amber-500'
                          : 'border-dark-border text-gray-400';
                        
                        let cardColor = isAnom 
                          ? entry.severity === 'Critical' ? 'bg-fuchsia-500/5 border-fuchsia-500/20' : entry.severity === 'High' ? 'bg-red-500/5 border-red-500/20' : 'bg-amber-500/5 border-amber-500/20'
                          : 'bg-dark-card/30 border-dark-border/20 hover:border-dark-border/40';

                        if (isSbx) {
                          if (verdict === 'SAFE') {
                            bulletColor = 'border-emerald-500 text-emerald-400';
                            cardColor = 'bg-emerald-500/10 border-emerald-500/30';
                          } else if (verdict === 'SUSPICIOUS') {
                            bulletColor = 'border-orange-500 text-orange-400';
                            cardColor = 'bg-orange-500/10 border-orange-500/30';
                          } else {
                            bulletColor = 'border-red-500 text-red-500';
                            cardColor = 'bg-red-500/10 border-red-500/30';
                          }
                        }

                        return (
                          <div key={idx} className="relative pl-6">
                            
                            {/* Chronological bullet icon */}
                            <div className={`absolute -left-[13px] top-1 p-1 rounded-full border bg-dark-card flex items-center justify-center ${bulletColor}`}>
                              {getTimelineIcon(entry.type)}
                            </div>

                            {/* Log item details */}
                            <div className={`p-3 rounded-lg border text-sm transition-all ${cardColor}`}>
                              <div className="flex justify-between items-start gap-3">
                                <span className={`font-semibold ${isAnom || isSbx ? 'text-white' : 'text-gray-300'}`}>
                                  {entry.description}
                                </span>
                                <div className="flex items-center gap-2">
                                  <span className="text-[10px] bg-dark-bg/60 text-blue-400 px-1.5 py-0.5 rounded font-mono border border-dark-border/40">
                                    {entry.source_dataset || `${entry.type}.csv`}
                                  </span>
                                  <span className="text-[10px] text-gray-500 font-mono whitespace-nowrap">{entry.timestamp}</span>
                                </div>
                              </div>
                              
                              {/* Sandbox Badge or Anomaly Alert Badge */}
                              {isSbx ? (
                                <div className="mt-2 flex items-center gap-2">
                                  <span className={`text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border ${
                                    verdict === 'SAFE'
                                      ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                                      : verdict === 'SUSPICIOUS'
                                        ? 'bg-orange-500/20 text-orange-300 border-orange-500/40'
                                        : 'bg-red-500/20 text-red-400 border-red-500/40'
                                  }`}>
                                    {verdict === 'SAFE' ? 'Green = Safe (Sandbox Passed)' : verdict === 'SUSPICIOUS' ? 'Orange = Suspicious (Under Observation)' : 'Red = Blocked (Sandbox Blocked Action)'}
                                  </span>
                                </div>
                              ) : isAnom ? (
                                <div className="mt-2 flex items-center gap-2">
                                  <span className={`text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                                    entry.severity === 'Critical' ? 'bg-fuchsia-500/10 text-fuchsia-400' : entry.severity === 'High' ? 'bg-red-500/10 text-red-400' : 'bg-amber-500/10 text-amber-400'
                                  }`}>
                                    {entry.severity} Alert
                                  </span>
                                </div>
                              ) : null}
                            </div>

                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="flex flex-col items-center justify-center h-96 text-gray-500">
                <Users className="w-16 h-16 text-gray-600 mb-3" />
                <p>Select an employee from the sidebar to inspect behavioral data.</p>
              </div>
            )}
          </div>

          {/* Right panel: AI Command Center (Investigate + chat) */}
          <div className="w-[450px] border-l border-dark-border bg-dark-card/30 flex flex-col">
            
            {/* Split panel selectors */}
            <div className="border-b border-dark-border flex">
              <button className="flex-1 py-3 text-xs font-bold text-center tracking-wider border-b-2 border-blue-500 text-white bg-dark-card/50 flex items-center justify-center gap-1.5">
                <Brain className="w-4 h-4 text-blue-500" />
                AI INVESTIGATION
              </button>
            </div>

            {/* Split content container */}
            <div className="flex-1 flex flex-col overflow-hidden">
              
              {/* Top half: Investigation documentation report */}
              <div className="flex-1 overflow-y-auto p-5 border-b border-dark-border space-y-4">

                {loadingReport ? (
                  <div className="flex flex-col items-center justify-center h-48 gap-2">
                    <RefreshCw className="w-6 h-6 animate-spin text-blue-500" />
                    <span className="text-xs text-gray-500">Querying Gemini security models...</span>
                  </div>
                ) : aiReport ? (
                  <div className="prose prose-invert text-xs max-w-none text-gray-300 space-y-3 font-sans leading-relaxed">
                    {/* Render investigation narrative */}
                    {aiReport.split('\n').map((line, i) => {
                      if (line.startsWith('### ')) {
                        return <h3 key={i} className="text-sm font-bold text-white mt-4 border-b border-dark-border/40 pb-1">{line.replace('### ', '')}</h3>;
                      }
                      if (line.startsWith('- **')) {
                        const parts = line.replace('- **', '').split('**');
                        return (
                          <div key={i} className="flex gap-2 pl-2">
                            <span className="text-blue-500 font-bold">&bull;</span>
                            <span><strong>{parts[0]}</strong>{parts.slice(1).join('')}</span>
                          </div>
                        );
                      }
                      if (line.startsWith('1. ') || line.startsWith('2. ') || line.startsWith('3. ') || line.startsWith('4. ')) {
                        return <div key={i} className="pl-4 font-semibold text-gray-200 mt-1">{line}</div>;
                      }
                      return <p key={i}>{line}</p>;
                    })}
                  </div>
                ) : (
                  <div className="text-center p-8 text-gray-500 text-xs">No active alerts selected for AI generation.</div>
                )}
              </div>

              {/* Bottom half: Command Chat widget */}
              <div className="h-[300px] flex flex-col bg-dark-bg/60">
                <div className="p-3 border-b border-dark-border/60 bg-dark-card/80 flex items-center justify-between">
                  <span className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
                    <img src="/garuda-logo.png" alt="Garuda AI" className="w-4 h-4 object-contain shrink-0" />
                    Garuda AI Security Command Chat
                  </span>
                </div>

                {/* Messages container */}
                <div className="flex-1 overflow-y-auto p-4 space-y-3">
                  {chatHistory.map((chat, idx) => (
                    <div key={idx} className={`flex ${chat.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`p-2.5 rounded-lg max-w-[85%] text-xs leading-normal ${
                        chat.role === 'user' 
                          ? 'bg-blue-600 text-white rounded-br-none shadow-md' 
                          : 'bg-dark-card border border-dark-border text-gray-300 rounded-bl-none'
                      }`}>
                        {/* Splitting simple markdown text inside chat messages */}
                        {chat.text.split('\n').map((para, pIdx) => (
                          <p key={pIdx} className={pIdx > 0 ? 'mt-1.5' : ''}>
                            {para.split('**').map((part, partIdx) => 
                              partIdx % 2 === 1 ? <strong key={partIdx} className="text-white">{part}</strong> : part
                            )}
                          </p>
                        ))}
                      </div>
                    </div>
                  ))}
                  {sendingChat && (
                    <div className="flex justify-start">
                      <div className="bg-dark-card border border-dark-border p-2.5 rounded-lg rounded-bl-none text-xs text-gray-500 flex items-center gap-1.5">
                        <RefreshCw className="w-3 h-3 animate-spin text-blue-500" />
                        Analyzing query...
                      </div>
                    </div>
                  )}
                  <div ref={chatBottomRef}></div>
                </div>

                {/* Chat input box */}
                <form onSubmit={handleSendChat} className="p-3 border-t border-dark-border bg-dark-card/60 flex gap-2">
                  <input
                    type="text"
                    placeholder="Ask assistant (e.g., 'who has score below 40?')"
                    className="flex-1 py-1.5 px-3 text-xs bg-dark-bg border border-dark-border rounded-md text-gray-200 focus:outline-none focus:border-blue-500"
                    value={chatMessage}
                    onChange={e => setChatMessage(e.target.value)}
                    disabled={sendingChat}
                  />
                  <button
                    type="submit"
                    className="p-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-md transition-all flex items-center justify-center cursor-pointer"
                    disabled={sendingChat || !chatMessage.trim()}
                  >
                    <Send className="w-3.5 h-3.5" />
                  </button>
                </form>
              </div>

            </div>

          </div>

          </div>
        )}

      </main>

      {/* Change Password Modal Overlay */}
      {showChangePassModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 animate-fadeIn">
          <div className="w-full max-w-sm glass rounded-xl border border-dark-border p-6 shadow-2xl relative">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400">
                <KeyRound className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Change Security Password</h3>
                <p className="text-[11px] text-gray-400">Protected with ML-KEM-768 Post-Quantum Encryption</p>
              </div>
            </div>

            {passMsg ? (
              <div className="py-4 text-center space-y-3">
                <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto animate-bounce" />
                <p className="text-xs text-gray-200 leading-relaxed">{passMsg}</p>
              </div>
            ) : (
              <form onSubmit={handleChangePasswordSubmit} className="space-y-3.5">
                {passErr && (
                  <div className="p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
                    <span>{passErr}</span>
                  </div>
                )}

                <div>
                  <label className="block text-[11px] font-semibold text-gray-300 uppercase tracking-wider mb-1">
                    Current Password
                  </label>
                  <input
                    type="password"
                    required
                    placeholder="••••••••••••"
                    value={currPass}
                    onChange={e => setCurrPass(e.target.value)}
                    className="w-full px-3 py-2 text-xs bg-dark-bg border border-dark-border rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-gray-300 uppercase tracking-wider mb-1">
                    New Password
                  </label>
                  <input
                    type="password"
                    required
                    placeholder="••••••••••••"
                    value={newPass}
                    onChange={e => setNewPass(e.target.value)}
                    className="w-full px-3 py-2 text-xs bg-dark-bg border border-dark-border rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-gray-300 uppercase tracking-wider mb-1">
                    Confirm New Password
                  </label>
                  <input
                    type="password"
                    required
                    placeholder="••••••••••••"
                    value={confirmPass}
                    onChange={e => setConfirmPass(e.target.value)}
                    className="w-full px-3 py-2 text-xs bg-dark-bg border border-dark-border rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div className="flex gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowChangePassModal(false)}
                    className="flex-1 py-2 bg-dark-hover border border-dark-border text-gray-300 text-xs rounded-lg font-medium cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={passLoading}
                    className="flex-1 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded-lg font-bold cursor-pointer disabled:opacity-50 flex items-center justify-center gap-1.5"
                  >
                    {passLoading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : 'Update Password'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* CEO Administrative User & Role Management Modal */}
      <RbacUserManagementModal
        isOpen={showUserMgmtModal}
        onClose={() => setShowUserMgmtModal(false)}
        currentUserToken={localStorage.getItem('garuda_token')}
        theme={theme}
      />

      {/* Analyst Investigation Escalation Modal */}
      {showEscalateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg bg-slate-900 border border-slate-700 rounded-2xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Escalate Investigation Report</h3>
                <p className="text-xs text-gray-400">Security Analyst Escalation Workflow to Security Manager</p>
              </div>
            </div>

            {escalateMsg ? (
              <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs rounded-xl flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 shrink-0" />
                <span>{escalateMsg}</span>
              </div>
            ) : (
              <form onSubmit={async (e) => {
                e.preventDefault();
                setEscalateLoading(true);
                try {
                  const res = await fetch(`${API_BASE}/rbac/escalate-investigation`, {
                    method: 'POST',
                    headers: {
                      'Content-Type': 'application/json',
                      'Authorization': `Bearer ${localStorage.getItem('garuda_token') || ''}`
                    },
                    body: JSON.stringify({
                      employee_id: selectedEmp?.employee_id,
                      title: `Analyst Escalation for ${selectedEmp?.full_name} (${selectedEmp?.employee_id})`,
                      summary: escalateSummary,
                      threat_level: escalateThreatLevel
                    })
                  });
                  const data = await res.json();
                  if (res.ok && data.success) {
                    setEscalateMsg(`Investigation report escalated to Security Manager (Report ID: ${data.report?.report_id})`);
                    setTimeout(() => {
                      setShowEscalateModal(false);
                      setEscalateMsg('');
                      setEscalateSummary('');
                    }, 2000);
                  } else {
                    alert(data.message || data.error || 'Failed to escalate report.');
                  }
                } catch (err) {
                  alert('Backend server connection error.');
                } finally {
                  setEscalateLoading(false);
                }
              }} className="space-y-4">
                <div>
                  <label className="text-xs font-semibold text-gray-300">Target Employee</label>
                  <input
                    type="text"
                    disabled
                    value={`${selectedEmp?.full_name || ''} (${selectedEmp?.employee_id || ''})`}
                    className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-gray-400"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-gray-300">Threat Severity</label>
                  <select
                    value={escalateThreatLevel}
                    onChange={(e) => setEscalateThreatLevel(e.target.value)}
                    className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-amber-300 font-semibold outline-none"
                  >
                    <option value="Critical">Critical Severity</option>
                    <option value="High">High Severity</option>
                    <option value="Medium">Medium Severity</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-gray-300">Investigation Notes & Evidence Summary *</label>
                  <textarea
                    required
                    rows={4}
                    placeholder="Document anomalous telemetry, file exfiltration patterns, or suspicious logon events..."
                    value={escalateSummary}
                    onChange={(e) => setEscalateSummary(e.target.value)}
                    className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-gray-200 outline-none focus:border-amber-500"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowEscalateModal(false)}
                    className="px-4 py-2 bg-slate-800 text-gray-300 text-xs rounded-lg cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={escalateLoading}
                    className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold rounded-lg cursor-pointer flex items-center gap-1.5"
                  >
                    {escalateLoading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : 'Escalate to Security Manager'}
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
