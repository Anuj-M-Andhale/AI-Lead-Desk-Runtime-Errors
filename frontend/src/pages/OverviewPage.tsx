import React, { useState } from 'react';
import { Plus, MessageSquare, Calendar } from 'lucide-react';
import { MetricsGrid } from '../components/overview/MetricsGrid';
import { RecentEnquiriesTable } from '../components/overview/RecentEnquiriesTable';
import { FollowUpsPanel } from '../components/overview/FollowUpsPanel';
import { LeadSourcesPanel } from '../components/overview/LeadSourcesPanel';
import { AiInsightsPanel } from '../components/overview/AiInsightsPanel';
import { QuickStatsPanel } from '../components/overview/QuickStatsPanel';
import { CandidateDetailModal } from '../components/overview/CandidateDetailModal';
import type {
  DashboardMetrics,
  Lead,
  FollowUp,
  NavigationRoute,
} from '../types/admissions';

interface OverviewPageProps {
  onNavigate: (route: NavigationRoute) => void;
  onOpenAddLead: () => void;
  searchFilter: string;
}

const INITIAL_METRICS: DashboardMetrics = {
  totalLeads: 248,
  hotLeads: 32,
  demosBooked: 14,
  followupsDue: 19,
  totalLeadsTrend: '↑ 12% from last week',
  hotLeadsTrend: '↑ 8% from last week',
  demosBookedTrend: '↑ 6% from last week',
  followupsDueTrend: '↘ 4% from last week',
};

const INITIAL_LEADS: Lead[] = [
  {
    id: 'lead-1',
    candidateNumber: '#LD-1092',
    studentName: 'Priya Sharma',
    email: 'priya.sharma@example.com',
    phone: '+91 98201 44521',
    courseInterest: 'Data Science',
    source: 'WhatsApp',
    status: 'Hot',
    leadScore: 92,
    intentScore: 94,
    lastContact: '2h ago',
    avatarColor: 'bg-[#2563EB] text-white',
    notes: 'Inquired about curriculum accreditations and scholarship eligibility.',
  },
  {
    id: 'lead-2',
    candidateNumber: '#LD-1093',
    studentName: 'Rahul Verma',
    email: 'rahul.verma@example.com',
    phone: '+91 97112 88390',
    courseInterest: 'AI/ML',
    source: 'Instagram',
    status: 'Warm',
    leadScore: 76,
    intentScore: 78,
    lastContact: '4h ago',
    avatarColor: 'bg-[#12345A] text-white',
    notes: 'Requested syllabus breakdown and faculty mentor credentials.',
  },
  {
    id: 'lead-3',
    candidateNumber: '#LD-1094',
    studentName: 'Sneha Patil',
    email: 'sneha.patil@example.com',
    phone: '+91 98334 11829',
    courseInterest: 'Python',
    source: 'Website',
    status: 'New',
    leadScore: 68,
    intentScore: 65,
    lastContact: '6h ago',
    avatarColor: 'bg-[#EF4444] text-white',
    notes: 'Working professional inquiring about weekend batch availability.',
  },
  {
    id: 'lead-4',
    candidateNumber: '#LD-1095',
    studentName: 'Aman Khan',
    email: 'aman.khan@example.com',
    phone: '+91 99200 77123',
    courseInterest: 'Web Development',
    source: 'Phone',
    status: 'Warm',
    leadScore: 71,
    intentScore: 70,
    lastContact: '8h ago',
    avatarColor: 'bg-[#0284C7] text-white',
    notes: 'Evaluating placement assistance and corporate hiring partners.',
  },
  {
    id: 'lead-5',
    candidateNumber: '#LD-1096',
    studentName: 'Neha Joshi',
    email: 'neha.joshi@example.com',
    phone: '+91 98450 33219',
    courseInterest: 'Data Science',
    source: 'Walk-in',
    status: 'Cold',
    leadScore: 54,
    intentScore: 40,
    lastContact: '12h ago',
    avatarColor: 'bg-[#7C3AED] text-white',
    notes: 'Visited campus desk; requested lab demonstration schedule.',
  },
];

const INITIAL_FOLLOWUPS: FollowUp[] = [
  {
    id: 'fu-1',
    studentName: 'Rohit Sharma',
    leadId: 'lead-1',
    courseInterest: 'AI/ML',
    scheduledTime: '10:30 AM',
    priority: 'High',
    status: 'Pending',
    avatarColor: 'bg-[#12345A] text-white',
  },
  {
    id: 'fu-2',
    studentName: 'Pooja Verma',
    leadId: 'lead-2',
    courseInterest: 'Data Science',
    scheduledTime: '12:00 PM',
    priority: 'Medium',
    status: 'Pending',
    avatarColor: 'bg-[#2563EB] text-white',
  },
  {
    id: 'fu-3',
    studentName: 'Sahil Khan',
    leadId: 'lead-3',
    courseInterest: 'Python',
    scheduledTime: '03:00 PM',
    priority: 'Low',
    status: 'Pending',
    avatarColor: 'bg-[#475569] text-white',
  },
  {
    id: 'fu-4',
    studentName: 'Anjali Singh',
    leadId: 'lead-4',
    courseInterest: 'Web Dev',
    scheduledTime: '05:00 PM',
    priority: 'Medium',
    status: 'Pending',
    avatarColor: 'bg-[#0B1F3A] text-white',
  },
];

export const OverviewPage: React.FC<OverviewPageProps> = ({
  onNavigate,
  onOpenAddLead,
  searchFilter,
}) => {
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleOpenLeadRecord = (leadId: string) => {
    const found = INITIAL_LEADS.find((l) => l.id === leadId);
    if (found) {
      setSelectedLead(found);
      setIsModalOpen(true);
    }
  };

  const handleSelectLead = (lead: Lead) => {
    setSelectedLead(lead);
    setIsModalOpen(true);
  };

  // Filter leads based on top header search
  const visibleLeads = INITIAL_LEADS.filter((lead) => {
    if (!searchFilter.trim()) return true;
    const q = searchFilter.toLowerCase();
    return (
      lead.studentName.toLowerCase().includes(q) ||
      lead.courseInterest.toLowerCase().includes(q) ||
      lead.source.toLowerCase().includes(q) ||
      lead.status.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      {/* 1. DASHBOARD HEADER with Original Title and 3 Action Buttons */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-[26px] sm:text-[28px] font-extrabold text-[#172B4D] tracking-tight leading-tight">
            Overview
          </h1>
          <p className="text-[14px] text-[#64748B] font-medium mt-0.5">
            Welcome back! Here's your admissions overview.
          </p>
        </div>

        {/* 3 Action Buttons */}
        <div className="flex items-center gap-2.5 sm:gap-3 flex-wrap">
          {/* Primary Navy Blue Add Lead */}
          <button
            type="button"
            onClick={onOpenAddLead}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-[#12345A] hover:bg-[#1A4574] text-white text-[13.5px] font-semibold rounded-xl shadow-sm transition-all"
          >
            <Plus className="w-4 h-4 stroke-[2.5]" />
            <span>+ Add Lead</span>
          </button>

          {/* Start Conversation */}
          <button
            type="button"
            onClick={() => onNavigate('conversations')}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-white hover:bg-[#F8FAFC] text-[#172B4D] border border-[#DCE5EF] text-[13.5px] font-semibold rounded-xl shadow-xs transition-all"
          >
            <MessageSquare className="w-4 h-4 text-[#2563EB] stroke-[2]" />
            <span>Start Conversation</span>
          </button>

          {/* Book Demo */}
          <button
            type="button"
            onClick={() => onNavigate('demos-followups')}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-white hover:bg-[#F8FAFC] text-[#172B4D] border border-[#DCE5EF] text-[13.5px] font-semibold rounded-xl shadow-xs transition-all"
          >
            <Calendar className="w-4 h-4 text-[#2563EB] stroke-[2]" />
            <span>Book Demo</span>
          </button>
        </div>
      </div>

      {/* 2. SUMMARY STATISTICS CARDS (Original 4 across: 248, 32, 14, 19) */}
      <section aria-label="Admissions Statistics">
        <MetricsGrid metrics={INITIAL_METRICS} />
      </section>

      {/* 3. MIDDLE ROW: Recent Leads & Follow-ups Today with Photo Features */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        {/* Left Column: Recent Leads (8 cols) */}
        <div className="lg:col-span-8 flex flex-col">
          <RecentEnquiriesTable
            leads={visibleLeads}
            onSelectLead={handleSelectLead}
            onViewAllLeads={() => onNavigate('all-leads')}
          />
        </div>

        {/* Right Column: Follow-ups Today (4 cols) */}
        <div className="lg:col-span-4 flex flex-col">
          <FollowUpsPanel
            followUps={INITIAL_FOLLOWUPS}
            onViewAllFollowUps={() => onNavigate('demos-followups')}
            onOpenLeadRecord={handleOpenLeadRecord}
          />
        </div>
      </div>

      {/* 4. BOTTOM ROW: Lead Sources, AI Insights, Quick Stats (3 cards) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-stretch">
        <div className="flex flex-col">
          <LeadSourcesPanel totalLeadsCount={INITIAL_METRICS.totalLeads ?? 248} />
        </div>

        <div className="flex flex-col">
          <AiInsightsPanel onViewAll={() => onNavigate('ai-insights')} />
        </div>

        <div className="flex flex-col">
          <QuickStatsPanel
            data={{
              newLeadsToday: null,
              demosScheduled: null,
              admissions: null,
              conversionRate: null,
            }}
            onNavigate={() => onNavigate('analytics')}
          />
        </div>
      </div>

      {/* 5. CANDIDATE RECORD MODAL DIALOG (From Photo 4) */}
      <CandidateDetailModal
        lead={selectedLead}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onOpenWhatsApp={(phone) => {
          window.open(`https://wa.me/${phone.replace(/[^0-9]/g, '')}`, '_blank');
        }}
        onScheduleDemo={(lead) => {
          alert(`Demo booking dialogue opened for ${lead.studentName}.`);
        }}
      />
    </div>
  );
};
