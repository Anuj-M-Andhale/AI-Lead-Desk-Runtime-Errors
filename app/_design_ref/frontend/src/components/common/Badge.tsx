import React from 'react';

export type BadgeVariant = 'teal' | 'neutral' | 'success' | 'warning' | 'error' | 'outline';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: 'sm' | 'md';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  size = 'md',
  className = '',
}) => {
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs';

  const variantClasses = {
    teal: 'bg-[#E8F4F1] text-[#176B65] border border-[#C5E1DC]',
    neutral: 'bg-[#F2F5F4] text-[#4A5754] border border-[#DDE5E2]',
    success: 'bg-[#EAF5ED] text-[#1E6B37] border border-[#C8E6D1]',
    warning: 'bg-[#FEF7EC] text-[#9A5B13] border border-[#F6E1BF]',
    error: 'bg-[#FDF2F2] text-[#A82A2A] border border-[#F5CACA]',
    outline: 'bg-transparent text-[#667572] border border-[#DDE5E2]',
  };

  return (
    <span
      className={`inline-flex items-center font-medium rounded ${sizeClasses} ${variantClasses[variant]} ${className}`}
    >
      {children}
    </span>
  );
};
