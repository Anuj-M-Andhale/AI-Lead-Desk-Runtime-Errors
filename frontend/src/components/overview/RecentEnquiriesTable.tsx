import React, { useState } from 'react';
import { Users, ChevronRight, Search, BookOpen } from 'lucide-react';
import type { Lead, LeadStatus } from '../../types/admissions';
import { StatusIndicator } from '../common/StatusIndicator';
import { LeadSourceBadge } from '../common/BrandIcons';

interface RecentEnquiriesTableProps {
  leads: Lead[];
  onSelectLead: (lead: Lead) => void;
  onViewAllLeads: () => void;
}

const getAvatarBg = (_name: string, index: number) => {
  const colors = [
    'bg-[#2563EB] text-white',
    'bg-[#12345A] text-white',
    'bg-[#EF4444] text-white',
    'bg-[#0284C7] text-white',
    'bg-[#7C3AED] text-white',
    'bg-[#0D9488] text-white',
  ];
  return colors[index % colors.length];
};

const getInitials = (name: string) => {
  if (!name) return 'ST';
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
};

export const RecentEnquiriesTable: React.FC<RecentEnquiriesTableProps> = ({
  leads,
  onSelectLead,
  onViewAllLeads,
}) => {
  const [activeFilter, setActiveFilter] = useState<'All' | LeadStatus>('All');
  const [nameFilter, setNameFilter] = useState<string>('');

  const filterOptions: ('All' | LeadStatus)[] = ['All', 'Hot', 'Warm', 'New', 'Cold'];

  // Filter leads based on selected status pill and search input
  const filteredLeads = leads.filter((lead) => {
    const matchesStatus = activeFilter === 'All' || lead.status === activeFilter;
    const matchesName =
      !nameFilter.trim() ||
      lead.studentName.toLowerCase().includes(nameFilter.toLowerCase()) ||
      lead.phone.includes(nameFilter) ||
      lead.courseInterest.toLowerCase().includes(nameFilter.toLowerCase());
    return matchesStatus && matchesName;
  });

  const getIntentBar = (status: LeadStatus, score: number) => {
    switch (status) {
      case 'Hot':
        return (
          <div className="w-14 h-2 bg-[#EF4444] rounded-full" title={`Intent: ${score}%`} />
        );
      case 'Warm':
        return (
          <div className="w-10 h-2 bg-[#F97316] rounded-full" title={`Intent: ${score}%`} />
        );
      case 'New':
        return (
          <div className="w-7 h-2 bg-[#3B82F6] rounded-full" title={`Intent: ${score}%`} />
        );
      case 'Cold':
        return (
          <div className="w-4 h-2 bg-[#94A3B8] rounded-full" title={`Intent: ${score}%`} />
        );
    }
  };

  return (
    <div className="bg-white border border-[#DCE5EF] rounded-2xl shadow-[0_2px_8px_rgba(18,52,90,0.04)] overflow-hidden flex flex-col">
      {/* Section Header */}
      <div className="px-6 py-4.5 border-b border-[#F1F5F9] flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <Users className="w-5 h-5 text-[#2563EB] stroke-[2]" />
          <h2 className="text-[17px] font-bold text-[#172B4D] tracking-tight">
            Recent Leads
          </h2>
        </div>

        <button
          type="button"
          onClick={onViewAllLeads}
          className="inline-flex items-center gap-1 text-[13px] font-semibold text-[#2563EB] hover:text-[#1D4ED8] transition-colors"
        >
          <span>View All</span>
          <ChevronRight className="w-4 h-4 stroke-[2.5]" />
        </button>
      </div>

      {/* Feature from Photos: Status Filter Pills & Quick Search Bar */}
      <div className="px-6 py-2.5 border-b border-[#F1F5F9] bg-[#F8FAFC] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-[11px] font-bold text-[#64748B] uppercase tracking-wider mr-1">
            FILTER:
          </span>
          {filterOptions.map((filter) => (
            <button
              key={filter}
              type="button"
              onClick={() => setActiveFilter(filter)}
              className={`px-3 py-1 rounded-lg text-[12px] font-semibold transition-all ${
                activeFilter === filter
                  ? 'bg-[#12345A] text-white shadow-xs'
                  : 'bg-transparent text-[#64748B] hover:bg-white hover:text-[#172B4D]'
              }`}
            >
              {filter}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-44">
          <Search className="w-3.5 h-3.5 text-[#94A3B8] absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            value={nameFilter}
            onChange={(e) => setNameFilter(e.target.value)}
            placeholder="Filter names..."
            className="w-full pl-8 pr-3 py-1 text-[12px] bg-white border border-[#DCE5EF] rounded-lg text-[#172B4D] placeholder-[#94A3B8] focus:border-[#2563EB] focus:outline-none"
          />
        </div>
      </div>

      {/* Table Content */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-[13.5px] border-collapse">
          <thead>
            <tr className="border-b border-[#F1F5F9] text-[11.5px] font-semibold text-[#64748B] bg-white uppercase tracking-wider">
              <th className="py-3 px-6">Student</th>
              <th className="py-3 px-4">Course Interest</th>
              <th className="py-3 px-4">Source</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4">Lead Score</th>
              <th className="py-3 px-4">Intent</th>
              <th className="py-3 px-4">Last Contact</th>
              <th className="py-3 px-5 text-right"><span className="sr-only">Actions</span></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#F1F5F9]">
            {filteredLeads.map((lead, idx) => (
              <tr
                key={lead.id}
                className="hover:bg-[#F8FAFC] transition-colors group cursor-pointer"
                onClick={() => onSelectLead(lead)}
              >
                {/* Student with initials avatar */}
                <td className="py-3.5 px-6">
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-[12px] shrink-0 shadow-xs ${
                        lead.avatarColor || getAvatarBg(lead.studentName, idx)
                      }`}
                    >
                      {getInitials(lead.studentName)}
                    </div>
                    <div>
                      <span className="font-semibold text-[#172B4D] block group-hover:text-[#2563EB] transition-colors">
                        {lead.studentName}
                      </span>
                      {lead.isLocalSession && (
                        <span className="text-[10px] font-semibold px-1.5 py-0.2 bg-[#EFF6FF] text-[#2563EB] rounded">
                          Local Session
                        </span>
                      )}
                    </div>
                  </div>
                </td>

                {/* Course Interest */}
                <td className="py-3.5 px-4 font-medium text-[#475569]">
                  <div className="flex items-center gap-1.5 max-w-[200px]">
                    <BookOpen className="w-3.5 h-3.5 text-[#94A3B8] shrink-0" />
                    <span className="truncate">{lead.courseInterest || '—'}</span>
                  </div>
                </td>

                {/* Source with Brand Icon */}
                <td className="py-3.5 px-4">
                  <LeadSourceBadge source={lead.source} />
                </td>

                {/* Status Pill Badge */}
                <td className="py-3.5 px-4">
                  <StatusIndicator status={lead.status} />
                </td>

                {/* Lead Score */}
                <td className="py-3.5 px-4 font-bold text-[#172B4D]">
                  {lead.leadScore ?? '—'}
                </td>

                {/* Intent Progress Bar Feature */}
                <td className="py-3.5 px-4">
                  {getIntentBar(lead.status, lead.intentScore || lead.leadScore || 50)}
                </td>

                {/* Last Contact */}
                <td className="py-3.5 px-4 text-[#64748B] font-medium text-[13px]">
                  {lead.lastContact || '—'}
                </td>

                {/* Row Chevron */}
                <td className="py-3.5 px-5 text-right">
                  <ChevronRight className="w-4 h-4 text-[#94A3B8] inline-block group-hover:text-[#2563EB] group-hover:translate-x-0.5 transition-all" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
