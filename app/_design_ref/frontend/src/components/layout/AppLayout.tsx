import React, { useState } from 'react';
import { Sidebar } from './Sidebar';
import { TopHeader } from './TopHeader';
import type { NavigationRoute, NotificationItem } from '../../types/admissions';

interface AppLayoutProps {
  children: React.ReactNode;
  currentRoute: NavigationRoute;
  onRouteChange: (route: NavigationRoute) => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  notifications: NotificationItem[];
}

export const AppLayout: React.FC<AppLayoutProps> = ({
  children,
  currentRoute,
  onRouteChange,
  searchQuery,
  onSearchChange,
  notifications,
}) => {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileNavOpen, setIsMobileNavOpen] = useState(false);

  return (
    <div className="min-h-screen flex bg-[#F4F7FB] text-[#172B4D]">
      {/* Sidebar Navigation */}
      <Sidebar
        currentRoute={currentRoute}
        onRouteChange={onRouteChange}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
        isMobileOpen={isMobileNavOpen}
        onCloseMobile={() => setIsMobileNavOpen(false)}
      />

      {/* Main Content Viewport */}
      <div className="flex-1 flex flex-col min-w-0">
        <TopHeader
          onOpenMobileNav={() => setIsMobileNavOpen(true)}
          searchQuery={searchQuery}
          onSearchChange={onSearchChange}
          notifications={notifications}
        />

        <main className="flex-1 p-4 sm:p-6 lg:p-7 max-w-[1550px] w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
};
