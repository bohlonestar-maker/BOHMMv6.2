/**
 * Treasury Overview Component
 * 
 * Displays account balances and recent activity summary
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { 
  Wallet, TrendingUp, TrendingDown, RefreshCw, 
  Building2, PiggyBank, Banknote, MoreHorizontal
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const accountIcons = {
  checking: Building2,
  savings: PiggyBank,
  cash: Banknote,
  other: Wallet
};

export default function TreasuryOverview({ accounts, totalBalance, onRefresh, canManage }) {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  
  const token = localStorage.getItem('token');

  useEffect(() => {
    loadSummary();
  }, []);

  const loadSummary = async () => {
    try {
      const res = await axios.get(`${API}/treasury/reports/summary`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSummary(res.data);
    } catch (err) {
      console.error('Error loading summary:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount || 0);
  };

  return (
    <div className="space-y-6">
      {/* Account Cards */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">Accounts</h2>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={onRefresh}
            className="text-slate-300"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
        
        {accounts.length === 0 ? (
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-8 text-center">
              <Wallet className="w-12 h-12 text-slate-500 mx-auto mb-4" />
              <p className="text-slate-400">No accounts set up yet.</p>
              {canManage && (
                <p className="text-slate-500 text-sm mt-2">
                  Go to Settings to create your first account.
                </p>
              )}
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {accounts.map((account) => {
              const IconComponent = accountIcons[account.type] || Wallet;
              return (
                <Card key={account.id} className="bg-slate-800 border-slate-700">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
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
                    </div>
                    <div className="mt-4">
                      <p className={`text-2xl font-bold ${
                        account.balance >= 0 ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {formatCurrency(account.balance)}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>

      {/* Monthly Summary */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-green-600/20 flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 text-green-400" />
                </div>
                <div>
                  <p className="text-slate-400 text-sm">Income This Month</p>
                  <p className="text-xl font-bold text-green-400">
                    {formatCurrency(summary.income?.total)}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-red-600/20 flex items-center justify-center">
                  <TrendingDown className="w-5 h-5 text-red-400" />
                </div>
                <div>
                  <p className="text-slate-400 text-sm">Expenses This Month</p>
                  <p className="text-xl font-bold text-red-400">
                    {formatCurrency(summary.expenses?.total)}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                  summary.net >= 0 ? 'bg-green-600/20' : 'bg-red-600/20'
                }`}>
                  <Wallet className={`w-5 h-5 ${
                    summary.net >= 0 ? 'text-green-400' : 'text-red-400'
                  }`} />
                </div>
                <div>
                  <p className="text-slate-400 text-sm">Net This Month</p>
                  <p className={`text-xl font-bold ${
                    summary.net >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {formatCurrency(summary.net)}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Top Categories */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Top Income Categories */}
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader className="pb-2">
              <CardTitle className="text-white text-base">Top Income Sources</CardTitle>
            </CardHeader>
            <CardContent>
              {summary.income?.by_category?.length > 0 ? (
                <div className="space-y-3">
                  {summary.income.by_category.slice(0, 5).map((cat) => (
                    <div key={cat.category_id} className="flex items-center justify-between">
                      <span className="text-slate-300 text-sm">{cat.category_name}</span>
                      <span className="text-green-400 font-medium">
                        {formatCurrency(cat.total)}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-slate-500 text-sm">No income recorded this month</p>
              )}
            </CardContent>
          </Card>

          {/* Top Expense Categories */}
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader className="pb-2">
              <CardTitle className="text-white text-base">Top Expenses</CardTitle>
            </CardHeader>
            <CardContent>
              {summary.expenses?.by_category?.length > 0 ? (
                <div className="space-y-3">
                  {summary.expenses.by_category.slice(0, 5).map((cat) => (
                    <div key={cat.category_id} className="flex items-center justify-between">
                      <span className="text-slate-300 text-sm">{cat.category_name}</span>
                      <span className="text-red-400 font-medium">
                        {formatCurrency(cat.total)}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-slate-500 text-sm">No expenses recorded this month</p>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
