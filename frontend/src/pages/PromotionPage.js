import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Checkbox } from "../components/ui/checkbox";
import { Badge } from "../components/ui/badge";
import { toast } from "sonner";
import { Users, Shield, Award, RefreshCw, Save, ArrowLeft, Building, UserCog } from "lucide-react";
import { useNavigate } from "react-router-dom";
import axios from 'axios';
import PageLayout from "../components/PageLayout";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const CHAPTERS = ["National", "AD", "HA", "HS"];
const TITLES = ["Prez", "VP", "S@A", "ENF", "SEC", "T", "CD", "CC", "CCLC", "MD", "PM", "(pm)", "Brother", "Honorary"];

export default function PromotionPage() {
  const navigate = useNavigate();
  const token = localStorage.getItem('token');
  
  const [members, setMembers] = useState([]);
  const [discordRoles, setDiscordRoles] = useState([]);
  const [selectedMemberId, setSelectedMemberId] = useState('');
  const [selectedMember, setSelectedMember] = useState(null);
  const [selectedRoles, setSelectedRoles] = useState([]);
  const [currentDiscordRoles, setCurrentDiscordRoles] = useState([]);
  const [nickname, setNickname] = useState('');
  const [chapter, setChapter] = useState('');
  const [title, setTitle] = useState('');
  const [loading, setLoading] = useState(true);
  const [promoting, setPromoting] = useState(false);
  const [updatingNickname, setUpdatingNickname] = useState(false);
  const [updatingMemberInfo, setUpdatingMemberInfo] = useState(false);
  const [hasPermission, setHasPermission] = useState(null);

  // Check permission on mount
  const [userChapter, setUserChapter] = useState(null);
  
  useEffect(() => {
    const checkPermission = async () => {
      try {
        const response = await axios.get(`${BACKEND_URL}/api/auth/verify`, { 
          headers: { Authorization: `Bearer ${token}` } 
        });
        const perms = response.data?.permissions || {};
        if (!perms.view_promotions) {
          toast.error('You do not have permission to access this page');
          navigate('/');
          return;
        }
        setHasPermission(true);
        setUserChapter(response.data?.chapter || null);
      } catch (error) {
        console.error('Error checking permission:', error);
        navigate('/login');
      }
    };
    checkPermission();
  }, [token, navigate]);

  // Fetch members and Discord roles on mount
  useEffect(() => {
    if (!hasPermission) return;
    
    const fetchData = async () => {
      try {
        const [membersRes, rolesRes] = await Promise.all([
          axios.get(`${BACKEND_URL}/api/members`, { headers: { Authorization: `Bearer ${token}` } }),
          axios.get(`${BACKEND_URL}/api/discord/roles`, { headers: { Authorization: `Bearer ${token}` } })
        ]);
        
        let membersList = membersRes.data || [];
        
        // Filter members by chapter if user is not National
        if (userChapter && userChapter !== 'National') {
          membersList = membersList.filter(m => m.chapter === userChapter);
        }
        
        setMembers(membersList);
        setDiscordRoles(rolesRes.data?.roles || []);
      } catch (error) {
        console.error('Error fetching data:', error);
        toast.error('Failed to load data');
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [token, hasPermission, userChapter]);

  // Show loading while checking permission
  if (hasPermission === null) {
    return (
      <PageLayout title="Member Promotion">
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        </div>
      </PageLayout>
    );
  }

  // When member is selected, fetch their current Discord roles
  const handleMemberSelect = async (memberId) => {
    setSelectedMemberId(memberId);
    const member = members.find(m => m.id === memberId);
    setSelectedMember(member);
    setSelectedRoles([]);
    setCurrentDiscordRoles([]);
    setNickname(member?.handle || '');
    setChapter(member?.chapter || '');
    setTitle(member?.title || '');
    
    if (memberId) {
      try {
        const response = await axios.get(
          `${BACKEND_URL}/api/discord/member/${memberId}/roles`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        
        if (response.data?.roles) {
          setCurrentDiscordRoles(response.data.roles);
          setSelectedRoles(response.data.roles.map(r => r.id));
        }
        if (response.data?.nickname) {
          setNickname(response.data.nickname);
        }
      } catch (error) {
        console.error('Error fetching member Discord info:', error);
        // Member might not be linked to Discord yet
      }
    }
  };

  // Toggle role selection
  const toggleRole = (roleId) => {
    setSelectedRoles(prev => 
      prev.includes(roleId) 
        ? prev.filter(id => id !== roleId)
        : [...prev, roleId]
    );
  };

  // Promote member - update their Discord roles
  const handlePromote = async () => {
    if (!selectedMemberId) {
      toast.error('Please select a member');
      return;
    }
    
    setPromoting(true);
    try {
      const response = await axios.post(
        `${BACKEND_URL}/api/discord/member/${selectedMemberId}/roles`,
        { role_ids: selectedRoles },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      if (response.data?.success) {
        toast.success(response.data.message || 'Roles updated successfully');
        // Refresh current roles
        handleMemberSelect(selectedMemberId);
      } else {
        toast.error(response.data?.message || 'Failed to update roles');
      }
    } catch (error) {
      console.error('Error updating roles:', error);
      toast.error(error.response?.data?.detail || 'Failed to update Discord roles');
    } finally {
      setPromoting(false);
    }
  };

  // Update Discord nickname
  const handleUpdateNickname = async () => {
    if (!selectedMemberId || !nickname.trim()) {
      toast.error('Please select a member and enter a nickname');
      return;
    }
    
    setUpdatingNickname(true);
    try {
      const response = await axios.post(
        `${BACKEND_URL}/api/discord/member/${selectedMemberId}/nickname`,
        { nickname: nickname.trim() },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      if (response.data?.success) {
        toast.success(response.data.message || 'Nickname updated successfully');
      } else {
        toast.error(response.data?.message || 'Failed to update nickname');
      }
    } catch (error) {
      console.error('Error updating nickname:', error);
      toast.error(error.response?.data?.detail || 'Failed to update Discord nickname');
    } finally {
      setUpdatingNickname(false);
    }
  };

  // Update member chapter and title in database
  const handleUpdateMemberInfo = async () => {
    if (!selectedMemberId) {
      toast.error('Please select a member');
      return;
    }
    
    if (!chapter || !title) {
      toast.error('Please select both chapter and title');
      return;
    }
    
    setUpdatingMemberInfo(true);
    try {
      const response = await axios.put(
        `${BACKEND_URL}/api/members/${selectedMemberId}`,
        { chapter, title },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      if (response.data) {
        toast.success(`Member updated to ${chapter} ${title}`);
        // Update local state
        setSelectedMember(prev => ({ ...prev, chapter, title }));
        // Refresh members list
        const membersRes = await axios.get(`${BACKEND_URL}/api/members`, { headers: { Authorization: `Bearer ${token}` } });
        let membersList = membersRes.data || [];
        // Re-apply chapter filter after refresh
        if (userChapter && userChapter !== 'National') {
          membersList = membersList.filter(m => m.chapter === userChapter);
        }
        setMembers(membersList);
      }
    } catch (error) {
      console.error('Error updating member info:', error);
      toast.error(error.response?.data?.detail || 'Failed to update member info');
    } finally {
      setUpdatingMemberInfo(false);
    }
  };

  // Sort roles by position (higher position = more important)
  const sortedRoles = [...discordRoles].sort((a, b) => b.position - a.position);

  return (
    <PageLayout title="Member Promotion">
      <div className="space-y-6">
        {/* Back Button */}
        <Button 
          variant="outline" 
          onClick={() => navigate('/')}
          className="mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Dashboard
        </Button>

        {/* Chapter Scope Indicator */}
        {userChapter && userChapter !== 'National' && (
          <div className="p-3 bg-blue-900/30 border border-blue-600/50 rounded-lg">
            <p className="text-blue-300 text-sm flex items-center gap-2">
              <Building className="w-4 h-4" />
              You can only manage members in the <span className="font-semibold">{userChapter}</span> chapter
            </p>
          </div>
        )}

        {/* Member Selection */}
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Users className="w-5 h-5" />
              Select Member
            </CardTitle>
            <CardDescription>
              {userChapter === 'National' 
                ? 'Choose a member to manage their Discord roles and nickname'
                : `Choose a ${userChapter} member to manage their Discord roles and nickname`
              }
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Select value={selectedMemberId} onValueChange={handleMemberSelect}>
              <SelectTrigger className="bg-slate-700 border-slate-600 text-white" data-testid="member-select">
                <SelectValue placeholder="Select a member..." />
              </SelectTrigger>
              <SelectContent className="bg-slate-700 border-slate-600 max-h-[300px]">
                {members.map(member => (
                  <SelectItem 
                    key={member.id} 
                    value={member.id}
                    className="text-white hover:bg-slate-600"
                  >
                    {member.handle} - {member.chapter} {member.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            {selectedMember && (
              <div className="mt-4 p-3 bg-slate-700/50 rounded-lg">
                <p className="text-white font-medium">{selectedMember.handle}</p>
                <p className="text-slate-400 text-sm">
                  {selectedMember.chapter} - {selectedMember.title}
                </p>
                {selectedMember.name && (
                  <p className="text-slate-400 text-sm">{selectedMember.name}</p>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Nickname Management */}
        {selectedMemberId && (
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Award className="w-5 h-5" />
                Discord Nickname
              </CardTitle>
              <CardDescription>
                Update the member's display name in Discord
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-3">
                <Input
                  value={nickname}
                  onChange={(e) => setNickname(e.target.value)}
                  placeholder="Enter Discord nickname..."
                  className="bg-slate-700 border-slate-600 text-white flex-1"
                  data-testid="nickname-input"
                />
                <Button 
                  onClick={handleUpdateNickname}
                  disabled={updatingNickname}
                  className="bg-blue-600 hover:bg-blue-700"
                  data-testid="update-nickname-btn"
                >
                  {updatingNickname ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      <Save className="w-4 h-4 mr-2" />
                      Update Nickname
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Chapter & Title Management */}
        {selectedMemberId && (
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <UserCog className="w-5 h-5" />
                Chapter & Title
              </CardTitle>
              <CardDescription>
                Update the member's chapter and title in the system database
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-slate-300">Chapter</Label>
                  <Select value={chapter} onValueChange={setChapter}>
                    <SelectTrigger className="bg-slate-700 border-slate-600 text-white" data-testid="chapter-select">
                      <SelectValue placeholder="Select chapter..." />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-700 border-slate-600">
                      {CHAPTERS.map(ch => (
                        <SelectItem key={ch} value={ch} className="text-white hover:bg-slate-600">
                          {ch}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label className="text-slate-300">Title</Label>
                  <Select value={title} onValueChange={setTitle}>
                    <SelectTrigger className="bg-slate-700 border-slate-600 text-white" data-testid="title-select">
                      <SelectValue placeholder="Select title..." />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-700 border-slate-600">
                      {TITLES.map(t => (
                        <SelectItem key={t} value={t} className="text-white hover:bg-slate-600">
                          {t}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              {(chapter !== selectedMember?.chapter || title !== selectedMember?.title) && (
                <div className="mt-4 p-3 bg-amber-900/30 border border-amber-600/50 rounded-lg">
                  <p className="text-amber-300 text-sm">
                    Changing from <span className="font-medium">{selectedMember?.chapter} {selectedMember?.title}</span> to <span className="font-medium">{chapter} {title}</span>
                  </p>
                </div>
              )}
              
              <div className="mt-4 flex justify-end">
                <Button 
                  onClick={handleUpdateMemberInfo}
                  disabled={updatingMemberInfo || (chapter === selectedMember?.chapter && title === selectedMember?.title)}
                  className="bg-amber-600 hover:bg-amber-700 disabled:bg-slate-600"
                  data-testid="update-member-info-btn"
                >
                  {updatingMemberInfo ? (
                    <RefreshCw className="w-4 h-4 animate-spin mr-2" />
                  ) : (
                    <Save className="w-4 h-4 mr-2" />
                  )}
                  {updatingMemberInfo ? 'Updating...' : 'Update Chapter & Title'}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Discord Roles */}
        {selectedMemberId && (
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Shield className="w-5 h-5" />
                Discord Roles
              </CardTitle>
              <CardDescription>
                Select the roles to assign to this member. Current roles are pre-selected.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {currentDiscordRoles.length > 0 && (
                <div className="mb-4">
                  <Label className="text-slate-400 text-sm">Current Roles:</Label>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {currentDiscordRoles.map(role => (
                      <Badge 
                        key={role.id} 
                        style={{ backgroundColor: role.color || '#5865F2' }}
                        className="text-white"
                      >
                        {role.name}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 max-h-[400px] overflow-y-auto p-2">
                {sortedRoles.map(role => (
                  <div
                    key={role.id}
                    className={`flex items-center space-x-2 p-2 rounded-lg border cursor-pointer transition-all ${
                      selectedRoles.includes(role.id)
                        ? 'bg-blue-900/50 border-blue-500'
                        : 'bg-slate-700/50 border-slate-600 hover:border-slate-500'
                    }`}
                    onClick={() => toggleRole(role.id)}
                  >
                    <Checkbox
                      checked={selectedRoles.includes(role.id)}
                      onCheckedChange={() => toggleRole(role.id)}
                      className="border-slate-400"
                    />
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <div 
                        className="w-3 h-3 rounded-full flex-shrink-0"
                        style={{ backgroundColor: role.color || '#99AAB5' }}
                      />
                      <span className="text-sm text-white truncate">{role.name}</span>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="mt-6 flex justify-end">
                <Button 
                  onClick={handlePromote}
                  disabled={promoting}
                  className="bg-green-600 hover:bg-green-700"
                  data-testid="promote-btn"
                >
                  {promoting ? (
                    <RefreshCw className="w-4 h-4 animate-spin mr-2" />
                  ) : (
                    <Award className="w-4 h-4 mr-2" />
                  )}
                  {promoting ? 'Updating Roles...' : 'Update Discord Roles'}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {loading && (
          <div className="text-center py-8">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto text-blue-500" />
            <p className="text-slate-400 mt-2">Loading...</p>
          </div>
        )}
      </div>
    </PageLayout>
  );
}
