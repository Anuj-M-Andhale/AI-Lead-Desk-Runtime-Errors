import React, { useState } from 'react';
import { Sparkles, ChevronRight, FileText, Bot, Lock } from 'lucide-react';
import type { IntelligenceBrief } from '../../types/admissions';

interface AiInsightsPanelProps {
  onViewAll?: () => void;
}

const DEFAULT_BRIEFS: IntelligenceBrief[] = [
  {
    id: 'brief-1',
    category: 'Financial & Fees',
    categoryColor: 'amber',
    title: 'Frequent Installment Inquiries in Weekend MBA',
    verificationRate: '92% verified',
    summary:
      '42% of recent working professional inquiries asked for 3-part installment plans rather than upfront semester payments.',
    sourceNote: 'Derived from 18 WhatsApp dialogues in LD-...',
    timestamp: 'Today, 10:30 AM',
  },
  {
    id: 'brief-2',
    category: 'Conversion Opportunity',
    categoryColor: 'green',
    title: 'High Demo Conversion Rate on AI Bootcamp',
    verificationRate: '88% verified',
    summary:
      'Students attending the 45-minute live AI lab demo convert at 3.2x higher rate within 48 hours of attendance.',
    sourceNote: 'Tracked across 24 recent booked demo sess...',
    timestamp: 'Yesterday, 04:15 PM',
  },
  {
    id: 'brief-3',
    category: 'Curriculum Delivery',
    categoryColor: 'blue',
    title: 'High Demand for Sunday-Only Hybrid Sessions',
    verificationRate: '85% verified',
    summary:
      'Several tech applicants inquired if in-person labs could be consolidated into Sundays to avoid Saturday work conflicts.',
    sourceNote: 'Derived from 12 counseling interview logs',
    timestamp: '2 days ago',
  },
];

export const AiInsightsPanel: React.FC<AiInsightsPanelProps> = ({ onViewAll }) => {
  const [showBriefs, setShowBriefs] = useState<boolean>(true);

  const getBadgeStyle = (categoryColor: 'amber' | 'green' | 'blue') => {
    switch (categoryColor) {
      case 'amber':
        return 'bg-amber-50 text-amber-700 border border-amber-200';
      case 'green':
        return 'bg-emerald-50 text-emerald-700 border border-emerald-200';
      case 'blue':
        return 'bg-sky-50 text-sky-700 border border-sky-200';
    }
  };

  return (
    <div className="bg-white border border-[#DCE5EF] rounded-2xl p-5 shadow-[0_2px_8px_rgba(18,52,90,0.04)] flex flex-col justify-between h-full">
      {/* Header */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-[#2563EB] stroke-[2]" />
            <h3 className="text-[17px] font-bold text-[#172B4D] tracking-tight">
              AI Insights
            </h3>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setShowBriefs(!showBriefs)}
              className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-[#F1F5F9] text-[#475569] hover:bg-[#E2E8F0] transition-colors"
            >
              {showBriefs ? 'Show Standby' : 'Show Briefs'}
            </button>
            <button
              type="button"
              onClick={onViewAll}
              className="inline-flex items-center gap-1 text-[13px] font-semibold text-[#2563EB] hover:text-[#1D4ED8] transition-colors"
            >
              <span>View All</span>
              <ChevronRight className="w-4 h-4 stroke-[2.5]" />
            </button>
          </div>
        </div>

        {/* Content: Either Grounded Briefs (Photo 2) or Standby Box */}
        {showBriefs ? (
          <div className="space-y-3 my-2">
            {DEFAULT_BRIEFS.map((brief) => (
              <div
                key={brief.id}
                className="p-3 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl hover:border-[#CBD5E1] transition-all space-y-1.5"
              >
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-0.2 rounded text-[10.5px] font-bold ${getBadgeStyle(
                        brief.categoryColor
                      )}`}
                    >
                      {brief.category}
                    </span>
                    <h4 className="text-[13px] font-bold text-[#172B4D]">
                      {brief.title}
                    </h4>
                  </div>
                  <span className="text-[10.5px] font-semibold px-2 py-0.2 rounded-full bg-white text-[#64748B] border border-[#E2E8F0]">
                    {brief.verificationRate}
                  </span>
                </div>

                <p className="text-[12px] text-[#475569] leading-snug">
                  {brief.summary}
                </p>

                <div className="flex items-center justify-between text-[11px] text-[#94A3B8] pt-0.5">
                  <span className="flex items-center gap-1 truncate max-w-[70%]">
                    <FileText className="w-3 h-3 shrink-0" />
                    <span className="truncate">Source: {brief.sourceNote}</span>
                  </span>
                  <span>{brief.timestamp}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-[#F0F7FF] border border-[#DCE5EF] rounded-xl p-5 my-auto flex flex-col justify-between gap-4">
            <div className="flex items-start gap-3.5">
              <div className="w-10 h-10 rounded-xl bg-white text-[#2563EB] border border-[#BFDBFE] flex items-center justify-center shrink-0 shadow-xs">
                <Bot className="w-5 h-5 stroke-[2]" />
              </div>
              <p className="text-[13.5px] text-[#334155] leading-relaxed font-medium">
                AI insights will appear here when the AI service is connected and sufficient lead data is available.
              </p>
            </div>

            <div className="flex items-center justify-between pt-3 border-t border-[#E2E8F0] text-[12px]">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-white border border-[#CBD5E1] text-[#475569] font-medium text-[11px]">
                <Lock className="w-3 h-3 text-[#64748B]" />
                Demo mode
              </span>
              <span className="text-[#64748B] italic">
                Insights are not available yet.
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
