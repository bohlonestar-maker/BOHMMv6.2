# Brothers of the Highway - Member Management System

## Product Requirements Document

### Original Problem Statement
Build a member management application with attendance tracking, dues management, automated Square payment integration, and community features for a motorcycle club (Brothers of the Highway TC).

### Core Requirements

#### 1. A&D (Attendance & Dues) Feature
- **View Access:** All officers can view the A&D page
- **Edit Access:** Only users with titles `SEC`, `NVP`, and `NPrez` can edit attendance and dues
- **Data Sync:** Changes made in A&D page sync with member profiles and vice-versa
- **UI:** Two prominent buttons to switch between "Attendance" and "Dues" views
- **Meeting Types:** Chapter-specific meeting types for accurate tracking

#### 2. Square Subscription Integration
- **Automated Dues Tracking:** Sync active Square subscriptions to mark dues as paid
- **Name Matching:** Match Square customers to members by name (using fuzzy matching)
- **View Subscriptions:** Display matched/unmatched subscriptions for review
- **Sync Feature:** "Sync from Square" button to update dues for current month
- **Manual Linking:** UI for manually linking unmatched subscriptions to members

#### 3. Suggestion Box
- **Submit:** All logged-in members can submit suggestions
- **Display:** Show submitter's handle, with option for anonymous submissions
- **Voting:** Upvote and downvote system
- **Status Management:** National Officers (except Honorary) can mark as: New, Reviewed, In Progress, Implemented, Declined
- **Location:** Section on the Dashboard

#### 4. Dynamic Permission Panel
- **UI:** National Officers (Prez, VP, SEC, T) can manage permissions for every title within every chapter
- **Chapter-Specific:** Each chapter has its own permission settings
- **Permissions:** ad_page_access, view_full_member_info, edit_members, admin_actions, view_suggestions, submit_suggestions, manage_suggestions, view_reports
- **Responsive:** Mobile, tablet, and desktop optimized

#### 5. Dues Reminders System (NEW)
- **Automated Emails:** System sends reminder emails on days 3, 8, and 10 of each month for unpaid dues
- **Configurable Templates:** Admins can edit email subject and body for each reminder day
- **Permission Suspension:** On day 10, members with unpaid dues are automatically suspended
- **Discord Integration:** When suspended, member's Discord roles are removed and saved for later restoration
- **Auto-Restoration:** When dues are paid (manual or Square sync), Discord roles are automatically restored
- **Custom Extensions:** Admins can grant payment extensions to specific members, preventing reminders and suspension until the extension expires
- **Status Dashboard:** Shows unpaid members count, suspended count, active extensions
- **Manual Trigger:** "Run Check Now" button to manually trigger reminder check
- **Scheduled Job:** Runs daily at 12:30 AM CST via APScheduler

### What's Been Implemented

#### January 11, 2026 - Dues Reminders System
- [x] **Backend API Endpoints:**
  - `GET /api/dues-reminders/templates` - Get all 3 email templates
  - `PUT /api/dues-reminders/templates/{id}` - Update template subject/body/active
  - `GET /api/dues-reminders/status` - Get unpaid members count, suspended count, list
  - `POST /api/dues-reminders/run-check` - Manual trigger for reminder check
  - `POST /api/dues-reminders/send-test` - Generate email preview
- [x] **Frontend UI (DuesReminders.js):**
  - Status cards (Current Month, Unpaid Members, Suspended, Day of Month)
  - Template list with Day 3, Day 8, Day 10 badges
  - Template editor with subject, body, active toggle
  - Save Template and Send Test buttons
  - Unpaid Members table with decrypted emails
- [x] **Automation:**
  - APScheduler job runs daily at 9:30 AM CST
  - `dues_suspended` field set on members after Day 10
  - Suspension cleared when dues marked paid (manual or Square sync)
- [x] **Navigation:**
  - Menu link added for National Prez, VP, SEC, T
  - Route added in App.js

#### January 10, 2026 - Dues Payment History & Auto-Sync Fix
- [x] **Actual Payment Dates** - Fetches real transaction dates from Square invoices
- [x] **Transaction IDs** - Displays actual Square payment/transaction IDs
- [x] **Auto-Update Dues from Payment History** - Payment date/amount determines months paid

#### January 8, 2026 - Square Sync Enhancements
- [x] **Batch API Performance** - Using `bulk_retrieve_customers`
- [x] **Fuzzy Name Matching** - RapidFuzz with 75% threshold
- [x] **Manual Linking UI** - Link buttons for unmatched subscriptions

#### January 8, 2026 - Suggestion Box Feature
- [x] Backend API endpoints for suggestions
- [x] Frontend UI on Dashboard with voting and status management

### Technical Architecture

```
/app/
├── backend/
│   └── server.py          # All backend logic (11K+ lines)
│       ├── Lines 8163-8470 - Dues Reminder endpoints
│       └── Lines 7380-7540 - Suggestion Box endpoints
└── frontend/
    └── src/
        ├── App.js             # Routes (DuesReminders at /dues-reminders)
        └── pages/
            ├── Dashboard.js       # Main dashboard with My Dues, Suggestion Box
            ├── DuesReminders.js   # Email template management
            ├── PermissionPanel.js # Dynamic permission management
            └── OfficerTracking.js # A&D page
```

### January 19, 2026 - Hangaround/Prospect Restructure (NEW)
- [x] **New Membership Hierarchy:**
  - **Hangaround** (Entry Level) - Only requires Handle and Name
  - **Prospect** (Promoted from Hangaround) - Requires full info (email, phone, address, etc.)
  - **Member** (Promoted from Prospect) - Existing flow
- [x] **Backend Implementation:**
  - New `hangarounds` collection in MongoDB
  - CRUD endpoints: `/api/hangarounds`, `/api/hangarounds/{id}`
  - Promotion endpoint: `/api/hangarounds/{id}/promote`
  - Actions endpoints for merits/disciplinary records
  - Migration endpoint to convert existing prospects
- [x] **Frontend Implementation:**
  - Tabs interface on Prospects page ("Hangarounds" / "Prospects")
  - Simplified "Add Hangaround" dialog (only Handle + Name)
  - "Promote to Prospect" button with form for remaining required info
  - Separate tables for hangarounds and prospects
- [x] **Discord Integration (optional):**
  - `DISCORD_HANGAROUND_ROLE_ID` - Role added when becoming hangaround
  - `DISCORD_PROSPECT_ROLE_ID` - Role swapped when promoted to prospect

### January 29, 2026 - Prospect Channel Analytics (NEW)
- [x] **Feature Overview:**
  - Track Discord voice activity in "Prospect" and "Prospect 2" channels
  - Track who else was in the channel during each session
  - Identify if actual Prospects/Hangarounds were present during sessions
- [x] **Access Control:**
  - Only National/HA Officers: Prez, VP, S@A, ENF, SEC can view
- [x] **Backend Implementation:**
  - New `prospect_channel_activity` collection for detailed tracking
  - New `prospect_channel_settings` collection for enable/disable and reset tracking
  - Endpoints: GET/POST `/api/prospect-channel-analytics`, `/settings`, `/reset`
- [x] **Frontend Implementation:**
  - New page: `/prospect-channel-analytics`
  - Access from Prospects page via "Channel Analytics" button
  - Summary cards: Unique Visitors, Total Sessions, Sessions w/ Prospect, Total Time
  - User table with expandable session details
  - Date range filtering (All Time, 7 Days, 30 Days, Custom)
  - Settings dialog to enable/disable tracking
  - Reset button to clear all data

### API Endpoints

#### Hangarounds (NEW - Jan 19, 2026)
- `GET /api/hangarounds` - Get all hangarounds
- `GET /api/hangarounds/{id}` - Get single hangaround
- `POST /api/hangarounds` - Create hangaround (only handle/name required)
- `PUT /api/hangarounds/{id}` - Update hangaround
- `DELETE /api/hangarounds/{id}` - Archive hangaround
- `POST /api/hangarounds/{id}/promote` - Promote to prospect
- `POST /api/hangarounds/{id}/actions` - Add action (merit/disciplinary)
- `DELETE /api/hangarounds/{id}/actions/{action_id}` - Delete action
- `POST /api/admin/migrate-prospects-to-hangarounds` - Migration endpoint

#### Dues Reminders
- `GET /api/dues-reminders/templates` - Get all email templates
- `PUT /api/dues-reminders/templates/{id}` - Update template
- `GET /api/dues-reminders/status` - Get unpaid/suspended status
- `POST /api/dues-reminders/run-check` - Trigger reminder check
- `POST /api/dues-reminders/send-test` - Generate email preview
- `GET /api/dues-reminders/extensions` - Get all extensions
- `POST /api/dues-reminders/extensions` - Grant extension
- `PUT /api/dues-reminders/extensions/{member_id}` - Update extension
- `DELETE /api/dues-reminders/extensions/{member_id}` - Revoke extension
- `POST /api/dues-reminders/test-discord-suspension` - Test Discord suspension

#### Permissions
- `GET /api/permissions/all` - Get all permissions by chapter
- `PUT /api/permissions/bulk-update` - Update permissions for a title

### Database Collections
- `hangarounds` - Entry-level members (handle, name, meeting_attendance, actions)
- `archived_hangarounds` - Archived/promoted hangarounds
- `prospects` - Full prospects with contact info
- `archived_prospects` - Archived prospects
- `dues_email_templates` - Email templates for reminders (Day 3, 8, 10)
- `dues_reminder_sent` - Log of reminders sent to prevent duplicates
- `dues_extensions` - Payment extensions granted to members (member_id, extension_until, reason, granted_by)
- `discord_suspensions` - Stores member's Discord roles before suspension for later restoration
- `role_permissions` - Chapter-specific permissions for each title
- `suggestions` - User suggestions with votes and status

### Prioritized Backlog

#### P0 - Critical
- [x] ~~Dues Reminders System~~ (Completed Jan 11)
- [x] ~~Permission Suspension~~ (Completed Jan 11)
- [x] ~~Square subscription sync feature~~ (Completed)
- [x] ~~Suggestion Box~~ (Completed)
- [x] ~~Hangaround/Prospect Restructure~~ (Completed Jan 19)

#### P1 - High Priority
- [ ] Square one-time payment sync bug (payments not updating member dues)
- [ ] Triple birthday notification fix (distributed lock not working across containers)
- [ ] "Update Dues" dialog mobile responsiveness
- [ ] Add quarterly/bi-yearly/yearly dues subscription options

#### P2 - Medium Priority
- [ ] Suggestion Box replies/comments
- [ ] Refactor server.py into modules (routes, models, services) - CRITICAL: Now 14K+ lines
- [ ] Link Discord members to system members UI

### Test Credentials
- **Admin/National SEC:** `Lonestar` / `boh2158tc`
- **Super Admin:** `admin` / `2X13y75Z`

### Third-Party Integrations
- **Square:** Payment processing and subscription management
- **Discord:** Automated notifications
- **OpenAI:** AI chatbot feature
- **Email:** MOCKED (logged to console, not actually sent)

### Important Notes
- **Email sending is MOCKED** - Emails are logged to console and recorded in `dues_reminder_sent` collection, but not actually sent via SMTP. Actual email integration would require a service like SendGrid or SES.
- **Suspension clears on payment** - When dues are marked paid (manual or Square sync), the `dues_suspended` flag is automatically cleared.
