import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Clock, CheckCircle } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function UpdateLog() {
  const navigate = useNavigate();

  const updates = [
    {
      version: "v.1.7a",
      date: "October 30, 2025",
      changes: [
        "Meeting Attendance Colors: Updated to traffic light system - Present (Green), Excused (Orange), Unexcused (Red)",
        "Visual Clarity: Improved meeting attendance tracking with clear color-coded status indicators",
        "Highway Asylum Officers: Added HA chapter leadership to AI chatbot knowledge base",
        "Enhanced Chatbot: Can now answer questions about Highway Asylum chapter officers and structure"
      ]
    },
    {
      version: "v.1.7",
      date: "October 30, 2025",
      changes: [
        "AI Chatbot Assistant: Floating chat icon on all pages for BOH knowledge assistance",
        "Comprehensive Knowledge Base: Answers questions about bylaws, officers, prospects, meetings, Chain of Command, and more",
        "BOH Expertise: Trained on officers bylaws, SOPs, prospect bylaws, mission statement, and logo meanings",
        "Real-time Notifications: Pop-up alerts when new private messages are received while logged in",
        "Message Alerts: Non-intrusive notifications with direct navigation to Messages page",
        "Auto-refresh: Message count updates every 30 seconds across all pages"
      ]
    },
    {
      version: "v.1.6b",
      date: "October 30, 2025",
      changes: [
        "User-to-User Messaging: All users can now send private messages to any other user in the system",
        "Support Simplified: Replaced in-app support form with direct email link on login page",
        "Email Contact: Support link now opens default email client to supp.boh2158@gmail.com",
        "Navigation Cleanup: Streamlined dashboard navigation for improved user experience",
        "User Experience: Simplified support contact method for easier accessibility"
      ]
    },
    {
      version: "v.1.6a",
      date: "October 30, 2025",
      changes: [
        "Resend Invite Feature: Admins can resend invitation emails for pending invites directly from the Manage Invites dialog",
        "Resend Button UI: Blue mail icon button appears next to delete button for unused, non-expired invites only",
        "Email Validation Fix: Resolved Pydantic validation error that prevented regular users from loading members",
        "Contact Restriction Enhancement: Fixed email format for restricted National chapter contact info (admin-only access)",
        "Invite Management: Improved invite workflow with visual indicators for pending, used, and expired invites",
        "Activity Logging: Resend invite actions are now logged in the activity log for audit purposes"
      ]
    },
    {
      version: "v.1.6",
      date: "October 30, 2025",
      changes: [
        "Session Management: Added automatic logout on token expiration with clear user notification",
        "Error Handling: Improved API error handling with user-friendly messages",
        "Navigation Layout: Moved Logout button to far right for better visual hierarchy",
        "UI Text Update: Changed 'Update Log' to 'Change Log' throughout the application"
      ]
    },
    {
      version: "v.1.5d",
      date: "October 29, 2025",
      changes: [
        "Support Message Center: Interactive support button on login page for user inquiries (no login required)",
        "Lonestar Support Dashboard: Dedicated support center accessible only to user 'Lonestar' for managing messages",
        "Email Reply System: Support messages can be replied to via email with automatic status tracking",
        "Export Support Messages: CSV export functionality for all support message history",
        "Bulk Message Management: Clear all closed/replied messages at once with confirmation",
        "Individual Message Deletion: Delete specific support messages with confirmation dialog",
        "Support Counter Badge: Real-time badge on Support button showing count of open messages",
        "Button Text Consistency: All buttons now use white text for better readability",
        "About Text Update: Changed 'motorcycle club organizations' to 'Brothers of the Highway TC'",
        "Export Button Enhancement: Made Export CSV buttons more visually prominent with green styling"
      ]
    },
    {
      version: "v.1.5c",
      date: "October 29, 2025",
      changes: [
        "UI Consistency: Standardized all button styling across the application for uniform appearance",
        "Navigation Rename: Changed 'Manage Users' button to 'Admin' for clearer identification",
        "Menu Standardization: All navigation buttons now use consistent outline styling",
        "Action Button Uniformity: Export CSV, Invite User, and other action buttons now have matching styles"
      ]
    },
    {
      version: "v.1.5b",
      date: "October 29, 2025",
      changes: [
        "Enhanced Dues Tracking: Added 3-state system (Paid/Unpaid/Late) with notes for late payments",
        "Private Messaging: Added user-to-user private messaging with archive and delete options",
        "Archive Conversations: Users can archive conversations instead of permanently deleting",
        "Regular Users Can Message Admins: Non-admin users can now initiate messages to administrators",
        "CSV Export Enhanced: Dues export now includes status and late payment notes",
        "Version Display: Added version number to login page",
        "Removed Admin Group Chat: Simplified to private messaging only",
        "Deployment Health Check: Verified application ready for production deployment"
      ]
    },
    {
      version: "v.1.4",
      date: "October 28, 2025",
      changes: [
        "Dark Theme: Complete dark mode redesign for all pages",
        "Custom Logo: Added Brothers of the Highway logo to login page",
        "Activity Log: Admins can view system activity and user actions",
        "Manage Invites: Admins can view and manage invitation links",
        "Close Button Fix: Fixed dialog close button positioning",
        "Enhanced Error Logging: Added detailed console logging for debugging"
      ]
    },
    {
      version: "v.1.3",
      date: "October 28, 2025",
      changes: [
        "Meeting Dates Display: Shows 1st and 3rd Wednesday dates for each month",
        "Meeting Attendance Notes: Added notes for excused and unexcused absences",
        "Multi-Year Tracking: Support for tracking attendance across multiple years",
        "Prospects Module: Separate Hangarounds/Prospects tracking with attendance",
        "Prospects CSV Export: Independent export for prospects data"
      ]
    },
    {
      version: "v.1.2",
      date: "October 28, 2025",
      changes: [
        "Email Invitations: Admins can invite new users via email",
        "Multi-Year Dues: Track dues across multiple years",
        "Meeting Attendance: Track attendance for 1st and 3rd Wednesday meetings",
        "Responsive Design: Mobile-friendly interface for all devices",
        "Support Link: Added support email link on login page"
      ]
    },
    {
      version: "v.1.1",
      date: "October 28, 2025",
      changes: [
        "Role-Based Permissions: Granular permissions for viewing member data",
        "User Management: Admin interface for managing users and roles",
        "CSV Export: Export member data with permission-based filtering",
        "Search Functionality: Search members by name, handle, or chapter",
        "Contact Links: Clickable email, phone, and address links"
      ]
    },
    {
      version: "v.1.0",
      date: "October 27, 2025",
      changes: [
        "Initial Release: Brothers of the Highway Member Directory",
        "Member Management: CRUD operations for member data",
        "Authentication: Secure JWT-based login system",
        "Chapter Organization: Members organized by National, AD, HA, HS",
        "Title Hierarchy: Support for all organizational titles",
        "Basic Contact Info: Name, email, phone, address tracking"
      ]
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <nav className="bg-slate-800 border-b border-slate-700 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-2 sm:gap-4">
              <Button
                onClick={() => navigate("/")}
                variant="outline"
                size="sm"
                className="flex items-center gap-1 sm:gap-2 border-slate-600 text-slate-200 hover:bg-slate-700"
              >
                <ArrowLeft className="w-3 h-3 sm:w-4 sm:h-4" />
                <span className="hidden sm:inline">Back</span>
              </Button>
              <div className="flex items-center gap-2">
                <Clock className="w-5 h-5 sm:w-6 sm:h-6 text-blue-400" />
                <h1 className="text-lg sm:text-2xl font-bold text-slate-100">Change Log</h1>
              </div>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-4 sm:py-8">
        <div className="space-y-6">
          {updates.map((update, index) => (
            <div
              key={index}
              className="bg-slate-800 rounded-xl shadow-xl border border-slate-700 p-6"
            >
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-xl font-bold text-slate-100">{update.version}</h2>
                  <p className="text-sm text-slate-400">{update.date}</p>
                </div>
                {index === 0 && (
                  <span className="bg-blue-600 text-white text-xs font-bold px-3 py-1 rounded-full">
                    Latest
                  </span>
                )}
              </div>

              <div className="space-y-2">
                {update.changes.map((change, changeIndex) => (
                  <div
                    key={changeIndex}
                    className="flex items-start gap-3 text-slate-200"
                  >
                    <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                    <p className="text-sm">{change}</p>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-8 bg-slate-800 rounded-xl shadow-xl border border-slate-700 p-6">
          <h3 className="text-lg font-bold text-slate-100 mb-3">About This Application</h3>
          <p className="text-sm text-slate-300 mb-3">
            The Brothers of the Highway Member Directory is a comprehensive member management system 
            designed specifically for Brothers of the Highway TC. It provides secure, role-based access 
            to member information, attendance tracking, dues management, and communication tools.
          </p>
          <div className="flex flex-wrap gap-2">
            <span className="bg-slate-700 text-slate-300 text-xs px-3 py-1 rounded-full">
              React
            </span>
            <span className="bg-slate-700 text-slate-300 text-xs px-3 py-1 rounded-full">
              FastAPI
            </span>
            <span className="bg-slate-700 text-slate-300 text-xs px-3 py-1 rounded-full">
              MongoDB
            </span>
            <span className="bg-slate-700 text-slate-300 text-xs px-3 py-1 rounded-full">
              JWT Auth
            </span>
            <span className="bg-slate-700 text-slate-300 text-xs px-3 py-1 rounded-full">
              Role-Based Permissions
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
