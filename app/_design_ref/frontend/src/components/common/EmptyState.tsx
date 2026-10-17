import type { LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: LucideIcon;
  actionText?: string;
  onAction?: () => void;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon: Icon,
  actionText,
  onAction,
  className = '',
}) => {
  return (
    <div
      className={`py-8 px-6 text-center flex flex-col items-center justify-center bg-[#FAFBFB] rounded border border-dashed border-[#DDE5E2] ${className}`}
    >
      {Icon && (
        <div className="w-8 h-8 rounded-full bg-[#E8F4F1] text-[#176B65] flex items-center justify-center mb-2.5">
          <Icon className="w-4 h-4 stroke-[1.75]" />
        </div>
      )}
      <h4 className="text-[14px] font-medium text-[#202B2A] mb-1">{title}</h4>
      <p className="text-[13px] text-[#667572] max-w-md mx-auto leading-relaxed">{description}</p>
      {actionText && onAction && (
        <button
          type="button"
          onClick={onAction}
          className="mt-3 inline-flex items-center text-[13px] font-medium text-[#176B65] hover:text-[#0F766E] hover:underline"
        >
          {actionText}
        </button>
      )}
    </div>
  );
};
