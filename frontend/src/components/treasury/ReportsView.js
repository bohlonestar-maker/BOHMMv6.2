/**
 * Reports View Component
 * 
 * Financial reports: monthly, quarterly, yearly summaries
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { toast } from 'sonner';
import { FileText, Download, Loader2, TrendingUp, TrendingDown, Calendar } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

export default function ReportsView() {
  const [loading, setLoading] = useState(false);
  const [reportType, setReportType] = useState('quarterly');
  const [year, setYear] = useState(new Date().getFullYear());
  const [quarter, setQuarter] = useState(Math.ceil((new Date().getMonth() + 1) / 3));
  const [report, setReport] = useState(null);

  const token = localStorage.getItem('token');

  useEffect(() => {
    loadReport();
  }, [reportType, year, quarter]);

  const loadReport = async () => {
    setLoading(true);
    try {
      let endpoint = '';
      let params = {};
      
      if (reportType === 'quarterly') {
        endpoint = '/treasury/reports/quarterly';
        params = { year, quarter };
      } else if (reportType === 'yearly') {
        endpoint = '/treasury/reports/yearly';
        params = { year };
      }
      
      const res = await axios.get(`${API}${endpoint}`, {
        params,
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setReport(res.data);
    } catch (err) {
      console.error('Error loading report:', err);
      toast.error('Failed to load report');
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

  const years = Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - i);

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Report Selection */}
      <div className="flex flex-col sm:flex-row gap-2 sm:gap-4 sm:items-center">
        <Select value={reportType} onValueChange={setReportType}>
          <SelectTrigger className="w-full sm:w-40 bg-slate-800 border-slate-700">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="quarterly">Quarterly</SelectItem>
            <SelectItem value="yearly">Yearly</SelectItem>
          </SelectContent>
        </Select>
        
        <div className="flex gap-2">
          <Select value={year.toString()} onValueChange={(v) => setYear(parseInt(v))}>
            <SelectTrigger className="w-full sm:w-32 bg-slate-800 border-slate-700">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {years.map(y => (
                <SelectItem key={y} value={y.toString()}>{y}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          {reportType === 'quarterly' && (
            <Select value={quarter.toString()} onValueChange={(v) => setQuarter(parseInt(v))}>
              <SelectTrigger className="w-full sm:w-32 bg-slate-800 border-slate-700">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1">Q1</SelectItem>
                <SelectItem value="2">Q2</SelectItem>
                <SelectItem value="3">Q3</SelectItem>
                <SelectItem value="4">Q4</SelectItem>
              </SelectContent>
            </Select>
          )}
        </div>
      </div>

      {/* Report Content */}
      {loading ? (
        <div className="flex items-center justify-center p-6 sm:p-8">
          <Loader2 className="w-8 h-8 text-green-400 animate-spin" />
        </div>
      ) : report ? (
        <div className="space-y-4 sm:space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
            <Card className="bg-slate-800 border-slate-700">
              <CardContent className="p-3 sm:p-4">
                <div className="flex items-center gap-2 sm:gap-3">
                  <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-green-600/20 flex items-center justify-center flex-shrink-0">
                    <TrendingUp className="w-4 h-4 sm:w-5 sm:h-5 text-green-400" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-slate-400 text-xs sm:text-sm">Total Income</p>
                    <p className="text-lg sm:text-xl font-bold text-green-400 truncate">
                      {formatCurrency(report.summary?.total_income)}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800 border-slate-700">
              <CardContent className="p-3 sm:p-4">
                <div className="flex items-center gap-2 sm:gap-3">
                  <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-red-600/20 flex items-center justify-center flex-shrink-0">
                    <TrendingDown className="w-4 h-4 sm:w-5 sm:h-5 text-red-400" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-slate-400 text-xs sm:text-sm">Total Expenses</p>
                    <p className="text-lg sm:text-xl font-bold text-red-400 truncate">
                      {formatCurrency(report.summary?.total_expenses)}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800 border-slate-700">
              <CardContent className="p-3 sm:p-4">
                <div className="flex items-center gap-2 sm:gap-3">
                  <div className={`w-8 h-8 sm:w-10 sm:h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    report.summary?.net >= 0 ? 'bg-green-600/20' : 'bg-red-600/20'
                  }`}>
                    <FileText className={`w-4 h-4 sm:w-5 sm:h-5 ${
                      report.summary?.net >= 0 ? 'text-green-400' : 'text-red-400'
                    }`} />
                  </div>
                  <div className="min-w-0">
                    <p className="text-slate-400 text-xs sm:text-sm">Net</p>
                    <p className={`text-lg sm:text-xl font-bold truncate ${
                      report.summary?.net >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {formatCurrency(report.summary?.net)}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Period Breakdown */}
          {(report.monthly_breakdown || report.quarterly_breakdown) && (
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader className="p-3 sm:p-6 pb-2 sm:pb-4">
                <CardTitle className="text-white text-sm sm:text-base">
                  {reportType === 'quarterly' ? 'Monthly' : 'Quarterly'} Breakdown
                </CardTitle>
              </CardHeader>
              <CardContent className="p-3 sm:p-6 pt-0">
                <div className="overflow-x-auto -mx-3 sm:mx-0">
                  <table className="w-full text-xs sm:text-sm min-w-[320px]">
                    <thead>
                      <tr className="border-b border-slate-700">
                        <th className="text-left p-2 text-slate-400">Period</th>
                        <th className="text-right p-2 text-slate-400">Income</th>
                        <th className="text-right p-2 text-slate-400">Expenses</th>
                        <th className="text-right p-2 text-slate-400">Net</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(report.monthly_breakdown || report.quarterly_breakdown || []).map((row, i) => (
                        <tr key={i} className="border-b border-slate-700/50">
                          <td className="p-2 text-white">
                            {row.month_name || row.quarter_name}
                          </td>
                          <td className="p-2 text-right text-green-400">
                            {formatCurrency(row.income)}
                          </td>
                          <td className="p-2 text-right text-red-400">
                            {formatCurrency(row.expenses)}
                          </td>
                          <td className={`p-2 text-right font-medium ${
                            row.net >= 0 ? 'text-green-400' : 'text-red-400'
                          }`}>
                            {formatCurrency(row.net)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Category Breakdowns */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
            {/* Income by Category */}
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white text-base">Income by Category</CardTitle>
              </CardHeader>
              <CardContent>
                {report.income_by_category?.length > 0 ? (
                  <div className="space-y-3">
                    {report.income_by_category.map((cat) => (
                      <div key={cat.category_id} className="flex items-center justify-between">
                        <div>
                          <span className="text-slate-300 text-sm">{cat.category_name}</span>
                          <span className="text-slate-500 text-xs ml-2">({cat.count} transactions)</span>
                        </div>
                        <span className="text-green-400 font-medium">
                          {formatCurrency(cat.total)}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-500 text-sm">No income for this period</p>
                )}
              </CardContent>
            </Card>

            {/* Expenses by Category */}
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white text-base">Expenses by Category</CardTitle>
              </CardHeader>
              <CardContent>
                {report.expense_by_category?.length > 0 ? (
                  <div className="space-y-3">
                    {report.expense_by_category.map((cat) => (
                      <div key={cat.category_id} className="flex items-center justify-between">
                        <div>
                          <span className="text-slate-300 text-sm">{cat.category_name}</span>
                          <span className="text-slate-500 text-xs ml-2">({cat.count} transactions)</span>
                        </div>
                        <span className="text-red-400 font-medium">
                          {formatCurrency(cat.total)}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-500 text-sm">No expenses for this period</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Budget Comparison (Quarterly only) */}
          {reportType === 'quarterly' && report.budget_comparison?.length > 0 && (
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Budget vs. Actual</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {report.budget_comparison.map((budget, i) => (
                    <div key={i} className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-white">{budget.category_name}</span>
                        <span className={`font-medium ${
                          budget.percent_used > 100 ? 'text-red-400' : 
                          budget.percent_used > 80 ? 'text-yellow-400' : 'text-green-400'
                        }`}>
                          {formatCurrency(budget.spent)} / {formatCurrency(budget.budgeted)}
                          ({budget.percent_used.toFixed(0)}%)
                        </span>
                      </div>
                      <div className="w-full bg-slate-700 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full ${
                            budget.percent_used > 100 ? 'bg-red-500' : 
                            budget.percent_used > 80 ? 'bg-yellow-500' : 'bg-green-500'
                          }`}
                          style={{ width: `${Math.min(budget.percent_used, 100)}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      ) : (
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="p-8 text-center">
            <FileText className="w-12 h-12 text-slate-500 mx-auto mb-4" />
            <p className="text-slate-400">Select a report type and period</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
