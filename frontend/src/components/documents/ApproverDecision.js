/**
 * ApproverDecision - Approve/Deny decision buttons and notes input
 */
import React from 'react';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { CheckCircle, XCircle } from 'lucide-react';

export default function ApproverDecision({ decision, setDecision, notes, setNotes }) {
  return (
    <div className="border-t border-slate-700 pt-4 space-y-4">
      <div>
        <Label className="text-slate-200 text-sm mb-3 block">Your Decision *</Label>
        <div className="grid grid-cols-2 gap-3">
          <button
            type="button"
            onClick={() => setDecision('approved')}
            className={`p-4 rounded-lg border-2 transition-all ${
              decision === 'approved' 
                ? 'border-green-500 bg-green-600/20' 
                : 'border-slate-600 hover:border-green-500/50'
            }`}
            data-testid="approve-btn"
          >
            <CheckCircle className={`w-8 h-8 mx-auto mb-2 ${decision === 'approved' ? 'text-green-400' : 'text-slate-400'}`} />
            <p className={`font-medium ${decision === 'approved' ? 'text-green-400' : 'text-slate-300'}`}>Approve</p>
          </button>
          <button
            type="button"
            onClick={() => setDecision('denied')}
            className={`p-4 rounded-lg border-2 transition-all ${
              decision === 'denied' 
                ? 'border-red-500 bg-red-600/20' 
                : 'border-slate-600 hover:border-red-500/50'
            }`}
            data-testid="deny-btn"
          >
            <XCircle className={`w-8 h-8 mx-auto mb-2 ${decision === 'denied' ? 'text-red-400' : 'text-slate-400'}`} />
            <p className={`font-medium ${decision === 'denied' ? 'text-red-400' : 'text-slate-300'}`}>Deny</p>
          </button>
        </div>
      </div>
      
      <div>
        <Label className="text-slate-200 text-sm">Notes / Comments (Optional)</Label>
        <Textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder={decision === 'denied' ? 'Please provide reason for denial...' : 'Add any notes or conditions...'}
          className="bg-slate-700 border-slate-600 text-white mt-1 min-h-[80px]"
          data-testid="approver-notes"
        />
      </div>
    </div>
  );
}
