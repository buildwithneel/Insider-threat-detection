import React, { useState, useEffect, useRef } from 'react';
import { 
  Fingerprint, UserCheck, Bot, Cpu, Activity, ShieldAlert, ShieldCheck, 
  AlertTriangle, TrendingUp, Zap, Clock, Terminal, MousePointer, Keyboard, 
  RefreshCw, Play, Lock, CheckCircle2, Info, Box, AlertCircle, ArrowUpRight, ArrowDownRight
} from 'lucide-react';
import { Chart } from 'chart.js/auto';

export default function HumanIdentityDashboard({ 
  selectedEmp, 
  onRefreshData,
  onTriggerLock,
  API_BASE = 'http://localhost:5000/api'
}) {
  const [identityRecord, setIdentityRecord] = useState(null);
  const [loading, setLoading] = useState(false);
  const [simulating, setSimulating] = useState(false);
  const [activeProfile, setActiveProfile] = useState('human_normal');
  const [timelineEvents, setTimelineEvents] = useState([]);
  const [errorMsg, setErrorMsg] = useState('');

  const chartRef = useRef(null);
  const chartInstance = useRef(null);

  // Fetch identity data for selected employee
  const fetchIdentityStatus = async (empId) => {
    if (!empId) return;
    setLoading(true);
    setErrorMsg('');
    try {
      const headers = {};
      const token = localStorage.getItem('garuda_token');
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch(`${API_BASE}/employees/${empId}/identity-status`, { headers });
      const data = await res.json();
      if (data.success && data.record) {
        setIdentityRecord(data.record);
      }

      // Fetch employee timeline for identity timeline display
      const tRes = await fetch(`${API_BASE}/employees/${empId}/timeline`, { headers });
      const tData = await tRes.json();
      if (Array.isArray(tData)) {
        setTimelineEvents(tData.filter(e => 
          ['identity_verified', 'behaviour_changed', 'automation_detected', 'trust_reduced', 'sandbox'].includes(e.type) ||
          e.description.toLowerCase().includes('identity') ||
          e.description.toLowerCase().includes('automation') ||
          e.description.toLowerCase().includes('behaviour')
        ));
      }
    } catch (e) {
      console.error('Failed to fetch identity status:', e);
      setErrorMsg('Failed to load identity telemetry data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedEmp?.employee_id) {
      fetchIdentityStatus(selectedEmp.employee_id);
    }
  }, [selectedEmp?.employee_id]);

  // Render Human Confidence vs Machine Confidence Chart
  useEffect(() => {
    if (!chartRef.current || !identityRecord?.history) return;

    if (chartInstance.current) {
      chartInstance.current.destroy();
    }

    const ctx = chartRef.current.getContext('2d');
    const labels = identityRecord.history.map(h => h.time);
    const humanData = identityRecord.history.map(h => h.human_confidence);
    const machineData = identityRecord.history.map(h => h.machine_confidence);

    chartInstance.current = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Human Confidence %',
            data: humanData,
            borderColor: '#10b981',
            backgroundColor: 'rgba(16, 185, 129, 0.12)',
            fill: true,
            tension: 0.35,
            borderWidth: 2.5,
            pointRadius: 4,
            pointBackgroundColor: '#10b981'
          },
          {
            label: 'Machine Confidence %',
            data: machineData,
            borderColor: '#ef4444',
            backgroundColor: 'rgba(239, 68, 68, 0.12)',
            fill: true,
            tension: 0.35,
            borderWidth: 2.5,
            pointRadius: 4,
            pointBackgroundColor: '#ef4444'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
            labels: {
              color: '#9ca3af',
              font: { size: 12, weight: 'bold' },
              usePointStyle: true,
              padding: 16
            }
          },
          tooltip: {
            mode: 'index',
            intersect: false,
            backgroundColor: '#1e293b',
            titleColor: '#f3f4f6',
            bodyColor: '#e2e8f0',
            borderColor: '#334155',
            borderWidth: 1
          }
        },
        scales: {
          x: {
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: '#9ca3af', font: { size: 11 } }
          },
          y: {
            min: 0,
            max: 100,
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { 
              color: '#9ca3af', 
              font: { size: 11 },
              callback: (val) => `${val}%`
            }
          }
        }
      }
    });

    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, [identityRecord?.history]);

  // Handle identity scenario simulation
  const handleSimulateProfile = async (profileId) => {
    if (!selectedEmp?.employee_id) return;
    setSimulating(true);
    setActiveProfile(profileId);
    try {
      const headers = { 'Content-Type': 'application/json' };
      const token = localStorage.getItem('garuda_token');
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch(`${API_BASE}/employees/${selectedEmp.employee_id}/identity-simulate`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ profile_id: profileId })
      });
      const data = await res.json();

      if (data.success && data.record) {
        setIdentityRecord(data.record);
        
        // If automation detected, trigger employee lock callback if provided
        if (data.employee_locked && onTriggerLock) {
          onTriggerLock(selectedEmp.employee_id);
        }

        if (onRefreshData) {
          await onRefreshData();
        }
        await fetchIdentityStatus(selectedEmp.employee_id);
      }
    } catch (e) {
      console.error('Simulation failed:', e);
    } finally {
      setSimulating(false);
    }
  };

  if (!selectedEmp) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-gray-500">
        <Fingerprint className="w-16 h-16 text-gray-600 mb-4 animate-pulse" />
        <h3 className="text-lg font-bold text-gray-300">Select an Employee to View Identity Telemetry</h3>
        <p className="text-sm max-w-md mt-1">Select an employee from the left panel to analyze typing dynamics, cursor physics, API frequencies, and AI Human–Machine identity confidence ratings.</p>
      </div>
    );
  }

  const scores = identityRecord?.scores || {
    human_confidence: 95.0,
    machine_confidence: 5.0,
    bot_probability: 2.0,
    behaviour_consistency: 94.0,
    overall_identity_score: 95.0,
    status: 'Verified Human',
    decision: 'Normal Behaviour - No Action Required'
  };

  const telemetry = identityRecord?.telemetry || {
    typing_behaviour: { wpm: 68, hold_time_ms: 110, variance: 24.5, robotic_cadence: false },
    mouse_movement: { path_type: 'Bezier Curve', micro_jitters: 18, straight_line_ratio: 0.08 },
    cursor_speed: { avg_px_ms: 1.2, max_burst_px: 4.5, acceleration_curve: 'Organic' },
    keyboard_rhythm: { flight_time_stdev: 42.1, burst_typing: true, fixed_latency: false },
    click_interval: { avg_ms: 340, min_ms: 120, integer_delay_flag: false },
    api_frequency: { requests_per_sec: 1.4, max_burst: 4, is_periodic: false },
    powershell_frequency: { execs_per_min: 0, headless_cli: false },
    browser_behaviour: { headless: false, webdriver_flag: false, synthetic_clicks: false },
    session_timing: { uninterrupted_hours: 3.5, after_hours: false },
    request_pattern: { type: 'Navigational Flow', batch_payload: false },
    idle_time: { avg_pause_sec: 14.2, zero_idle_duration_min: 0 },
    automation_indicators: { signatures_detected: [] }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'Verified Human':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
            <UserCheck className="w-4 h-4" />
            Verified Human
          </span>
        );
      case 'Suspicious Behaviour':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">
            <AlertTriangle className="w-4 h-4" />
            Suspicious Behaviour
          </span>
        );
      case 'Automation Detected':
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30 animate-pulse">
            <Bot className="w-4 h-4" />
            Automation Detected
          </span>
        );
    }
  };

  return (
    <div className="flex-1 flex flex-col overflow-y-auto p-6 space-y-6">
      
      {/* Header Banner */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center p-5 bg-dark-card rounded-xl border border-dark-border shadow-lg gap-4">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-blue-600/20 rounded-xl border border-blue-500/30 text-blue-400">
            <Fingerprint className="w-8 h-8" />
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-bold text-white tracking-wide">{selectedEmp.full_name}</h2>
              <span className="text-xs bg-dark-bg text-gray-400 px-2 py-0.5 rounded font-mono border border-dark-border">
                {selectedEmp.employee_id}
              </span>
              {getStatusBadge(scores.status)}
            </div>
            <p className="text-xs text-gray-400 mt-1">
              AI-Powered Human–Machine Identity Monitoring • Active Telemetry Vector Engine
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => fetchIdentityStatus(selectedEmp.employee_id)}
            disabled={loading}
            className="flex items-center gap-2 px-3.5 py-2 bg-dark-bg hover:bg-dark-hover text-gray-300 rounded-lg border border-dark-border text-xs font-semibold transition cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh Telemetry
          </button>
        </div>
      </div>

      {/* KPI Scores Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        
        {/* Human Confidence */}
        <div className="p-4 bg-dark-card rounded-xl border border-dark-border flex flex-col justify-between relative overflow-hidden">
          <div className="flex justify-between items-start">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Human Confidence</span>
            <UserCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-3">
            <div className="text-3xl font-extrabold text-emerald-400 font-mono">
              {scores.human_confidence}%
            </div>
            <div className="w-full bg-dark-bg rounded-full h-1.5 mt-2">
              <div 
                className="bg-emerald-500 h-1.5 rounded-full transition-all duration-500" 
                style={{ width: `${scores.human_confidence}%` }}
              ></div>
            </div>
          </div>
          <span className="text-[10px] text-gray-500 mt-2 font-medium">Organic typing & mouse rhythm</span>
        </div>

        {/* Machine Confidence */}
        <div className="p-4 bg-dark-card rounded-xl border border-dark-border flex flex-col justify-between">
          <div className="flex justify-between items-start">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Machine Confidence</span>
            <Bot className="w-4 h-4 text-rose-400" />
          </div>
          <div className="mt-3">
            <div className="text-3xl font-extrabold text-rose-400 font-mono">
              {scores.machine_confidence}%
            </div>
            <div className="w-full bg-dark-bg rounded-full h-1.5 mt-2">
              <div 
                className="bg-rose-500 h-1.5 rounded-full transition-all duration-500" 
                style={{ width: `${scores.machine_confidence}%` }}
              ></div>
            </div>
          </div>
          <span className="text-[10px] text-gray-500 mt-2 font-medium">Automated script execution ratio</span>
        </div>

        {/* Bot Probability */}
        <div className="p-4 bg-dark-card rounded-xl border border-dark-border flex flex-col justify-between">
          <div className="flex justify-between items-start">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Bot Probability</span>
            <Cpu className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-3">
            <div className="text-3xl font-extrabold text-amber-400 font-mono">
              {scores.bot_probability}%
            </div>
            <div className="w-full bg-dark-bg rounded-full h-1.5 mt-2">
              <div 
                className="bg-amber-500 h-1.5 rounded-full transition-all duration-500" 
                style={{ width: `${scores.bot_probability}%` }}
              ></div>
            </div>
          </div>
          <span className="text-[10px] text-gray-500 mt-2 font-medium">Selenium / Puppeteer signature match</span>
        </div>

        {/* Behaviour Consistency */}
        <div className="p-4 bg-dark-card rounded-xl border border-dark-border flex flex-col justify-between">
          <div className="flex justify-between items-start">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Consistency</span>
            <Activity className="w-4 h-4 text-blue-400" />
          </div>
          <div className="mt-3">
            <div className="text-3xl font-extrabold text-blue-400 font-mono">
              {scores.behaviour_consistency}%
            </div>
            <div className="w-full bg-dark-bg rounded-full h-1.5 mt-2">
              <div 
                className="bg-blue-500 h-1.5 rounded-full transition-all duration-500" 
                style={{ width: `${scores.behaviour_consistency}%` }}
              ></div>
            </div>
          </div>
          <span className="text-[10px] text-gray-500 mt-2 font-medium">Historical baseline alignment</span>
        </div>

        {/* Overall Identity Score */}
        <div className="p-4 bg-dark-card rounded-xl border border-dark-border flex flex-col justify-between">
          <div className="flex justify-between items-start">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Identity Health</span>
            <ShieldCheck className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="mt-3">
            <div className="text-3xl font-extrabold text-cyan-400 font-mono">
              {scores.overall_identity_score}/100
            </div>
            <div className="w-full bg-dark-bg rounded-full h-1.5 mt-2">
              <div 
                className="bg-cyan-500 h-1.5 rounded-full transition-all duration-500" 
                style={{ width: `${scores.overall_identity_score}%` }}
              ></div>
            </div>
          </div>
          <span className="text-[10px] text-gray-500 mt-2 font-medium">Weighted identity confidence index</span>
        </div>

      </div>

      {/* Main Analysis Section: Graph + Simulation Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Behavior Graph (2 Columns) */}
        <div className="lg:col-span-2 bg-dark-card p-5 rounded-xl border border-dark-border flex flex-col">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3 className="text-sm font-bold text-gray-200 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-blue-400" />
                Human Confidence vs Machine Confidence Over Time
              </h3>
              <p className="text-xs text-gray-400 mt-0.5">Real-time behavioral telemetry trajectory monitoring</p>
            </div>
            <div className="flex items-center gap-3 text-xs">
              <span className="flex items-center gap-1.5 text-emerald-400 font-semibold">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span> Human
              </span>
              <span className="flex items-center gap-1.5 text-rose-400 font-semibold">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span> Machine
              </span>
            </div>
          </div>

          <div className="h-64 w-full relative">
            <canvas ref={chartRef}></canvas>
          </div>
        </div>

        {/* Live Simulation Controls & Decision Engine Box (1 Column) */}
        <div className="bg-dark-card p-5 rounded-xl border border-dark-border flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-gray-200 flex items-center gap-2 mb-1">
              <Zap className="w-4 h-4 text-amber-400" />
              Identity Telemetry Simulator
            </h3>
            <p className="text-xs text-gray-400 mb-4">Inject simulated behavioral profiles to test real-time Decision Engine responses.</p>

            <div className="space-y-2">
              <button
                onClick={() => handleSimulateProfile('human_normal')}
                disabled={simulating}
                className={`w-full text-left p-3 rounded-lg border transition cursor-pointer flex justify-between items-center ${
                  activeProfile === 'human_normal' 
                    ? 'bg-emerald-950/40 border-emerald-500/50 text-emerald-300' 
                    : 'bg-dark-bg border-dark-border hover:bg-dark-hover text-gray-300'
                }`}
              >
                <div>
                  <div className="font-semibold text-xs flex items-center gap-2">
                    <UserCheck className="w-3.5 h-3.5 text-emerald-400" />
                    Standard Human Desktop
                  </div>
                  <div className="text-[10px] text-gray-400 mt-0.5">Natural typing variance & Bezier curves</div>
                </div>
                <span className="text-[10px] bg-emerald-500/20 text-emerald-400 font-mono px-2 py-0.5 rounded">
                  Human 96%
                </span>
              </button>

              <button
                onClick={() => handleSimulateProfile('python_script')}
                disabled={simulating}
                className={`w-full text-left p-3 rounded-lg border transition cursor-pointer flex justify-between items-center ${
                  activeProfile === 'python_script' 
                    ? 'bg-rose-950/40 border-rose-500/50 text-rose-300' 
                    : 'bg-dark-bg border-dark-border hover:bg-dark-hover text-gray-300'
                }`}
              >
                <div>
                  <div className="font-semibold text-xs flex items-center gap-2">
                    <Bot className="w-3.5 h-3.5 text-rose-400" />
                    Automated Python Script
                  </div>
                  <div className="text-[10px] text-gray-400 mt-0.5">Sub-ms API calls & disembodied input</div>
                </div>
                <span className="text-[10px] bg-rose-500/20 text-rose-400 font-mono px-2 py-0.5 rounded">
                  Machine 86%
                </span>
              </button>

              <button
                onClick={() => handleSimulateProfile('headless_bot')}
                disabled={simulating}
                className={`w-full text-left p-3 rounded-lg border transition cursor-pointer flex justify-between items-center ${
                  activeProfile === 'headless_bot' 
                    ? 'bg-rose-950/40 border-rose-500/50 text-rose-300' 
                    : 'bg-dark-bg border-dark-border hover:bg-dark-hover text-gray-300'
                }`}
              >
                <div>
                  <div className="font-semibold text-xs flex items-center gap-2">
                    <Cpu className="w-3.5 h-3.5 text-rose-400" />
                    Headless Crawler Bot
                  </div>
                  <div className="text-[10px] text-gray-400 mt-0.5">Selenium / Puppeteer WebDriver flags</div>
                </div>
                <span className="text-[10px] bg-rose-500/20 text-rose-400 font-mono px-2 py-0.5 rounded">
                  Machine 92%
                </span>
              </button>

              <button
                onClick={() => handleSimulateProfile('ai_agent_autopilot')}
                disabled={simulating}
                className={`w-full text-left p-3 rounded-lg border transition cursor-pointer flex justify-between items-center ${
                  activeProfile === 'ai_agent_autopilot' 
                    ? 'bg-purple-950/40 border-purple-500/50 text-purple-300' 
                    : 'bg-dark-bg border-dark-border hover:bg-dark-hover text-gray-300'
                }`}
              >
                <div>
                  <div className="font-semibold text-xs flex items-center gap-2">
                    <Terminal className="w-3.5 h-3.5 text-purple-400" />
                    AI Agent Auto-Pilot Session
                  </div>
                  <div className="text-[10px] text-gray-400 mt-0.5">Sequential shell loops & quantized steps</div>
                </div>
                <span className="text-[10px] bg-purple-500/20 text-purple-400 font-mono px-2 py-0.5 rounded">
                  Machine 72%
                </span>
              </button>

              <button
                onClick={() => handleSimulateProfile('compromised_session')}
                disabled={simulating}
                className={`w-full text-left p-3 rounded-lg border transition cursor-pointer flex justify-between items-center ${
                  activeProfile === 'compromised_session' 
                    ? 'bg-amber-950/40 border-amber-500/50 text-amber-300' 
                    : 'bg-dark-bg border-dark-border hover:bg-dark-hover text-gray-300'
                }`}
              >
                <div>
                  <div className="font-semibold text-xs flex items-center gap-2">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                    Compromised Session Hijack
                  </div>
                  <div className="text-[10px] text-gray-400 mt-0.5">Drastic rhythm change & high PowerShell rate</div>
                </div>
                <span className="text-[10px] bg-amber-500/20 text-amber-400 font-mono px-2 py-0.5 rounded">
                  Suspicious 54%
                </span>
              </button>
            </div>
          </div>

          <div className="mt-4 p-3 bg-dark-bg rounded-lg border border-dark-border text-xs">
            <span className="font-bold text-gray-300 uppercase tracking-wider block mb-1">Decision Engine Verdict:</span>
            <p className="text-gray-400">{scores.decision}</p>
          </div>
        </div>

      </div>

      {/* Detailed Analysis Panels: Typing & Mouse Telemetry Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Typing Analysis Card */}
        <div className="bg-dark-card p-5 rounded-xl border border-dark-border flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-sm font-bold text-gray-200 flex items-center gap-2">
                <Keyboard className="w-4 h-4 text-blue-400" />
                Typing Behaviour & Rhythm Analysis
              </h3>
              <span className="text-xs text-gray-400 font-mono">Telemetry Vector #1</span>
            </div>

            <div className="grid grid-cols-2 gap-3 mb-4">
              <div className="p-3 bg-dark-bg rounded-lg border border-dark-border">
                <span className="text-[10px] text-gray-400 uppercase tracking-wider">Typing Speed (WPM)</span>
                <div className="text-xl font-bold font-mono text-white mt-1">
                  {telemetry.typing_behaviour.wpm} <span className="text-xs text-gray-500 font-normal">WPM</span>
                </div>
              </div>

              <div className="p-3 bg-dark-bg rounded-lg border border-dark-border">
                <span className="text-[10px] text-gray-400 uppercase tracking-wider">Key Hold Duration</span>
                <div className="text-xl font-bold font-mono text-white mt-1">
                  {telemetry.typing_behaviour.hold_time_ms} <span className="text-xs text-gray-500 font-normal">ms</span>
                </div>
              </div>

              <div className="p-3 bg-dark-bg rounded-lg border border-dark-border">
                <span className="text-[10px] text-gray-400 uppercase tracking-wider">Rhythm Variance</span>
                <div className="text-xl font-bold font-mono text-white mt-1">
                  ±{telemetry.typing_behaviour.variance} <span className="text-xs text-gray-500 font-normal">stdev</span>
                </div>
              </div>

              <div className="p-3 bg-dark-bg rounded-lg border border-dark-border">
                <span className="text-[10px] text-gray-400 uppercase tracking-wider">Flight Time Variance</span>
                <div className="text-xl font-bold font-mono text-white mt-1">
                  {telemetry.keyboard_rhythm.flight_time_stdev} <span className="text-xs text-gray-500 font-normal">ms</span>
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-between items-center p-3 bg-dark-bg/60 rounded-lg border border-dark-border text-xs">
            <span className="text-gray-400">Robotic Rhythm Pattern:</span>
            <span className={`font-bold font-mono px-2 py-0.5 rounded ${
              telemetry.typing_behaviour.robotic_cadence 
                ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' 
                : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
            }`}>
              {telemetry.typing_behaviour.robotic_cadence ? 'DETECTED (Synthetic Input)' : 'NORMAL (Human Cadence)'}
            </span>
          </div>
        </div>

        {/* Mouse & Cursor Physics Analysis Card */}
        <div className="bg-dark-card p-5 rounded-xl border border-dark-border flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-sm font-bold text-gray-200 flex items-center gap-2">
                <MousePointer className="w-4 h-4 text-purple-400" />
                Mouse Movement & Physics Analysis
              </h3>
              <span className="text-xs text-gray-400 font-mono">Telemetry Vector #2</span>
            </div>

            <div className="grid grid-cols-2 gap-3 mb-4">
              <div className="p-3 bg-dark-bg rounded-lg border border-dark-border">
                <span className="text-[10px] text-gray-400 uppercase tracking-wider">Trajectory Path Type</span>
                <div className="text-sm font-bold text-white mt-1 truncate font-mono">
                  {telemetry.mouse_movement.path_type}
                </div>
              </div>

              <div className="p-3 bg-dark-bg rounded-lg border border-dark-border">
                <span className="text-[10px] text-gray-400 uppercase tracking-wider">Micro-Jitter Count</span>
                <div className="text-xl font-bold font-mono text-white mt-1">
                  {telemetry.mouse_movement.micro_jitters} <span className="text-xs text-gray-500 font-normal">pts</span>
                </div>
              </div>

              <div className="p-3 bg-dark-bg rounded-lg border border-dark-border">
                <span className="text-[10px] text-gray-400 uppercase tracking-wider">Avg Cursor Speed</span>
                <div className="text-xl font-bold font-mono text-white mt-1">
                  {telemetry.cursor_speed.avg_px_ms} <span className="text-xs text-gray-500 font-normal">px/ms</span>
                </div>
              </div>

              <div className="p-3 bg-dark-bg rounded-lg border border-dark-border">
                <span className="text-[10px] text-gray-400 uppercase tracking-wider">Click Interval</span>
                <div className="text-xl font-bold font-mono text-white mt-1">
                  {telemetry.click_interval.avg_ms} <span className="text-xs text-gray-500 font-normal">ms</span>
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-between items-center p-3 bg-dark-bg/60 rounded-lg border border-dark-border text-xs">
            <span className="text-gray-400">Straight-Line Ratio & Acceleration:</span>
            <span className="font-mono text-gray-200">
              {(telemetry.mouse_movement.straight_line_ratio * 100).toFixed(0)}% straight • {telemetry.cursor_speed.acceleration_curve}
            </span>
          </div>
        </div>

      </div>

      {/* Identity Timeline Section */}
      <div className="bg-dark-card p-5 rounded-xl border border-dark-border">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h3 className="text-sm font-bold text-gray-200 flex items-center gap-2">
              <Clock className="w-4 h-4 text-cyan-400" />
              Human Identity Audit Timeline
            </h3>
            <p className="text-xs text-gray-400 mt-0.5">Chronological record of identity verifications, behavioral shifts, and decision engine events</p>
          </div>
          <span className="text-xs text-gray-500 font-mono">{timelineEvents.length} Recorded Events</span>
        </div>

        <div className="space-y-3">
          {timelineEvents.length === 0 ? (
            <div className="p-6 text-center text-xs text-gray-500 bg-dark-bg/50 rounded-lg border border-dark-border/50">
              No identity events recorded yet. Run a simulation profile to append identity timeline entries.
            </div>
          ) : (
            timelineEvents.map((evt, idx) => {
              const isAutomation = evt.type === 'automation_detected' || evt.description.includes('Automation Detected');
              const isTrustRed = evt.type === 'trust_reduced' || evt.description.includes('Trust Reduced');
              const isSandbox = evt.type === 'sandbox' || evt.description.includes('Sandbox');
              const isChanged = evt.type === 'behaviour_changed' || evt.description.includes('Behaviour Changed');

              return (
                <div key={idx} className="flex items-start gap-3 p-3 bg-dark-bg/70 rounded-lg border border-dark-border/60 hover:bg-dark-hover/40 transition">
                  <div className={`p-2 rounded-lg mt-0.5 ${
                    isAutomation ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' :
                    isTrustRed ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                    isSandbox ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30' :
                    isChanged ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30' :
                    'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  }`}>
                    {isAutomation ? <Bot className="w-4 h-4" /> :
                     isTrustRed ? <AlertTriangle className="w-4 h-4" /> :
                     isSandbox ? <Box className="w-4 h-4" /> :
                     isChanged ? <Activity className="w-4 h-4" /> :
                     <UserCheck className="w-4 h-4" />}
                  </div>

                  <div className="flex-1">
                    <div className="flex justify-between items-center">
                      <span className="font-semibold text-xs text-gray-200">{evt.description}</span>
                      <span className="text-[10px] text-gray-500 font-mono">{evt.timestamp}</span>
                    </div>
                    <div className="flex items-center gap-3 text-[10px] text-gray-500 mt-1">
                      <span>Source: {evt.source_dataset || 'identity_monitoring_engine'}</span>
                      {evt.severity && (
                        <span className={`font-bold px-1.5 py-0.2 rounded ${
                          evt.severity === 'Critical' ? 'bg-rose-500/20 text-rose-400' :
                          evt.severity === 'High' ? 'bg-amber-500/20 text-amber-400' : 'bg-blue-500/20 text-blue-400'
                        }`}>
                          {evt.severity}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

    </div>
  );
}
