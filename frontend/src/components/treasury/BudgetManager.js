/**
 * Budget Manager Component
 * 
 * Manages budget allocations and tracks spending against budgets
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '../ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Progress } from '../ui/progress';
import { toast } from 'sonner';
import { Plus, PieChart, Loader2, Trash2, AlertCircle } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

export default function BudgetManager({ categories, isAdmin }) {
  const [budgets, setBudgets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  
  const [formData, setFormData] = useState({
    category_id: '',
    amount: '',
    period: 'quarterly',
    year: new Date().getFullYear(),
    quarter: Math.ceil((new Date().getMonth() + 1) / 3),
    month: new Date().getMonth() + 1
  });

  const token = localStorage.getItem('token');
  
  const expenseCategories = categories.filter(c => c.type === 'expense');

  useEffect(() => {
    loadBudgets();
  }, []);

  const loadBudgets = async () => {
    try {
      const res = await axios.get(`${API}/treasury/budgets`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setBudgets(res.data || []);
    } catch (err) {
      console.error('Error loading budgets:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!formData.category_id || !formData.amount) {
      toast.error('Please fill in all required fields');
      return;
    }
    
    setSubmitting(true);
    try {
      const data = {
        ...formData,
        amount: parseFloat(formData.amount),
        quarter: formData.period === 'quarterly' ? formData.quarter : null,
        month: formData.period === 'monthly' ? formData.month : null
      };
      
      await axios.post(`${API}/treasury/budgets`, data, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success('Budget created');
      setDialogOpen(false);
      loadBudgets();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create budget');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (budget) => {
    if (!confirm('Delete this budget?')) return;
    
    try {
      await axios.delete(`${API}/treasury/budgets/${budget.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Budget deleted');
      loadBudgets();
    } catch (err) {
      toast.error('Failed to delete budget');
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount || 0);
  };

  const getQuarterName = (quarter) => `Q${quarter}`;
  const getMonthName = (month) => new Date(2000, month - 1).toLocaleString('default', { month: 'short' });

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="w-8 h-8 text-green-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Budget Allocations</h2>
        {isAdmin && (
          <Button onClick={() => setDialogOpen(true)} className="bg-green-600 hover:bg-green-700">
            <Plus className="w-4 h-4 mr-2" />
            Add Budget
          </Button>
        )}
      </div>

      {/* Budget List */}
      {budgets.length === 0 ? (
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="p-8 text-center">
            <PieChart className="w-12 h-12 text-slate-500 mx-auto mb-4" />
            <p className="text-slate-400">No budgets set up yet.</p>
            {isAdmin && (
              <p className="text-slate-500 text-sm mt-2">
                Create budgets to track spending by category.
              </p>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {budgets.map((budget) => {
            const percentUsed = budget.percent_used || 0;
            const isOverBudget = percentUsed > 100;
            const isNearLimit = percentUsed > 80 && percentUsed <= 100;
            
            return (
              <Card key={budget.id} className="bg-slate-800 border-slate-700">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <p className="text-white font-medium">{budget.category_name}</p>
                      <p className="text-slate-400 text-xs">
                        {budget.period === 'yearly' && budget.year}
                        {budget.period === 'quarterly' && `${getQuarterName(budget.quarter)} ${budget.year}`}
                        {budget.period === 'monthly' && `${getMonthName(budget.month)} ${budget.year}`}
                      </p>
                    </div>
                    {isAdmin && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(budget)}
                        className="text-slate-400 hover:text-red-400"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-400">
                        {formatCurrency(budget.spent)} of {formatCurrency(budget.amount)}
                      </span>
                      <span className={`font-medium ${
                        isOverBudget ? 'text-red-400' : isNearLimit ? 'text-yellow-400' : 'text-green-400'
                      }`}>
                        {percentUsed.toFixed(0)}%
                      </span>
                    </div>
                    
                    <Progress 
                      value={Math.min(percentUsed, 100)} 
                      className={`h-2 ${
                        isOverBudget ? 'bg-red-900' : isNearLimit ? 'bg-yellow-900' : 'bg-slate-700'
                      }`}
                    />
                    
                    {isOverBudget && (
                      <div className="flex items-center gap-1 text-red-400 text-xs">
                        <AlertCircle className="w-3 h-3" />
                        Over budget by {formatCurrency(budget.spent - budget.amount)}
                      </div>
                    )}
                    
                    <p className="text-slate-500 text-xs">
                      Remaining: {formatCurrency(Math.max(0, budget.remaining))}
                    </p>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Add Budget Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Add Budget</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div>
              <Label>Category *</Label>
              <Select 
                value={formData.category_id} 
                onValueChange={(v) => setFormData(prev => ({ ...prev, category_id: v }))}
              >
                <SelectTrigger className="bg-slate-800 border-slate-700">
                  <SelectValue placeholder="Select expense category" />
                </SelectTrigger>
                <SelectContent>
                  {expenseCategories.map(cat => (
                    <SelectItem key={cat.id} value={cat.id}>{cat.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label>Budget Amount *</Label>
              <Input
                type="number"
                step="0.01"
                min="0"
                value={formData.amount}
                onChange={(e) => setFormData(prev => ({ ...prev, amount: e.target.value }))}
                className="bg-slate-800 border-slate-700"
                placeholder="0.00"
              />
            </div>
            
            <div>
              <Label>Period *</Label>
              <Select 
                value={formData.period} 
                onValueChange={(v) => setFormData(prev => ({ ...prev, period: v }))}
              >
                <SelectTrigger className="bg-slate-800 border-slate-700">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="monthly">Monthly</SelectItem>
                  <SelectItem value="quarterly">Quarterly</SelectItem>
                  <SelectItem value="yearly">Yearly</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Year</Label>
                <Input
                  type="number"
                  value={formData.year}
                  onChange={(e) => setFormData(prev => ({ ...prev, year: parseInt(e.target.value) }))}
                  className="bg-slate-800 border-slate-700"
                />
              </div>
              
              {formData.period === 'quarterly' && (
                <div>
                  <Label>Quarter</Label>
                  <Select 
                    value={formData.quarter.toString()} 
                    onValueChange={(v) => setFormData(prev => ({ ...prev, quarter: parseInt(v) }))}
                  >
                    <SelectTrigger className="bg-slate-800 border-slate-700">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">Q1 (Jan-Mar)</SelectItem>
                      <SelectItem value="2">Q2 (Apr-Jun)</SelectItem>
                      <SelectItem value="3">Q3 (Jul-Sep)</SelectItem>
                      <SelectItem value="4">Q4 (Oct-Dec)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              )}
              
              {formData.period === 'monthly' && (
                <div>
                  <Label>Month</Label>
                  <Select 
                    value={formData.month.toString()} 
                    onValueChange={(v) => setFormData(prev => ({ ...prev, month: parseInt(v) }))}
                  >
                    <SelectTrigger className="bg-slate-800 border-slate-700">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Array.from({ length: 12 }, (_, i) => (
                        <SelectItem key={i + 1} value={(i + 1).toString()}>
                          {new Date(2000, i).toLocaleString('default', { month: 'long' })}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleSubmit} 
              disabled={submitting}
              className="bg-green-600 hover:bg-green-700"
            >
              {submitting && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Create Budget
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
