from django.core.management.base import BaseCommand
from django.db import connections, OperationalError
from django.contrib.auth.hashers import make_password
from django.core.management import call_command
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from mainsystem.models import (
    Role,  CustomUser, ModuleGroup, Module, ActionType, Permission, ActionType
)
from hrm.models import (    
    Department, Profile,
)
from mainsystem.context_processors import MODULE_LAYOUT, SUPERADMIN_MODULES

class Command(BaseCommand): 
    help = "🎯 Full or Partial System Setup: Roles, Users, Modules, Permissions, Diagnostics, BedType, PaymentMethodType" 
    def add_arguments(self, parser): 
        parser.add_argument( 
            '--only', 
            nargs='+', 
            type=str, 
            help='🔧 শুধুমাত্র নির্দিষ্ট ফাংশন চালাতে চাইলে তাদের নাম দিন (যেমন: setup_modules setup_roles)'
        ) 
    def handle(self, *args, **options):
        if not self.check_db():
            return 
        call_command('migrate', interactive=False) 
        self.stdout.write(self.style.SUCCESS("✅ মাইগ্রেশন সম্পন্ন")) 
        only = options.get('only') 
        steps = { 
            'setup_action_types': self.setup_action_types,
            'setup_roles': self.setup_roles, 
            'setup_department': self.setup_department, 
            'setup_default_users': self.setup_default_users, 
            'setup_modules': self.setup_modules, 
            'assign_permissions': self.assign_permissions, 
        } 
        if only: 
            for step in only: 
                func = steps.get(step) 
                if func: 
                    self.stdout.write(f"⚙️ Executing: {step}") 
                    func() 
                else: 
                    self.stdout.write(self.style.WARNING(f"⚠️ '{step}' ফাংশন খুঁজে পাওয়া যায়নি")) 
        else:
            self.action_map = self.setup_action_types() 
            self.role_map = self.setup_roles()
            self.default_department = self.setup_department() 
            self.setup_default_users()
            self.setup_modules() 
            self.assign_permissions()
        self.stdout.write(self.style.SUCCESS("🎯 সেটআপ প্রক্রিয়া সম্পন্ন ✅")) 
    def check_db(self):
        try:
            connections['default'].ensure_connection()
            self.stdout.write(self.style.SUCCESS("✅ ডাটাবেজ সংযোগ সফল"))
            return True
        except OperationalError:
            self.stdout.write(self.style.ERROR("❌ ডাটাবেজ সংযোগ ব্যর্থ")) 
            return False

    def setup_action_types(self):
        keys = ['access', 'create', 'edit', 'delete']
        action_map = {}
        for i, key in enumerate(keys):
            action, _ = ActionType.objects.get_or_create(
                key=key,
                defaults={'name_bn': key.title(), 'order': i}
            )
            action_map[key] = action
        return action_map

    def setup_roles(self):
        names = [
            "SystemAdmin", "Admin"
        ]
        role_map = {}
        for name in names:
            role, _ = Role.objects.get_or_create(name=name)
            role_map[name] = role
        return role_map

    def setup_department(self):
        dept, _ = Department.objects.get_or_create(name="Administration", code="ADM")
        return dept

    def setup_default_users(self):
        # টাপল-এ ৩ নম্বর এলিমেন্ট হিসেবে is_superuser এর ভ্যালু (True/False) পাস করা হয়েছে
        users = [
            ("sadmin", "SystemAdmin", True),  # sadmin হবে আসল Django Superuser
            ("admin", "Admin", False),       # admin হবে সাধারণ স্টাফ/ম্যানেজার
        ]
        
        for username, role_key, is_superuser_status in users:
            user, created = CustomUser.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"{username}@example.com",
                    "is_staff": True,
                    "is_superuser": is_superuser_status,  # জ্যাঙ্গোর ডিফল্ট সুপারইউজার ফ্ল্যাগ
                    "role": self.role_map[role_key],
                    "password": make_password("123456"),
                    "is_protected": True if is_superuser_status else False, # সুপারইউজারকে সুরক্ষিত (Protected) করা হলো
                }
            )
            
            # প্রোফাইল তৈরি বা গেট করা
            Profile.objects.get_or_create(
                user=user, 
                defaults={
                    "department": self.default_department,
                    "designation": role_key
                }
            )
    
    def to_pascal_case(self, s):
        return ''.join(word.capitalize() for word in s.split('_'))

    def setup_modules(self):
        # Ensure action_map is initialized
        if not hasattr(self, 'action_map') or not self.action_map:
            self.action_map = self.setup_action_types()

        for group_name, modules in MODULE_LAYOUT.items():
            group, _ = ModuleGroup.objects.get_or_create(name=group_name)

            for parent_url, config in modules.items():
                config = config or {}

                # Check for existing module by class_name to avoid duplicates
                class_name = config.get("class_name")
                existing = Module.objects.filter(class_name=class_name).first() if class_name else None

                if existing:
                    parent = existing
                    self.stdout.write(f"⚠️ Skipping duplicate module: {class_name}")
                else:
                    parent, _ = Module.objects.get_or_create(
                        url_name=parent_url,
                        defaults={
                            "name": config.get("label", parent_url.split(":")[-1].replace('_', ' ').title()),
                            "label": config.get("label"),
                            "group": group,
                            "icon": config.get("icon", "bi-speedometer"),
                            "class_name": class_name,
                            "is_visible": True,
                            "is_header": config.get("is_header", False),
                            "order": config.get("order", 0)
                        }
                    )
                    parent.actions.set([self.action_map['access']])

                # Handle child modules
                for child_url in config.get("children", []):
                    inferred = []
                    if 'add' in child_url or 'create' in child_url:
                        inferred.append('create')
                    if 'edit' in child_url:
                        inferred.append('edit')
                    if 'delete' in child_url or 'cancel' in child_url:
                        inferred.append('delete')
                    if any(k in child_url for k in ['view', 'list', 'print', 'approve']):
                        inferred.append('access')
                    if not inferred:
                        inferred = ['access']

                    child_class = None  # Optional: infer or define child class_name if needed

                    # Prevent duplicate child modules by url_name
                    child, _ = Module.objects.get_or_create(
                        url_name=child_url,
                        defaults={
                            "name": child_url.split(":")[-1].replace('_', ' ').title(),
                            "group": group,
                            "parent": parent,
                            "icon": "bi-circle",
                            "is_visible": False,
                            "is_header": False,
                            "order": 0,
                            "class_name": child_class
                        }
                    )
                    child.actions.set([self.action_map[k] for k in inferred])

    def assign_permissions(self):
        admin = CustomUser.objects.filter(username="admin").first()
        for module in Module.objects.all():
            for action in ActionType.objects.all():
                url_key = module.url_name.split(":")[-1]
                is_allowed = url_key in SUPERADMIN_MODULES

                perm, created = Permission.objects.get_or_create(
                    role=self.role_map["SystemAdmin"],
                    module=module,
                    action=action,
                    defaults={
                        'is_allowed': is_allowed,
                        'created_by': admin,
                        'updated_by': admin,
                    }
                )

                if not created:
                    if is_allowed and not perm.is_allowed:
                        perm.is_allowed = True
                        perm.updated_by = admin
                        perm.save()
