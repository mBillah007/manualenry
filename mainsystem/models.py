from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.core.exceptions import ValidationError

# --- ১. মডিউল গ্রুপ মডেল ---
class ModuleGroup(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="গ্রুপের নাম")
    icon = models.CharField(max_length=50, default='bi-folder', verbose_name="আইকন ক্লাস (Bootstrap/FontAwesome)")
    icon_unicode = models.CharField(max_length=10, blank=True, null=True, verbose_name="আইকন ইউনিকোড")
    order = models.PositiveIntegerField(default=0, verbose_name="ক্রমিক নম্বর")

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "মডিউল গ্রুপ"
        verbose_name_plural = "মডিউল গ্রুপসমূহ"

    def __str__(self):
        return self.name

# --- ২. অ্যাকশন টাইপ মডেল ---
class ActionType(models.Model):
    key = models.CharField(max_length=20, unique=True, verbose_name="অ্যাকশন কী (e.g., create, view)")
    name_bn = models.CharField(max_length=50, verbose_name="অ্যাকশন নাম (বাংলা)")
    order = models.PositiveIntegerField(default=0, verbose_name="ক্রমিক নম্বর")

    class Meta:
        ordering = ['order', 'key']
        verbose_name = "অ্যাকশন টাইপ"
        verbose_name_plural = "অ্যাকশন টাইপসমূহ"

    def __str__(self):
        return f"{self.name_bn} ({self.key})"

# --- ৩. মডিউল মডেল ---
class Module(models.Model):
    name = models.CharField(max_length=100, verbose_name="মডিউলের নাম (ইংরেজী)")
    label = models.CharField(max_length=100, blank=True, null=True, verbose_name="লেবেল (বাংলা)")    
    url_name = models.CharField(max_length=100, unique=True, verbose_name="ইউআরএল নেমস্পেস (Namespace URL)")
    class_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="CSS/JS ক্লাস টার্গেটিং")
    icon = models.CharField(max_length=50, default='bi-circle', verbose_name="আইকন ক্লাস")
    icon_unicode = models.CharField(max_length=10, blank=True, null=True, verbose_name="ইউনিকোড আইকন")
    
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children', verbose_name="প্যারেন্ট মडीউল")    
    group = models.ForeignKey(ModuleGroup, on_delete=models.SET_NULL, null=True, related_name='modules', verbose_name="মডিউল গ্রুপ")
    actions = models.ManyToManyField(ActionType, related_name='modules', verbose_name="অনুমোদিত অ্যাকশনসমূহ")
    
    order = models.PositiveIntegerField(default=0, verbose_name="ক্রমিক নম্বর")
    is_visible = models.BooleanField(default=True, verbose_name="মেনুতে দৃশ্যমান কিনা")
    is_header = models.BooleanField(default=False, verbose_name="হেডার দৃশ্যমানতা")  
    is_default = models.BooleanField(default=False, verbose_name="ডিফল্ট মডিউল")  

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "মডিউল"
        verbose_name_plural = "মডিউলসমূহ"

    def __str__(self):
        return self.label if self.label else self.name


# --- ৪. রোল মডেল ---
class Role(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="রোলের নাম")
    is_protected = models.BooleanField(default=False, verbose_name="সুরক্ষিত রোল (মুছে ফেলা যাবে না)")  
    modules = models.ManyToManyField(Module, through='Permission', verbose_name="অ্যাক্সেসযোগ্য মডিউলসমূহ")
    is_active = models.BooleanField(default=True, verbose_name="সক্রিয়")

    class Meta:
        verbose_name = "ইউজার রোল"
        verbose_name_plural = "ইউজার রোলসমূহ"

    def __str__(self):
        return self.name

    def sync_to_group(self):
        """জ্যাঙ্গোর ডিফল্ট গ্রুপের সাথে সিঙ্ক করার মেথড"""
        group, created = Group.objects.get_or_create(name=self.name)
        return group


# --- ৫. কাস্টম ইউজার মডেল ---
class CustomUser(AbstractUser):
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="ইউজার রোল")
    email = models.EmailField(unique=True, verbose_name="ইমেইল অ্যাড্রেস")
    username = models.CharField(max_length=150, unique=True, verbose_name="ইউজারনেম")
    is_active = models.BooleanField(default=True, verbose_name="অ্যাকাউন্ট সক্রিয়")
    is_staff = models.BooleanField(default=False, verbose_name="স্টাফ স্ট্যাটাস (অ্যাডমিন প্যানেল অ্যাক্সেস)")
    is_superuser = models.BooleanField(default=False, verbose_name="সুপার ইউজার স্ট্যাটাস")
    
    last_login = models.DateTimeField(auto_now=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_protected = models.BooleanField(default=False, verbose_name="সুরক্ষিত ইউজার")  

    class Meta:
        verbose_name = "ব্যবহারকারী"
        verbose_name_plural = "ব্যবহারকারীগণ"

    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"


# --- ৬. পারমিশন ম্যাট্রিক্স মডেল (Pivot Table) ---
class Permission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='permissions')
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='permissions')
    action = models.ForeignKey(ActionType, on_delete=models.CASCADE, related_name='permissions')
    
    is_allowed = models.BooleanField(default=False, db_index=True, verbose_name="অনুমতি আছে?")
    
    # Audit Trail (সুরক্ষিত রিলেশন)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='created_permissions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='updated_permissions'
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('role', 'module', 'action')
        verbose_name = "ম্যাট্রিক্স পারমিশন"
        verbose_name_plural = "ম্যাট্রিক্স পারমিশনসমূহ"

    def __str__(self):
        return f"{self.role.name} -> {self.module.name} [{self.action.key}] : {self.is_allowed}"


# --- ৭. সিগন্যাল হ্যান্ডলার (Group Sync করার জন্য নিরাপদ মাধ্যম) ---
@receiver(post_save, sender=CustomUser)
def sync_user_role_to_group(sender, instance, created, **kwargs):
    """
    ইউজার সেভ হওয়ার পর তার রোল অনুযায়ী জ্যাঙ্গো গ্রুপ অ্যাসাইন করা।
    এটি সেভ মেথডের ভেতর রাখলে রিকার্সন বা ইনফিনিট লুপের ঝুঁকি থাকে, সিগন্যালে তা সম্পূর্ণ নিরাপদ।
    """
    if instance.role:
        group = instance.role.sync_to_group()
        # ইউজার ইতিমধ্যে এই গ্রুপে না থাকলে যুক্ত করা হবে
        if not instance.groups.filter(id=group.id).exists():
            instance.groups.set([group])
    else:
        # যদি রোল রিমুভ করে দেওয়া হয়, তবে জ্যাঙ্গো গ্রুপ লিস্ট খালি করা
        if instance.groups.exists():
            instance.groups.clear()