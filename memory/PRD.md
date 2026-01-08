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

### What's Been Implemented

#### January 2026
- [x] Fixed Square SDK integration (updated from deprecated API methods)
- [x] `GET /api/dues/subscriptions` - Fetch and match subscriptions
- [x] `POST /api/dues/sync-subscriptions` - Sync subscriptions to dues
- [x] View Subscriptions dialog showing matched (25) and unmatched subscriptions
- [x] A&D page with Attendance and Dues tabs
- [x] Quick dues update buttons (Paid/Late/Not Paid)
- [x] Meeting attendance tracking with chapter-specific types
- [x] View All meetings with monthly filter and print functionality

### Technical Architecture

```
/app/
├── backend/
│   ├── server.py          # FastAPI backend with Square integration
│   ├── requirements.txt   # Python dependencies
│   └── .env              # Environment variables (Square credentials)
└── frontend/
    └── src/
        └── pages/
            └── OfficerTracking.js  # A&D feature React component
```

### API Endpoints

#### Subscription Endpoints
- `GET /api/dues/subscriptions` - Get Square subscriptions with member matching
- `POST /api/dues/sync-subscriptions` - Sync active subscriptions to member dues
- `POST /api/dues/link-subscription` - Manually link member to Square customer

#### A&D Endpoints
- `GET /api/officer-tracking/members` - Get members for tracking
- `GET /api/officer-tracking/attendance` - Get attendance records
- `POST /api/officer-tracking/attendance` - Record attendance
- `DELETE /api/officer-tracking/attendance/{id}` - Delete attendance
- `GET /api/officer-tracking/dues` - Get dues records
- `POST /api/officer-tracking/dues` - Update dues status

### Prioritized Backlog

#### P0 - Critical
- [x] ~~DigitalOcean deployment routing fix~~ (User needs to apply fix)
- [x] ~~Square subscription sync feature~~ (Completed)

#### P1 - High Priority
- [ ] Wall of Honor photos disappearing for older entries (needs user verification)
- [ ] Add quarterly/bi-yearly/yearly dues subscription options

#### P2 - Medium Priority
- [ ] Improve Square sync performance (batch customer fetches)
- [ ] Add manual member-to-subscription linking UI

### Known Issues
1. **DigitalOcean Deployment** - User needs to update App Spec YAML with correct routing:
   - Backend route: `/api` with `preserve_path_prefix: true`
   - Frontend route: `/`

2. **Square API Performance** - Each subscription requires individual customer lookup (32 calls per sync)

### Test Credentials
- **Admin:** `admin` / `admin123`
- **National Officer:** `Lonestar` / `boh2158tc`

### Third-Party Integrations
- **Square:** Payment processing and subscription management
- **Discord:** Automated notifications
- **OpenAI:** AI chatbot feature
