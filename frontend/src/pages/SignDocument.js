import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Checkbox } from '../components/ui/checkbox';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import { FileSignature, Lock, Keyboard, Pen, Loader2, CheckCircle, XCircle, Info, ExternalLink } from 'lucide-react';

// Document signing components
import { 
  SignatureCanvas, 
  ApproverBanner, 
  DocumentFormFields, 
  ApproverDecision 
} from '../components/documents';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function SignDocument() {
  const { signingToken } = useParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [documentData, setDocumentData] = useState(null);
  const [signatureType, setSignatureType] = useState('typed');
  const [typedName, setTypedName] = useState('');
  const [consentAgreed, setConsentAgreed] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [signed, setSigned] = useState(false);
  
  // Fillable form fields
  const [formFields, setFormFields] = useState({});
  
  // Approver-specific state
  const [decision, setDecision] = useState('');  // 'approved' or 'denied'
  const [approverNotes, setApproverNotes] = useState('');
  
  // Canvas for drawn signature
  const signatureCanvasRef = useRef(null);
  const [hasDrawn, setHasDrawn] = useState(false);

  useEffect(() => {
    fetchDocument();
  }, [signingToken]);

  const fetchDocument = async () => {
    try {
      const response = await axios.get(`${API}/documents/sign/${signingToken}`);
      setDocumentData(response.data);
      setTypedName(response.data.recipient_name || '');
      
      // Initialize form fields with any previously filled values
      const filledFields = response.data.filled_fields || {};
      const fieldPlacements = response.data.field_placements || [];
      const initialFields = {};
      fieldPlacements.forEach(field => {
        initialFields[field.id] = filledFields[field.id] || '';
      });
      setFormFields(initialFields);
    } catch (err) {
      console.error('Error fetching document:', err);
      if (err.response?.status === 404) {
        setError('This signing link is invalid or has expired.');
      } else if (err.response?.status === 400) {
        setError(err.response?.data?.detail || 'This document is no longer available for signing.');
      } else if (err.response?.status === 410) {
        setError('This signing link has expired.');
      } else {
        setError('Unable to load the document. Please try again later.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Get signature image from canvas ref
  const getSignatureImage = () => {
    return signatureCanvasRef.current?.getSignatureImage() || null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!typedName.trim()) {
      toast.error('Please enter your full legal name');
      return;
    }
    
    if (!consentAgreed) {
      toast.error('You must agree to the consent statement');
      return;
    }
    
    if (signatureType === 'drawn' && !hasDrawn) {
      toast.error('Please draw your signature');
      return;
    }
    
    // For approvers, require a decision
    if (documentData?.is_approver && !decision) {
      toast.error('Please select Approve or Deny');
      return;
    }
    
    // Validate required form fields
    const fieldPlacements = documentData?.field_placements || [];
    for (const field of fieldPlacements) {
      if (field.required && !formFields[field.id]?.trim()) {
        toast.error(`Please fill in: ${field.label}`);
        return;
      }
    }
    
    setSubmitting(true);
    
    try {
      const formData = new FormData();
      formData.append('signature_type', signatureType);
      formData.append('typed_name', typedName.trim());
      formData.append('consent_agreed', 'true');
      
      if (signatureType === 'drawn') {
        formData.append('signature_image', getSignatureImage());
      }
      
      // Add filled form fields
      if (Object.keys(formFields).length > 0) {
        formData.append('recipient_fields', JSON.stringify(formFields));
      }
      
      // Approver-specific fields
      if (documentData?.is_approver) {
        formData.append('decision', decision);
        if (approverNotes) {
          formData.append('approver_notes', approverNotes);
        }
      }
      
      const response = await axios.post(`${API}/documents/sign/${signingToken}/submit`, formData);
      
      if (documentData?.is_approver) {
        toast.success(`Document ${decision} successfully!`);
      } else if (response.data?.has_approvers) {
        toast.success('Document signed! It has been sent for approval.');
      } else {
        toast.success('Document signed successfully!');
      }
      setSigned(true);
    } catch (err) {
      console.error('Error submitting signature:', err);
      toast.error(err.response?.data?.detail || 'Failed to submit signature');
    } finally {
      setSubmitting(false);
    }
  };

  // Loading State
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
        <div className="text-center">
          <Loader2 className="w-10 h-10 text-purple-400 mb-4 animate-spin mx-auto" />
          <p className="text-white">Loading document...</p>
        </div>
      </div>
    );
  }

  // Error State
  if (error) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
        <Card className="max-w-md w-full bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-red-400 flex items-center gap-2 text-lg sm:text-xl">
              <XCircle className="w-6 h-6" />
              Unable to Sign
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-slate-300 text-sm sm:text-base">{error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Success State
  if (signed) {
    const isApprover = documentData?.is_approver;
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
        <Card className="max-w-md w-full bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className={`${decision === 'denied' ? 'text-red-400' : 'text-green-400'} flex items-center gap-2 text-lg sm:text-xl`}>
              {decision === 'denied' ? (
                <XCircle className="w-6 h-6" />
              ) : (
                <CheckCircle className="w-6 h-6" />
              )}
              {isApprover 
                ? (decision === 'approved' ? 'Document Approved!' : 'Document Denied')
                : 'Document Signed!'
              }
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-slate-300 text-sm sm:text-base">
              {isApprover 
                ? `You have ${decision} the document "${documentData?.template_name}".`
                : `Thank you! You have successfully signed "${documentData?.template_name}".`
              }
            </p>
            {documentData?.has_approvers && !isApprover && (
              <p className="text-purple-400 text-sm">
                <Info className="w-4 h-4 inline mr-1" />
                This document has been sent for approval.
              </p>
            )}
            <p className="text-slate-400 text-xs sm:text-sm">
              You may close this window.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Main Signing View
  const isApprover = documentData?.is_approver;
  
  return (
    <div className="min-h-screen bg-slate-900 py-4 sm:py-8 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="text-center mb-6 sm:mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2">
            {isApprover ? 'Document Approval' : 'Document Signing'}
          </h1>
          <p className="text-slate-400 text-sm sm:text-base">
            {isApprover 
              ? `Review and ${documentData?.approver_title ? `approve as ${documentData.approver_title}` : 'approve'}`
              : 'Please review and sign the document below'
            }
          </p>
        </div>

        {/* Approver Info Banner */}
        {isApprover && (
          <ApproverBanner
            approverOrder={documentData?.approver_order}
            totalApprovers={documentData?.total_approvers}
            approverTitle={documentData?.approver_title}
            previousApprovals={documentData?.previous_approvals}
          />
        )}

        {/* Document Info */}
        <Card className="bg-slate-800 border-slate-700 mb-4 sm:mb-6">
          <CardHeader className="p-4 sm:p-6">
            <CardTitle className="text-purple-400 flex items-center gap-2 text-base sm:text-lg">
              <FileSignature className="w-5 h-5" />
              <span className="truncate">{documentData?.template_name}</span>
            </CardTitle>
            <CardDescription className="text-xs sm:text-sm">
              {isApprover 
                ? `From: ${documentData?.recipient_name} | Sent by: ${documentData?.sent_by}`
                : `Sent by ${documentData?.sent_by} on ${new Date(documentData?.sent_at).toLocaleDateString()}`
              }
            </CardDescription>
          </CardHeader>
          {documentData?.message && (
            <CardContent className="p-4 sm:p-6 pt-0">
              <div className="bg-slate-700/50 rounded-lg p-3 sm:p-4 border-l-4 border-purple-500">
                <p className="text-slate-300 italic text-sm sm:text-base">"{documentData.message}"</p>
              </div>
            </CardContent>
          )}
        </Card>

        {/* Approval Chain Info for Recipient */}
        {!isApprover && documentData?.has_approvers && (
          <Card className="bg-purple-900/20 border-purple-700 mb-4 sm:mb-6">
            <CardContent className="p-4">
              <p className="text-purple-200 text-sm mb-2">
                <Info className="w-4 h-4 inline mr-2" />
                After you sign, this document will be sent for approval to:
              </p>
              <div className="flex flex-wrap gap-2">
                {documentData.approver_titles?.map((title, i) => (
                  <span key={i} className="px-2 py-1 bg-purple-600/30 rounded text-xs text-purple-200">
                    {i + 1}. {title}
                  </span>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Document Content */}
        <Card className="bg-slate-800 border-slate-700 mb-4 sm:mb-6">
          <CardHeader className="p-4 sm:p-6 pb-2 sm:pb-4">
            <CardTitle className="text-white text-base sm:text-lg">Document Content</CardTitle>
          </CardHeader>
          <CardContent className="p-4 sm:p-6 pt-0">
            {documentData?.template_type === 'pdf' || documentData?.has_pdf ? (
              <div className="space-y-3">
                {/* PDF Viewer with fallback */}
                <div className="bg-white rounded-lg overflow-hidden relative" style={{ height: '300px', maxHeight: '50vh' }}>
                  <iframe
                    src={`${API}/documents/sign/${signingToken}/pdf`}
                    className="w-full h-full"
                    title="Document PDF"
                    onError={() => console.log('PDF iframe error')}
                  />
                </div>
                {/* Fallback download button for blocked iframes */}
                <div className="flex items-center justify-center gap-3 p-3 bg-slate-700/50 rounded-lg">
                  <p className="text-slate-400 text-sm">
                    <Info className="w-4 h-4 inline mr-2" />
                    Can't see the document?
                  </p>
                  <a
                    href={`${API}/documents/sign/${signingToken}/pdf`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm transition-colors"
                  >
                    <ExternalLink className="w-4 h-4" />
                    Open PDF
                  </a>
                </div>
              </div>
            ) : (
              <div className="bg-slate-700/50 rounded-lg p-4 sm:p-6 max-h-64 sm:max-h-96 overflow-y-auto">
                <pre className="text-slate-300 whitespace-pre-wrap font-sans text-xs sm:text-sm leading-relaxed">
                  {documentData?.text_content}
                </pre>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Fillable Form Fields - Using component */}
        <DocumentFormFields 
          fieldPlacements={documentData?.field_placements} 
          formFields={formFields} 
          setFormFields={setFormFields} 
        />

        {/* Signature Form */}
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader className="p-4 sm:p-6 pb-2 sm:pb-4">
            <CardTitle className="text-white text-base sm:text-lg">Your Signature</CardTitle>
            <CardDescription className="text-xs sm:text-sm">
              Choose how you want to sign this document
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 sm:p-6 pt-0">
            <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-6">
              {/* Signature Type Toggle - Stack on mobile */}
              <div className="flex flex-col sm:flex-row gap-2 sm:gap-4">
                <Button
                  type="button"
                  variant={signatureType === 'typed' ? 'default' : 'outline'}
                  onClick={() => setSignatureType('typed')}
                  className={`flex-1 ${signatureType === 'typed' ? 'bg-purple-600' : ''}`}
                  data-testid="signature-type-typed"
                >
                  <Keyboard className="w-4 h-4 mr-2" />
                  Type Signature
                </Button>
                <Button
                  type="button"
                  variant={signatureType === 'drawn' ? 'default' : 'outline'}
                  onClick={() => setSignatureType('drawn')}
                  className={`flex-1 ${signatureType === 'drawn' ? 'bg-purple-600' : ''}`}
                  data-testid="signature-type-drawn"
                >
                  <Pen className="w-4 h-4 mr-2" />
                  Draw Signature
                </Button>
              </div>

              {/* Full Legal Name */}
              <div>
                <Label className="text-slate-200 text-sm">Full Legal Name *</Label>
                <Input
                  value={typedName}
                  onChange={(e) => setTypedName(e.target.value)}
                  placeholder="Enter your full legal name"
                  className="bg-slate-700 border-slate-600 text-white mt-1"
                  required
                  data-testid="typed-name-input"
                />
              </div>

              {/* Typed Signature Preview */}
              {signatureType === 'typed' && typedName && (
                <div>
                  <Label className="text-slate-200 text-sm">Signature Preview</Label>
                  <div className="bg-white rounded-lg p-4 mt-1">
                    <p className="text-xl sm:text-2xl text-slate-800 font-serif italic text-center break-words">
                      {typedName}
                    </p>
                  </div>
                </div>
              )}

              {/* Drawn Signature Canvas */}
              {signatureType === 'drawn' && (
                <SignatureCanvas 
                  ref={signatureCanvasRef}
                  onSignatureChange={setHasDrawn}
                />
              )}

              {/* Consent Checkbox */}
              <div className="bg-slate-700/50 rounded-lg p-3 sm:p-4 border border-slate-600">
                <div className="flex items-start gap-3">
                  <Checkbox
                    id="consent"
                    checked={consentAgreed}
                    onCheckedChange={setConsentAgreed}
                    className="mt-0.5"
                    data-testid="consent-checkbox"
                  />
                  <Label htmlFor="consent" className="text-slate-300 text-xs sm:text-sm cursor-pointer leading-relaxed">
                    I agree that this electronic signature is my legal signature and I intend to sign this document. 
                    I understand that by checking this box and submitting, I am legally signing this document.
                  </Label>
                </div>
              </div>

              {/* Approver Decision Section */}
              {isApprover && (
                <ApproverDecision
                  decision={decision}
                  setDecision={setDecision}
                  notes={approverNotes}
                  setNotes={setApproverNotes}
                />
              )}

              {/* Submit Button */}
              <Button
                type="submit"
                disabled={submitting || !consentAgreed || !typedName.trim() || (isApprover && !decision)}
                className={`w-full py-5 sm:py-6 text-base sm:text-lg ${
                  decision === 'denied' 
                    ? 'bg-red-600 hover:bg-red-700' 
                    : 'bg-purple-600 hover:bg-purple-700'
                }`}
                data-testid="submit-signature-btn"
              >
                {submitting ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    {isApprover ? 'Submitting...' : 'Signing...'}
                  </>
                ) : isApprover ? (
                  <>
                    {decision === 'denied' ? (
                      <XCircle className="w-5 h-5 mr-2" />
                    ) : (
                      <CheckCircle className="w-5 h-5 mr-2" />
                    )}
                    {decision ? (decision === 'approved' ? 'Approve & Sign' : 'Deny & Sign') : 'Select Decision'}
                  </>
                ) : (
                  <>
                    <FileSignature className="w-5 h-5 mr-2" />
                    Sign Document
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center mt-6 sm:mt-8 text-slate-500 text-xs sm:text-sm">
          <p>
            <Lock className="w-4 h-4 inline mr-1" />
            Your signature is secure and legally binding
          </p>
        </div>
      </div>
    </div>
  );
}
