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

#### 3. Suggestion Box (NEW)
- **Submit:** All logged-in members can submit suggestions
- **Display:** Show submitter's handle, with option for anonymous submissions
- **Voting:** Upvote and downvote system
- **Status Management:** National Officers (except Honorary) can mark as: New, Reviewed, In Progress, Implemented, Declined
- **Location:** Section on the Dashboard

#### 4. Responsive Design (A&D Page)
- **Mobile (390px):** Card-based layout, 2x2 chapter grid, stacked action buttons
- **Tablet (768px):** Full table layout, 2x2 chapter grid
- **Laptop (1440px+):** Full table layout, 4-column chapter grid, inline controls

### What's Been Implemented

#### January 8, 2026 - Suggestion Box Feature
- [x] **Backend API Endpoints:**
  - `GET /api/suggestions` - Get all suggestions with vote counts
  - `POST /api/suggestions` - Submit new suggestion (with anonymous option)
  - `POST /api/suggestions/{id}/vote` - Upvote or downvote
  - `PATCH /api/suggestions/{id}/status` - Update status (National Officers only)
  - `DELETE /api/suggestions/{id}` - Delete suggestion
- [x] **Frontend UI on Dashboard:**
  - Suggestion Box section with collapsible view
  - "New Suggestion" dialog with title, description, anonymous checkbox
  - Vote buttons (thumbs up/down) with vote count display
  - Status badges (color-coded)
  - Status dropdown for National Officers to manage
  - Delete functionality

#### January 10, 2026 - Dues Payment History Fix
- [x] **Actual Payment Dates** - Fetches real transaction dates from Square invoices (not sync dates)
- [x] **Transaction IDs** - Displays actual Square payment/transaction IDs via order tenders
- [x] **Invoice IDs** - Shows invoice IDs for each subscription payment
- [x] **Enhanced UI** - Improved payment history dialog with clear date/amount/ID display

#### January 8, 2026 - Square Sync Enhancements
- [x] **Batch API Performance** - Using `bulk_retrieve_customers`
- [x] **Fuzzy Name Matching** - RapidFuzz with 75% threshold
- [x] **Manual Linking UI** - Link buttons for unmatched subscriptions
- [x] **A&D Dues Sync Fix** - Summary now correctly counts monthly dues

### Technical Architecture

```
/app/
├── backend/
│   └── server.py          # Contains suggestion box endpoints (lines ~7380-7540)
└── frontend/
    └── src/
        └── pages/
            └── Dashboard.js  # Contains Suggestion Box UI section
```

### API Endpoints

#### Suggestion Box Endpoints (NEW)
- `GET /api/suggestions` - Get all suggestions
- `POST /api/suggestions` - Create suggestion
- `POST /api/suggestions/{id}/vote` - Vote (upvote/downvote)
- `PATCH /api/suggestions/{id}/status` - Update status
- `DELETE /api/suggestions/{id}` - Delete suggestion

#### Subscription Endpoints
- `GET /api/dues/subscriptions` - Get Square subscriptions with matching
- `POST /api/dues/sync-subscriptions` - Sync subscriptions to dues
- `POST /api/dues/link-subscription` - Manual linking
- `GET /api/dues/all-members-for-linking` - Get members for dropdown

### Database Collections
- `suggestions` (NEW) - Stores suggestion submissions
  - `id`, `title`, `description`, `submitted_by`, `submitter_id`, `is_anonymous`
  - `status` (new/reviewed/in_progress/implemented/declined)
  - `upvotes` [], `downvotes` [] - Arrays of member IDs
  - `created_at`, `updated_at`, `status_updated_by`, `status_updated_at`

### Prioritized Backlog

#### P0 - Critical
- [x] ~~Square subscription sync feature~~ (Completed)
- [x] ~~Batch API performance~~ (Completed)
- [x] ~~Fuzzy matching~~ (Completed)
- [x] ~~Manual linking UI~~ (Completed)
- [x] ~~A&D dues sync fix~~ (Completed)
- [x] ~~Suggestion Box~~ (Completed)

#### P1 - High Priority
- [x] ~~Wall of Honor photos~~ (User confirmed fixed)
- [ ] Add quarterly/bi-yearly/yearly dues subscription options

#### P2 - Medium Priority
- [ ] Automated monthly sync (run on 1st of each month)
- [ ] Email notifications for unmatched subscriptions

### Test Credentials
- **Admin:** `admin` / `admin123`
- **National Officer:** `Lonestar` / `boh2158tc`

### Third-Party Integrations
- **Square:** Payment processing and subscription management
- **Discord:** Automated notifications
- **OpenAI:** AI chatbot feature
