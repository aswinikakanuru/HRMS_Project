// HRMS Frontend - Built with React 18 & JavaScript (Zero Node.js Required)
const { useState, useEffect, useCallback, useMemo } = React;

const API_BASE = window.location.origin.includes(':8000') 
  ? window.location.origin 
  : 'http://127.0.0.1:8000';

// API Helper
async function api(endpoint, method = 'GET', body = null) {
  const token = localStorage.getItem('hrms_token');
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const config = { method, headers };
  if (body && method !== 'GET') config.body = JSON.stringify(body);

  const res = await fetch(`${API_BASE}${endpoint}`, config);
  if (res.status === 401) {
    localStorage.removeItem('hrms_token');
    localStorage.removeItem('hrms_user');
    localStorage.removeItem('hrms_employee');
    window.location.reload();
    throw new Error('Session expired');
  }

  const contentType = res.headers.get('content-type');
  if (contentType && contentType.includes('text/csv')) {
    return res.blob();
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || 'An error occurred');
  }
  return res.json();
}

function App() {
  const [token, setToken] = useState(localStorage.getItem('hrms_token') || '');
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('hrms_user')) || null; } catch { return null; }
  });
  const [employee, setEmployee] = useState(() => {
    try { return JSON.parse(localStorage.getItem('hrms_employee')) || null; } catch { return null; }
  });

  const [activeTab, setActiveTab] = useState('dashboard');
  const [toast, setToast] = useState(null);
  const [unreadNotifsCount, setUnreadNotifsCount] = useState(0);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const handleLoginSuccess = (authToken, authUser, authEmp) => {
    setToken(authToken);
    setUser(authUser);
    setEmployee(authEmp);
    localStorage.setItem('hrms_token', authToken);
    localStorage.setItem('hrms_user', JSON.stringify(authUser));
    localStorage.setItem('hrms_employee', JSON.stringify(authEmp));
    showToast(`Welcome back, ${authEmp ? authEmp.firstname : authUser.email}!`);
  };

  const handleLogout = () => {
    localStorage.removeItem('hrms_token');
    localStorage.removeItem('hrms_user');
    localStorage.removeItem('hrms_employee');
    setToken('');
    setUser(null);
    setEmployee(null);
    showToast('Logged out successfully', 'info');
  };

  const fetchNotificationCount = useCallback(async () => {
    if (!token) return;
    try {
      const data = await api('/notifications/');
      const unread = data.filter(n => !n.is_read).length;
      setUnreadNotifsCount(unread);
    } catch (e) {
      // silent
    }
  }, [token]);

  useEffect(() => {
    if (token) {
      fetchNotificationCount();
      const interval = setInterval(fetchNotificationCount, 15000);
      return () => clearInterval(interval);
    }
  }, [token, fetchNotificationCount]);

  if (!token) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} showToast={showToast} />;
  }

  const isAdminOrHR = user && (user.role === 'Admin' || user.role === 'HR');
  const isManager = user && (user.role === 'Manager' || isAdminOrHR);

  return (
    <div className="min-h-screen flex flex-col bg-slate-100">
      {/* Toast Alert */}
      {toast && (
        <div className={`fixed top-5 right-5 z-50 px-4 py-3 rounded-lg shadow-lg text-white font-medium text-sm flex items-center space-x-2 transition-all ${
          toast.type === 'error' ? 'bg-rose-600' : toast.type === 'info' ? 'bg-sky-600' : 'bg-emerald-600'
        }`}>
          <span>{toast.message}</span>
        </div>
      )}

      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center text-white font-bold text-lg shadow-sm">
              HR
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-800 leading-tight">HRMS Portal</h1>
              <p className="text-xs text-slate-400 font-medium">Enterprise Management</p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="hidden sm:flex flex-col text-right">
              <span className="text-sm font-semibold text-slate-800">
                {employee ? `${employee.firstname} ${employee.lastname}` : user?.email}
              </span>
              <div className="flex items-center justify-end space-x-1.5 mt-0.5">
                <span className="text-xs text-slate-400 font-mono">{employee?.employee_code || 'ID: ' + user?.id}</span>
                <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold ${
                  user?.role === 'Admin' ? 'bg-purple-100 text-purple-700' :
                  user?.role === 'Manager' ? 'bg-blue-100 text-blue-700' :
                  user?.role === 'HR' ? 'bg-sky-100 text-sky-700' : 'bg-emerald-100 text-emerald-700'
                }`}>
                  {user?.role}
                </span>
              </div>
            </div>

            <button 
              onClick={() => setActiveTab('notifications')}
              className="relative p-2 text-slate-500 hover:text-indigo-600 hover:bg-slate-50 rounded-lg transition"
              title="Notifications"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              {unreadNotifsCount > 0 && (
                <span className="absolute top-1 right-1 w-4 h-4 bg-rose-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center">
                  {unreadNotifsCount}
                </span>
              )}
            </button>

            <button 
              onClick={handleLogout}
              className="px-3 py-1.5 text-xs font-semibold text-rose-600 hover:bg-rose-50 border border-rose-200 rounded-lg transition"
            >
              Sign Out
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 border-t border-slate-100">
          <nav className="flex space-x-1 sm:space-x-4 overflow-x-auto py-2">
            {[
              { id: 'dashboard', label: 'Dashboard', icon: '📊' },
              { id: 'attendance', label: 'Attendance', icon: '⏱️' },
              { id: 'leaves', label: 'Leaves', icon: '🏖️' },
              { id: 'wfh', label: 'Work From Home', icon: '🏠' },
              { id: 'holidays', label: 'Holidays', icon: '📅' },
              { id: 'notifications', label: `Notifications ${unreadNotifsCount > 0 ? `(${unreadNotifsCount})` : ''}`, icon: '🔔' },
              ...(isAdminOrHR ? [{ id: 'employees', label: 'Employees', icon: '👥' }] : []),
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-1.5 px-3 py-2 rounded-lg text-sm font-medium transition whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'bg-indigo-50 text-indigo-700 font-semibold shadow-sm'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'dashboard' && <DashboardTab user={user} employee={employee} showToast={showToast} setActiveTab={setActiveTab} />}
        {activeTab === 'attendance' && <AttendanceTab employee={employee} isAdminOrHR={isAdminOrHR} showToast={showToast} />}
        {activeTab === 'leaves' && <LeavesTab employee={employee} isManager={isManager} showToast={showToast} />}
        {activeTab === 'wfh' && <WFHTab employee={employee} isManager={isManager} showToast={showToast} />}
        {activeTab === 'holidays' && <HolidaysTab isAdminOrHR={isAdminOrHR} showToast={showToast} />}
        {activeTab === 'notifications' && <NotificationsTab onUpdate={fetchNotificationCount} showToast={showToast} />}
        {activeTab === 'employees' && isAdminOrHR && <EmployeesTab showToast={showToast} />}
      </main>
    </div>
  );
}

// -------------------------------------------------------------
// 1. LOGIN & REGISTRATION COMPONENT
// -------------------------------------------------------------
function LoginPage({ onLoginSuccess, showToast }) {
  const [isRegister, setIsRegister] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('Employee');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!email || !password) return showToast('Please enter both email and password', 'error');

    setLoading(true);
    try {
      if (isRegister) {
        if (!name) {
          setLoading(false);
          return showToast('Please enter your full name', 'error');
        }
        await api('/auth/register', 'POST', { name, email, password, role });
        showToast('Registration successful! Signing in...', 'success');
      }

      // Login immediately
      const res = await api('/auth/login-json', 'POST', { email, password });
      const authToken = res.access_token;

      localStorage.setItem('hrms_token', authToken);
      const authUser = await api('/auth/getuser');

      let authEmp = null;
      try {
        authEmp = await api('/employees/me');
      } catch (err) {
        // User has no linked employee profile
      }

      onLoginSuccess(authToken, authUser, authEmp);
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const fillCredentials = (demoEmail, demoPass) => {
    setIsRegister(false);
    setEmail(demoEmail);
    setPassword(demoPass);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 p-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-2xl p-8 border border-slate-100">
        <div className="text-center mb-6">
          <div className="w-16 h-16 bg-gradient-to-tr from-indigo-600 to-violet-500 rounded-2xl mx-auto flex items-center justify-center text-white text-2xl font-bold shadow-lg shadow-indigo-500/20 mb-3">
            HR
          </div>
          <h2 className="text-2xl font-bold text-slate-800">
            {isRegister ? 'Create Your Account' : 'HRMS Portal Login'}
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            {isRegister ? 'Register your individual employee profile' : 'Sign in to access your dashboard'}
          </p>

          {/* Mode Switcher Tabs */}
          <div className="flex bg-slate-100 p-1 rounded-xl mt-4">
            <button
              type="button"
              onClick={() => setIsRegister(false)}
              className={`flex-1 py-1.5 text-xs font-bold rounded-lg transition ${
                !isRegister ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              🔑 Sign In
            </button>
            <button
              type="button"
              onClick={() => setIsRegister(true)}
              className={`flex-1 py-1.5 text-xs font-bold rounded-lg transition ${
                isRegister ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              📝 Register
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {isRegister && (
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
                Full Name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
                placeholder="e.g. Rahul Sharma"
                required={isRegister}
              />
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
              placeholder="e.g. employee@company.com"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
              placeholder="••••••••"
              required
            />
          </div>

          {isRegister && (
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
                Select Role
              </label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition font-medium"
              >
                <option value="Employee">Employee</option>
                <option value="Manager">Manager</option>
                <option value="HR">HR</option>
              </select>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl text-sm shadow-md shadow-indigo-600/20 transition disabled:opacity-50 mt-2"
          >
            {loading ? (isRegister ? 'Registering...' : 'Authenticating...') : (isRegister ? 'Complete Registration' : 'Sign In')}
          </button>
        </form>

        {/* Demo Fast-fill Buttons */}
        <div className="mt-6 pt-5 border-t border-slate-100">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider text-center mb-3">
            Quick Test Accounts
          </p>
          <div className="grid grid-cols-3 gap-2">
            <button
              type="button"
              onClick={() => fillCredentials('admin@gmail.com', 'admin123')}
              className="px-2.5 py-2 text-xs font-medium bg-purple-50 text-purple-700 hover:bg-purple-100 rounded-lg text-center transition"
            >
              👑 Admin
            </button>
            <button
              type="button"
              onClick={() => fillCredentials('manager@gmail.com', 'manager123')}
              className="px-2.5 py-2 text-xs font-medium bg-blue-50 text-blue-700 hover:bg-blue-100 rounded-lg text-center transition"
            >
              👔 Manager
            </button>
            <button
              type="button"
              onClick={() => fillCredentials('employee@gmail.com', 'employee123')}
              className="px-2.5 py-2 text-xs font-medium bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded-lg text-center transition"
            >
              💻 Employee
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// -------------------------------------------------------------
// 2. DASHBOARD TAB
// -------------------------------------------------------------
function DashboardTab({ user, employee, showToast, setActiveTab }) {
  const [summary, setSummary] = useState(null);
  const [overview, setOverview] = useState(null);
  const [leaveBalances, setLeaveBalances] = useState([]);
  const [loading, setLoading] = useState(true);
  const [clockLoading, setClockLoading] = useState(false);

  const loadData = useCallback(async () => {
    try {
      if (employee) {
        const sum = await api('/dashboard/my-summary');
        setSummary(sum);
        const balances = await api('/leaves/balances');
        setLeaveBalances(balances);
      }
      if (user?.role === 'Admin' || user?.role === 'HR') {
        const ov = await api('/dashboard/overview');
        setOverview(ov);
      }
    } catch (e) {
      // Handled
    } finally {
      setLoading(false);
    }
  }, [employee, user]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleClockAction = async (action) => {
    setClockLoading(true);
    try {
      await api(`/attendance/${action}`, 'POST');
      showToast(action === 'clock-in' ? 'Successfully clocked in!' : 'Successfully clocked out!');
      loadData();
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setClockLoading(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-slate-400 font-medium">Loading Dashboard...</div>;
  }

  const isClockedIn = summary?.today_attendance?.clocked_in;
  const checkInTime = summary?.today_attendance?.check_in;
  const checkOutTime = summary?.today_attendance?.check_out;
  const attendanceStatus = summary?.today_attendance?.status;
  const attendanceRemarks = summary?.today_attendance?.remarks;

  return (
    <div className="space-y-6">
      {/* Top Welcome & Clock In Card */}
      <div className="bg-gradient-to-r from-indigo-900 to-indigo-700 rounded-2xl p-6 sm:p-8 text-white shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <h2 className="text-2xl sm:text-3xl font-bold">
              Hi, {summary?.employee_name || (employee ? employee.firstname : (user?.name || user?.email))}!
            </h2>
            <p className="text-indigo-200 text-sm mt-1">
              {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
            </p>
          </div>

          <div className="bg-white/10 backdrop-blur-md p-4 rounded-xl flex items-center space-x-4 border border-white/15">
            <div>
              <p className="text-xs text-indigo-200 uppercase font-semibold">Today's Attendance (IST)</p>
              <div className="flex items-center space-x-2 mt-1">
                <span className={`w-2.5 h-2.5 rounded-full ${
                  !isClockedIn ? 'bg-slate-300' :
                  attendanceStatus === 'Late' ? 'bg-amber-400 animate-pulse' : 'bg-emerald-400 animate-pulse'
                }`}></span>
                <span className="font-semibold text-sm">
                  {isClockedIn 
                    ? (checkOutTime 
                        ? `Shift Done (${new Date(checkOutTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true })})` 
                        : `In: ${new Date(checkInTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true })}`)
                    : 'Not Clocked In'}
                </span>
                {isClockedIn && (
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                    attendanceStatus === 'On Time' ? 'bg-emerald-500/80 text-white' :
                    attendanceStatus === 'Late' ? 'bg-amber-500/90 text-white' : 'bg-white/20 text-white'
                  }`}>
                    {attendanceStatus === 'On Time' ? '✓ On Time' : attendanceStatus === 'Late' ? '⚠️ Late' : attendanceStatus}
                  </span>
                )}
              </div>
              {attendanceRemarks && (
                <p className="text-[11px] text-indigo-200 mt-1 max-w-xs truncate">{attendanceRemarks}</p>
              )}
            </div>

            <div className="flex space-x-2">
              {!isClockedIn ? (
                <button
                  onClick={() => handleClockAction('clock-in')}
                  disabled={clockLoading}
                  className="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold text-xs rounded-lg shadow-sm transition disabled:opacity-50"
                >
                  {clockLoading ? 'Processing...' : '⏱️ Clock In'}
                </button>
              ) : !checkOutTime ? (
                <button
                  onClick={() => handleClockAction('clock-out')}
                  disabled={clockLoading}
                  className="px-4 py-2 bg-rose-500 hover:bg-rose-600 text-white font-semibold text-xs rounded-lg shadow-sm transition disabled:opacity-50"
                >
                  {clockLoading ? 'Processing...' : '⏱️ Clock Out'}
                </button>
              ) : (
                <span className="px-3 py-2 bg-white/20 text-xs rounded-lg font-medium">Logged Out</span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Employee Identity & Profile Info Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
        <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-100">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
            👤 Employee Profile Dossier
          </span>
          <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700">
            {user?.role || 'Employee'}
          </span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase">Employee Name</p>
            <p className="text-sm sm:text-base font-bold text-slate-800 mt-0.5">
              {summary?.employee_name || (employee ? `${employee.firstname} ${employee.lastname || ''}`.trim() : (user?.name || user?.email))}
            </p>
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase">Employee ID (Emp ID)</p>
            <p className="text-sm sm:text-base font-bold text-indigo-600 mt-0.5 font-mono">
              {summary?.employee_code || employee?.employee_code || `EMP-${1000 + (user?.id || 1)}`}
            </p>
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase">Employee Email (Emp Mail)</p>
            <p className="text-xs sm:text-sm font-semibold text-slate-700 mt-0.5 truncate">
              {summary?.employee_email || employee?.email || user?.email}
            </p>
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase">Department & Designation</p>
            <p className="text-xs sm:text-sm font-semibold text-slate-700 mt-0.5">
              {summary?.department || 'Engineering'} • {summary?.designation || 'Software Engineer'}
            </p>
          </div>
        </div>
      </div>

      {/* Admin / HR Company Overview */}
      {overview && (
        <div className="space-y-3">
          <h3 className="text-sm font-bold text-slate-700 uppercase tracking-wider">Company Overview</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <p className="text-xs font-semibold text-slate-400 uppercase">Total Employees</p>
              <p className="text-2xl font-bold text-slate-800 mt-1">{overview.total_employees}</p>
            </div>
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <p className="text-xs font-semibold text-slate-400 uppercase">Departments</p>
              <p className="text-2xl font-bold text-slate-800 mt-1">{overview.total_departments}</p>
            </div>
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <p className="text-xs font-semibold text-slate-400 uppercase">Present Today</p>
              <p className="text-2xl font-bold text-emerald-600 mt-1">{overview.today_attendance?.present || 0}</p>
            </div>
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <p className="text-xs font-semibold text-slate-400 uppercase">Pending Approvals</p>
              <p className="text-2xl font-bold text-amber-600 mt-1">
                {(overview.pending_approvals?.leaves || 0) + (overview.pending_approvals?.wfh || 0)}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Employee Personal Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div 
            onClick={() => setActiveTab('leaves')}
            className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm cursor-pointer hover:border-indigo-300 transition"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase">Pending Leave Requests</p>
                <p className="text-2xl font-bold text-slate-800 mt-1">{summary.pending_requests?.leaves || 0}</p>
              </div>
              <span className="text-2xl">🏖️</span>
            </div>
            <p className="text-xs text-indigo-600 font-medium mt-3">View all leaves →</p>
          </div>

          <div 
            onClick={() => setActiveTab('wfh')}
            className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm cursor-pointer hover:border-indigo-300 transition"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase">Pending WFH Requests</p>
                <p className="text-2xl font-bold text-slate-800 mt-1">{summary.pending_requests?.wfh || 0}</p>
              </div>
              <span className="text-2xl">🏠</span>
            </div>
            <p className="text-xs text-indigo-600 font-medium mt-3">View WFH requests →</p>
          </div>

          <div 
            onClick={() => setActiveTab('notifications')}
            className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm cursor-pointer hover:border-indigo-300 transition"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase">Unread Notifications</p>
                <p className="text-2xl font-bold text-indigo-600 mt-1">{summary.unread_notifications || 0}</p>
              </div>
              <span className="text-2xl">🔔</span>
            </div>
            <p className="text-xs text-indigo-600 font-medium mt-3">Open notifications →</p>
          </div>
        </div>
      )}

      {/* Leave Balances Grid */}
      {leaveBalances.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-slate-800 text-base">My Leave Balances</h3>
            <button 
              onClick={() => setActiveTab('leaves')}
              className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 transition"
            >
              Apply Leave
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {leaveBalances.map((b, idx) => {
              const remaining = b.remaining_days;
              const quota = b.annual_quota;
              const used = b.used_days;
              const leaveName = b.leave_type_name || b.leave_type || (idx === 0 ? "Casual Leave" : "Sick Leave");
              const pct = quota > 0 ? Math.min(100, Math.round((used / quota) * 100)) : 0;
              return (
                <div key={b.leave_type_id || idx} className="p-4 rounded-xl bg-slate-50 border border-slate-100">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-semibold text-sm text-slate-800">{leaveName}</span>
                    <span className="text-xs font-bold text-indigo-600">{remaining} left</span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-2 mb-2">
                    <div 
                      className={`h-2 rounded-full ${pct > 80 ? 'bg-rose-500' : 'bg-indigo-600'}`}
                      style={{ width: `${pct}%` }}
                    ></div>
                  </div>
                  <div className="flex justify-between text-[11px] text-slate-400 font-medium">
                    <span>Used: {used} days</span>
                    <span>Quota: {quota} days</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

// -------------------------------------------------------------
// 3. ATTENDANCE TAB
// -------------------------------------------------------------
function AttendanceTab({ employee, isAdminOrHR, showToast }) {
  const [history, setHistory] = useState([]);
  const [todayAtt, setTodayAtt] = useState(null);
  const [loading, setLoading] = useState(true);
  const [clockLoading, setClockLoading] = useState(false);

  const loadAttendance = useCallback(async () => {
    try {
      if (employee) {
        const hist = await api('/attendance/my-history');
        setHistory(hist);
        try {
          const t = await api('/attendance/today');
          setTodayAtt(t);
        } catch {
          setTodayAtt(null);
        }
      }
    } catch (err) {
      //
    } finally {
      setLoading(false);
    }
  }, [employee]);

  useEffect(() => {
    loadAttendance();
  }, [loadAttendance]);

  const handleClockAction = async (action) => {
    setClockLoading(true);
    try {
      await api(`/attendance/${action}`, 'POST');
      showToast(action === 'clock-in' ? 'Clocked in successfully!' : 'Clocked out successfully!');
      loadAttendance();
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setClockLoading(false);
    }
  };

  const handleExportCSV = async () => {
    try {
      const blob = await api('/attendance/export-csv');
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `attendance_report_${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      showToast('Attendance report downloaded');
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  return (
    <div className="space-y-6">
      {/* Action Banner */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Time & Attendance</h2>
          <p className="text-xs text-slate-400 mt-0.5">Manage daily clock-in records and view attendance history</p>
        </div>

        <div className="flex items-center space-x-3">
          {employee && (
            todayAtt && todayAtt.check_in ? (
              !todayAtt.check_out ? (
                <button
                  onClick={() => handleClockAction('clock-out')}
                  disabled={clockLoading}
                  className="px-4 py-2.5 bg-rose-600 hover:bg-rose-700 text-white font-semibold text-xs rounded-xl shadow-sm transition disabled:opacity-50"
                >
                  {clockLoading ? 'Processing...' : '⏱️ Clock Out'}
                </button>
              ) : (
                <span className="px-3 py-2 bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-semibold rounded-xl">
                  ✓ Completed for Today
                </span>
              )
            ) : (
              <button
                onClick={() => handleClockAction('clock-in')}
                disabled={clockLoading}
                className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl shadow-sm transition disabled:opacity-50"
              >
                {clockLoading ? 'Processing...' : '⏱️ Clock In'}
              </button>
            )
          )}

          {isAdminOrHR && (
            <button
              onClick={handleExportCSV}
              className="px-4 py-2.5 bg-slate-800 hover:bg-slate-900 text-white font-semibold text-xs rounded-xl shadow-sm transition"
            >
              📥 Export CSV
            </button>
          )}
        </div>
      </div>

      {/* History Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <h3 className="font-bold text-slate-800 text-sm">My Attendance Records</h3>
          <span className="text-xs text-slate-400">{history.length} records found</span>
        </div>

        {loading ? (
          <div className="p-8 text-center text-slate-400">Loading records...</div>
        ) : history.length === 0 ? (
          <div className="p-8 text-center text-slate-400">No attendance logs found yet.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-700">
              <thead className="bg-slate-50 text-xs uppercase text-slate-400 font-semibold border-b border-slate-100">
                <tr>
                  <th className="px-6 py-3">Date</th>
                  <th className="px-6 py-3">Clock In</th>
                  <th className="px-6 py-3">Clock Out</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3">Remarks</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {history.map((rec) => (
                  <tr key={rec.id} className="hover:bg-slate-50/50">
                    <td className="px-6 py-3.5 font-medium text-slate-800">{rec.attendance_date}</td>
                    <td className="px-6 py-3.5 font-mono text-xs">
                      {rec.check_in ? new Date(rec.check_in).toLocaleTimeString() : '-'}
                    </td>
                    <td className="px-6 py-3.5 font-mono text-xs">
                      {rec.check_out ? new Date(rec.check_out).toLocaleTimeString() : '-'}
                    </td>
                    <td className="px-6 py-3.5">
                      <span className="inline-flex px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800">
                        {rec.status}
                      </span>
                    </td>
                    <td className="px-6 py-3.5 text-xs text-slate-500">{rec.remarks || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

// -------------------------------------------------------------
// 4. LEAVES TAB
// -------------------------------------------------------------
function LeavesTab({ employee, isManager, showToast }) {
  const [balances, setBalances] = useState([]);
  const [myLeaves, setMyLeaves] = useState([]);
  const [pendingLeaves, setPendingLeaves] = useState([]);
  const [leaveTypes, setLeaveTypes] = useState([]);
  const [modalOpen, setModalOpen] = useState(false);

  // Form State
  const [leaveTypeId, setLeaveTypeId] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [reason, setReason] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadAll = useCallback(async () => {
    try {
      if (employee) {
        const b = await api('/leaves/balances');
        setBalances(b);
        const l = await api('/leaves/my-leaves');
        setMyLeaves(l);
      }
      const types = await api('/leaves/types');
      setLeaveTypes(types);
      if (types.length > 0) setLeaveTypeId(types[0].id);

      if (isManager) {
        const p = await api('/leaves/pending');
        setPendingLeaves(p);
      }
    } catch {
      //
    }
  }, [employee, isManager]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  const handleApply = async (e) => {
    e.preventDefault();
    if (!leaveTypeId || !startDate || !endDate || !reason) {
      return showToast('Please fill all fields', 'error');
    }
    setSubmitting(true);
    try {
      await api('/leaves/apply', 'POST', {
        leave_type_id: parseInt(leaveTypeId),
        start_date: startDate,
        end_date: endDate,
        reason
      });
      showToast('Leave request submitted successfully!');
      setModalOpen(false);
      setReason('');
      loadAll();
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const handleReview = async (leaveId, action) => {
    const finalAction = (action === 'approve' || action === 'approved') ? 'approved' : 'rejected';
    const comments = prompt(`Enter comments for ${finalAction}:`, finalAction === 'approved' ? 'Approved' : 'Rejected');
    if (comments === null) return;
    try {
      await api(`/leaves/${leaveId}/review`, 'POST', { action: finalAction, comments: comments || (finalAction === 'approved' ? 'Approved' : 'Rejected') });
      showToast(`Leave request ${finalAction} successfully!`);
      loadAll();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Leave Management</h2>
          <p className="text-xs text-slate-400 mt-0.5">Apply for annual, sick, or personal leaves and track status</p>
        </div>
        <button
          onClick={() => setModalOpen(true)}
          className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl shadow-sm transition"
        >
          + Apply for Leave
        </button>
      </div>

      {/* Balances */}
      {balances.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {balances.map((b, idx) => {
            const leaveName = b.leave_type_name || b.leave_type || (idx === 0 ? "Casual Leave" : "Sick Leave");
            return (
              <div key={b.leave_type_id || idx} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <div className="flex justify-between items-center mb-1">
                  <span className="font-bold text-slate-800 text-sm">{leaveName}</span>
                  <span className="text-xs font-bold px-2 py-0.5 rounded bg-indigo-50 text-indigo-700">
                    {b.remaining_days} remaining
                  </span>
                </div>
                <p className="text-xs text-slate-400 mb-3">Annual Quota: {b.annual_quota} days</p>
                <div className="w-full bg-slate-100 rounded-full h-1.5">
                  <div 
                    className="h-1.5 rounded-full bg-indigo-600"
                    style={{ width: `${b.annual_quota > 0 ? (b.used_days / b.annual_quota) * 100 : 0}%` }}
                  ></div>
                </div>
                <div className="flex justify-between text-[11px] text-slate-400 mt-2 font-medium">
                  <span>Used: {b.used_days}</span>
                  <span>Quota: {b.annual_quota}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Manager Approvals Queue */}
      {isManager && pendingLeaves.length > 0 && (
        <div className="bg-white rounded-xl border border-amber-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 bg-amber-50/50 border-b border-amber-100 flex items-center justify-between">
            <h3 className="font-bold text-amber-900 text-sm">Pending Team Approvals ({pendingLeaves.length})</h3>
            <span className="text-xs text-amber-700 font-medium">Requires Manager Action</span>
          </div>
          <div className="divide-y divide-slate-100">
            {pendingLeaves.map((req) => (
              <div key={req.id} className="p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-slate-800 text-sm">Leave #{req.id}</span>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded bg-indigo-100 text-indigo-800">
                      Emp ID: {req.employee_id}
                    </span>
                    <span className="text-xs text-slate-500">
                      {req.start_date} to {req.end_date}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600"><strong>Reason:</strong> {req.reason}</p>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleReview(req.id, 'approve')}
                    className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs rounded-lg transition"
                  >
                    ✓ Approve
                  </button>
                  <button
                    onClick={() => handleReview(req.id, 'reject')}
                    className="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white font-semibold text-xs rounded-lg transition"
                  >
                    ✕ Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* My Leaves Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100">
          <h3 className="font-bold text-slate-800 text-sm">My Leave Applications</h3>
        </div>
        {myLeaves.length === 0 ? (
          <div className="p-8 text-center text-slate-400">No leave requests found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-700">
              <thead className="bg-slate-50 text-xs uppercase text-slate-400 font-semibold border-b border-slate-100">
                <tr>
                  <th className="px-6 py-3">Applied</th>
                  <th className="px-6 py-3">Dates</th>
                  <th className="px-6 py-3">Days</th>
                  <th className="px-6 py-3">Reason</th>
                  <th className="px-6 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {myLeaves.map((l) => (
                  <tr key={l.id} className="hover:bg-slate-50/50">
                    <td className="px-6 py-3.5 text-xs text-slate-500">
                      {l.applied_at ? new Date(l.applied_at).toLocaleDateString() : '-'}
                    </td>
                    <td className="px-6 py-3.5 font-medium text-slate-800">
                      {l.start_date} → {l.end_date}
                    </td>
                    <td className="px-6 py-3.5 text-xs font-semibold">{l.total_days}</td>
                    <td className="px-6 py-3.5 text-xs text-slate-500">{l.reason}</td>
                    <td className="px-6 py-3.5">
                      <span className={`inline-flex px-2 py-0.5 rounded text-xs font-semibold ${
                        l.status === 'approved' ? 'bg-emerald-100 text-emerald-800' :
                        l.status === 'rejected' ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800'
                      }`}>
                        {l.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-100">
            <h3 className="text-lg font-bold text-slate-800 mb-4">Apply for Leave</h3>
            <form onSubmit={handleApply} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Leave Type</label>
                <select
                  value={leaveTypeId}
                  onChange={(e) => setLeaveTypeId(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
                  required
                >
                  {leaveTypes.map((t) => (
                    <option key={t.id} value={t.id}>{t.name} ({t.annual_quota} days/yr)</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Start Date</label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">End Date</label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Reason</label>
                <textarea
                  rows="3"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="State the reason for your leave request..."
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
                  required
                ></textarea>
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl shadow-sm transition disabled:opacity-50"
                >
                  {submitting ? 'Submitting...' : 'Submit Application'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

// -------------------------------------------------------------
// 5. WORK FROM HOME (WFH) TAB
// -------------------------------------------------------------
function WFHTab({ employee, isManager, showToast }) {
  const [myWfh, setMyWfh] = useState([]);
  const [pendingWfh, setPendingWfh] = useState([]);
  const [modalOpen, setModalOpen] = useState(false);

  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [reason, setReason] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadAll = useCallback(async () => {
    try {
      if (employee) {
        const w = await api('/wfh/my-requests');
        setMyWfh(w);
      }
      if (isManager) {
        const p = await api('/wfh/pending');
        setPendingWfh(p);
      }
    } catch {
      //
    }
  }, [employee, isManager]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  const handleApply = async (e) => {
    e.preventDefault();
    if (!startDate || !endDate || !reason) return showToast('Please fill all fields', 'error');

    setSubmitting(true);
    try {
      await api('/wfh/apply', 'POST', { start_date: startDate, end_date: endDate, reason });
      showToast('WFH request submitted successfully!');
      setModalOpen(false);
      setReason('');
      loadAll();
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const handleReview = async (wfhId, action) => {
    const finalAction = (action === 'approve' || action === 'approved') ? 'approved' : 'rejected';
    const comments = prompt(`Enter review comment for ${finalAction}:`, finalAction === 'approved' ? 'Approved' : 'Rejected');
    if (comments === null) return;
    try {
      await api(`/wfh/${wfhId}/review`, 'POST', { action: finalAction, comments: comments || (finalAction === 'approved' ? 'Approved' : 'Rejected') });
      showToast(`WFH request ${finalAction} successfully!`);
      loadAll();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Work From Home (WFH)</h2>
          <p className="text-xs text-slate-400 mt-0.5">Request remote working days and track approval status</p>
        </div>
        <button
          onClick={() => setModalOpen(true)}
          className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl shadow-sm transition"
        >
          + Request WFH
        </button>
      </div>

      {/* Manager Approvals */}
      {isManager && pendingWfh.length > 0 && (
        <div className="bg-white rounded-xl border border-amber-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 bg-amber-50/50 border-b border-amber-100 flex items-center justify-between">
            <h3 className="font-bold text-amber-900 text-sm">Pending Team WFH Requests ({pendingWfh.length})</h3>
            <span className="text-xs text-amber-700 font-medium">Requires Action</span>
          </div>
          <div className="divide-y divide-slate-100">
            {pendingWfh.map((req) => (
              <div key={req.id} className="p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-slate-800 text-sm">Request #{req.id}</span>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded bg-indigo-100 text-indigo-800">
                      Emp ID: {req.employee_id}
                    </span>
                    <span className="text-xs text-slate-500">{req.start_date} to {req.end_date}</span>
                  </div>
                  <p className="text-xs text-slate-600"><strong>Reason:</strong> {req.reason}</p>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleReview(req.id, 'approve')}
                    className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs rounded-lg transition"
                  >
                    ✓ Approve
                  </button>
                  <button
                    onClick={() => handleReview(req.id, 'reject')}
                    className="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white font-semibold text-xs rounded-lg transition"
                  >
                    ✕ Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* My Requests Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100">
          <h3 className="font-bold text-slate-800 text-sm">My WFH Requests</h3>
        </div>
        {myWfh.length === 0 ? (
          <div className="p-8 text-center text-slate-400">No WFH requests found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-700">
              <thead className="bg-slate-50 text-xs uppercase text-slate-400 font-semibold border-b border-slate-100">
                <tr>
                  <th className="px-6 py-3">Applied</th>
                  <th className="px-6 py-3">Dates</th>
                  <th className="px-6 py-3">Reason</th>
                  <th className="px-6 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {myWfh.map((w) => (
                  <tr key={w.id} className="hover:bg-slate-50/50">
                    <td className="px-6 py-3.5 text-xs text-slate-500">
                      {w.applied_at ? new Date(w.applied_at).toLocaleDateString() : '-'}
                    </td>
                    <td className="px-6 py-3.5 font-medium text-slate-800">
                      {w.start_date} → {w.end_date}
                    </td>
                    <td className="px-6 py-3.5 text-xs text-slate-500">{w.reason}</td>
                    <td className="px-6 py-3.5">
                      <span className={`inline-flex px-2 py-0.5 rounded text-xs font-semibold ${
                        w.status === 'approved' ? 'bg-emerald-100 text-emerald-800' :
                        w.status === 'rejected' ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800'
                      }`}>
                        {w.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-100">
            <h3 className="text-lg font-bold text-slate-800 mb-4">Request Work From Home</h3>
            <form onSubmit={handleApply} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Start Date</label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">End Date</label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Reason</label>
                <textarea
                  rows="3"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="State the reason for your WFH request..."
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
                  required
                ></textarea>
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl shadow-sm transition disabled:opacity-50"
                >
                  {submitting ? 'Submitting...' : 'Submit Request'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

// -------------------------------------------------------------
// 6. HOLIDAYS TAB
// -------------------------------------------------------------
function HolidaysTab({ isAdminOrHR, showToast }) {
  const [holidays, setHolidays] = useState([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [name, setName] = useState('');
  const [date, setDate] = useState('');
  const [desc, setDesc] = useState('');

  const loadHolidays = useCallback(async () => {
    try {
      const h = await api('/holidays/');
      setHolidays(h);
    } catch {
      //
    }
  }, []);

  useEffect(() => {
    loadHolidays();
  }, [loadHolidays]);

  const handleAdd = async (e) => {
    e.preventDefault();
    try {
      await api('/holidays/', 'POST', { holiday_name: name, holiday_date: date, description: desc });
      showToast('Holiday added successfully!');
      setModalOpen(false);
      setName('');
      setDate('');
      setDesc('');
      loadHolidays();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to delete this holiday?')) return;
    try {
      await api(`/holidays/${id}`, 'DELETE');
      showToast('Holiday deleted');
      loadHolidays();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Company Holidays</h2>
          <p className="text-xs text-slate-400 mt-0.5">Upcoming recognized annual public and corporate holidays</p>
        </div>
        {isAdminOrHR && (
          <button
            onClick={() => setModalOpen(true)}
            className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl shadow-sm transition"
          >
            + Add Holiday
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {holidays.map((h) => (
          <div key={h.id} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm relative group">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-xs font-bold text-indigo-600 font-mono">
                  {new Date(h.holiday_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                </span>
                <h4 className="font-bold text-slate-800 text-base mt-1">{h.holiday_name}</h4>
                <p className="text-xs text-slate-500 mt-1">{h.description || 'Public holiday'}</p>
              </div>
              <span className="text-2xl">🎉</span>
            </div>

            {isAdminOrHR && (
              <button
                onClick={() => handleDelete(h.id)}
                className="text-xs text-rose-500 hover:text-rose-700 font-medium mt-4 transition"
              >
                Delete
              </button>
            )}
          </div>
        ))}
      </div>

      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-100">
            <h3 className="text-lg font-bold text-slate-800 mb-4">Add Holiday</h3>
            <form onSubmit={handleAdd} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Holiday Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
                  placeholder="e.g. New Year's Day"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Date</label>
                <input
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Description</label>
                <input
                  type="text"
                  value={desc}
                  onChange={(e) => setDesc(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
                  placeholder="e.g. National holiday"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl shadow-sm transition"
                >
                  Save Holiday
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

// -------------------------------------------------------------
// 7. NOTIFICATIONS TAB
// -------------------------------------------------------------
function NotificationsTab({ onUpdate, showToast }) {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadNotifications = useCallback(async () => {
    try {
      const data = await api('/notifications/');
      setNotifications(data);
      onUpdate();
    } catch {
      //
    } finally {
      setLoading(false);
    }
  }, [onUpdate]);

  useEffect(() => {
    loadNotifications();
  }, [loadNotifications]);

  const markRead = async (id) => {
    try {
      await api(`/notifications/${id}/read`, 'PATCH');
      loadNotifications();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const markAllRead = async () => {
    try {
      await api('/notifications/read-all', 'PATCH');
      showToast('All notifications marked as read');
      loadNotifications();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Notifications</h2>
          <p className="text-xs text-slate-400 mt-0.5">Alerts, leave approval decisions, and company announcements</p>
        </div>
        <button
          onClick={markAllRead}
          className="px-4 py-2 text-xs font-semibold text-indigo-600 hover:bg-indigo-50 border border-indigo-200 rounded-xl transition"
        >
          ✓ Mark All as Read
        </button>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden divide-y divide-slate-100">
        {loading ? (
          <div className="p-8 text-center text-slate-400">Loading notifications...</div>
        ) : notifications.length === 0 ? (
          <div className="p-8 text-center text-slate-400">No notifications found.</div>
        ) : (
          notifications.map((n) => (
            <div key={n.id} className={`p-5 flex items-start justify-between gap-4 transition ${n.is_read ? 'bg-white' : 'bg-indigo-50/40'}`}>
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <h4 className={`text-sm ${n.is_read ? 'font-medium text-slate-700' : 'font-bold text-slate-900'}`}>{n.title}</h4>
                  {!n.is_read && (
                    <span className="w-2 h-2 rounded-full bg-indigo-600"></span>
                  )}
                </div>
                <p className="text-xs text-slate-600">{n.message}</p>
                <p className="text-[11px] text-slate-400 font-mono">
                  {new Date(n.created_at).toLocaleString()}
                </p>
              </div>

              {!n.is_read && (
                <button
                  onClick={() => markRead(n.id)}
                  className="px-3 py-1 text-xs font-semibold text-slate-500 hover:text-indigo-600 hover:bg-white rounded-lg border border-slate-200 transition whitespace-nowrap"
                >
                  Mark Read
                </button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

// -------------------------------------------------------------
// 8. EMPLOYEES TAB (Admin / HR)
// -------------------------------------------------------------
function EmployeesTab({ showToast }) {
  const [employees, setEmployees] = useState([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  // Form State
  const [code, setCode] = useState('');
  const [fname, setFname] = useState('');
  const [lname, setLname] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [deptId, setDeptId] = useState(1);
  const [desigId, setDesigId] = useState(1);
  const [mgrId, setMgrId] = useState('');
  const [joiningDate, setJoiningDate] = useState(new Date().toISOString().slice(0, 10));

  const loadEmployees = useCallback(async () => {
    try {
      const data = await api('/employees/');
      setEmployees(data);
    } catch {
      //
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadEmployees();
  }, [loadEmployees]);

  const handleOnboard = async (e) => {
    e.preventDefault();
    try {
      await api('/employees/', 'POST', {
        employee_code: code,
        firstname: fname,
        lastname: lname,
        email,
        phone,
        department_id: parseInt(deptId),
        designation_id: parseInt(desigId),
        manager_id: mgrId ? parseInt(mgrId) : null,
        joining_date: joiningDate
      });
      showToast('Employee onboarded successfully!');
      setModalOpen(false);
      setCode('');
      setFname('');
      setLname('');
      setEmail('');
      setPhone('');
      loadEmployees();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Employee Directory</h2>
          <p className="text-xs text-slate-400 mt-0.5">Manage workforce profiles, department assignments, and reporting managers</p>
        </div>
        <button
          onClick={() => setModalOpen(true)}
          className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl shadow-sm transition"
        >
          + Onboard Employee
        </button>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-slate-400">Loading directory...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-700">
              <thead className="bg-slate-50 text-xs uppercase text-slate-400 font-semibold border-b border-slate-100">
                <tr>
                  <th className="px-6 py-3">Code</th>
                  <th className="px-6 py-3">Name</th>
                  <th className="px-6 py-3">Email</th>
                  <th className="px-6 py-3">Dept ID</th>
                  <th className="px-6 py-3">Desig ID</th>
                  <th className="px-6 py-3">Manager ID</th>
                  <th className="px-6 py-3">Joined</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {employees.map((emp) => (
                  <tr key={emp.id} className="hover:bg-slate-50/50">
                    <td className="px-6 py-3.5 font-mono text-xs font-bold text-indigo-600">{emp.employee_code}</td>
                    <td className="px-6 py-3.5 font-medium text-slate-900">{emp.firstname} {emp.lastname}</td>
                    <td className="px-6 py-3.5 text-xs text-slate-500">{emp.email}</td>
                    <td className="px-6 py-3.5 text-xs font-semibold">{emp.department_id}</td>
                    <td className="px-6 py-3.5 text-xs font-semibold">{emp.designation_id}</td>
                    <td className="px-6 py-3.5 text-xs text-slate-500">{emp.manager_id || 'None'}</td>
                    <td className="px-6 py-3.5 text-xs text-slate-500">{emp.joining_date}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-100 my-8">
            <h3 className="text-lg font-bold text-slate-800 mb-4">Onboard New Employee</h3>
            <form onSubmit={handleOnboard} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">First Name</label>
                  <input
                    type="text"
                    value={fname}
                    onChange={(e) => setFname(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Last Name</label>
                  <input
                    type="text"
                    value={lname}
                    onChange={(e) => setLname(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Employee Code</label>
                <input
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
                  placeholder="e.g. EMP-101"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Phone</label>
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
                />
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Dept ID</label>
                  <input
                    type="number"
                    value={deptId}
                    onChange={(e) => setDeptId(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Desig ID</label>
                  <input
                    type="number"
                    value={desigId}
                    onChange={(e) => setDesigId(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Manager ID</label>
                  <input
                    type="number"
                    value={mgrId}
                    onChange={(e) => setMgrId(e.target.value)}
                    placeholder="Optional"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Joining Date</label>
                <input
                  type="date"
                  value={joiningDate}
                  onChange={(e) => setJoiningDate(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
                  required
                />
              </div>

              <div className="flex justify-end space-x-2 pt-3">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl shadow-sm transition"
                >
                  Onboard
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

// Mount React Root
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
