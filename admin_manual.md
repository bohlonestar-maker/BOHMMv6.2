# BOH Hub - Administrator Manual

## Version 2.0 | February 2026

---

# Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Member Management](#member-management)
4. [Dues Management](#dues-management)
5. [Square Payment Integration](#square-payment-integration)
6. [Discord Integration](#discord-integration)
7. [Prospects & Hangarounds](#prospects--hangarounds)
8. [Officer Tracking](#officer-tracking)
9. [Meeting Management](#meeting-management)
10. [Analytics & Reports](#analytics--reports)
11. [System Administration](#system-administration)

---

# Getting Started

## Logging In

1. Navigate to the application URL
2. Enter your **Username** and **Password**
3. Click **Sign In**

## User Roles

| Role | Access Level |
|------|-------------|
| **Admin** | Full system access, all features |
| **National Officer** | Chapter management, dues, officer tracking |
| **Chapter Officer** | Limited to own chapter members |
| **Member** | View own profile and dues only |

## Navigation

The main navigation menu includes:
- **Dashboard** - Home page with overview
- **Members** - Member directory
- **Prospects** - Prospect and Hangaround management
- **Officer Tracking** - Dues and reminders
- **Meeting Manager** - Meeting scheduling
- **Discord Analytics** - Voice/text activity
- **Admin** - System settings (Admin only)

---

# Dashboard Overview

The Dashboard provides a quick overview of:

### My Dues Section
- Current month dues status
- Recent payment history
- Year-at-a-glance calendar showing paid/unpaid months

### Quick Stats
- Total active members
- Upcoming birthdays
- Upcoming anniversaries
- Recent activity

### Member Directory
- Searchable list of all members
- Quick access to member profiles
- Filter by chapter

---

# Member Management

## Adding a New Member

1. Click **Add Member** button on Dashboard
2. Fill in required fields:
   - **Handle** (Discord/display name)
   - **Name** (Legal name - encrypted)
   - **Email** (encrypted)
   - **Phone** (encrypted)
   - **Chapter**
   - **Title/Role**
   - **Join Date** (MM/YYYY format)
   - **Birthday** (MM/DD format)
3. Click **Save**

## Editing a Member

1. Find member in the directory
2. Click the **three-dot menu** (⋮)
3. Select **Edit**
4. Update fields as needed
5. Click **Save Changes**

## Archiving a Member

When a member leaves the organization:

1. Click the **three-dot menu** (⋮) on the member
2. Select **Archive**
3. Enter a **deletion reason**
4. Optional: Check **"Also kick from Discord server"**
5. Optional: Check **"Cancel Square subscription"** (checked by default)
6. Click **Archive Member**

The member will be moved to the Archived Members section and can be restored if needed.

## Member Profile Fields

| Field | Description | Encrypted |
|-------|-------------|-----------|
| Handle | Discord/display name | No |
| Name | Legal full name | Yes |
| Email | Contact email | Yes |
| Phone | Phone number | Yes |
| Address | Mailing address | Yes |
| Chapter | Chapter assignment | No |
| Title | Role in organization | No |
| Join Date | MM/YYYY membership start | No |
| Birthday | MM/DD for notifications | No |

---

# Dues Management

## Understanding Dues Status

Each month can have one of these statuses:
- **Paid** (Green) - Payment confirmed
- **Unpaid** (Gray) - No payment recorded
- **Suspended** (Red) - Member suspended for non-payment

## Viewing Member Dues

1. Go to **Officer Tracking**
2. Click the **Dues** tab
3. Select a month from the dropdown
4. View all members and their dues status

## Manually Updating Dues

1. Find the member in the Dues tab
2. Click **Update** next to their name
3. Select the new status (Paid/Unpaid)
4. Add optional notes
5. Click **Save**

## Dues Reminders

The system automatically sends email reminders:
- **Day 3**: First reminder
- **Day 8**: Second reminder  
- **Day 10**: Final warning before suspension

### Configuring Reminder Templates

1. Go to **Officer Tracking** → **Dues** tab
2. Click **Edit Templates**
3. Modify the email subject and body
4. Use placeholders: `{member_name}`, `{month}`, `{amount}`
5. Click **Save**

## Dues Extensions

To grant a member extra time to pay:

1. Find the member in the Dues list
2. Click **Grant Extension**
3. Select the extension end date
4. Enter a reason
5. Click **Confirm**

---

# Square Payment Integration

## Automatic Sync

The system automatically syncs with Square every hour to:
- Match subscription payments to members
- Update dues status for paid months
- Track one-time payments

## Manual Sync

To force an immediate sync:

1. Go to **Officer Tracking** → **Dues** tab
2. Click **Sync Square**
3. Wait for the sync to complete
4. Review any unmatched payments

## Viewing Subscriptions

1. Click **View Subscriptions** in the Dues tab
2. See two sections:
   - **Matched Subscriptions** - Linked to members
   - **Unmatched Subscriptions** - Need manual linking

## Linking Unmatched Subscriptions

1. Find the unmatched subscription
2. Click **Link**
3. Select the member from the dropdown
4. Click **Confirm**

## Cancelling Unmatched Subscriptions

For subscriptions belonging to former members:

1. Find the unmatched subscription
2. Click **Cancel**
3. Confirm the cancellation
4. The subscription will be cancelled in Square

## Payment Types

| Type | Description |
|------|-------------|
| **Monthly Subscription** | $30/month recurring |
| **6-Month Prepay** | $180 one-time |
| **Annual Prepay** | $330 one-time |

---

# Discord Integration

## Discord Bot Features

The integrated Discord bot provides:
- Birthday notifications
- Anniversary notifications
- Voice channel tracking
- Text activity logging
- Role-based permissions

## Birthday/Anniversary Notifications

Automatic notifications are sent to a designated Discord channel:
- **Birthdays**: Posted on the member's birthday
- **Anniversaries**: Posted on the 1st of their join month

## Voice Activity Tracking

The bot tracks when members join voice channels:
- Duration in each channel
- Who else was in the channel
- Total monthly voice time

## Prospect Channel Analytics

Special tracking for "Prospect" voice channels:

1. Go to **Prospects** page
2. Click **Channel Analytics**
3. View:
   - Currently active users (live)
   - Time spent with each prospect
   - Historical session data

### Real-Time Tracking

The live view shows:
- Users currently in Prospect channels
- Live duration timers
- Which prospects are present
- Other members in the channel

## Discord Analytics Page

Access detailed Discord activity:

1. Go to **Discord Analytics** from the menu
2. View voice activity by member
3. View text activity by channel
4. Filter by date range

### Cleaning Up Analytics

To remove data for members who left Discord:

1. Go to Discord Analytics
2. Click **Cleanup Departed Members**
3. Confirm the action
4. Records for non-members will be removed

---

# Prospects & Hangarounds

## Understanding the Pipeline

The prospecting workflow has two stages:

1. **Hangaround** - Initial contact, minimal info required
2. **Prospect** - Full prospect with complete information

## Managing Hangarounds

### Adding a Hangaround

1. Go to **Prospects** page
2. Click the **Hangarounds** tab
3. Click **Add Hangaround**
4. Enter:
   - Handle (required)
   - Name (optional)
5. Click **Save**

### Tracking Hangaround Attendance

1. Find the hangaround in the list
2. Click the **attendance icon**
3. Mark meetings attended
4. View attendance history

### Promoting to Prospect

When ready to promote:

1. Click **Promote** on the hangaround
2. Fill in required prospect information:
   - Full Name
   - Email
   - Phone
   - Sponsor
3. Click **Confirm Promotion**

## Managing Prospects

### Adding a Prospect

1. Click the **Prospects** tab
2. Click **Add Prospect**
3. Fill in all required fields
4. Click **Save**

### Prospect Actions

Track prospect activities:
- Meetings attended
- Rides participated
- Events attended
- Custom actions

### Archiving Prospects

1. Click **Archive** on the prospect
2. Select a reason
3. Confirm archival

---

# Officer Tracking

## Dues Tab

Monitor and manage member dues:
- View dues by month
- Update payment status
- Grant extensions
- Send manual reminders

## Reminders Tab

View reminder history:
- See which reminders were sent
- Check delivery status
- Resend failed reminders

## Reports Tab

Access financial reports:
- Monthly payment summary
- Outstanding dues report
- Year-to-date collections

---

# Meeting Management

## Creating a Meeting

1. Go to **Meeting Manager**
2. Click **Schedule Meeting**
3. Enter:
   - Meeting name
   - Date and time
   - Location
   - Description
4. Click **Create**

## Taking Attendance

1. Open the meeting
2. Click **Take Attendance**
3. Check off members present
4. Add notes if needed
5. Click **Save Attendance**

## Viewing Meeting History

1. Go to Meeting Manager
2. Use the date filter to find past meetings
3. Click on a meeting to view details
4. See attendance records and notes

---

# Analytics & Reports

## Discord Analytics

Track member engagement through Discord:
- Voice channel participation
- Text message activity
- Most active members
- Quiet members needing outreach

## Prospect Channel Analytics

Detailed tracking for prospect interactions:
- Who visits prospect channels
- How long they stay
- Whether actual prospects were present
- Time breakdown per prospect

## Dues Reports

Financial tracking:
- Payment history
- Outstanding balances
- Subscription status
- One-time payments

---

# System Administration

## User Management

### Creating Admin Users

1. Go to **Admin** section
2. Click **Add User**
3. Enter username and password
4. Select role and permissions
5. Click **Create**

### Resetting Passwords

1. Find the user in Admin section
2. Click **Reset Password**
3. Enter new password
4. Click **Confirm**

## Data Cleanup

### Cleanup Duplicate Payment Notes

If payment notes show duplicates:

1. Contact system administrator
2. Run the cleanup endpoint
3. Duplicates will be removed

### Cleanup Discord Analytics

To remove data for departed members:

1. Go to Discord Analytics
2. Click admin cleanup option
3. Confirm removal

## Backup & Recovery

Member data is automatically backed up. To restore an archived member:

1. Go to **Archived Members**
2. Find the member
3. Click **Restore**
4. Member will be moved back to active

---

# Troubleshooting

## Common Issues

### Square Payments Not Syncing

1. Check Square API connection in Admin
2. Verify API keys are valid
3. Run manual sync
4. Check for unmatched payments

### Discord Bot Offline

1. Check Discord bot status
2. Verify bot token is valid
3. Check server permissions
4. Contact administrator

### Dues Status Incorrect

1. Verify Square payment sync
2. Check for manual overrides
3. Review payment notes
4. Contact SEC for correction

### Member Not Receiving Emails

1. Verify email address is correct
2. Check spam folder
3. Verify email service is working
4. Check reminder logs

---

# Quick Reference

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `/` | Open search |
| `Esc` | Close dialog |

## Status Colors

| Color | Meaning |
|-------|---------|
| Green | Paid/Active/Success |
| Yellow | Pending/Warning |
| Red | Unpaid/Suspended/Error |
| Gray | Inactive/Archived |

## Contact & Support

For technical issues, contact your system administrator.

---

*Document Version: 2.0*
*Last Updated: February 2026*
*BOH Hub - Member Management System*
