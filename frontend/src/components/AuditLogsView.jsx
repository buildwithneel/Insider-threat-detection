import React, { useState, useEffect } from 'react';
import { 
  FileText, Shield, ShieldAlert, CheckCircle2, XCircle, AlertTriangle, RefreshCw, Filter, Clock, Search, Lock
} from 'lucide-react';

const API_BASE = 'http://localhost:5000/api';

export default function AuditLogsView({ currentUserToken, theme = 'dark' }) {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [roleFilter, setRoleFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchAuditLogs();
  }, [roleFilter, statusFilter]);

  const fetchAuditLogs = async () => {
    setLoading(true);
    setError('');
    try {
      const queryParams = new URLSearchParams();
      if (roleFilter !== 'All') queryParams.append('role', roleFilter);
      if (statusFilter !== 'All') queryParams.append('status', statusFilter);
      queryParams.append('limit', '150');

      const res = await fetch(`${API_BASE}/rbac/audit-logs?${queryParams.toString()}`, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': currentUserToken ? `Bearer ${currentUserToken}` : ''
        }
      });

      const data = await res.json();
      if (res.ok && data.success) {
        setLogs(data.audit_logs || []);
      } else {
        setError(data.message || data.error || 'Failed to fetch system audit logs.');
      }
    } catch (err) {
      setError('Backend API server unreachable.');
    } finally {
      setLoading(false);
    }
  };

  const filteredLogs = logs.filter(l => {
    const q = searchQuery.toLowerCase();
    return (
      l.action?.toLowerCase().includes(q) ||
      l.user_email?.toLowerCase().includes(q) ||
      l.details?.toLowerCase().includes(q) ||
      l.log_id?.toLowerCase().includes(q)
    );
  });

  const isDark = theme === 'dark';

  return (
    <div className={`p-6 rounded-2xl shadow-xl border space-y-6 ${isDark ? 'bg-slate-900 border-slate-800 text-gray-100' : 'bg-white border-slate-200 text-slate-900'}`}>
      
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-xl bg-gradient-to-br from-amber-500/20 to-orange-500/20 border border-amber-500/30 text-amber-400">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold tracking-tight">System Security & Access Audit Trail</h2>
            <p className="text-xs text-gray-400">Immutable logging of logins, permission checks, token generations & security overrides</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={fetchAuditLogs}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-gray-300 transition-all border border-slate-700 cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Audit Stream</span>
          </button>
        </div>
      </div>

      {/* Filter Controls Bar */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-3 p-3 rounded-xl bg-slate-800/40 border border-slate-800">
        <div className="flex items-center gap-2 w-full md:w-auto">
          <div className="relative flex-1 md:w-64">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-gray-400" />
            <input
              type="text"
              placeholder="Search action, email, log ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs outline-none focus:border-amber-500 text-gray-200"
            />
          </div>
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="flex items-center gap-1.5">
            <Filter className="w-3.5 h-3.5 text-gray-400" />
            <span className="text-xs text-gray-400">Role:</span>
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-amber-300 font-semibold outline-none focus:border-amber-500"
            >
              <option value="All">All System Roles</option>
              <option value="CEO">CEO</option>
              <option value="HR">HR</option>
              <option value="Security Manager">Security Manager</option>
              <option value="Security Analyst">Security Analyst</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-xs text-gray-400">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-emerald-300 font-semibold outline-none focus:border-amber-500"
            >
              <option value="All">All Statuses</option>
              <option value="SUCCESS">SUCCESS</option>
              <option value="DENIED">DENIED (HTTP 403)</option>
              <option value="FAILED">FAILED</option>
            </select>
          </div>
        </div>
      </div>

      {/* Error Notice */}
      {error && (
        <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Audit Logs Table */}
      <div className="overflow-x-auto rounded-xl border border-slate-800">
        {loading ? (
          <div className="py-16 text-center text-xs text-gray-400 flex justify-center items-center gap-2">
            <RefreshCw className="w-4 h-4 animate-spin text-amber-400" />
            <span>Loading security audit trail...</span>
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="py-16 text-center text-xs text-gray-400">
            No audit log entries matching current criteria.
          </div>
        ) : (
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/60 text-gray-400 font-semibold">
                <th className="py-3 px-3">Log ID & Timestamp</th>
                <th className="py-3 px-3">Event Action</th>
                <th className="py-3 px-3">User & Role</th>
                <th className="py-3 px-3">Status</th>
                <th className="py-3 px-3">Details & Technical Context</th>
                <th className="py-3 px-3 text-right">IP Address</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredLogs.map((log) => {
                const isDenied = log.status === 'DENIED';
                const isSuccess = log.status === 'SUCCESS';

                return (
                  <tr key={log.log_id || Math.random()} className={`hover:bg-slate-800/30 transition-all ${isDenied ? 'bg-red-500/5' : ''}`}>
                    <td className="py-3 px-3 whitespace-nowrap">
                      <div className="font-mono text-amber-400 font-medium">{log.log_id}</div>
                      <div className="text-[11px] text-gray-400 flex items-center gap-1 mt-0.5">
                        <Clock className="w-3 h-3 text-gray-500" />
                        {new Date(log.timestamp).toLocaleString()}
                      </div>
                    </td>

                    <td className="py-3 px-3">
                      <div className="font-semibold text-gray-200 flex items-center gap-1.5">
                        {isDenied && <Lock className="w-3.5 h-3.5 text-red-400" />}
                        {log.action}
                      </div>
                    </td>

                    <td className="py-3 px-3">
                      <div className="text-gray-300">{log.user_email}</div>
                      <div className="text-[11px] text-indigo-400 font-medium">{log.user_role}</div>
                    </td>

                    <td className="py-3 px-3">
                      {isDenied ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-500/20 text-red-400 border border-red-500/30 flex items-center gap-1 w-fit">
                          <XCircle className="w-3 h-3" /> ACCESS DENIED
                        </span>
                      ) : isSuccess ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1 w-fit">
                          <CheckCircle2 className="w-3 h-3" /> SUCCESS
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center gap-1 w-fit">
                          <AlertTriangle className="w-3 h-3" /> FAILED
                        </span>
                      )}
                    </td>

                    <td className="py-3 px-3 text-gray-300 max-w-md break-words">
                      {log.details}
                    </td>

                    <td className="py-3 px-3 text-right font-mono text-[11px] text-gray-400">
                      {log.ip_address || '127.0.0.1'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

    </div>
  );
}
