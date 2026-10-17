import React from 'react';
import type { LeadStatus } from '../../types/admissions';

interface StatusIndicatorProps {
  status: LeadStatus;
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({ status }) => {
  const config = {
    Hot: {
      bg: 'bg-[#FEE2E2]/70',
      text: 'text-[#EF4444]',
      label: 'Hot',
    },
    Warm: {
      bg: 'bg-[#FFEDD5]/80',
      text: 'text-[#EA580C]',
      label: 'Warm',
    },
    New: {
      bg: 'bg-[#DBEAFE]/80',
      text: 'text-[#2563EB]',
      label: 'New',
    },
    Cold: {
      bg: 'bg-[#F1F5F9]',
      text: 'text-[#64748B]',
      label: 'Cold',
    },
  }[status] || {
    bg: 'bg-[#F1F5F9]',
    text: 'text-[#64748B]',
    label: status,
  };

  return (
    <span
      className={`inline-flex items-center justify-center min-w-[58px] px-2.5 py-0.5 rounded-full text-[12px] font-semibold ${config.bg} ${config.text}`}
    >
      {config.label}
    </span>
  );
};
