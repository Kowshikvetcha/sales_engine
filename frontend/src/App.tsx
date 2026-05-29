import React, { useState, useEffect } from "react";
import { 
  QueryClient, 
  QueryClientProvider, 
  useQuery, 
  useMutation, 
  useQueryClient 
} from "@tanstack/react-query";
import { 
  LayoutDashboard, 
  FileSpreadsheet, 
  Users, 
  FileCheck, 
  Send, 
  Settings, 
  Cpu, 
  AlertCircle, 
  Key, 
  Check, 
  X, 
  Search, 
  ChevronRight, 
  RotateCw, 
  Play, 
  CheckCircle, 
  TrendingUp, 
  ShieldCheck, 
  Clock,
  ExternalLink,
  Upload,
  AlertTriangle,
  Sparkles
} from "lucide-react";
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Cell
} from "recharts";

import { api, getStoredToken, setStoredToken, apiRequest } from "./api/client";
import "./App.css";

// Initialize Query Client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <DashboardShell />
    </QueryClientProvider>
  );
}

function DashboardShell() {
  const [activeTab, setActiveTab] = useState<string>("dashboard");
  const [tokenInput, setTokenInput] = useState<string>("");
  const [authToken, setAuthToken] = useState<string>(getStoredToken());
  const [showTokenOverlay, setShowTokenOverlay] = useState<boolean>(!getStoredToken());
  const [selectedLeadId, setSelectedLeadId] = useState<number | null>(null);
  
  const queryClient = useQueryClient();

  useEffect(() => {
    setAuthToken(getStoredToken());
    setShowTokenOverlay(!getStoredToken());
  }, []);

  const handleSaveToken = (e: React.FormEvent) => {
    e.preventDefault();
    if (tokenInput.trim()) {
      setStoredToken(tokenInput.trim());
      setAuthToken(tokenInput.trim());
      setShowTokenOverlay(false);
      // Invalidate all queries to trigger refetch with new token
      queryClient.invalidateQueries();
    }
  };

  const handleLogout = () => {
    setStoredToken("");
    setAuthToken("");
    setShowTokenOverlay(true);
  };

  // Shared stats query
  const { data: stats, isLoading: statsLoading, refetch: refetchStats, error: statsError } = useQuery({
    queryKey: ["stats"],
    queryFn: api.getStats,
    enabled: !!authToken,
  });

  // Handle unauthorized responses globally
  useEffect(() => {
    if (statsError && statsError.message.includes("UNAUTHORIZED")) {
      setShowTokenOverlay(true);
    }
  }, [statsError]);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100 font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between shrink-0">
        <div>
          <div className="p-6 flex items-center space-x-3 border-b border-slate-800">
            <div className="bg-brand-600 p-2 rounded-lg">
              <Cpu className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-sm leading-tight tracking-wider text-slate-200 uppercase">Sales Engine</h1>
              <span className="text-[10px] text-brand-500 font-medium">B2B Website Auditor</span>
            </div>
          </div>

          <nav className="p-4 space-y-1">
            <SidebarLink 
              icon={<LayoutDashboard className="h-5 w-5" />} 
              label="Dashboard" 
              active={activeTab === "dashboard"} 
              onClick={() => { setActiveTab("dashboard"); setSelectedLeadId(null); }} 
            />
            <SidebarLink 
              icon={<Users className="h-5 w-5" />} 
              label="Leads Directory" 
              active={activeTab === "leads"} 
              onClick={() => { setActiveTab("leads"); }} 
            />
            <SidebarLink 
              icon={<FileSpreadsheet className="h-5 w-5" />} 
              label="Lead Import" 
              active={activeTab === "import"} 
              onClick={() => { setActiveTab("import"); setSelectedLeadId(null); }} 
            />
            <SidebarLink 
              icon={<FileCheck className="h-5 w-5" />} 
              label="Review Queue" 
              active={activeTab === "review"} 
              onClick={() => { setActiveTab("review"); setSelectedLeadId(null); }} 
            />
            <SidebarLink 
              icon={<Send className="h-5 w-5" />} 
              label="Send Console" 
              active={activeTab === "send"} 
              onClick={() => { setActiveTab("send"); setSelectedLeadId(null); }} 
            />
            <SidebarLink 
              icon={<Cpu className="h-5 w-5" />} 
              label="Background Jobs" 
              active={activeTab === "jobs"} 
              onClick={() => { setActiveTab("jobs"); setSelectedLeadId(null); }} 
            />
            <SidebarLink 
              icon={<Sparkles className="h-5 w-5" />} 
              label="Model Bake-off" 
              active={activeTab === "bakeoff"} 
              onClick={() => { setActiveTab("bakeoff"); setSelectedLeadId(null); }} 
            />
            <SidebarLink 
              icon={<Settings className="h-5 w-5" />} 
              label="Settings" 
              active={activeTab === "settings"} 
              onClick={() => { setActiveTab("settings"); setSelectedLeadId(null); }} 
            />
          </nav>
        </div>

        {/* Sidebar Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/50 flex flex-col space-y-2">
          {authToken ? (
            <div className="flex items-center justify-between text-xs">
              <span className="text-emerald-500 flex items-center space-x-1">
                <span className="h-2 w-2 bg-emerald-500 rounded-full inline-block animate-pulse"></span>
                <span>Connected</span>
              </span>
              <button 
                onClick={handleLogout}
                className="text-slate-400 hover:text-red-400 transition"
              >
                Disconnect
              </button>
            </div>
          ) : (
            <span className="text-xs text-red-500 flex items-center space-x-1">
              <span className="h-2 w-2 bg-red-500 rounded-full inline-block"></span>
              <span>Disconnected</span>
            </span>
          )}
        </div>
      </aside>

      {/* Main Panel Content */}
      <main className="flex-1 flex flex-col min-w-0 bg-slate-950 overflow-hidden relative">
        <header className="h-16 border-b border-slate-800 bg-slate-900/40 flex items-center justify-between px-8 shrink-0">
          <h2 className="text-xl font-semibold capitalize text-slate-200">
            {activeTab.replace("-", " ")}
          </h2>
          <div className="flex items-center space-x-4">
            <button 
              onClick={() => { refetchStats(); queryClient.invalidateQueries(); }}
              className="p-2 text-slate-400 hover:text-slate-200 bg-slate-900 border border-slate-800 rounded-lg hover:border-slate-700 transition"
              title="Refresh all data"
            >
              <RotateCw className="h-4 w-4" />
            </button>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-8">
          {activeTab === "dashboard" && (
            <DashboardView 
              stats={stats} 
              loading={statsLoading} 
              onLaunchJob={() => setActiveTab("jobs")} 
            />
          )}
          {activeTab === "leads" && (
            <LeadsView 
              selectedLeadId={selectedLeadId}
              onSelectLead={setSelectedLeadId}
            />
          )}
          {activeTab === "import" && (
            <ImportView 
              onSuccess={() => setActiveTab("leads")} 
            />
          )}
          {activeTab === "review" && (
            <ReviewView />
          )}
          {activeTab === "send" && (
            <SendConsoleView 
              onLaunchJob={() => setActiveTab("jobs")} 
            />
          )}
          {activeTab === "jobs" && (
            <JobsView />
          )}
          {activeTab === "settings" && (
            <SettingsView />
          )}
          {activeTab === "bakeoff" && (
            <BakeoffView />
          )}
        </div>
      </main>

      {/* API Token Prompt Overlay */}
      {showTokenOverlay && (
        <div className="fixed inset-0 bg-slate-950/95 backdrop-blur-md flex items-center justify-center z-50 p-4">
          <div className="max-w-md w-full glass-panel rounded-2xl p-8 shadow-2xl border border-slate-800">
            <div className="flex flex-col items-center text-center space-y-4 mb-6">
              <div className="bg-brand-900/50 p-3 rounded-full border border-brand-500/20">
                <Key className="h-8 w-8 text-brand-500" />
              </div>
              <h3 className="text-xl font-bold text-slate-100">API Connection Required</h3>
              <p className="text-sm text-slate-400">
                To connect to the local Sales Engine server, please enter your API Authentication token (the <code className="text-xs bg-slate-900 text-brand-500 font-mono">API_AUTH_TOKEN</code> configured in your backend <code className="text-xs">.env</code> file).
              </p>
            </div>

            <form onSubmit={handleSaveToken} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                  Access Token
                </label>
                <input 
                  type="password"
                  value={tokenInput}
                  onChange={(e) => setTokenInput(e.target.value)}
                  placeholder="Enter API token..."
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-brand-500 transition font-mono"
                  required
                />
              </div>

              <button 
                type="submit"
                className="w-full bg-brand-600 hover:bg-brand-500 text-white font-medium py-3 px-4 rounded-xl shadow-lg shadow-brand-500/20 hover:shadow-brand-500/30 transition duration-200"
              >
                Connect to Server
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

// Sidebar Button Helper Component
interface SidebarLinkProps {
  icon: React.ReactNode;
  label: string;
  active: boolean;
  onClick: () => void;
}
function SidebarLink({ icon, label, active, onClick }: SidebarLinkProps) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-medium transition ${
        active 
          ? "bg-brand-900/30 text-brand-500 border-l-4 border-brand-500" 
          : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
      }`}
    >
      <span className={active ? "text-brand-500" : "text-slate-400"}>
        {icon}
      </span>
      <span>{label}</span>
    </button>
  );
}

// ----------------------------------------------------
// VIEW 1: DASHBOARD
// ----------------------------------------------------
interface DashboardViewProps {
  stats: Record<string, number> | undefined;
  loading: boolean;
  onLaunchJob: () => void;
}
function DashboardView({ stats, loading, onLaunchJob }: DashboardViewProps) {
  const queryClient = useQueryClient();

  const runMutation = useMutation({
    mutationFn: ({ type }: { type: string }) => api.createJob(type, {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      onLaunchJob(); // Redirect to jobs panel to view logs
    },
    onError: (err: any) => {
      alert(`Failed to launch pipeline job: ${err.message}`);
    }
  });

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-64 space-y-4">
        <RotateCw className="h-8 w-8 text-brand-500 animate-spin" />
        <span className="text-slate-400 text-sm">Querying system statuses...</span>
      </div>
    );
  }

  // Format Recharts data
  const chartData = stats ? Object.entries(stats)
    .filter(([name]) => name !== "total")
    .map(([name, val]) => ({
      name: name.replace("_", " "),
      count: val
    })) : [];

  const totalLeads = stats ? Object.values(stats).reduce((a, b) => a + b, 0) : 0;

  // Custom colors for funnel chart mapping
  const STATUS_COLORS: Record<string, string> = {
    "pending": "#f59e0b",
    "scraped": "#3b82f6",
    "analyzed": "#6366f1",
    "drafted": "#8b5cf6",
    "approved": "#10b981",
    "rejected": "#ef4444",
    "sent": "#10b981",
    "failed": "#f43f5e",
    "suppressed": "#6b7280",
    "skipped no findings": "#4b5563"
  };

  return (
    <div className="space-y-8">
      {/* Metric Funnel Counts */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        <StatCard title="Pending Scrapes" value={stats?.pending ?? 0} color="amber" icon={<Clock className="h-5 w-5" />} />
        <StatCard title="Scraped Sites" value={stats?.scraped ?? 0} color="blue" icon={<TrendingUp className="h-5 w-5" />} />
        <StatCard title="Analyzed Audits" value={stats?.analyzed ?? 0} color="indigo" icon={<ShieldCheck className="h-5 w-5" />} />
        <StatCard title="Drafted Emails" value={stats?.drafted ?? 0} color="purple" icon={<FileCheck className="h-5 w-5" />} />
        <StatCard title="Emails Sent" value={stats?.sent ?? 0} color="emerald" icon={<Send className="h-5 w-5" />} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Recharts Bar Visualizer */}
        <div className="lg:col-span-2 glass-panel rounded-2xl p-6 flex flex-col justify-between">
          <div className="mb-4">
            <h3 className="text-lg font-bold text-slate-200">Pipeline Funnel Distribution</h3>
            <span className="text-xs text-slate-400">Total ingested records: {totalLeads} leads</span>
          </div>
          
          <div className="h-72 w-full text-xs">
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="name" stroke="#64748b" tickLine={false} />
                  <YAxis stroke="#64748b" allowDecimals={false} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", color: "#f1f5f9" }} 
                    cursor={{ fill: "rgba(255, 255, 255, 0.05)" }}
                  />
                  <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                    {chartData.map((entry, index) => {
                      const color = STATUS_COLORS[entry.name.toLowerCase()] || "#8b5cf6";
                      return <Cell key={`cell-${index}`} fill={color} />;
                    })}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-slate-500">No data to display. Please import leads first.</div>
            )}
          </div>
        </div>

        {/* Pipeline Control Hub */}
        <div className="glass-panel rounded-2xl p-6 flex flex-col space-y-4">
          <div>
            <h3 className="text-lg font-bold text-slate-200">Quick Actions Control</h3>
            <span className="text-xs text-slate-400">Run pipelines manually in background</span>
          </div>

          <div className="flex-1 flex flex-col justify-center space-y-3">
            <PipelineButton 
              label="Run Web Scraper" 
              desc="Scrape pending websites" 
              onClick={() => runMutation.mutate({ type: "scrape" })} 
              loading={runMutation.isPending && runMutation.variables?.type === "scrape"}
            />
            <PipelineButton 
              label="Run Site Analyzer" 
              desc="Calculate Lighthouse scores" 
              onClick={() => runMutation.mutate({ type: "analyze" })} 
              loading={runMutation.isPending && runMutation.variables?.type === "analyze"}
            />
            <PipelineButton 
              label="Generate Email Drafts" 
              desc="Draft cold emails using LLM" 
              onClick={() => runMutation.mutate({ type: "generate" })} 
              loading={runMutation.isPending && runMutation.variables?.type === "generate"}
            />
            <PipelineButton 
              label="Dispatch Send Runner" 
              desc="Process sends and dry-runs" 
              onClick={() => runMutation.mutate({ type: "send" })} 
              loading={runMutation.isPending && runMutation.variables?.type === "send"}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

interface StatCardProps {
  title: string;
  value: number;
  color: "amber" | "blue" | "indigo" | "purple" | "emerald";
  icon: React.ReactNode;
}
function StatCard({ title, value, color, icon }: StatCardProps) {
  const colorMaps = {
    amber: "border-amber-500/20 text-amber-500 bg-amber-950/20",
    blue: "border-blue-500/20 text-blue-500 bg-blue-950/20",
    indigo: "border-indigo-500/20 text-indigo-500 bg-indigo-950/20",
    purple: "border-purple-500/20 text-purple-500 bg-purple-950/20",
    emerald: "border-emerald-500/20 text-emerald-500 bg-emerald-950/20"
  };

  return (
    <div className={`p-6 rounded-2xl border flex flex-col justify-between h-32 ${colorMaps[color]} shadow-lg`}>
      <div className="flex items-center justify-between">
        <span className="text-xs uppercase tracking-wider font-semibold opacity-85 text-slate-400">{title}</span>
        <span className="opacity-80">{icon}</span>
      </div>
      <span className="text-3xl font-extrabold tracking-tight text-slate-100">{value}</span>
    </div>
  );
}

interface PipelineButtonProps {
  label: string;
  desc: string;
  onClick: () => void;
  loading: boolean;
}
function PipelineButton({ label, desc, onClick, loading }: PipelineButtonProps) {
  return (
    <button 
      onClick={onClick}
      disabled={loading}
      className="w-full flex items-center justify-between p-4 rounded-xl bg-slate-900 border border-slate-800 hover:border-brand-500/30 hover:bg-slate-900/80 transition text-left group disabled:opacity-50"
    >
      <div>
        <h4 className="text-sm font-semibold text-slate-200 group-hover:text-brand-500 transition">{label}</h4>
        <span className="text-xs text-slate-400 leading-tight">{desc}</span>
      </div>
      <div className="bg-slate-800 p-2 rounded-lg text-slate-400 group-hover:text-brand-500 group-hover:bg-brand-900/20 transition">
        {loading ? <RotateCw className="h-4 w-4 animate-spin text-brand-500" /> : <Play className="h-4 w-4" />}
      </div>
    </button>
  );
}

// ----------------------------------------------------
// VIEW 2: LEADS LIST DIRECTORY & DETAIL INSPECTOR
// ----------------------------------------------------
interface LeadsViewProps {
  selectedLeadId: number | null;
  onSelectLead: (id: number | null) => void;
}
function LeadsView({ selectedLeadId, onSelectLead }: LeadsViewProps) {
  const [filterStatus, setFilterStatus] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [page, setPage] = useState<number>(0);
  const limit = 15;

  const { data: leads, isLoading } = useQuery({
    queryKey: ["leads", filterStatus],
    queryFn: () => api.getLeads(filterStatus || undefined),
  });

  // Filter client-side for search queries
  const filteredLeads = leads ? leads.filter(lead => {
    const text = `${lead.name || ""} ${lead.email || ""} ${lead.domain || ""}`.toLowerCase();
    return text.includes(searchQuery.toLowerCase());
  }) : [];

  // Paged leads
  const pagedLeads = filteredLeads.slice(page * limit, (page + 1) * limit);
  const totalPages = Math.ceil(filteredLeads.length / limit);

  const getStatusBadge = (status: string) => {
    const maps: Record<string, string> = {
      pending: "bg-amber-950/40 text-amber-500 border-amber-500/20",
      scraped: "bg-blue-950/40 text-blue-500 border-blue-500/20",
      analyzed: "bg-indigo-950/40 text-indigo-500 border-indigo-500/20",
      drafted: "bg-purple-950/40 text-purple-500 border-purple-500/20",
      approved: "bg-emerald-950/40 text-emerald-500 border-emerald-500/20",
      rejected: "bg-rose-950/40 text-rose-500 border-rose-500/20",
      sent: "bg-emerald-950/40 text-emerald-500 border-emerald-500/20",
      failed: "bg-rose-950/40 text-rose-500 border-rose-500/20",
      suppressed: "bg-slate-900 text-slate-400 border-slate-800",
      skipped_no_findings: "bg-slate-900 text-slate-400 border-slate-800"
    };
    return (
      <span className={`px-2.5 py-0.5 text-xs font-semibold border rounded-full ${maps[status] || "bg-slate-900 text-slate-400 border-slate-800"}`}>
        {status.replace("_", " ")}
      </span>
    );
  };

  return (
    <div className="flex space-x-8 h-full relative">
      {/* List Pane */}
      <div className={`flex-1 flex flex-col min-w-0 transition-all duration-300 ${selectedLeadId ? "w-2/3" : "w-full"}`}>
        {/* Filter bar */}
        <div className="flex flex-col md:flex-row space-y-3 md:space-y-0 md:space-x-4 mb-6">
          <div className="flex-1 relative">
            <input 
              type="text" 
              placeholder="Search leads by name, email, website..." 
              value={searchQuery}
              onChange={(e) => { setSearchQuery(e.target.value); setPage(0); }}
              className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm placeholder-slate-500 focus:outline-none focus:border-brand-500 transition"
            />
            <Search className="h-4 w-4 text-slate-500 absolute left-3 top-3.5" />
          </div>

          <select 
            value={filterStatus}
            onChange={(e) => { setFilterStatus(e.target.value); setPage(0); }}
            className="bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-300 focus:outline-none focus:border-brand-500 transition"
          >
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="scraped">Scraped</option>
            <option value="analyzed">Analyzed</option>
            <option value="drafted">Drafted</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
            <option value="sent">Sent</option>
            <option value="failed">Failed</option>
            <option value="suppressed">Suppressed</option>
          </select>
        </div>

        {/* Leads Table */}
        <div className="flex-1 glass-panel rounded-2xl overflow-hidden flex flex-col justify-between shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900/50">
                  <th className="p-4 font-semibold text-slate-400 text-xs uppercase tracking-wider">Company Name</th>
                  <th className="p-4 font-semibold text-slate-400 text-xs uppercase tracking-wider">Domain</th>
                  <th className="p-4 font-semibold text-slate-400 text-xs uppercase tracking-wider">Email Address</th>
                  <th className="p-4 font-semibold text-slate-400 text-xs uppercase tracking-wider">Pipeline Status</th>
                  <th className="p-4 font-semibold text-slate-400 text-xs uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {isLoading ? (
                  <tr>
                    <td colSpan={5} className="p-8 text-center text-slate-400">Loading leads data...</td>
                  </tr>
                ) : pagedLeads.length > 0 ? (
                  pagedLeads.map(lead => (
                    <tr 
                      key={lead.id} 
                      onClick={() => onSelectLead(lead.id)}
                      className={`hover:bg-slate-900/30 transition cursor-pointer ${selectedLeadId === lead.id ? "bg-brand-900/10 hover:bg-brand-900/20" : ""}`}
                    >
                      <td className="p-4 font-semibold text-slate-200">{lead.name || "(Unnamed)"}</td>
                      <td className="p-4 font-mono text-slate-400">{lead.domain || lead.website_url || "—"}</td>
                      <td className="p-4 text-slate-300">{lead.email || "—"}</td>
                      <td className="p-4">{getStatusBadge(lead.status)}</td>
                      <td className="p-4">
                        <button className="text-brand-500 hover:text-brand-400 flex items-center space-x-1 font-medium transition text-xs">
                          <span>Open</span>
                          <ChevronRight className="h-3 w-3" />
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="p-8 text-center text-slate-500">No matching leads found.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="p-4 border-t border-slate-800 bg-slate-900/20 flex items-center justify-between text-xs text-slate-400">
              <span>Showing {page * limit + 1}-{Math.min((page + 1) * limit, filteredLeads.length)} of {filteredLeads.length} leads</span>
              <div className="flex space-x-2">
                <button 
                  disabled={page === 0}
                  onClick={() => setPage(p => p - 1)}
                  className="px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900 hover:border-slate-700 transition disabled:opacity-40"
                >
                  Previous
                </button>
                <button 
                  disabled={page >= totalPages - 1}
                  onClick={() => setPage(p => p + 1)}
                  className="px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900 hover:border-slate-700 transition disabled:opacity-40"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Details Inspector Slide-over */}
      {selectedLeadId && (
        <LeadDetailsPanel 
          id={selectedLeadId} 
          onClose={() => onSelectLead(null)} 
        />
      )}
    </div>
  );
}

// Subcomponent: Lead Details Drawer
interface LeadDetailsPanelProps {
  id: number;
  onClose: () => void;
}
function LeadDetailsPanel({ id, onClose }: LeadDetailsPanelProps) {
  const { data: lead, isLoading, error } = useQuery({
    queryKey: ["lead", id],
    queryFn: () => api.getLead(id),
  });

  if (isLoading) {
    return (
      <div className="w-96 lg:w-[480px] glass-panel border-l border-slate-800 h-full flex flex-col justify-center items-center space-y-4 shrink-0 shadow-2xl p-6">
        <RotateCw className="h-8 w-8 text-brand-500 animate-spin" />
        <span className="text-slate-400 text-sm">Querying audit metrics...</span>
      </div>
    );
  }

  if (error || !lead) {
    return (
      <div className="w-96 lg:w-[480px] glass-panel border-l border-slate-800 h-full flex flex-col justify-center items-center space-y-4 shrink-0 shadow-2xl p-6">
        <AlertCircle className="h-10 w-10 text-red-500" />
        <span className="text-red-400 text-sm">Failed to load lead details.</span>
        <button onClick={onClose} className="text-slate-300 underline text-xs">Close Details</button>
      </div>
    );
  }

  const analysis = lead.analysis;
  const scrape = lead.scrape;
  const emailDraft = lead.emails?.[0]; // Get the latest draft

  const getSeverityColor = (sev: string) => {
    if (sev === "high") return "text-red-400 bg-red-950/20 border-red-500/10";
    if (sev === "medium") return "text-amber-400 bg-amber-950/20 border-amber-500/10";
    return "text-blue-400 bg-blue-950/20 border-blue-500/10";
  };

  return (
    <div className="w-96 lg:w-[480px] glass-panel border-l border-slate-800 h-full flex flex-col shrink-0 shadow-2xl animate-in slide-in-from-right duration-200">
      {/* Details Header */}
      <div className="p-6 border-b border-slate-800 flex items-center justify-between shrink-0 bg-slate-900/50">
        <div className="min-w-0">
          <h3 className="font-bold text-slate-100 truncate text-base">{lead.name || "(Unnamed Biz)"}</h3>
          <span className="text-xs font-mono text-brand-400 truncate block mt-0.5">{lead.domain || lead.website_url}</span>
        </div>
        <button onClick={onClose} className="p-1 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition">
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Details Body */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Core audit scores */}
        {analysis ? (
          <div className="space-y-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Lighthouse Performance Report</h4>
            
            <div className="grid grid-cols-2 gap-4">
              <ScoreCard title="Performance" score={analysis.perf_score} />
              <ScoreCard title="SEO Score" score={analysis.seo_score} />
              <ScoreCard title="Accessibility" score={analysis.accessibility_score} />
              <ScoreCard title="Best Practices" score={analysis.best_practices_score} />
            </div>

            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 grid grid-cols-2 gap-y-3 text-xs">
              <div className="text-slate-400">SSL Certificate:</div>
              <div className="font-semibold text-right flex items-center justify-end space-x-1">
                {analysis.has_ssl ? (
                  <>
                    <CheckCircle className="h-4.5 w-4.5 text-emerald-500" />
                    <span className="text-emerald-400">Secure (HTTPS)</span>
                  </>
                ) : (
                  <>
                    <AlertTriangle className="h-4.5 w-4.5 text-red-500" />
                    <span className="text-red-400">Unsecured (HTTP)</span>
                  </>
                )}
              </div>

              <div className="text-slate-400">Load Duration:</div>
              <div className="font-semibold text-right text-slate-200">
                {analysis.load_time_ms ? `${(analysis.load_time_ms / 1000).toFixed(2)}s` : "—"}
              </div>

              <div className="text-slate-400">Broken Links Sample:</div>
              <div className="font-semibold text-right text-slate-200">
                {analysis.broken_links_count > 0 ? (
                  <span className="text-red-400 font-bold">{analysis.broken_links_count} broken link(s)</span>
                ) : (
                  <span className="text-emerald-400">0 broken links found</span>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800 border-dashed text-center text-xs text-slate-500 py-6">
            Lighthouse Performance Audits have not been run on this website yet. Run the Analyzer pipeline to gather scores.
          </div>
        )}

        {/* Signals lists */}
        {analysis?.signals && analysis.signals.length > 0 && (
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">Objective Signal Weaknesses</h4>
            <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
              {analysis.signals.map((sig: any, index: number) => (
                <div key={index} className={`p-3 rounded-lg border text-xs flex justify-between items-center ${getSeverityColor(sig.severity)}`}>
                  <span className="font-semibold font-mono tracking-tight">{sig.key.replace("_", " ")}</span>
                  <span>{String(sig.value)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Generated Email Outreach Section */}
        {emailDraft ? (
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Personalized outreach draft</h4>
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
              <div className="text-xs font-semibold text-slate-300">
                <span className="text-slate-400 mr-2 uppercase text-[10px]">Subject:</span>
                {emailDraft.subject}
              </div>
              <div className="p-3 bg-slate-950/60 rounded-lg text-xs leading-relaxed text-slate-300 font-mono whitespace-pre-wrap max-h-60 overflow-y-auto">
                {emailDraft.body}
              </div>
            </div>
          </div>
        ) : lead.status === "drafted" || lead.status === "approved" ? (
          <div className="text-xs text-amber-500">Generating outreach draft contents...</div>
        ) : null}

        {/* Raw text extractor preview */}
        {scrape?.rendered_text && (
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Rendered Webpage Text Preview</h4>
            <div className="p-3 bg-slate-900 rounded-xl text-xs font-mono max-h-40 overflow-y-auto leading-relaxed border border-slate-800 text-slate-400">
              {scrape.rendered_text}
            </div>
          </div>
        )}

        {/* Screenshot preview */}
        {scrape?.screenshot_path && (
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Homepage Screenshot Capture</h4>
            <div className="rounded-xl overflow-hidden border border-slate-800 bg-slate-900/50 aspect-video relative group">
              <img 
                src={api.getScreenshotUrl(lead.id)} 
                alt="Homepage Screenshot"
                className="w-full h-full object-cover"
                onError={(e) => {
                  (e.target as HTMLElement).style.display = "none";
                }}
              />
              <div className="absolute inset-0 bg-slate-950/40 opacity-0 group-hover:opacity-100 transition flex items-center justify-center">
                <a 
                  href={api.getScreenshotUrl(lead.id)} 
                  target="_blank" 
                  rel="noreferrer" 
                  className="bg-slate-900/90 text-xs px-3 py-1.5 rounded-lg border border-slate-700 flex items-center space-x-1 hover:bg-slate-800 transition"
                >
                  <span>Open Full Image</span>
                  <ExternalLink className="h-3 w-3" />
                </a>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

interface ScoreCardProps {
  title: string;
  score: number | null | undefined;
}
function ScoreCard({ title, score }: ScoreCardProps) {
  const getScoreColor = (s: number | null | undefined) => {
    if (s === null || s === undefined) return "text-slate-400 border-slate-800";
    if (s < 50) return "text-red-500 border-red-500/20 bg-red-950/10";
    if (s < 90) return "text-amber-500 border-amber-500/20 bg-amber-950/10";
    return "text-emerald-500 border-emerald-500/20 bg-emerald-950/10";
  };

  return (
    <div className={`p-4 rounded-xl border flex flex-col justify-between items-center text-center ${getScoreColor(score)}`}>
      <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider mb-1">{title}</span>
      <span className="text-xl font-extrabold">{score !== null && score !== undefined ? score : "—"}</span>
    </div>
  );
}

// ----------------------------------------------------
// VIEW 3: LEAD IMPORT CSV PANEL
// ----------------------------------------------------
interface ImportViewProps {
  onSuccess: () => void;
}
function ImportView({ onSuccess }: ImportViewProps) {
  const [csvText, setCsvText] = useState<string>("");
  const [dragActive, setDragActive] = useState<boolean>(false);
  const [parsedRows, setParsedRows] = useState<Record<string, string>[]>([]);
  const [headers, setHeaders] = useState<string[]>([]);
  const [columnMap, setColumnMap] = useState<Record<string, string>>({
    name: "",
    website: "",
    email: ""
  });
  
  const queryClient = useQueryClient();

  const parseCSVLines = (text: string) => {
    const rawLines = text.split(/\r?\n/).map(line => line.trim()).filter(Boolean);
    if (rawLines.length === 0) return;

    // A very basic CSV parser that splits by comma, respecting quotes
    const parseLine = (line: string) => {
      const result = [];
      let current = "";
      let inQuotes = false;
      
      for (let i = 0; i < line.length; i++) {
        const char = line[i];
        if (char === '"') {
          inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
          result.push(current.trim());
          current = "";
        } else {
          current += char;
        }
      }
      result.push(current.trim());
      // Strip outer quotes if any
      return result.map(cell => cell.replace(/^"(.*)"$/, "$1"));
    };

    const parsedHeader = parseLine(rawLines[0]);
    const rows: Record<string, string>[] = [];

    for (let i = 1; i < rawLines.length; i++) {
      const cells = parseLine(rawLines[i]);
      const row: Record<string, string> = {};
      parsedHeader.forEach((h, index) => {
        row[h] = cells[index] || "";
      });
      rows.push(row);
    }

    setHeaders(parsedHeader);
    setParsedRows(rows);

    // Dynamic header mapper guesses
    const newMap = { name: "", website: "", email: "" };
    parsedHeader.forEach(h => {
      const lower = h.toLowerCase();
      if (lower.includes("name") || lower.includes("company") || lower.includes("biz")) {
        newMap.name = h;
      }
      if (lower.includes("web") || lower.includes("site") || lower.includes("url") || lower.includes("domain")) {
        newMap.website = h;
      }
      if (lower.includes("email") || lower.includes("mail")) {
        newMap.email = h;
      }
    });
    setColumnMap(newMap);
  };

  useEffect(() => {
    if (csvText.trim()) {
      parseCSVLines(csvText);
    } else {
      setHeaders([]);
      setParsedRows([]);
    }
  }, [csvText]);

  // Handle file drop
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      const reader = new FileReader();
      reader.onload = (event) => {
        const text = event.target?.result as string;
        setCsvText(text);
      };
      reader.readAsText(file);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const reader = new FileReader();
      reader.onload = (event) => {
        const text = event.target?.result as string;
        setCsvText(text);
      };
      reader.readAsText(file);
    }
  };

  const importMutation = useMutation({
    mutationFn: (payload: any[]) => {
      // Calls POST /api/leads
      return apiRequest<any[]>("/api/leads", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    },
    onSuccess: (res: any[]) => {
      alert(`Success! Successfully processed lead imports. Imported ${res.length} valid rows.`);
      queryClient.invalidateQueries({ queryKey: ["leads"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
      onSuccess();
    },
    onError: (err: any) => {
      alert(`Failed to import leads: ${err.message}`);
    }
  });

  const handleImportSubmit = () => {
    if (!columnMap.email || !columnMap.website) {
      alert("Missing Column Mapping! You must map at least the Email and Website columns to proceed.");
      return;
    }

    const payload = parsedRows.map(row => ({
      name: columnMap.name ? row[columnMap.name] : "",
      website_url: row[columnMap.website],
      email: row[columnMap.email],
      country: "US"
    }));

    importMutation.mutate(payload);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 h-full">
      {/* Upload Column Mapping Pane */}
      <div className="space-y-6 flex flex-col">
        <div className="mb-2">
          <p className="text-sm text-slate-400">
            Upload a CSV containing business lead info. Map headers and preview before committing.
          </p>
        </div>

        {/* Drag Drop Zone */}
        <div 
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-2xl p-8 text-center flex flex-col justify-center items-center h-48 transition cursor-pointer ${
            dragActive 
              ? "border-brand-500 bg-brand-900/10" 
              : "border-slate-800 bg-slate-900/30 hover:border-slate-700"
          }`}
        >
          <Upload className={`h-8 w-8 mb-3 ${dragActive ? "text-brand-500" : "text-slate-500"}`} />
          <span className="text-sm font-semibold text-slate-300">Drag & drop CSV file here</span>
          <span className="text-xs text-slate-500 mt-1">or click below to choose a file from disk</span>
          <input 
            type="file" 
            accept=".csv"
            onChange={handleFileChange}
            className="mt-4 text-xs text-slate-400 file:bg-brand-600/20 file:border-0 file:text-brand-400 file:px-4 file:py-2 file:rounded-lg file:mr-4 hover:file:bg-brand-600/30 transition cursor-pointer"
          />
        </div>

        {/* Paste Raw Textarea */}
        <div className="flex-1 flex flex-col">
          <label className="block text-xs uppercase tracking-wider font-bold text-slate-400 mb-2">Or Paste Raw CSV Data</label>
          <textarea 
            value={csvText}
            onChange={(e) => setCsvText(e.target.value)}
            placeholder="name,website,email&#10;Acme Corp,acme.com,info@acme.com&#10;..."
            className="w-full flex-1 bg-slate-900 border border-slate-800 rounded-2xl p-4 text-sm font-mono focus:outline-none focus:border-brand-500 transition resize-none placeholder-slate-600"
          />
        </div>
      </div>

      {/* Preview Column Mapping Pane */}
      <div className="glass-panel rounded-2xl p-6 flex flex-col justify-between shadow-xl">
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-bold text-slate-200">Import Preview & Header Mappings</h3>
            <span className="text-xs text-slate-400">Total detected rows: {parsedRows.length} lines</span>
          </div>

          {headers.length > 0 ? (
            <div className="space-y-4">
              {/* Header Selector Mappings */}
              <div className="p-4 bg-slate-900/50 border border-slate-800 rounded-xl space-y-3">
                <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Column Header Mappings</h4>
                
                <div className="grid grid-cols-3 gap-3 text-xs">
                  <div>
                    <label className="block text-[10px] text-slate-400 font-bold mb-1 uppercase">Business Name</label>
                    <select 
                      value={columnMap.name}
                      onChange={(e) => setColumnMap(p => ({ ...p, name: e.target.value }))}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200"
                    >
                      <option value="">(None - Empty)</option>
                      {headers.map(h => <option key={h} value={h}>{h}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-[10px] text-slate-400 font-bold mb-1 uppercase">Website URL *</label>
                    <select 
                      value={columnMap.website}
                      onChange={(e) => setColumnMap(p => ({ ...p, website: e.target.value }))}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 focus:border-brand-500"
                      required
                    >
                      <option value="">Select column...</option>
                      {headers.map(h => <option key={h} value={h}>{h}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-[10px] text-slate-400 font-bold mb-1 uppercase">Email Address *</label>
                    <select 
                      value={columnMap.email}
                      onChange={(e) => setColumnMap(p => ({ ...p, email: e.target.value }))}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 focus:border-brand-500"
                      required
                    >
                      <option value="">Select column...</option>
                      {headers.map(h => <option key={h} value={h}>{h}</option>)}
                    </select>
                  </div>
                </div>
              </div>

              {/* Data table preview */}
              <div className="space-y-2">
                <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Lead Row Previews (Max 5 rows)</h4>
                <div className="overflow-x-auto border border-slate-800 rounded-xl">
                  <table className="w-full text-left text-xs border-collapse font-sans">
                    <thead>
                      <tr className="border-b border-slate-800 bg-slate-900/50 text-slate-400">
                        <th className="p-3">Name</th>
                        <th className="p-3">Website</th>
                        <th className="p-3">Email</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      {parsedRows.slice(0, 5).map((row, i) => (
                        <tr key={i} className="hover:bg-slate-900/10">
                          <td className="p-3 text-slate-300 max-w-[120px] truncate">
                            {columnMap.name ? row[columnMap.name] : <span className="text-slate-600 font-mono italic">empty</span>}
                          </td>
                          <td className="p-3 text-slate-400 font-mono max-w-[150px] truncate">
                            {columnMap.website ? row[columnMap.website] : <span className="text-slate-600 font-mono italic">empty</span>}
                          </td>
                          <td className="p-3 text-slate-300 max-w-[150px] truncate">
                            {columnMap.email ? row[columnMap.email] : <span className="text-slate-600 font-mono italic">empty</span>}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-48 border border-dashed border-slate-800 rounded-2xl text-slate-500 text-xs py-10">
              <Upload className="h-6 w-6 mb-2 text-slate-600" />
              <span>Preview will display after uploading a valid CSV.</span>
            </div>
          )}
        </div>

        {/* Submit action */}
        {parsedRows.length > 0 && (
          <div className="mt-6 border-t border-slate-800 pt-6">
            <button 
              onClick={handleImportSubmit}
              disabled={importMutation.isPending}
              className="w-full flex items-center justify-center space-x-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white font-medium py-3 px-4 rounded-xl shadow-lg shadow-brand-500/20 hover:shadow-brand-500/30 transition duration-200"
            >
              {importMutation.isPending ? (
                <>
                  <RotateCw className="h-4.5 w-4.5 animate-spin" />
                  <span>Importing Ingest Records...</span>
                </>
              ) : (
                <>
                  <Check className="h-4.5 w-4.5" />
                  <span>Import {parsedRows.length} Leads to Database</span>
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// ----------------------------------------------------
// VIEW 4: BACKGROUND JOBS HISTORY & WORKER PROGRESS
// ----------------------------------------------------
function JobsView() {
  const queryClient = useQueryClient();
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null);
  const [logMessages, setLogMessages] = useState<string[]>([]);
  
  // List history jobs
  const { data: jobs, isLoading, refetch } = useQuery({
    queryKey: ["jobs"],
    queryFn: api.getJobs,
    refetchInterval: 3000, // Poll list every 3s to keep list states updated
  });

  const getJobStatusBadge = (status: string) => {
    const maps: Record<string, string> = {
      queued: "bg-slate-900 text-slate-400 border-slate-800",
      running: "bg-blue-950/40 text-blue-500 border-blue-500/20 animate-pulse",
      completed: "bg-emerald-950/40 text-emerald-500 border-emerald-500/20",
      failed: "bg-rose-950/40 text-rose-500 border-rose-500/20",
      cancelled: "bg-slate-900 text-slate-400 border-slate-800"
    };
    return (
      <span className={`px-2.5 py-0.5 text-xs font-semibold border rounded-full ${maps[status] || "bg-slate-900 text-slate-400 border-slate-800"}`}>
        {status}
      </span>
    );
  };

  const cancelMutation = useMutation({
    mutationFn: (id: number) => api.cancelJob(id),
    onSuccess: (res) => {
      alert(res.message || "Cancellation request successfully enqueued.");
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
    onError: (err: any) => {
      alert(`Failed to cancel job: ${err.message}`);
    }
  });

  // Handle SSE listener streaming logs
  useEffect(() => {
    if (!selectedJobId) {
      setLogMessages([]);
      return;
    }

    const token = getStoredToken();
    const eventSourceUrl = `/api/events/jobs/${selectedJobId}?token=${encodeURIComponent(token)}`;
    const eventSource = new EventSource(eventSourceUrl);

    setLogMessages(["[SSE] Connecting to live event streaming channel..."]);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const timestamp = new Date().toLocaleTimeString();
        let message = `[${timestamp}] Job status: ${data.status.toUpperCase()}`;
        
        if (data.done !== undefined && data.total !== undefined) {
          message += ` | Progress: ${data.done}/${data.total} units`;
        }
        if (data.error) {
          message += ` | Error: ${data.error}`;
        }
        
        setLogMessages(prev => [...prev, message]);

        if (["completed", "failed", "cancelled"].includes(data.status)) {
          setLogMessages(prev => [...prev, `[SSE] Connection closed: Job reached terminal state.`]);
          eventSource.close();
          // Invalidate to refresh DB counts on UI
          queryClient.invalidateQueries({ queryKey: ["jobs"] });
          queryClient.invalidateQueries({ queryKey: ["stats"] });
        }
      } catch (err) {
        // parsing failed
      }
    };

    eventSource.onerror = () => {
      setLogMessages(prev => [...prev, "[SSE] Connection closed or token validation failed."]);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [selectedJobId]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 h-full relative">
      {/* Jobs History List */}
      <div className="lg:col-span-2 flex flex-col min-w-0 h-full justify-between">
        <div className="glass-panel rounded-2xl overflow-hidden shadow-xl flex-1 flex flex-col">
          <div className="p-4 bg-slate-900/30 border-b border-slate-800 flex justify-between items-center shrink-0">
            <h3 className="text-sm font-bold text-slate-300">Background Job Execution Log</h3>
            <button onClick={() => refetch()} className="text-slate-400 hover:text-slate-200 p-1 bg-slate-950 border border-slate-850 rounded">
              <RotateCw className="h-3.5 w-3.5" />
            </button>
          </div>
          
          <div className="flex-1 overflow-y-auto max-h-[500px]">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900/50 text-slate-400">
                  <th className="p-3.5">ID</th>
                  <th className="p-3.5">Task Stage</th>
                  <th className="p-3.5">State</th>
                  <th className="p-3.5">Progress</th>
                  <th className="p-3.5">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {isLoading ? (
                  <tr>
                    <td colSpan={5} className="p-6 text-center text-slate-400">Loading job queues...</td>
                  </tr>
                ) : jobs && jobs.length > 0 ? (
                  jobs.map(job => (
                    <tr 
                      key={job.id} 
                      onClick={() => setSelectedJobId(job.id)}
                      className={`hover:bg-slate-900/30 transition cursor-pointer ${selectedJobId === job.id ? "bg-brand-900/10 hover:bg-brand-900/20" : ""}`}
                    >
                      <td className="p-3.5 font-bold text-slate-300">#{job.id}</td>
                      <td className="p-3.5 font-semibold uppercase text-slate-200">{job.type}</td>
                      <td className="p-3.5">{getJobStatusBadge(job.status)}</td>
                      <td className="p-3.5 max-w-[120px]">
                        <div className="space-y-1">
                          <div className="flex justify-between font-mono text-[10px] text-slate-400">
                            <span>{job.done}/{job.total}</span>
                            <span>{job.total > 0 ? `${Math.round((job.done / job.total) * 100)}%` : "0%"}</span>
                          </div>
                          <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                            <div 
                              className={`h-1.5 rounded-full ${job.status === "failed" ? "bg-red-500" : "bg-brand-500"}`} 
                              style={{ width: `${job.total > 0 ? (job.done / job.total) * 100 : 0}%` }}
                            ></div>
                          </div>
                        </div>
                      </td>
                      <td className="p-3.5">
                        <div className="flex items-center space-x-2">
                          <button 
                            onClick={(e) => { e.stopPropagation(); setSelectedJobId(job.id); }}
                            className="text-brand-500 hover:text-brand-400 font-semibold"
                          >
                            Logs
                          </button>
                          {["queued", "running"].includes(job.status) && (
                            <button 
                              onClick={(e) => { e.stopPropagation(); cancelMutation.mutate(job.id); }}
                              disabled={cancelMutation.isPending}
                              className="text-red-500 hover:text-red-400 font-semibold disabled:opacity-40"
                            >
                              Cancel
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="p-6 text-center text-slate-500">No jobs queued or run yet. Try triggering a Quick Action on the Dashboard.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* SSE Live Log Monitor */}
      <div className="glass-panel rounded-2xl p-6 flex flex-col justify-between shadow-xl">
        <div className="space-y-4 flex-1 flex flex-col">
          <div>
            <h3 className="text-lg font-bold text-slate-200">Live SSE Monitor</h3>
            <span className="text-xs text-slate-400">
              {selectedJobId ? `Listening to Job #${selectedJobId} event logs` : "Select a job to view real-time execution logs"}
            </span>
          </div>

          <div className="flex-1 bg-slate-950/70 border border-slate-850 rounded-xl p-4 font-mono text-xs text-emerald-400 leading-relaxed overflow-y-auto max-h-[400px]">
            {logMessages.length > 0 ? (
              logMessages.map((msg, index) => (
                <div key={index} className="mb-1.5">{msg}</div>
              ))
            ) : (
              <div className="flex items-center justify-center h-full text-slate-600 text-center select-none font-sans">
                SSE Terminal offline. Click "Logs" or select a job from the history list to listen to real-time events.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ----------------------------------------------------
// VIEW 5: INTERACTIVE REVIEW QUEUE
// ----------------------------------------------------
function ReviewView() {
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [subject, setSubject] = useState<string>("");
  const [bodyRaw, setBodyRaw] = useState<string>("");
  const [rejectReason, setRejectReason] = useState<string>("");
  const [showRejectModal, setShowRejectModal] = useState<boolean>(false);
  const [isEditing, setIsEditing] = useState<boolean>(false);

  // Fetch drafted leads
  const { data: draftedLeads, isLoading: leadsLoading } = useQuery({
    queryKey: ["leads", "drafted"],
    queryFn: () => api.getLeads("drafted"),
  });

  // Fetch detailed lead telemetry for selected lead
  const { data: leadDetails, isLoading: detailsLoading } = useQuery({
    queryKey: ["leadDetails", selectedId],
    queryFn: () => api.getLead(selectedId!),
    enabled: !!selectedId,
  });

  // Automatically select first lead in drafted list
  useEffect(() => {
    if (draftedLeads && draftedLeads.length > 0 && !selectedId) {
      setSelectedId(draftedLeads[0].id);
    } else if (draftedLeads && draftedLeads.length === 0) {
      setSelectedId(null);
    }
  }, [draftedLeads, selectedId]);

  // Sync edit states when leadDetails changes
  useEffect(() => {
    if (leadDetails && leadDetails.emails && leadDetails.emails.length > 0) {
      const email = leadDetails.emails[0]; // assuming first email is the current draft
      setSubject(email.subject || "");
      
      // Split the main body from the CAN-SPAM compliant footer
      const { mainBody } = splitFooter(email.body || "");
      setBodyRaw(mainBody || "");
      setIsEditing(false);
    } else {
      setSubject("");
      setBodyRaw("");
    }
  }, [leadDetails]);

  // Utility to split the footer
  const splitFooter = (bodyText: string) => {
    if (!bodyText) return { mainBody: "", footer: "" };
    const index = bodyText.indexOf("\n\n---\n");
    if (index !== -1) {
      return {
        mainBody: bodyText.substring(0, index),
        footer: bodyText.substring(index)
      };
    }
    return { mainBody: bodyText, footer: "" };
  };

  // Mutations
  const approveMutation = useMutation({
    mutationFn: (id: number) => api.approveLeadEmail(id),
    onSuccess: () => {
      alert("Lead approved!");
      queryClient.invalidateQueries({ queryKey: ["leads"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
      moveToNext();
    },
    onError: (err: any) => alert(`Approval failed: ${err.message}`),
  });

  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: number; reason?: string }) => api.rejectLeadEmail(id, reason),
    onSuccess: () => {
      alert("Lead rejected!");
      setShowRejectModal(false);
      setRejectReason("");
      queryClient.invalidateQueries({ queryKey: ["leads"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
      moveToNext();
    },
    onError: (err: any) => alert(`Rejection failed: ${err.message}`),
  });

  const saveMutation = useMutation({
    mutationFn: ({ id, subject, body }: { id: number; subject: string; body: string }) =>
      api.editLeadEmail(id, subject, body),
    onSuccess: () => {
      alert("Changes saved successfully!");
      setIsEditing(false);
      queryClient.invalidateQueries({ queryKey: ["leadDetails", selectedId] });
    },
    onError: (err: any) => alert(`Failed to save draft edits: ${err.message}`),
  });

  const moveToNext = () => {
    if (!draftedLeads || draftedLeads.length === 0) return;
    const currentIndex = draftedLeads.findIndex(l => l.id === selectedId);
    if (currentIndex !== -1 && currentIndex < draftedLeads.length - 1) {
      setSelectedId(draftedLeads[currentIndex + 1].id);
    } else if (draftedLeads.length > 1) {
      setSelectedId(draftedLeads[0].id); // loop back
    } else {
      setSelectedId(null);
    }
  };

  // Keyboard shortcut listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore shortcuts if the user is typing in input or textarea
      if (document.activeElement?.tagName === "INPUT" || document.activeElement?.tagName === "TEXTAREA") {
        return;
      }
      
      if (!selectedId) return;

      if (e.key.toLowerCase() === "a") {
        e.preventDefault();
        approveMutation.mutate(selectedId);
      } else if (e.key.toLowerCase() === "r") {
        e.preventDefault();
        setShowRejectModal(true);
      } else if (e.key.toLowerCase() === "s") {
        e.preventDefault();
        moveToNext();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [selectedId, draftedLeads, approveMutation]);

  if (leadsLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-64 space-y-4">
        <RotateCw className="h-8 w-8 text-brand-500 animate-spin" />
        <span className="text-slate-400 text-sm">Loading review queue...</span>
      </div>
    );
  }

  if (!draftedLeads || draftedLeads.length === 0) {
    return (
      <PlaceholderView
        icon={<CheckCircle className="h-12 w-12 text-emerald-400" />}
        title="Queue Clear!"
        description="All lead outreach drafts have been reviewed! Run another generate background job in the dashboard to draft more emails."
      />
    );
  }

  // Get current lead
  const currentLead = draftedLeads.find(l => l.id === selectedId);
  const emailObj = leadDetails?.emails?.[0];
  const { footer: complFooter } = splitFooter(emailObj?.body || "");

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 h-[calc(100vh-12rem)] min-h-[500px]">
      {/* LEFT PANE: LEAD SELECTION LIST */}
      <div className="lg:col-span-4 bg-slate-900/60 border border-slate-800 rounded-2xl flex flex-col overflow-hidden backdrop-blur-sm">
        <div className="p-4 border-b border-slate-800 bg-slate-900/40">
          <h3 className="text-sm font-bold tracking-wider text-slate-300 uppercase">
            Draft Queue ({draftedLeads.length})
          </h3>
          <p className="text-xs text-slate-500 mt-1">Select a lead to audit and approve</p>
        </div>
        <div className="flex-1 overflow-y-auto divide-y divide-slate-800/40">
          {draftedLeads.map(lead => {
            const isSelected = lead.id === selectedId;
            return (
              <button
                key={lead.id}
                onClick={() => setSelectedId(lead.id)}
                className={`w-full text-left p-4 transition flex flex-col space-y-1 hover:bg-slate-800/40 ${
                  isSelected ? "bg-brand-900/20 border-l-4 border-brand-500" : ""
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-200 truncate text-sm">
                    {lead.name || lead.domain}
                  </span>
                  <span className="text-xs text-slate-500">ID: {lead.id}</span>
                </div>
                <span className="text-xs text-slate-400 truncate">{lead.email}</span>
                <span className="text-xs text-slate-500 truncate">{lead.domain}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* RIGHT PANE: Telemetry & Outreach Editor */}
      <div className="lg:col-span-8 bg-slate-900/40 border border-slate-800 rounded-2xl flex flex-col overflow-hidden backdrop-blur-sm">
        {detailsLoading ? (
          <div className="flex-1 flex flex-col items-center justify-center space-y-4">
            <RotateCw className="h-8 w-8 text-brand-500 animate-spin" />
            <span className="text-slate-400 text-sm">Querying lead telemetry...</span>
          </div>
        ) : currentLead && leadDetails ? (
          <div className="flex-1 flex flex-col overflow-y-auto p-6 space-y-6">
            {/* Header Details */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-slate-800 pb-4">
              <div>
                <h2 className="text-xl font-extrabold text-slate-100">{leadDetails.name || leadDetails.domain}</h2>
                <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-slate-400 mt-1">
                  <span>Email: {leadDetails.email}</span>
                  <span>•</span>
                  <span>Website: <a href={leadDetails.website_url} target="_blank" rel="noreferrer" className="text-brand-400 hover:underline">{leadDetails.domain}</a></span>
                </div>
              </div>
              <div className="flex items-center space-x-2 mt-4 md:mt-0">
                <button
                  onClick={() => approveMutation.mutate(leadDetails.id)}
                  disabled={approveMutation.isPending}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-sm font-semibold rounded-xl transition shadow-lg shadow-emerald-900/20 flex items-center space-x-2"
                  title="Hotkey: A"
                >
                  <Check className="h-4 w-4" />
                  <span>Approve [A]</span>
                </button>
                <button
                  onClick={() => setShowRejectModal(true)}
                  disabled={rejectMutation.isPending}
                  className="px-4 py-2 bg-rose-600/20 hover:bg-rose-600/40 border border-rose-500/30 text-rose-400 text-sm font-semibold rounded-xl transition flex items-center space-x-2"
                  title="Hotkey: R"
                >
                  <X className="h-4 w-4" />
                  <span>Reject [R]</span>
                </button>
                <button
                  onClick={moveToNext}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-semibold rounded-xl transition flex items-center space-x-2"
                  title="Hotkey: S"
                >
                  <span>Skip [S]</span>
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>

            {/* Content Split: Left details, Right Screenshot */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Audit Findings */}
              <div className="space-y-4">
                <h4 className="text-sm font-bold uppercase tracking-wider text-slate-300">
                  Mapped Findings
                </h4>
                {leadDetails.analysis && leadDetails.analysis.service_map ? (
                  <div className="space-y-2">
                    {Object.entries(leadDetails.analysis.service_map).map(([service, entry]: [string, any]) => (
                      <div key={service} className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
                        <span className="text-xs font-bold text-brand-400 uppercase">{service}</span>
                        <p className="text-xs text-slate-300 leading-normal">{entry.evidence}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-3 bg-slate-900/20 text-slate-500 text-xs rounded-xl italic">
                    No findings mapped for this lead.
                  </div>
                )}

                <div className="p-3 bg-slate-950 border border-slate-800/40 rounded-xl space-y-2">
                  <span className="text-xs font-semibold text-slate-400">Score Audit Card:</span>
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="bg-slate-900/80 p-2 rounded-lg">
                      <span className="block text-slate-500 text-[10px]">PSI Performance</span>
                      <span className="text-sm font-extrabold text-slate-200">{leadDetails.analysis?.perf_score ?? "N/A"}</span>
                    </div>
                    <div className="bg-slate-900/80 p-2 rounded-lg">
                      <span className="block text-slate-500 text-[10px]">Broken Links</span>
                      <span className="text-sm font-extrabold text-rose-400">{leadDetails.analysis?.broken_links_count ?? 0}</span>
                    </div>
                    <div className="bg-slate-900/80 p-2 rounded-lg">
                      <span className="block text-slate-500 text-[10px]">SSL Certificate</span>
                      <span className={`text-xs font-extrabold ${leadDetails.analysis?.has_ssl ? "text-emerald-400" : "text-rose-400"}`}>
                        {leadDetails.analysis?.has_ssl ? "SECURE" : "MISSING"}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Screenshot */}
              <div className="space-y-4">
                <h4 className="text-sm font-bold uppercase tracking-wider text-slate-300">
                  Homepage Screenshot
                </h4>
                {leadDetails.scrape && leadDetails.scrape.screenshot_path ? (
                  <div className="aspect-[4/3] w-full border border-slate-850 rounded-xl overflow-hidden bg-slate-950 flex items-center justify-center relative group">
                    <img
                      src={api.getScreenshotUrl(leadDetails.id)}
                      alt={`${leadDetails.domain} screenshot`}
                      className="w-full h-full object-cover group-hover:scale-[1.03] transition duration-300"
                    />
                    <a
                      href={api.getScreenshotUrl(leadDetails.id)}
                      target="_blank"
                      rel="noreferrer"
                      className="absolute bottom-2 right-2 bg-slate-950/80 p-1.5 rounded-lg border border-slate-800 text-slate-400 hover:text-slate-200 transition"
                    >
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  </div>
                ) : (
                  <div className="aspect-[4/3] w-full border border-slate-800 rounded-xl bg-slate-950/40 flex flex-col items-center justify-center text-slate-500 space-y-2 text-xs">
                    <AlertTriangle className="h-6 w-6 text-slate-600" />
                    <span>No screenshot captured for this lead.</span>
                  </div>
                )}
              </div>
            </div>

            {/* Email Outreach Editor */}
            <div className="space-y-3 bg-slate-950 p-5 rounded-2xl border border-slate-850">
              <div className="flex justify-between items-center">
                <h4 className="text-sm font-bold uppercase tracking-wider text-slate-300">
                  Outreach Template Editor
                </h4>
                <div className="flex items-center space-x-2">
                  {isEditing ? (
                    <>
                      <button
                        onClick={() => saveMutation.mutate({ id: leadDetails.id, subject, body: bodyRaw })}
                        disabled={saveMutation.isPending}
                        className="px-3 py-1 bg-brand-600 text-white text-xs font-semibold rounded-lg hover:bg-brand-500 transition"
                      >
                        {saveMutation.isPending ? "Saving..." : "Save Draft"}
                      </button>
                      <button
                        onClick={() => {
                          // reset states
                          const email = leadDetails.emails[0];
                          const { mainBody } = splitFooter(email.body || "");
                          setSubject(email.subject || "");
                          setBodyRaw(mainBody || "");
                          setIsEditing(false);
                        }}
                        className="px-3 py-1 bg-slate-800 text-slate-300 text-xs font-semibold rounded-lg hover:bg-slate-700 transition"
                      >
                        Cancel
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={() => setIsEditing(true)}
                      className="px-3 py-1 bg-slate-900 border border-slate-800 hover:border-brand-500/20 text-brand-400 text-xs font-semibold rounded-lg transition"
                    >
                      Edit Custom Copy
                    </button>
                  )}
                </div>
              </div>

              <div className="space-y-3">
                <div>
                  <label className="block text-[11px] uppercase tracking-wider font-bold text-slate-500 mb-1">Subject Line</label>
                  <input
                    type="text"
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    disabled={!isEditing}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-brand-500 disabled:opacity-70 disabled:bg-slate-900/40"
                  />
                </div>
                <div>
                  <label className="block text-[11px] uppercase tracking-wider font-bold text-slate-500 mb-1">Email Body Text</label>
                  <textarea
                    rows={6}
                    value={bodyRaw}
                    onChange={(e) => setBodyRaw(e.target.value)}
                    disabled={!isEditing}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-200 focus:outline-none focus:border-brand-500 font-mono text-xs leading-relaxed disabled:opacity-70 disabled:bg-slate-900/40"
                  />
                </div>
                
                {/* CAN-SPAM Footer Preview */}
                {complFooter && (
                  <div className="bg-slate-900/60 border border-slate-850 p-3 rounded-lg text-[10px] text-slate-500 leading-normal font-mono">
                    <span className="block font-bold text-[9px] uppercase tracking-wider text-slate-400 mb-1">Compliance Footer (Auto-Appended)</span>
                    {complFooter}
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center space-y-2 text-slate-500">
            <span>Select a lead in the left list to begin human review</span>
          </div>
        )}
      </div>

      {/* REJECTION MODAL */}
      {showRejectModal && selectedId && (
        <div className="fixed inset-0 bg-slate-950/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-4 shadow-xl">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-bold text-slate-200">Reject Email Draft</h3>
              <button onClick={() => setShowRejectModal(false)} className="text-slate-400 hover:text-slate-200">
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="space-y-2">
              <label className="block text-xs font-semibold text-slate-400">Rejection Reason (Optional)</label>
              <textarea
                rows={3}
                placeholder="e.g. Inaccurate audit findings, incorrect contact person..."
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-brand-500"
              />
            </div>
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => setShowRejectModal(false)}
                className="px-4 py-2 bg-slate-800 text-slate-300 text-sm font-semibold rounded-xl hover:bg-slate-700 transition"
              >
                Cancel
              </button>
              <button
                onClick={() => rejectMutation.mutate({ id: selectedId, reason: rejectReason })}
                disabled={rejectMutation.isPending}
                className="px-4 py-2 bg-rose-600 text-white text-sm font-semibold rounded-xl hover:bg-rose-500 transition shadow-lg shadow-rose-950/20"
              >
                Confirm Reject
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ----------------------------------------------------
// VIEW 6: CAMPAIGN SEND CONSOLE
// ----------------------------------------------------
interface SendConsoleViewProps {
  onLaunchJob: () => void;
}
function SendConsoleView({ onLaunchJob }: SendConsoleViewProps) {
  const queryClient = useQueryClient();
  const [activeSendJobId, setActiveSendJobId] = useState<number | null>(null);
  const [logs, setLogs] = useState<string[]>([]);

  // Fetch configs
  const { data: config, isLoading: configLoading } = useQuery({
    queryKey: ["config"],
    queryFn: api.getConfig,
  });

  // Fetch stats
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["stats"],
    queryFn: api.getStats,
  });

  // Query jobs
  const { data: jobs } = useQuery({
    queryKey: ["jobs"],
    queryFn: api.getJobs,
    refetchInterval: 3000,
  });

  // Find latest send job
  const latestSendJob = jobs?.find(j => j.type === "send");
  const isJobRunning = latestSendJob?.status === "running" || latestSendJob?.status === "queued";

  // Auto-connect to SSE
  useEffect(() => {
    if (latestSendJob && (latestSendJob.status === "running" || latestSendJob.status === "queued")) {
      setActiveSendJobId(latestSendJob.id);
    } else {
      setActiveSendJobId(null);
    }
  }, [latestSendJob]);

  // Connect to SSE stream
  useEffect(() => {
    if (!activeSendJobId) return;

    const token = getStoredToken();
    const eventSource = new EventSource(`/api/events/jobs/${activeSendJobId}?token=${encodeURIComponent(token)}`);
    setLogs(["[Campaign Sender] Connecting to sending stream..."]);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const timestamp = new Date().toLocaleTimeString();
        let msg = `[${timestamp}] Job: ${data.status.toUpperCase()}`;
        if (data.done !== undefined && data.total !== undefined) {
          msg += ` | Sent: ${data.done}/${data.total} emails`;
        }
        if (data.error) {
          msg += ` | Error: ${data.error}`;
        }
        setLogs(prev => [...prev, msg]);

        if (["completed", "failed", "cancelled"].includes(data.status)) {
          eventSource.close();
          queryClient.invalidateQueries({ queryKey: ["stats"] });
          queryClient.invalidateQueries({ queryKey: ["jobs"] });
        }
      } catch (err) {
        // parser err
      }
    };

    return () => eventSource.close();
  }, [activeSendJobId, queryClient]);

  // Mutation to toggle dry_run
  const toggleDryRunMutation = useMutation({
    mutationFn: (dryRunValue: boolean) => {
      const updatedConfig = {
        send: {
          ...config?.send,
          dry_run: dryRunValue,
        },
      };
      return api.updateConfig(updatedConfig);
    },
    onSuccess: () => {
      alert("Sending mode updated successfully!");
      queryClient.invalidateQueries({ queryKey: ["config"] });
    },
    onError: (err: any) => alert(`Failed to update config: ${err.message}`),
  });

  // Mutation to launch send job
  const startCampaignMutation = useMutation({
    mutationFn: () => api.createJob("send", {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      onLaunchJob(); // redirect to jobs view
    },
    onError: (err: any) => alert(`Failed to launch campaign runner: ${err.message}`),
  });

  if (configLoading || statsLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-64 space-y-4">
        <RotateCw className="h-8 w-8 text-brand-500 animate-spin" />
        <span className="text-slate-400 text-sm">Querying send dashboard parameters...</span>
      </div>
    );
  }

  // Compliance variables
  const physicalAddress = config?.email?.physical_address || "";
  const unsubUrl = config?.email?.unsubscribe_base_url || "";
  const requireHumanReview = config?.send?.require_human_review ?? true;
  const isComplianceBlocker =
    !physicalAddress.trim ||
    physicalAddress.trim() === "" ||
    physicalAddress.trim() === "123 Main St, Anytown, USA" ||
    !unsubUrl.trim ||
    unsubUrl.trim() === "" ||
    unsubUrl.trim() === "http://localhost:8000/unsubscribe";

  const isDryRun = config?.send?.dry_run ?? true;
  const dailyLimit = config?.send?.daily_send_limit ?? 30;
  const sentTodayCount = stats?.sent ?? 0;
  const approvedCount = stats?.approved ?? 0;
  const draftCount = stats?.drafted ?? 0;

  const targetOutboxCount = requireHumanReview ? approvedCount : approvedCount + draftCount;

  // Percentage for daily limits progress
  const limitPercentage = Math.min(100, Math.round((sentTodayCount / dailyLimit) * 100));

  return (
    <div className="space-y-8">
      {/* CAN-SPAM Compliance Alert banner */}
      {isComplianceBlocker && (
        <div className="p-4 bg-rose-950/60 border border-rose-500/30 rounded-2xl flex items-start space-x-3 backdrop-blur-sm animate-pulse">
          <AlertTriangle className="h-6 w-6 text-rose-400 shrink-0 mt-0.5" />
          <div>
            <h4 className="text-sm font-bold text-rose-200">CAN-SPAM Compliance Protection Active</h4>
            <p className="text-xs text-rose-400 mt-1 leading-relaxed">
              Real email sending (Gmail API) is strictly blocked because your Settings contain either missing values or default placeholders for the **Physical Address** or **Unsubscribe URL**. 
              Please navigate to the **Settings** panel to configure valid compliance parameters.
            </p>
          </div>
        </div>
      )}

      {/* Outbox Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Cap gauge */}
        <div className="p-6 bg-slate-900/60 border border-slate-800 rounded-2xl shadow-lg relative overflow-hidden flex flex-col justify-between h-40">
          <div className="flex items-center justify-between">
            <span className="text-xs uppercase tracking-wider font-semibold text-slate-400">Daily Cap Threshold</span>
            <Send className="h-4 w-4 text-brand-400 opacity-80" />
          </div>
          <div className="space-y-2 mt-4">
            <div className="flex items-end justify-between">
              <span className="text-3xl font-extrabold text-slate-100">{sentTodayCount} <span className="text-xs text-slate-500 font-normal">/ {dailyLimit} sent today</span></span>
              <span className="text-xs font-semibold text-slate-400">{limitPercentage}%</span>
            </div>
            <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden border border-slate-850">
              <div
                className={`h-full transition-all duration-500 ${limitPercentage >= 100 ? "bg-rose-500" : "bg-brand-500"}`}
                style={{ width: `${limitPercentage}%` }}
              />
            </div>
          </div>
        </div>

        {/* Pending Approved Queue */}
        <div className="p-6 bg-slate-900/60 border border-slate-800 rounded-2xl shadow-lg flex flex-col justify-between h-40">
          <div className="flex items-center justify-between">
            <span className="text-xs uppercase tracking-wider font-semibold text-slate-400">Approved Outbox</span>
            <CheckCircle className="h-4 w-4 text-emerald-400 opacity-80" />
          </div>
          <div>
            <span className="text-3xl font-extrabold text-slate-100 block">{approvedCount}</span>
            <span className="text-xs text-slate-500 leading-normal mt-1 block">
              {requireHumanReview 
                ? "Emails approved by human review ready for immediate dispatch."
                : "Human review is disabled; approved drafts will queue for sending."
              }
            </span>
          </div>
        </div>

        {/* Sending Mode Status */}
        <div className="p-6 bg-slate-900/60 border border-slate-800 rounded-2xl shadow-lg flex flex-col justify-between h-40">
          <div className="flex items-center justify-between">
            <span className="text-xs uppercase tracking-wider font-semibold text-slate-400">Dispatch Mode</span>
            <Cpu className="h-4 w-4 text-blue-400 opacity-80" />
          </div>
          <div>
            <span className={`text-2xl font-extrabold block ${isDryRun ? "text-amber-500" : "text-emerald-500"}`}>
              {isDryRun ? "SIMULATION MODE" : "REAL SENDING OUTBOX"}
            </span>
            <span className="text-xs text-slate-500 leading-normal mt-1 block">
              {isDryRun 
                ? "Dry-runs are simulated and will write to audit event logs without calling the Gmail API." 
                : "Active outreach is fully engaged and will send emails to B2B targets using Gmail."
              }
            </span>
          </div>
        </div>
      </div>

      {/* Main Runner Controls */}
      <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-6 space-y-6">
        <h3 className="text-base font-bold text-slate-200 border-b border-slate-800 pb-3">Campaign Execution Engine</h3>
        
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 bg-slate-950 p-5 rounded-xl border border-slate-850">
          <div className="space-y-1">
            <h4 className="text-sm font-semibold text-slate-200">Outgoing Mail Authentication Safeguard</h4>
            <p className="text-xs text-slate-400 leading-relaxed max-w-xl">
              Toggle this switch to transition between testing mock outputs and running active production pipelines. 
              If safety checks fail due to non-compliant sender files, live campaigns are disabled.
            </p>
          </div>
          
          <div className="flex items-center space-x-3">
            <span className={`text-xs font-bold uppercase tracking-wider ${isDryRun ? "text-amber-500" : "text-emerald-500"}`}>
              {isDryRun ? "Simulator (Safe)" : "Gmail API Live"}
            </span>
            <button
              onClick={() => toggleDryRunMutation.mutate(!isDryRun)}
              disabled={isComplianceBlocker || toggleDryRunMutation.isPending}
              className={`w-14 h-8 rounded-full p-1 transition duration-200 focus:outline-none flex items-center ${
                isDryRun ? "bg-slate-800" : "bg-emerald-600"
              } ${isComplianceBlocker ? "opacity-40 cursor-not-allowed" : ""}`}
            >
              <div
                className={`w-6 h-6 rounded-full bg-slate-100 shadow-md transform transition duration-200 ${
                  isDryRun ? "translate-x-0" : "translate-x-6"
                }`}
              />
            </button>
          </div>
        </div>

        {/* Pipeline Runner Trigger */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-1">
            <h4 className="text-sm font-semibold text-slate-300">Run Outbox Campaign Dispatcher</h4>
            <p className="text-xs text-slate-500 leading-relaxed max-w-xl">
              This triggers the asynchronous campaign dispatch routine. It processes the outbox up to your daily limits, respects robots.txt compliance, skips unsubscribed targets, and rate-limits with politeness delays.
              {requireHumanReview 
                ? ` Found ${approvedCount} approved drafts ready.` 
                : ` Found ${approvedCount + draftCount} drafts ready.`
              }
            </p>
          </div>

          <button
            onClick={() => startCampaignMutation.mutate()}
            disabled={isJobRunning || startCampaignMutation.isPending || targetOutboxCount === 0}
            className="px-6 py-3 bg-brand-600 hover:bg-brand-500 disabled:bg-slate-850 disabled:text-slate-500 disabled:opacity-50 text-white font-bold rounded-xl shadow-lg shadow-brand-950/20 transition flex items-center space-x-2 whitespace-nowrap"
          >
            {isJobRunning ? (
              <>
                <RotateCw className="h-4 w-4 animate-spin" />
                <span>Job Executing...</span>
              </>
            ) : (
              <>
                <Play className="h-4 w-4" />
                <span>Start Campaign Runner</span>
              </>
            )}
          </button>
        </div>

        {/* Live SSE Logging terminal */}
        {logs.length > 0 && (
          <div className="space-y-2 mt-6">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">Active Streaming Logs</span>
            <div className="w-full bg-slate-950/80 border border-slate-850 rounded-xl p-4 font-mono text-xs text-slate-300 space-y-1.5 h-64 overflow-y-auto leading-relaxed shadow-inner">
              {logs.map((log, idx) => (
                <div key={idx} className={log.includes("ERROR") ? "text-rose-400" : log.includes("Job status: COMPLETED") ? "text-emerald-400" : ""}>
                  {log}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ----------------------------------------------------
// VIEW 7: GLOBAL SETTINGS & SUPPRESSION MANAGER
// ----------------------------------------------------
function SettingsView() {
  const queryClient = useQueryClient();
  const [activeSubTab, setActiveSubTab] = useState<"compliance" | "scraper" | "llm" | "suppression">("compliance");
  const [suppressionEmail, setSuppressionEmail] = useState<string>("");
  const [suppressionSearch, setSuppressionSearch] = useState<string>("");

  // Fetch configs
  const { data: config, isLoading: configLoading } = useQuery({
    queryKey: ["config"],
    queryFn: api.getConfig,
  });

  // Fetch suppressions list
  const { data: suppressions, isLoading: suppLoading } = useQuery({
    queryKey: ["suppressions"],
    queryFn: api.getSuppressions,
    enabled: activeSubTab === "suppression",
  });

  // Local state for configuration inputs
  const [complianceState, setComplianceState] = useState({
    sender_name: "",
    sender_company: "",
    physical_address: "",
    unsubscribe_base_url: "",
    daily_send_limit: 30,
    send_delay_seconds: 5,
    require_human_review: true,
  });

  const [scraperState, setScraperState] = useState({
    concurrency: 3,
    timeout_seconds: 30,
    politeness_delay_ms: 1000,
    check_robots_txt: true,
    max_findings: 3,
  });

  const [llmState, setLlmState] = useState({
    provider: "anthropic",
    model: "claude-3-5-sonnet-latest",
    temperature: 0.1,
  });

  // Sync inputs with config query values
  useEffect(() => {
    if (config) {
      setComplianceState({
        sender_name: config.email?.sender_name || "",
        sender_company: config.email?.sender_company || "",
        physical_address: config.email?.physical_address || "",
        unsubscribe_base_url: config.email?.unsubscribe_base_url || "",
        daily_send_limit: config.send?.daily_send_limit ?? 30,
        send_delay_seconds: config.send?.send_delay_seconds ?? 5,
        require_human_review: config.send?.require_human_review ?? true,
      });

      setScraperState({
        concurrency: config.scrape?.concurrency ?? 3,
        timeout_seconds: config.scrape?.timeout_seconds ?? 30,
        politeness_delay_ms: config.scrape?.politeness_delay_ms ?? 1000,
        check_robots_txt: config.scrape?.check_robots_txt ?? true,
        max_findings: config.service_map?.max_findings ?? 3,
      });

      setLlmState({
        provider: config.email?.provider || "anthropic",
        model: config.email?.model || "claude-3-5-sonnet-latest",
        temperature: config.email?.temperature ?? 0.1,
      });
    }
  }, [config]);

  // Mutations to save configuration
  const saveConfigMutation = useMutation({
    mutationFn: (updatedPayload: Record<string, any>) => api.updateConfig(updatedPayload),
    onSuccess: () => {
      alert("Settings updated and saved successfully!");
      queryClient.invalidateQueries({ queryKey: ["config"] });
    },
    onError: (err: any) => alert(`Failed to save settings: ${err.message}`),
  });

  // Suppression list mutations
  const addSuppressionMutation = useMutation({
    mutationFn: ({ email, reason }: { email: string; reason: string }) => api.addSuppression(email, reason),
    onSuccess: () => {
      alert("Email suppressed successfully!");
      setSuppressionEmail("");
      queryClient.invalidateQueries({ queryKey: ["suppressions"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
    },
    onError: (err: any) => alert(`Failed to suppress email: ${err.message}`),
  });

  const deleteSuppressionMutation = useMutation({
    mutationFn: (email: string) => api.deleteSuppression(email),
    onSuccess: () => {
      alert("Email removed from suppression list!");
      queryClient.invalidateQueries({ queryKey: ["suppressions"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
    },
    onError: (err: any) => alert(`Failed to remove email from suppression: ${err.message}`),
  });

  // Handle saving compliance/sending forms
  const handleSaveCompliance = (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      email: {
        ...config?.email,
        sender_name: complianceState.sender_name,
        sender_company: complianceState.sender_company,
        physical_address: complianceState.physical_address,
        unsubscribe_base_url: complianceState.unsubscribe_base_url,
      },
      send: {
        ...config?.send,
        daily_send_limit: Number(complianceState.daily_send_limit),
        send_delay_seconds: Number(complianceState.send_delay_seconds),
        require_human_review: complianceState.require_human_review,
      },
    };
    saveConfigMutation.mutate(payload);
  };

  // Handle saving scraper parameters
  const handleSaveScraper = (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      scrape: {
        ...config?.scrape,
        concurrency: Number(scraperState.concurrency),
        timeout_seconds: Number(scraperState.timeout_seconds),
        politeness_delay_ms: Number(scraperState.politeness_delay_ms),
        check_robots_txt: scraperState.check_robots_txt,
      },
      service_map: {
        ...config?.service_map,
        max_findings: Number(scraperState.max_findings),
      },
    };
    saveConfigMutation.mutate(payload);
  };

  // Handle saving LLM options
  const handleSaveLLM = (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      email: {
        ...config?.email,
        provider: llmState.provider,
        model: llmState.model,
        temperature: Number(llmState.temperature),
      },
    };
    saveConfigMutation.mutate(payload);
  };

  // Add suppression trigger
  const handleAddSuppressionSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!suppressionEmail.trim()) return;
    addSuppressionMutation.mutate({ email: suppressionEmail.trim(), reason: "manual" });
  };

  if (configLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-64 space-y-4">
        <RotateCw className="h-8 w-8 text-brand-500 animate-spin" />
        <span className="text-slate-400 text-sm">Querying configurations...</span>
      </div>
    );
  }

  // Compliance warning check
  const hasPlaceholders =
    !complianceState.physical_address.trim ||
    complianceState.physical_address.trim() === "" ||
    complianceState.physical_address.trim() === "123 Main St, Anytown, USA" ||
    !complianceState.unsubscribe_base_url.trim ||
    complianceState.unsubscribe_base_url.trim() === "" ||
    complianceState.unsubscribe_base_url.trim() === "http://localhost:8000/unsubscribe";

  // Filter suppressions client-side
  const filteredSuppressions = suppressions
    ? suppressions.filter(s => s.email.toLowerCase().includes(suppressionSearch.toLowerCase()))
    : [];

  return (
    <div className="space-y-8">
      {/* Subtab selection header */}
      <div className="flex border-b border-slate-800 overflow-x-auto pb-px scrollbar-none">
        <button
          onClick={() => setActiveSubTab("compliance")}
          className={`px-5 py-3 text-sm font-semibold transition border-b-2 flex items-center space-x-2 shrink-0 ${
            activeSubTab === "compliance"
              ? "border-brand-500 text-brand-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <span>Compliance & Sending</span>
        </button>
        <button
          onClick={() => setActiveSubTab("scraper")}
          className={`px-5 py-3 text-sm font-semibold transition border-b-2 flex items-center space-x-2 shrink-0 ${
            activeSubTab === "scraper"
              ? "border-brand-500 text-brand-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <span>Scraper & Findings</span>
        </button>
        <button
          onClick={() => setActiveSubTab("llm")}
          className={`px-5 py-3 text-sm font-semibold transition border-b-2 flex items-center space-x-2 shrink-0 ${
            activeSubTab === "llm"
              ? "border-brand-500 text-brand-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <span>Outreach LLM Model</span>
        </button>
        <button
          onClick={() => setActiveSubTab("suppression")}
          className={`px-5 py-3 text-sm font-semibold transition border-b-2 flex items-center space-x-2 shrink-0 ${
            activeSubTab === "suppression"
              ? "border-brand-500 text-brand-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <span>Suppression List</span>
        </button>
      </div>

      {/* SUB-TABS VIEWS */}
      {activeSubTab === "compliance" && (
        <form onSubmit={handleSaveCompliance} className="bg-slate-900/40 border border-slate-800 p-6 rounded-2xl space-y-6 max-w-3xl">
          <div className="flex justify-between items-center border-b border-slate-800 pb-3">
            <h3 className="text-base font-bold text-slate-200">Email Config & CAN-SPAM Compliance</h3>
            <button
              type="submit"
              disabled={saveConfigMutation.isPending}
              className="px-4 py-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg transition"
            >
              Save Configuration
            </button>
          </div>

          {hasPlaceholders && (
            <div className="p-4 bg-rose-950/40 border border-rose-500/20 text-rose-400 text-xs rounded-xl flex items-start space-x-2">
              <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
              <span>
                **CAN-SPAM Warning:** You are using placeholder details for either your Physical Address or Unsubscribe URL. 
                Real outgoing campaign dispatches will remain locked in Simulator-only mode until these settings are saved with valid production values.
              </span>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-1">
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Sender Name</label>
              <input
                type="text"
                value={complianceState.sender_name}
                onChange={e => setComplianceState({ ...complianceState, sender_name: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-brand-500"
              />
            </div>
            <div className="space-y-1">
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Sender Company</label>
              <input
                type="text"
                value={complianceState.sender_company}
                onChange={e => setComplianceState({ ...complianceState, sender_company: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-brand-500"
              />
            </div>
            <div className="space-y-1 md:col-span-2">
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Compliance Physical Address</label>
              <input
                type="text"
                value={complianceState.physical_address}
                onChange={e => setComplianceState({ ...complianceState, physical_address: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-brand-500 font-mono text-xs"
              />
            </div>
            <div className="space-y-1 md:col-span-2">
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Unsubscribe Landing Base URL</label>
              <input
                type="text"
                value={complianceState.unsubscribe_base_url}
                onChange={e => setComplianceState({ ...complianceState, unsubscribe_base_url: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-brand-500 font-mono text-xs"
              />
            </div>
            <div className="space-y-1">
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Daily Outreach Limit Cap</label>
              <input
                type="number"
                value={complianceState.daily_send_limit}
                onChange={e => setComplianceState({ ...complianceState, daily_send_limit: Number(e.target.value) })}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-brand-500"
              />
            </div>
            <div className="space-y-1">
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Throttling Delay (Seconds)</label>
              <input
                type="number"
                value={complianceState.send_delay_seconds}
                onChange={e => setComplianceState({ ...complianceState, send_delay_seconds: Number(e.target.value) })}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-brand-500"
              />
            </div>
            <div className="md:col-span-2 flex items-center justify-between p-3 bg-slate-950 rounded-xl border border-slate-850">
              <div className="space-y-0.5">
                <span className="block text-xs font-bold text-slate-200">Require Human Review Approval</span>
                <span className="block text-[10px] text-slate-500">If enabled, emails must be approved manually in the Review tab before dispatching.</span>
              </div>
              <button
                type="button"
                onClick={() => setComplianceState({ ...complianceState, require_human_review: !complianceState.require_human_review })}
                className={`w-12 h-7 rounded-full p-1 transition duration-200 flex items-center ${
                  complianceState.require_human_review ? "bg-brand-600" : "bg-slate-800"
                }`}
              >
                <div
                  className={`w-5 h-5 rounded-full bg-slate-100 shadow-md transform transition duration-200 ${
                    complianceState.require_human_review ? "translate-x-5" : "translate-x-0"
                  }`}
                />
              </button>
            </div>
          </div>
        </form>
      )}

      {activeSubTab === "scraper" && (
        <form onSubmit={handleSaveScraper} className="bg-slate-900/40 border border-slate-800 p-6 rounded-2xl space-y-6 max-w-3xl">
          <div className="flex justify-between items-center border-b border-slate-800 pb-3">
            <h3 className="text-base font-bold text-slate-200">Scraper Concurrency & Politeness Settings</h3>
            <button
              type="submit"
              disabled={saveConfigMutation.isPending}
              className="px-4 py-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg transition"
            >
              Save Configuration
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-1">
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Browser Concurrency Limit</label>
              <input
                type="number"
                value={scraperState.concurrency}
                onChange={e => setScraperState({ ...scraperState, concurrency: Number(e.target.value) })}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-brand-500"
              />
            </div>
            <div className="space-y-1">
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Page Timeout (Seconds)</label>
              <input
                type="number"
                value={scraperState.timeout_seconds}
                onChange={e => setScraperState({ ...scraperState, timeout_seconds: Number(e.target.value) })}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-brand-500"
              />
            </div>
            <div className="space-y-1">
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Politeness Delay (ms)</label>
              <input
                type="number"
                value={scraperState.politeness_delay_ms}
                onChange={e => setScraperState({ ...scraperState, politeness_delay_ms: Number(e.target.value) })}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-brand-500"
              />
            </div>
            <div className="space-y-1">
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Max Weakness Findings / Lead</label>
              <input
                type="number"
                value={scraperState.max_findings}
                onChange={e => setScraperState({ ...scraperState, max_findings: Number(e.target.value) })}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-brand-500"
              />
            </div>
            <div className="md:col-span-2 flex items-center justify-between p-3 bg-slate-950 rounded-xl border border-slate-850">
              <div className="space-y-0.5">
                <span className="block text-xs font-bold text-slate-200">Respect Robots.txt Exclusions</span>
                <span className="block text-[10px] text-slate-500">If enabled, the scraper parses robots.txt and drops directories blacklisted by hosts.</span>
              </div>
              <button
                type="button"
                onClick={() => setScraperState({ ...scraperState, check_robots_txt: !scraperState.check_robots_txt })}
                className={`w-12 h-7 rounded-full p-1 transition duration-200 flex items-center ${
                  scraperState.check_robots_txt ? "bg-brand-600" : "bg-slate-800"
                }`}
              >
                <div
                  className={`w-5 h-5 rounded-full bg-slate-100 shadow-md transform transition duration-200 ${
                    scraperState.check_robots_txt ? "translate-x-5" : "translate-x-0"
                  }`}
                />
              </button>
            </div>
          </div>
        </form>
      )}

      {activeSubTab === "llm" && (
        <form onSubmit={handleSaveLLM} className="bg-slate-900/40 border border-slate-800 p-6 rounded-2xl space-y-6 max-w-3xl">
          <div className="flex justify-between items-center border-b border-slate-800 pb-3">
            <h3 className="text-base font-bold text-slate-200">Outreach Prompting Models (LangChain client)</h3>
            <button
              type="submit"
              disabled={saveConfigMutation.isPending}
              className="px-4 py-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg transition"
            >
              Save Configuration
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-1">
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">LLM Provider</label>
              <select
                value={llmState.provider}
                onChange={e => setLlmState({ ...llmState, provider: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-brand-500"
              >
                <option value="anthropic">Anthropic Claude</option>
                <option value="openai">OpenAI GPT</option>
                <option value="google">Google Gemini</option>
              </select>
            </div>
            <div className="space-y-1">
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Model Name / Alias</label>
              <input
                type="text"
                value={llmState.model}
                onChange={e => setLlmState({ ...llmState, model: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-brand-500"
              />
            </div>
            <div className="space-y-1">
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Temperature ({llmState.temperature})</label>
              <input
                type="range"
                min="0.0"
                max="1.0"
                step="0.05"
                value={llmState.temperature}
                onChange={e => setLlmState({ ...llmState, temperature: Number(e.target.value) })}
                className="w-full h-2 bg-slate-950 rounded-lg appearance-none cursor-pointer accent-brand-500 mt-3"
              />
            </div>
          </div>
        </form>
      )}

      {activeSubTab === "suppression" && (
        <div className="bg-slate-900/40 border border-slate-800 p-6 rounded-2xl space-y-6 max-w-4xl">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-base font-bold text-slate-200">Suppression Registry & Campaign Blacklist</h3>
            <p className="text-xs text-slate-500 mt-1">
              Emails added here are blocked from being ingested and will be skipped by the send campaign dispatch runner.
            </p>
          </div>

          {/* Add Form */}
          <form onSubmit={handleAddSuppressionSubmit} className="flex flex-col sm:flex-row gap-3 bg-slate-950 p-4 rounded-xl border border-slate-850">
            <div className="flex-1 space-y-1">
              <input
                type="email"
                required
                placeholder="Enter lead email to suppress (e.g. boss@targetcompany.com)..."
                value={suppressionEmail}
                onChange={e => setSuppressionEmail(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 text-sm text-slate-200 focus:outline-none focus:border-brand-500"
              />
            </div>
            <button
              type="submit"
              disabled={addSuppressionMutation.isPending}
              className="px-5 py-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-bold rounded-xl transition flex items-center justify-center space-x-1 whitespace-nowrap"
            >
              <span>Add Opt-out Email</span>
            </button>
          </form>

          {/* Search and Table */}
          <div className="space-y-4">
            <div className="flex items-center bg-slate-950 px-3.5 py-2 rounded-xl border border-slate-850 max-w-md">
              <Search className="h-4 w-4 text-slate-500 mr-2" />
              <input
                type="text"
                placeholder="Search suppressed emails..."
                value={suppressionSearch}
                onChange={e => setSuppressionSearch(e.target.value)}
                className="bg-transparent border-none text-sm text-slate-200 focus:outline-none w-full placeholder-slate-600"
              />
            </div>

            {suppLoading ? (
              <div className="flex justify-center py-12">
                <RotateCw className="h-6 w-6 text-brand-500 animate-spin" />
              </div>
            ) : filteredSuppressions.length > 0 ? (
              <div className="border border-slate-800 rounded-xl overflow-hidden bg-slate-950/20">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="bg-slate-950/70 border-b border-slate-800 text-slate-400 font-bold uppercase tracking-wider">
                      <th className="p-3.5">Suppressed Email Address</th>
                      <th className="p-3.5">Reason</th>
                      <th className="p-3.5">Added Date</th>
                      <th className="p-3.5 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/40 text-slate-300">
                    {filteredSuppressions.map(supp => (
                      <tr key={supp.email} className="hover:bg-slate-900/30 transition">
                        <td className="p-3.5 font-semibold text-slate-200">{supp.email}</td>
                        <td className="p-3.5">
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold border border-slate-800 bg-slate-900 text-slate-400">
                            {supp.reason}
                          </span>
                        </td>
                        <td className="p-3.5 text-slate-400">
                          {new Date(supp.added_at).toLocaleString()}
                        </td>
                        <td className="p-3.5 text-right">
                          <button
                            onClick={() => {
                              if (confirm(`Are you sure you want to remove '${supp.email}' from suppression?`)) {
                                deleteSuppressionMutation.mutate(supp.email);
                              }
                            }}
                            className="p-1.5 hover:bg-slate-800/60 rounded-lg text-slate-400 hover:text-rose-400 transition"
                            title="Remove suppression"
                          >
                            <X className="h-4 w-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-12 text-slate-500 text-xs italic bg-slate-950/20 border border-dashed border-slate-800 rounded-xl">
                No matching suppressed emails found in blacklist.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ----------------------------------------------------
// VIEW 8: LLM MODEL BAKEOFF OUTPOST
// ----------------------------------------------------
function BakeoffView() {
  const [sampleSize, setSampleSize] = useState<number>(2);
  const [selectedModels, setSelectedModels] = useState<string[]>([
    "claude-sonnet-4-6:anthropic",
    "gpt-5.4-mini:openai",
    "gemini-flash:google"
  ]);
  const [results, setResults] = useState<any[] | null>(null);
  const [activeLeadIndex, setActiveLeadIndex] = useState<number>(0);

  const modelOptions = [
    { label: "Claude Sonnet (Anthropic)", value: "claude-sonnet-4-6:anthropic" },
    { label: "GPT-4o Mini (OpenAI)", value: "gpt-5.4-mini:openai" },
    { label: "Gemini Flash (Google)", value: "gemini-flash:google" }
  ];

  const handleModelToggle = (modelValue: string) => {
    if (selectedModels.includes(modelValue)) {
      if (selectedModels.length > 1) {
        setSelectedModels(selectedModels.filter(m => m !== modelValue));
      } else {
        alert("You must select at least one model for bake-off comparison!");
      }
    } else {
      setSelectedModels([...selectedModels, modelValue]);
    }
  };

  const bakeoffMutation = useMutation({
    mutationFn: () => api.runBakeoff(sampleSize, selectedModels),
    onSuccess: (data) => {
      if (data && data.length > 0) {
        setResults(data);
        setActiveLeadIndex(0);
      } else {
        alert("No eligible leads found in the database. Ensure you have leads in 'analyzed' or 'drafted' status first!");
      }
    },
    onError: (err: any) => {
      alert(`Bake-off execution failed: ${err.message}`);
    }
  });

  const getCheapestModel = (runs: any[]) => {
    if (!runs || runs.length === 0) return null;
    return runs.reduce((cheapest, run) => 
      run.estimated_cost_usd < cheapest.estimated_cost_usd ? run : cheapest
    , runs[0]).model;
  };

  const getFastestModel = (runs: any[]) => {
    if (!runs || runs.length === 0) return null;
    return runs.reduce((fastest, run) => 
      run.latency_s < fastest.latency_s ? run : fastest
    , runs[0]).model;
  };

  return (
    <div className="space-y-8">
      <div className="bg-slate-900/40 border border-slate-800 p-6 rounded-2xl space-y-6">
        <div className="border-b border-slate-800 pb-3">
          <h3 className="text-base font-bold text-slate-200">A/B LLM Model Bake-off Console</h3>
          <p className="text-xs text-slate-500 mt-1">
            Compare latency, character-token pricing, subject lines, and draft styles side-by-side across Claude, GPT, and Gemini.
          </p>
        </div>

        <div className="flex flex-col md:flex-row gap-6 items-end">
          <div className="space-y-2">
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Evaluation Sample Size</label>
            <input
              type="number"
              min={1}
              max={5}
              value={sampleSize}
              onChange={e => setSampleSize(Number(e.target.value))}
              className="w-32 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-brand-500"
            />
          </div>

          <div className="flex-1 space-y-2">
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Target Models</label>
            <div className="flex flex-wrap gap-3">
              {modelOptions.map(opt => {
                const checked = selectedModels.includes(opt.value);
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => handleModelToggle(opt.value)}
                    className={`px-3 py-2 text-xs font-semibold border rounded-xl transition ${
                      checked
                        ? "bg-brand-900/20 border-brand-500 text-brand-400"
                        : "bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {opt.label}
                  </button>
                );
              })}
            </div>
          </div>

          <button
            onClick={() => bakeoffMutation.mutate()}
            disabled={bakeoffMutation.isPending}
            className="px-6 py-2.5 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-bold rounded-xl transition flex items-center space-x-2"
          >
            {bakeoffMutation.isPending ? (
              <>
                <RotateCw className="h-4 w-4 animate-spin" />
                <span>Baking Outposts...</span>
              </>
            ) : (
              <>
                <Play className="h-4 w-4" />
                <span>Run A/B Comparison</span>
              </>
            )}
          </button>
        </div>
      </div>

      {bakeoffMutation.isPending && (
        <div className="bg-slate-900/20 border border-slate-800 border-dashed p-12 rounded-2xl flex flex-col items-center justify-center space-y-4 text-center">
          <RotateCw className="h-10 w-10 text-brand-500 animate-spin" />
          <h4 className="text-sm font-bold text-slate-300">Comparing Generations...</h4>
          <p className="text-xs text-slate-500 max-w-md leading-relaxed">
            Spawning concurrent model requests across target providers. Generating custom subjects, email body text, counting cost profiles, and tracking latencies.
          </p>
        </div>
      )}

      {results && results.length > 0 && !bakeoffMutation.isPending && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left panel: Sample Leads selector */}
          <div className="lg:col-span-3 bg-slate-900/60 border border-slate-800 rounded-2xl flex flex-col overflow-hidden">
            <div className="p-4 border-b border-slate-800 bg-slate-900/40">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Evaluation Sample Leads</span>
            </div>
            <div className="divide-y divide-slate-800/40 overflow-y-auto">
              {results.map((res, idx) => {
                const isActive = idx === activeLeadIndex;
                return (
                  <button
                    key={res.lead_id}
                    onClick={() => setActiveLeadIndex(idx)}
                    className={`w-full text-left p-4 transition flex flex-col hover:bg-slate-800/40 ${
                      isActive ? "bg-brand-900/20 border-l-4 border-brand-500" : ""
                    }`}
                  >
                    <span className="font-semibold text-slate-200 text-sm truncate">{res.lead_name || `Lead #${res.lead_id}`}</span>
                    <span className="text-xs text-slate-500 truncate">{res.website_url}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Right panel: Side by Side models output */}
          <div className="lg:col-span-9 space-y-6">
            <div className="flex items-center justify-between bg-slate-900/40 p-4 border border-slate-800 rounded-2xl">
              <div>
                <h4 className="font-bold text-slate-200">{results[activeLeadIndex].lead_name || "Lead Details"}</h4>
                <a href={results[activeLeadIndex].website_url} target="_blank" rel="noreferrer" className="text-xs text-brand-400 hover:underline">
                  {results[activeLeadIndex].website_url}
                </a>
              </div>
              <span className="text-xs text-slate-500 font-mono">Lead ID: {results[activeLeadIndex].lead_id}</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {results[activeLeadIndex].runs.map((run: any) => {
                const isCheapest = run.model === getCheapestModel(results[activeLeadIndex].runs);
                const isFastest = run.model === getFastestModel(results[activeLeadIndex].runs);
                
                return (
                  <div key={run.model} className="bg-slate-900/40 border border-slate-800 rounded-2xl flex flex-col justify-between overflow-hidden shadow-lg">
                    {/* Header */}
                    <div className="p-4 border-b border-slate-800 bg-slate-900/60 flex flex-col space-y-1">
                      <div className="flex justify-between items-center">
                        <span className="font-bold text-slate-200 text-sm">{run.model}</span>
                        <span className="text-[10px] text-slate-500 uppercase tracking-wider font-bold">{run.provider}</span>
                      </div>
                      <div className="flex flex-wrap gap-1.5 mt-1">
                        {isFastest && (
                          <span className="bg-emerald-950/40 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded text-[8px] font-bold">
                            ⚡ FASTEST
                          </span>
                        )}
                        {isCheapest && (
                          <span className="bg-blue-950/40 text-blue-400 border border-blue-500/20 px-2 py-0.5 rounded text-[8px] font-bold">
                            💎 CHEAPEST
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Telemetry metadata */}
                    <div className="p-4 border-b border-slate-800 bg-slate-950/40 grid grid-cols-2 gap-2 text-center text-xs font-mono">
                      <div className="bg-slate-900/60 p-2 rounded-lg border border-slate-850">
                        <span className="block text-[9px] text-slate-500">LATENCY</span>
                        <span className="font-bold text-slate-200">{run.latency_s}s</span>
                      </div>
                      <div className="bg-slate-900/60 p-2 rounded-lg border border-slate-850">
                        <span className="block text-[9px] text-slate-500">EST. COST</span>
                        <span className="font-bold text-slate-200">${run.estimated_cost_usd}</span>
                      </div>
                    </div>

                    {/* Email output */}
                    <div className="p-4 flex-1 space-y-3">
                      <div>
                        <span className="block text-[9px] uppercase tracking-wider font-bold text-slate-500 mb-1">Subject</span>
                        <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-850 text-xs text-slate-300 font-sans leading-normal">
                          {run.subject}
                        </div>
                      </div>
                      <div>
                        <span className="block text-[9px] uppercase tracking-wider font-bold text-slate-500 mb-1">Body Text</span>
                        <div className="bg-slate-950 p-3 rounded-lg border border-slate-850 font-mono text-[10px] text-slate-300 h-64 overflow-y-auto whitespace-pre-wrap leading-relaxed">
                          {run.body}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ----------------------------------------------------
// VIEW 9: PLACEHOLDER CONSOLE VIEW
// ----------------------------------------------------
interface PlaceholderViewProps {
  icon: React.ReactNode;
  title: string;
  description: string;
}
function PlaceholderView({ icon, title, description }: PlaceholderViewProps) {
  return (
    <div className="flex flex-col items-center justify-center text-center max-w-xl mx-auto h-[400px] space-y-4">
      <div className="bg-slate-900 border border-slate-800 p-4 rounded-full shadow-lg">
        {icon}
      </div>
      <h3 className="text-xl font-bold text-slate-200">{title}</h3>
      <p className="text-sm text-slate-400 leading-relaxed">
        {description}
      </p>
    </div>
  );
}
