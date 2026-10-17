export type LeadSource = 'WhatsApp' | 'Instagram' | 'Website' | 'Phone' | 'Walk-in';

export type LeadStatus = 'Hot' | 'Warm' | 'New' | 'Cold';

export type FollowUpPriority = 'High' | 'Medium' | 'Low';

export interface Lead {
  id: string;
  candidateNumber?: string; // e.g. #LD-1092
  studentName: string;
  email?: string;
  phone: string;
  courseInterest: string;
  source: LeadSource;
  status: LeadStatus;
  leadScore?: number; // e.g. 92
  intentScore?: number; // e.g. 94 out of 100
  lastContact: string; // e.g. 2h ago or Today at 02:15 PM
  notes?: string;
  avatarColor?: string;
  isLocalSession?: boolean;
}

export interface FollowUp {
  id: string;
  studentName: string;
  leadId: string;
  scheduledTime: string;
  courseInterest: string;
  priority: FollowUpPriority;
  status: 'Pending' | 'Completed' | 'Overdue';
  assignedDesk?: string;
  completed?: boolean;
  avatarColor?: string;
  counsellor?: string;
}

export interface DashboardMetrics {
  totalLeads: number | null;
  hotLeads: number | null;
  demosBooked: number | null;
  followupsDue: number | null;
  totalLeadsTrend?: string;
  hotLeadsTrend?: string;
  demosBookedTrend?: string;
  followupsDueTrend?: string;
}

export interface QuickStatsData {
  newLeadsToday: number | null;
  demosScheduled: number | null;
  admissions: number | null;
  conversionRate: string | null;
}

export interface LeadSourceMetric {
  source: LeadSource;
  count: number;
  percentage: number;
  conversionRate?: string;
  color?: string;
}

export interface AIInsight {
  id: string;
  category: string;
  title: string;
  summary: string;
  supportingContext: string;
  isRecommendation: boolean;
  relatedLeadId?: string;
  createdAt: string;
}

export interface IntelligenceBrief {
  id: string;
  category: string;
  categoryColor: 'amber' | 'green' | 'blue';
  title: string;
  summary: string;
  verificationRate: string;
  sourceNote: string;
  timestamp: string;
}

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  type: 'enquiry' | 'followup' | 'system';
}

export type NavigationRoute = 
  | 'overview'
  | 'all-leads'
  | 'conversations'
  | 'ai-insights'
  | 'demos-followups'
  | 'analytics'
  | 'knowledge-base'
  | 'settings';
