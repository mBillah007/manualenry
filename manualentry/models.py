from django.db import models
from django.conf import settings  # CustomUser এর জন্য settings.AUTH_USER_MODEL ব্যবহার করা সেফ

# 🛡️ আপনার দেওয়া কমন অডিট অবজেক্ট ট্র্যাক ফ্রেমওয়ার্ক
class AuditModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created Time")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated Time")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="%(class)s_created",
        verbose_name="Created By"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="%(class)s_updated",
        verbose_name="Updated By"
    )

    class Meta:
        abstract = True

# ১. Terminal Model
class Terminal(AuditModel):
    # ID অটোমেটিক জেনারেট হবে (Django default), আলাদা করে লিখার প্রয়োজন নেই।
    code = models.CharField(max_length=50, unique=True, verbose_name="Terminal Code")
    value = models.CharField(max_length=255, verbose_name="Value")
    description = models.TextField(null=True, blank=True, verbose_name="Description")

    def __str__(self):
        return f"{self.code} - {self.value}"


# 📊 ম্যানুয়াল এন্ট্রি লগ ক্যালকুলেশন মডেল
class ManualEntry(AuditModel):  # AuditModel ইনহেরিট করা হলো
    first_entry = models.IntegerField(default=0)
    second_entry = models.IntegerField(default=0)
    default_entry = models.IntegerField(default=1)
    total_terminal = models.ForeignKey(Terminal, on_delete=models.SET_NULL, null=True, blank=True)

    @property
    def calculated_net(self):
        first = self.first_entry or 0
        second = self.second_entry or 0
        default = self.default_entry or 0
        
        if second > first:
            return second - first - default
        return first - second - default

    def __str__(self):
        return f"Entry #{self.id} - Net: {self.calculated_net}"