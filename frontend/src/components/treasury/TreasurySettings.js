/**
 * Treasury Settings Component
 * 
 * Manage accounts, categories, and view audit logs
 */
import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '../ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { toast } from 'sonner';
import { 
  Plus, Building2, PiggyBank, Banknote, Wallet, 
  Tag, Loader2, Trash2, Edit2, History, RefreshCw,
  ChevronLeft, ChevronRight
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const accountIcons = {
  checking: Building2,
  savings: PiggyBank,
  cash: Banknote,
  other: Wallet
};

export default function TreasurySettings({ accounts, categories, onAccountsChange, onCategoriesChange }) {
  const [activeTab, setActiveTab] = useState('accounts');
  
  // Account dialog
  const [accountDialogOpen, setAccountDialogOpen] = useState(false);
  const [accountForm, setAccountForm] = useState({
    name: '',
    type: 'checking',
    initial_balance: '0',
    description: ''
  });
  const [submittingAccount, setSubmittingAccount] = useState(false);
  
  // Category dialog
  const [categoryDialogOpen, setCategoryDialogOpen] = useState(false);
  const [categoryForm, setCategoryForm] = useState({
    name: '',
    type: 'expense',
    description: ''
  });
  const [submittingCategory, setSubmittingCategory] = useState(false);
  
  // Audit logs
  const [auditLogs, setAuditLogs] = useState([]);
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditTotal, setAuditTotal] = useState(0);
  const [auditOffset, setAuditOffset] = useState(0);
  const [auditFilter, setAuditFilter] = useState('');
  const auditLimit = 20;

  const token = localStorage.getItem('token');
  
  // Fetch audit logs
  const fetchAuditLogs = useCallback(async () => {
    setAuditLoading(true);
    try {
      const params = new URLSearchParams({
        limit: auditLimit,
        offset: auditOffset
      });
      if (auditFilter) {
        params.append('entity_type', auditFilter);
      }
      
      const res = await axios.get(`${API}/treasury/audit?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAuditLogs(res.data.logs || []);
      setAuditTotal(res.data.total || 0);
    } catch (err) {
      console.error('Failed to fetch audit logs:', err);
    } finally {
      setAuditLoading(false);
    }
  }, [token, auditOffset, auditFilter]);
  
  // Load audit logs when tab changes
  useEffect(() => {
    if (activeTab === 'audit') {
      fetchAuditLogs();
    }
  }, [activeTab, fetchAuditLogs]);

  // Account handlers
  const handleCreateAccount = async () => {
    if (!accountForm.name) {
      toast.error('Please enter an account name');
      return;
    }
    
    setSubmittingAccount(true);
    try {
      await axios.post(`${API}/treasury/accounts`, {
        ...accountForm,
        initial_balance: parseFloat(accountForm.initial_balance) || 0
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success('Account created');
      setAccountDialogOpen(false);
      setAccountForm({ name: '', type: 'checking', initial_balance: '0', description: '' });
      onAccountsChange?.();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create account');
    } finally {
      setSubmittingAccount(false);
    }
  };

  const handleDeleteAccount = async (account) => {
    if (!confirm(`Delete account "${account.name}"? This cannot be undone.`)) return;
    
    try {
      await axios.put(`${API}/treasury/accounts/${account.id}`, {
        is_active: false
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Account deactivated');
      onAccountsChange?.();
    } catch (err) {
      toast.error('Failed to delete account');
    }
  };

  // Category handlers
  const handleCreateCategory = async () => {
    if (!categoryForm.name) {
      toast.error('Please enter a category name');
      return;
    }
    
    setSubmittingCategory(true);
    try {
      await axios.post(`${API}/treasury/categories`, categoryForm, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success('Category created');
      setCategoryDialogOpen(false);
      setCategoryForm({ name: '', type: 'expense', description: '' });
      onCategoriesChange?.();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create category');
    } finally {
      setSubmittingCategory(false);
    }
  };

  const handleDeleteCategory = async (category) => {
    if (category.is_default) {
      toast.error('Cannot delete default categories');
      return;
    }
    
    if (!confirm(`Delete category "${category.name}"?`)) return;
    
    try {
      await axios.delete(`${API}/treasury/categories/${category.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Category deleted');
      onCategoriesChange?.();
    } catch (err) {
      toast.error('Failed to delete category');
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount || 0);
  };

  const incomeCategories = categories.filter(c => c.type === 'income');
  const expenseCategories = categories.filter(c => c.type === 'expense');
  
  // Audit log helpers
  const formatAuditDate = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };
  
  const getActionColor = (action) => {
    if (action?.includes('created')) return 'text-green-400';
    if (action?.includes('deleted')) return 'text-red-400';
    if (action?.includes('updated') || action?.includes('adjusted')) return 'text-amber-400';
    if (action?.includes('transfer')) return 'text-blue-400';
    return 'text-slate-400';
  };

  return (
    <div className="space-y-4 sm:space-y-6">
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-slate-800 w-full sm:w-auto flex overflow-x-auto">
          <TabsTrigger value="accounts" className="flex-shrink-0 text-xs sm:text-sm">Accounts</TabsTrigger>
          <TabsTrigger value="categories" className="flex-shrink-0 text-xs sm:text-sm">Categories</TabsTrigger>
          <TabsTrigger value="audit" className="flex items-center gap-1 flex-shrink-0 text-xs sm:text-sm">
            <History className="w-3 h-3" />
            <span className="hidden sm:inline">Audit</span> Log
          </TabsTrigger>
        </TabsList>

        {/* Accounts Tab */}
        <TabsContent value="accounts" className="space-y-3 sm:space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base sm:text-lg font-medium text-white">Treasury Accounts</h3>
            <Button onClick={() => setAccountDialogOpen(true)} className="bg-green-600 hover:bg-green-700" size="sm">
              <Plus className="w-4 h-4 sm:mr-2" />
              <span className="hidden sm:inline">Add Account</span>
            </Button>
          </div>

          {accounts.length === 0 ? (
            <Card className="bg-slate-800 border-slate-700">
              <CardContent className="p-6 sm:p-8 text-center">
                <Wallet className="w-10 h-10 sm:w-12 sm:h-12 text-slate-500 mx-auto mb-3 sm:mb-4" />
                <p className="text-slate-400 text-sm sm:text-base">No accounts yet. Create your first account to get started.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-3 sm:gap-4">
              {accounts.map((account) => {
                const IconComponent = accountIcons[account.type] || Wallet;
                return (
                  <Card key={account.id} className="bg-slate-800 border-slate-700">
                    <CardContent className="p-3 sm:p-4">
                      {/* Mobile: Stacked layout */}
                      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-0">
                        <div className="flex items-center gap-2 sm:gap-3">
                          <div className={`w-8 h-8 sm:w-10 sm:h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
                            account.type === 'checking' ? 'bg-blue-600/20' :
                            account.type === 'savings' ? 'bg-purple-600/20' :
                            account.type === 'cash' ? 'bg-green-600/20' : 'bg-slate-600/20'
                          }`}>
                            <IconComponent className={`w-4 h-4 sm:w-5 sm:h-5 ${
                              account.type === 'checking' ? 'text-blue-400' :
                              account.type === 'savings' ? 'text-purple-400' :
                              account.type === 'cash' ? 'text-green-400' : 'text-slate-400'
                            }`} />
                          </div>
                          <div className="min-w-0">
                            <p className="text-white font-medium text-sm sm:text-base truncate">{account.name}</p>
                            <p className="text-slate-500 text-xs capitalize">{account.type}</p>
                          </div>
                        </div>
                        <div className="flex items-center justify-between sm:justify-end gap-3 sm:gap-4 pl-10 sm:pl-0">
                          <p className={`text-base sm:text-lg font-bold ${
                            account.balance >= 0 ? 'text-green-400' : 'text-red-400'
                          }`}>
                            {formatCurrency(account.balance)}
                          </p>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteAccount(account)}
                            className="text-slate-400 hover:text-red-400 h-8 w-8 p-0"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>

        {/* Categories Tab */}
        <TabsContent value="categories" className="space-y-3 sm:space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base sm:text-lg font-medium text-white">Transaction Categories</h3>
            <Button onClick={() => setCategoryDialogOpen(true)} className="bg-green-600 hover:bg-green-700" size="sm">
              <Plus className="w-4 h-4 sm:mr-2" />
              <span className="hidden sm:inline">Add Category</span>
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
            {/* Income Categories */}
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader className="pb-2 p-3 sm:p-6 sm:pb-2">
                <CardTitle className="text-green-400 text-sm sm:text-base flex items-center gap-2">
                  <Tag className="w-4 h-4" />
                  Income Categories
                </CardTitle>
              </CardHeader>
              <CardContent className="p-3 sm:p-6 pt-0">
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {incomeCategories.map((cat) => (
                    <div key={cat.id} className="flex items-center justify-between py-2 border-b border-slate-700 last:border-0">
                      <span className="text-slate-300 text-xs sm:text-sm">{cat.name}</span>
                      {!cat.is_default && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteCategory(cat)}
                          className="text-slate-400 hover:text-red-400 h-6 w-6 p-0"
                        >
                          <Trash2 className="w-3 h-3" />
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Expense Categories */}
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader className="pb-2 p-3 sm:p-6 sm:pb-2">
                <CardTitle className="text-red-400 text-sm sm:text-base flex items-center gap-2">
                  <Tag className="w-4 h-4" />
                  Expense Categories
                </CardTitle>
              </CardHeader>
              <CardContent className="p-3 sm:p-6 pt-0">
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {expenseCategories.map((cat) => (
                    <div key={cat.id} className="flex items-center justify-between py-2 border-b border-slate-700 last:border-0">
                      <span className="text-slate-300 text-xs sm:text-sm">{cat.name}</span>
                      {!cat.is_default && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteCategory(cat)}
                          className="text-slate-400 hover:text-red-400 h-6 w-6 p-0"
                        >
                          <Trash2 className="w-3 h-3" />
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Audit Log Tab */}
        <TabsContent value="audit" className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <h3 className="text-base sm:text-lg font-medium text-white flex items-center gap-2">
              <History className="w-4 h-4 sm:w-5 sm:h-5 text-slate-400" />
              Activity History
            </h3>
            <div className="flex items-center gap-2">
              <Select value={auditFilter || 'all'} onValueChange={(v) => { setAuditFilter(v === 'all' ? '' : v); setAuditOffset(0); }}>
                <SelectTrigger className="bg-slate-800 border-slate-700 w-28 sm:w-36 text-xs sm:text-sm">
                  <SelectValue placeholder="All Types" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="account">Accounts</SelectItem>
                  <SelectItem value="transaction">Transactions</SelectItem>
                  <SelectItem value="category">Categories</SelectItem>
                </SelectContent>
              </Select>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={fetchAuditLogs}
                disabled={auditLoading}
                className="h-9 w-9 p-0"
              >
                <RefreshCw className={`w-4 h-4 ${auditLoading ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </div>

          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-0">
              {auditLoading && auditLogs.length === 0 ? (
                <div className="p-6 sm:p-8 text-center">
                  <Loader2 className="w-8 h-8 text-slate-500 mx-auto animate-spin" />
                  <p className="text-slate-400 mt-2 text-sm">Loading audit logs...</p>
                </div>
              ) : auditLogs.length === 0 ? (
                <div className="p-6 sm:p-8 text-center">
                  <History className="w-10 h-10 sm:w-12 sm:h-12 text-slate-500 mx-auto mb-3 sm:mb-4" />
                  <p className="text-slate-400 text-sm sm:text-base">No activity recorded yet.</p>
                  <p className="text-slate-500 text-xs sm:text-sm">Actions will be logged as you manage accounts and transactions.</p>
                </div>
              ) : (
                <div className="divide-y divide-slate-700">
                  {auditLogs.map((log) => (
                    <div key={log.id} className="p-3 sm:p-4 hover:bg-slate-700/50 transition-colors">
                      {/* Mobile Layout */}
                      <div className="sm:hidden">
                        <div className="flex items-start justify-between mb-1">
                          <span className={`font-medium text-sm ${getActionColor(log.action)}`}>
                            {log.action_display}
                          </span>
                          <span className="text-slate-500 text-xs px-1.5 py-0.5 bg-slate-700 rounded">
                            {log.entity_type}
                          </span>
                        </div>
                        <p className="text-white text-sm truncate">{log.entity_name}</p>
                        <div className="flex items-center justify-between mt-2 text-xs text-slate-500">
                          <span>{formatAuditDate(log.timestamp)}</span>
                          <span>by {log.username}</span>
                        </div>
                        {log.details && (
                          <div className="mt-2 text-xs text-slate-500 flex flex-wrap gap-2">
                            {log.details.amount && <span>Amount: ${log.details.amount}</span>}
                            {log.details.type && <span>Type: {log.details.type}</span>}
                          </div>
                        )}
                      </div>
                      
                      {/* Desktop Layout */}
                      <div className="hidden sm:flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className={`font-medium ${getActionColor(log.action)}`}>
                              {log.action_display}
                            </span>
                            <span className="text-slate-500 text-xs px-2 py-0.5 bg-slate-700 rounded">
                              {log.entity_type}
                            </span>
                          </div>
                          <p className="text-white text-sm mt-1">{log.entity_name}</p>
                          {log.details && (
                            <div className="mt-2 text-xs text-slate-500">
                              {log.details.amount && <span className="mr-3">Amount: ${log.details.amount}</span>}
                              {log.details.reason && <span className="mr-3">Reason: {log.details.reason}</span>}
                              {log.details.type && <span className="mr-3">Type: {log.details.type}</span>}
                            </div>
                          )}
                          {(log.old_values || log.new_values) && (
                            <div className="mt-2 text-xs">
                              {log.old_values && Object.keys(log.old_values).length > 0 && (
                                <div className="text-red-400/70">
                                  Old: {Object.entries(log.old_values).map(([k, v]) => `${k}: ${v}`).join(', ')}
                                </div>
                              )}
                              {log.new_values && Object.keys(log.new_values).length > 0 && (
                                <div className="text-green-400/70">
                                  New: {Object.entries(log.new_values).map(([k, v]) => `${k}: ${v}`).join(', ')}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                        <div className="text-right text-xs text-slate-500 whitespace-nowrap ml-4">
                          <div>{formatAuditDate(log.timestamp)}</div>
                          <div className="mt-1">by {log.username}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              
              {/* Pagination */}
              {auditTotal > auditLimit && (
                <div className="flex items-center justify-between p-4 border-t border-slate-700">
                  <p className="text-sm text-slate-500">
                    Showing {auditOffset + 1} - {Math.min(auditOffset + auditLimit, auditTotal)} of {auditTotal}
                  </p>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setAuditOffset(Math.max(0, auditOffset - auditLimit))}
                      disabled={auditOffset === 0}
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setAuditOffset(auditOffset + auditLimit)}
                      disabled={auditOffset + auditLimit >= auditTotal}
                    >
                      <ChevronRight className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Add Account Dialog */}
      <Dialog open={accountDialogOpen} onOpenChange={setAccountDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Add Account</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div>
              <Label>Account Name *</Label>
              <Input
                value={accountForm.name}
                onChange={(e) => setAccountForm(prev => ({ ...prev, name: e.target.value }))}
                className="bg-slate-800 border-slate-700"
                placeholder="e.g., Main Checking"
              />
            </div>
            
            <div>
              <Label>Account Type</Label>
              <Select 
                value={accountForm.type} 
                onValueChange={(v) => setAccountForm(prev => ({ ...prev, type: v }))}
              >
                <SelectTrigger className="bg-slate-800 border-slate-700">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="checking">Checking</SelectItem>
                  <SelectItem value="savings">Savings</SelectItem>
                  <SelectItem value="cash">Cash</SelectItem>
                  <SelectItem value="other">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label>Initial Balance</Label>
              <Input
                type="number"
                step="0.01"
                value={accountForm.initial_balance}
                onChange={(e) => setAccountForm(prev => ({ ...prev, initial_balance: e.target.value }))}
                className="bg-slate-800 border-slate-700"
                placeholder="0.00"
              />
            </div>
            
            <div>
              <Label>Description</Label>
              <Input
                value={accountForm.description}
                onChange={(e) => setAccountForm(prev => ({ ...prev, description: e.target.value }))}
                className="bg-slate-800 border-slate-700"
                placeholder="Optional description"
              />
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setAccountDialogOpen(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleCreateAccount} 
              disabled={submittingAccount}
              className="bg-green-600 hover:bg-green-700"
            >
              {submittingAccount && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Create Account
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Category Dialog */}
      <Dialog open={categoryDialogOpen} onOpenChange={setCategoryDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Add Category</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div>
              <Label>Category Name *</Label>
              <Input
                value={categoryForm.name}
                onChange={(e) => setCategoryForm(prev => ({ ...prev, name: e.target.value }))}
                className="bg-slate-800 border-slate-700"
                placeholder="e.g., Membership Fees"
              />
            </div>
            
            <div>
              <Label>Category Type</Label>
              <Select 
                value={categoryForm.type} 
                onValueChange={(v) => setCategoryForm(prev => ({ ...prev, type: v }))}
              >
                <SelectTrigger className="bg-slate-800 border-slate-700">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="income">Income</SelectItem>
                  <SelectItem value="expense">Expense</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label>Description</Label>
              <Input
                value={categoryForm.description}
                onChange={(e) => setCategoryForm(prev => ({ ...prev, description: e.target.value }))}
                className="bg-slate-800 border-slate-700"
                placeholder="Optional description"
              />
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setCategoryDialogOpen(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleCreateCategory} 
              disabled={submittingCategory}
              className="bg-green-600 hover:bg-green-700"
            >
              {submittingCategory && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Create Category
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
