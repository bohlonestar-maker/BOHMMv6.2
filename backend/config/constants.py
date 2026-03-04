# Application constants - chapters, titles, permissions, and Discord configuration
import os

# =============================================================================
# Discord Configuration (from environment)
# =============================================================================
DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
DISCORD_CLIENT_ID = os.environ.get('DISCORD_CLIENT_ID')
DISCORD_CLIENT_SECRET = os.environ.get('DISCORD_CLIENT_SECRET')
DISCORD_PUBLIC_KEY = os.environ.get('DISCORD_PUBLIC_KEY')
DISCORD_GUILD_ID = os.environ.get('DISCORD_GUILD_ID')
DISCORD_SUSPENDED_ROLE_ID = os.environ.get('DISCORD_SUSPENDED_ROLE_ID')
DISCORD_HANGAROUND_ROLE_ID = os.environ.get('DISCORD_HANGAROUND_ROLE_ID')
DISCORD_PROSPECT_ROLE_ID = os.environ.get('DISCORD_PROSPECT_ROLE_ID')

# =============================================================================
# Application Constants
# =============================================================================

# Chapter definitions
CHAPTERS = ['National', 'AD', 'HA', 'HS']

# Officer titles that have special permissions
OFFICER_TITLES = [
    'Prez', 'VP', 'COO', 'S@A', 'Enf', 'SEC', 'CD', 'T', 
    'ENF', 'PM', 'CC', 'CMD', 'CCLC', 'NVP', 'NPrez'
]

# Titles that can edit A&D (fallback - actual control via permissions)
AD_EDIT_TITLES = ['SEC', 'NVP', 'NPrez', 'Prez', 'VP', 'T']

# All manageable titles in the permission system
MANAGEABLE_TITLES = [
    "Prez", "VP", "COO", "S@A", "ENF", "SEC", "T", "CD", 
    "CC", "CCLC", "MD", "PM", "(pm)", "Brother", "Honorary"
]

# Available permissions that can be assigned via Permission Panel
AVAILABLE_PERMISSIONS = [
    {"key": "ad_page_access", "label": "A&D Page Access", "description": "Can view Attendance & Dues page"},
    {"key": "view_national_ad", "label": "View National A&D", "description": "Can view National chapter's Attendance & Dues data"},
    {"key": "edit_attendance", "label": "Edit Attendance", "description": "Can record and edit attendance on A&D page"},
    {"key": "edit_dues", "label": "Edit Dues", "description": "Can update dues status on A&D page"},
    {"key": "view_promotions", "label": "View Promotions Page", "description": "Can access Promotions page to manage Discord roles and member titles"},
    {"key": "view_full_member_info", "label": "View Full Member Info", "description": "Can see all member details (address, DOB, etc.)"},
    {"key": "view_private_personal_email", "label": "View Private Personal Email", "description": "Can see personal emails even if marked private"},
    {"key": "edit_members", "label": "Edit Members", "description": "Can add/edit/delete members"},
    {"key": "view_prospects", "label": "View Prospects", "description": "Can access Prospects page"},
    {"key": "manage_store", "label": "Manage Store", "description": "Can add/edit store products"},
    {"key": "view_reports", "label": "View Reports", "description": "Can access Reports page"},
    {"key": "manage_events", "label": "Manage Events", "description": "Can add/edit events"},
    {"key": "manage_system_users", "label": "Manage System Users", "description": "Can add/edit system user accounts"},
    {"key": "manage_dues_reminders", "label": "Manage Dues Reminders", "description": "Can view/edit dues reminder emails and run checks"},
    {"key": "send_documents", "label": "Send Documents", "description": "Can send SignNow documents for signing to members"},
]
