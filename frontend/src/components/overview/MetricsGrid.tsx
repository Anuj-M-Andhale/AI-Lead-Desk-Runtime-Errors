import React from 'react';
import { Users, Flame, CalendarCheck, Clock, ChevronRight, TrendingUp, TrendingDown } from 'lucide-react';
import type { DashboardMetrics } from '../../types/admissions';

interface MetricsGridProps {
  metrics: DashboardMetrics;
}

export const MetricsGrid: React.FC<MetricsGridProps> = ({ metrics }) => {
  const cards = [
    {
      id: 'total-leads',
      label: 'Total Leads',
      value: metrics.totalLeads,
      trend: metrics.totalLeadsTrend,
      trendType: 'up' as const,
      icon: Users,
      iconBg: 'bg-[#EFF6FF]',
      iconColor: 'text-[#2563EB]',
    },
    {
      id: 'hot-leads',
      label: 'Hot Leads',
      value: metrics.hotLeads,
      trend: metrics.hotLeadsTrend,
      trendType: 'up' as const,
      icon: Flame,
      iconBg: 'bg-[#FFF7ED]',
      iconColor: 'text-[#EA580C]',
    },
    {
      id: 'demos-booked',
      label: 'Demos Booked',
      value: metrics.demosBooked,
      trend: metrics.demosBookedTrend,
      trendType: 'up' as const,
      icon: CalendarCheck,
      iconBg: 'bg-[#CCFBF1]',
      iconColor: 'text-[#0D9488]',
    },
    {
      id: 'followups-due',
      label: 'Follow-ups Due',
      value: metrics.followupsDue,
      trend: metrics.followupsDueTrend,
      trendType: 'down' as const,
      icon: Clock,
      iconBg: 'bg-[#FFE4E6]',
      iconColor: 'text-[#EF4444]',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
      {cards.map((card) => {
        const Icon = card.icon;

        return (
          <div
            key={card.id}
            className="bg-white border border-[#DCE5EF] rounded-2xl p-5 shadow-[0_2px_8px_rgba(18,52,90,0.04)] hover-card-lift flex flex-col justify-between cursor-pointer group"
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3.5">
                <div
                  className={`w-12 h-12 rounded-full ${card.iconBg} ${card.iconColor} flex items-center justify-center shrink-0 transition-transform group-hover:scale-105`}
                >
                  <Icon className="w-6 h-6 stroke-[2]" />
                </div>
                <div>
                  <span className="text-[13.5px] font-semibold text-[#64748B]">
                    {card.label}
                  </span>
                  <div className="text-[26px] sm:text-[28px] font-bold text-[#172B4D] tracking-tight leading-none mt-1">
                    {card.value !== null && card.value !== undefined ? card.value.toLocaleString() : '—'}
                  </div>
                </div>
              </div>

              <ChevronRight className="w-4 h-4 text-[#94A3B8] group-hover:text-[#2563EB] group-hover:translate-x-0.5 transition-all mt-1" />
            </div>

            <div className="mt-4 pt-3 border-t border-[#F1F5F9] flex items-center gap-1.5 text-[12px]">
              {card.trendType === 'up' ? (
                <span className="inline-flex items-center text-[#16A34A] font-semibold gap-0.5">
                  <TrendingUp className="w-3.5 h-3.5 stroke-[2.5]" />
                  {card.trend ? card.trend.split(' ')[1] : ''}
                </span>
              ) : (
                <span className="inline-flex items-center text-[#16A34A] font-semibold gap-0.5">
                  <TrendingDown className="w-3.5 h-3.5 stroke-[2.5]" />
                  {card.trend ? card.trend.split(' ')[1] : ''}
                </span>
              )}
              <span className="text-[#94A3B8]">
                {card.trend && card.trend.includes('from last week') ? 'from last week' : ''}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
};
