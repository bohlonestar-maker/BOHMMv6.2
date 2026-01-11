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
- **Status Dashboard:** Shows unpaid members count, suspended count, reminders sent
- **Manual Trigger:** "Run Check Now" button to manually trigger reminder check
- **Scheduled Job:** Runs daily at 9:30 AM CST via APScheduler

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

### API Endpoints

#### Dues Reminders (NEW)
- `GET /api/dues-reminders/templates` - Get all email templates
- `PUT /api/dues-reminders/templates/{id}` - Update template
- `GET /api/dues-reminders/status` - Get unpaid/suspended status
- `POST /api/dues-reminders/run-check` - Trigger reminder check
- `POST /api/dues-reminders/send-test` - Generate email preview

#### Permissions
- `GET /api/permissions/all` - Get all permissions by chapter
- `PUT /api/permissions/bulk-update` - Update permissions for a title

### Database Collections
- `dues_email_templates` - Email templates for reminders (Day 3, 8, 10)
- `dues_reminder_sent` - Log of reminders sent to prevent duplicates
- `role_permissions` - Chapter-specific permissions for each title
- `suggestions` - User suggestions with votes and status

### Prioritized Backlog

#### P0 - Critical
- [x] ~~Dues Reminders System~~ (Completed Jan 11)
- [x] ~~Permission Suspension~~ (Completed Jan 11)
- [x] ~~Square subscription sync feature~~ (Completed)
- [x] ~~Suggestion Box~~ (Completed)

#### P1 - High Priority
- [ ] Add quarterly/bi-yearly/yearly dues subscription options
- [ ] Actual email sending (currently MOCKED - logged only)

#### P2 - Medium Priority
- [ ] Automated monthly sync (run on 1st of each month)
- [ ] Suggestion Box replies/comments
- [ ] Refactor server.py into modules (routes, models, services)

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
