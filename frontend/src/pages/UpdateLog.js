import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Clock, CheckCircle } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function UpdateLog() {
  const navigate = useNavigate();

  const updates = [
    {
      version: "v5.6",
      date: "December 27, 2025",
      changes: [
        "National Privacy: National chapter members are now hidden from non-National users in the member database",
        "Access Control: Non-National users cannot view individual National member profiles",
        "CSV Export: National members excluded from exports for non-National users",
        "Security Patch: Fixed NoSQL injection vulnerability in dues payment endpoint",
        "Input Sanitization: Added regex escaping for all user-supplied search patterns"
      ]
    },
    {
      version: "v5.5",
      date: "December 27, 2025",
      changes: [
        "Store Admin Management: Primary admins (Prez, VP, SEC) can now delegate store management access to other National members",
        "Dynamic Permission System: New async permission checker supports both primary and delegated store admins",
        "Auto-Sync on Login: Square catalog automatically syncs when any user logs in (runs in background)",
        "New Items Hidden by Default: Products synced from Square are hidden from Supporter Store until admin enables them",
        "Store Admin UI: New management card in Settings tab to add/remove delegated store admins",
        "Square Webhook Security: Added signature verification key for webhook authentication",
        "Supporter Store Button: Moved to top of login page for better visibility",
        "Login Page Cleanup: Removed 'browse merchandise without logging in' text"
      ]
    },
    {
      version: "v5.1",
      date: "December 25, 2025",
      changes: [
        "Wall of Honor: New memorial page to honor fallen brothers with photo upload, tribute messages, and service badges",
        "Photo Upload: Direct image upload for memorials (stored as base64 for deployment persistence)",
        "Chapter Tabs: Members page now has tabs to filter by chapter (All, National, AD, HA, HS) with member counts",
        "Support Form: New support request form on login page - sends email directly to support@boh2158.org with reply-to functionality",
        "Honorary Title: Added 'Honorary' as a new title option for members",
        "Member Count Badge: Dashboard now shows total member count that updates dynamically",
        "Discord Analytics Mobile: Fully responsive design for mobile, tablet, and desktop",
        "Timezone Fix: All Discord Analytics times now correctly display in Central Time (CST)",
        "First Responder Simplified: Single checkbox for first responder status instead of three separate fields",
        "Trucker Club Branding: Updated Wall of Honor messaging for trucker club context"
      ]
    },
    {
      version: "v.2.3",
      date: "November 8, 2025",
      changes: [
        "CSV Export Overhaul: Complete redesign as dedicated React page component (/export-view route)",
        "Print Custom Feature: New customizable print functionality with column selection",
        "Quick Presets: Added 4 preset options - All Fields, Contact Info, Dues Tracking, Meeting Attendance",
        "Export View UI: Modern responsive interface with stats display (members, columns, filtered count)",
        "Search & Filter: Real-time search across all member data in export view",
        "View Toggle: Switch between formatted table view and raw CSV text view",
        "Export Options: Download CSV, Print All, Print Custom, and Google Sheets export",
        "Google Sheets Integration: One-click copy to clipboard and auto-open Google Sheets",
        "Print Optimization: Landscape orientation with proper column sizing for all print outputs",
        "Browser Security Fix: Resolved dynamic script execution issues by using proper React routing",
        "Performance Improvement: Eliminated window.open() security blocks with native React components",
        "Backend Verified: CSV API endpoint confirmed working with all 24 members and 69 columns"
      ]
    },
    {
      version: "v.2.2",
      date: "November 5, 2025",
      changes: [
        "Privacy Feature: Reimplemented member privacy controls - phone and address can be marked private",
        "National Admin Access: Only National Chapter admins can see private contact information",
        "JWT Enhancement: Added chapter field to authentication tokens for proper access control",
        "Privacy Logic: Non-National admins, members, and prospects see 'Private' text for private fields",
        "Password Change Fix: Resolved 500 error - now properly uses hash_password helper function",
        "Password Security: All password changes properly validated (8-char minimum) and bcrypt hashed",
        "Activity Logging: Password changes logged in audit trail with admin and target user details",
        "Default Admin Setup: Fixed required email field and added all permissions including meeting_attendance",
        "Deployment Fixes: Resolved module import issues, added comprehensive logging for production debugging",
        "Scheduler Optimization: Moved APScheduler to startup event with fault-tolerant error handling"
      ]
    },
    {
      version: "v.2.1",
      date: "November 4, 2025",
      changes: [
        "Event Calendar: Complete event management system with date, time, location, description, chapter and title filtering",
        "Event Badge Counter: Green badge on Dashboard shows upcoming events count, auto-refreshes every 30 seconds",
        "Event Detail View: Click any event for large, comprehensive view with all details and metadata",
        "Discord Integration: Automatic notifications sent to Discord 24 hours and 3 hours before events",
        "Discord Toggle: Per-event checkbox to enable/disable Discord notifications (checked by default)",
        "Send Now Button: Green send button in table and detail view to manually trigger Discord notifications",
        "Discord Embeds: Rich formatted notifications with color coding (green=24h, orange=3h, blue=manual)",
        "User Email Field: Added required email field to all users with validation and uniqueness check",
        "Chapter & Title Assignment: Assign chapters (National, AD, HA, HS) and titles (Prez, VP, S@A, etc.) to users",
        "User Management Columns: Added Email, Chapter, and Title columns to user management table",
        "Chatbot Optimization: Fully responsive design - full screen on mobile, floating corner on tablets/desktops",
        "Mobile-First Design: Touch-friendly buttons, optimized text sizes, and proper padding for all screen sizes"
      ]
    },
    {
      version: "v.2.0",
      date: "November 1, 2025",
      changes: [
        "Rebranding: Updated from 'Member Directory' to 'Member Management' to reflect comprehensive management capabilities",
        "Bulk Promotion: Added ability to promote multiple prospects to members simultaneously with chapter/title assignment",
        "Checkbox Improvements: Enhanced visibility with green checkmarks and better border styling on dark theme",
        "Dynamic Bulk Button: 'Bulk Promote (X)' button appears automatically when prospects are selected",
        "Prospects Dark Theme: Fixed all UI elements on Prospects page to conform to application-wide dark theme",
        "Chatbot Repositioning: Moved AI assistant icon higher (bottom-20) to prevent overlap with action buttons",
        "Backend Testing: Comprehensive bulk promotion endpoint testing completed (50/50 tests passed)",
        "Selection System: Master checkbox in header for select all/none functionality with individual row checkboxes"
      ]
    },
    {
      version: "v.1.9",
      date: "November 4, 2025",
      changes: [
        "DOB & Join Date: Added optional Date of Birth and Join Date fields to member and prospect profiles",
        "Actions History: Comprehensive tracking system for merit awards, promotions, and disciplinary actions (admin-only)",
        "Actions UI: FileText button opens dialog to view history and add new actions with type, date, and description",
        "Archive System: Members/prospects now archived (not deleted) with mandatory reason and complete metadata",
        "Archive Manager: New 'Archived' button in User Management displays all archived records with deletion details",
        "Restore/Undo: Green restore button on archived records moves them back to active status with one click",
        "Archive Export: CSV export for archived members and prospects including all metadata and deletion reason",
        "CST Timestamps: All archived records display date and time in Central Standard Time (e.g., 'Oct 28, 2025, 3:45 PM CST')",
        "CSV Decryption: Fixed all CSV exports to show actual readable data instead of encrypted values",
        "Phone Formatting: All phone numbers automatically formatted to (xxx) xxx-xxxx format throughout application"
      ]
    },
    {
      version: "v.1.8b",
      date: "November 3, 2025",
      changes: [
        "Prospect Promotion: Added green promotion button to move prospects to members directory with chapter and title selection",
        "Member Analytics: Added Analytics button and dialog to User Management showing total members and breakdown by chapter",
        "Promotion Dialog: Select chapter (National, AD, HA, HS) and title when promoting prospects to members",
        "Privacy Fix: Corrected field name mismatch (phone_private/address_private) for proper privacy functionality",
        "Automatic Migration: Prospect data including meeting attendance automatically copied when promoted to member",
        "Activity Logging: All prospect promotions logged in system activity log for audit trail"
      ]
    },
    {
      version: "v.1.8a",
      date: "November 2, 2025",
      changes: [
        "Contact Privacy: Added checkboxes to make phone numbers and addresses private when creating/editing members",
        "Privacy Controls: Private contact info hidden from non-admin users (replaced with 'Private' text)",
        "Admin Access: Admins can always view all contact information regardless of privacy settings",
        "Enhanced Security: Member-level granular control over phone and address visibility"
      ]
    },
    {
      version: "v.1.8",
      date: "November 1, 2025",
      changes: [
        "3-Role System: Implemented Admin, Member (previously User), and Prospect roles with distinct access levels",
        "Password Management: Admins can now change passwords for any system user with 8+ character validation",
        "Prospect Restrictions: Limited contact access - names hidden, can only message HA chapter officers",
        "Messaging Controls: Prospects restricted to contact HA President, VP, S@A, Secretary, and Prospect Manager only",
        "Role Migration: All existing 'user' accounts automatically converted to 'member' role",
        "Invite System: Updated to support inviting users with prospect role",
        "Chatbot Clarification: Prospect Manager position exists only in Highway Asylum chapter"
      ]
    },
    {
      version: "v.1.7d",
      date: "October 31, 2025",
      changes: [
        "Chain of Command Access: CoC structure and all officer positions now available to all users (not just admins)",
        "Enhanced Transparency: All members can now see National and Chapter officer names and positions",
        "HAPM Position Correction: Highway Asylum Prospect Manager properly positioned after Secretary in CoC",
        "Improved Chatbot Access: Better information availability while keeping detailed officer bylaws admin-only"
      ]
    },
    {
      version: "v.1.7c",
      date: "October 31, 2025",
      changes: [
        "General Rules of Order: Added complete officer bylaws to chatbot (7 articles covering all officer regulations)",
        "Role-Based Chatbot Access: Officer information, chain of command, and bylaws now restricted to admin users only",
        "Enhanced Security: Regular users see organization overview, mission, and public information only",
        "Comprehensive Officer Rules: Includes observation periods, disciplinary process, resignation procedures, and all officer expectations"
      ]
    },
    {
      version: "v.1.7b",
      date: "October 31, 2025",
      changes: [
        "Chapter Officers Integration: Added Highway Souls (HS) and Asphalt Demons (AD) chapter leadership to chatbot",
        "National Support Positions: Added Club Chaplain (CC), Club Media Director (CMD), and Club Counselor & Life Coach (CCLC)",
        "Complete Leadership Coverage: Chatbot can now answer questions about all chapter officers and national support roles",
        "Enhanced Knowledge Base: Comprehensive organizational structure information for all BOH chapters"
      ]
    },
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
