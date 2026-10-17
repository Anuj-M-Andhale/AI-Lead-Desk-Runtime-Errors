import React, { useState } from 'react';
import { BarChart2 } from 'lucide-react';
import type { LeadSourceMetric } from '../../types/admissions';

interface LeadSourcesPanelProps {
  sources?: LeadSourceMetric[];
  totalLeadsCount?: number;
}

const DEFAULT_SOURCES: LeadSourceMetric[] = [
  { source: 'WhatsApp', count: 94, percentage: 38, conversionRate: '28% conv', color: '#10B981' },
  { source: 'Instagram', count: 55, percentage: 22, conversionRate: '19% conv', color: '#C026D3' },
  { source: 'Website', count: 45, percentage: 18, conversionRate: '34% conv', color: '#3B82F6' },
  { source: 'Phone', count: 30, percentage: 12, conversionRate: '22% conv', color: '#F97316' },
  { source: 'Walk-in', count: 24, percentage: 10, conversionRate: '41% conv', color: '#94A3B8' },
];

export const LeadSourcesPanel: React.FC<LeadSourcesPanelProps> = ({
  sources = DEFAULT_SOURCES,
  totalLeadsCount = 248,
}) => {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  // Donut SVG geometry
  const radius = 56;
  const strokeWidth = 24;
  const circumference = 2 * Math.PI * radius; // ~351.858

  let cumulativeOffset = 0;
  const segments = sources.map((item, index) => {
    const strokeDash = (item.percentage / 100) * circumference;
    const offset = cumulativeOffset;
    cumulativeOffset += strokeDash;
    return {
      ...item,
      strokeDash,
      offset,
      index,
    };
  });

  return (
    <div className="bg-white border border-[#DCE5EF] rounded-2xl p-5 shadow-[0_2px_8px_rgba(18,52,90,0.04)] flex flex-col justify-between h-full">
      {/* Header */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <BarChart2 className="w-5 h-5 text-[#2563EB] stroke-[2]" />
            <h3 className="text-[17px] font-bold text-[#172B4D] tracking-tight">
              Lead Sources
            </h3>
          </div>
          <span className="text-[11.5px] font-bold px-2.5 py-0.5 rounded-full bg-[#EFF6FF] text-[#2563EB]">
            {totalLeadsCount} Leads
          </span>
        </div>

        {/* Donut Chart & Legend */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-6 my-2 py-1">
          {/* Donut Chart */}
          <div className="relative w-40 h-40 shrink-0 flex items-center justify-center">
            <svg
              className="w-full h-full -rotate-90 transform"
              viewBox="0 0 160 160"
            >
              {/* Background ring */}
              <circle
                cx="80"
                cy="80"
                r={radius}
                fill="transparent"
                stroke="#F1F5F9"
                strokeWidth={strokeWidth}
              />
              {/* Colored Segments */}
              {segments.map((seg) => (
                <circle
                  key={seg.source}
                  cx="80"
                  cy="80"
                  r={radius}
                  fill="transparent"
                  stroke={seg.color}
                  strokeWidth={hoveredIdx === seg.index ? strokeWidth + 3 : strokeWidth}
                  strokeDasharray={`${seg.strokeDash - 2} ${circumference}`}
                  strokeDashoffset={-seg.offset}
                  strokeLinecap="round"
                  className="transition-all duration-300 cursor-pointer"
                  onMouseEnter={() => setHoveredIdx(seg.index)}
                  onMouseLeave={() => setHoveredIdx(null)}
                />
              ))}
            </svg>

            {/* Donut Center Label */}
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-[22px] font-extrabold text-[#172B4D] leading-none">
                {totalLeadsCount}
              </span>
              <span className="text-[11px] font-bold text-[#64748B] mt-0.5">
                Total Leads
              </span>
            </div>
          </div>

          {/* Legend */}
          <div className="flex-1 w-full space-y-2">
            {sources.map((item, idx) => (
              <div
                key={item.source}
                onMouseEnter={() => setHoveredIdx(idx)}
                onMouseLeave={() => setHoveredIdx(null)}
                className={`flex items-center justify-between text-[13px] px-2 py-1 rounded-lg transition-colors cursor-pointer ${
                  hoveredIdx === idx ? 'bg-[#F8FAFC]' : ''
                }`}
              >
                <div className="flex items-center gap-2">
                  <span
                    className="w-2.5 h-2.5 rounded-full shrink-0"
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="font-semibold text-[#172B4D]">
                    {item.source}
                  </span>
                  {item.conversionRate && (
                    <span className="text-[11px] text-[#64748B] font-medium hidden xl:inline">
                      ({item.conversionRate})
                    </span>
                  )}
                </div>
                <span className="font-bold text-[#64748B]">
                  {item.percentage}%
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Feature from Photo 2: Highest converting channel footer banner */}
      <div className="pt-3 border-t border-[#F1F5F9] flex items-center justify-between text-[12px] mt-2">
        <span className="font-semibold text-[#64748B]">Top Channel:</span>
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full bg-[#ECFDF5] border border-[#A7F3D0] text-[#059669] font-bold text-[11px]">
          Walk-in Campus Desk (41% Yield)
        </span>
      </div>
    </div>
  );
};
