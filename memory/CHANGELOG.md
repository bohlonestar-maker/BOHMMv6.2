# BOH Hub Changelog

## January 9, 2026

### New Features
- **Chapter Officer Emails Visible to Members**
  - Regular members can now see email addresses of officers in their own chapter
  - Email column always visible in member table
  - Non-officer emails show "—" for regular members without full email permission

### Updates
- **Title Options Updated**
  - Added "Honorary" to User Management title dropdowns
  - Updated PM description to "Patch Master" (was "Prospect Manager")
  - All title options now consistent across System Users and Members

### Bug Fixes
- **Birthday Notification Duplicates Fixed**
  - Fixed race condition that was sending 2-3 duplicate birthday notifications to Discord
  - Added unique index on `(member_id, notification_date)` to prevent duplicates at database level
  - Changed from check-then-insert to atomic upsert using `$setOnInsert`

- **Square Webhook URL Updated**
  - Webhook URL updated from old preview URL to current: `https://bohtrack-app.preview.emergentagent.com/api/webhooks/square`

---

## January 8, 2026

### New Features
- **Suggestion Box Page**
  - New dedicated page at `/suggestions` accessible from menu
  - All logged-in members can submit suggestions (with anonymous option)
  - Upvote/downvote voting system
  - National Officers can mark status: New, Reviewed, In Progress, Implemented, Declined
  - Filter buttons by status with counts
  - Clarified as "App Suggestions Only" for BOH Hub improvements

- **Square Subscription Sync Enhancements**
  - **Batch API Performance**: Reduced 32 individual API calls to 1 batch call using `bulk_retrieve_customers`
  - **Fuzzy Name Matching**: Implemented using RapidFuzz library with 75% threshold
  - **Manual Linking UI**: Added "Link" buttons for unmatched subscriptions with member dropdown
  - Performance improved from ~15+ seconds to ~4 seconds

- **A&D Page Responsive Design**
  - Mobile (390px): Card-based layout, 2x2 chapter grid, stacked action buttons
  - Tablet (768px): Full table layout, 2x2 chapter grid
  - Laptop (1440px+): Full table layout, 4-column chapter grid, inline controls

### Bug Fixes
- **A&D Dues Sync Fixed**
  - Summary endpoint now correctly counts monthly dues (was looking for quarterly)
  - Dues paid counts now reflect Square subscription syncs properly

- **Square SDK Updated**
  - Fixed deprecated API methods (`search_subscriptions()` → `search()`)
  - Updated customer retrieval method (`retrieve_customer()` → `get()`)

---

## Previous Updates
- A&D (Attendance & Dues) feature with SEC/NVP/NPrez edit permissions
- Square payment integration and store
- Discord notifications and analytics
- Wall of Honor memorial page
- AI Knowledge Manager (National only)
- Event Calendar
- Quarterly Reports
- Member management with privacy controls
