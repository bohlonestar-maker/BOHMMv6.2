import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Checkbox } from '../components/ui/checkbox';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { toast } from 'sonner';

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
  
  // Approver-specific state
  const [decision, setDecision] = useState('');  // 'approved' or 'denied'
  const [approverNotes, setApproverNotes] = useState('');
  
  // Canvas for drawn signature
  const canvasRef = useRef(null);
  const canvasContainerRef = useRef(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [hasDrawn, setHasDrawn] = useState(false);

  useEffect(() => {
    fetchDocument();
  }, [signingToken]);

  // Resize canvas on window resize
  useEffect(() => {
    const resizeCanvas = () => {
      if (canvasRef.current && canvasContainerRef.current) {
        const container = canvasContainerRef.current;
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        
        // Save current drawing
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        
        // Resize
        canvas.width = container.clientWidth - 16; // Account for padding
        canvas.height = 120;
        
        // Restore drawing (may be distorted but better than losing it)
        ctx.putImageData(imageData, 0, 0);
      }
    };

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    return () => window.removeEventListener('resize', resizeCanvas);
  }, [signatureType]);

  const fetchDocument = async () => {
    try {
      const response = await axios.get(`${API}/documents/sign/${signingToken}`);
      setDocumentData(response.data);
      setTypedName(response.data.recipient_name || '');
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

  // Canvas drawing functions with touch support
  const getCoordinates = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    
    if (e.touches) {
      return {
        x: (e.touches[0].clientX - rect.left) * scaleX,
        y: (e.touches[0].clientY - rect.top) * scaleY
      };
    }
    return {
      x: (e.clientX - rect.left) * scaleX,
      y: (e.clientY - rect.top) * scaleY
    };
  };

  const startDrawing = (e) => {
    e.preventDefault();
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const { x, y } = getCoordinates(e);
    
    ctx.beginPath();
    ctx.moveTo(x, y);
    setIsDrawing(true);
  };

  const draw = (e) => {
    if (!isDrawing) return;
    e.preventDefault();
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const { x, y } = getCoordinates(e);
    
    ctx.lineTo(x, y);
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.stroke();
    setHasDrawn(true);
  };

  const stopDrawing = (e) => {
    if (e) e.preventDefault();
    setIsDrawing(false);
  };

  const clearSignature = () => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    setHasDrawn(false);
  };

  const getSignatureImage = () => {
    if (!hasDrawn) return null;
    const canvas = canvasRef.current;
    return canvas.toDataURL('image/png');
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
    
    setSubmitting(true);
    
    try {
      const formData = new FormData();
      formData.append('signature_type', signatureType);
      formData.append('typed_name', typedName.trim());
      formData.append('consent_agreed', 'true');
      
      if (signatureType === 'drawn') {
        formData.append('signature_image', getSignatureImage());
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
          <i className="fas fa-spinner fa-spin text-3xl text-purple-400 mb-4"></i>
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
              <i className="fas fa-exclamation-circle"></i>
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
              <i className={`fas fa-${decision === 'denied' ? 'times' : 'check'}-circle`}></i>
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
                <i className="fas fa-info-circle mr-1"></i>
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
          <Card className="bg-orange-900/30 border-orange-700 mb-4 sm:mb-6">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-orange-600 flex items-center justify-center text-white font-bold">
                  {documentData?.approver_order}
                </div>
                <div>
                  <p className="text-orange-200 font-medium">
                    You are approver {documentData?.approver_order} of {documentData?.total_approvers}
                  </p>
                  <p className="text-orange-300/70 text-sm">
                    {documentData?.approver_title}
                  </p>
                </div>
              </div>
              
              {/* Previous approvals */}
              {documentData?.previous_approvals?.length > 0 && (
                <div className="mt-3 pt-3 border-t border-orange-700/50">
                  <p className="text-xs text-orange-300/70 mb-2">Previous approvals:</p>
                  <div className="space-y-1">
                    {documentData.previous_approvals.map((approval, i) => (
                      <div key={i} className="flex items-center gap-2 text-sm">
                        <i className={`fas fa-${approval.decision === 'approved' ? 'check text-green-400' : 'times text-red-400'}`}></i>
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
        )}

        {/* Document Info */}
        <Card className="bg-slate-800 border-slate-700 mb-4 sm:mb-6">
          <CardHeader className="p-4 sm:p-6">
            <CardTitle className="text-purple-400 flex items-center gap-2 text-base sm:text-lg">
              <i className="fas fa-file-signature"></i>
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
                <i className="fas fa-info-circle mr-2"></i>
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
            {documentData?.template_type === 'pdf' ? (
              <div className="bg-white rounded-lg overflow-hidden" style={{ height: '300px', maxHeight: '50vh' }}>
                <iframe
                  src={`${API}/documents/sign/${signingToken}/pdf`}
                  className="w-full h-full"
                  title="Document PDF"
                />
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
                  <i className="fas fa-keyboard mr-2"></i>
                  Type Signature
                </Button>
                <Button
                  type="button"
                  variant={signatureType === 'drawn' ? 'default' : 'outline'}
                  onClick={() => setSignatureType('drawn')}
                  className={`flex-1 ${signatureType === 'drawn' ? 'bg-purple-600' : ''}`}
                  data-testid="signature-type-drawn"
                >
                  <i className="fas fa-pen mr-2"></i>
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
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <Label className="text-slate-200 text-sm">Draw Your Signature</Label>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={clearSignature}
                      data-testid="clear-signature-btn"
                    >
                      <i className="fas fa-eraser mr-1"></i>
                      Clear
                    </Button>
                  </div>
                  <div ref={canvasContainerRef} className="bg-white rounded-lg p-2">
                    <canvas
                      ref={canvasRef}
                      width={300}
                      height={120}
                      className="w-full border-2 border-dashed border-slate-300 rounded cursor-crosshair"
                      style={{ touchAction: 'none' }}
                      onMouseDown={startDrawing}
                      onMouseMove={draw}
                      onMouseUp={stopDrawing}
                      onMouseLeave={stopDrawing}
                      onTouchStart={startDrawing}
                      onTouchMove={draw}
                      onTouchEnd={stopDrawing}
                      data-testid="signature-canvas"
                    />
                  </div>
                  <p className="text-xs text-slate-400 mt-1">
                    Use your finger or mouse to draw your signature
                  </p>
                </div>
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
                      >
                        <i className={`fas fa-check-circle text-2xl mb-2 ${decision === 'approved' ? 'text-green-400' : 'text-slate-400'}`}></i>
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
                      >
                        <i className={`fas fa-times-circle text-2xl mb-2 ${decision === 'denied' ? 'text-red-400' : 'text-slate-400'}`}></i>
                        <p className={`font-medium ${decision === 'denied' ? 'text-red-400' : 'text-slate-300'}`}>Deny</p>
                      </button>
                    </div>
                  </div>
                  
                  <div>
                    <Label className="text-slate-200 text-sm">Notes / Comments (Optional)</Label>
                    <Textarea
                      value={approverNotes}
                      onChange={(e) => setApproverNotes(e.target.value)}
                      placeholder={decision === 'denied' ? 'Please provide reason for denial...' : 'Add any notes or conditions...'}
                      className="bg-slate-700 border-slate-600 text-white mt-1 min-h-[80px]"
                    />
                  </div>
                </div>
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
                    <i className="fas fa-spinner fa-spin mr-2"></i>
                    {isApprover ? 'Submitting...' : 'Signing...'}
                  </>
                ) : isApprover ? (
                  <>
                    <i className={`fas fa-${decision === 'denied' ? 'times' : 'check'}-circle mr-2`}></i>
                    {decision ? (decision === 'approved' ? 'Approve & Sign' : 'Deny & Sign') : 'Select Decision'}
                  </>
                ) : (
                  <>
                    <i className="fas fa-signature mr-2"></i>
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
            <i className="fas fa-lock mr-1"></i>
            Your signature is secure and legally binding
          </p>
        </div>
      </div>
    </div>
  );
}
