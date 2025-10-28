import { useState, useEffect } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ArrowLeft, Plus, Trash2, Shield, Pencil, Key, Mail } from "lucide-react";
import { useNavigate } from "react-router-dom";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function UserManagement({ onLogout }) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [passwordDialogOpen, setPasswordDialogOpen] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    username: "",
    password: "",
    role: "user",
    permissions: {
      basic_info: true,
      email: false,
      phone: false,
      address: false,
      dues_tracking: false,
      meeting_attendance: false,
      admin_actions: false
    }
  });

  const [inviteFormData, setInviteFormData] = useState({
    email: "",
    role: "user",
    permissions: {
      basic_info: true,
      email: false,
      phone: false,
      address: false,
      dues_tracking: false,
      meeting_attendance: false,
      admin_actions: false
    }
  });

  const [editFormData, setEditFormData] = useState({
    role: "user",
    permissions: {
      basic_info: true,
      email: false,
      phone: false,
      address: false,
      dues_tracking: false,
      meeting_attendance: false,
      admin_actions: false
    }
  });

  const [passwordFormData, setPasswordFormData] = useState({
    newPassword: "",
    confirmPassword: "",
  });

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/users`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setUsers(response.data);
    } catch (error) {
      toast.error("Failed to load users");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem("token");

    try {
      await axios.post(`${API}/users`, formData, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success("User created successfully");
      setDialogOpen(false);
      resetForm();
      fetchUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to create user");
    }
  };

  const handleInviteSubmit = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem("token");

    try {
      const response = await axios.post(`${API}/invites`, inviteFormData, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success(response.data.message);
      setInviteDialogOpen(false);
      resetInviteForm();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to send invitation");
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this user?")) return;

    const token = localStorage.getItem("token");
    try {
      await axios.delete(`${API}/users/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success("User deleted successfully");
      fetchUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to delete user");
    }
  };

  const handleEdit = (user) => {
    setEditingUser(user);
    setEditFormData({
      role: user.role,
      permissions: user.permissions || {
        basic_info: true,
        email: false,
        phone: false,
        address: false,
        dues_tracking: false,
        meeting_attendance: false,
        admin_actions: false
      }
    });
    setEditDialogOpen(true);
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem("token");

    try {
      await axios.put(`${API}/users/${editingUser.id}`, editFormData, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success("User updated successfully");
      setEditDialogOpen(false);
      setEditingUser(null);
      fetchUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to update user");
    }
  };

  const handlePasswordChange = (user) => {
    setEditingUser(user);
    setPasswordFormData({
      newPassword: "",
      confirmPassword: "",
    });
    setPasswordDialogOpen(true);
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    
    if (passwordFormData.newPassword !== passwordFormData.confirmPassword) {
      toast.error("Passwords do not match");
      return;
    }

    if (passwordFormData.newPassword.length < 6) {
      toast.error("Password must be at least 6 characters");
      return;
    }

    const token = localStorage.getItem("token");

    try {
      await axios.put(
        `${API}/users/${editingUser.id}`,
        { password: passwordFormData.newPassword },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      toast.success("Password changed successfully");
      setPasswordDialogOpen(false);
      setEditingUser(null);
      setPasswordFormData({ newPassword: "", confirmPassword: "" });
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to change password");
    }
  };

  const resetForm = () => {
    setFormData({
      username: "",
      password: "",
      role: "user",
      permissions: {
        basic_info: true,
        email: false,
        phone: false,
        address: false,
        dues_tracking: false,
        meeting_attendance: false,
        admin_actions: false
      }
    });
  };

  const resetInviteForm = () => {
    setInviteFormData({
      email: "",
      role: "user",
      permissions: {
        basic_info: true,
        email: false,
        phone: false,
        address: false,
        dues_tracking: false,
        meeting_attendance: false,
        admin_actions: false
      }
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <nav className="bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <Button
                onClick={() => navigate("/")}
                variant="outline"
                data-testid="back-button"
                className="flex items-center gap-2"
              >
                <ArrowLeft className="w-4 h-4" />
                Back
              </Button>
              <h1 className="text-2xl font-bold text-slate-900">User Management</h1>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-semibold text-slate-900">System Users</h2>
            <div className="flex gap-3">
              <Dialog open={inviteDialogOpen} onOpenChange={(open) => {
                setInviteDialogOpen(open);
                if (!open) resetInviteForm();
              }}>
                <DialogTrigger asChild>
                  <Button
                    data-testid="invite-user-button"
                    variant="outline"
                    className="flex items-center gap-2"
                  >
                    <Mail className="w-4 h-4" />
                    Invite User
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                  <DialogHeader>
                    <DialogTitle>Invite New User</DialogTitle>
                  </DialogHeader>
                  <form onSubmit={handleInviteSubmit} className="space-y-4 mt-4">
                    <div>
                      <Label>Email Address</Label>
                      <Input
                        data-testid="invite-email-input"
                        type="email"
                        value={inviteFormData.email}
                        onChange={(e) =>
                          setInviteFormData({ ...inviteFormData, email: e.target.value })
                        }
                        placeholder="user@example.com"
                        required
                      />
                    </div>

                    <div>
                      <Label>Role</Label>
                      <Select
                        value={inviteFormData.role}
                        onValueChange={(value) =>
                          setInviteFormData({ ...inviteFormData, role: value })
                        }
                      >
                        <SelectTrigger data-testid="invite-role-select">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="user">User</SelectItem>
                          <SelectItem value="admin">Admin</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-3">
                      <Label>Permissions</Label>
                      <div className="space-y-2 border rounded-lg p-4">
                        <div className="flex items-center space-x-2">
                          <Checkbox
                            id="invite_basic_info"
                            checked={inviteFormData.permissions.basic_info}
                            onCheckedChange={(checked) =>
                              setInviteFormData({
                                ...inviteFormData,
                                permissions: { ...inviteFormData.permissions, basic_info: checked }
                              })
                            }
                          />
                          <label htmlFor="invite_basic_info" className="text-sm font-medium cursor-pointer">
                            Basic Info (Chapter, Title, Handle, Name)
                          </label>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Checkbox
                            id="invite_email"
                            checked={inviteFormData.permissions.email}
                            onCheckedChange={(checked) =>
                              setInviteFormData({
                                ...inviteFormData,
                                permissions: { ...inviteFormData.permissions, email: checked }
                              })
                            }
                          />
                          <label htmlFor="invite_email" className="text-sm font-medium cursor-pointer">
                            Email
                          </label>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Checkbox
                            id="invite_phone"
                            checked={inviteFormData.permissions.phone}
                            onCheckedChange={(checked) =>
                              setInviteFormData({
                                ...inviteFormData,
                                permissions: { ...inviteFormData.permissions, phone: checked }
                              })
                            }
                          />
                          <label htmlFor="invite_phone" className="text-sm font-medium cursor-pointer">
                            Phone
                          </label>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Checkbox
                            id="invite_address"
                            checked={inviteFormData.permissions.address}
                            onCheckedChange={(checked) =>
                              setInviteFormData({
                                ...inviteFormData,
                                permissions: { ...inviteFormData.permissions, address: checked }
                              })
                            }
                          />
                          <label htmlFor="invite_address" className="text-sm font-medium cursor-pointer">
                            Address
                          </label>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Checkbox
                            id="invite_dues_tracking"
                            checked={inviteFormData.permissions.dues_tracking}
                            onCheckedChange={(checked) =>
                              setInviteFormData({
                                ...inviteFormData,
                                permissions: { ...inviteFormData.permissions, dues_tracking: checked }
                              })
                            }
                          />
                          <label htmlFor="invite_dues_tracking" className="text-sm font-medium cursor-pointer">
                            Dues Tracking
                          </label>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Checkbox
                            id="invite_meeting_attendance"
                            checked={inviteFormData.permissions.meeting_attendance}
                            onCheckedChange={(checked) =>
                              setInviteFormData({
                                ...inviteFormData,
                                permissions: { ...inviteFormData.permissions, meeting_attendance: checked }
                              })
                            }
                          />
                          <label htmlFor="invite_meeting_attendance" className="text-sm font-medium cursor-pointer">
                            Meeting Attendance
                          </label>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Checkbox
                            id="invite_admin_actions"
                            checked={inviteFormData.permissions.admin_actions}
                            onCheckedChange={(checked) =>
                              setInviteFormData({
                                ...inviteFormData,
                                permissions: { ...inviteFormData.permissions, admin_actions: checked }
                              })
                            }
                          />
                          <label htmlFor="invite_admin_actions" className="text-sm font-medium cursor-pointer">
                            Admin Actions (Add/Edit/Delete, Export CSV, User Management)
                          </label>
                        </div>
                      </div>
                    </div>

                    <div className="flex gap-3 justify-end pt-4">
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => {
                          setInviteDialogOpen(false);
                          resetInviteForm();
                        }}
                      >
                        Cancel
                      </Button>
                      <Button
                        type="submit"
                        data-testid="submit-invite-button"
                        className="bg-slate-800 hover:bg-slate-900"
                      >
                        Send Invitation
                      </Button>
                    </div>
                  </form>
                </DialogContent>
              </Dialog>

              <Dialog open={dialogOpen} onOpenChange={(open) => {
                setDialogOpen(open);
                if (!open) resetForm();
              }}>
                <DialogTrigger asChild>
                  <Button
                    data-testid="add-user-button"
                    className="flex items-center gap-2 bg-slate-800 hover:bg-slate-900"
                  >
                    <Plus className="w-4 h-4" />
                    Add User
                  </Button>
                </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Add New User</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                  <div>
                    <Label>Username</Label>
                    <Input
                      data-testid="username-input"
                      value={formData.username}
                      onChange={(e) =>
                        setFormData({ ...formData, username: e.target.value })
                      }
                      required
                    />
                  </div>

                  <div>
                    <Label>Password</Label>
                    <Input
                      data-testid="password-input"
                      type="password"
                      value={formData.password}
                      onChange={(e) =>
                        setFormData({ ...formData, password: e.target.value })
                      }
                      required
                    />
                  </div>

                  <div>
                    <Label>Role</Label>
                    <Select
                      value={formData.role}
                      onValueChange={(value) =>
                        setFormData({ ...formData, role: value })
                      }
                    >
                      <SelectTrigger data-testid="role-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="user">User</SelectItem>
                        <SelectItem value="admin">Admin</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-3">
                    <Label>Permissions</Label>
                    <div className="space-y-2 border rounded-lg p-4">
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="basic_info"
                          checked={formData.permissions.basic_info}
                          onCheckedChange={(checked) =>
                            setFormData({
                              ...formData,
                              permissions: { ...formData.permissions, basic_info: checked }
                            })
                          }
                        />
                        <label htmlFor="basic_info" className="text-sm font-medium cursor-pointer">
                          Basic Info (Chapter, Title, Handle, Name)
                        </label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="email"
                          checked={formData.permissions.email}
                          onCheckedChange={(checked) =>
                            setFormData({
                              ...formData,
                              permissions: { ...formData.permissions, email: checked }
                            })
                          }
                        />
                        <label htmlFor="email" className="text-sm font-medium cursor-pointer">
                          Email
                        </label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="phone"
                          checked={formData.permissions.phone}
                          onCheckedChange={(checked) =>
                            setFormData({
                              ...formData,
                              permissions: { ...formData.permissions, phone: checked }
                            })
                          }
                        />
                        <label htmlFor="phone" className="text-sm font-medium cursor-pointer">
                          Phone
                        </label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="address"
                          checked={formData.permissions.address}
                          onCheckedChange={(checked) =>
                            setFormData({
                              ...formData,
                              permissions: { ...formData.permissions, address: checked }
                            })
                          }
                        />
                        <label htmlFor="address" className="text-sm font-medium cursor-pointer">
                          Address
                        </label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="dues_tracking"
                          checked={formData.permissions.dues_tracking}
                          onCheckedChange={(checked) =>
                            setFormData({
                              ...formData,
                              permissions: { ...formData.permissions, dues_tracking: checked }
                            })
                          }
                        />
                        <label htmlFor="dues_tracking" className="text-sm font-medium cursor-pointer">
                          Dues Tracking
                        </label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="meeting_attendance"
                          checked={formData.permissions.meeting_attendance}
                          onCheckedChange={(checked) =>
                            setFormData({
                              ...formData,
                              permissions: { ...formData.permissions, meeting_attendance: checked }
                            })
                          }
                        />
                        <label htmlFor="meeting_attendance" className="text-sm font-medium cursor-pointer">
                          Meeting Attendance
                        </label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="admin_actions"
                          checked={formData.permissions.admin_actions}
                          onCheckedChange={(checked) =>
                            setFormData({
                              ...formData,
                              permissions: { ...formData.permissions, admin_actions: checked }
                            })
                          }
                        />
                        <label htmlFor="admin_actions" className="text-sm font-medium cursor-pointer">
                          Admin Actions (Add/Edit/Delete, Export CSV, User Management)
                        </label>
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-3 justify-end pt-4">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => {
                        setDialogOpen(false);
                        resetForm();
                      }}
                    >
                      Cancel
                    </Button>
                    <Button
                      type="submit"
                      data-testid="submit-user-button"
                      className="bg-slate-800 hover:bg-slate-900"
                    >
                      Create User
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          </div>

          {/* Edit User Dialog */}
          <Dialog open={editDialogOpen} onOpenChange={(open) => {
            setEditDialogOpen(open);
            if (!open) setEditingUser(null);
          }}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Edit User: {editingUser?.username}</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleEditSubmit} className="space-y-4 mt-4">
                <div>
                  <Label>Role</Label>
                  <Select
                    value={editFormData.role}
                    onValueChange={(value) =>
                      setEditFormData({ ...editFormData, role: value })
                    }
                  >
                    <SelectTrigger data-testid="edit-role-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="user">User</SelectItem>
                      <SelectItem value="admin">Admin</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-3">
                  <Label>Permissions</Label>
                  <div className="space-y-2 border rounded-lg p-4">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="edit_basic_info"
                        checked={editFormData.permissions.basic_info}
                        onCheckedChange={(checked) =>
                          setEditFormData({
                            ...editFormData,
                            permissions: { ...editFormData.permissions, basic_info: checked }
                          })
                        }
                      />
                      <label htmlFor="edit_basic_info" className="text-sm font-medium cursor-pointer">
                        Basic Info (Chapter, Title, Handle, Name)
                      </label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="edit_email"
                        checked={editFormData.permissions.email}
                        onCheckedChange={(checked) =>
                          setEditFormData({
                            ...editFormData,
                            permissions: { ...editFormData.permissions, email: checked }
                          })
                        }
                      />
                      <label htmlFor="edit_email" className="text-sm font-medium cursor-pointer">
                        Email
                      </label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="edit_phone"
                        checked={editFormData.permissions.phone}
                        onCheckedChange={(checked) =>
                          setEditFormData({
                            ...editFormData,
                            permissions: { ...editFormData.permissions, phone: checked }
                          })
                        }
                      />
                      <label htmlFor="edit_phone" className="text-sm font-medium cursor-pointer">
                        Phone
                      </label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="edit_address"
                        checked={editFormData.permissions.address}
                        onCheckedChange={(checked) =>
                          setEditFormData({
                            ...editFormData,
                            permissions: { ...editFormData.permissions, address: checked }
                          })
                        }
                      />
                      <label htmlFor="edit_address" className="text-sm font-medium cursor-pointer">
                        Address
                      </label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="edit_dues_tracking"
                        checked={editFormData.permissions.dues_tracking}
                        onCheckedChange={(checked) =>
                          setEditFormData({
                            ...editFormData,
                            permissions: { ...editFormData.permissions, dues_tracking: checked }
                          })
                        }
                      />
                      <label htmlFor="edit_dues_tracking" className="text-sm font-medium cursor-pointer">
                        Dues Tracking
                      </label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="edit_meeting_attendance"
                        checked={editFormData.permissions.meeting_attendance}
                        onCheckedChange={(checked) =>
                          setEditFormData({
                            ...editFormData,
                            permissions: { ...editFormData.permissions, meeting_attendance: checked }
                          })
                        }
                      />
                      <label htmlFor="edit_meeting_attendance" className="text-sm font-medium cursor-pointer">
                        Meeting Attendance
                      </label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="edit_admin_actions"
                        checked={editFormData.permissions.admin_actions}
                        onCheckedChange={(checked) =>
                          setEditFormData({
                            ...editFormData,
                            permissions: { ...editFormData.permissions, admin_actions: checked }
                          })
                        }
                      />
                      <label htmlFor="edit_admin_actions" className="text-sm font-medium cursor-pointer">
                        Admin Actions (Add/Edit/Delete, Export CSV, User Management)
                      </label>
                    </div>
                  </div>
                </div>

                <div className="flex gap-3 justify-end pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setEditDialogOpen(false);
                      setEditingUser(null);
                    }}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    data-testid="submit-edit-user-button"
                    className="bg-slate-800 hover:bg-slate-900"
                  >
                    Update User
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>

          {/* Change Password Dialog */}
          <Dialog open={passwordDialogOpen} onOpenChange={(open) => {
            setPasswordDialogOpen(open);
            if (!open) {
              setEditingUser(null);
              setPasswordFormData({ newPassword: "", confirmPassword: "" });
            }
          }}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Change Password: {editingUser?.username}</DialogTitle>
              </DialogHeader>
              <form onSubmit={handlePasswordSubmit} className="space-y-4 mt-4">
                <div>
                  <Label>New Password</Label>
                  <Input
                    data-testid="new-password-input"
                    type="password"
                    value={passwordFormData.newPassword}
                    onChange={(e) =>
                      setPasswordFormData({ ...passwordFormData, newPassword: e.target.value })
                    }
                    required
                    minLength={6}
                  />
                </div>

                <div>
                  <Label>Confirm New Password</Label>
                  <Input
                    data-testid="confirm-password-input"
                    type="password"
                    value={passwordFormData.confirmPassword}
                    onChange={(e) =>
                      setPasswordFormData({ ...passwordFormData, confirmPassword: e.target.value })
                    }
                    required
                    minLength={6}
                  />
                </div>

                <div className="flex gap-3 justify-end pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setPasswordDialogOpen(false);
                      setEditingUser(null);
                      setPasswordFormData({ newPassword: "", confirmPassword: "" });
                    }}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    data-testid="submit-password-button"
                    className="bg-slate-800 hover:bg-slate-900"
                  >
                    Change Password
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
          </div>

          {loading ? (
            <div className="text-center py-12 text-slate-600">Loading users...</div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Username</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Created At</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users.map((user) => (
                    <TableRow key={user.id} data-testid={`user-row-${user.id}`}>
                      <TableCell className="font-medium">{user.username}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {user.role === "admin" && (
                            <Shield className="w-4 h-4 text-slate-600" />
                          )}
                          <span className="capitalize">{user.role}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        {new Date(user.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleEdit(user)}
                            data-testid={`edit-user-${user.id}`}
                          >
                            <Pencil className="w-4 h-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handlePasswordChange(user)}
                            data-testid={`change-password-${user.id}`}
                          >
                            <Key className="w-4 h-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="destructive"
                            onClick={() => handleDelete(user.id)}
                            data-testid={`delete-user-${user.id}`}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}