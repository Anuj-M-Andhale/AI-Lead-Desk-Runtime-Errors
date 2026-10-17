import React from 'react';
import { ArrowLeft, Clock, Layers } from 'lucide-react';
import type { NavigationRoute } from '../types/admissions';

interface PlaceholderPageProps {
  route: NavigationRoute;
  onBackToOverview: () => void;
}

const ROUTE_INFO: Record<
  NavigationRoute,
  { title: string; subtitle: string; description: string; phase: string }
> = {
  'overview': {
    title: 'Overview',
    subtitle: 'Admissions workspace',
    description: 'Admissions activity and next steps.',
    phase: 'Core Workspace',
  },
  'all-leads': {
    title: 'All Leads Directory',
    subtitle: 'Master candidate registry',
    description:
      'Comprehensive candidate management with multi-stage filtering, bulk counsellor assignment, and historical academic documentation. This module connects to the institutional admissions database in Phase 2.',
    phase: 'Phase 2 Architecture',
  },
  'conversations': {
    title: 'Conversations & Omni-Channel Messaging',
    subtitle: 'Integrated dialogue logs',
    description:
      'Unified inbox connecting WhatsApp Official Business API, website chat widgets, and telephony transcripts with counsellor audit trails. Awaiting API credentials setup.',
    phase: 'Phase 2 Architecture',
  },
  'ai-insights': {
    title: 'AI Insights & Enrolment Intelligence',
    subtitle: 'Predictive admissions analytics',
    description:
      'Detailed analytical breakdown of student decision drivers, fee sensitivity signals, and automated counsellor follow-up prioritization models. Requires historical conversation datasets.',
    phase: 'Phase 2 Architecture',
  },
  'demos-followups': {
    title: 'Demo Classes & Follow-ups Schedule',
    subtitle: 'Academic trial coordination',
    description:
      'Faculty demo class scheduling, student attendance confirmations, and calendar sync for admissions counsellors. Integrates with the college scheduling software.',
    phase: 'Phase 2 Architecture',
  },
  'analytics': {
    title: 'Admissions Analytics & Funnel Reports',
    subtitle: 'Institutional performance metrics',
    description:
      'Conversion rates from initial touchpoint to fee deposit, counsellor performance benchmarking, and seasonal admissions cohort forecasting.',
    phase: 'Phase 2 Architecture',
  },
  'knowledge-base': {
    title: 'Institute Knowledge Base',
    subtitle: 'Accreditation, curricula, and fee schedules',
    description:
      'Centralized repository of verified institute program guidelines, fee structures, hostel policies, and scholarship criteria used by counsellors and AI agents.',
    phase: 'Phase 2 Architecture',
  },
  'settings': {
    title: 'Settings & Integrations',
    subtitle: 'CRM connections and permissions',
    description:
      'Configuration management for ERP endpoints, WhatsApp Business API tokens, role-based access control, and counsellor shifts.',
    phase: 'Phase 2 Architecture',
  },
};

export const PlaceholderPage: React.FC<PlaceholderPageProps> = ({
  route,
  onBackToOverview,
}) => {
  const info = ROUTE_INFO[route] || ROUTE_INFO['all-leads'];

  return (
    <div className="space-y-6">
      {/* Back button and breadcrumb */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onBackToOverview}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 text-[13px] font-semibold text-[#12345A] bg-white border border-[#DCE5EF] hover:bg-[#F8FAFC] rounded-xl shadow-xs transition-colors"
        >
          <ArrowLeft className="w-4 h-4 stroke-[2]" />
          <span>Return to Overview</span>
        </button>
        <span className="text-[13px] text-[#94A3B8]">/</span>
        <span className="text-[13px] text-[#64748B] font-semibold">{info.title}</span>
      </div>

      {/* Main Container */}
      <div className="bg-white border border-[#DCE5EF] rounded-2xl shadow-[0_2px_8px_rgba(18,52,90,0.04)] p-8 sm:p-12 text-center max-w-2xl mx-auto">
        <div className="w-14 h-14 rounded-2xl bg-[#EFF6FF] text-[#2563EB] flex items-center justify-center mx-auto mb-4 border border-[#BFDBFE]">
          <Layers className="w-7 h-7 stroke-[2]" />
        </div>

        <span className="inline-block px-3 py-1 text-[11px] font-bold uppercase tracking-wider text-[#2563EB] bg-[#EFF6FF] rounded-full mb-3 border border-[#BFDBFE]">
          {info.phase}
        </span>

        <h2 className="text-[22px] font-extrabold text-[#172B4D] tracking-tight">
          {info.title}
        </h2>
        <p className="text-[14px] text-[#64748B] mt-1 font-semibold">
          {info.subtitle}
        </p>

        <p className="text-[13.5px] text-[#475569] mt-4 leading-relaxed max-w-lg mx-auto font-medium">
          {info.description}
        </p>

        <div className="mt-8 pt-6 border-t border-[#F1F5F9] flex flex-col sm:flex-row items-center justify-between gap-4 text-[12px] text-[#64748B]">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-[#94A3B8]" />
            <span>Planned for Phase 2 backend integration</span>
          </div>
          <button
            type="button"
            onClick={onBackToOverview}
            className="text-[13px] font-bold text-[#2563EB] hover:underline"
          >
            Go back to working Overview →
          </button>
        </div>
      </div>
    </div>
  );
};
