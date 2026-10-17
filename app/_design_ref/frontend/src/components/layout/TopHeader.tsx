import React, { useState } from 'react';
import { Search, Bell, Menu, Landmark, ChevronDown } from 'lucide-react';
import { NotificationPopover } from './NotificationPopover';
import type { NotificationItem } from '../../types/admissions';

interface TopHeaderProps {
  onOpenMobileNav: () => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  notifications: NotificationItem[];
}

export const TopHeader: React.FC<TopHeaderProps> = ({
  onOpenMobileNav,
  searchQuery,
  onSearchChange,
  notifications,
}) => {
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const [selectedInstitute, setSelectedInstitute] = useState('TechVision Institute');
  const [isInstituteMenuOpen, setIsInstituteMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-20 bg-white border-b border-[#DCE5EF] px-4 sm:px-6 py-3 flex items-center justify-between gap-4">
      {/* Left: Mobile menu toggle + Global Search */}
      <div className="flex items-center gap-3 flex-1 max-w-md">
        <button
          type="button"
          onClick={onOpenMobileNav}
          className="lg:hidden p-2 text-[#64748B] hover:text-[#172B4D] hover:bg-[#F1F5F9] rounded-lg transition-colors"
          aria-label="Open navigation menu"
        >
          <Menu className="w-5 h-5 stroke-[1.8]" />
        </button>

        <div className="relative w-full">
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
            <Search className="w-4 h-4 text-[#94A3B8] stroke-[2]" />
          </div>
          <input
            type="search"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search students or courses..."
            className="w-full pl-10 pr-12 py-2 text-[13.5px] bg-[#FFFFFF] border border-[#DCE5EF] rounded-xl text-[#172B4D] placeholder-[#94A3B8] focus:border-[#3B82F6] focus:ring-2 focus:ring-[#3B82F6]/15 focus:outline-none transition-all"
          />
          <div className="absolute inset-y-0 right-0 pr-2.5 flex items-center pointer-events-none">
            <kbd className="px-1.5 py-0.5 text-[10px] font-mono text-[#64748B] bg-[#F8FAFC] border border-[#CBD5E1] rounded shadow-2xs">
              ⌘ K
            </kbd>
          </div>
        </div>
      </div>

      {/* Right: Notifications, Institute Selector, Administrator Profile */}
      <div className="flex items-center gap-3 sm:gap-5">
        {/* Notification Bell */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setIsNotificationsOpen(!isNotificationsOpen)}
            className="p-2 text-[#64748B] hover:text-[#172B4D] hover:bg-[#F4F7FB] rounded-full transition-colors relative"
            aria-label="View notifications"
            aria-expanded={isNotificationsOpen}
          >
            <Bell className="w-5 h-5 stroke-[1.8]" />
            <span className="absolute top-1 right-1 w-4 h-4 rounded-full bg-[#EF4444] text-white text-[10px] font-bold flex items-center justify-center border-2 border-white">
              3
            </span>
          </button>

          <NotificationPopover
            isOpen={isNotificationsOpen}
            onClose={() => setIsNotificationsOpen(false)}
            notifications={notifications}
          />
        </div>

        {/* Institute Selector */}
        <div className="relative hidden md:block">
          <button
            type="button"
            onClick={() => setIsInstituteMenuOpen(!isInstituteMenuOpen)}
            className="flex items-center gap-2 px-3 py-1.5 text-[13.5px] font-semibold text-[#172B4D] bg-[#F4F7FB] hover:bg-[#E9EFF7] border border-[#DCE5EF] rounded-lg transition-colors"
          >
            <Landmark className="w-4 h-4 text-[#245A8D] stroke-[2]" />
            <span>{selectedInstitute}</span>
            <ChevronDown className="w-3.5 h-3.5 text-[#64748B] stroke-[2]" />
          </button>

          {isInstituteMenuOpen && (
            <div className="absolute right-0 top-full mt-1.5 w-56 bg-white border border-[#DCE5EF] rounded-lg shadow-lg py-1.5 z-40 text-left">
              {['TechVision Institute', 'Apex University', 'Horizon College of Tech'].map((inst) => (
                <button
                  key={inst}
                  type="button"
                  onClick={() => {
                    setSelectedInstitute(inst);
                    setIsInstituteMenuOpen(false);
                  }}
                  className={`w-full px-3.5 py-2 text-[13px] text-left hover:bg-[#F4F7FB] transition-colors ${
                    selectedInstitute === inst ? 'font-semibold text-[#2563EB] bg-[#EFF6FF]' : 'text-[#172B4D]'
                  }`}
                >
                  {inst}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Administrator Profile Badge */}
        <div className="flex items-center gap-3 pl-2 sm:pl-3 border-l border-[#DCE5EF]">
          <div
            className="w-9 h-9 rounded-full bg-[#12345A] text-white font-bold text-[13px] flex items-center justify-center shadow-xs"
            title="Admissions Admin"
          >
            AD
          </div>
          <div className="hidden sm:block text-left">
            <p className="text-[13.5px] font-bold text-[#172B4D] leading-tight">Admissions Admin</p>
            <p className="text-[11.5px] text-[#64748B] font-medium">Administrator</p>
          </div>
        </div>
      </div>
    </header>
  );
};
