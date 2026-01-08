# Brothers of the Highway - Member Management System

## Product Requirements Document

### Original Problem Statement
Build a member management application with attendance tracking, dues management, and automated Square payment integration for a motorcycle club (Brothers of the Highway TC).

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

### What's Been Implemented

#### January 8, 2026
- [x] **Batch API Performance Enhancement**
  - Implemented `bulk_retrieve_customers` for Square API
  - Reduced 32 individual API calls to 1 batch call
  - Performance improved from ~15+ seconds to ~4 seconds
- [x] **Fuzzy Name Matching**
  - Implemented using RapidFuzz library with 75% threshold
  - Supports exact_name, exact_handle, fuzzy_name, fuzzy_handle, partial_name matches
  - Match scores displayed in UI (e.g., "Fuzzy 90%")
- [x] **Manual Linking UI**
  - Added "Link" buttons for unmatched subscriptions
  - Member dropdown with all members (Handle - Name (Chapter))
  - Confirm/Cancel workflow for linking
  - Links stored in `member_subscriptions` collection

#### Earlier Implementation
- [x] Fixed Square SDK integration (updated from deprecated API methods)
- [x] `GET /api/dues/subscriptions` - Fetch and match subscriptions
- [x] `POST /api/dues/sync-subscriptions` - Sync subscriptions to dues
- [x] View Subscriptions dialog showing matched and unmatched subscriptions
- [x] A&D page with Attendance and Dues tabs
- [x] Quick dues update buttons (Paid/Late/Not Paid)
- [x] Meeting attendance tracking with chapter-specific types
- [x] View All meetings with monthly filter and print functionality

### Technical Architecture

```
/app/
├── backend/
│   ├── server.py          # FastAPI backend with Square integration
│   ├── requirements.txt   # Python dependencies (includes RapidFuzz)
│   └── .env              # Environment variables (Square credentials)
└── frontend/
    └── src/
        └── pages/
            └── OfficerTracking.js  # A&D feature React component
```

### API Endpoints

#### Subscription Endpoints
- `GET /api/dues/subscriptions` - Get Square subscriptions with member matching (returns match_score, match_type, customer_fetch_method)
- `POST /api/dues/sync-subscriptions` - Sync active subscriptions to member dues
- `POST /api/dues/link-subscription` - Manually link member to Square customer
- `DELETE /api/dues/link-subscription/{customer_id}` - Remove manual link
- `GET /api/dues/all-members-for-linking` - Get members for linking dropdown

#### A&D Endpoints
- `GET /api/officer-tracking/members` - Get members for tracking
- `GET /api/officer-tracking/attendance` - Get attendance records
- `POST /api/officer-tracking/attendance` - Record attendance
- `DELETE /api/officer-tracking/attendance/{id}` - Delete attendance
- `GET /api/officer-tracking/dues` - Get dues records
- `POST /api/officer-tracking/dues` - Update dues status

### Database Collections
- `member_subscriptions` - Stores manual/automatic subscription-to-member links
  - `member_id`, `member_handle`, `square_customer_id`, `square_subscription_id`
  - `customer_name`, `last_synced`, `link_type` (manual/automatic), `linked_by`, `linked_at`

### Prioritized Backlog

#### P0 - Critical
- [x] ~~DigitalOcean deployment routing fix~~ (User applied fix)
- [x] ~~Square subscription sync feature~~ (Completed)
- [x] ~~Batch API performance~~ (Completed)
- [x] ~~Fuzzy matching~~ (Completed)
- [x] ~~Manual linking UI~~ (Completed)

#### P1 - High Priority
- [ ] Wall of Honor photos disappearing for older entries (needs user verification)
- [ ] Add quarterly/bi-yearly/yearly dues subscription options

#### P2 - Medium Priority
- [ ] Automated monthly sync (run sync automatically on 1st of each month)
- [ ] Email notifications for unmatched subscriptions

### Test Results (Latest)
- **Backend:** 12/12 tests passed (100%)
- **Frontend:** All features working
- **Test file:** `/app/tests/test_subscription_endpoints.py`

### Test Credentials
- **Admin:** `admin` / `admin123`
- **National Officer:** `Lonestar` / `boh2158tc`

### Third-Party Integrations
- **Square:** Payment processing and subscription management
- **Discord:** Automated notifications
- **OpenAI:** AI chatbot feature
