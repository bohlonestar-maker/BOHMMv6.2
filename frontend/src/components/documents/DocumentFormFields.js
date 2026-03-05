/**
 * DocumentFormFields - Renders fillable form fields for document signing
 * 
 * Supports: text, date, textarea, checkbox field types
 * Handles mutually exclusive Approved/Denied checkboxes
 */
import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Checkbox } from '../ui/checkbox';
import { Edit } from 'lucide-react';

export default function DocumentFormFields({ fieldPlacements = [], formFields, setFormFields }) {
  if (!fieldPlacements.length) return null;

  const handleCheckboxChange = (field, checked) => {
    const fieldId = field.id.toLowerCase();
    const isApprovedField = fieldId.includes('approved');
    const isDeniedField = fieldId.includes('denied');
    
    // Handle mutually exclusive Approved/Denied checkboxes
    if (checked && (isApprovedField || isDeniedField)) {
      const rowMatch = fieldId.match(/(\d+)$/);
      if (rowMatch) {
        const rowNum = rowMatch[1];
        const oppositeType = isApprovedField ? 'denied' : 'approved';
        
        // Find opposite checkbox for same row
        const oppositeFieldId = Object.keys(formFields).find(key => 
          key.toLowerCase().includes(oppositeType) && key.includes(rowNum)
        ) || fieldPlacements.find(f => 
          f.id.toLowerCase().includes(oppositeType) && f.id.includes(rowNum)
        )?.id;
        
        if (oppositeFieldId) {
          setFormFields(prev => ({ 
            ...prev, 
            [field.id]: 'true',
            [oppositeFieldId]: '' 
          }));
          return;
        }
      }
    }
    
    setFormFields(prev => ({ ...prev, [field.id]: checked ? 'true' : '' }));
  };

  const renderField = (field) => {
    switch (field.field_type) {
      case 'textarea':
        return (
          <Textarea
            value={formFields[field.id] || ''}
            onChange={(e) => setFormFields(prev => ({ ...prev, [field.id]: e.target.value }))}
            placeholder={field.placeholder || `Enter ${field.label.toLowerCase()}`}
            className="bg-slate-700 border-slate-600 text-white min-h-[100px]"
            data-testid={`field-${field.id}`}
          />
        );
      
      case 'date':
        return (
          <Input
            type="date"
            value={formFields[field.id] || ''}
            onChange={(e) => setFormFields(prev => ({ ...prev, [field.id]: e.target.value }))}
            className="bg-slate-700 border-slate-600 text-white"
            data-testid={`field-${field.id}`}
          />
        );
      
      case 'checkbox':
        return (
          <div className="flex items-center gap-2">
            <Checkbox
              checked={formFields[field.id] === 'true'}
              onCheckedChange={(checked) => handleCheckboxChange(field, checked)}
              data-testid={`field-${field.id}`}
            />
            <span className="text-slate-400 text-sm">{field.placeholder || field.label}</span>
          </div>
        );
      
      default:
        return (
          <Input
            type="text"
            value={formFields[field.id] || ''}
            onChange={(e) => setFormFields(prev => ({ ...prev, [field.id]: e.target.value }))}
            placeholder={field.placeholder || `Enter ${field.label.toLowerCase()}`}
            className="bg-slate-700 border-slate-600 text-white"
            data-testid={`field-${field.id}`}
          />
        );
    }
  };

  return (
    <Card className="bg-slate-800 border-slate-700 mb-4 sm:mb-6">
      <CardHeader className="p-4 sm:p-6 pb-2 sm:pb-4">
        <CardTitle className="text-white text-base sm:text-lg">
          <Edit className="w-4 h-4 inline mr-2 text-purple-400" />
          Form Fields
        </CardTitle>
        <CardDescription className="text-xs sm:text-sm">
          Please fill in the required information
        </CardDescription>
      </CardHeader>
      <CardContent className="p-4 sm:p-6 pt-0">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {fieldPlacements.map((field) => (
            <div key={field.id} className={field.field_type === 'textarea' ? 'md:col-span-2' : ''}>
              <Label className="text-slate-300 text-sm mb-1 block">
                {field.label}
                {field.required && <span className="text-red-400 ml-1">*</span>}
              </Label>
              {renderField(field)}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
