from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER

# Create PDF document
doc = SimpleDocTemplate(
    "/app/frontend/public/BOH_Hub_Admin_Manual.pdf",
    pagesize=letter,
    rightMargin=72,
    leftMargin=72,
    topMargin=72,
    bottomMargin=72
)

# Styles
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='MainTitle', fontSize=36, alignment=TA_CENTER, spaceAfter=20, textColor=colors.HexColor('#1a365d')))
styles.add(ParagraphStyle(name='SubTitle', fontSize=24, alignment=TA_CENTER, spaceAfter=10, textColor=colors.HexColor('#1a365d')))
styles.add(ParagraphStyle(name='Chapter', fontSize=24, spaceBefore=30, spaceAfter=15, textColor=colors.HexColor('#1a365d'), borderWidth=2, borderColor=colors.HexColor('#3182ce'), borderPadding=5))
styles.add(ParagraphStyle(name='Section', fontSize=16, spaceBefore=20, spaceAfter=10, textColor=colors.HexColor('#2c5282')))
styles.add(ParagraphStyle(name='SubSection', fontSize=13, spaceBefore=15, spaceAfter=8, textColor=colors.HexColor('#2b6cb0')))
styles.add(ParagraphStyle(name='BodyText', fontSize=11, spaceAfter=6, textColor=colors.HexColor('#333333'), leading=14))
styles.add(ParagraphStyle(name='BulletText', fontSize=11, spaceAfter=4, leftIndent=20, textColor=colors.HexColor('#333333'), leading=14))
styles.add(ParagraphStyle(name='NumberedText', fontSize=11, spaceAfter=4, leftIndent=20, textColor=colors.HexColor('#333333'), leading=14))

story = []

# Title Page
story.append(Spacer(1, 2*inch))
story.append(Paragraph('BOH Hub', styles['MainTitle']))
story.append(Paragraph('Administrator Manual', styles['SubTitle']))
story.append(Spacer(1, 0.5*inch))
story.append(Paragraph('Version 2.0 | February 2026', styles['BodyText']))
story.append(Spacer(1, 2*inch))
story.append(Paragraph('<i>Member Management System</i>', styles['BodyText']))
story.append(PageBreak())

# Table of Contents
story.append(Paragraph('Table of Contents', styles['Chapter']))
toc = [
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
for item in toc:
    story.append(Paragraph(item, styles['BodyText']))
story.append(PageBreak())

# Section 1: Getting Started
story.append(Paragraph('1. Getting Started', styles['Chapter']))

story.append(Paragraph('Logging In', styles['Section']))
story.append(Paragraph('To access the BOH Hub system:', styles['BodyText']))
story.append(Paragraph('1. Navigate to the application URL', styles['NumberedText']))
story.append(Paragraph('2. Enter your Username and Password', styles['NumberedText']))
story.append(Paragraph('3. Click Sign In', styles['NumberedText']))

story.append(Paragraph('User Roles', styles['Section']))
story.append(Paragraph('The system has four access levels:', styles['BodyText']))
role_data = [
    ['Role', 'Access Level'],
    ['Admin', 'Full system access, all features'],
    ['National Officer', 'Chapter management, dues, officer tracking'],
    ['Chapter Officer', 'Limited to own chapter members'],
    ['Member', 'View own profile and dues only']
]
role_table = Table(role_data, colWidths=[1.5*inch, 4*inch])
role_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#edf2f7')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 10),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('PADDING', (0, 0), (-1, -1), 6),
]))
story.append(Spacer(1, 0.2*inch))
story.append(role_table)

story.append(Paragraph('Navigation', styles['Section']))
story.append(Paragraph('The main navigation menu includes:', styles['BodyText']))
nav_items = [
    '• Dashboard - Home page with overview',
    '• Members - Member directory',
    '• Prospects - Prospect and Hangaround management',
    '• Officer Tracking - Dues and reminders',
    '• Meeting Manager - Meeting scheduling',
    '• Discord Analytics - Voice/text activity',
    '• Admin - System settings (Admin only)'
]
for item in nav_items:
    story.append(Paragraph(item, styles['BulletText']))

story.append(PageBreak())

# Section 2: Dashboard
story.append(Paragraph('2. Dashboard Overview', styles['Chapter']))
story.append(Paragraph('The Dashboard provides a quick overview of the organization status.', styles['BodyText']))

story.append(Paragraph('My Dues Section', styles['Section']))
dues_items = [
    '• Current month dues status',
    '• Recent payment history',
    '• Year-at-a-glance calendar showing paid/unpaid months'
]
for item in dues_items:
    story.append(Paragraph(item, styles['BulletText']))

story.append(Paragraph('Quick Stats', styles['Section']))
stats_items = [
    '• Total active members',
    '• Upcoming birthdays and anniversaries',
    '• Recent activity'
]
for item in stats_items:
    story.append(Paragraph(item, styles['BulletText']))

story.append(PageBreak())

# Section 3: Member Management
story.append(Paragraph('3. Member Management', styles['Chapter']))

story.append(Paragraph('Adding a New Member', styles['Section']))
story.append(Paragraph('1. Click "Add Member" button on Dashboard', styles['NumberedText']))
story.append(Paragraph('2. Fill in required fields: Handle, Name, Email, Phone', styles['NumberedText']))
story.append(Paragraph('3. Set Chapter, Title, Join Date, Birthday', styles['NumberedText']))
story.append(Paragraph('4. Click "Save"', styles['NumberedText']))

story.append(Paragraph('Editing a Member', styles['Section']))
story.append(Paragraph('1. Find member in the directory', styles['NumberedText']))
story.append(Paragraph('2. Click the three-dot menu', styles['NumberedText']))
story.append(Paragraph('3. Select "Edit" and update fields', styles['NumberedText']))
story.append(Paragraph('4. Click "Save Changes"', styles['NumberedText']))

story.append(Paragraph('Archiving a Member', styles['Section']))
story.append(Paragraph('When a member leaves the organization:', styles['BodyText']))
story.append(Paragraph('1. Click three-dot menu > "Archive"', styles['NumberedText']))
story.append(Paragraph('2. Enter deletion reason', styles['NumberedText']))
story.append(Paragraph('3. Optional: Check "Also kick from Discord server"', styles['NumberedText']))
story.append(Paragraph('4. Optional: Check "Cancel Square subscription" (default: on)', styles['NumberedText']))
story.append(Paragraph('5. Click "Archive Member"', styles['NumberedText']))

story.append(Paragraph('Member Profile Fields', styles['Section']))
field_data = [
    ['Field', 'Description', 'Encrypted'],
    ['Handle', 'Discord/display name', 'No'],
    ['Name', 'Legal full name', 'Yes'],
    ['Email', 'Contact email', 'Yes'],
    ['Phone', 'Phone number', 'Yes'],
    ['Address', 'Mailing address', 'Yes'],
    ['Chapter', 'Chapter assignment', 'No'],
    ['Title', 'Role in organization', 'No'],
    ['Join Date', 'MM/YYYY start date', 'No'],
    ['Birthday', 'MM/DD for notifications', 'No']
]
field_table = Table(field_data, colWidths=[1.2*inch, 2.8*inch, 1*inch])
field_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#edf2f7')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 10),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('PADDING', (0, 0), (-1, -1), 6),
]))
story.append(Spacer(1, 0.2*inch))
story.append(field_table)

story.append(PageBreak())

# Section 4: Dues Management
story.append(Paragraph('4. Dues Management', styles['Chapter']))

story.append(Paragraph('Understanding Dues Status', styles['Section']))
story.append(Paragraph('Each month can have one of these statuses:', styles['BodyText']))
story.append(Paragraph('• Paid (Green) - Payment confirmed', styles['BulletText']))
story.append(Paragraph('• Unpaid (Gray) - No payment recorded', styles['BulletText']))
story.append(Paragraph('• Suspended (Red) - Member suspended for non-payment', styles['BulletText']))

story.append(Paragraph('Viewing Member Dues', styles['Section']))
story.append(Paragraph('1. Go to Officer Tracking', styles['NumberedText']))
story.append(Paragraph('2. Click the Dues tab', styles['NumberedText']))
story.append(Paragraph('3. Select a month from the dropdown', styles['NumberedText']))
story.append(Paragraph('4. View all members and their status', styles['NumberedText']))

story.append(Paragraph('Manually Updating Dues', styles['Section']))
story.append(Paragraph('1. Find the member in the Dues tab', styles['NumberedText']))
story.append(Paragraph('2. Click "Update" next to their name', styles['NumberedText']))
story.append(Paragraph('3. Select new status and add notes', styles['NumberedText']))
story.append(Paragraph('4. Click "Save"', styles['NumberedText']))

story.append(Paragraph('Dues Reminders', styles['Section']))
story.append(Paragraph('The system automatically sends email reminders:', styles['BodyText']))
story.append(Paragraph('• Day 3: First reminder', styles['BulletText']))
story.append(Paragraph('• Day 8: Second reminder', styles['BulletText']))
story.append(Paragraph('• Day 10: Final warning before suspension', styles['BulletText']))

story.append(Paragraph('Dues Extensions', styles['Section']))
story.append(Paragraph('To grant extra time to pay:', styles['BodyText']))
story.append(Paragraph('1. Find member in Dues list', styles['NumberedText']))
story.append(Paragraph('2. Click "Grant Extension"', styles['NumberedText']))
story.append(Paragraph('3. Select end date and enter reason', styles['NumberedText']))
story.append(Paragraph('4. Click "Confirm"', styles['NumberedText']))

story.append(PageBreak())

# Section 5: Square Integration
story.append(Paragraph('5. Square Payment Integration', styles['Chapter']))

story.append(Paragraph('Automatic Sync', styles['Section']))
story.append(Paragraph('The system automatically syncs with Square hourly to:', styles['BodyText']))
story.append(Paragraph('• Match subscription payments to members', styles['BulletText']))
story.append(Paragraph('• Update dues status for paid months', styles['BulletText']))
story.append(Paragraph('• Track one-time payments', styles['BulletText']))

story.append(Paragraph('Manual Sync', styles['Section']))
story.append(Paragraph('1. Go to Officer Tracking > Dues tab', styles['NumberedText']))
story.append(Paragraph('2. Click "Sync Square"', styles['NumberedText']))
story.append(Paragraph('3. Review any unmatched payments', styles['NumberedText']))

story.append(Paragraph('Viewing Subscriptions', styles['Section']))
story.append(Paragraph('Click "View Subscriptions" in the Dues tab to see:', styles['BodyText']))
story.append(Paragraph('• Matched Subscriptions - Linked to members', styles['BulletText']))
story.append(Paragraph('• Unmatched Subscriptions - Need manual linking', styles['BulletText']))

story.append(Paragraph('Linking Unmatched Subscriptions', styles['Section']))
story.append(Paragraph('1. Find the unmatched subscription', styles['NumberedText']))
story.append(Paragraph('2. Click "Link"', styles['NumberedText']))
story.append(Paragraph('3. Select member and confirm', styles['NumberedText']))

story.append(Paragraph('Cancelling Unmatched Subscriptions', styles['Section']))
story.append(Paragraph('For subscriptions of former members:', styles['BodyText']))
story.append(Paragraph('1. Find the unmatched subscription', styles['NumberedText']))
story.append(Paragraph('2. Click "Cancel"', styles['NumberedText']))
story.append(Paragraph('3. Confirm the cancellation', styles['NumberedText']))

story.append(Paragraph('Payment Types', styles['Section']))
pay_data = [
    ['Type', 'Description'],
    ['Monthly Subscription', '$30/month recurring'],
    ['6-Month Prepay', '$180 one-time'],
    ['Annual Prepay', '$330 one-time']
]
pay_table = Table(pay_data, colWidths=[2*inch, 3*inch])
pay_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#edf2f7')),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 10),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
    ('PADDING', (0, 0), (-1, -1), 6),
]))
story.append(Spacer(1, 0.2*inch))
story.append(pay_table)

story.append(PageBreak())

# Section 6: Discord Integration
story.append(Paragraph('6. Discord Integration', styles['Chapter']))

story.append(Paragraph('Discord Bot Features', styles['Section']))
story.append(Paragraph('The integrated Discord bot provides:', styles['BodyText']))
story.append(Paragraph('• Birthday and anniversary notifications', styles['BulletText']))
story.append(Paragraph('• Voice channel tracking', styles['BulletText']))
story.append(Paragraph('• Text activity logging', styles['BulletText']))
story.append(Paragraph('• Role-based permissions', styles['BulletText']))

story.append(Paragraph('Notifications', styles['Section']))
story.append(Paragraph('Automatic notifications sent to designated channels:', styles['BodyText']))
story.append(Paragraph('• Birthdays: Posted on members birthday', styles['BulletText']))
story.append(Paragraph('• Anniversaries: Posted on 1st of join month', styles['BulletText']))

story.append(Paragraph('Prospect Channel Analytics', styles['Section']))
story.append(Paragraph('Special tracking for Prospect voice channels:', styles['BodyText']))
story.append(Paragraph('1. Go to Prospects page', styles['NumberedText']))
story.append(Paragraph('2. Click "Channel Analytics"', styles['NumberedText']))
story.append(Paragraph('Features include:', styles['BodyText']))
story.append(Paragraph('• Live view of current users', styles['BulletText']))
story.append(Paragraph('• Time spent with each prospect', styles['BulletText']))
story.append(Paragraph('• Historical session data', styles['BulletText']))

story.append(PageBreak())

# Section 7: Prospects & Hangarounds
story.append(Paragraph('7. Prospects & Hangarounds', styles['Chapter']))

story.append(Paragraph('Pipeline Overview', styles['Section']))
story.append(Paragraph('Two-stage prospecting workflow:', styles['BodyText']))
story.append(Paragraph('1. Hangaround - Initial contact, minimal info required', styles['NumberedText']))
story.append(Paragraph('2. Prospect - Full information required', styles['NumberedText']))

story.append(Paragraph('Managing Hangarounds', styles['Section']))
story.append(Paragraph('Adding a Hangaround:', styles['BodyText']))
story.append(Paragraph('1. Go to Prospects > Hangarounds tab', styles['NumberedText']))
story.append(Paragraph('2. Click "Add Hangaround"', styles['NumberedText']))
story.append(Paragraph('3. Enter Handle (required)', styles['NumberedText']))
story.append(Paragraph('4. Click "Save"', styles['NumberedText']))

story.append(Paragraph('Promoting to Prospect:', styles['BodyText']))
story.append(Paragraph('1. Click "Promote" on the hangaround', styles['NumberedText']))
story.append(Paragraph('2. Fill in required information', styles['NumberedText']))
story.append(Paragraph('3. Click "Confirm Promotion"', styles['NumberedText']))

story.append(PageBreak())

# Section 8-12 (abbreviated)
story.append(Paragraph('8. Officer Tracking', styles['Chapter']))
story.append(Paragraph('The Officer Tracking section provides tools for managing dues, reminders, and reports.', styles['BodyText']))
story.append(Paragraph('• Dues Tab - View and update member dues by month', styles['BulletText']))
story.append(Paragraph('• Reminders Tab - View sent reminders and resend if needed', styles['BulletText']))
story.append(Paragraph('• Reports Tab - Access financial summaries', styles['BulletText']))

story.append(PageBreak())

story.append(Paragraph('9. Meeting Management', styles['Chapter']))
story.append(Paragraph('Creating a Meeting:', styles['BodyText']))
story.append(Paragraph('1. Go to Meeting Manager', styles['NumberedText']))
story.append(Paragraph('2. Click "Schedule Meeting"', styles['NumberedText']))
story.append(Paragraph('3. Enter meeting details', styles['NumberedText']))
story.append(Paragraph('4. Click "Create"', styles['NumberedText']))

story.append(Paragraph('Taking Attendance:', styles['BodyText']))
story.append(Paragraph('1. Open the meeting', styles['NumberedText']))
story.append(Paragraph('2. Click "Take Attendance"', styles['NumberedText']))
story.append(Paragraph('3. Check off members present', styles['NumberedText']))
story.append(Paragraph('4. Click "Save Attendance"', styles['NumberedText']))

story.append(PageBreak())

story.append(Paragraph('10. Analytics & Reports', styles['Chapter']))
story.append(Paragraph('Discord Analytics:', styles['BodyText']))
story.append(Paragraph('• Voice channel participation', styles['BulletText']))
story.append(Paragraph('• Text message activity', styles['BulletText']))
story.append(Paragraph('• Most active members', styles['BulletText']))

story.append(PageBreak())

story.append(Paragraph('11. System Administration', styles['Chapter']))
story.append(Paragraph('Creating Admin Users:', styles['BodyText']))
story.append(Paragraph('1. Go to Admin section', styles['NumberedText']))
story.append(Paragraph('2. Click "Add User"', styles['NumberedText']))
story.append(Paragraph('3. Enter username/password', styles['NumberedText']))
story.append(Paragraph('4. Select role and click "Create"', styles['NumberedText']))

story.append(PageBreak())

story.append(Paragraph('12. Troubleshooting', styles['Chapter']))

story.append(Paragraph('Square Payments Not Syncing', styles['Section']))
story.append(Paragraph('1. Check Square API connection', styles['NumberedText']))
story.append(Paragraph('2. Verify API keys are valid', styles['NumberedText']))
story.append(Paragraph('3. Run manual sync', styles['NumberedText']))
story.append(Paragraph('4. Check for unmatched payments', styles['NumberedText']))

story.append(Paragraph('Discord Bot Offline', styles['Section']))
story.append(Paragraph('1. Check Discord bot status', styles['NumberedText']))
story.append(Paragraph('2. Verify bot token is valid', styles['NumberedText']))
story.append(Paragraph('3. Check server permissions', styles['NumberedText']))

story.append(Paragraph('Quick Reference - Status Colors', styles['Section']))
color_data = [
    ['Color', 'Meaning'],
    ['Green', 'Paid/Active/Success'],
    ['Yellow', 'Pending/Warning'],
    ['Red', 'Unpaid/Suspended/Error'],
    ['Gray', 'Inactive/Archived']
]
color_table = Table(color_data, colWidths=[1.5*inch, 3.5*inch])
color_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#edf2f7')),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 10),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
    ('PADDING', (0, 0), (-1, -1), 6),
]))
story.append(Spacer(1, 0.2*inch))
story.append(color_table)

story.append(Spacer(1, 0.5*inch))
story.append(Paragraph('Document Version: 2.0 | Last Updated: February 2026', styles['BodyText']))
story.append(Paragraph('BOH Hub - Member Management System', styles['BodyText']))

# Build PDF
doc.build(story)
print("PDF generated successfully!")
print("Download at: https://attendance-mgr-4.preview.emergentagent.com/BOH_Hub_Admin_Manual.pdf")
