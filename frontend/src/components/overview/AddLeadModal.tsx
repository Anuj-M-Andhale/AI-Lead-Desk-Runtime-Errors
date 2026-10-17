import React, { useState } from 'react';
import { X, AlertCircle, CheckCircle2 } from 'lucide-react';
import type { Lead, LeadSource, LeadStatus } from '../../types/admissions';
import { saveLocalSessionLead } from '../../services/admissionsService';

interface AddLeadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLeadAdded: (lead: Lead) => void;
}

export const AddLeadModal: React.FC<AddLeadModalProps> = ({ isOpen, onClose, onLeadAdded }) => {
  const [studentName, setStudentName] = useState('');
  const [courseInterest, setCourseInterest] = useState('');
  const [source, setSource] = useState<LeadSource>('Website');
  const [status, setStatus] = useState<LeadStatus>('New');
  const [contact, setContact] = useState('');
  const [notes, setNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!studentName.trim() || !courseInterest.trim()) return;

    setIsSubmitting(true);
    setFeedback(null);

    // Save as local session lead (transparent frontend-only persistence)
    const newLead = saveLocalSessionLead({
      studentName: studentName.trim(),
      courseInterest: courseInterest.trim(),
      source,
      status,
      leadScore: status === 'Hot' ? 92 : status === 'Warm' ? 76 : status === 'New' ? 68 : 54,
      intentScore: status === 'Hot' ? 95 : status === 'Warm' ? 75 : status === 'New' ? 50 : 25,
      lastContact: 'Just now',
      phone: contact.trim() || '+91 98000 00000',
      notes: notes.trim() || undefined,
    });

    setIsSubmitting(false);
    setFeedback('Enquiry recorded in local browser session.');
    onLeadAdded(newLead);

    // Auto-close after short acknowledgement
    setTimeout(() => {
      onClose();
      // Reset form
      setStudentName('');
      setCourseInterest('');
      setContact('');
      setNotes('');
      setFeedback(null);
    }, 900);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-[2px]"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div className="bg-white border border-[#DCE5EF] rounded-2xl shadow-xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="px-6 py-4.5 border-b border-[#F1F5F9] flex items-center justify-between">
          <div>
            <h3 id="modal-title" className="text-[18px] font-bold text-[#172B4D]">
              Record Student Enquiry
            </h3>
            <p className="text-[13px] text-[#64748B] mt-0.5">
              Add new candidate enquiry for admissions counselling
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-[#94A3B8] hover:text-[#172B4D] hover:bg-[#F1F5F9] rounded-lg transition-colors"
            aria-label="Close dialog"
          >
            <X className="w-5 h-5 stroke-[2]" />
          </button>
        </div>

        {/* Backend limitation transparency note */}
        <div className="px-6 py-2.5 bg-[#EFF6FF] border-b border-[#DBEAFE] flex items-start gap-2.5 text-[12px] text-[#1E40AF]">
          <AlertCircle className="w-4 h-4 text-[#2563EB] shrink-0 mt-0.5" />
          <span>
            <strong>Local Session Storage:</strong> Saved to your current session. Syncs with admissions database once live backend is connected.
          </span>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {feedback && (
            <div className="p-3 bg-[#ECFDF5] border border-[#A7F3D0] text-[#065F46] text-[13px] font-medium rounded-xl flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-[#059669]" />
              {feedback}
            </div>
          )}

          <div>
            <label className="block text-[13px] font-semibold text-[#172B4D] mb-1">
              Student Full Name <span className="text-[#EF4444]">*</span>
            </label>
            <input
              type="text"
              required
              value={studentName}
              onChange={(e) => setStudentName(e.target.value)}
              placeholder="e.g. Priya Sharma"
              className="w-full px-3.5 py-2.5 text-[13.5px] bg-white border border-[#DCE5EF] rounded-xl text-[#172B4D] placeholder-[#94A3B8] focus:border-[#2563EB] focus:ring-2 focus:ring-[#2563EB]/15 focus:outline-none transition-all"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-[13px] font-semibold text-[#172B4D] mb-1">
                Course Interest <span className="text-[#EF4444]">*</span>
              </label>
              <input
                type="text"
                required
                value={courseInterest}
                onChange={(e) => setCourseInterest(e.target.value)}
                placeholder="e.g. Data Science"
                className="w-full px-3.5 py-2.5 text-[13.5px] bg-white border border-[#DCE5EF] rounded-xl text-[#172B4D] placeholder-[#94A3B8] focus:border-[#2563EB] focus:ring-2 focus:ring-[#2563EB]/15 focus:outline-none transition-all"
              />
            </div>

            <div>
              <label className="block text-[13px] font-semibold text-[#172B4D] mb-1">
                Contact Phone / Email
              </label>
              <input
                type="text"
                value={contact}
                onChange={(e) => setContact(e.target.value)}
                placeholder="e.g. +91 98200 12345"
                className="w-full px-3.5 py-2.5 text-[13.5px] bg-white border border-[#DCE5EF] rounded-xl text-[#172B4D] placeholder-[#94A3B8] focus:border-[#2563EB] focus:ring-2 focus:ring-[#2563EB]/15 focus:outline-none transition-all"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-[13px] font-semibold text-[#172B4D] mb-1">
                Enquiry Source
              </label>
              <select
                value={source}
                onChange={(e) => setSource(e.target.value as LeadSource)}
                className="w-full px-3.5 py-2.5 text-[13.5px] bg-white border border-[#DCE5EF] rounded-xl text-[#172B4D] focus:border-[#2563EB] focus:ring-2 focus:ring-[#2563EB]/15 focus:outline-none"
              >
                <option value="WhatsApp">WhatsApp</option>
                <option value="Instagram">Instagram</option>
                <option value="Website">Website</option>
                <option value="Phone">Phone</option>
                <option value="Walk-in">Walk-in</option>
              </select>
            </div>

            <div>
              <label className="block text-[13px] font-semibold text-[#172B4D] mb-1">
                Initial Lead Stage
              </label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value as LeadStatus)}
                className="w-full px-3.5 py-2.5 text-[13.5px] bg-white border border-[#DCE5EF] rounded-xl text-[#172B4D] focus:border-[#2563EB] focus:ring-2 focus:ring-[#2563EB]/15 focus:outline-none"
              >
                <option value="New">New</option>
                <option value="Hot">Hot (Immediate Intent)</option>
                <option value="Warm">Warm (Considering)</option>
                <option value="Cold">Cold</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-[13px] font-semibold text-[#172B4D] mb-1">
              Counsellor Initial Notes (Optional)
            </label>
            <textarea
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Inquired about scholarship criteria and hostel facilities"
              className="w-full px-3.5 py-2.5 text-[13.5px] bg-white border border-[#DCE5EF] rounded-xl text-[#172B4D] placeholder-[#94A3B8] focus:border-[#2563EB] focus:ring-2 focus:ring-[#2563EB]/15 focus:outline-none resize-none"
            />
          </div>

          {/* Footer Actions */}
          <div className="pt-3 flex items-center justify-end gap-3 border-t border-[#F1F5F9]">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2 text-[13px] font-semibold text-[#64748B] hover:text-[#172B4D] hover:bg-[#F1F5F9] rounded-xl transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !studentName.trim() || !courseInterest.trim()}
              className="px-5 py-2.5 text-[13px] font-semibold text-white bg-[#12345A] hover:bg-[#1A4574] disabled:opacity-50 disabled:cursor-not-allowed rounded-xl shadow-sm transition-colors flex items-center gap-1.5"
            >
              {isSubmitting ? 'Recording...' : 'Save Enquiry'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
