import type {
  DashboardMetrics,
  Lead,
  FollowUp,
  LeadSourceMetric,
  AIInsight,
  NotificationItem,
} from '../types/admissions';

// Environment variable for backend API endpoint (when connected in production)
const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || '';

export interface ApiResponse<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  sourceConnected: boolean;
}

const LOCAL_STORAGE_KEY = 'ai_lead_desk_local_leads';

/**
 * Reads local leads created by counsellor in the active browser session
 */
export const getLocalSessionLeads = (): Lead[] => {
  try {
    const raw = sessionStorage.getItem(LOCAL_STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw);
  } catch {
    return [];
  }
};

/**
 * Saves a new lead locally in current browser session
 */
export const saveLocalSessionLead = (newLead: Omit<Lead, 'id' | 'isLocalSession'>): Lead => {
  const currentLeads = getLocalSessionLeads();
  const lead: Lead = {
    ...newLead,
    id: `local-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
    isLocalSession: true,
  };
  const updated = [lead, ...currentLeads];
  try {
    sessionStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(updated));
  } catch (err) {
    console.warn('Could not persist to sessionStorage:', err);
  }
  return lead;
};

/**
 * Clears local session leads
 */
export const clearLocalSessionLeads = (): void => {
  try {
    sessionStorage.removeItem(LOCAL_STORAGE_KEY);
  } catch (err) {
    console.warn(err);
  }
};

/**
 * Fetches dashboard summary metrics.
 * When backend is not connected, returns null values with sourceConnected: false.
 * If local leads exist, computes metrics from local leads while marking source as offline.
 */
export const fetchDashboardMetrics = async (): Promise<ApiResponse<DashboardMetrics>> => {
  // If backend base URL is configured, attempt real connection
  if (API_BASE_URL) {
    try {
      const response = await fetch(`${API_BASE_URL}/metrics`);
      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}`);
      }
      const data: DashboardMetrics = await response.json();
      return { data, loading: false, error: null, sourceConnected: true };
    } catch (err: any) {
      return {
        data: null,
        loading: false,
        error: `Could not reach admissions server at ${API_BASE_URL}: ${err.message}`,
        sourceConnected: false,
      };
    }
  }

  // Backend is not configured yet
  const localLeads = getLocalSessionLeads();
  if (localLeads.length > 0) {
    return {
      data: {
        totalLeads: localLeads.length,
        hotLeads: localLeads.filter(l => l.status === 'Hot').length,
        demosBooked: 0,
        followupsDue: 0,
      },
      loading: false,
      error: null,
      sourceConnected: false,
    };
  }

  return {
    data: {
      totalLeads: null,
      hotLeads: null,
      demosBooked: null,
      followupsDue: null,
    },
    loading: false,
    error: null,
    sourceConnected: false,
  };
};

/**
 * Fetches recent student enquiries.
 * Merges local session leads with any backend response.
 */
export const fetchRecentEnquiries = async (): Promise<ApiResponse<Lead[]>> => {
  const localLeads = getLocalSessionLeads();

  if (API_BASE_URL) {
    try {
      const res = await fetch(`${API_BASE_URL}/leads/recent`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const backendLeads: Lead[] = await res.json();
      return {
        data: [...localLeads, ...backendLeads],
        loading: false,
        error: null,
        sourceConnected: true,
      };
    } catch (err: any) {
      return {
        data: localLeads.length > 0 ? localLeads : null,
        loading: false,
        error: `Backend enquiry feed unavailable: ${err.message}`,
        sourceConnected: false,
      };
    }
  }

  return {
    data: localLeads.length > 0 ? localLeads : null,
    loading: false,
    error: null,
    sourceConnected: false,
  };
};

/**
 * Fetches scheduled follow-ups
 */
export const fetchFollowUps = async (): Promise<ApiResponse<FollowUp[]>> => {
  if (API_BASE_URL) {
    try {
      const res = await fetch(`${API_BASE_URL}/followups/upcoming`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: FollowUp[] = await res.json();
      return { data, loading: false, error: null, sourceConnected: true };
    } catch (err: any) {
      return {
        data: null,
        loading: false,
        error: `Follow-up service unavailable: ${err.message}`,
        sourceConnected: false,
      };
    }
  }

  return {
    data: null,
    loading: false,
    error: null,
    sourceConnected: false,
  };
};

/**
 * Fetches lead sources breakdown
 */
export const fetchLeadSources = async (): Promise<ApiResponse<LeadSourceMetric[]>> => {
  if (API_BASE_URL) {
    try {
      const res = await fetch(`${API_BASE_URL}/analytics/lead-sources`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: LeadSourceMetric[] = await res.json();
      return { data, loading: false, error: null, sourceConnected: true };
    } catch (err: any) {
      return {
        data: null,
        loading: false,
        error: `Analytics service unavailable: ${err.message}`,
        sourceConnected: false,
      };
    }
  }

  // If local leads exist, compute actual breakdown from local session records
  const localLeads = getLocalSessionLeads();
  if (localLeads.length > 0) {
    const counts: Record<string, number> = {};
    localLeads.forEach(l => {
      counts[l.source] = (counts[l.source] || 0) + 1;
    });
    const metrics: LeadSourceMetric[] = Object.entries(counts).map(([source, count]) => ({
      source: source as any,
      count,
      percentage: Math.round((count / localLeads.length) * 100),
    }));
    return { data: metrics, loading: false, error: null, sourceConnected: false };
  }

  return {
    data: null,
    loading: false,
    error: null,
    sourceConnected: false,
  };
};

/**
 * Fetches AI insights
 */
export const fetchAIInsights = async (): Promise<ApiResponse<AIInsight[]>> => {
  if (API_BASE_URL) {
    try {
      const res = await fetch(`${API_BASE_URL}/ai/insights`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: AIInsight[] = await res.json();
      return { data, loading: false, error: null, sourceConnected: true };
    } catch (err: any) {
      return {
        data: null,
        loading: false,
        error: `AI Insight service unavailable: ${err.message}`,
        sourceConnected: false,
      };
    }
  }

  return {
    data: null,
    loading: false,
    error: null,
    sourceConnected: false,
  };
};

/**
 * Fetches notifications
 */
export const fetchNotifications = async (): Promise<ApiResponse<NotificationItem[]>> => {
  if (API_BASE_URL) {
    try {
      const res = await fetch(`${API_BASE_URL}/notifications`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: NotificationItem[] = await res.json();
      return { data, loading: false, error: null, sourceConnected: true };
    } catch (err: any) {
      return {
        data: null,
        loading: false,
        error: `Notification service error: ${err.message}`,
        sourceConnected: false,
      };
    }
  }

  return {
    data: [],
    loading: false,
    error: null,
    sourceConnected: false,
  };
};
