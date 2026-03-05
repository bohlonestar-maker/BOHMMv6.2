/**
 * Treasury Settings Component
 * 
 * Manage accounts and categories
 */
import React, { useState } from 'react';
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
  Tag, Loader2, Trash2, Edit2
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

  const token = localStorage.getItem('token');

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

  return (
    <div className="space-y-6">
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-slate-800">
          <TabsTrigger value="accounts">Accounts</TabsTrigger>
          <TabsTrigger value="categories">Categories</TabsTrigger>
        </TabsList>

        {/* Accounts Tab */}
        <TabsContent value="accounts" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-white">Treasury Accounts</h3>
            <Button onClick={() => setAccountDialogOpen(true)} className="bg-green-600 hover:bg-green-700">
              <Plus className="w-4 h-4 mr-2" />
              Add Account
            </Button>
          </div>

          {accounts.length === 0 ? (
            <Card className="bg-slate-800 border-slate-700">
              <CardContent className="p-8 text-center">
                <Wallet className="w-12 h-12 text-slate-500 mx-auto mb-4" />
                <p className="text-slate-400">No accounts yet. Create your first account to get started.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {accounts.map((account) => {
                const IconComponent = accountIcons[account.type] || Wallet;
                return (
                  <Card key={account.id} className="bg-slate-800 border-slate-700">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                            account.type === 'checking' ? 'bg-blue-600/20' :
                            account.type === 'savings' ? 'bg-purple-600/20' :
                            account.type === 'cash' ? 'bg-green-600/20' : 'bg-slate-600/20'
                          }`}>
                            <IconComponent className={`w-5 h-5 ${
                              account.type === 'checking' ? 'text-blue-400' :
                              account.type === 'savings' ? 'text-purple-400' :
                              account.type === 'cash' ? 'text-green-400' : 'text-slate-400'
                            }`} />
                          </div>
                          <div>
                            <p className="text-white font-medium">{account.name}</p>
                            <p className="text-slate-500 text-xs capitalize">{account.type}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <p className={`text-lg font-bold ${
                            account.balance >= 0 ? 'text-green-400' : 'text-red-400'
                          }`}>
                            {formatCurrency(account.balance)}
                          </p>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteAccount(account)}
                            className="text-slate-400 hover:text-red-400"
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
        <TabsContent value="categories" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-white">Transaction Categories</h3>
            <Button onClick={() => setCategoryDialogOpen(true)} className="bg-green-600 hover:bg-green-700">
              <Plus className="w-4 h-4 mr-2" />
              Add Category
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Income Categories */}
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader className="pb-2">
                <CardTitle className="text-green-400 text-base flex items-center gap-2">
                  <Tag className="w-4 h-4" />
                  Income Categories
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {incomeCategories.map((cat) => (
                    <div key={cat.id} className="flex items-center justify-between py-2 border-b border-slate-700 last:border-0">
                      <span className="text-slate-300 text-sm">{cat.name}</span>
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
              <CardHeader className="pb-2">
                <CardTitle className="text-red-400 text-base flex items-center gap-2">
                  <Tag className="w-4 h-4" />
                  Expense Categories
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {expenseCategories.map((cat) => (
                    <div key={cat.id} className="flex items-center justify-between py-2 border-b border-slate-700 last:border-0">
                      <span className="text-slate-300 text-sm">{cat.name}</span>
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
