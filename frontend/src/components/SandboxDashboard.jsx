import React, { useState, useEffect } from 'react';
import {
  Shield, ShieldAlert, ShieldCheck, Box, Terminal, Activity,
  Cpu, HardDrive, Lock, AlertTriangle, CheckCircle2, XCircle,
  RefreshCw, Play, Search, AlertCircle, Server, Eye, FileText,
  Key, Radio, Layers, Check, ArrowRight
} from 'lucide-react';

const API_BASE = 'http://localhost:5000/api';

export default function SandboxDashboard({ employees, selectedEmp, setSelectedEmp, criticalThreshold, onRunSandboxComplete }) {
  // State
  const [categories, setCategories] = useState([
    "Opening executable files", "USB insertion", "File deletion",
    "Privilege escalation", "Registry modification", "PowerShell execution",
    "Bulk file copy", "Database export", "Unknown executable", "Mass downloads"
  ]);
  const [presets, setPresets] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState("PowerShell execution");
  const [commandInput, setCommandInput] = useState("powershell.exe -ExecutionPolicy Bypass -NoProfile -EncodedCommand SQBFA... (Encoded Payload)");
  const [targetEmpId, setTargetEmpId] = useState(selectedEmp ? selectedEmp.employee_id : (employees[0]?.employee_id || ''));

  // Execution & Simulation State
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisPhase, setAnalysisPhase] = useState(0);
  const [analysisReport, setAnalysisReport] = useState(null);
  const [sandboxHistory, setSandboxHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  // Analysis Phase Titles for realistic simulation animation
  const PHASES = [
    "Spinning up Isolated Virtual Kernel Container...",
    "Injecting process binary into Virtual Sandbox memory space...",
    "Running Behaviour & File Integrity Analysis...",
    "Performing Command Sequence & Registry Modification Detection...",
    "Scanning Network Connection & Privilege Escalation telemetry...",
    "Executing YARA Malware Signature & Data Exfiltration Scans...",
    "Synthesizing Risk Score & Generating AI Verdict..."
  ];

  // Synchronize target employee when selectedEmp changes from parent sidebar
  useEffect(() => {
    if (selectedEmp) {
      setTargetEmpId(selectedEmp.employee_id);
    }
  }, [selectedEmp]);

  // Fetch Presets and History on mount
  useEffect(() => {
    fetchPresets();
    fetchHistory();
  }, []);

  const fetchPresets = async () => {
    try {
      const token = localStorage.getItem('garuda_token');
      const res = await fetch(`${API_BASE}/sandbox/presets`, {
        headers: { 'Authorization': token ? `Bearer ${token}` : '' }
      });
      if (res.ok) {
        const data = await res.json();
        if (data.categories) setCategories(data.categories);
        if (data.presets) {
          setPresets(data.presets);
          // Set default command from first preset
          if (data.presets.length > 0) {
            setSelectedCategory(data.presets[0].category);
            setCommandInput(data.presets[0].command);
          }
        }
      }
    } catch (e) {
      console.error("Error loading sandbox presets:", e);
    }
  };

  const fetchHistory = async () => {
    setLoadingHistory(true);
    try {
      const token = localStorage.getItem('garuda_token');
      const res = await fetch(`${API_BASE}/sandbox/history?limit=25`, {
        headers: { 'Authorization': token ? `Bearer ${token}` : '' }
      });
      if (res.ok) {
        const data = await res.json();
        if (data.success) {
          setSandboxHistory(data.history || []);
        }
      }
    } catch (e) {
      console.error("Error fetching sandbox history:", e);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleSelectPreset = (preset) => {
    setSelectedCategory(preset.category);
    setCommandInput(preset.command);
  };

  const handleRunSandbox = async (e) => {
    if (e) e.preventDefault();
    if (!targetEmpId) {
      setErrorMsg("Please select an employee profile to analyze.");
      return;
    }
    if (!commandInput.trim()) {
      setErrorMsg("Please enter a command or action string to analyze.");
      return;
    }

    setErrorMsg('');
    setAnalyzing(true);
    setAnalysisPhase(0);
    setAnalysisReport(null);

    // Animate phase steps
    for (let i = 0; i < PHASES.length; i++) {
      setAnalysisPhase(i);
      await new Promise(r => setTimeout(r, 220));
    }

    try {
      const token = localStorage.getItem('garuda_token');
      const res = await fetch(`${API_BASE}/sandbox/evaluate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : ''
        },
        body: JSON.stringify({
          employee_id: targetEmpId,
          action_type: selectedCategory,
          command_name: commandInput,
          critical_threshold: criticalThreshold || 30
        })
      });

      const data = await res.json();
      if (res.ok && data.success) {
        setAnalysisReport(data.report);
        fetchHistory();
        if (onRunSandboxComplete) {
          onRunSandboxComplete(data.report);
        }
      } else {
        setErrorMsg(data.error || "Sandbox verification failed.");
      }
    } catch (e) {
      setErrorMsg("Network error communicating with Sandbox Engine: " + e.message);
    } finally {
      setAnalyzing(false);
    }
  };

  const activeEmpDoc = employees.find(e => e.employee_id === targetEmpId) || selectedEmp;

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-dark-bg text-gray-200">
      
      {/* Top Banner: Virtual Sandbox Engine Status */}
      <div className="p-4 bg-dark-card/60 border-b border-dark-border flex flex-wrap justify-between items-center gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-blue-500/10 border border-blue-500/30 rounded-lg text-blue-400">
            <Box className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-white tracking-wide">AI SANDBOX VERIFICATION ENGINE</h2>
              <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-full flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span>
                Isolated & Active
              </span>
            </div>
            <p className="text-xs text-gray-400 mt-0.5">
              Virtually executes suspicious employee activities before permitting real system interaction.
            </p>
          </div>
        </div>

        {/* Virtual Sandbox Hardware Telemetry Metrics */}
        <div className="flex items-center gap-4 text-xs font-mono bg-dark-bg/80 px-3.5 py-2 rounded-lg border border-dark-border/80">
          <div className="flex items-center gap-1.5">
            <Server className="w-3.5 h-3.5 text-blue-400" />
            <span className="text-gray-400">ENV:</span>
            <span className="text-gray-200 font-semibold">SBX-WIN11-V2.4</span>
          </div>
          <div className="h-4 w-px bg-dark-border"></div>
          <div className="flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5 text-indigo-400" />
            <span className="text-gray-400">CPU:</span>
            <span className="text-emerald-400 font-semibold">1.4% (Isolated)</span>
          </div>
          <div className="h-4 w-px bg-dark-border"></div>
          <div className="flex items-center gap-1.5">
            <HardDrive className="w-3.5 h-3.5 text-purple-400" />
            <span className="text-gray-400">MEM:</span>
            <span className="text-purple-300 font-semibold">128 MB</span>
          </div>
        </div>
      </div>

      {/* Main Split Layout: Left Controls & Right Sandbox Report */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* Left Side: Command Inspector & Trigger Controls */}
        <div className="w-[480px] border-r border-dark-border bg-dark-card/20 overflow-y-auto p-5 space-y-5 flex flex-col">
          
          {/* Target Employee Selection Card */}
          <div className="p-4 rounded-xl bg-dark-card/60 border border-dark-border/80 space-y-3">
            <label className="text-xs font-bold uppercase tracking-wider text-gray-300 flex items-center gap-2">
              <Key className="w-4 h-4 text-blue-400" />
              Target Employee Workstation
            </label>
            <select
              value={targetEmpId}
              onChange={(e) => {
                setTargetEmpId(e.target.value);
                const found = employees.find(emp => emp.employee_id === e.target.value);
                if (found && setSelectedEmp) setSelectedEmp(found);
              }}
              className="w-full bg-dark-bg border border-dark-border rounded-lg px-3 py-2 text-xs font-medium text-white focus:outline-none focus:border-blue-500"
            >
              {employees.map(emp => (
                <option key={emp.employee_id} value={emp.employee_id}>
                  {emp.full_name} ({emp.employee_id}) — {emp.department} [Score: {emp.current_score}]
                </option>
              ))}
            </select>

            {activeEmpDoc && (
              <div className="flex items-center justify-between text-xs p-2 rounded bg-dark-bg/60 border border-dark-border/40 text-gray-400">
                <span>Role: <strong className="text-gray-200">{activeEmpDoc.role}</strong></span>
                <span>Current Score: <strong className={activeEmpDoc.current_score < 50 ? 'text-rose-400 font-bold' : 'text-emerald-400 font-bold'}>{activeEmpDoc.current_score}</strong></span>
              </div>
            )}
          </div>

          {/* Trigger Category & Preset Attack Scenarios */}
          <div className="p-4 rounded-xl bg-dark-card/60 border border-dark-border/80 space-y-3">
            <div className="flex justify-between items-center">
              <label className="text-xs font-bold uppercase tracking-wider text-gray-300 flex items-center gap-2">
                <Radio className="w-4 h-4 text-amber-400" />
                High-Risk Trigger Action Category
              </label>
              <span className="text-[10px] text-amber-400 font-semibold px-2 py-0.5 bg-amber-500/10 rounded border border-amber-500/20">
                Sandbox Redirect Active
              </span>
            </div>

            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full bg-dark-bg border border-dark-border rounded-lg px-3 py-2 text-xs font-medium text-amber-300 focus:outline-none focus:border-amber-500"
            >
              {categories.map((cat, i) => (
                <option key={i} value={cat}>{cat}</option>
              ))}
            </select>

            {/* Quick Demo Preset Selector */}
            <div className="space-y-1.5">
              <span className="text-[11px] font-semibold text-gray-400">Quick Test Templates:</span>
              <div className="grid grid-cols-2 gap-1.5 max-h-36 overflow-y-auto pr-1">
                {presets.map((preset) => {
                  const isSelected = commandInput === preset.command;
                  return (
                    <button
                      key={preset.id}
                      onClick={() => handleSelectPreset(preset)}
                      className={`text-left p-2 rounded text-[11px] border transition-all cursor-pointer ${
                        isSelected
                          ? 'bg-blue-600/20 border-blue-500 text-blue-200'
                          : 'bg-dark-bg/60 border-dark-border/50 text-gray-400 hover:text-gray-200 hover:bg-dark-hover'
                      }`}
                    >
                      <div className="font-semibold truncate text-gray-200">{preset.description}</div>
                      <div className="text-[10px] text-gray-500 truncate">{preset.category}</div>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Action / Command Being Analysed */}
          <div className="p-4 rounded-xl bg-dark-card/60 border border-dark-border/80 space-y-3 flex-1 flex flex-col">
            <label className="text-xs font-bold uppercase tracking-wider text-gray-300 flex items-center gap-2">
              <Terminal className="w-4 h-4 text-emerald-400" />
              Command / Action Being Analysed
            </label>

            <textarea
              rows={4}
              value={commandInput}
              onChange={(e) => setCommandInput(e.target.value)}
              placeholder="Enter binary execution path, PowerShell command, registry change string..."
              className="w-full bg-dark-bg border border-dark-border rounded-lg p-3 text-xs font-mono text-emerald-300 focus:outline-none focus:border-emerald-500 resize-none flex-1"
            />

            {errorMsg && (
              <div className="p-2.5 rounded bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}

            {/* Run Sandbox Verification Action Button */}
            <button
              onClick={handleRunSandbox}
              disabled={analyzing}
              className={`w-full py-3 px-4 rounded-lg font-bold text-xs tracking-wider uppercase transition-all flex items-center justify-center gap-2 cursor-pointer ${
                analyzing
                  ? 'bg-blue-600/50 text-gray-300 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-600/30'
              }`}
            >
              {analyzing ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin text-white" />
                  <span>Redirecting to Virtual Sandbox...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  <span>Execute Sandbox Verification</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right Side: Virtual Sandbox Verification Report & Live Telemetry */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          
          {/* Animated Execution Progress Banner */}
          {analyzing && (
            <div className="p-6 rounded-xl bg-blue-950/40 border border-blue-500/40 space-y-4 animate-pulse">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <RefreshCw className="w-6 h-6 text-blue-400 animate-spin" />
                  <div>
                    <h3 className="text-sm font-bold text-white">VIRTUAL SANDBOX SIMULATION IN PROGRESS</h3>
                    <p className="text-xs text-blue-300 font-mono mt-0.5">{PHASES[analysisPhase]}</p>
                  </div>
                </div>
                <span className="text-xs font-mono text-blue-400 font-bold">Phase {analysisPhase + 1} of 7</span>
              </div>
              <div className="w-full bg-dark-bg h-2 rounded-full overflow-hidden border border-blue-500/30">
                <div
                  className="bg-blue-500 h-full transition-all duration-300"
                  style={{ width: `${((analysisPhase + 1) / 7) * 100}%` }}
                ></div>
              </div>
            </div>
          )}

          {/* Analysis Report Display */}
          {analysisReport ? (
            <div className="space-y-6">
              
              {/* Verdict Header Banner */}
              <div className={`p-6 rounded-xl border transition-all ${
                analysisReport.verdict === 'SAFE'
                  ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-300'
                  : analysisReport.verdict === 'SUSPICIOUS'
                    ? 'bg-amber-500/10 border-amber-500/40 text-amber-300'
                    : 'bg-rose-500/10 border-rose-500/40 text-rose-300'
              }`}>
                <div className="flex flex-wrap justify-between items-start gap-4">
                  <div className="flex items-start gap-4">
                    <div className={`p-3 rounded-xl border ${
                      analysisReport.verdict === 'SAFE'
                        ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-400'
                        : analysisReport.verdict === 'SUSPICIOUS'
                          ? 'bg-amber-500/20 border-amber-500/50 text-amber-400'
                          : 'bg-rose-500/20 border-rose-500/50 text-rose-400'
                    }`}>
                      {analysisReport.verdict === 'SAFE' ? (
                        <ShieldCheck className="w-10 h-10" />
                      ) : analysisReport.verdict === 'SUSPICIOUS' ? (
                        <AlertTriangle className="w-10 h-10" />
                      ) : (
                        <ShieldAlert className="w-10 h-10" />
                      )}
                    </div>
                    <div>
                      <div className="flex items-center gap-3">
                        <span className={`px-3 py-1 rounded-md text-sm font-extrabold uppercase tracking-wider ${
                          analysisReport.verdict === 'SAFE'
                            ? 'bg-emerald-500 text-black shadow-md'
                            : analysisReport.verdict === 'SUSPICIOUS'
                              ? 'bg-amber-500 text-black shadow-md'
                              : 'bg-rose-600 text-white shadow-md'
                        }`}>
                          VERDICT: {analysisReport.verdict}
                        </span>
                        <span className="text-xs font-mono text-gray-400">
                          {analysisReport.display_status}
                        </span>
                      </div>

                      <h3 className="text-lg font-bold text-white mt-2">
                        {analysisReport.threat_category}
                      </h3>
                      <p className="text-xs text-gray-300 mt-1 max-w-xl">
                        {analysisReport.recommendation}
                      </p>
                    </div>
                  </div>

                  {/* Risk Score & Confidence Badge */}
                  <div className="text-right bg-dark-bg/80 p-4 rounded-xl border border-dark-border/80 min-w-[160px]">
                    <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Risk Score</div>
                    <div className={`text-3xl font-black font-mono my-1 ${
                      analysisReport.risk_score >= 70 ? 'text-rose-500' : analysisReport.risk_score >= 40 ? 'text-amber-400' : 'text-emerald-400'
                    }`}>
                      {analysisReport.risk_score} <span className="text-sm font-normal text-gray-500">/ 100</span>
                    </div>
                    <div className="text-[11px] text-gray-400">
                      Confidence: <strong className="text-white">{analysisReport.confidence_score}%</strong>
                    </div>
                  </div>
                </div>

                {/* Status Summary pill badges */}
                <div className="mt-4 pt-4 border-t border-dark-border/40 flex flex-wrap items-center justify-between text-xs gap-3">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-gray-400">Execution Decision:</span>
                    <span className="font-bold text-white">{analysisReport.execution_status}</span>
                  </div>
                  {analysisReport.lock_triggered && (
                    <div className="flex items-center gap-1.5 px-2.5 py-1 bg-rose-500/20 text-rose-300 border border-rose-500/40 rounded font-bold">
                      <Lock className="w-3.5 h-3.5" />
                      Employee Workstation Lock Triggered!
                    </div>
                  )}
                </div>
              </div>

              {/* 8-Point Behaviour Analysis Breakdown Grid */}
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2 uppercase tracking-wider">
                    <Layers className="w-4 h-4 text-blue-400" />
                    8-Point Behaviour Analysis Breakdown
                  </h3>
                  <span className="text-xs text-gray-400 font-mono">Isolated Container Diagnostics</span>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  {Object.entries({
                    "Behaviour Analysis": analysisReport.checks?.behaviour_analysis,
                    "File Integrity Check": analysisReport.checks?.file_integrity_check,
                    "Command Sequence Analysis": analysisReport.checks?.command_sequence_analysis,
                    "Registry Change Detection": analysisReport.checks?.registry_change_detection,
                    "Network Connection Detection": analysisReport.checks?.network_connection_detection,
                    "Privilege Escalation Detection": analysisReport.checks?.privilege_escalation_detection,
                    "Malware Signature Scan": analysisReport.checks?.malware_signature_scan,
                    "Data Exfiltration Detection": analysisReport.checks?.data_exfiltration_detection
                  }).map(([checkName, data], idx) => {
                    if (!data) return null;
                    const isSevere = data.status === 'CRITICAL' || data.status === 'MALICIOUS' || data.status === 'HIGH_RISK';
                    const isWarn = data.status === 'WARNING' || data.status === 'SUSPICIOUS';
                    return (
                      <div
                        key={idx}
                        className={`p-3.5 rounded-xl border transition-all ${
                          isSevere
                            ? 'bg-rose-500/5 border-rose-500/30'
                            : isWarn
                              ? 'bg-amber-500/5 border-amber-500/30'
                              : 'bg-dark-card/40 border-dark-border/60'
                        }`}
                      >
                        <div className="flex justify-between items-start gap-2">
                          <span className="font-bold text-xs text-gray-200">{checkName}</span>
                          <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${
                            isSevere
                              ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                              : isWarn
                                ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                                : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                          }`}>
                            {data.status}
                          </span>
                        </div>
                        <p className="text-xs text-gray-400 mt-2 font-sans leading-relaxed">
                          {data.details}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>

            </div>
          ) : !analyzing && (
            <div className="flex flex-col items-center justify-center h-80 rounded-xl border border-dashed border-dark-border/80 text-gray-500 space-y-3">
              <Box className="w-12 h-12 text-gray-600" />
              <div className="text-center">
                <p className="text-sm font-semibold text-gray-400">No active Sandbox verification report loaded.</p>
                <p className="text-xs text-gray-500 mt-1">Select a command or trigger scenario on the left and click "Execute Sandbox Verification".</p>
              </div>
            </div>
          )}

          {/* Sandbox Evaluation Audit Log History Table */}
          <div className="space-y-3 pt-4 border-t border-dark-border">
            <div className="flex justify-between items-center">
              <h3 className="text-sm font-bold text-white flex items-center gap-2 uppercase tracking-wider">
                <Activity className="w-4 h-4 text-purple-400" />
                Recent Sandbox Execution Logs
              </h3>
              <button
                onClick={fetchHistory}
                className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 cursor-pointer"
              >
                <RefreshCw className={`w-3 h-3 ${loadingHistory ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>

            <div className="overflow-x-auto rounded-xl border border-dark-border bg-dark-card/30">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-dark-bg/60 border-b border-dark-border text-gray-400 text-[11px] font-semibold uppercase tracking-wider">
                    <th className="p-3">Timestamp</th>
                    <th className="p-3">Employee</th>
                    <th className="p-3">Category</th>
                    <th className="p-3">Command</th>
                    <th className="p-3">Verdict</th>
                    <th className="p-3 text-right">Risk Score</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-dark-border/40 text-gray-300 font-mono text-[11px]">
                  {sandboxHistory.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="p-4 text-center text-gray-500 font-sans">
                        No previous sandbox execution history logged.
                      </td>
                    </tr>
                  ) : (
                    sandboxHistory.map((run, idx) => (
                      <tr key={idx} className="hover:bg-dark-hover/40 transition-all">
                        <td className="p-3 text-gray-400 whitespace-nowrap">{run.timestamp}</td>
                        <td className="p-3 font-sans font-semibold text-white whitespace-nowrap">
                          {run.employee_name} ({run.employee_id})
                        </td>
                        <td className="p-3 font-sans text-gray-400">{run.action_type}</td>
                        <td className="p-3 max-w-xs truncate text-emerald-400" title={run.command_name}>
                          {run.command_name}
                        </td>
                        <td className="p-3 whitespace-nowrap">
                          <span className={`px-2 py-0.5 rounded font-extrabold uppercase text-[10px] ${
                            run.verdict === 'SAFE'
                              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                              : run.verdict === 'SUSPICIOUS'
                                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                                : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                          }`}>
                            {run.verdict}
                          </span>
                        </td>
                        <td className={`p-3 text-right font-bold whitespace-nowrap ${
                          run.risk_score >= 70 ? 'text-rose-400' : run.risk_score >= 40 ? 'text-amber-400' : 'text-emerald-400'
                        }`}>
                          {run.risk_score} / 100
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
