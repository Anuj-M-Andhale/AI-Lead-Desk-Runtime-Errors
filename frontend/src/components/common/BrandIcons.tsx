import React from 'react';
import { Globe, Phone, Users } from 'lucide-react';
import type { LeadSource } from '../../types/admissions';

export const WhatsAppIcon: React.FC<{ className?: string }> = ({ className = 'w-4 h-4' }) => (
  <svg
    viewBox="0 0 24 24"
    fill="currentColor"
    className={`text-[#25D366] shrink-0 ${className}`}
    aria-hidden="true"
  >
    <path d="M12.04 2c-5.46 0-9.91 4.45-9.91 9.91 0 1.75.46 3.45 1.32 4.95L2.05 22l5.25-1.38c1.45.79 3.08 1.21 4.74 1.21 5.46 0 9.91-4.45 9.91-9.91 0-2.65-1.03-5.14-2.9-7.01A9.816 9.816 0 0 0 12.04 2zm.01 1.67c4.54 0 8.24 3.7 8.24 8.24 0 2.2-.86 4.28-2.42 5.83a8.188 8.188 0 0 1-5.82 2.42c-1.45 0-2.88-.39-4.14-1.13l-.3-.18-3.08.81.82-3-.2-.31a8.157 8.157 0 0 1-1.25-4.44c0-4.54 3.7-8.24 8.25-8.24zm4.52 11.53c-.25-.13-1.47-.72-1.7-.81-.23-.08-.39-.13-.56.13-.17.25-.64.81-.79.97-.14.17-.29.19-.54.06-.25-.13-1.06-.39-2.02-1.24-.75-.67-1.26-1.5-1.4-1.75-.15-.25-.02-.39.11-.51.11-.11.25-.29.38-.44.13-.14.17-.25.25-.42.08-.17.04-.31-.02-.44-.06-.13-.56-1.34-.76-1.84-.2-.48-.41-.42-.56-.43h-.48c-.17 0-.44.06-.67.31-.23.25-.88.86-.88 2.1 0 1.24.9 2.44 1.03 2.61.13.17 1.77 2.7 4.29 3.78.6.26 1.07.41 1.43.53.6.19 1.15.16 1.58.1.48-.07 1.47-.6 1.68-1.18.21-.58.21-1.07.15-1.18-.06-.1-.21-.17-.46-.3z" />
  </svg>
);

export const InstagramIcon: React.FC<{ className?: string }> = ({ className = 'w-4 h-4' }) => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    className={`shrink-0 ${className}`}
    aria-hidden="true"
  >
    <defs>
      <linearGradient id="igGrad" x1="0%" y1="100%" x2="100%" y2="0%">
        <stop offset="0%" stopColor="#FFDC80" />
        <stop offset="25%" stopColor="#F77737" />
        <stop offset="50%" stopColor="#F56040" />
        <stop offset="75%" stopColor="#FD1D1D" />
        <stop offset="100%" stopColor="#C13584" />
      </linearGradient>
    </defs>
    <rect x="2" y="2" width="20" height="20" rx="5" ry="5" stroke="url(#igGrad)" strokeWidth="2" fill="none" />
    <circle cx="12" cy="12" r="4.5" stroke="url(#igGrad)" strokeWidth="2" fill="none" />
    <circle cx="17.5" cy="6.5" r="1.2" fill="#E1306C" />
  </svg>
);

export const GraduationCapIcon: React.FC<{ className?: string }> = ({ className = 'w-6 h-6' }) => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    aria-hidden="true"
  >
    <path d="M22 10v6M2 10l10-5 10 5-10 5z" />
    <path d="M6 12v5c3 3 9 3 12 0v-5" />
  </svg>
);

export const UniversityCampusWatermark: React.FC<{ className?: string }> = ({ className = '' }) => (
  <svg
    viewBox="0 0 300 160"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={`pointer-events-none select-none ${className}`}
    aria-hidden="true"
  >
    {/* Subtle architectural university building with dome and columns */}
    <g stroke="currentColor" strokeWidth="1.2" opacity="0.12">
      {/* Central Dome */}
      <path d="M120 70 C120 40 180 40 180 70 Z" />
      <line x1="150" y1="28" x2="150" y2="40" strokeWidth="2" />
      <polygon points="146,28 150,22 154,28" fill="currentColor" opacity="0.2" />
      
      {/* Pediment triangle */}
      <polygon points="100,70 150,52 200,70" />
      
      {/* Portico beam */}
      <rect x="95" y="70" width="110" height="8" rx="1" />
      
      {/* Classical Columns */}
      <line x1="108" y1="78" x2="108" y2="135" strokeWidth="3" />
      <line x1="125" y1="78" x2="125" y2="135" strokeWidth="3" />
      <line x1="142" y1="78" x2="142" y2="135" strokeWidth="3" />
      <line x1="158" y1="78" x2="158" y2="135" strokeWidth="3" />
      <line x1="175" y1="78" x2="175" y2="135" strokeWidth="3" />
      <line x1="192" y1="78" x2="192" y2="135" strokeWidth="3" />
      
      {/* Left Wing */}
      <rect x="25" y="85" width="70" height="50" rx="1" />
      <line x1="45" y1="95" x2="45" y2="115" />
      <line x1="60" y1="95" x2="60" y2="115" />
      <line x1="75" y1="95" x2="75" y2="115" />
      
      {/* Right Wing */}
      <rect x="205" y="85" width="70" height="50" rx="1" />
      <line x1="225" y1="95" x2="225" y2="115" />
      <line x1="240" y1="95" x2="240" y2="115" />
      <line x1="255" y1="95" x2="255" y2="115" />
      
      {/* Base steps */}
      <line x1="15" y1="135" x2="285" y2="135" strokeWidth="2" />
      <line x1="10" y1="140" x2="290" y2="140" strokeWidth="2" />
      <line x1="5" y1="145" x2="295" y2="145" strokeWidth="2" />
    </g>
  </svg>
);

export const LeadSourceBadge: React.FC<{ source: LeadSource; showLabel?: boolean }> = ({
  source,
  showLabel = true,
}) => {
  switch (source) {
    case 'WhatsApp':
      return (
        <span className="inline-flex items-center gap-2 text-[13px] font-medium text-[#1E293B]">
          <WhatsAppIcon className="w-4 h-4" />
          {showLabel && <span>WhatsApp</span>}
        </span>
      );
    case 'Instagram':
      return (
        <span className="inline-flex items-center gap-2 text-[13px] font-medium text-[#1E293B]">
          <InstagramIcon className="w-4 h-4" />
          {showLabel && <span>Instagram</span>}
        </span>
      );
    case 'Website':
      return (
        <span className="inline-flex items-center gap-2 text-[13px] font-medium text-[#1E293B]">
          <Globe className="w-4 h-4 text-[#3B82F6]" />
          {showLabel && <span>Website</span>}
        </span>
      );
    case 'Phone':
      return (
        <span className="inline-flex items-center gap-2 text-[13px] font-medium text-[#1E293B]">
          <Phone className="w-4 h-4 text-[#F97316]" />
          {showLabel && <span>Phone</span>}
        </span>
      );
    case 'Walk-in':
      return (
        <span className="inline-flex items-center gap-2 text-[13px] font-medium text-[#1E293B]">
          <Users className="w-4 h-4 text-[#64748B]" />
          {showLabel && <span>Walk-in</span>}
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center gap-2 text-[13px] font-medium text-[#1E293B]">
          <Globe className="w-4 h-4 text-[#64748B]" />
          {showLabel && <span>{source}</span>}
        </span>
      );
  }
};
