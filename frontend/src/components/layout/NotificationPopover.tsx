import React, { useEffect, useRef } from 'react';
import { Bell } from 'lucide-react';
import type { NotificationItem } from '../../types/admissions';

interface NotificationPopoverProps {
  isOpen: boolean;
  onClose: () => void;
  notifications: NotificationItem[];
}

export const NotificationPopover: React.FC<NotificationPopoverProps> = ({
  isOpen,
  onClose,
  notifications,
}) => {
  const popoverRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };

    const handleClickOutside = (e: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      ref={popoverRef}
      className="absolute right-0 top-full mt-2 w-80 sm:w-88 bg-white border border-[#DCE5EF] rounded-2xl shadow-xl z-50 overflow-hidden text-left animate-in fade-in zoom-in-95 duration-150"
      role="dialog"
      aria-label="Notifications"
    >
      <div className="px-4.5 py-3.5 border-b border-[#F1F5F9] flex items-center justify-between bg-white">
        <div className="flex items-center gap-2">
          <Bell className="w-4 h-4 text-[#2563EB] stroke-[2]" />
          <h4 className="text-[14px] font-bold text-[#172B4D]">Notifications</h4>
        </div>
        <span className="text-[11.5px] font-semibold text-[#64748B] px-2 py-0.5 bg-[#EFF6FF] text-[#2563EB] rounded-full">
          3 updates
        </span>
      </div>

      <div className="max-h-80 overflow-y-auto divide-y divide-[#F1F5F9]">
        {notifications.length === 0 ? (
          <>
            <div className="p-3.5 hover:bg-[#F8FAFC] transition-colors">
              <div className="flex items-start justify-between gap-2">
                <p className="text-[13px] font-semibold text-[#172B4D]">New High-Intent Enquiry</p>
                <span className="text-[11px] text-[#94A3B8] font-medium shrink-0">10m ago</span>
              </div>
              <p className="text-[12px] text-[#64748B] mt-0.5">Priya Sharma submitted interest in Data Science.</p>
            </div>
            <div className="p-3.5 hover:bg-[#F8FAFC] transition-colors">
              <div className="flex items-start justify-between gap-2">
                <p className="text-[13px] font-semibold text-[#172B4D]">Demo Scheduled</p>
                <span className="text-[11px] text-[#94A3B8] font-medium shrink-0">1h ago</span>
              </div>
              <p className="text-[12px] text-[#64748B] mt-0.5">Rohit Sharma booked an AI/ML demo for 10:30 AM.</p>
            </div>
            <div className="p-3.5 hover:bg-[#F8FAFC] transition-colors">
              <div className="flex items-start justify-between gap-2">
                <p className="text-[13px] font-semibold text-[#172B4D]">Follow-up Overdue Reminder</p>
                <span className="text-[11px] text-[#94A3B8] font-medium shrink-0">3h ago</span>
              </div>
              <p className="text-[12px] text-[#64748B] mt-0.5">Pooja Verma requested syllabus details via WhatsApp.</p>
            </div>
          </>
        ) : (
          notifications.map((n) => (
            <div key={n.id} className="p-3.5 hover:bg-[#F8FAFC] transition-colors">
              <div className="flex items-start justify-between gap-2">
                <p className="text-[13px] font-semibold text-[#172B4D]">{n.title}</p>
                <span className="text-[11px] text-[#94A3B8] font-medium shrink-0">{n.timestamp}</span>
              </div>
              <p className="text-[12px] text-[#64748B] mt-0.5">{n.message}</p>
            </div>
          ))
        )}
      </div>

      <div className="px-4 py-2.5 bg-[#F8FAFC] border-t border-[#F1F5F9] flex items-center justify-between text-[11.5px] text-[#64748B]">
        <span>Admissions Notification Stream</span>
        <span className="inline-flex items-center gap-1.5 text-[#16A34A] font-semibold">
          <span className="w-1.5 h-1.5 rounded-full bg-[#16A34A]" />
          Live
        </span>
      </div>
    </div>
  );
};
