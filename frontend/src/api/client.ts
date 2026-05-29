// API base utilities and endpoints for the sales engine dashboard

export const TOKEN_KEY = "sales_engine_token";

export function getStoredToken(): string {
  return localStorage.getItem(TOKEN_KEY) || "";
}

export function setStoredToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export async function apiRequest<T>(
  path: string, 
  options: RequestInit = {}
): Promise<T> {
  const token = getStoredToken();
  const headers = new Headers(options.headers || {});
  
  if (token) {
    headers.set("X-API-Token", token);
  }
  
  if (options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(path, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorMessage = `HTTP error! Status: ${response.status}`;
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorMessage;
    } catch {
      // JSON parsing failed, keep default error
    }
    
    if (response.status === 401) {
      throw new Error("UNAUTHORIZED: Invalid or missing API token.");
    }
    throw new Error(errorMessage);
  }

  // Handle empty or file responses
  const contentType = response.headers.get("Content-Type") || "";
  if (contentType.includes("application/json")) {
    return response.json() as Promise<T>;
  }
  
  return {} as Promise<T>;
}

// REST endpoints API methods
export const api = {
  // Leads API
  getLeads: (status?: string) => {
    const url = status ? `/api/leads?status=${status}` : "/api/leads";
    return apiRequest<any[]>(url);
  },
  
  getLead: (id: number) => {
    return apiRequest<any>(`/api/leads/${id}`);
  },

  approveLeadEmail: (id: number) => {
    return apiRequest<{ success: boolean; message: string }>(`/api/leads/${id}/approve`, {
      method: "POST",
    });
  },

  rejectLeadEmail: (id: number, rejectReason?: string) => {
    return apiRequest<{ success: boolean; message: string }>(`/api/leads/${id}/reject`, {
      method: "POST",
      body: JSON.stringify({ reject_reason: rejectReason }),
    });
  },

  editLeadEmail: (id: number, subject: string, body: string) => {
    return apiRequest<{ success: boolean; message: string }>(`/api/leads/${id}/edit`, {
      method: "POST",
      body: JSON.stringify({ subject, body }),
    });
  },

  // Suppression List API
  getSuppressions: () => {
    return apiRequest<any[]>("/api/suppression");
  },

  addSuppression: (email: string, reason: string = "manual") => {
    return apiRequest<any>("/api/suppression", {
      method: "POST",
      body: JSON.stringify({ email, reason }),
    });
  },

  deleteSuppression: (email: string) => {
    return apiRequest<{ success: boolean; message: string }>(`/api/suppression/${encodeURIComponent(email)}`, {
      method: "DELETE",
    });
  },

  runBakeoff: (sampleSize: number, models: string[]) => {
    return apiRequest<any[]>("/api/bakeoff", {
      method: "POST",
      body: JSON.stringify({ sample_size: sampleSize, models }),
    });
  },
  
  getScreenshotUrl: (id: number) => {
    const token = getStoredToken();
    return `/api/screenshots/${id}?token=${encodeURIComponent(token)}`;
  },
  
  getStats: () => {
    return apiRequest<Record<string, number>>("/api/stats");
  },
  
  // Config API
  getConfig: () => {
    return apiRequest<Record<string, any>>("/api/config");
  },
  
  updateConfig: (payload: Record<string, any>) => {
    return apiRequest<{ success: boolean; message: string }>("/api/config", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  
  // Jobs API
  createJob: (type: string, params: Record<string, any> = {}) => {
    return apiRequest<any>("/api/jobs", {
      method: "POST",
      body: JSON.stringify({ type, params }),
    });
  },
  
  getJobs: () => {
    return apiRequest<any[]>("/api/jobs");
  },
  
  getJob: (id: number) => {
    return apiRequest<any>(`/api/jobs/${id}`);
  },
  
  cancelJob: (id: number) => {
    return apiRequest<{ success: boolean; message: string }>(`/api/jobs/${id}/cancel`, {
      method: "POST",
    });
  },
};
