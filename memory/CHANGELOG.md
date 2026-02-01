# BOH Hub Changelog

## February 1, 2026

### New Features
- **Non-Dues Paying Members**
  - Added `non_dues_paying` field to Member model
  - New "Dues Exemption" checkbox in member edit form (amber styling)
  - Members marked as non-dues paying are excluded from:
    - Dues reminder emails
    - Suspension logic
    - Unpaid dues reports
  - Officer Tracking dues tab shows "Exempt" badge for non-dues paying members
  - Status column shows "Non-Dues Paying" instead of regular dues status

- **Dues Extensions from A&D Panel**
  - Can now add dues extensions directly from the Update Dues dialog
  - Select "Extended" status to reveal date picker
  - Enter extension end date - member won't receive reminders until then
  - Extension status displayed in dues table with "Extended" badge and date
  - When dues are marked as "Paid", any active extension is automatically lifted

### UI Improvements
- **Menu Restructured**
  - All Admin items now grouped together under red "ADMIN" header
  - Moved A & D, Forms, and Reports to Admin section
  - Clearer visual separation between sections
  - Admin section includes: A & D, Forms, Reports, Admin, Change Log, Permissions, Dues Reminders, Message Monitor, AI Knowledge, Discord Analytics
  - Added scrollable menu for better mobile experience

- **Cancel Unmatched Square Subscriptions**
  - Added "Cancel" button next to each unmatched subscription in View Subscriptions dialog
  - Directly cancels the subscription in Square via API
  - Subscriptions with scheduled cancellation now immediately hidden from lists

- **Auto-Cancel Square Subscription on Member Deletion**
  - When archiving a member, their Square subscription is now automatically cancelled (enabled by default)
  - New checkbox "Cancel Square subscription (if any)" in the archive dialog
  - Activity log records if subscription was cancelled

- **Prospect Channel Analytics - Time Breakdown**
  - Completed sessions now show exact time spent with each prospect
  - Tracks when prospects join/leave during a user's session
  - Displays breakdown like: "Time with HA(p) Dice: 30m, Time with HA(p) Sparky: 45m"
  - Aggregated "Total Time with Each Prospect" summary in expanded user view

- **Admin User Manual (PDF)**
  - Created comprehensive admin manual in Markdown (`/app/admin_manual.md`)
  - Generated downloadable PDF using ReportLab library
  - Available at `/app/BOH_Hub_Admin_Manual.pdf`
  - Covers all admin features: member management, dues, permissions, Discord integration

### Bug Fixes
- **Anniversary Notifications Fixed (Duplicate Prevention)**
  - Applied same distributed lock mechanism as birthday notifications
  - Uses `scheduler_locks` collection to prevent multiple container instances from running simultaneously
  - Added unique index on `anniversary_notifications` collection
  
- **Square Cancel Subscription Method Fixed**
  - Fixed "SubscriptionsClient object has no attribute 'cancel_subscription'" error
  - Updated to use correct SDK method: `square_client.subscriptions.cancel()`

- **Cancelled Subscriptions Now Hidden**
  - Subscriptions with `canceled_date` set are now filtered out from all lists
  - Previously, cancelled subscriptions still showed as "ACTIVE" until billing period ended

- **Prospect Channel Analytics - Duplicate Users Fixed**
  - Added deduplication logic to prevent same user appearing multiple times
  - All prospects in channel now correctly shown (was only showing first prospect)

- **Dues Payment History - Duplicate Transactions Fixed**
  - Fixed issue where same transaction appeared multiple times in payment notes
  - Created admin cleanup endpoint to deduplicate historical records
  - Frontend now deduplicates payment records from multiple sources

---

## January 29, 2026

### New Features
- **Hangaround/Prospect Workflow**
  - New "Hangaround" status as preliminary step before Prospect
  - Tabbed UI on Prospects page (Hangarounds | Prospects)
  - Promote Hangarounds to Prospects with full info collection

- **Hangaround Meeting Attendance**
  - Track meeting attendance for Hangarounds

- **Prospect Channel Analytics**
  - New page at `/prospect-channel-analytics`
  - Real-time view of users currently in Prospect voice channels
  - Live timers showing session duration
  - Identifies prospects by "HA(p)" in Discord display name
  - Role-based access (Prez, VP, S@A, ENF, SEC only)

- **Discord Analytics Cleanup**
  - Admin endpoint to purge analytics for departed Discord members

### Bug Fixes
- **Square One-Time Payment Sync**
  - Fixed bug where payment notes weren't added to already-paid months
  - Added admin endpoint `/api/admin/reapply-payment-notes` for historical fix

---

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
  - Webhook URL updated from old preview URL to current: `https://member-tracker-40.preview.emergentagent.com/api/webhooks/square`

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
