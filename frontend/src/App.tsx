import React, { useState } from 'react';
import { AppLayout } from './components/layout/AppLayout';
import { OverviewPage } from './pages/OverviewPage';
import { PlaceholderPage } from './pages/PlaceholderPage';
import { AddLeadModal } from './components/overview/AddLeadModal';
import type { NavigationRoute, NotificationItem, Lead } from './types/admissions';

export const App: React.FC = () => {
  const [currentRoute, setCurrentRoute] = useState<NavigationRoute>('overview');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isAddLeadOpen, setIsAddLeadOpen] = useState<boolean>(false);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);

  const handleLeadAdded = (lead: Lead) => {
    const newNotification: NotificationItem = {
      id: `notif-${Date.now()}`,
      title: 'New Enquiry Recorded',
      message: `${lead.studentName} registered for ${lead.courseInterest}.`,
      timestamp: 'Just now',
      read: false,
      type: 'enquiry',
    };
    setNotifications((prev) => [newNotification, ...prev]);
  };

  return (
    <>
      <AppLayout
        currentRoute={currentRoute}
        onRouteChange={setCurrentRoute}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        notifications={notifications}
      >
        {currentRoute === 'overview' ? (
          <OverviewPage
            onNavigate={setCurrentRoute}
            onOpenAddLead={() => setIsAddLeadOpen(true)}
            searchFilter={searchQuery}
          />
        ) : (
          <PlaceholderPage
            route={currentRoute}
            onBackToOverview={() => setCurrentRoute('overview')}
          />
        )}
      </AppLayout>

      {/* Add Lead Dialog */}
      <AddLeadModal
        isOpen={isAddLeadOpen}
        onClose={() => setIsAddLeadOpen(false)}
        onLeadAdded={handleLeadAdded}
      />
    </>
  );
};

export default App;
