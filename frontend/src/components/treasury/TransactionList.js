/**
 * Transaction List Component
 * 
 * Lists income/expense transactions with filtering and CRUD operations
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '../ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { toast } from 'sonner';
import { 
  Plus, Search, Filter, TrendingUp, TrendingDown, 
  Edit2, Trash2, Receipt, Loader2, Upload, Eye
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

export default function TransactionList({ accounts, categories, canManage, onTransactionChange }) {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  
  // Filters
  const [filterType, setFilterType] = useState('all');
  const [filterAccount, setFilterAccount] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  
  // Dialog state
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingTransaction, setEditingTransaction] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  
  // Receipt state
  const [receiptDialogOpen, setReceiptDialogOpen] = useState(false);
  const [viewingReceipt, setViewingReceipt] = useState(null);
  const [uploadingReceipt, setUploadingReceipt] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  
  // Form state
  const [formData, setFormData] = useState({
    type: 'expense',
    account_id: '',
    category_id: '',
    amount: '',
    description: '',
    date: new Date().toISOString().split('T')[0],
    vendor_payee: '',
    reference_number: '',
    notes: ''
  });

  const token = localStorage.getItem('token');

  useEffect(() => {
    loadTransactions();
  }, [filterType, filterAccount]);

  const loadTransactions = async () => {
    setLoading(true);
    try {
      const params = {};
      if (filterType !== 'all') params.type = filterType;
      if (filterAccount !== 'all') params.account_id = filterAccount;
      
      const res = await axios.get(`${API}/treasury/transactions`, {
        params,
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setTransactions(res.data.transactions || []);
      setTotal(res.data.total || 0);
    } catch (err) {
      console.error('Error loading transactions:', err);
      toast.error('Failed to load transactions');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (transaction = null) => {
    if (transaction) {
      setEditingTransaction(transaction);
      setFormData({
        type: transaction.type,
        account_id: transaction.account_id,
        category_id: transaction.category_id,
        amount: transaction.amount.toString(),
        description: transaction.description,
        date: transaction.date,
        vendor_payee: transaction.vendor_payee || '',
        reference_number: transaction.reference_number || '',
        notes: transaction.notes || ''
      });
    } else {
      setEditingTransaction(null);
      setFormData({
        type: 'expense',
        account_id: accounts[0]?.id || '',
        category_id: '',
        amount: '',
        description: '',
        date: new Date().toISOString().split('T')[0],
        vendor_payee: '',
        reference_number: '',
        notes: ''
      });
    }
    setDialogOpen(true);
  };

  const handleSubmit = async () => {
    if (!formData.account_id || !formData.category_id || !formData.amount || !formData.description) {
      toast.error('Please fill in all required fields');
      return;
    }
    
    setSubmitting(true);
    try {
      const data = {
        ...formData,
        amount: parseFloat(formData.amount)
      };
      
      if (editingTransaction) {
        await axios.put(`${API}/treasury/transactions/${editingTransaction.id}`, data, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Transaction updated');
      } else {
        await axios.post(`${API}/treasury/transactions`, data, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Transaction created');
      }
      
      setDialogOpen(false);
      loadTransactions();
      onTransactionChange?.();
    } catch (err) {
      console.error('Error saving transaction:', err);
      toast.error(err.response?.data?.detail || 'Failed to save transaction');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (transaction) => {
    if (!confirm(`Delete this ${transaction.type}?`)) return;
    
    try {
      await axios.delete(`${API}/treasury/transactions/${transaction.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Transaction deleted');
      loadTransactions();
      onTransactionChange?.();
    } catch (err) {
      toast.error('Failed to delete transaction');
    }
  };

  const handleUploadReceipt = async (transactionId) => {
    if (!selectedFile) {
      toast.error('Please select a file');
      return;
    }
    
    setUploadingReceipt(true);
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      
      await axios.post(`${API}/treasury/transactions/${transactionId}/receipt`, formData, {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });
      
      toast.success('Receipt uploaded successfully');
      setSelectedFile(null);
      setReceiptDialogOpen(false);
      loadTransactions();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to upload receipt');
    } finally {
      setUploadingReceipt(false);
    }
  };

  const handleViewReceipt = (transaction) => {
    // Open receipt in new tab
    window.open(`${API}/treasury/transactions/${transaction.id}/receipt`, '_blank');
  };

  const openReceiptUpload = (transaction) => {
    setViewingReceipt(transaction);
    setSelectedFile(null);
    setReceiptDialogOpen(true);
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount || 0);
  };

  const filteredCategories = categories.filter(c => c.type === formData.type);

  const filteredTransactions = transactions.filter(t => {
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      return t.description?.toLowerCase().includes(search) ||
             t.vendor_payee?.toLowerCase().includes(search) ||
             t.category_name?.toLowerCase().includes(search);
    }
    return true;
  });

  return (
    <div className="space-y-4">
      {/* Header with filters */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex flex-wrap gap-2">
          <Select value={filterType} onValueChange={setFilterType}>
            <SelectTrigger className="w-32 bg-slate-800 border-slate-700">
              <SelectValue placeholder="Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem value="income">Income</SelectItem>
              <SelectItem value="expense">Expenses</SelectItem>
            </SelectContent>
          </Select>
          
          <Select value={filterAccount} onValueChange={setFilterAccount}>
            <SelectTrigger className="w-40 bg-slate-800 border-slate-700">
              <SelectValue placeholder="Account" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Accounts</SelectItem>
              {accounts.map(acc => (
                <SelectItem key={acc.id} value={acc.id}>{acc.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              placeholder="Search..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 w-48 bg-slate-800 border-slate-700"
            />
          </div>
        </div>
        
        {canManage && (
          <Button onClick={() => handleOpenDialog()} className="bg-green-600 hover:bg-green-700">
            <Plus className="w-4 h-4 mr-2" />
            Add Transaction
          </Button>
        )}
      </div>

      {/* Transaction List */}
      <Card className="bg-slate-800 border-slate-700">
        <CardContent className="p-0">
          {loading ? (
            <div className="p-8 text-center">
              <Loader2 className="w-8 h-8 text-green-400 animate-spin mx-auto" />
            </div>
          ) : filteredTransactions.length === 0 ? (
            <div className="p-8 text-center">
              <Receipt className="w-12 h-12 text-slate-500 mx-auto mb-4" />
              <p className="text-slate-400">No transactions found</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-700">
              {filteredTransactions.map((t) => (
                <div key={t.id} className="p-4 hover:bg-slate-700/50 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                        t.type === 'income' ? 'bg-green-600/20' : 'bg-red-600/20'
                      }`}>
                        {t.type === 'income' ? (
                          <TrendingUp className="w-5 h-5 text-green-400" />
                        ) : (
                          <TrendingDown className="w-5 h-5 text-red-400" />
                        )}
                      </div>
                      <div>
                        <p className="text-white font-medium">{t.description}</p>
                        <div className="flex items-center gap-2 text-xs text-slate-400">
                          <span>{t.category_name}</span>
                          <span>•</span>
                          <span>{t.account_name}</span>
                          <span>•</span>
                          <span>{new Date(t.date).toLocaleDateString()}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <p className={`text-lg font-bold ${
                        t.type === 'income' ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {t.type === 'income' ? '+' : '-'}{formatCurrency(t.amount)}
                      </p>
                      <div className="flex gap-1">
                        {/* Receipt buttons */}
                        {t.receipt_filename ? (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleViewReceipt(t)}
                            className="text-green-400 hover:text-green-300"
                            title="View Receipt"
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                        ) : canManage ? (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openReceiptUpload(t)}
                            className="text-slate-400 hover:text-purple-400"
                            title="Upload Receipt"
                          >
                            <Upload className="w-4 h-4" />
                          </Button>
                        ) : null}
                        
                        {canManage && (
                          <>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleOpenDialog(t)}
                              className="text-slate-400 hover:text-white"
                            >
                              <Edit2 className="w-4 h-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDelete(t)}
                              className="text-slate-400 hover:text-red-400"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>
              {editingTransaction ? 'Edit Transaction' : 'Add Transaction'}
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            {/* Type Selection */}
            <div className="grid grid-cols-2 gap-2">
              <Button
                type="button"
                variant={formData.type === 'income' ? 'default' : 'outline'}
                onClick={() => setFormData(prev => ({ ...prev, type: 'income', category_id: '' }))}
                className={formData.type === 'income' ? 'bg-green-600' : ''}
              >
                <TrendingUp className="w-4 h-4 mr-2" />
                Income
              </Button>
              <Button
                type="button"
                variant={formData.type === 'expense' ? 'default' : 'outline'}
                onClick={() => setFormData(prev => ({ ...prev, type: 'expense', category_id: '' }))}
                className={formData.type === 'expense' ? 'bg-red-600' : ''}
              >
                <TrendingDown className="w-4 h-4 mr-2" />
                Expense
              </Button>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Account *</Label>
                <Select 
                  value={formData.account_id} 
                  onValueChange={(v) => setFormData(prev => ({ ...prev, account_id: v }))}
                >
                  <SelectTrigger className="bg-slate-800 border-slate-700">
                    <SelectValue placeholder="Select account" />
                  </SelectTrigger>
                  <SelectContent>
                    {accounts.map(acc => (
                      <SelectItem key={acc.id} value={acc.id}>{acc.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <Label>Category *</Label>
                <Select 
                  value={formData.category_id} 
                  onValueChange={(v) => setFormData(prev => ({ ...prev, category_id: v }))}
                >
                  <SelectTrigger className="bg-slate-800 border-slate-700">
                    <SelectValue placeholder="Select category" />
                  </SelectTrigger>
                  <SelectContent>
                    {filteredCategories.map(cat => (
                      <SelectItem key={cat.id} value={cat.id}>{cat.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Amount *</Label>
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
                <Label>Date *</Label>
                <Input
                  type="date"
                  value={formData.date}
                  onChange={(e) => setFormData(prev => ({ ...prev, date: e.target.value }))}
                  className="bg-slate-800 border-slate-700"
                />
              </div>
            </div>
            
            <div>
              <Label>Description *</Label>
              <Input
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                className="bg-slate-800 border-slate-700"
                placeholder="What was this for?"
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Vendor/Payee</Label>
                <Input
                  value={formData.vendor_payee}
                  onChange={(e) => setFormData(prev => ({ ...prev, vendor_payee: e.target.value }))}
                  className="bg-slate-800 border-slate-700"
                  placeholder="Company or person"
                />
              </div>
              
              <div>
                <Label>Reference #</Label>
                <Input
                  value={formData.reference_number}
                  onChange={(e) => setFormData(prev => ({ ...prev, reference_number: e.target.value }))}
                  className="bg-slate-800 border-slate-700"
                  placeholder="Check #, invoice #"
                />
              </div>
            </div>
            
            <div>
              <Label>Notes</Label>
              <Textarea
                value={formData.notes}
                onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
                className="bg-slate-800 border-slate-700"
                placeholder="Additional details..."
              />
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleSubmit} 
              disabled={submitting}
              className={formData.type === 'income' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'}
            >
              {submitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
              {editingTransaction ? 'Update' : 'Add'} {formData.type === 'income' ? 'Income' : 'Expense'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Receipt Upload Dialog */}
      <Dialog open={receiptDialogOpen} onOpenChange={setReceiptDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Receipt className="w-5 h-5 text-purple-400" />
              Upload Receipt
            </DialogTitle>
            <DialogDescription>
              {viewingReceipt?.description} - {formatCurrency(viewingReceipt?.amount)}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="border-2 border-dashed border-slate-600 rounded-lg p-6 text-center">
              <input
                type="file"
                id="receipt-upload"
                accept="image/*,.pdf"
                onChange={(e) => setSelectedFile(e.target.files[0])}
                className="hidden"
              />
              <label 
                htmlFor="receipt-upload" 
                className="cursor-pointer block"
              >
                {selectedFile ? (
                  <div className="space-y-2">
                    <Receipt className="w-10 h-10 text-green-400 mx-auto" />
                    <p className="text-white font-medium">{selectedFile.name}</p>
                    <p className="text-slate-400 text-sm">
                      {(selectedFile.size / 1024).toFixed(1)} KB
                    </p>
                    <p className="text-purple-400 text-sm">Click to change</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <Upload className="w-10 h-10 text-slate-400 mx-auto" />
                    <p className="text-slate-300">Click to select file</p>
                    <p className="text-slate-500 text-sm">
                      Images or PDF (max 5MB)
                    </p>
                  </div>
                )}
              </label>
            </div>
            
            {viewingReceipt?.receipt_filename && (
              <div className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
                <div className="flex items-center gap-2">
                  <Eye className="w-4 h-4 text-green-400" />
                  <span className="text-slate-300 text-sm">Current: {viewingReceipt.receipt_filename}</span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleViewReceipt(viewingReceipt)}
                  className="text-green-400 hover:text-green-300"
                >
                  View
                </Button>
              </div>
            )}
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setReceiptDialogOpen(false)}>
              Cancel
            </Button>
            <Button 
              onClick={() => handleUploadReceipt(viewingReceipt?.id)}
              disabled={uploadingReceipt || !selectedFile}
              className="bg-purple-600 hover:bg-purple-700"
            >
              {uploadingReceipt ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Upload className="w-4 h-4 mr-2" />}
              Upload Receipt
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
