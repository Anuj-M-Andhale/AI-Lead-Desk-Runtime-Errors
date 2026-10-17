import React from 'react';
import { BarChart2, UserPlus, Calendar, Landmark, Compass, ChevronRight } from 'lucide-react';
import type { QuickStatsData } from '../../types/admissions';

interface QuickStatsPanelProps {
  data?: QuickStatsData | null;
  onNavigate?: () => void;
}

export const QuickStatsPanel: React.FC<QuickStatsPanelProps> = ({
  data,
  onNavigate,
}) => {
  const items = [
    {
      label: 'New Leads Today',
      value: data?.newLeadsToday !== null && data?.newLeadsToday !== undefined ? data.newLeadsToday : '—',
      icon: UserPlus,
    },
    {
      label: 'Demos Scheduled',
      value: data?.demosScheduled !== null && data?.demosScheduled !== undefined ? data.demosScheduled : '—',
      icon: Calendar,
    },
    {
      label: 'Admissions',
      value: data?.admissions !== null && data?.admissions !== undefined ? data.admissions : '—',
      icon: Landmark,
    },
    {
      label: 'Conversion Rate',
      value: data?.conversionRate || '—',
      icon: Compass,
    },
  ];

  return (
    <div className="bg-white border border-[#DCE5EF] rounded-2xl p-5 shadow-[0_2px_8px_rgba(18,52,90,0.04)] flex flex-col justify-between h-full">
      {/* Header */}
      <div className="flex items-center gap-2 mb-3">
        <BarChart2 className="w-5 h-5 text-[#2563EB] stroke-[2]" />
        <h3 className="text-[17px] font-bold text-[#172B4D] tracking-tight">
          Quick Stats
        </h3>
      </div>

      {/* Rows */}
      <div className="divide-y divide-[#F1F5F9] my-auto">
        {items.map((item, idx) => {
          const Icon = item.icon;
          return (
            <div
              key={idx}
              onClick={onNavigate}
              className="py-3 first:pt-1 last:pb-1 flex items-center justify-between hover:bg-[#F8FAFC] px-2 -mx-2 rounded-lg transition-colors cursor-pointer group"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-[#CCFBF1] text-[#0D9488] flex items-center justify-center shrink-0">
                  <Icon className="w-4 h-4 stroke-[2]" />
                </div>
                <span className="text-[13.5px] font-semibold text-[#172B4D] group-hover:text-[#2563EB] transition-colors">
                  {item.label}
                </span>
              </div>

              <div className="flex items-center gap-3">
                <span className="text-[14px] font-bold text-[#172B4D]">
                  {item.value}
                </span>
                <ChevronRight className="w-4 h-4 text-[#94A3B8] group-hover:text-[#2563EB] group-hover:translate-x-0.5 transition-all" />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
