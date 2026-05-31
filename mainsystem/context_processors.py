# mainsystem/context_processors.py
from mainsystem.models import Permission, Module, ActionType
from django.urls import reverse, NoReverseMatch
from django.db.models import Q

# Optional: Custom label mapping (for Bangla or display override)
LABEL_MAP = {
    "mainsystem:dashboard": "Dashboard",
    "mainsystem:user_list": "ইউজার তালিকা",
    "mainsystem:role_list": "রোল ম্যানেজমেন্ট",
    "products:product_list": "পণ্য তালিকা"
}
# সুপারঅ্যাডমিনের স্পেশাল মডিউল লিস্ট
SUPERADMIN_MODULES = [
    'mainsystem:user_list', 'mainsystem:user_create', 'mainsystem:user_edit', 
    'mainsystem:role_list', 'mainsystem:role_add', 'mainsystem:role_edit', 'mainsystem:role_delete', 
    'mainsystem:permission_role', 'mainsystem:permission_update',
    'mainsystem:module_list', 'mainsystem:module_add', 'mainsystem:module_edit', 'mainsystem:module_delete', 'mainsystem:module_sync',
    'mainsystem:module_group_list', 'mainsystem:module_group_save', 'mainsystem:module_group_delete'
]

MODULE_LAYOUT = {
    "Dashboard": {
        "dashboard": {
            "label": "Dashboard",
            "icon": "bi-speedometer2",
            "children": []
        }
    },
    "Settings & Control": {
        "mainsystem:user_list": {
            "label": "User Management",
            "icon": "bi-people",
            "children": [
                "mainsystem:user_create", "mainsystem:user_edit", "mainsystem:user_delete",
                "mainsystem:profile_view", "mainsystem:add_department"
            ]
        },
        "mainsystem:role_list": {
            "icon": "bi-person-badge",
            "children": [
                "mainsystem:role_add", "mainsystem:role_edit", "mainsystem:role_delete",
                "mainsystem:permission_role", "mainsystem:permission_update"
            ]
        },
        "mainsystem:module_list": {
            "icon": "bi-box",
            "children": [
                "mainsystem:module_add", "mainsystem:module_edit", "mainsystem:module_delete",
                "mainsystem:module_sync", "mainsystem:module_group_list",
                "mainsystem:module_group_save", "mainsystem:module_group_delete"
            ]
        }
    },
    "HRM & Operations": {
        "hrm:staff_list": {
            "label": "Staff Directory",
            "icon": "bi-person-badge",
            "children": [
                "hrm:staff_create",
                "hrm:staff_biodata",
                "hrm:get_staff_data",
                "hrm:staff_report",
                "hrm:single_id_card",
                "hrm:edit_department",
                "hrm:delete_department",
                "hrm:department_list_json"
            ]
        },
        "hrm:leave_list": {
            "label": "Leave Requests (ছুটির আবেদন)",
            "icon": "bi-calendar-x",
            "children": [
                "hrm:leave_create",
                "hrm:leave_edit",
                "hrm:leave_approve",
                "hrm:leave_reject"
            ]
        },
        "hrm:holiday_list": {
            "label": "Public Holidays (সরকারি ছুটি)",
            "icon": "bi-calendar-event",
            "children": [
                "hrm:holiday_create",
                "hrm:holiday_delete"
            ]
        },
        "attendance:attendance_list": {
            "label": "Daily Attendance",
            "icon": "bi-calendar-check",
            "children": [
                "attendance:mark_attendance",
                "attendance:get_attendance_data",
                "attendance:attendance_report"
            ]
        },
        "attendance:roster_master": {
            "label": "Roster & Shift Management",
            "icon": "bi-clock-history",
            "children": [
                "attendance:shift_list",
                "attendance:add_shift",
                "attendance:delete_shift",
                "attendance:roster_assign",
                "attendance:assign_bulk_shift",
                "attendance:delete_roster",
                "attendance:roster_api_events",
                "attendance:monthly_roster"
            ]
        },
        "attendance:time_device_list": {
            "label": "Biometric Devices",
            "icon": "bi-cpu",
            "children": [
                "attendance:get_device_list",
                "attendance:add_device",
                "attendance:delete_device",
                "attendance:manual_device_sync",
                "attendance:ping_device",
                "attendance:discover_devices",
                
                "attendance:device_user_add",
                "attendance:device_user_edit",
                "attendance:push_user_to_devices",
                "attendance:link_profile_to_device"
            ]
        }
    }
}

def sidebar_context(request):
    if not request.user.is_authenticated:
        return {"sidebar_groups": [], "user_role": "Guest"}

    User = request.user
    UserRoleObj = getattr(User, 'role', None)
    CurrentView = request.resolver_match.view_name if request.resolver_match else None

    # ১. রোলের নাম রিভোল্ভ করা
    if UserRoleObj and hasattr(UserRoleObj, 'name'):
        RoleName = UserRoleObj.name.upper()
    else:
        RoleName = str(UserRoleObj).upper() if UserRoleObj else ''

    IsSuperadmin = getattr(User, 'is_superuser', False) or RoleName == 'SUPERADMIN'

    # ২. ডাটাবেজ থেকে শুধুমাত্র রুট (parent__isnull=True) মডিউলগুলো কুয়েরি করা (N+1 অপ্টিমাইজড)
    # চাইল্ড মডিউলগুলো ডেটাবেজে parent_id দিয়ে কানেক্টেড থাকবে, তাই তারা এখানে সরাসরি আসবে না
    BaseModules = Module.objects.filter(is_visible=True, parent__isnull=True).select_related('group').prefetch_related('children')

    AllowedModules = []
    if IsSuperadmin:
        AllowedModules = list(BaseModules)
    else:
        # সাধারণ ইউজারদের জন্য রুট মডিউলের অ্যাক্সেস পারমিশন চেক
        AllowedModules = [
            mod for mod in BaseModules
            if has_permission(request, mod.url_name, 'access')
        ]

    # ৩. মডিউল গ্রুপিং ম্যাট্রিক্স
    GroupedModules = {}
    for mod in AllowedModules:
        GroupObj = mod.group
        if not GroupObj:
            continue
        GroupedModules.setdefault(GroupObj, []).append(mod)

    # ৪. অর্ডারিং এবং ডাটা প্রিপারেশন
    SortedGroups = sorted(GroupedModules.items(), key=lambda item: item[0].order if hasattr(item[0], 'order') else 0)
    SidebarGroups = []

    for group, mods in SortedGroups:
        GroupData = {
            "name": group.name,
            "icon": group.icon or "bi-folder",
            "modules": [],
            "active": False
        }

        SortedMods = sorted(mods, key=lambda m: m.order if hasattr(m, 'order') else 0)
        for mod in SortedMods:
            try:
                Url = reverse(mod.url_name)
            except NoReverseMatch:
                Url = "#"

            # 🔄 চিল্ড্রেন ট্র্যাক করা: কারেন্ট ভিউ যদি নিজের url_name হয় অথবা কোনো চাইল্ডের url_name হয়
            ChildUrls = list(mod.children.filter(is_visible=False).values_list('url_name', flat=True))
            
            # ডেটাবেজ রিলেশন ছাড়া হার্ডকোডেড চিল্ড্রেন সাপোর্ট ব্যাকআপ (ঐচ্ছিক নিরাপত্তা)
            if mod.url_name == "mainsystem:user_list":
                ChildUrls += ["mainsystem:user_create", "mainsystem:user_edit", "mainsystem:user_delete", "mainsystem:profile_view", "mainsystem:add_department"]

            # মেইন প্যারেন্ট অথবা তার যেকোনো চাইল্ড একটিভ থাকলে সম্পূর্ণ মডিউল একটিভ হবে
            IsActive = (mod.url_name == CurrentView) or (CurrentView in ChildUrls)

            Label = mod.label or mod.name or mod.url_name.split(":")[-1].replace("_", " ").title()

            ModuleData = {
                "name": Label,
                "url_name": mod.url_name,
                "icon": mod.icon or "bi-circle",
                "url": Url,
                "is_active": IsActive
            }

            GroupData["modules"].append(ModuleData)
            if IsActive:
                GroupData["active"] = True

        if GroupData["modules"]:
            SidebarGroups.append(GroupData)

    return {
        "sidebar_groups": SidebarGroups,
        "user_role": RoleName if RoleName else 'USER'
    }
def header_modules(request):
    """
    টপ হেডার নেভিগেশনে প্রদর্শনের জন্য নির্দিষ্ট মডিউলসমূহ ফিল্টার করে।
    """
    if not request.user.is_authenticated:
        return {'header_modules': []}

    User = request.user
    UserRoleObj = getattr(User, 'role', None)
    RoleName = UserRoleObj.name.upper() if UserRoleObj and hasattr(UserRoleObj, 'name') else ''
    IsSuperadmin = getattr(User, 'is_superuser', False) or RoleName == 'SUPERADMIN'

    BaseHeaderModules = Module.objects.filter(is_header=True)

    if IsSuperadmin:
        return {'header_modules': BaseHeaderModules}

    if not UserRoleObj:
        return {'header_modules': []}

    AccessPerms = Permission.objects.filter(role=UserRoleObj, is_allowed=True, action__key='access')
    AllowedHeaderModules = BaseHeaderModules.filter(id__in=AccessPerms.values('module_id'))

    return {'header_modules': AllowedHeaderModules}


def has_permission(request, module_url_name, action_key='access'):
    """
    যেকোনো ভিউ বা টেমপ্লেট থেকে সিঙ্গেল রানটাইম পারমিশন চেক করার গ্লোবাল হেল্পার ফাংশন।
    """
    User = request.user
    if not User.is_authenticated:
        return False

    UserRoleObj = getattr(User, 'role', None)
    RoleName = UserRoleObj.name.upper() if UserRoleObj and hasattr(UserRoleObj, 'name') else ''
    
    # সুপারঅ্যাডমিন হলে সরাসরি অনুমতি প্রদান
    if getattr(User, 'is_superuser', False) or RoleName == 'SUPERADMIN':
        return True

    if not UserRoleObj:
        return False

    try:
        ModuleObj = Module.objects.get(url_name=module_url_name)
        ActionObj = ActionType.objects.get(key=action_key)
    except (Module.DoesNotExist, ActionType.DoesNotExist):
        return False

    return Permission.objects.filter(
        role=UserRoleObj,
        module=ModuleObj,
        action=ActionObj,
        is_allowed=True
    ).exists()


def permissions(request): 
    """
    টেমপ্লেটে ডাইনামিক ল্যাম্বডা ফাংশন কলিং ইনেবল করে।
    ব্যবহার: {% if has_permission.products.product_list %} ... {% endif %}
    """
    return { 
        'has_permission': lambda module, action='access': has_permission(request, module, action) 
    }


def permissions_matrix(request):
    """
    একক কুয়েরিতে সব পারমিশন ক্যাশ মেমোরিতে ডিকশনারি করে টেমপ্লেটে পাঠায় (হাই-পারফর্ম্যান্স পেজ লোড)।
    ব্যবহার: {% if permissions_matrix|get_item:my_key %}
    """
    if not request.user.is_authenticated:
        return {'permissions_matrix': {}}

    User = request.user
    UserRoleObj = getattr(User, 'role', None)
    Matrix = {}

    if UserRoleObj:
        Perms = Permission.objects.filter(role=UserRoleObj, is_allowed=True).select_related('module', 'action')
        for perm in Perms:
            Matrix[(perm.module.url_name, perm.action.key)] = True

    return {
        'permissions_matrix': Matrix
    }