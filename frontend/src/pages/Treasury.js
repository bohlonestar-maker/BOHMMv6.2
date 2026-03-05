/**
 * Treasury Page - Main financial management interface
 * 
 * Modular architecture with tab-based navigation:
 * - Overview: Account balances and recent activity
 * - Transactions: Income/expense tracking
 * - Budgets: Budget management
 * - Reports: Financial reports
 * - Settings: Categories and accounts
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';
import { 
  DollarSign, TrendingUp, TrendingDown, Wallet, 
  ArrowLeft, PieChart, Settings, FileText, Receipt,
  Loader2
} from 'lucide-react';

// Treasury components
import TreasuryOverview from '../components/treasury/TreasuryOverview';
import TransactionList from '../components/treasury/TransactionList';
import BudgetManager from '../components/treasury/BudgetManager';
import ReportsView from '../components/treasury/ReportsView';
import TreasurySettings from '../components/treasury/TreasurySettings';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

export default function Treasury() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [hasPermission, setHasPermission] = useState(false);
  const [permissionLevel, setPermissionLevel] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  
  // Shared state
  const [accounts, setAccounts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [totalBalance, setTotalBalance] = useState(0);

  const token = localStorage.getItem('token');

  useEffect(() => {
    checkPermissionAndLoad();
  }, []);

  const checkPermissionAndLoad = async () => {
    try {
      // Check user permissions
      const userRes = await axios.get(`${API}/auth/verify`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const user = userRes.data;
      const permissions = user.permissions || {};
      
      // Check treasury permissions (admin has all)
      if (user.role === 'admin' || permissions.treasury_admin) {
        setPermissionLevel('admin');
        setHasPermission(true);
      } else if (permissions.manage_treasury) {
        setPermissionLevel('manage');
        setHasPermission(true);
      } else if (permissions.view_treasury) {
        setPermissionLevel('view');
        setHasPermission(true);
      } else {
        setHasPermission(false);
        setLoading(false);
        return;
      }
      
      // Load initial data
      await Promise.all([
        loadAccounts(),
        loadCategories()
      ]);
      
    } catch (err) {
      console.error('Error loading treasury:', err);
      toast.error('Failed to load treasury data');
    } finally {
      setLoading(false);
    }
  };

  const loadAccounts = async () => {
    try {
      const res = await axios.get(`${API}/treasury/accounts`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAccounts(res.data.accounts || []);
      setTotalBalance(res.data.total_balance || 0);
    } catch (err) {
      console.error('Error loading accounts:', err);
    }
  };

  const loadCategories = async () => {
    try {
      const res = await axios.get(`${API}/treasury/categories`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCategories(res.data || []);
    } catch (err) {
      console.error('Error loading categories:', err);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-10 h-10 text-green-400 mb-4 animate-spin mx-auto" />
          <p className="text-white">Loading Treasury...</p>
        </div>
      </div>
    );
  }

  if (!hasPermission) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
        <Card className="max-w-md w-full bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-red-400">Access Denied</CardTitle>
            <CardDescription>
              You don't have permission to access the Treasury. 
              Contact an administrator to request access.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => navigate('/dashboard')} variant="outline">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const canManage = permissionLevel === 'admin' || permissionLevel === 'manage';
  const isAdmin = permissionLevel === 'admin';

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <div className="bg-slate-800 border-b border-slate-700 px-4 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => navigate('/dashboard')}
              className="text-slate-400 hover:text-white"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Dashboard
            </Button>
            <div>
              <h1 className="text-xl font-bold text-white flex items-center gap-2">
                <DollarSign className="w-6 h-6 text-green-400" />
                Treasury
              </h1>
              <p className="text-slate-400 text-sm">Financial Management</p>
            </div>
          </div>
          
          {/* Total Balance Display */}
          <div className="text-right">
            <p className="text-slate-400 text-xs">Total Balance</p>
            <p className={`text-2xl font-bold ${totalBalance >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              ${totalBalance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto p-4">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-5 bg-slate-800 mb-6">
            <TabsTrigger value="overview" className="data-[state=active]:bg-green-600">
              <Wallet className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">Overview</span>
            </TabsTrigger>
            <TabsTrigger value="transactions" className="data-[state=active]:bg-green-600">
              <Receipt className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">Transactions</span>
            </TabsTrigger>
            <TabsTrigger value="budgets" className="data-[state=active]:bg-green-600">
              <PieChart className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">Budgets</span>
            </TabsTrigger>
            <TabsTrigger value="reports" className="data-[state=active]:bg-green-600">
              <FileText className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">Reports</span>
            </TabsTrigger>
            {isAdmin && (
              <TabsTrigger value="settings" className="data-[state=active]:bg-green-600">
                <Settings className="w-4 h-4 mr-2" />
                <span className="hidden sm:inline">Settings</span>
              </TabsTrigger>
            )}
          </TabsList>

          <TabsContent value="overview">
            <TreasuryOverview 
              accounts={accounts}
              totalBalance={totalBalance}
              onRefresh={loadAccounts}
              canManage={canManage}
            />
          </TabsContent>

          <TabsContent value="transactions">
            <TransactionList 
              accounts={accounts}
              categories={categories}
              canManage={canManage}
              onTransactionChange={loadAccounts}
            />
          </TabsContent>

          <TabsContent value="budgets">
            <BudgetManager 
              categories={categories}
              isAdmin={isAdmin}
            />
          </TabsContent>

          <TabsContent value="reports">
            <ReportsView />
          </TabsContent>

          {isAdmin && (
            <TabsContent value="settings">
              <TreasurySettings 
                accounts={accounts}
                categories={categories}
                onAccountsChange={loadAccounts}
                onCategoriesChange={loadCategories}
              />
            </TabsContent>
          )}
        </Tabs>
      </div>
    </div>
  );
}
