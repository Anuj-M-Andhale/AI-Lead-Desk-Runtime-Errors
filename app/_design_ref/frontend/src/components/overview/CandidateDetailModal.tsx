import React from 'react';
import { X, ExternalLink, BookOpen, MessageCircle, Calendar } from 'lucide-react';
import type { Lead } from '../../types/admissions';
import { WhatsAppIcon } from '../common/BrandIcons';

interface CandidateDetailModalProps {
  lead: Lead | null;
  isOpen: boolean;
  onClose: () => void;
  onOpenWhatsApp?: (phone: string) => void;
  onScheduleDemo?: (lead: Lead) => void;
}

export const CandidateDetailModal: React.FC<CandidateDetailModalProps> = ({
  lead,
  isOpen,
  onClose,
  onOpenWhatsApp,
  onScheduleDemo,
}) => {
  if (!isOpen || !lead) return null;

  const initials = lead.studentName
    .split(' ')
    .map((n) => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-[2px] animate-in fade-in duration-150"
      role="dialog"
      aria-modal="true"
    >
      <div className="bg-white border border-[#E2E8F0] rounded-2xl shadow-2xl w-full max-w-xl overflow-hidden animate-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="px-6 py-5 border-b border-[#F1F5F9] flex items-start justify-between">
          <div className="flex items-center gap-3.5">
            <div className="w-11 h-11 rounded-xl bg-[#0F291E] text-emerald-400 font-bold text-[14px] flex items-center justify-center shrink-0 shadow-xs border border-emerald-900/30">
              {initials}
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h3 className="text-[18px] font-bold text-[#111827] tracking-tight">
                  {lead.studentName}
                </h3>
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11.5px] font-bold bg-[#FEE2E2] text-[#DC2626]">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#DC2626]" />
                  {lead.status.toUpperCase()}
                </span>
              </div>
              <p className="text-[12.5px] text-[#64748B] font-medium mt-0.5">
                Candidate Record {lead.candidateNumber || '#LD-1092'}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-[#94A3B8] hover:text-[#111827] hover:bg-[#F1F5F9] rounded-lg transition-colors"
            aria-label="Close modal"
          >
            <X className="w-5 h-5 stroke-[2]" />
          </button>
        </div>

        {/* Body Content */}
        <div className="p-6 space-y-5">
          {/* Program & Intent Score Row */}
          <div className="grid grid-cols-2 gap-4 pb-4 border-b border-[#F1F5F9]">
            <div>
              <span className="text-[12.5px] font-medium text-[#64748B] block">
                Program Applied
              </span>
              <div className="flex items-center gap-2 mt-1">
                <BookOpen className="w-4 h-4 text-[#475569] shrink-0" />
                <span className="text-[14px] font-semibold text-[#111827] truncate">
                  {lead.courseInterest}
                </span>
              </div>
            </div>

            <div>
              <span className="text-[12.5px] font-medium text-[#64748B] block">
                Intent Score
              </span>
              <span className="text-[15px] font-bold text-[#111827] mt-1 block">
                {lead.intentScore} / 100
              </span>
            </div>
          </div>

          {/* Contact Details Grid */}
          <div className="space-y-2.5 text-[13.5px]">
            <div className="flex items-center justify-between py-1">
              <span className="text-[#64748B] font-medium">Email Address:</span>
              <span className="font-semibold text-[#111827]">
                {lead.email || `${lead.studentName.toLowerCase().replace(/\s+/g, '.')}@example.com`}
              </span>
            </div>

            <div className="flex items-center justify-between py-1">
              <span className="text-[#64748B] font-medium">Contact Number:</span>
              <span className="font-semibold text-[#111827]">{lead.phone}</span>
            </div>

            <div className="flex items-center justify-between py-1">
              <span className="text-[#64748B] font-medium">Acquisition Channel:</span>
              <span className="inline-flex items-center gap-1.5 font-semibold text-[#111827]">
                {lead.source === 'WhatsApp' ? (
                  <WhatsAppIcon className="w-4 h-4" />
                ) : (
                  <MessageCircle className="w-4 h-4 text-[#2563EB]" />
                )}
                {lead.source}
              </span>
            </div>

            <div className="flex items-center justify-between py-1">
              <span className="text-[#64748B] font-medium">Last Touchpoint:</span>
              <span className="font-semibold text-[#111827]">{lead.lastContact}</span>
            </div>
          </div>

          {/* Counselor & Dialogue Notes Callout */}
          <div className="p-4 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl space-y-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#475569] block">
              COUNSELOR & DIALOGUE NOTES
            </span>
            <p className="text-[13.5px] text-[#1E293B] leading-relaxed">
              {lead.notes || 'Inquired about curriculum accreditations and scholarship eligibility.'}
            </p>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 bg-[#F9FAFB] border-t border-[#F1F5F9] flex items-center justify-between gap-3">
          {/* Left quick actions */}
          <div className="flex items-center gap-2.5">
            <button
              type="button"
              onClick={() => onOpenWhatsApp?.(lead.phone)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[13px] font-semibold text-[#059669] bg-[#ECFDF5] border border-[#A7F3D0] hover:bg-[#D1FAE5] rounded-lg transition-colors"
            >
              <WhatsAppIcon className="w-3.5 h-3.5" />
              <span>WhatsApp</span>
            </button>

            <button
              type="button"
              onClick={() => onScheduleDemo?.(lead)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[13px] font-semibold text-[#2563EB] bg-[#EFF6FF] border border-[#BFDBFE] hover:bg-[#DBEAFE] rounded-lg transition-colors"
            >
              <Calendar className="w-3.5 h-3.5 stroke-[2]" />
              <span>Schedule Demo</span>
            </button>
          </div>

          {/* Right dismiss / view full */}
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-1.5 text-[13px] font-semibold text-[#64748B] hover:text-[#111827] transition-colors"
            >
              Close
            </button>
            <button
              type="button"
              onClick={onClose}
              className="inline-flex items-center gap-1.5 px-4 py-2 text-[13px] font-semibold text-white bg-[#111827] hover:bg-[#1F2937] rounded-lg shadow-sm transition-colors"
            >
              <span>Open Full Record</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
