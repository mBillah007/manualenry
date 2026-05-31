from django.db import models
from mainsystem.models import * 
from datetime import datetime, timedelta
#from attendance.models import * 

# Create your models here.
class UserType(models.Model):
    name = models.CharField(max_length=50, unique=True) # e.g., Staff, Admin
    slug = models.SlugField(max_length=50, unique=True) # e.g., staff, admin
    
    def __str__(self):
        return self.name
    
class Department(models.Model):
    name = models.CharField("Department", max_length=100, unique=True)
    code = models.CharField("Department Code", max_length=20, unique=True)
    description = models.TextField("Descriptions", blank=True)

    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"
                
class Shift(models.Model):
    SHIFT_TYPES = [
        ('Regular', 'Regular'), ('Emergency', 'Emergency'),
        ('Overtime', 'Overtime'), ('Double', 'Double'),
    ]

    name = models.CharField(max_length=50, unique=True)
    shift_type = models.CharField(max_length=20, choices=SHIFT_TYPES, default='Regular')
    start_time = models.TimeField()
    end_time = models.TimeField()
    late_grace_period = models.PositiveIntegerField(
        default=15, help_text="মিনিটে (যেমন: ১৫ মিনিট পর্যন্ত ছাড়)"
    )
    is_active = models.BooleanField(default=True)
    color_code = models.CharField(max_length=10, default="#0d6efd")

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        return f"{self.name} ({self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')})"
    @property
    def short_name(self):
        words = self.name.split()
        if len(words) >= 2:
            return f"{words[0][0]}{words[1][0]}".upper()
        return self.name[:2].upper()
    @property
    def total_hours(self):
        start = datetime.combine(datetime.today(), self.start_time)
        end = datetime.combine(datetime.today(), self.end_time)
        if end <= start: end += timedelta(days=1)
        return round((end - start).total_seconds() / 3600, 2)
class WeekDay(models.Model):
    # id হবে 0-6 (0=Monday, 6=Sunday)
    name = models.CharField(max_length=20)
class Profile(models.Model):
    # Status Choices
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('on_leave', 'On Leave'),
    )
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )
    EMPLOYMENT_TYPES = (
            ('permanent', 'Permanent'),
            ('probation', 'Probation'),
            ('contractual', 'Contractual'),
            ('intern', 'Intern'),
        )
    WEEK_DAYS = (
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'),
    )
    USER_TYPES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('staff', 'Staff'),
        ('admin', 'Admin'),
    )
    user_type = models.ForeignKey(UserType, on_delete=models.PROTECT, related_name='staff_members', null=True, blank=True)
    #user_type = models.CharField(max_length=15, choices=USER_TYPES, default='staff')
    #weekly_off = models.IntegerField(choices=WEEK_DAYS, default=4, blank=True, null=True, ) # ডিফল্ট শুক্রবার (৪)
    weekly_off = models.ManyToManyField(WeekDay, blank=True)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE,blank=True, null=True, unique=True, related_name='profile')
    
    # আইডি কার্ড বা অফিস আইডি
    staff_id = models.CharField("Staff ID", max_length=20, db_index=True, unique=True, null=True, help_text="e.g. 1001")
    device_user_id = models.CharField("Biometric Device ID", max_length=20, blank=True, null=True, unique=True)
    
    # ব্যক্তিগত তথ্য
    first_name = models.CharField("নামের প্রথম অংশ", max_length=30)
    last_name = models.CharField("নামের শেষ অংশ", max_length=30)
    father_name = models.CharField("পিতার নাম", max_length=100, blank=True)
    mother_name = models.CharField("মাতার নাম", max_length=100, blank=True)
    nid_number = models.CharField("NID নম্বর", max_length=20, blank=True, null=True, unique=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    blood_group = models.CharField(max_length=5,null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)

    # কন্টাক্ট (ইমারজেন্সি কন্টাক্ট সহ)
    phone_number = models.CharField("Primary Phone", max_length=15)
    emergency_contact = models.CharField("Emergency Contact", max_length=15, blank=True)
    present_address = models.TextField("বর্তমান ঠিকানা", blank=True)
    permanent_address = models.TextField("স্থায়ী ঠিকানা", blank=True)

    # প্রাতিষ্ঠানিক তথ্য (HR/Admin)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    designation = models.CharField("পদবি", max_length=100)
    shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True, blank=True) # 🕒 শিফটিং
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPES, default='probation')
    
    # বেতন ও তারিখ
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    joining_date = models.DateField(null=True, blank=True)
    resignation_date = models.DateField(null=True, blank=True)
    
    # স্ট্যাটাস
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_active = models.BooleanField(default=True)
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)

    class Meta:
        verbose_name = "Staff Profile"
        verbose_name_plural = "Staff Profiles"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.staff_id})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
class Education(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='educations')
    degree_name = models.CharField(max_length=100) # যেমন: SSC, Diploma, BSc
    institute = models.CharField(max_length=200)
    board_university = models.CharField(max_length=100, blank=True, null=True)
    passing_year = models.IntegerField()
    result = models.CharField(max_length=20) # যেমন: GPA 5.00 বা 1st Class

    class Meta:
        ordering = ['-passing_year'] # নতুন ডিগ্রি আগে দেখাবে

    def __str__(self):
        return f"{self.degree_name} - {self.profile.first_name}"  
class LeaveRequest(models.Model):
    LEAVE_TYPES = [('CL', 'Casual Leave'), ('SL', 'Sick Leave'), ('AL', 'Annual Leave')]
    
    # নতুন স্ট্যাটাস চয়েস
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected/Cancelled'),
    ]

    staff = models.ForeignKey('Profile', on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    leave_type = models.CharField(max_length=5, choices=LEAVE_TYPES)
    
    # পুরাতন BooleanField-এর জায়গায় আধুনিক status ফিল্ড
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    is_approved = models.BooleanField(default=False) # ব্যাকওয়ার্ড কম্প্যাটিবিলিটির জন্য রাখতে পারেন, না রাখলেও সমস্যা নেই

    # --- Audit Trail ---
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='leave_created'
    )
    
    approved_at = models.DateTimeField(null=True, blank=True) # auto_now=True বাদ দেওয়া হয়েছে সঠিক ট্র্যাকিংয়ের জন্য
    approved_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='leave_approved'
    )

    # [নতুন] ক্যান্সেল বা রিজেক্ট লগের জন্য ফিল্ডসমূহ
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejected_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='leave_rejected'
    )
    rejection_reason = models.TextField(blank=True, null=True) # কেন বাতিল করা হলো তার নোট রাখার জন্য

class PublicHoliday(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateField(unique=True)
    description = models.TextField(blank=True)