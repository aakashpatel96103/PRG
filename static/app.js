/**
 * StaffPulse - Frontend Application Logic
 * Fast, reactive JavaScript for CRUD operations, JWT Auth, and Cluster Health checks.
 */

// Application State
const state = {
  token: localStorage.getItem("ems_token") || null,
  user: JSON.parse(localStorage.getItem("ems_user") || "null"),
  employees: [],
  stats: null,
  searchQuery: "",
  departmentFilter: "",
  statusFilter: "",
  editingEmployeeId: null,
};

// DOM Element References
const elements = {
  // Stats
  statTotalEmployees: document.getElementById("statTotalEmployees"),
  statActiveRatio: document.getElementById("statActiveRatio"),
  statTotalPayroll: document.getElementById("statTotalPayroll"),
  statAvgSalary: document.getElementById("statAvgSalary"),
  statTotalDepts: document.getElementById("statTotalDepts"),
  deptBreakdown: document.getElementById("deptBreakdown"),
  statDbPing: document.getElementById("statDbPing"),
  k8sProbeBadge: document.getElementById("k8sProbeBadge"),

  // Health
  healthPill: document.getElementById("healthPill"),
  healthStatusText: document.getElementById("healthStatusText"),

  // User Widget & Navigation
  userProfileWidget: document.getElementById("userProfileWidget"),

  // Controls & Table
  searchInput: document.getElementById("searchInput"),
  departmentFilter: document.getElementById("departmentFilter"),
  statusFilter: document.getElementById("statusFilter"),
  refreshBtn: document.getElementById("refreshBtn"),
  addEmployeeBtn: document.getElementById("addEmployeeBtn"),
  employeesTbody: document.getElementById("employeesTbody"),
  emptyState: document.getElementById("emptyState"),
  emptyAddBtn: document.getElementById("emptyAddBtn"),
  loadingState: document.getElementById("loadingState"),

  // Employee Modal
  employeeModalBackdrop: document.getElementById("employeeModalBackdrop"),
  employeeModalTitle: document.getElementById("employeeModalTitle"),
  closeEmployeeModalBtn: document.getElementById("closeEmployeeModalBtn"),
  cancelEmployeeModalBtn: document.getElementById("cancelEmployeeModalBtn"),
  employeeForm: document.getElementById("employeeForm"),
  employeeId: document.getElementById("employeeId"),
  empFullName: document.getElementById("empFullName"),
  empEmail: document.getElementById("empEmail"),
  empDepartment: document.getElementById("empDepartment"),
  empPosition: document.getElementById("empPosition"),
  empSalary: document.getElementById("empSalary"),
  empPhone: document.getElementById("empPhone"),
  empStatus: document.getElementById("empStatus"),

  // Auth Modal
  authModalBackdrop: document.getElementById("authModalBackdrop"),
  closeAuthModalBtn: document.getElementById("closeAuthModalBtn"),
  tabSignIn: document.getElementById("tabSignIn"),
  tabRegister: document.getElementById("tabRegister"),
  loginForm: document.getElementById("loginForm"),
  registerForm: document.getElementById("registerForm"),
  loginUsername: document.getElementById("loginUsername"),
  loginPassword: document.getElementById("loginPassword"),
  regFullName: document.getElementById("regFullName"),
  regUsername: document.getElementById("regUsername"),
  regPassword: document.getElementById("regPassword"),
  cancelLoginBtn: document.getElementById("cancelLoginBtn"),
  cancelRegisterBtn: document.getElementById("cancelRegisterBtn"),

  // Metrics Modal
  metricsModalBackdrop: document.getElementById("metricsModalBackdrop"),
  openMetricsModalBtn: document.getElementById("openMetricsModalBtn"),
  closeMetricsModalBtn: document.getElementById("closeMetricsModalBtn"),
  refreshMetricsExcerptBtn: document.getElementById("refreshMetricsExcerptBtn"),
  metricsPre: document.getElementById("metricsPre"),
  readinessStatusHeader: document.getElementById("readinessStatusHeader"),

  // Toast Container
  toastContainer: document.getElementById("toastContainer"),
};

// --------------------------------------------------------------------------
// API Client Helper
// --------------------------------------------------------------------------
async function apiCall(endpoint, options = {}) {
  const headers = options.headers || {};
  if (state.token) {
    headers["Authorization"] = `Bearer ${state.token}`;
  }
  if (options.body && !(options.body instanceof FormData) && typeof options.body === "object") {
    headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(options.body);
  }

  const response = await fetch(endpoint, { ...options, headers });
  
  if (response.status === 401 && endpoint !== "/auth/login") {
    // Session expired or invalid
    clearAuthSession();
    showToast("Session expired. Please sign in again.", "error");
    openAuthModal();
    throw new Error("Unauthorized");
  }

  return response;
}

// --------------------------------------------------------------------------
// Toast Notifications
// --------------------------------------------------------------------------
function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerText = message;
  elements.toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// --------------------------------------------------------------------------
// Health & Observability Polling
// --------------------------------------------------------------------------
async function checkClusterHealth() {
  const startTime = performance.now();
  try {
    const res = await fetch("/health/ready");
    const ping = Math.round(performance.now() - startTime);
    elements.statDbPing.innerText = `${ping} ms`;

    if (res.ok) {
      elements.healthPill.className = "health-pill";
      elements.healthStatusText.innerText = "K8s & DB Healthy";
      elements.k8sProbeBadge.className = "metric-badge positive";
      elements.k8sProbeBadge.innerText = "Readiness: OK";
    } else {
      elements.healthPill.className = "health-pill error";
      elements.healthStatusText.innerText = "DB Not Ready (503)";
      elements.k8sProbeBadge.className = "metric-badge";
      elements.k8sProbeBadge.innerText = "DB Disconnected";
    }
  } catch (err) {
    elements.healthPill.className = "health-pill error";
    elements.healthStatusText.innerText = "Cluster Unreachable";
    elements.statDbPing.innerText = "Timeout";
    elements.k8sProbeBadge.className = "metric-badge";
    elements.k8sProbeBadge.innerText = "Offline";
  }
}

// --------------------------------------------------------------------------
// Authentication Logic
// --------------------------------------------------------------------------
function renderUserWidget() {
  if (state.token && state.user) {
    const isAdmin = state.user.role === "admin";
    elements.userProfileWidget.innerHTML = `
      <div class="user-chip" style="display: flex; align-items: center; gap: 8px; background: rgba(255,255,255,0.05); padding: 5px 12px; border-radius: 20px; border: 1px solid var(--border-color);">
        <div style="width: 26px; height: 26px; border-radius: 50%; background: ${isAdmin ? 'linear-gradient(135deg,#f43f5e,#ec4899)' : 'linear-gradient(135deg,#3b82f6,#6366f1)'}; display: flex; align-items: center; justify-content: center; font-size: 0.72rem; font-weight: bold; color: white;">
          ${state.user.username.charAt(0).toUpperCase()}
        </div>
        <div style="display: flex; flex-direction: column; line-height: 1.1;">
          <span style="font-size: 0.8rem; font-weight: 600;">${state.user.username}</span>
          <span style="font-size: 0.65rem; color: ${isAdmin ? '#fb7185' : '#94a3b8'}; text-transform: uppercase; font-weight: 700;">${state.user.role}</span>
        </div>
        <button id="logoutBtn" class="btn-xs" style="margin-left: 6px; cursor: pointer;">Logout</button>
      </div>
    `;

    document.getElementById("logoutBtn").addEventListener("click", () => {
      clearAuthSession();
      showToast("Signed out successfully", "info");
      loadEmployees();
    });
  } else {
    elements.userProfileWidget.innerHTML = `
      <button class="btn btn-primary" id="openSignInBtn" style="padding: 6px 14px; font-size: 0.82rem;">Sign In</button>
    `;
    document.getElementById("openSignInBtn").addEventListener("click", openAuthModal);
  }
}

function saveAuthSession(token, user) {
  state.token = token;
  state.user = user;
  localStorage.setItem("ems_token", token);
  localStorage.setItem("ems_user", JSON.stringify(user));
  renderUserWidget();
}

function clearAuthSession() {
  state.token = null;
  state.user = null;
  localStorage.removeItem("ems_token");
  localStorage.removeItem("ems_user");
  renderUserWidget();
}

function openAuthModal() {
  elements.authModalBackdrop.classList.add("open");
  switchAuthTab("signin");
}

function closeAuthModal() {
  elements.authModalBackdrop.classList.remove("open");
}

function switchAuthTab(tab) {
  if (tab === "signin") {
    elements.tabSignIn.classList.add("active");
    elements.tabRegister.classList.remove("active");
    elements.loginForm.style.display = "flex";
    elements.registerForm.style.display = "none";
  } else {
    elements.tabRegister.classList.add("active");
    elements.tabSignIn.classList.remove("active");
    elements.loginForm.style.display = "none";
    elements.registerForm.style.display = "flex";
  }
}

// --------------------------------------------------------------------------
// Employee CRUD Operations
// --------------------------------------------------------------------------
async function loadEmployees() {
  elements.loadingState.style.display = "flex";
  try {
    let url = `/employees/?limit=100`;
    if (state.searchQuery) url += `&q=${encodeURIComponent(state.searchQuery)}`;
    if (state.departmentFilter) url += `&department=${encodeURIComponent(state.departmentFilter)}`;
    if (state.statusFilter) url += `&status=${encodeURIComponent(state.statusFilter)}`;

    const res = await apiCall(url);
    if (!res.ok) throw new Error("Failed to fetch employees");
    
    state.employees = await res.json();
    renderEmployeesTable();
    loadStats();
  } catch (err) {
    if (err.message !== "Unauthorized") {
      showToast("Unable to load employees. Sign in to view.", "error");
    }
    state.employees = [];
    renderEmployeesTable();
  } finally {
    elements.loadingState.style.display = "none";
  }
}

async function loadStats() {
  try {
    const res = await apiCall("/employees/stats/summary");
    if (res.ok) {
      const stats = await res.json();
      state.stats = stats;
      elements.statTotalEmployees.innerText = stats.total_employees;
      elements.statTotalPayroll.innerText = `$${stats.total_payroll.toLocaleString()}`;
      elements.statAvgSalary.innerText = `Avg $${Math.round(stats.average_salary).toLocaleString()}`;
      elements.statTotalDepts.innerText = stats.total_departments;

      const activeCount = stats.status_counts["active"] || 0;
      const ratio = stats.total_employees > 0 ? Math.round((activeCount / stats.total_employees) * 100) : 0;
      elements.statActiveRatio.innerText = `${ratio}% active`;
    }
  } catch (err) {
    console.error("Stats load error", err);
  }
}

function renderEmployeesTable() {
  elements.employeesTbody.innerHTML = "";
  if (!state.employees || state.employees.length === 0) {
    elements.emptyState.style.display = "flex";
    return;
  }
  elements.emptyState.style.display = "none";

  const isAdmin = state.user && state.user.role === "admin";

  state.employees.forEach((emp) => {
    const tr = document.createElement("tr");

    // Avatar initials
    const initials = emp.full_name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .substring(0, 2)
      .toUpperCase();

    // Format date
    const hireDate = emp.hired_on ? new Date(emp.hired_on).toLocaleDateString() : "N/A";

    tr.innerHTML = `
      <td>
        <div class="user-cell">
          <div class="user-avatar">${initials}</div>
          <div class="user-meta">
            <span class="user-meta-name">${escapeHtml(emp.full_name)}</span>
            <span class="user-meta-email">${escapeHtml(emp.email)}</span>
          </div>
        </div>
      </td>
      <td><span class="badge badge-department">${escapeHtml(emp.department)}</span></td>
      <td>${escapeHtml(emp.position)}</td>
      <td><span class="salary-val">$${Number(emp.salary).toLocaleString()}</span></td>
      <td><span class="badge badge-${emp.status}">${emp.status.replace("_", " ")}</span></td>
      <td><span class="date-val">${hireDate}</span></td>
      <td class="text-right">
        ${
          isAdmin
            ? `
          <div class="row-actions">
            <button class="icon-btn edit-btn" title="Edit Employee" data-id="${emp.id}">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>
            </button>
            <button class="icon-btn delete delete-btn" title="Delete Employee" data-id="${emp.id}">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
            </button>
          </div>
        `
            : `<span style="font-size: 0.76rem; color: var(--text-muted);">Read-Only</span>`
        }
      </td>
    `;

    elements.employeesTbody.appendChild(tr);
  });

  // Attach action button handlers
  document.querySelectorAll(".edit-btn").forEach((btn) => {
    btn.addEventListener("click", () => openEditEmployeeModal(btn.dataset.id));
  });
  document.querySelectorAll(".delete-btn").forEach((btn) => {
    btn.addEventListener("click", () => handleDeleteEmployee(btn.dataset.id));
  });
}

function openAddEmployeeModal() {
  if (!state.token) {
    showToast("Please sign in to add employees", "info");
    openAuthModal();
    return;
  }
  if (!state.user || state.user.role !== "admin") {
    showToast("Admin privileges required to manage employees", "error");
    return;
  }
  state.editingEmployeeId = null;
  elements.employeeModalTitle.innerText = "Add New Employee";
  elements.employeeForm.reset();
  elements.employeeId.value = "";
  elements.employeeModalBackdrop.classList.add("open");
}

function openEditEmployeeModal(id) {
  const emp = state.employees.find((e) => String(e.id) === String(id));
  if (!emp) return;

  state.editingEmployeeId = emp.id;
  elements.employeeModalTitle.innerText = "Edit Employee";
  elements.employeeId.value = emp.id;
  elements.empFullName.value = emp.full_name;
  elements.empEmail.value = emp.email;
  elements.empDepartment.value = emp.department;
  elements.empPosition.value = emp.position;
  elements.empSalary.value = emp.salary;
  elements.empPhone.value = emp.phone || "";
  elements.empStatus.value = emp.status;

  elements.employeeModalBackdrop.classList.add("open");
}

function closeEmployeeModal() {
  elements.employeeModalBackdrop.classList.remove("open");
}

async function handleDeleteEmployee(id) {
  if (!confirm("Are you sure you want to permanently delete this employee record?")) return;

  try {
    const res = await apiCall(`/employees/${id}`, { method: "DELETE" });
    if (res.status === 204) {
      showToast("Employee deleted successfully", "success");
      loadEmployees();
    } else {
      const err = await res.json();
      showToast(err.detail || "Failed to delete employee", "error");
    }
  } catch (err) {
    showToast("An error occurred while deleting employee", "error");
  }
}

// --------------------------------------------------------------------------
// Observability Modal Logic
// --------------------------------------------------------------------------
async function loadMetricsExcerpt() {
  elements.metricsPre.innerText = "Fetching Prometheus metrics...";
  try {
    const res = await fetch("/metrics");
    if (res.ok) {
      const text = await res.text();
      // Display first 25 relevant lines
      const sample = text.split("\n").filter(l => !l.startsWith("#") && l.trim()).slice(0, 18).join("\n");
      elements.metricsPre.innerText = sample || "Prometheus metrics endpoint is active and scraping.";
    } else {
      elements.metricsPre.innerText = "Metrics endpoint returned HTTP " + res.status;
    }
  } catch (err) {
    elements.metricsPre.innerText = "Error fetching metrics: " + err.message;
  }
}

// Helper: Escape HTML
function escapeHtml(str) {
  if (!str) return "";
  return String(str).replace(/[&<>"']/g, (m) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[m]));
}

// --------------------------------------------------------------------------
// Event Listeners Initialization
// --------------------------------------------------------------------------
function initEventListeners() {
  // Search and Filters
  elements.searchInput.addEventListener("input", (e) => {
    state.searchQuery = e.target.value.trim();
    loadEmployees();
  });
  elements.departmentFilter.addEventListener("change", (e) => {
    state.departmentFilter = e.target.value;
    loadEmployees();
  });
  elements.statusFilter.addEventListener("change", (e) => {
    state.statusFilter = e.target.value;
    loadEmployees();
  });
  elements.refreshBtn.addEventListener("click", () => {
    loadEmployees();
    checkClusterHealth();
    showToast("Refreshed employee list", "info");
  });

  // Modal open/close
  elements.addEmployeeBtn.addEventListener("click", openAddEmployeeModal);
  elements.emptyAddBtn.addEventListener("click", openAddEmployeeModal);
  elements.closeEmployeeModalBtn.addEventListener("click", closeEmployeeModal);
  elements.cancelEmployeeModalBtn.addEventListener("click", closeEmployeeModal);

  elements.closeAuthModalBtn.addEventListener("click", closeAuthModal);
  elements.cancelLoginBtn.addEventListener("click", closeAuthModal);
  elements.cancelRegisterBtn.addEventListener("click", closeAuthModal);
  elements.tabSignIn.addEventListener("click", () => switchAuthTab("signin"));
  elements.tabRegister.addEventListener("click", () => switchAuthTab("register"));

  elements.openMetricsModalBtn.addEventListener("click", () => {
    elements.metricsModalBackdrop.classList.add("open");
    loadMetricsExcerpt();
  });
  elements.closeMetricsModalBtn.addEventListener("click", () => {
    elements.metricsModalBackdrop.classList.remove("open");
  });
  elements.refreshMetricsExcerptBtn.addEventListener("click", loadMetricsExcerpt);

  // Close modals on backdrop click
  window.addEventListener("click", (e) => {
    if (e.target === elements.employeeModalBackdrop) closeEmployeeModal();
    if (e.target === elements.authModalBackdrop) closeAuthModal();
    if (e.target === elements.metricsModalBackdrop) elements.metricsModalBackdrop.classList.remove("open");
  });

  // Form Submissions: Employee Form
  elements.employeeForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      full_name: elements.empFullName.value.trim(),
      email: elements.empEmail.value.trim(),
      department: elements.empDepartment.value.trim(),
      position: elements.empPosition.value.trim(),
      salary: parseFloat(elements.empSalary.value),
      phone: elements.empPhone.value.trim() || null,
      status: elements.empStatus.value,
    };

    const isEdit = Boolean(state.editingEmployeeId);
    const url = isEdit ? `/employees/${state.editingEmployeeId}` : `/employees/`;
    const method = isEdit ? "PUT" : "POST";

    try {
      const res = await apiCall(url, { method, body: payload });
      if (res.ok) {
        showToast(`Employee ${isEdit ? "updated" : "created"} successfully!`, "success");
        closeEmployeeModal();
        loadEmployees();
      } else {
        const err = await res.json();
        showToast(err.detail || "Failed to save employee", "error");
      }
    } catch (err) {
      showToast("Error processing request", "error");
    }
  });

  // Form Submissions: Login Form
  elements.loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append("username", elements.loginUsername.value.trim());
    formData.append("password", elements.loginPassword.value);

    try {
      const res = await fetch("/auth/login", {
        method: "POST",
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        saveAuthSession(data.access_token, {
          username: data.username,
          role: data.role,
        });
        showToast(`Welcome back, ${data.username}!`, "success");
        closeAuthModal();
        loadEmployees();
      } else {
        const err = await res.json();
        showToast(err.detail || "Authentication failed", "error");
      }
    } catch (err) {
      showToast("Network error during login", "error");
    }
  });

  // Form Submissions: Register Form
  elements.registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      username: elements.regUsername.value.trim(),
      password: elements.regPassword.value,
      full_name: elements.regFullName.value.trim() || null,
    };

    try {
      const res = await fetch("/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        const user = await res.json();
        showToast(`Registration successful! You are ${user.role}. Signing in...`, "success");
        
        // Auto-login after registration
        const formData = new FormData();
        formData.append("username", payload.username);
        formData.append("password", payload.password);
        const loginRes = await fetch("/auth/login", { method: "POST", body: formData });
        if (loginRes.ok) {
          const loginData = await loginRes.json();
          saveAuthSession(loginData.access_token, {
            username: loginData.username,
            role: loginData.role,
          });
          closeAuthModal();
          loadEmployees();
        }
      } else {
        const err = await res.json();
        showToast(err.detail || "Registration failed", "error");
      }
    } catch (err) {
      showToast("Network error during registration", "error");
    }
  });
}

// --------------------------------------------------------------------------
// Bootstrap Application
// --------------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  initEventListeners();
  renderUserWidget();
  checkClusterHealth();
  setInterval(checkClusterHealth, 10000); // Poll health probe every 10s
  loadEmployees();
});
