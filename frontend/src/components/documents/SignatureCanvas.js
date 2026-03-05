/**
 * SignatureCanvas - A reusable canvas component for capturing drawn signatures
 * 
 * Features:
 * - Touch and mouse support
 * - Auto-resize on window resize
 * - Clear signature functionality
 * - Export to data URL
 */
import React, { useRef, useState, useEffect, useCallback, useImperativeHandle, forwardRef } from 'react';
import { Button } from '../ui/button';
import { Label } from '../ui/label';
import { Eraser } from 'lucide-react';

const SignatureCanvas = forwardRef(({ onSignatureChange }, ref) => {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [hasDrawn, setHasDrawn] = useState(false);

  // Expose methods to parent
  useImperativeHandle(ref, () => ({
    getSignatureImage: () => hasDrawn ? canvasRef.current?.toDataURL('image/png') : null,
    hasSignature: () => hasDrawn,
    clear: () => clearSignature()
  }));

  // Resize canvas on window resize
  useEffect(() => {
    const resizeCanvas = () => {
      if (canvasRef.current && containerRef.current) {
        const container = containerRef.current;
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        
        // Save current drawing
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        
        // Resize
        canvas.width = container.clientWidth - 16;
        canvas.height = 120;
        
        // Restore drawing
        ctx.putImageData(imageData, 0, 0);
      }
    };

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    return () => window.removeEventListener('resize', resizeCanvas);
  }, []);

  const getCoordinates = useCallback((e) => {
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
  }, []);

  const startDrawing = useCallback((e) => {
    e.preventDefault();
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const { x, y } = getCoordinates(e);
    
    ctx.beginPath();
    ctx.moveTo(x, y);
    setIsDrawing(true);
  }, [getCoordinates]);

  const draw = useCallback((e) => {
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
    
    if (!hasDrawn) {
      setHasDrawn(true);
      onSignatureChange?.(true);
    }
  }, [isDrawing, hasDrawn, getCoordinates, onSignatureChange]);

  const stopDrawing = useCallback((e) => {
    if (e) e.preventDefault();
    setIsDrawing(false);
  }, []);

  const clearSignature = useCallback(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    setHasDrawn(false);
    onSignatureChange?.(false);
  }, [onSignatureChange]);

  return (
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
          <Eraser className="w-4 h-4 mr-1" />
          Clear
        </Button>
      </div>
      <div ref={containerRef} className="bg-white rounded-lg p-2">
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
  );
});

SignatureCanvas.displayName = 'SignatureCanvas';

export default SignatureCanvas;
