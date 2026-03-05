/**
 * ApproverBanner - Displays approver information and previous approvals
 */
import React from 'react';
import { Card, CardContent } from '../ui/card';
import { Check, X } from 'lucide-react';

export default function ApproverBanner({ 
  approverOrder, 
  totalApprovers, 
  approverTitle, 
  previousApprovals = [] 
}) {
  return (
    <Card className="bg-orange-900/30 border-orange-700 mb-4 sm:mb-6">
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-orange-600 flex items-center justify-center text-white font-bold">
            {approverOrder}
          </div>
          <div>
            <p className="text-orange-200 font-medium">
              You are approver {approverOrder} of {totalApprovers}
            </p>
            <p className="text-orange-300/70 text-sm">
              {approverTitle}
            </p>
          </div>
        </div>
        
        {previousApprovals.length > 0 && (
          <div className="mt-3 pt-3 border-t border-orange-700/50">
            <p className="text-xs text-orange-300/70 mb-2">Previous approvals:</p>
            <div className="space-y-1">
              {previousApprovals.map((approval, i) => (
                <div key={i} className="flex items-center gap-2 text-sm">
                  {approval.decision === 'approved' ? (
                    <Check className="w-4 h-4 text-green-400" />
                  ) : (
                    <X className="w-4 h-4 text-red-400" />
                  )}
                  <span className="text-slate-300">{approval.title}</span>
                  <span className={approval.decision === 'approved' ? 'text-green-400' : 'text-red-400'}>
                    ({approval.decision})
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
