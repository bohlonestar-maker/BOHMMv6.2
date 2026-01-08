import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ArrowLeft, Lightbulb, ThumbsUp, ThumbsDown, Plus, Trash2, Filter } from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL;

export default function SuggestionBox() {
  const navigate = useNavigate();
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newSuggestion, setNewSuggestion] = useState({ title: "", description: "", is_anonymous: false });
  const [statusFilter, setStatusFilter] = useState("all");
  
  const userChapter = localStorage.getItem('chapter');
  const userTitle = localStorage.getItem('title');
  const userRole = localStorage.getItem('role');
  
  // Check if user can manage suggestions (National Officers except Honorary)
  const canManageSuggestions = userChapter === 'National' && 
    ['Prez', 'VP', 'S@A', 'ENF', 'CD', 'T', 'SEC', 'NPrez', 'NVP'].includes(userTitle);

  const fetchSuggestions = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/api/suggestions`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setSuggestions(response.data);
    } catch (error) {
      toast.error("Failed to fetch suggestions");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSuggestions();
  }, []);

  const handleSubmitSuggestion = async (e) => {
    e.preventDefault();
    if (!newSuggestion.title.trim() || !newSuggestion.description.trim()) {
      toast.error("Please fill in both title and description");
      return;
    }
    
    try {
      const token = localStorage.getItem("token");
      await axios.post(`${API}/api/suggestions`, newSuggestion, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success("Suggestion submitted!");
      setNewSuggestion({ title: "", description: "", is_anonymous: false });
      setDialogOpen(false);
      fetchSuggestions();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to submit suggestion");
    }
  };

  const handleVoteSuggestion = async (suggestionId, voteType) => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.post(`${API}/api/suggestions/${suggestionId}/vote`, 
        { vote_type: voteType },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setSuggestions(prev => prev.map(s => 
        s.id === suggestionId ? { ...s, ...response.data } : s
      ));
    } catch (error) {
      toast.error("Failed to vote");
    }
  };

  const handleUpdateSuggestionStatus = async (suggestionId, newStatus) => {
    try {
      const token = localStorage.getItem("token");
      await axios.patch(`${API}/api/suggestions/${suggestionId}/status`, 
        { status: newStatus },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success(`Status updated to ${newStatus.replace('_', ' ')}`);
      fetchSuggestions();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to update status");
    }
  };

  const handleDeleteSuggestion = async (suggestionId) => {
    if (!window.confirm("Are you sure you want to delete this suggestion?")) return;
    
    try {
      const token = localStorage.getItem("token");
      await axios.delete(`${API}/api/suggestions/${suggestionId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success("Suggestion deleted");
      fetchSuggestions();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to delete suggestion");
    }
  };

  const getStatusBadgeColor = (status) => {
    const colors = {
      'new': 'bg-blue-500',
      'reviewed': 'bg-yellow-500',
      'in_progress': 'bg-purple-500',
      'implemented': 'bg-green-500',
      'declined': 'bg-red-500'
    };
    return colors[status] || 'bg-gray-500';
  };

  const filteredSuggestions = statusFilter === "all" 
    ? suggestions 
    : suggestions.filter(s => s.status === statusFilter);

  const statusCounts = {
    all: suggestions.length,
    new: suggestions.filter(s => s.status === 'new').length,
    reviewed: suggestions.filter(s => s.status === 'reviewed').length,
    in_progress: suggestions.filter(s => s.status === 'in_progress').length,
    implemented: suggestions.filter(s => s.status === 'implemented').length,
    declined: suggestions.filter(s => s.status === 'declined').length,
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <div className="bg-slate-800 border-b border-slate-700 sticky top-0 z-10">
        <div className="container mx-auto px-3 sm:px-4 py-3 sm:py-4 max-w-5xl">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-2 sm:gap-4">
              <Button variant="ghost" size="icon" onClick={() => navigate('/')} className="h-8 w-8 sm:h-10 sm:w-10">
                <ArrowLeft className="h-4 w-4 sm:h-5 sm:w-5" />
              </Button>
              <div>
                <h1 className="text-lg sm:text-2xl font-bold flex items-center gap-2 text-white">
                  <Lightbulb className="h-5 w-5 sm:h-6 sm:w-6 text-yellow-400" />
                  Suggestion Box
                </h1>
                <p className="text-muted-foreground text-xs sm:text-sm hidden sm:block">
                  Share your ideas to improve the BOH Hub app
                </p>
              </div>
            </div>
            <Button onClick={() => setDialogOpen(true)} className="bg-yellow-600 hover:bg-yellow-700 h-9 sm:h-10 text-xs sm:text-sm">
              <Plus className="w-4 h-4 mr-1 sm:mr-2" />
              <span className="hidden sm:inline">New Suggestion</span>
              <span className="sm:hidden">New</span>
            </Button>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-3 sm:px-4 py-4 sm:py-6 max-w-5xl">
        {/* Info Banner */}
        <div className="bg-yellow-900/30 border border-yellow-700/50 rounded-lg p-3 mb-4 text-sm text-yellow-200">
          <span className="font-semibold">💡 App Suggestions Only:</span> Share ideas to improve the BOH Hub app features and functionality.
        </div>

        {/* Filter Buttons - More Visible */}
        <div className="flex flex-wrap gap-2 mb-4">
          {[
            { value: 'all', label: 'All', color: 'bg-slate-600 hover:bg-slate-500 border-slate-500' },
            { value: 'new', label: 'New', color: 'bg-blue-600 hover:bg-blue-500 border-blue-500' },
            { value: 'reviewed', label: 'Reviewed', color: 'bg-yellow-600 hover:bg-yellow-500 border-yellow-500' },
            { value: 'in_progress', label: 'In Progress', color: 'bg-purple-600 hover:bg-purple-500 border-purple-500' },
            { value: 'implemented', label: 'Done', color: 'bg-green-600 hover:bg-green-500 border-green-500' },
            { value: 'declined', label: 'Declined', color: 'bg-red-600 hover:bg-red-500 border-red-500' },
          ].map(filter => (
            <Button
              key={filter.value}
              size="sm"
              onClick={() => setStatusFilter(filter.value)}
              className={`text-xs font-medium px-3 py-2 h-9 ${
                statusFilter === filter.value 
                  ? `${filter.color} text-white ring-2 ring-white/30` 
                  : 'bg-slate-700 hover:bg-slate-600 text-slate-300 border border-slate-600'
              }`}
            >
              {filter.label}
              <span className={`ml-1.5 px-1.5 py-0.5 rounded text-xs ${
                statusFilter === filter.value ? 'bg-white/20' : 'bg-slate-600'
              }`}>
                {statusCounts[filter.value]}
              </span>
            </Button>
          ))}
        </div>

        {/* Suggestions List */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-400"></div>
          </div>
        ) : filteredSuggestions.length === 0 ? (
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="text-center py-12">
              <Lightbulb className="w-16 h-16 mx-auto mb-4 text-slate-600" />
              <p className="text-slate-400 text-lg mb-2">
                {statusFilter === "all" ? "No suggestions yet" : `No ${statusFilter.replace('_', ' ')} suggestions`}
              </p>
              <p className="text-slate-500 text-sm mb-4">Be the first to share an idea!</p>
              <Button onClick={() => setDialogOpen(true)} className="bg-yellow-600 hover:bg-yellow-700">
                <Plus className="w-4 h-4 mr-2" />
                Submit a Suggestion
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {filteredSuggestions.map((suggestion) => (
              <Card
                key={suggestion.id}
                className="bg-slate-800 border-slate-700 hover:border-slate-600 transition-all"
                data-testid={`suggestion-${suggestion.id}`}
              >
                <CardContent className="p-3 sm:p-4">
                  <div className="flex items-start gap-3 sm:gap-4">
                    {/* Vote buttons */}
                    <div className="flex flex-col items-center gap-1 min-w-[40px] sm:min-w-[50px]">
                      <button
                        onClick={() => handleVoteSuggestion(suggestion.id, 'upvote')}
                        className={`p-1.5 sm:p-2 rounded-lg hover:bg-slate-700 transition-colors ${
                          suggestion.user_vote === 'upvote' ? 'text-green-400 bg-green-900/30' : 'text-slate-400'
                        }`}
                        data-testid={`upvote-${suggestion.id}`}
                      >
                        <ThumbsUp className="w-4 h-4 sm:w-5 sm:h-5" />
                      </button>
                      <span className={`text-lg sm:text-xl font-bold ${
                        suggestion.vote_count > 0 ? 'text-green-400' : 
                        suggestion.vote_count < 0 ? 'text-red-400' : 'text-slate-400'
                      }`}>
                        {suggestion.vote_count}
                      </span>
                      <button
                        onClick={() => handleVoteSuggestion(suggestion.id, 'downvote')}
                        className={`p-1.5 sm:p-2 rounded-lg hover:bg-slate-700 transition-colors ${
                          suggestion.user_vote === 'downvote' ? 'text-red-400 bg-red-900/30' : 'text-slate-400'
                        }`}
                        data-testid={`downvote-${suggestion.id}`}
                      >
                        <ThumbsDown className="w-4 h-4 sm:w-5 sm:h-5" />
                      </button>
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2 mb-2">
                        <h3 className="font-semibold text-white text-sm sm:text-base">{suggestion.title}</h3>
                        <Badge className={`${getStatusBadgeColor(suggestion.status)} text-white text-xs`}>
                          {suggestion.status.replace('_', ' ')}
                        </Badge>
                      </div>
                      <p className="text-slate-300 text-sm mb-3">{suggestion.description}</p>
                      <div className="flex flex-wrap items-center gap-2 sm:gap-4 text-xs text-slate-400">
                        <span>by <span className="text-slate-300">{suggestion.submitted_by}</span></span>
                        <span>{new Date(suggestion.created_at).toLocaleDateString()}</span>
                        {suggestion.status_updated_by && (
                          <span className="text-slate-500">
                            Updated by {suggestion.status_updated_by}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Actions for National Officers */}
                    {(canManageSuggestions || userRole === 'admin') && (
                      <div className="flex flex-col sm:flex-row items-end sm:items-center gap-2">
                        <Select
                          value={suggestion.status}
                          onValueChange={(value) => handleUpdateSuggestionStatus(suggestion.id, value)}
                        >
                          <SelectTrigger className="w-28 sm:w-32 h-8 text-xs bg-slate-700 border-slate-600">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent className="bg-slate-700 border-slate-600">
                            <SelectItem value="new">New</SelectItem>
                            <SelectItem value="reviewed">Reviewed</SelectItem>
                            <SelectItem value="in_progress">In Progress</SelectItem>
                            <SelectItem value="implemented">Implemented</SelectItem>
                            <SelectItem value="declined">Declined</SelectItem>
                          </SelectContent>
                        </Select>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteSuggestion(suggestion.id)}
                          className="text-red-400 hover:text-red-300 hover:bg-red-900/30 h-8 w-8 p-0"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* New Suggestion Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="bg-slate-800 border-slate-700 mx-4 sm:mx-auto max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Lightbulb className="w-5 h-5 text-yellow-400" />
              Submit App Suggestion
            </DialogTitle>
          </DialogHeader>
          <div className="bg-yellow-900/30 border border-yellow-700/50 rounded-lg p-2 mb-2 text-xs text-yellow-200">
            💡 Suggestions should be about improving the BOH Hub app features and functionality only.
          </div>
          <form onSubmit={handleSubmitSuggestion} className="space-y-4">
            <div>
              <Label className="text-slate-300">Title</Label>
              <Input
                value={newSuggestion.title}
                onChange={(e) => setNewSuggestion(prev => ({ ...prev, title: e.target.value }))}
                placeholder="Brief title for your suggestion"
                className="bg-slate-700 border-slate-600 text-white mt-1"
                data-testid="suggestion-title-input"
              />
            </div>
            <div>
              <Label className="text-slate-300">Description</Label>
              <Textarea
                value={newSuggestion.description}
                onChange={(e) => setNewSuggestion(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Describe your suggestion in detail..."
                rows={4}
                className="bg-slate-700 border-slate-600 text-white mt-1"
                data-testid="suggestion-description-input"
              />
            </div>
            <div className="flex items-center gap-2">
              <Checkbox
                id="anonymous"
                checked={newSuggestion.is_anonymous}
                onCheckedChange={(checked) => setNewSuggestion(prev => ({ ...prev, is_anonymous: checked }))}
              />
              <Label htmlFor="anonymous" className="text-slate-300 text-sm cursor-pointer">
                Submit anonymously
              </Label>
            </div>
            <DialogFooter className="flex-col sm:flex-row gap-2">
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)} className="w-full sm:w-auto">
                Cancel
              </Button>
              <Button type="submit" className="bg-yellow-600 hover:bg-yellow-700 w-full sm:w-auto" data-testid="submit-suggestion-btn">
                Submit Suggestion
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
