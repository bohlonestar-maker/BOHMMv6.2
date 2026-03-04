# Models package - exports all Pydantic models
from .user import (
    User, UserCreate, UserUpdate, UserResponse,
    Invite, InviteCreate, InviteAccept,
    LoginRequest, LoginResponse,
    PasswordResetRequest, PasswordResetConfirm,
    PasswordChange, OwnPasswordChange,
    AuditLog
)
from .member import (
    Member, MemberCreate, MemberUpdate,
    Hangaround, HangaroundCreate, HangaroundUpdate,
    Prospect, ProspectCreate, ProspectUpdate,
    HangaroundToProspectPromotion,
    FallenMember, FallenMemberCreate, FallenMemberUpdate
)
from .event import Event, EventCreate, EventUpdate
from .meeting import Meeting, MeetingCreate, MeetingAttendanceRecord
from .message import (
    PrivateMessage, PrivateMessageCreate,
    SupportMessage, SupportMessageCreate, SupportReply,
    SupportRequest
)
from .discord import (
    DiscordMember, DiscordVoiceActivity, DiscordTextActivity, DiscordAnalytics,
    DiscordLinkRequest, UpdateRolesRequest, UpdateNicknameRequest
)
from .store import (
    ProductVariation, StoreProduct, StoreProductCreate, StoreProductUpdate,
    CartItem, ShoppingCart, StoreOrder, PaymentRequest,
    StoreAdmin, StoreAdminCreate, SupporterCheckoutRequest
)
from .dues import (
    AttendanceRecord, DuesRecord, DuesExtensionCreate, DuesExtensionUpdate,
    SuspendMemberRequest, ForgiveDuesRequest, BulkDuesCorrectionRequest,
    DuesEmailTemplateUpdate, LinkSubscriptionRequest
)
from .permissions import PermissionUpdate, BulkPermissionUpdate
from .ai import ChatMessage, AIKnowledgeEntry, AIKnowledgeUpdate
from .suggestions import SuggestionCreate, SuggestionStatusUpdate, SuggestionVote
from .signnow import SendDocumentRequest
