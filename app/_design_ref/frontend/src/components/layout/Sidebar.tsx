import React from 'react';
import {
  Home,
  Users,
  MessageSquare,
  Sparkles,
  Calendar,
  BarChart2,
  BookOpen,
  Settings,
  ChevronLeft,
  ChevronRight,
  ChevronsUpDown,
  X,
} from 'lucide-react';
import type { NavigationRoute } from '../../types/admissions';
import { GraduationCapIcon, UniversityCampusWatermark } from '../common/BrandIcons';

interface NavItem {
  id: NavigationRoute;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const NAV_ITEMS: NavItem[] = [
  { id: 'overview', label: 'Overview', icon: Home },
  { id: 'all-leads', label: 'All Leads', icon: Users },
  { id: 'conversations', label: 'Conversations', icon: MessageSquare },
  { id: 'ai-insights', label: 'AI Insights', icon: Sparkles },
  { id: 'demos-followups', label: 'Demo Classes & Follow-ups', icon: Calendar },
  { id: 'analytics', label: 'Analytics', icon: BarChart2 },
  { id: 'knowledge-base', label: 'Institute Knowledge Base', icon: BookOpen },
  { id: 'settings', label: 'Settings & Integrations', icon: Settings },
];

interface SidebarProps {
  currentRoute: NavigationRoute;
  onRouteChange: (route: NavigationRoute) => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  isMobileOpen: boolean;
  onCloseMobile: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentRoute,
  onRouteChange,
  isCollapsed,
  onToggleCollapse,
  isMobileOpen,
  onCloseMobile,
}) => {
  const handleNavClick = (route: NavigationRoute) => {
    onRouteChange(route);
    onCloseMobile();
  };

  const sidebarContent = (
    <div className="h-full flex flex-col justify-between select-none bg-[#0B1F3A] text-white relative overflow-hidden">
      {/* Top Branding Section */}
      <div>
        <div
          className={`flex items-center gap-3 px-4 py-5 border-b border-[#1A3358] ${
            isCollapsed ? 'justify-center' : 'justify-between'
          }`}
        >
          <div className="flex items-center gap-2.5 overflow-hidden">
            {/* Graduation Cap Icon */}
            <div className="text-white shrink-0">
              <GraduationCapIcon className="w-6 h-6 stroke-[2]" />
            </div>

            {!isCollapsed && (
              <div className="flex items-center gap-2">
                <span className="text-[17px] font-bold text-white tracking-tight leading-none">
                  AI Lead Desk
                </span>
                <ChevronsUpDown className="w-3.5 h-3.5 text-[#64748B] shrink-0" />
              </div>
            )}
          </div>

          {/* Mobile close button */}
          <button
            type="button"
            onClick={onCloseMobile}
            className="lg:hidden p-1.5 text-[#94A3B8] hover:text-white rounded-md"
            aria-label="Close navigation"
          >
            <X className="w-5 h-5 stroke-[1.75]" />
          </button>
        </div>

        {/* Navigation List with Original Names */}
        <nav className="p-3 space-y-1.5 mt-2" aria-label="Main Navigation">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = currentRoute === item.id;

            return (
              <button
                key={item.id}
                type="button"
                onClick={() => handleNavClick(item.id)}
                title={isCollapsed ? item.label : undefined}
                className={`w-full group relative flex items-center gap-3.5 px-3.5 py-2.5 rounded-xl text-[14px] font-medium transition-all text-left ${
                  isActive
                    ? 'bg-[#2563EB] text-white shadow-md shadow-[#2563EB]/25'
                    : 'text-[#94A3B8] hover:bg-[#132B4F] hover:text-white'
                } ${isCollapsed ? 'justify-center px-0' : ''}`}
                aria-current={isActive ? 'page' : undefined}
              >
                <Icon
                  className={`w-5 h-5 shrink-0 stroke-[1.8] ${
                    isActive ? 'text-white' : 'text-[#94A3B8] group-hover:text-white'
                  }`}
                />

                {!isCollapsed && (
                  <span className="truncate">{item.label}</span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* University building watermark illustration in sidebar background */}
      <div className="relative mt-auto">
        {!isCollapsed && (
          <div className="px-4 pb-2 text-[#38BDF8]">
            <UniversityCampusWatermark className="w-full h-auto text-[#60A5FA]" />
          </div>
        )}

        {/* Bottom Collapse Button */}
        <div className="p-3.5 border-t border-[#1A3358] bg-[#08182E]">
          {!isCollapsed ? (
            <button
              type="button"
              onClick={onToggleCollapse}
              className="flex items-center gap-2 text-[13px] font-medium text-[#94A3B8] hover:text-white transition-colors w-full"
            >
              <ChevronLeft className="w-4 h-4 stroke-[2]" />
              <span>Collapse Sidebar</span>
            </button>
          ) : (
            <button
              type="button"
              onClick={onToggleCollapse}
              className="flex justify-center text-[#94A3B8] hover:text-white transition-colors w-full p-1"
              title="Expand Sidebar"
            >
              <ChevronRight className="w-4 h-4 stroke-[2]" />
            </button>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Sidebar */}
      <aside
        className={`hidden lg:block shrink-0 transition-all duration-200 z-30 ${
          isCollapsed ? 'w-20' : 'w-64'
        }`}
      >
        <div className="sticky top-0 h-screen">{sidebarContent}</div>
      </aside>

      {/* Mobile Drawer */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 z-50 lg:hidden bg-black/40 backdrop-blur-xs flex"
          role="dialog"
          aria-modal="true"
        >
          <div className="w-72 max-w-[85vw] h-full shadow-2xl flex flex-col">
            {sidebarContent}
          </div>
          <div
            className="flex-1"
            onClick={onCloseMobile}
            aria-label="Close navigation overlay"
          />
        </div>
      )}
    </>
  );
};
