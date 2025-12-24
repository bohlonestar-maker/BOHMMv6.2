import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { toast } from "sonner";
import { 
  ArrowLeft, 
  Plus, 
  Edit2, 
  Trash2, 
  Star,
  Shield,
  Heart,
  Calendar
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CHAPTERS = ["National", "AD", "HA", "HS"];
const TITLES = ["Prez", "VP", "S@A", "ENF", "SEC", "T", "CD", "CC", "CCLC", "MD", "PM", "Member", "Honorary"];
const MILITARY_BRANCHES = ["Army", "Navy", "Air Force", "Marines", "Coast Guard", "Space Force", "National Guard"];

export default function WallOfHonor({ token, userRole }) {
  const navigate = useNavigate();
  const [fallenMembers, setFallenMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingMember, setEditingMember] = useState(null);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [memberToDelete, setMemberToDelete] = useState(null);
  
  const [formData, setFormData] = useState({
    name: "",
    handle: "",
    chapter: "",
    title: "",
    photo_url: "",
    date_of_passing: "",
    join_date: "",
    tribute: "",
    military_service: false,
    military_branch: "",
    is_first_responder: false
  });

  const isAdmin = userRole === "admin";

  useEffect(() => {
    fetchFallenMembers();
  }, []);

  const fetchFallenMembers = async () => {
    try {
      const response = await axios.get(`${API}/fallen`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setFallenMembers(response.data);
    } catch (error) {
      console.error("Error fetching fallen members:", error);
      toast.error("Failed to load Wall of Honor");
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      name: "",
      handle: "",
      chapter: "",
      title: "",
      photo_url: "",
      date_of_passing: "",
      join_date: "",
      tribute: "",
      military_service: false,
      military_branch: "",
      is_first_responder: false
    });
    setEditingMember(null);
  };

  const openAddDialog = () => {
    resetForm();
    setDialogOpen(true);
  };

  const openEditDialog = (member) => {
    setFormData({
      name: member.name || "",
      handle: member.handle || "",
      chapter: member.chapter || "",
      title: member.title || "",
      photo_url: member.photo_url || "",
      date_of_passing: member.date_of_passing || "",
      join_date: member.join_date || "",
      tribute: member.tribute || "",
      military_service: member.military_service || false,
      military_branch: member.military_branch || "",
      is_first_responder: member.is_first_responder || false
    });
    setEditingMember(member);
    setDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.name.trim() || !formData.handle.trim()) {
      toast.error("Name and Handle are required");
      return;
    }

    try {
      if (editingMember) {
        await axios.put(`${API}/fallen/${editingMember.id}`, formData, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success("Memorial updated successfully");
      } else {
        await axios.post(`${API}/fallen`, formData, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success("Memorial added to Wall of Honor");
      }
      
      setDialogOpen(false);
      resetForm();
      fetchFallenMembers();
    } catch (error) {
      console.error("Error saving fallen member:", error);
      toast.error(error.response?.data?.detail || "Failed to save memorial");
    }
  };

  const handleDelete = async () => {
    if (!memberToDelete) return;
    
    try {
      await axios.delete(`${API}/fallen/${memberToDelete.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Memorial removed from Wall of Honor");
      setDeleteConfirmOpen(false);
      setMemberToDelete(null);
      fetchFallenMembers();
    } catch (error) {
      console.error("Error deleting fallen member:", error);
      toast.error("Failed to remove memorial");
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return null;
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
      });
    } catch {
      return dateStr;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading Wall of Honor...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 text-white">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6 sm:py-10">
        {/* Header */}
        <div className="mb-8">
          <Button
            onClick={() => navigate("/dashboard")}
            variant="ghost"
            size="sm"
            className="text-slate-300 hover:text-white mb-4 -ml-2"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Members
          </Button>
          
          <div className="text-center mb-8">
            <div className="flex justify-center mb-4">
              <div className="w-16 h-16 sm:w-20 sm:h-20 bg-amber-600 rounded-full flex items-center justify-center">
                <Star className="w-8 h-8 sm:w-10 sm:h-10 text-white" />
              </div>
            </div>
            <h1 className="text-3xl sm:text-4xl font-bold text-amber-400 mb-2">Wall of Honor</h1>
            <p className="text-slate-400 text-sm sm:text-base max-w-2xl mx-auto">
              In loving memory of our fallen brothers who rode beside us. 
              Though they&apos;ve made their final haul, their spirit rides on in our hearts forever.
            </p>
          </div>
          
          {isAdmin && (
            <div className="flex justify-center">
              <Button
                onClick={openAddDialog}
                className="bg-amber-600 hover:bg-amber-700 text-white"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Memorial
              </Button>
            </div>
          )}
        </div>

        {/* Fallen Members Grid */}
        {fallenMembers.length === 0 ? (
          <div className="text-center py-16">
            <Heart className="w-16 h-16 text-slate-600 mx-auto mb-4" />
            <p className="text-slate-400 text-lg">No memorials yet</p>
            {isAdmin && (
              <p className="text-slate-500 text-sm mt-2">
                Click &ldquo;Add Memorial&rdquo; to honor a fallen brother
              </p>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {fallenMembers.map((member) => (
              <Card 
                key={member.id} 
                className="bg-slate-800/80 border-amber-600/30 hover:border-amber-500/50 transition-all duration-300 overflow-hidden"
              >
                <div className="h-2 bg-gradient-to-r from-amber-600 via-amber-500 to-amber-600"></div>
                <CardContent className="p-5">
                  {/* Photo or Placeholder */}
                  <div className="flex justify-center mb-4">
                    {member.photo_url ? (
                      <img 
                        src={member.photo_url} 
                        alt={member.name}
                        className="w-24 h-24 sm:w-28 sm:h-28 rounded-full object-cover border-4 border-amber-600/50"
                      />
                    ) : (
                      <div className="w-24 h-24 sm:w-28 sm:h-28 rounded-full bg-slate-700 border-4 border-amber-600/50 flex items-center justify-center">
                        <Star className="w-10 h-10 text-amber-500" />
                      </div>
                    )}
                  </div>
                  
                  {/* Name and Handle */}
                  <div className="text-center mb-3">
                    <h3 className="text-xl font-bold text-amber-400">{member.handle}</h3>
                    <p className="text-slate-300">{member.name}</p>
                    {(member.chapter || member.title) && (
                      <p className="text-sm text-slate-400 mt-1">
                        {[member.chapter, member.title].filter(Boolean).join(" • ")}
                      </p>
                    )}
                  </div>
                  
                  {/* Dates */}
                  {(member.date_of_passing || member.join_date) && (
                    <div className="flex items-center justify-center gap-2 text-xs text-slate-400 mb-3">
                      <Calendar className="w-3 h-3" />
                      {member.join_date && member.date_of_passing ? (
                        <span>{member.join_date} — {formatDate(member.date_of_passing)}</span>
                      ) : member.date_of_passing ? (
                        <span>Passed: {formatDate(member.date_of_passing)}</span>
                      ) : (
                        <span>Joined: {member.join_date}</span>
                      )}
                    </div>
                  )}
                  
                  {/* Service Badges */}
                  {(member.military_service || member.is_first_responder) && (
                    <div className="flex justify-center gap-2 mb-3">
                      {member.military_service && (
                        <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-900/50 text-green-400 text-xs rounded-full border border-green-600/30">
                          <Shield className="w-3 h-3" />
                          {member.military_branch || "Veteran"}
                        </span>
                      )}
                      {member.is_first_responder && (
                        <span className="inline-flex items-center gap-1 px-2 py-1 bg-red-900/50 text-red-400 text-xs rounded-full border border-red-600/30">
                          🚨 First Responder
                        </span>
                      )}
                    </div>
                  )}
                  
                  {/* Tribute */}
                  {member.tribute && (
                    <div className="bg-slate-900/50 rounded-lg p-3 mt-3">
                      <p className="text-sm text-slate-300 italic text-center leading-relaxed">
                        &ldquo;{member.tribute}&rdquo;
                      </p>
                    </div>
                  )}
                  
                  {/* Admin Actions */}
                  {isAdmin && (
                    <div className="flex justify-center gap-2 mt-4 pt-4 border-t border-slate-700">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => openEditDialog(member)}
                        className="border-slate-600 text-slate-300 hover:bg-slate-700"
                      >
                        <Edit2 className="w-3 h-3 mr-1" />
                        Edit
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setMemberToDelete(member);
                          setDeleteConfirmOpen(true);
                        }}
                        className="border-red-600/50 text-red-400 hover:bg-red-900/30"
                      >
                        <Trash2 className="w-3 h-3 mr-1" />
                        Remove
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
        
        {/* Footer Quote */}
        <div className="text-center mt-12 pt-8 border-t border-slate-700">
          <p className="text-amber-500 italic text-sm sm:text-base">
            &ldquo;Gone from our sight, but never from our hearts&rdquo;
          </p>
        </div>
      </div>

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="bg-slate-800 border-slate-700 w-[95vw] max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Star className="w-5 h-5 text-amber-500" />
              {editingMember ? "Edit Memorial" : "Add to Wall of Honor"}
            </DialogTitle>
          </DialogHeader>
          
          <form onSubmit={handleSubmit} className="space-y-4 mt-2">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-200">Name <span className="text-red-400">*</span></Label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Full name"
                  required
                  className="mt-1 bg-slate-700 border-slate-600 text-white"
                />
              </div>
              <div>
                <Label className="text-slate-200">Handle <span className="text-red-400">*</span></Label>
                <Input
                  value={formData.handle}
                  onChange={(e) => setFormData({ ...formData, handle: e.target.value })}
                  placeholder="Road name"
                  required
                  className="mt-1 bg-slate-700 border-slate-600 text-white"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-200">Chapter</Label>
                <Select
                  value={formData.chapter}
                  onValueChange={(value) => setFormData({ ...formData, chapter: value })}
                >
                  <SelectTrigger className="mt-1 bg-slate-700 border-slate-600 text-white">
                    <SelectValue placeholder="Select chapter" />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-700 border-slate-600">
                    {CHAPTERS.map((chapter) => (
                      <SelectItem key={chapter} value={chapter} className="text-white hover:bg-slate-600">
                        {chapter}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-slate-200">Title</Label>
                <Select
                  value={formData.title}
                  onValueChange={(value) => setFormData({ ...formData, title: value })}
                >
                  <SelectTrigger className="mt-1 bg-slate-700 border-slate-600 text-white">
                    <SelectValue placeholder="Select title" />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-700 border-slate-600">
                    {TITLES.map((title) => (
                      <SelectItem key={title} value={title} className="text-white hover:bg-slate-600">
                        {title}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-200">Join Date</Label>
                <Input
                  value={formData.join_date}
                  onChange={(e) => setFormData({ ...formData, join_date: e.target.value })}
                  placeholder="MM/YYYY"
                  className="mt-1 bg-slate-700 border-slate-600 text-white"
                />
              </div>
              <div>
                <Label className="text-slate-200">Date of Passing</Label>
                <Input
                  type="date"
                  value={formData.date_of_passing}
                  onChange={(e) => setFormData({ ...formData, date_of_passing: e.target.value })}
                  className="mt-1 bg-slate-700 border-slate-600 text-white"
                />
              </div>
            </div>

            <div>
              <Label className="text-slate-200">Photo URL</Label>
              <Input
                value={formData.photo_url}
                onChange={(e) => setFormData({ ...formData, photo_url: e.target.value })}
                placeholder="https://example.com/photo.jpg"
                className="mt-1 bg-slate-700 border-slate-600 text-white"
              />
              <p className="text-xs text-slate-500 mt-1">Direct link to a photo (optional)</p>
            </div>

            <div>
              <Label className="text-slate-200">Tribute / Memorial Message</Label>
              <Textarea
                value={formData.tribute}
                onChange={(e) => setFormData({ ...formData, tribute: e.target.value })}
                placeholder="A few words in their memory..."
                rows={3}
                className="mt-1 bg-slate-700 border-slate-600 text-white resize-none"
              />
            </div>

            {/* Service */}
            <div className="space-y-3 pt-2 border-t border-slate-700">
              <div className="flex items-center space-x-3">
                <Checkbox
                  id="military_service"
                  checked={formData.military_service}
                  onCheckedChange={(checked) => setFormData({ ...formData, military_service: checked })}
                />
                <Label htmlFor="military_service" className="text-slate-200 cursor-pointer">
                  Military Veteran
                </Label>
              </div>
              
              {formData.military_service && (
                <Select
                  value={formData.military_branch}
                  onValueChange={(value) => setFormData({ ...formData, military_branch: value })}
                >
                  <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                    <SelectValue placeholder="Select branch" />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-700 border-slate-600">
                    {MILITARY_BRANCHES.map((branch) => (
                      <SelectItem key={branch} value={branch} className="text-white hover:bg-slate-600">
                        {branch}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}

              <div className="flex items-center space-x-3">
                <Checkbox
                  id="is_first_responder"
                  checked={formData.is_first_responder}
                  onCheckedChange={(checked) => setFormData({ ...formData, is_first_responder: checked })}
                />
                <Label htmlFor="is_first_responder" className="text-slate-200 cursor-pointer">
                  First Responder (Police, Fire, or EMS)
                </Label>
              </div>
            </div>

            <div className="flex gap-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => setDialogOpen(false)}
                className="flex-1 border-slate-600 text-slate-300 hover:bg-slate-700"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                className="flex-1 bg-amber-600 hover:bg-amber-700 text-white"
              >
                {editingMember ? "Update Memorial" : "Add to Wall of Honor"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteConfirmOpen} onOpenChange={setDeleteConfirmOpen}>
        <DialogContent className="bg-slate-800 border-slate-700 max-w-sm">
          <DialogHeader>
            <DialogTitle className="text-white">Remove Memorial</DialogTitle>
          </DialogHeader>
          <p className="text-slate-300 text-sm">
            Are you sure you want to remove <strong>{memberToDelete?.handle}</strong> from the Wall of Honor? 
            This action cannot be undone.
          </p>
          <div className="flex gap-3 mt-4">
            <Button
              variant="outline"
              onClick={() => setDeleteConfirmOpen(false)}
              className="flex-1 border-slate-600 text-slate-300 hover:bg-slate-700"
            >
              Cancel
            </Button>
            <Button
              onClick={handleDelete}
              className="flex-1 bg-red-600 hover:bg-red-700 text-white"
            >
              Remove
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
