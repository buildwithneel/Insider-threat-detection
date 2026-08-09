import React, { useState, useEffect } from 'react';
import { 
  Users, UserPlus, Shield, Trash2, KeyRound, Unlock, RefreshCw, X, AlertTriangle, CheckCircle2, Lock
} from 'lucide-react';

const API_BASE = 'http://localhost:5000/api';

export default function RbacUserManagementModal({ isOpen, onClose, currentUserToken, theme = 'dark' }) {
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // New User Form State
  const [showAddForm, setShowAddForm] = useState(false);
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [employeeId, setEmployeeId] = useState('');
  const [department, setDepartment] = useState('SOC & Operations');
  const [designation, setDesignation] = useState('Security Specialist');
  const [role, setRole] = useState('Security Analyst');
  const [password, setPassword] = useState('');
  const [formLoading, setFormLoading] = useState(false);

  // Reset Password Modal State
  const [resetTargetUser, setResetTargetUser] = useState(null);
  const [newPass, setNewPass] = useState('');
  const [resetLoading, setResetLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchUsers();
      fetchRoles();
    }
  }, [isOpen]);

  const getHeaders = () => ({
    'Content-Type': 'application/json',
    'Authorization': currentUserToken ? `Bearer ${currentUserToken}` : ''
  });

  const fetchUsers = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/rbac/users`, { headers: getHeaders() });
      const data = await res.json();
      if (res.ok && data.success) {
        setUsers(data.users || []);
      } else {
        setError(data.message || data.error || 'Failed to load user accounts.');
      }
    } catch (err) {
      setError('Backend API server unreachable.');
    } finally {
      setLoading(false);
    }
  };

  const fetchRoles = async () => {
    try {
      const res = await fetch(`${API_BASE}/rbac/roles`, { headers: getHeaders() });
      const data = await res.json();
      if (res.ok && data.success) {
        setRoles(data.roles || []);
      }
    } catch (err) {
      console.error('Error fetching roles:', err);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');

    if (!fullName || !email || !employeeId || !password) {
      setError('Please fill in all required fields.');
      return;
    }

    setFormLoading(true);
    try {
      const res = await fetch(`${API_BASE}/rbac/users`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
          full_name: fullName,
          email,
          employee_id: employeeId,
          department,
          designation,
          role,
          password
        })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setSuccessMsg(`User ${email} (${role}) created successfully!`);
        setShowAddForm(false);
        setFullName('');
        setEmail('');
        setEmployeeId('');
        setPassword('');
        fetchUsers();
      } else {
        setError(data.message || data.error || 'Failed to create user.');
      }
    } catch (err) {
      setError('Failed to connect to backend server.');
    } finally {
      setFormLoading(false);
    }
  };

  const handleDeleteUser = async (userId, targetEmail) => {
    if (!window.confirm(`Are you sure you want to permanently delete user account ${targetEmail}?`)) return;

    setError('');
    setSuccessMsg('');
    try {
      const res = await fetch(`${API_BASE}/rbac/users/${userId}`, {
        method: 'DELETE',
        headers: getHeaders()
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setSuccessMsg(`User ${targetEmail} deleted.`);
        fetchUsers();
      } else {
        setError(data.message || data.error || 'Failed to delete user account.');
      }
    } catch (err) {
      setError('Failed to connect to backend server.');
    }
  };

  const handleUnlockUser = async (userId, targetEmail) => {
    setError('');
    setSuccessMsg('');
    try {
      const res = await fetch(`${API_BASE}/rbac/users/${userId}/unlock`, {
        method: 'POST',
        headers: getHeaders()
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setSuccessMsg(`Account ${targetEmail} unlocked successfully.`);
        fetchUsers();
      } else {
        setError(data.message || data.error || 'Failed to unlock user.');
      }
    } catch (err) {
      setError('Failed to connect to backend server.');
    }
  };

  const handleResetPasswordSubmit = async (e) => {
    e.preventDefault();
    if (!resetTargetUser || !newPass) return;

    setError('');
    setSuccessMsg('');
    setResetLoading(true);
    try {
      const res = await fetch(`${API_BASE}/rbac/users/${resetTargetUser._id}/reset-password`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ new_password: newPass })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setSuccessMsg(`Password reset for ${resetTargetUser.email}.`);
        setResetTargetUser(null);
        setNewPass('');
        fetchUsers();
      } else {
        setError(data.message || data.error || 'Failed to reset password.');
      }
    } catch (err) {
      setError('Failed to connect to backend server.');
    } finally {
      setResetLoading(false);
    }
  };

  if (!isOpen) return null;

  const isDark = theme === 'dark';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 overflow-y-auto select-none">
      <div className={`w-full max-w-5xl rounded-2xl shadow-2xl border p-6 max-h-[90vh] flex flex-col ${isDark ? 'bg-slate-900 border-slate-800 text-gray-100' : 'bg-white border-slate-200 text-slate-900'}`}>
        
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-700/50">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/30 text-indigo-400">
              <Shield className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold tracking-tight">Enterprise User & Role Management</h2>
              <p className="text-xs text-gray-400">CEO Administrative Console • Provision Accounts & RBAC Hierarchies</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowAddForm(!showAddForm)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white transition-all shadow-md cursor-pointer"
            >
              <UserPlus className="w-4 h-4" />
              <span>{showAddForm ? 'Cancel Provisioning' : 'Provision User Account'}</span>
            </button>

            <button 
              onClick={onClose}
              className="p-1.5 rounded-lg hover:bg-slate-800 text-gray-400 hover:text-white transition-all cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Notifications */}
        {error && (
          <div className="mt-4 p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {successMsg && (
          <div className="mt-4 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Provision New User Form */}
        {showAddForm && (
          <form onSubmit={handleCreateUser} className="mt-4 p-4 rounded-xl bg-slate-800/60 border border-slate-700 space-y-3">
            <h3 className="text-sm font-semibold text-indigo-400 flex items-center gap-2">
              <UserPlus className="w-4 h-4" /> Provision New Enterprise Security Account
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label className="text-[11px] font-medium text-gray-400">Full Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. John Doe"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full mt-1 px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs focus:border-indigo-500 outline-none"
                />
              </div>

              <div>
                <label className="text-[11px] font-medium text-gray-400">Email Address *</label>
                <input
                  type="email"
                  required
                  placeholder="john.doe@garudaai.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full mt-1 px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs focus:border-indigo-500 outline-none"
                />
              </div>

              <div>
                <label className="text-[11px] font-medium text-gray-400">Employee ID *</label>
                <input
                  type="text"
                  required
                  placeholder="GAR-EMP-109"
                  value={employeeId}
                  onChange={(e) => setEmployeeId(e.target.value)}
                  className="w-full mt-1 px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs focus:border-indigo-500 outline-none"
                />
              </div>

              <div>
                <label className="text-[11px] font-medium text-gray-400">Department</label>
                <input
                  type="text"
                  placeholder="SOC & Operations"
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                  className="w-full mt-1 px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs focus:border-indigo-500 outline-none"
                />
              </div>

              <div>
                <label className="text-[11px] font-medium text-gray-400">Designation</label>
                <input
                  type="text"
                  placeholder="Security Specialist"
                  value={designation}
                  onChange={(e) => setDesignation(e.target.value)}
                  className="w-full mt-1 px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs focus:border-indigo-500 outline-none"
                />
              </div>

              <div>
                <label className="text-[11px] font-medium text-gray-400">Assigned System Role *</label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full mt-1 px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-indigo-300 font-semibold focus:border-indigo-500 outline-none"
                >
                  <option value="CEO">CEO (Highest Privilege)</option>
                  <option value="HR">HR (Human Resources)</option>
                  <option value="Security Manager">Security Manager (SOC Lead)</option>
                  <option value="Security Analyst">Security Analyst (Read-Only Investigation)</option>
                </select>
              </div>

              <div>
                <label className="text-[11px] font-medium text-gray-400">Password (PQC Protected) *</label>
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full mt-1 px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs focus:border-indigo-500 outline-none"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="submit"
                disabled={formLoading}
                className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg shadow cursor-pointer"
              >
                {formLoading ? 'Encrypting & Saving...' : 'Create Account'}
              </button>
            </div>
          </form>
        )}

        {/* User Accounts Table */}
        <div className="mt-4 flex-1 overflow-y-auto">
          {loading ? (
            <div className="py-12 flex justify-center items-center text-gray-400 text-xs gap-2">
              <RefreshCw className="w-4 h-4 animate-spin text-indigo-400" />
              <span>Fetching enterprise user accounts...</span>
            </div>
          ) : (
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-gray-400 font-semibold">
                  <th className="py-2.5 px-3">User & ID</th>
                  <th className="py-2.5 px-3">Department & Title</th>
                  <th className="py-2.5 px-3">Role</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Failed Logins</th>
                  <th className="py-2.5 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {users.map((u) => {
                  const isLocked = u.account_locked;
                  return (
                    <tr key={u._id} className="hover:bg-slate-800/30 transition-all">
                      <td className="py-3 px-3">
                        <div className="font-semibold text-gray-200">{u.full_name}</div>
                        <div className="text-[11px] text-gray-400 font-mono">{u.email} • ID: {u.employee_id}</div>
                      </td>

                      <td className="py-3 px-3">
                        <div className="text-gray-300">{u.designation || u.role}</div>
                        <div className="text-[11px] text-indigo-400">{u.department}</div>
                      </td>

                      <td className="py-3 px-3">
                        <span className={`px-2 py-0.5 rounded-md font-semibold text-[11px] ${
                          u.role === 'CEO' ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' :
                          u.role === 'Security Manager' ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30' :
                          u.role === 'HR' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' :
                          'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                        }`}>
                          {u.role}
                        </span>
                      </td>

                      <td className="py-3 px-3">
                        {isLocked ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-500/20 text-red-400 border border-red-500/30 flex items-center gap-1 w-fit">
                            <Lock className="w-3 h-3" /> Locked
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1 w-fit">
                            <CheckCircle2 className="w-3 h-3" /> Active
                          </span>
                        )}
                      </td>

                      <td className="py-3 px-3 font-mono text-gray-400">
                        {u.failed_login_attempts || 0} / 5
                      </td>

                      <td className="py-3 px-3 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          {isLocked && (
                            <button
                              onClick={() => handleUnlockUser(u._id, u.email)}
                              title="Unlock Account"
                              className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 border border-emerald-500/30 cursor-pointer"
                            >
                              <Unlock className="w-3.5 h-3.5" />
                            </button>
                          )}

                          <button
                            onClick={() => setResetTargetUser(u)}
                            title="Reset Password"
                            className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400 hover:bg-indigo-500/20 border border-indigo-500/30 cursor-pointer"
                          >
                            <KeyRound className="w-3.5 h-3.5" />
                          </button>

                          <button
                            onClick={() => handleDeleteUser(u._id, u.email)}
                            title="Delete User Account"
                            className="p-1.5 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 border border-red-500/30 cursor-pointer"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        {/* Reset Password Sub-Modal */}
        {resetTargetUser && (
          <div className="fixed inset-0 z-60 flex items-center justify-center bg-black/80 p-4">
            <form onSubmit={handleResetPasswordSubmit} className="w-full max-w-md bg-slate-900 border border-slate-700 rounded-xl p-5 space-y-4 shadow-2xl">
              <h3 className="text-sm font-bold text-gray-200 flex items-center gap-2">
                <KeyRound className="w-4 h-4 text-indigo-400" /> Reset Password for {resetTargetUser.email}
              </h3>
              <div>
                <label className="text-xs text-gray-400">New Password (ML-KEM-768 PQC Encrypted)</label>
                <input
                  type="password"
                  required
                  placeholder="Enter new password..."
                  value={newPass}
                  onChange={(e) => setNewPass(e.target.value)}
                  className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:border-indigo-500 outline-none"
                />
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setResetTargetUser(null)}
                  className="px-3 py-1.5 bg-slate-800 text-gray-300 text-xs rounded-lg cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={resetLoading}
                  className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg cursor-pointer"
                >
                  {resetLoading ? 'Resetting...' : 'Confirm Password Reset'}
                </button>
              </div>
            </form>
          </div>
        )}

      </div>
    </div>
  );
}
