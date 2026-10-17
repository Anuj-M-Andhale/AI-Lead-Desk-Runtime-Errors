import React, { useState } from 'react';
import { Calendar, ChevronRight, Check, ExternalLink } from 'lucide-react';
import type { FollowUp } from '../../types/admissions';

interface FollowUpsPanelProps {
  followUps: FollowUp[];
  onViewAllFollowUps: () => void;
  onOpenLeadRecord: (leadId: string) => void;
}

const getAvatarBg = (_name: string, index: number) => {
  const colors = [
    'bg-[#12345A] text-white',
    'bg-[#2563EB] text-white',
    'bg-[#475569] text-white',
    'bg-[#0B1F3A] text-white',
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

export const FollowUpsPanel: React.FC<FollowUpsPanelProps> = ({
  followUps,
  onViewAllFollowUps,
  onOpenLeadRecord,
}) => {
  const [tasks, setTasks] = useState<FollowUp[]>(followUps);

  const toggleComplete = (id: string) => {
    setTasks((prev) =>
      prev.map((t) => (t.id === id ? { ...t, completed: !t.completed } : t))
    );
  };

  return (
    <div className="bg-white border border-[#DCE5EF] rounded-2xl shadow-[0_2px_8px_rgba(18,52,90,0.04)] overflow-hidden flex flex-col h-full">
      {/* Header */}
      <div className="px-5 py-4.5 border-b border-[#F1F5F9] flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <Calendar className="w-5 h-5 text-[#2563EB] stroke-[2]" />
          <h3 className="text-[17px] font-bold text-[#172B4D] tracking-tight">
            Follow-ups Today
          </h3>
        </div>

        <button
          type="button"
          onClick={onViewAllFollowUps}
          className="inline-flex items-center gap-1 text-[13px] font-semibold text-[#2563EB] hover:text-[#1D4ED8] transition-colors"
        >
          <span>View All</span>
          <ChevronRight className="w-4 h-4 stroke-[2.5]" />
        </button>
      </div>

      {/* List Content */}
      <div className="p-4 sm:p-5 flex-1 flex flex-col justify-start divide-y divide-[#F1F5F9]">
        {tasks.map((item, idx) => {
          const priorityClass = {
            High: 'bg-[#FEE2E2] text-[#EF4444]',
            Medium: 'bg-[#FFEDD5] text-[#EA580C]',
            Low: 'bg-[#CCFBF1] text-[#0D9488]',
          }[item.priority] || 'bg-[#F1F5F9] text-[#64748B]';

          return (
            <div
              key={item.id}
              className={`py-3.5 first:pt-1 last:pb-1 flex items-center justify-between gap-3 rounded-lg px-2 -mx-2 transition-colors group ${
                item.completed ? 'opacity-60 bg-[#F8FAFC]' : 'hover:bg-[#F8FAFC]'
              }`}
            >
              {/* Left: Task checkbox + Avatar + Name & Course */}
              <div className="flex items-center gap-2.5 sm:gap-3 min-w-0">
                {/* Feature: Checkbox */}
                <button
                  type="button"
                  onClick={() => toggleComplete(item.id)}
                  className={`w-4 h-4 rounded flex items-center justify-center border transition-colors shrink-0 ${
                    item.completed
                      ? 'bg-[#12345A] border-[#12345A] text-white'
                      : 'border-[#CBD5E1] hover:border-[#12345A] bg-white'
                  }`}
                  aria-label="Mark task done"
                >
                  {item.completed && <Check className="w-3 h-3 stroke-[3]" />}
                </button>

                <div
                  className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-[12px] shrink-0 shadow-xs cursor-pointer ${
                    item.avatarColor || getAvatarBg(item.studentName, idx)
                  }`}
                  onClick={() => onOpenLeadRecord(item.leadId)}
                >
                  {getInitials(item.studentName)}
                </div>

                <div
                  className="min-w-0 cursor-pointer"
                  onClick={() => onOpenLeadRecord(item.leadId)}
                >
                  <span
                    className={`text-[13.5px] font-bold text-[#172B4D] truncate block group-hover:text-[#2563EB] transition-colors ${
                      item.completed ? 'line-through text-[#64748B]' : ''
                    }`}
                  >
                    {item.studentName}
                  </span>
                  <span className="text-[12px] text-[#64748B] font-medium block truncate">
                    {item.courseInterest}
                  </span>
                </div>
              </div>

              {/* Right: Time, Priority, Status, and Lead Record Link */}
              <div className="flex items-center gap-2 sm:gap-3 shrink-0">
                <span className="text-[12px] font-medium text-[#64748B] hidden sm:inline">
                  {item.scheduledTime}
                </span>

                <div className="flex flex-col items-end gap-1">
                  <span
                    className={`px-2 py-0.5 rounded-full text-[10.5px] font-bold ${priorityClass}`}
                  >
                    {item.priority}
                  </span>
                  <span className="px-2 py-0.2 rounded-full text-[10px] font-semibold bg-[#EFF6FF] text-[#2563EB]">
                    {item.completed ? 'Done' : item.status}
                  </span>
                </div>

                {/* Feature: Open Lead Record directly */}
                <button
                  type="button"
                  onClick={() => onOpenLeadRecord(item.leadId)}
                  className="p-1 text-[#94A3B8] hover:text-[#2563EB] hover:bg-[#EFF6FF] rounded transition-colors"
                  title="Open Lead Record"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
