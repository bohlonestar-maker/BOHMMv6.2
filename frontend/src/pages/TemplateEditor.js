import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '../components/ui/sheet';
import { toast } from 'sonner';
import { ChevronLeft, ChevronRight, Plus, Trash2, Save, Type, PenLine, Calendar, FileText, CheckSquare, Menu, X, Settings, Layers } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const FIELD_TYPES = [
  { value: 'text', label: 'Text Field', icon: Type },
  { value: 'date', label: 'Date Field', icon: Calendar },
  { value: 'textarea', label: 'Text Area', icon: FileText },
  { value: 'initials', label: 'Initials', icon: PenLine },
  { value: 'checkbox', label: 'Checkbox', icon: CheckSquare },
];

const SIGNER_TYPES = [
  { value: 'recipient', label: 'Recipient (Applicant)' },
  { value: 'approver_0', label: 'Approver 1 (Committee)' },
  { value: 'approver_1', label: 'Approver 2' },
  { value: 'approver_2', label: 'Approver 3' },
  { value: 'approver_3', label: 'Approver 4' },
  { value: 'approver_4', label: 'Approver 5' },
  { value: 'approver_5', label: 'Approver 6' },
  { value: 'approver_6', label: 'Approver 7' },
];

export default function TemplateEditor() {
  const { templateId } = useParams();
  const navigate = useNavigate();
  const containerRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [template, setTemplate] = useState(null);
  const [pagesInfo, setPagesInfo] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageImage, setPageImage] = useState(null);
  const [loadingPage, setLoadingPage] = useState(false);
  
  // Placements state
  const [fieldPlacements, setFieldPlacements] = useState([]);
  const [signaturePlacements, setSignaturePlacements] = useState([]);
  
  // UI state
  const [selectedItem, setSelectedItem] = useState(null);
  const [addMode, setAddMode] = useState(null);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [newItemConfig, setNewItemConfig] = useState({});
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [showElementsPanel, setShowElementsPanel] = useState(false);
  const mobileScrollRef = useRef(null);
  
  // Image dimensions
  const [imageDimensions, setImageDimensions] = useState({ width: 0, height: 0 });

  useEffect(() => {
    fetchTemplateData();
  }, [templateId]);

  useEffect(() => {
    if (pagesInfo.length > 0) {
      fetchPageImage(currentPage);
    }
  }, [currentPage, pagesInfo]);

  const fetchTemplateData = async () => {
    const token = localStorage.getItem('token');
    try {
      const templateRes = await axios.get(`${API}/documents/templates/${templateId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTemplate(templateRes.data);
      
      const pagesRes = await axios.get(`${API}/documents/templates/${templateId}/pages`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPagesInfo(pagesRes.data.pages || []);
      setFieldPlacements(pagesRes.data.field_placements || []);
      setSignaturePlacements(pagesRes.data.signature_placements || []);
    } catch (error) {
      toast.error('Failed to load template');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPageImage = async (pageNum) => {
    const token = localStorage.getItem('token');
    setLoadingPage(true);
    try {
      const response = await axios.get(
        `${API}/documents/templates/${templateId}/page/${pageNum}/image`,
        {
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob'
        }
      );
      const imageUrl = URL.createObjectURL(response.data);
      setPageImage(imageUrl);
    } catch (error) {
      toast.error('Failed to load page image');
      console.error(error);
    } finally {
      setLoadingPage(false);
    }
  };

  const handleImageLoad = (e) => {
    setImageDimensions({
      width: e.target.naturalWidth,
      height: e.target.naturalHeight
    });
  };

  const handleCanvasClick = useCallback((e) => {
    if (!addMode || !containerRef.current) return;
    
    const img = containerRef.current.querySelector('img');
    if (!img) return;
    
    const imgRect = img.getBoundingClientRect();
    
    const x = ((e.clientX - imgRect.left) / imgRect.width) * 100;
    const y = ((e.clientY - imgRect.top) / imgRect.height) * 100;
    
    if (x < 0 || x > 100 || y < 0 || y > 100) return;
    
    setNewItemConfig({
      x: Math.round(x * 10) / 10,
      y: Math.round(y * 10) / 10,
      page: currentPage,
      width: addMode === 'signature' ? 20 : 15,
      height: addMode === 'signature' ? 5 : 3,
      field_type: 'text',
      signer_type: 'recipient',
      label: '',
      required: true,
      include_date: true,
    });
    setShowAddDialog(true);
  }, [addMode, currentPage]);

  // Touch support for mobile
  const handleCanvasTouch = useCallback((e) => {
    if (!addMode || !containerRef.current) return;
    e.preventDefault();
    
    const touch = e.touches[0];
    const img = containerRef.current.querySelector('img');
    if (!img) return;
    
    const imgRect = img.getBoundingClientRect();
    
    const x = ((touch.clientX - imgRect.left) / imgRect.width) * 100;
    const y = ((touch.clientY - imgRect.top) / imgRect.height) * 100;
    
    if (x < 0 || x > 100 || y < 0 || y > 100) return;
    
    setNewItemConfig({
      x: Math.round(x * 10) / 10,
      y: Math.round(y * 10) / 10,
      page: currentPage,
      width: addMode === 'signature' ? 20 : 15,
      height: addMode === 'signature' ? 5 : 3,
      field_type: 'text',
      signer_type: 'recipient',
      label: '',
      required: true,
      include_date: true,
    });
    setShowAddDialog(true);
  }, [addMode, currentPage]);

  const handleAddItem = () => {
    const id = `${addMode}_${Date.now()}`;
    
    if (addMode === 'field') {
      const newField = {
        id,
        field_type: newItemConfig.field_type,
        label: newItemConfig.label || 'New Field',
        page: newItemConfig.page,
        x: newItemConfig.x,
        y: newItemConfig.y,
        width: newItemConfig.width,
        height: newItemConfig.height,
        required: newItemConfig.required,
        signer_type: newItemConfig.signer_type,
        placeholder: newItemConfig.placeholder || '',
      };
      setFieldPlacements(prev => [...prev, newField]);
    } else if (addMode === 'signature') {
      const newSig = {
        id,
        label: newItemConfig.label || 'Signature',
        page: newItemConfig.page,
        x: newItemConfig.x,
        y: newItemConfig.y,
        width: newItemConfig.width,
        height: newItemConfig.height,
        signer_type: newItemConfig.signer_type,
        include_date: newItemConfig.include_date,
        date_x: newItemConfig.x + newItemConfig.width + 5,
        date_y: newItemConfig.y,
      };
      setSignaturePlacements(prev => [...prev, newSig]);
    }
    
    setShowAddDialog(false);
    setAddMode(null);
    toast.success(`${addMode === 'field' ? 'Field' : 'Signature'} added`);
  };

  const handleDeleteItem = (type, id) => {
    if (type === 'field') {
      setFieldPlacements(prev => prev.filter(f => f.id !== id));
    } else {
      setSignaturePlacements(prev => prev.filter(s => s.id !== id));
    }
    setSelectedItem(null);
    toast.success('Item removed');
  };

  const handleUpdateItem = (type, id, updates) => {
    if (type === 'field') {
      setFieldPlacements(prev => prev.map(f => f.id === id ? { ...f, ...updates } : f));
    } else {
      setSignaturePlacements(prev => prev.map(s => s.id === id ? { ...s, ...updates } : s));
    }
  };

  const handleSave = async () => {
    const token = localStorage.getItem('token');
    setSaving(true);
    try {
      await axios.put(
        `${API}/documents/templates/${templateId}/placements`,
        {
          field_placements: fieldPlacements,
          signature_placements: signaturePlacements
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Placements saved successfully');
    } catch (error) {
      toast.error('Failed to save placements');
      console.error(error);
    } finally {
      setSaving(false);
    }
  };

  const currentPageFields = fieldPlacements.filter(f => f.page === currentPage);
  const currentPageSignatures = signaturePlacements.filter(s => s.page === currentPage);
  const totalElements = fieldPlacements.length + signaturePlacements.length;

  // Tools Panel Content (shared between mobile sheet and desktop sidebar)
  const ToolsPanel = ({ scrollContainerRef }) => (
    <div className="space-y-4">
      {/* Add Elements */}
      <div className="space-y-2">
        <h3 className="text-sm font-medium text-white">Add Elements</h3>
        <Button
          variant={addMode === 'field' ? 'default' : 'outline'}
          className="w-full justify-start text-sm"
          onClick={() => { setAddMode(addMode === 'field' ? null : 'field'); setMobileMenuOpen(false); }}
        >
          <Type className="w-4 h-4 mr-2" />
          Add Form Field
        </Button>
        <Button
          variant={addMode === 'signature' ? 'default' : 'outline'}
          className="w-full justify-start text-sm"
          onClick={() => { setAddMode(addMode === 'signature' ? null : 'signature'); setMobileMenuOpen(false); }}
        >
          <PenLine className="w-4 h-4 mr-2" />
          Add Signature
        </Button>
        {addMode && (
          <p className="text-xs text-purple-400 p-2 bg-purple-500/10 rounded">
            Tap on the PDF to place the {addMode}
          </p>
        )}
      </div>

      {/* Page Navigation */}
      <div className="space-y-2">
        <h3 className="text-sm font-medium text-white">Pages</h3>
        <div className="flex items-center justify-between bg-slate-700/50 rounded-lg p-2">
          <Button
            variant="ghost"
            size="sm"
            disabled={currentPage <= 1}
            onClick={() => setCurrentPage(p => p - 1)}
            className="h-8 w-8 p-0"
          >
            <ChevronLeft className="w-4 h-4" />
          </Button>
          <span className="text-white text-sm">
            {currentPage} / {pagesInfo.length}
          </span>
          <Button
            variant="ghost"
            size="sm"
            disabled={currentPage >= pagesInfo.length}
            onClick={() => setCurrentPage(p => p + 1)}
            className="h-8 w-8 p-0"
          >
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Elements List */}
      <div className="space-y-2">
        <h3 className="text-sm font-medium text-white">
          Elements on Page {currentPage}
          <span className="ml-2 text-xs text-slate-400">
            ({currentPageFields.length + currentPageSignatures.length})
          </span>
        </h3>
        <div className="space-y-1 max-h-48 overflow-y-auto">
          {currentPageFields.length === 0 && currentPageSignatures.length === 0 && (
            <p className="text-xs text-slate-500 p-2">No elements on this page</p>
          )}
          {currentPageFields.map(field => (
            <div
              key={field.id}
              className={`p-2 rounded text-xs cursor-pointer transition-colors ${
                selectedItem?.id === field.id
                  ? 'bg-purple-600/30 border border-purple-500'
                  : 'bg-slate-700/50 hover:bg-slate-600/50'
              }`}
              onClick={() => {
                setSelectedItem({ type: 'field', id: field.id });
                // Scroll to properties section on mobile
                setTimeout(() => {
                  if (scrollContainerRef?.current) {
                    scrollContainerRef.current.scrollTo({ top: scrollContainerRef.current.scrollHeight, behavior: 'smooth' });
                  }
                }, 100);
              }}
            >
              <div className="flex items-center justify-between">
                <span className="text-white truncate flex-1">{field.label}</span>
                <button
                  onClick={(e) => { e.stopPropagation(); handleDeleteItem('field', field.id); }}
                  className="text-red-400 hover:text-red-300 ml-2 p-1"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
              <span className="text-slate-400 text-[10px]">{field.field_type} • {field.signer_type.replace('_', ' ')}</span>
            </div>
          ))}
          {currentPageSignatures.map(sig => (
            <div
              key={sig.id}
              className={`p-2 rounded text-xs cursor-pointer transition-colors ${
                selectedItem?.id === sig.id
                  ? 'bg-orange-600/30 border border-orange-500'
                  : 'bg-slate-700/50 hover:bg-slate-600/50'
              }`}
              onClick={() => {
                setSelectedItem({ type: 'signature', id: sig.id });
                // Scroll to properties section on mobile
                setTimeout(() => {
                  if (scrollContainerRef?.current) {
                    scrollContainerRef.current.scrollTo({ top: scrollContainerRef.current.scrollHeight, behavior: 'smooth' });
                  }
                }, 100);
              }}
            >
              <div className="flex items-center justify-between">
                <span className="text-white truncate flex-1">{sig.label}</span>
                <button
                  onClick={(e) => { e.stopPropagation(); handleDeleteItem('signature', sig.id); }}
                  className="text-red-400 hover:text-red-300 ml-2 p-1"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
              <span className="text-slate-400 text-[10px]">signature • {sig.signer_type.replace('_', ' ')}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Selected Item Properties */}
      {selectedItem && (
        <div className="space-y-2 border-t border-slate-700 pt-4">
          <h3 className="text-sm font-medium text-white">Properties</h3>
          {selectedItem.type === 'field' && (() => {
            const field = fieldPlacements.find(f => f.id === selectedItem.id);
            if (!field) return null;
            return (
              <div className="space-y-3">
                <div>
                  <Label className="text-xs text-slate-400">Label</Label>
                  <Input
                    value={field.label}
                    onChange={(e) => handleUpdateItem('field', field.id, { label: e.target.value })}
                    className="h-8 text-sm bg-slate-700 border-slate-600"
                  />
                </div>
                <div>
                  <Label className="text-xs text-slate-400">Field Type</Label>
                  <Select
                    value={field.field_type}
                    onValueChange={(v) => handleUpdateItem('field', field.id, { field_type: v })}
                  >
                    <SelectTrigger className="h-8 text-sm bg-slate-700 border-slate-600">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {FIELD_TYPES.map(ft => (
                        <SelectItem key={ft.value} value={ft.value}>{ft.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className="text-xs text-slate-400">Signer</Label>
                  <Select
                    value={field.signer_type}
                    onValueChange={(v) => handleUpdateItem('field', field.id, { signer_type: v })}
                  >
                    <SelectTrigger className="h-8 text-sm bg-slate-700 border-slate-600">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {SIGNER_TYPES.map(st => (
                        <SelectItem key={st.value} value={st.value}>{st.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                {/* Position Controls with Arrow Buttons */}
                <div className="border-t border-slate-600 pt-3 mt-3">
                  <Label className="text-xs text-slate-400 mb-2 block">Position (%)</Label>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <Label className="text-[10px] text-slate-500">X (Left)</Label>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => handleUpdateItem('field', field.id, { x: Math.max(0, (field.x || 0) - 1) })}
                          className="h-7 w-7 flex items-center justify-center bg-slate-600 hover:bg-slate-500 rounded text-white"
                        >
                          <ChevronLeft className="w-4 h-4" />
                        </button>
                        <Input
                          type="number"
                          min="0"
                          max="100"
                          step="1"
                          value={field.x}
                          onChange={(e) => handleUpdateItem('field', field.id, { x: parseFloat(e.target.value) || 0 })}
                          className="h-7 text-xs bg-slate-700 border-slate-600 text-center flex-1"
                        />
                        <button
                          onClick={() => handleUpdateItem('field', field.id, { x: Math.min(100, (field.x || 0) + 1) })}
                          className="h-7 w-7 flex items-center justify-center bg-slate-600 hover:bg-slate-500 rounded text-white"
                        >
                          <ChevronRight className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                    <div>
                      <Label className="text-[10px] text-slate-500">Y (Top)</Label>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => handleUpdateItem('field', field.id, { y: Math.max(0, (field.y || 0) - 1) })}
                          className="h-7 w-7 flex items-center justify-center bg-slate-600 hover:bg-slate-500 rounded text-white"
                        >
                          <ChevronLeft className="w-4 h-4" />
                        </button>
                        <Input
                          type="number"
                          min="0"
                          max="100"
                          step="1"
                          value={field.y}
                          onChange={(e) => handleUpdateItem('field', field.id, { y: parseFloat(e.target.value) || 0 })}
                          className="h-7 text-xs bg-slate-700 border-slate-600 text-center flex-1"
                        />
                        <button
                          onClick={() => handleUpdateItem('field', field.id, { y: Math.min(100, (field.y || 0) + 1) })}
                          className="h-7 w-7 flex items-center justify-center bg-slate-600 hover:bg-slate-500 rounded text-white"
                        >
                          <ChevronRight className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                    <div>
                      <Label className="text-[10px] text-slate-500">Width</Label>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => handleUpdateItem('field', field.id, { width: Math.max(1, (field.width || 1) - 1) })}
                          className="h-7 w-7 flex items-center justify-center bg-slate-600 hover:bg-slate-500 rounded text-white"
                        >
                          <ChevronLeft className="w-4 h-4" />
                        </button>
                        <Input
                          type="number"
                          min="1"
                          max="100"
                          step="1"
                          value={field.width}
                          onChange={(e) => handleUpdateItem('field', field.id, { width: parseFloat(e.target.value) || 1 })}
                          className="h-7 text-xs bg-slate-700 border-slate-600 text-center flex-1"
                        />
                        <button
                          onClick={() => handleUpdateItem('field', field.id, { width: Math.min(100, (field.width || 1) + 1) })}
                          className="h-7 w-7 flex items-center justify-center bg-slate-600 hover:bg-slate-500 rounded text-white"
                        >
                          <ChevronRight className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                    <div>
                      <Label className="text-[10px] text-slate-500">Height</Label>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => handleUpdateItem('field', field.id, { height: Math.max(1, (field.height || 1) - 1) })}
                          className="h-7 w-7 flex items-center justify-center bg-slate-600 hover:bg-slate-500 rounded text-white"
                        >
                          <ChevronLeft className="w-4 h-4" />
                        </button>
                        <Input
                          type="number"
                          min="1"
                          max="100"
                          step="1"
                          value={field.height}
                          onChange={(e) => handleUpdateItem('field', field.id, { height: parseFloat(e.target.value) || 1 })}
                          className="h-7 text-xs bg-slate-700 border-slate-600 text-center flex-1"
                        />
                        <button
                          onClick={() => handleUpdateItem('field', field.id, { height: Math.min(100, (field.height || 1) + 1) })}
                          className="h-7 w-7 flex items-center justify-center bg-slate-600 hover:bg-slate-500 rounded text-white"
                        >
                          <ChevronRight className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })()}
          {selectedItem.type === 'signature' && (() => {
            const sig = signaturePlacements.find(s => s.id === selectedItem.id);
            if (!sig) return null;
            return (
              <div className="space-y-3">
                <div>
                  <Label className="text-xs text-slate-400">Label</Label>
                  <Input
                    value={sig.label}
                    onChange={(e) => handleUpdateItem('signature', sig.id, { label: e.target.value })}
                    className="h-8 text-sm bg-slate-700 border-slate-600"
                  />
                </div>
                <div>
                  <Label className="text-xs text-slate-400">Signer</Label>
                  <Select
                    value={sig.signer_type}
                    onValueChange={(v) => handleUpdateItem('signature', sig.id, { signer_type: v })}
                  >
                    <SelectTrigger className="h-8 text-sm bg-slate-700 border-slate-600">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {SIGNER_TYPES.map(st => (
                        <SelectItem key={st.value} value={st.value}>{st.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                {/* Position Controls with Arrow Buttons */}
                <div className="border-t border-slate-600 pt-3 mt-3">
                  <Label className="text-xs text-slate-400 mb-2 block">Position (%)</Label>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <Label className="text-[10px] text-slate-500">X (Left)</Label>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => handleUpdateItem('signature', sig.id, { x: Math.max(0, (sig.x || 0) - 1) })}
                          className="h-7 w-7 flex items-center justify-center bg-slate-600 hover:bg-slate-500 rounded text-white"
                        >
                          <ChevronLeft className="w-4 h-4" />
                        </button>
                        <Input
                          type="number"
                          min="0"
                          max="100"
                          step="1"
                          value={sig.x}
                          onChange={(e) => handleUpdateItem('signature', sig.id, { x: parseFloat(e.target.value) || 0 })}
                          className="h-7 text-xs bg-slate-700 border-slate-600 text-center flex-1"
                        />
                        <button
                          onClick={() => handleUpdateItem('signature', sig.id, { x: Math.min(100, (sig.x || 0) + 1) })}
                          className="h-7 w-7 flex items-center justify-center bg-slate-600 hover:bg-slate-500 rounded text-white"
                        >
                          <ChevronRight className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                    <div>
                      <Label className="text-[10px] text-slate-500">Y (Top)</Label>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => handleUpdateItem('signature', sig.id, { y: Math.max(0, (sig.y || 0) - 1) })}
                          className="h-7 w-7 flex items-center justify-center bg-slate-600 hover:bg-slate-500 rounded text-white"
                        >
                          <ChevronLeft className="w-4 h-4" />
                        </button>
                        <Input
                          type="number"
                          min="0"
                          max="100"
                          step="1"
                          value={sig.y}
                          onChange={(e) => handleUpdateItem('signature', sig.id, { y: parseFloat(e.target.value) || 0 })}
                          className="h-7 text-xs bg-slate-700 border-slate-600 text-center flex-1"
                        />
                        <button
                          onClick={() => handleUpdateItem('signature', sig.id, { y: Math.min(100, (sig.y || 0) + 1) })}
                          className="h-7 w-7 flex items-center justify-center bg-slate-600 hover:bg-slate-500 rounded text-white"
                        >
                          <ChevronRight className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                    <div>
                      <Label className="text-[10px] text-slate-500">Width</Label>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => handleUpdateItem('signature', sig.id, { width: Math.max(1, (sig.width || 1) - 1) })}
                          className="h-7 w-7 flex items-center justify-center bg-slate-600 hover:bg-slate-500 rounded text-white"
                        >
                          <ChevronLeft className="w-4 h-4" />
                        </button>
                        <Input
                          type="number"
                          min="1"
                          max="100"
                          step="1"
                          value={sig.width}
                          onChange={(e) => handleUpdateItem('signature', sig.id, { width: parseFloat(e.target.value) || 1 })}
                          className="h-7 text-xs bg-slate-700 border-slate-600 text-center flex-1"
                        />
                        <button
                          onClick={() => handleUpdateItem('signature', sig.id, { width: Math.min(100, (sig.width || 1) + 1) })}
                          className="h-7 w-7 flex items-center justify-center bg-slate-600 hover:bg-slate-500 rounded text-white"
                        >
                          <ChevronRight className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                    <div>
                      <Label className="text-[10px] text-slate-500">Height</Label>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => handleUpdateItem('signature', sig.id, { height: Math.max(1, (sig.height || 1) - 1) })}
                          className="h-7 w-7 flex items-center justify-center bg-slate-600 hover:bg-slate-500 rounded text-white"
                        >
                          <ChevronLeft className="w-4 h-4" />
                        </button>
                        <Input
                          type="number"
                          min="1"
                          max="100"
                          step="1"
                          value={sig.height}
                          onChange={(e) => handleUpdateItem('signature', sig.id, { height: parseFloat(e.target.value) || 1 })}
                          className="h-7 text-xs bg-slate-700 border-slate-600 text-center flex-1"
                        />
                        <button
                          onClick={() => handleUpdateItem('signature', sig.id, { height: Math.min(100, (sig.height || 1) + 1) })}
                          className="h-7 w-7 flex items-center justify-center bg-slate-600 hover:bg-slate-500 rounded text-white"
                        >
                          <ChevronRight className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <i className="fas fa-spinner fa-spin text-3xl text-purple-400 mb-4"></i>
          <p className="text-white">Loading template...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col">
      {/* Header - Responsive */}
      <div className="bg-slate-800 border-b border-slate-700 px-3 sm:px-4 py-2 sm:py-3 sticky top-0 z-20">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 sm:gap-4 min-w-0">
            <Button 
              variant="ghost" 
              size="sm"
              onClick={() => navigate('/document-templates')}
              className="flex-shrink-0 h-8 sm:h-9 px-2 sm:px-3"
            >
              <ChevronLeft className="w-4 h-4" />
              <span className="hidden sm:inline ml-1">Back</span>
            </Button>
            <div className="min-w-0">
              <h1 className="text-sm sm:text-lg font-semibold text-white truncate">{template?.name}</h1>
              <p className="text-xs text-slate-400 hidden sm:block">Configure form fields and signature placements</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {/* Mobile Menu Button */}
            <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
              <SheetTrigger asChild>
                <Button variant="outline" size="sm" className="lg:hidden h-8 sm:h-9">
                  <Menu className="w-4 h-4" />
                  <span className="ml-1 text-xs">{totalElements}</span>
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="w-80 bg-slate-800 border-slate-700 p-0 flex flex-col h-full">
                <SheetHeader className="p-4 pb-2 flex-shrink-0">
                  <SheetTitle className="text-white">Tools</SheetTitle>
                </SheetHeader>
                <div ref={mobileScrollRef} className="flex-1 overflow-y-auto p-4 pt-0">
                  <ToolsPanel scrollContainerRef={mobileScrollRef} />
                </div>
              </SheetContent>
            </Sheet>
            
            <Button 
              onClick={handleSave} 
              disabled={saving} 
              size="sm"
              className="bg-purple-600 hover:bg-purple-700 h-8 sm:h-9 px-2 sm:px-4"
            >
              <Save className="w-4 h-4" />
              <span className="hidden sm:inline ml-2">{saving ? 'Saving...' : 'Save'}</span>
            </Button>
          </div>
        </div>
      </div>

      {/* Mobile Add Mode Indicator */}
      {addMode && (
        <div className="lg:hidden bg-purple-600 text-white text-center py-2 px-4 text-sm flex items-center justify-between">
          <span>Tap on PDF to place {addMode}</span>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => setAddMode(null)}
            className="h-6 px-2 text-white hover:bg-purple-700"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>
      )}

      {/* Mobile Page Navigation */}
      <div className="lg:hidden bg-slate-800/50 border-b border-slate-700 px-3 py-2 flex items-center justify-between">
        <Button
          variant="ghost"
          size="sm"
          disabled={currentPage <= 1}
          onClick={() => setCurrentPage(p => p - 1)}
          className="h-8"
        >
          <ChevronLeft className="w-4 h-4 mr-1" />
          Prev
        </Button>
        <span className="text-white text-sm font-medium">
          Page {currentPage} of {pagesInfo.length}
        </span>
        <Button
          variant="ghost"
          size="sm"
          disabled={currentPage >= pagesInfo.length}
          onClick={() => setCurrentPage(p => p + 1)}
          className="h-8"
        >
          Next
          <ChevronRight className="w-4 h-4 ml-1" />
        </Button>
      </div>

      <div className="flex-1 flex">
        {/* Desktop Left Panel */}
        <div className="hidden lg:block w-64 flex-shrink-0 bg-slate-800/50 border-r border-slate-700 p-4 overflow-y-auto">
          <ToolsPanel scrollContainerRef={null} />
        </div>

        {/* Main Canvas Area */}
        <div className="flex-1 p-2 sm:p-4 overflow-auto">
          <div className="max-w-4xl mx-auto">
            <div
              ref={containerRef}
              className={`relative bg-white rounded-lg overflow-hidden shadow-xl ${addMode ? 'cursor-crosshair ring-2 ring-purple-500' : ''}`}
              onClick={handleCanvasClick}
              onTouchStart={handleCanvasTouch}
            >
              {loadingPage ? (
                <div className="flex items-center justify-center bg-slate-200 min-h-[400px] sm:min-h-[600px]">
                  <i className="fas fa-spinner fa-spin text-2xl text-slate-500"></i>
                </div>
              ) : pageImage ? (
                <>
                  <img
                    src={pageImage}
                    alt={`Page ${currentPage}`}
                    className="w-full h-auto"
                    onLoad={handleImageLoad}
                    draggable={false}
                  />
                  {/* Field overlays */}
                  {currentPageFields.map(field => (
                    <div
                      key={field.id}
                      className={`absolute border-2 rounded transition-all ${
                        selectedItem?.id === field.id
                          ? 'border-purple-500 bg-purple-500/30 z-10'
                          : 'border-blue-500 bg-blue-500/20 hover:bg-blue-500/30'
                      }`}
                      style={{
                        left: `${field.x}%`,
                        top: `${field.y}%`,
                        width: `${field.width}%`,
                        height: `${field.height}%`,
                        minWidth: '20px',
                        minHeight: '12px',
                      }}
                      onClick={(e) => {
                        e.stopPropagation();
                        if (!addMode) setSelectedItem({ type: 'field', id: field.id });
                      }}
                    >
                      <span className="absolute -top-5 left-0 text-[10px] sm:text-xs bg-blue-600 text-white px-1 rounded whitespace-nowrap max-w-[100px] sm:max-w-none truncate">
                        {field.label}
                      </span>
                    </div>
                  ))}
                  {/* Signature overlays */}
                  {currentPageSignatures.map(sig => (
                    <div
                      key={sig.id}
                      className={`absolute border-2 rounded transition-all ${
                        selectedItem?.id === sig.id
                          ? 'border-orange-500 bg-orange-500/30 z-10'
                          : 'border-orange-400 bg-orange-400/20 hover:bg-orange-400/30'
                      }`}
                      style={{
                        left: `${sig.x}%`,
                        top: `${sig.y}%`,
                        width: `${sig.width}%`,
                        height: `${sig.height}%`,
                        minWidth: '30px',
                        minHeight: '15px',
                      }}
                      onClick={(e) => {
                        e.stopPropagation();
                        if (!addMode) setSelectedItem({ type: 'signature', id: sig.id });
                      }}
                    >
                      <span className="absolute -top-5 left-0 text-[10px] sm:text-xs bg-orange-600 text-white px-1 rounded whitespace-nowrap max-w-[100px] sm:max-w-none truncate">
                        {sig.label}
                      </span>
                    </div>
                  ))}
                </>
              ) : (
                <div className="flex items-center justify-center text-slate-500 min-h-[400px] sm:min-h-[600px]">
                  No page to display
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Bottom Bar - Quick Actions */}
      <div className="lg:hidden bg-slate-800 border-t border-slate-700 px-3 py-2 flex items-center justify-around gap-2 safe-area-inset-bottom">
        <Button
          variant={addMode === 'field' ? 'default' : 'outline'}
          size="sm"
          className={`flex-1 h-10 ${addMode === 'field' ? 'bg-purple-600' : ''}`}
          onClick={() => setAddMode(addMode === 'field' ? null : 'field')}
        >
          <Type className="w-4 h-4 mr-1" />
          <span className="text-xs">Field</span>
        </Button>
        <Button
          variant={addMode === 'signature' ? 'default' : 'outline'}
          size="sm"
          className={`flex-1 h-10 ${addMode === 'signature' ? 'bg-orange-600' : ''}`}
          onClick={() => setAddMode(addMode === 'signature' ? null : 'signature')}
        >
          <PenLine className="w-4 h-4 mr-1" />
          <span className="text-xs">Sign</span>
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="flex-1 h-10"
          onClick={() => setShowElementsPanel(true)}
        >
          <Layers className="w-4 h-4 mr-1" />
          <span className="text-xs">{currentPageFields.length + currentPageSignatures.length}</span>
        </Button>
      </div>

      {/* Mobile Elements Panel */}
      <Sheet open={showElementsPanel} onOpenChange={setShowElementsPanel}>
        <SheetContent side="bottom" className="bg-slate-800 border-slate-700 h-[60vh] rounded-t-xl">
          <SheetHeader className="mb-4">
            <SheetTitle className="text-white">Elements on Page {currentPage}</SheetTitle>
          </SheetHeader>
          <div className="space-y-2 overflow-y-auto max-h-[calc(60vh-100px)]">
            {currentPageFields.length === 0 && currentPageSignatures.length === 0 && (
              <p className="text-slate-500 text-sm text-center py-8">No elements on this page. Tap "Field" or "Sign" to add.</p>
            )}
            {currentPageFields.map(field => (
              <div
                key={field.id}
                className="p-3 bg-slate-700/50 rounded-lg flex items-center justify-between"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-white text-sm font-medium truncate">{field.label}</p>
                  <p className="text-slate-400 text-xs">{field.field_type} • {field.signer_type.replace('_', ' ')}</p>
                </div>
                <button
                  onClick={() => handleDeleteItem('field', field.id)}
                  className="p-2 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
            {currentPageSignatures.map(sig => (
              <div
                key={sig.id}
                className="p-3 bg-slate-700/50 rounded-lg flex items-center justify-between"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-white text-sm font-medium truncate">{sig.label}</p>
                  <p className="text-slate-400 text-xs">signature • {sig.signer_type.replace('_', ' ')}</p>
                </div>
                <button
                  onClick={() => handleDeleteItem('signature', sig.id)}
                  className="p-2 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </SheetContent>
      </Sheet>

      {/* Add Item Dialog */}
      <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
        <DialogContent className="w-[95vw] max-w-md mx-auto rounded-lg">
          <DialogHeader>
            <DialogTitle>
              Add {addMode === 'field' ? 'Form Field' : 'Signature'}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Label</Label>
              <Input
                value={newItemConfig.label || ''}
                onChange={(e) => setNewItemConfig(prev => ({ ...prev, label: e.target.value }))}
                placeholder={addMode === 'field' ? 'e.g., First Name' : 'e.g., Applicant Signature'}
                className="mt-1"
              />
            </div>
            {addMode === 'field' && (
              <div>
                <Label>Field Type</Label>
                <Select
                  value={newItemConfig.field_type}
                  onValueChange={(v) => setNewItemConfig(prev => ({ ...prev, field_type: v }))}
                >
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {FIELD_TYPES.map(ft => (
                      <SelectItem key={ft.value} value={ft.value}>{ft.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
            <div>
              <Label>Who fills this?</Label>
              <Select
                value={newItemConfig.signer_type}
                onValueChange={(v) => setNewItemConfig(prev => ({ ...prev, signer_type: v }))}
              >
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {SIGNER_TYPES.map(st => (
                    <SelectItem key={st.value} value={st.value}>{st.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Width (%)</Label>
                <Input
                  type="number"
                  min="1"
                  max="50"
                  value={newItemConfig.width || 15}
                  onChange={(e) => setNewItemConfig(prev => ({ ...prev, width: parseFloat(e.target.value) }))}
                  className="mt-1"
                />
              </div>
              <div>
                <Label>Height (%)</Label>
                <Input
                  type="number"
                  min="1"
                  max="20"
                  value={newItemConfig.height || 3}
                  onChange={(e) => setNewItemConfig(prev => ({ ...prev, height: parseFloat(e.target.value) }))}
                  className="mt-1"
                />
              </div>
            </div>
          </div>
          <DialogFooter className="flex-col sm:flex-row gap-2">
            <Button variant="outline" onClick={() => { setShowAddDialog(false); setAddMode(null); }} className="w-full sm:w-auto">
              Cancel
            </Button>
            <Button onClick={handleAddItem} className="w-full sm:w-auto bg-purple-600 hover:bg-purple-700">
              Add {addMode === 'field' ? 'Field' : 'Signature'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
