from fpdf import FPDF
import re

class PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)
        
    def header(self):
        if self.page_no() > 1:
            self.set_font('Helvetica', 'I', 9)
            self.set_text_color(100, 100, 100)
            self.cell(0, 10, 'BOH Hub Administrator Manual', align='C')
            self.ln(5)
            
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

    def chapter_title(self, title, level=1):
        if level == 1:
            self.add_page()
            self.set_font('Helvetica', 'B', 24)
            self.set_text_color(26, 54, 93)
            self.cell(0, 15, title, ln=True)
            self.set_draw_color(49, 130, 206)
            self.set_line_width(1)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(10)
        elif level == 2:
            self.set_font('Helvetica', 'B', 16)
            self.set_text_color(44, 82, 130)
            self.ln(5)
            self.cell(0, 10, title, ln=True)
            self.set_draw_color(190, 227, 248)
            self.set_line_width(0.5)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(3)
        elif level == 3:
            self.set_font('Helvetica', 'B', 13)
            self.set_text_color(43, 108, 176)
            self.ln(3)
            self.cell(0, 8, title, ln=True)
            self.ln(2)
            
    def body_text(self, text):
        self.set_font('Helvetica', '', 11)
        self.set_text_color(51, 51, 51)
        self.multi_cell(0, 6, text)
        self.ln(2)
        
    def bullet_item(self, text, indent=0):
        self.set_font('Helvetica', '', 11)
        self.set_text_color(51, 51, 51)
        x = self.get_x() + indent
        self.set_x(x)
        self.cell(5, 6, chr(149))  # bullet point
        self.multi_cell(0, 6, text)
        
    def numbered_item(self, num, text):
        self.set_font('Helvetica', '', 11)
        self.set_text_color(51, 51, 51)
        self.cell(8, 6, f"{num}.")
        self.multi_cell(0, 6, text)
        
    def table_header(self, headers, widths):
        self.set_font('Helvetica', 'B', 10)
        self.set_fill_color(237, 242, 247)
        self.set_text_color(45, 55, 72)
        for i, header in enumerate(headers):
            self.cell(widths[i], 8, header, border=1, fill=True)
        self.ln()
        
    def table_row(self, data, widths):
        self.set_font('Helvetica', '', 10)
        self.set_text_color(51, 51, 51)
        for i, item in enumerate(data):
            self.cell(widths[i], 7, item, border=1)
        self.ln()

# Create PDF
pdf = PDF()
pdf.set_margins(15, 15, 15)

# Title Page
pdf.add_page()
pdf.set_font('Helvetica', 'B', 36)
pdf.set_text_color(26, 54, 93)
pdf.ln(60)
pdf.cell(0, 20, 'BOH Hub', align='C', ln=True)
pdf.set_font('Helvetica', 'B', 24)
pdf.cell(0, 15, 'Administrator Manual', align='C', ln=True)
pdf.ln(20)
pdf.set_font('Helvetica', '', 14)
pdf.set_text_color(100, 100, 100)
pdf.cell(0, 10, 'Version 2.0 | February 2026', align='C', ln=True)
pdf.ln(80)
pdf.set_font('Helvetica', 'I', 11)
pdf.cell(0, 10, 'Member Management System', align='C', ln=True)

# Table of Contents
pdf.chapter_title('Table of Contents', 1)
toc_items = [
    '1. Getting Started',
    '2. Dashboard Overview', 
    '3. Member Management',
    '4. Dues Management',
    '5. Square Payment Integration',
    '6. Discord Integration',
    '7. Prospects & Hangarounds',
    '8. Officer Tracking',
    '9. Meeting Management',
    '10. Analytics & Reports',
    '11. System Administration',
    '12. Troubleshooting'
]
for item in toc_items:
    pdf.body_text(item)

# Section 1: Getting Started
pdf.chapter_title('1. Getting Started', 1)

pdf.chapter_title('Logging In', 2)
pdf.body_text('To access the BOH Hub system:')
pdf.numbered_item(1, 'Navigate to the application URL')
pdf.numbered_item(2, 'Enter your Username and Password')
pdf.numbered_item(3, 'Click Sign In')

pdf.chapter_title('User Roles', 2)
pdf.body_text('The system has four access levels:')
pdf.ln(3)
pdf.table_header(['Role', 'Access Level'], [50, 140])
pdf.table_row(['Admin', 'Full system access, all features'], [50, 140])
pdf.table_row(['National Officer', 'Chapter management, dues, officer tracking'], [50, 140])
pdf.table_row(['Chapter Officer', 'Limited to own chapter members'], [50, 140])
pdf.table_row(['Member', 'View own profile and dues only'], [50, 140])

pdf.chapter_title('Navigation', 2)
pdf.body_text('The main navigation menu includes:')
pdf.bullet_item('Dashboard - Home page with overview')
pdf.bullet_item('Members - Member directory')
pdf.bullet_item('Prospects - Prospect and Hangaround management')
pdf.bullet_item('Officer Tracking - Dues and reminders')
pdf.bullet_item('Meeting Manager - Meeting scheduling')
pdf.bullet_item('Discord Analytics - Voice/text activity')
pdf.bullet_item('Admin - System settings (Admin only)')

# Section 2: Dashboard
pdf.chapter_title('2. Dashboard Overview', 1)

pdf.body_text('The Dashboard provides a quick overview of the organization status.')

pdf.chapter_title('My Dues Section', 2)
pdf.bullet_item('Current month dues status')
pdf.bullet_item('Recent payment history')
pdf.bullet_item('Year-at-a-glance calendar showing paid/unpaid months')

pdf.chapter_title('Quick Stats', 2)
pdf.bullet_item('Total active members')
pdf.bullet_item('Upcoming birthdays')
pdf.bullet_item('Upcoming anniversaries')
pdf.bullet_item('Recent activity')

# Section 3: Member Management
pdf.chapter_title('3. Member Management', 1)

pdf.chapter_title('Adding a New Member', 2)
pdf.numbered_item(1, 'Click "Add Member" button on Dashboard')
pdf.numbered_item(2, 'Fill in required fields: Handle, Name, Email, Phone, Chapter, Title, Join Date, Birthday')
pdf.numbered_item(3, 'Click "Save"')

pdf.chapter_title('Editing a Member', 2)
pdf.numbered_item(1, 'Find member in the directory')
pdf.numbered_item(2, 'Click the three-dot menu')
pdf.numbered_item(3, 'Select "Edit"')
pdf.numbered_item(4, 'Update fields as needed')
pdf.numbered_item(5, 'Click "Save Changes"')

pdf.chapter_title('Archiving a Member', 2)
pdf.body_text('When a member leaves the organization:')
pdf.numbered_item(1, 'Click the three-dot menu on the member')
pdf.numbered_item(2, 'Select "Archive"')
pdf.numbered_item(3, 'Enter a deletion reason')
pdf.numbered_item(4, 'Optional: Check "Also kick from Discord server"')
pdf.numbered_item(5, 'Optional: Check "Cancel Square subscription" (default: checked)')
pdf.numbered_item(6, 'Click "Archive Member"')

pdf.chapter_title('Member Profile Fields', 2)
pdf.ln(3)
pdf.table_header(['Field', 'Description', 'Encrypted'], [40, 100, 40])
pdf.table_row(['Handle', 'Discord/display name', 'No'], [40, 100, 40])
pdf.table_row(['Name', 'Legal full name', 'Yes'], [40, 100, 40])
pdf.table_row(['Email', 'Contact email', 'Yes'], [40, 100, 40])
pdf.table_row(['Phone', 'Phone number', 'Yes'], [40, 100, 40])
pdf.table_row(['Address', 'Mailing address', 'Yes'], [40, 100, 40])
pdf.table_row(['Chapter', 'Chapter assignment', 'No'], [40, 100, 40])
pdf.table_row(['Title', 'Role in organization', 'No'], [40, 100, 40])
pdf.table_row(['Join Date', 'MM/YYYY start date', 'No'], [40, 100, 40])
pdf.table_row(['Birthday', 'MM/DD for notifications', 'No'], [40, 100, 40])

# Section 4: Dues Management
pdf.chapter_title('4. Dues Management', 1)

pdf.chapter_title('Understanding Dues Status', 2)
pdf.body_text('Each month can have one of these statuses:')
pdf.bullet_item('Paid (Green) - Payment confirmed')
pdf.bullet_item('Unpaid (Gray) - No payment recorded')
pdf.bullet_item('Suspended (Red) - Member suspended for non-payment')

pdf.chapter_title('Viewing Member Dues', 2)
pdf.numbered_item(1, 'Go to Officer Tracking')
pdf.numbered_item(2, 'Click the Dues tab')
pdf.numbered_item(3, 'Select a month from the dropdown')
pdf.numbered_item(4, 'View all members and their dues status')

pdf.chapter_title('Manually Updating Dues', 2)
pdf.numbered_item(1, 'Find the member in the Dues tab')
pdf.numbered_item(2, 'Click "Update" next to their name')
pdf.numbered_item(3, 'Select the new status (Paid/Unpaid)')
pdf.numbered_item(4, 'Add optional notes')
pdf.numbered_item(5, 'Click "Save"')

pdf.chapter_title('Dues Reminders', 2)
pdf.body_text('The system automatically sends email reminders:')
pdf.bullet_item('Day 3: First reminder')
pdf.bullet_item('Day 8: Second reminder')
pdf.bullet_item('Day 10: Final warning before suspension')

pdf.chapter_title('Dues Extensions', 2)
pdf.body_text('To grant a member extra time to pay:')
pdf.numbered_item(1, 'Find the member in the Dues list')
pdf.numbered_item(2, 'Click "Grant Extension"')
pdf.numbered_item(3, 'Select the extension end date')
pdf.numbered_item(4, 'Enter a reason')
pdf.numbered_item(5, 'Click "Confirm"')

# Section 5: Square Integration
pdf.chapter_title('5. Square Payment Integration', 1)

pdf.chapter_title('Automatic Sync', 2)
pdf.body_text('The system automatically syncs with Square every hour to:')
pdf.bullet_item('Match subscription payments to members')
pdf.bullet_item('Update dues status for paid months')
pdf.bullet_item('Track one-time payments')

pdf.chapter_title('Manual Sync', 2)
pdf.body_text('To force an immediate sync:')
pdf.numbered_item(1, 'Go to Officer Tracking > Dues tab')
pdf.numbered_item(2, 'Click "Sync Square"')
pdf.numbered_item(3, 'Wait for the sync to complete')
pdf.numbered_item(4, 'Review any unmatched payments')

pdf.chapter_title('Viewing Subscriptions', 2)
pdf.numbered_item(1, 'Click "View Subscriptions" in the Dues tab')
pdf.numbered_item(2, 'See two sections: Matched and Unmatched Subscriptions')

pdf.chapter_title('Linking Unmatched Subscriptions', 2)
pdf.numbered_item(1, 'Find the unmatched subscription')
pdf.numbered_item(2, 'Click "Link"')
pdf.numbered_item(3, 'Select the member from the dropdown')
pdf.numbered_item(4, 'Click "Confirm"')

pdf.chapter_title('Cancelling Unmatched Subscriptions', 2)
pdf.body_text('For subscriptions belonging to former members:')
pdf.numbered_item(1, 'Find the unmatched subscription')
pdf.numbered_item(2, 'Click "Cancel"')
pdf.numbered_item(3, 'Confirm the cancellation')

pdf.chapter_title('Payment Types', 2)
pdf.ln(3)
pdf.table_header(['Type', 'Description'], [60, 120])
pdf.table_row(['Monthly Subscription', '$30/month recurring'], [60, 120])
pdf.table_row(['6-Month Prepay', '$180 one-time'], [60, 120])
pdf.table_row(['Annual Prepay', '$330 one-time'], [60, 120])

# Section 6: Discord Integration
pdf.chapter_title('6. Discord Integration', 1)

pdf.chapter_title('Discord Bot Features', 2)
pdf.body_text('The integrated Discord bot provides:')
pdf.bullet_item('Birthday notifications')
pdf.bullet_item('Anniversary notifications')
pdf.bullet_item('Voice channel tracking')
pdf.bullet_item('Text activity logging')
pdf.bullet_item('Role-based permissions')

pdf.chapter_title('Birthday/Anniversary Notifications', 2)
pdf.body_text('Automatic notifications are sent to a designated Discord channel:')
pdf.bullet_item('Birthdays: Posted on the member\'s birthday')
pdf.bullet_item('Anniversaries: Posted on the 1st of their join month')

pdf.chapter_title('Voice Activity Tracking', 2)
pdf.body_text('The bot tracks when members join voice channels:')
pdf.bullet_item('Duration in each channel')
pdf.bullet_item('Who else was in the channel')
pdf.bullet_item('Total monthly voice time')

pdf.chapter_title('Prospect Channel Analytics', 2)
pdf.body_text('Special tracking for "Prospect" voice channels. Access via:')
pdf.numbered_item(1, 'Go to Prospects page')
pdf.numbered_item(2, 'Click "Channel Analytics"')
pdf.body_text('Features include:')
pdf.bullet_item('Currently active users (live view)')
pdf.bullet_item('Time spent with each prospect')
pdf.bullet_item('Historical session data')

# Section 7: Prospects & Hangarounds
pdf.chapter_title('7. Prospects & Hangarounds', 1)

pdf.chapter_title('Understanding the Pipeline', 2)
pdf.body_text('The prospecting workflow has two stages:')
pdf.numbered_item(1, 'Hangaround - Initial contact, minimal info required')
pdf.numbered_item(2, 'Prospect - Full prospect with complete information')

pdf.chapter_title('Managing Hangarounds', 2)
pdf.chapter_title('Adding a Hangaround', 3)
pdf.numbered_item(1, 'Go to Prospects page')
pdf.numbered_item(2, 'Click the Hangarounds tab')
pdf.numbered_item(3, 'Click "Add Hangaround"')
pdf.numbered_item(4, 'Enter Handle (required) and Name (optional)')
pdf.numbered_item(5, 'Click "Save"')

pdf.chapter_title('Promoting to Prospect', 3)
pdf.numbered_item(1, 'Click "Promote" on the hangaround')
pdf.numbered_item(2, 'Fill in required prospect information')
pdf.numbered_item(3, 'Click "Confirm Promotion"')

pdf.chapter_title('Managing Prospects', 2)
pdf.body_text('Track prospect activities:')
pdf.bullet_item('Meetings attended')
pdf.bullet_item('Rides participated')
pdf.bullet_item('Events attended')
pdf.bullet_item('Custom actions')

# Section 8: Officer Tracking
pdf.chapter_title('8. Officer Tracking', 1)

pdf.chapter_title('Dues Tab', 2)
pdf.body_text('Monitor and manage member dues:')
pdf.bullet_item('View dues by month')
pdf.bullet_item('Update payment status')
pdf.bullet_item('Grant extensions')
pdf.bullet_item('Send manual reminders')

pdf.chapter_title('Reminders Tab', 2)
pdf.body_text('View reminder history:')
pdf.bullet_item('See which reminders were sent')
pdf.bullet_item('Check delivery status')
pdf.bullet_item('Resend failed reminders')

pdf.chapter_title('Reports Tab', 2)
pdf.body_text('Access financial reports:')
pdf.bullet_item('Monthly payment summary')
pdf.bullet_item('Outstanding dues report')
pdf.bullet_item('Year-to-date collections')

# Section 9: Meeting Management
pdf.chapter_title('9. Meeting Management', 1)

pdf.chapter_title('Creating a Meeting', 2)
pdf.numbered_item(1, 'Go to Meeting Manager')
pdf.numbered_item(2, 'Click "Schedule Meeting"')
pdf.numbered_item(3, 'Enter meeting details: Name, Date/Time, Location, Description')
pdf.numbered_item(4, 'Click "Create"')

pdf.chapter_title('Taking Attendance', 2)
pdf.numbered_item(1, 'Open the meeting')
pdf.numbered_item(2, 'Click "Take Attendance"')
pdf.numbered_item(3, 'Check off members present')
pdf.numbered_item(4, 'Add notes if needed')
pdf.numbered_item(5, 'Click "Save Attendance"')

# Section 10: Analytics
pdf.chapter_title('10. Analytics & Reports', 1)

pdf.chapter_title('Discord Analytics', 2)
pdf.body_text('Track member engagement through Discord:')
pdf.bullet_item('Voice channel participation')
pdf.bullet_item('Text message activity')
pdf.bullet_item('Most active members')
pdf.bullet_item('Quiet members needing outreach')

pdf.chapter_title('Prospect Channel Analytics', 2)
pdf.body_text('Detailed tracking for prospect interactions:')
pdf.bullet_item('Who visits prospect channels')
pdf.bullet_item('How long they stay')
pdf.bullet_item('Whether actual prospects were present')
pdf.bullet_item('Time breakdown per prospect')

# Section 11: System Administration
pdf.chapter_title('11. System Administration', 1)

pdf.chapter_title('User Management', 2)
pdf.chapter_title('Creating Admin Users', 3)
pdf.numbered_item(1, 'Go to Admin section')
pdf.numbered_item(2, 'Click "Add User"')
pdf.numbered_item(3, 'Enter username and password')
pdf.numbered_item(4, 'Select role and permissions')
pdf.numbered_item(5, 'Click "Create"')

pdf.chapter_title('Resetting Passwords', 3)
pdf.numbered_item(1, 'Find the user in Admin section')
pdf.numbered_item(2, 'Click "Reset Password"')
pdf.numbered_item(3, 'Enter new password')
pdf.numbered_item(4, 'Click "Confirm"')

pdf.chapter_title('Backup & Recovery', 2)
pdf.body_text('Member data is automatically backed up. To restore an archived member:')
pdf.numbered_item(1, 'Go to "Archived Members"')
pdf.numbered_item(2, 'Find the member')
pdf.numbered_item(3, 'Click "Restore"')

# Section 12: Troubleshooting
pdf.chapter_title('12. Troubleshooting', 1)

pdf.chapter_title('Square Payments Not Syncing', 2)
pdf.numbered_item(1, 'Check Square API connection in Admin')
pdf.numbered_item(2, 'Verify API keys are valid')
pdf.numbered_item(3, 'Run manual sync')
pdf.numbered_item(4, 'Check for unmatched payments')

pdf.chapter_title('Discord Bot Offline', 2)
pdf.numbered_item(1, 'Check Discord bot status')
pdf.numbered_item(2, 'Verify bot token is valid')
pdf.numbered_item(3, 'Check server permissions')
pdf.numbered_item(4, 'Contact administrator')

pdf.chapter_title('Dues Status Incorrect', 2)
pdf.numbered_item(1, 'Verify Square payment sync')
pdf.numbered_item(2, 'Check for manual overrides')
pdf.numbered_item(3, 'Review payment notes')
pdf.numbered_item(4, 'Contact SEC for correction')

pdf.chapter_title('Quick Reference', 2)
pdf.ln(3)
pdf.body_text('Status Colors:')
pdf.table_header(['Color', 'Meaning'], [50, 130])
pdf.table_row(['Green', 'Paid/Active/Success'], [50, 130])
pdf.table_row(['Yellow', 'Pending/Warning'], [50, 130])
pdf.table_row(['Red', 'Unpaid/Suspended/Error'], [50, 130])
pdf.table_row(['Gray', 'Inactive/Archived'], [50, 130])

# Save PDF
pdf.output('/app/frontend/public/BOH_Hub_Admin_Manual.pdf')
print("PDF generated successfully!")
print("Download URL: /BOH_Hub_Admin_Manual.pdf")
