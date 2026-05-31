import calendar
import io
import json
import socket
from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Count, FloatField, IntegerField, Prefetch, Q, Sum
from django.db.models.functions import Cast
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import get_resolver, reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_POST
import qrcode
from zk import ZK

# --- প্রজেক্ট অ্যাপস ও কাস্টম মডেলস ইমপোর্ট ---
from hrm.forms import LeaveRequestForm, ProfileForm, PublicHolidayForm
from hrm.models import Department, LeaveRequest, Profile, PublicHoliday
from mainsystem.context_processors import has_permission
from mainsystem.models import ActionType, Module, ModuleGroup

# নোট: সেফটি এবং লোকাল মডেল ওভাররাইড এড়াতে ওয়াইল্ডকার্ড (*) ইমপোর্ট সবার শেষে রাখা হয়েছে
from .models import *


# =========================================================================
#                             VIEWS LOGIC START
# =========================================================================

def get_refined_dashboard_data(today):
    return {
        'total_staff': Profile.objects.filter(status='active').count(),
    }

@login_required
def dashboard(request):
    """প্রথমবার পেজ লোডের ভিউ"""
    today = timezone.now().date()
    stats = get_refined_dashboard_data(today)
    context = {
        'today': today,
        **stats
    }
    return render(request, 'hrm/dashboard.html', context)

#--- ড্যাশবোর্ড এপিআই ভিউ (লাইভ জেসব রিকোয়েস্ট হ্যান্ডেল করার জন্য) ---
@login_required
def dashboard_api(request):
    today = timezone.now().date()
    stats = get_refined_dashboard_data(today)
    
    stats['upcoming_holidays'] = [
        {'name': h.name, 'date': h.date.strftime('%d %b')} for h in stats['upcoming_holidays']
    ]
    return JsonResponse(stats)

#--- Leave Requests Views ---
@login_required
def leave_list(request):
    leaves = LeaveRequest.objects.select_related('staff').all().order_by('-created_at')
    return render(request, 'hrm/leave_list.html', {'leaves': leaves})

@login_required
def leave_create(request):
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.created_by = request.user
            leave.save()
            messages.success(request, "ছুটির আবেদনটি সফলভাবে জমা দেওয়া হয়েছে।")
            return redirect('hrm:leave_list')
    else:
        form = LeaveRequestForm()
    return render(request, 'hrm/leave_form.html', {'form': form, 'title': 'নতুন ছুটির আবেদন'})

@login_required
def leave_edit(request, id):
    leave = get_object_or_404(LeaveRequest, id=id)
    
    was_approved = leave.is_approved
    old_start_date = leave.start_date
    old_end_date = leave.end_date
    old_staff = leave.staff
    
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST, instance=leave)
        if form.is_valid():
            updated_leave = form.save()
            
            if was_approved:
                current_date = old_start_date
                while current_date <= old_end_date:
                    Attendance.objects.filter(staff=old_staff, date=current_date, status='On Leave').delete()
                    current_date += timedelta(days=1)
                
                new_current_date = updated_leave.start_date
                while new_current_date <= updated_leave.end_date:
                    Attendance.objects.update_or_create(
                        staff=updated_leave.staff,
                        date=new_current_date,
                        defaults={'status': 'On Leave', 'source': 'Manual'}
                    )
                    new_current_date += timedelta(days=1)
            
            messages.success(request, "মঞ্জুরকৃত ছুটির আবেদনটি সফলভাবে সংশোধন করা হয়েছে এবং উপস্থিতির রেকর্ড আপডেট করা হয়েছে।")
            return redirect('hrm:leave_list')
    else:
        form = LeaveRequestForm(instance=leave)
        
    return render(request, 'hrm/leave_form.html', {
        'form': form, 
        'title': f'{leave.staff.full_name}-এর ছুটির আবেদন সংশোধন (মঞ্জুরকৃত)',
        'was_approved': was_approved
    })

@login_required
def leave_approve(request, id):
    leave = get_object_or_404(LeaveRequest, id=id)
    
    if leave.status in ['PENDING', 'REJECTED']:
        current_date = leave.start_date
        while current_date <= leave.end_date:
            Attendance.objects.update_or_create(
                staff=leave.staff,
                date=current_date,
                defaults={'status': 'On Leave', 'source': 'Manual'}
            )
            current_date += timedelta(days=1)
            
        leave.status = 'APPROVED'
        leave.is_approved = True
        leave.approved_by = request.user
        leave.approved_at = timezone.now()
        
        leave.rejected_by = None
        leave.rejected_at = None
        leave.rejection_reason = None
        
        leave.save()
        messages.success(request, f"{leave.staff.full_name}-এর ছুটির আবেদনটি সফলভাবে মঞ্জুর করা হয়েছে।")
        
    return redirect('hrm:leave_list')

@login_required
def leave_reject(request, id):
    leave = get_object_or_404(LeaveRequest, id=id)
    
    if leave.status == 'APPROVED' or leave.is_approved:
        current_date = leave.start_date
        while current_date <= leave.end_date:
            Attendance.objects.filter(
                staff=leave.staff, 
                date=current_date, 
                status='On Leave'
            ).delete()
            current_date += timedelta(days=1)
            
        messages.warning(request, f"{leave.staff.full_name}-এর মঞ্জুরকৃত ছুটি বাতিল করা হয়েছে।")
    else:
        messages.warning(request, "ছুটির আবেদনটি রিজেক্ট করা হয়েছে।")
    
    leave.status = 'REJECTED'
    leave.is_approved = False
    leave.rejected_by = request.user
    leave.rejected_at = timezone.now()
    
    leave.rejection_reason = request.POST.get('reason', 'অ্যাডমিন কর্তৃক বাতিলকৃত') 
    leave.save()
    
    return redirect('hrm:leave_list')

#--- Public Holiday Views ---
@login_required
def holiday_list(request):
    holidays = PublicHoliday.objects.all().order_by('-date')
    form = PublicHolidayForm()
    return render(request, 'hrm/holiday_list.html', {'holidays': holidays, 'form': form})

@login_required
def holiday_create(request):
    if request.method == 'POST':
        form = PublicHolidayForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "নতুন সরকারি ছুটি যুক্ত করা হয়েছে।")
    return redirect('hrm:holiday_list')

@login_required
def holiday_delete(request, id):
    holiday = get_object_or_404(PublicHoliday, id=id)
    holiday.delete()
    messages.error(request, "सरकारी ছুটিটি মুছে ফেলা হয়েছে।")
    return redirect('hrm:holiday_list')

@login_required
def add_department(request):
    if request.method == "POST":
        dept_id = request.POST.get('dept_id')
        name = request.POST.get('name')
        code = request.POST.get('code')
        description = request.POST.get('description')

        if dept_id:
            dept = Department.objects.get(id=dept_id)
            dept.name = name
            dept.code = code
            dept.description = description
            dept.save()
            message = "বিভাগ সফলভাবে আপডেট করা হয়েছে"
        else:
            Department.objects.create(name=name, code=code, description=description)
            message = "নতুন বিভাগ সফলভাবে যোগ করা হয়েছে"

        return JsonResponse({'status': 'success', 'message': message})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@login_required
def edit_department(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    
    if request.method == "POST":
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip().upper()
        description = request.POST.get('description', '').strip()

        if Department.objects.filter(name__iexact=name).exclude(pk=pk).exists():
            return JsonResponse({'success': False, 'error': 'এই নামের অন্য একটি বিভাগ আছে'}, status=400)
        
        if Department.objects.filter(code__iexact=code).exclude(pk=pk).exists():
            return JsonResponse({'success': False, 'error': 'এই কোডটি অন্য বিভাগে ব্যবহৃত'}, status=400)

        try:
            dept.name = name
            dept.code = code
            dept.description = description
            dept.save()
            return JsonResponse({'success': True, 'message': 'বিভাগ সফলভাবে আপডেট করা হয়েছে'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'আপডেট করতে সমস্যা হয়েছে'}, status=500)

@csrf_exempt
@login_required
def delete_department(request, pk): 
    dept = Department.objects.filter(pk=pk).first()
    if not dept:
        return JsonResponse({'success': False, 'error': 'বিভাগ পাওয়া যায়নি'}, status=404)
    
    dept.delete()
    return JsonResponse({'success': True})

@login_required
def department_list_json(request):
    departments = Department.objects.all().order_by('name')
    data = [{
        'id': d.id,
        'name': d.name,
        'code': d.code,
        'description': d.description or ''
    } for d in departments]
    return JsonResponse({'departments': data})

def manage_department_ajax(request):
    if request.method == "POST":
        dept_id = request.POST.get('dept_id')
        name = request.POST.get('name')
        
        if dept_id:
            dept = Department.objects.get(id=dept_id)
            dept.name = name
            dept.save()
        else:
            Department.objects.create(name=name)
            
        return JsonResponse({'status': 'success', 'message': 'Saved successfully'})

@login_required
def profile_view_or_edit(request, user_id):
    target_user = get_object_or_404(CustomUser, pk=user_id)
    profile, created = Profile.objects.get_or_create(user=target_user)
    form = ProfileForm(request.POST or None, request.FILES or None, instance=profile)
    departments = Department.objects.all()

    can_edit = request.user.is_superuser or request.user.id == target_user.id

    if request.method == 'POST':
        if not can_edit:
            return render(request, 'mainsystem/profile_view.html', {
                'profile': profile,
                'form': form,
                'departments': departments,
                'target_user': target_user,
                'error': "আপনার এই প্রোফাইল আপডেট করার অনুমতি নেই"
            })

        if form.is_valid():
            form.save()
            return redirect('mainsystem:profile_view', user_id=user_id)

    return render(request, 'mainsystem/profile_view.html', {
        'profile': profile,
        'form': form,
        'departments': departments,
        'target_user': target_user,
        'can_edit': can_edit
    })

@login_required
def staff_list(request):
    if request.method == "GET":
        staffs = Profile.objects.select_related('user', 'department', 'shift', 'user_type').all()
        departments = Department.objects.all().order_by('-id')
        shifts = Shift.objects.filter(is_active=True)
        user_type = UserType.objects.all()
        
        staffs = staffs.annotate(
            roll_int=Cast('designation', output_field=IntegerField())
        ).order_by('department__id', 'roll_int', 'first_name')
        
        return render(request, 'hrm/staff_list.html', {
            'staffs': staffs,
            'departments': departments,
            'shifts': shifts,
            'user_roles': user_type
        })

    if request.method == "POST":
        staff_db_id = request.POST.get('staff_db_id')
        email = request.POST.get('email', '').strip().lower() or None
        user_type_id = request.POST.get('user_type_id')
        weekly_off_vals = request.POST.getlist('weekly_off')

        try:
            with transaction.atomic():
                if staff_db_id:
                    profile = get_object_or_404(Profile, id=staff_db_id)
                    user = profile.user
                    if user and email:
                        user.email = email
                        user.save()
                else:
                    user = None
                    if email:
                        User = get_user_model()
                        user, created = User.objects.get_or_create(
                            email=email, 
                            defaults={'username': email.split('@')[0]}
                        )
                        if not created and Profile.objects.filter(user=user).exists():
                            return JsonResponse({'status': 'error', 'message': 'এই ইমেইল দিয়ে অলরেডি প্রোফাইল আছে!'})
                    
                    profile = Profile.objects.create(user=user)

                profile.first_name = request.POST.get('first_name')
                profile.last_name = request.POST.get('last_name')
                profile.father_name = request.POST.get('father_name')
                profile.mother_name = request.POST.get('mother_name')
                profile.nid_number = request.POST.get('nid_number')
                profile.staff_id = request.POST.get('staff_id')
                profile.phone_number = request.POST.get('phone_number')
                profile.designation = request.POST.get('designation')
                profile.gender = request.POST.get('gender')
                profile.present_address = request.POST.get('present_address')
                profile.permanent_address = request.POST.get('permanent_address')
                
                profile.user_type_id = user_type_id if user_type_id else None
                profile.department_id = request.POST.get('department') or None
                profile.shift_id = request.POST.get('shift') or None
                
                device_id = request.POST.get('device_user_id', '').strip()
                profile.device_user_id = device_id if device_id else None
                
                dob = request.POST.get('date_of_birth')
                profile.date_of_birth = dob if dob else None
                
                joining_date = request.POST.get('joining_date')
                profile.joining_date = joining_date if joining_date else None
                
                salary = request.POST.get('basic_salary', 0)
                profile.basic_salary = float(salary) if salary else 0

                if not weekly_off_vals or '' in weekly_off_vals:
                    profile.weekly_off.clear()
                else:
                    off_day_ids = [int(val) for val in weekly_off_vals if val.isdigit()]
                    profile.weekly_off.set(off_day_ids)

                profile.email = email

                if 'profile_image' in request.FILES:
                    profile.profile_image = request.FILES['profile_image']

                profile.is_active = request.POST.get('is_active') == 'on'
                profile.status = request.POST.get('status', 'active')
                
                profile.save()

                profile.educations.all().delete() 
                degrees = request.POST.getlist('edu_degree[]')
                institutes = request.POST.getlist('edu_institute[]')
                years = request.POST.getlist('edu_year[]')
                results = request.POST.getlist('edu_result[]')

                edu_objs = []
                for i in range(len(degrees)):
                    if degrees[i].strip():
                        edu_objs.append(Education(
                            profile=profile,
                            degree_name=degrees[i],
                            institute=institutes[i],
                            passing_year=years[i] if years[i].isdigit() else 0,
                            result=results[i]
                        ))
                Education.objects.bulk_create(edu_objs) 

                return JsonResponse({
                    'status': 'success', 
                    'message': 'সফলভাবে সংরক্ষিত হয়েছে!',
                    'redirect_url': reverse('hrm:staff_list')
                })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f"সিস্টেম এরর: {str(e)}"})

@login_required
def get_staff_data(request, id):
    try:
        p = Profile.objects.select_related('user', 'department', 'shift', 'user_type').prefetch_related('educations').get(id=id)
        
        edu_list = []
        for edu in p.educations.all():
            edu_list.append({
                'degree_name': edu.degree_name or '',
                'institute': edu.institute or '',
                'passing_year': edu.passing_year or '',
                'result': edu.result or '',
            })

        data = {
            'status': 'success',
            'db_id': p.id,
            'first_name': p.first_name or '',
            'last_name': p.last_name or '',
            'father_name': p.father_name or '',
            'mother_name': p.mother_name or '',
            'nid_number': p.nid_number or '',
            'email': p.user.email if p.user else (p.email or ''),
            'phone_number': p.phone_number or '',
            'emergency_contact': p.emergency_contact or '',
            'staff_id': p.staff_id or '',
            'designation': p.designation or '',
            'gender': p.gender or 'male',
            'blood_group': p.blood_group or '',
            'employment_type': p.employment_type or 'probation',
            'basic_salary': float(p.basic_salary) if p.basic_salary else 0,
            'device_user_id': p.device_user_id or '',
            'present_address': p.present_address or '',
            'permanent_address': p.permanent_address or '',
            'work_status': p.status or 'active',
            'weekly_off': list(p.weekly_off.values_list('id', flat=True)) if p.weekly_off.exists() else [],
            'is_active': p.is_active,
            'date_of_birth': p.date_of_birth.strftime('%Y-%m-%d') if p.date_of_birth else '',
            'joining_date': p.joining_date.strftime('%Y-%m-%d') if p.joining_date else '',
            'resignation_date': p.resignation_date.strftime('%Y-%m-%d') if p.resignation_date else '',
            'dept_id': p.department.id if p.department else '',
            'shift_id': p.shift.id if p.shift else '',
            'user_type_id': p.user_type.id if p.user_type else '', 
            'profile_image_url': p.profile_image.url if p.profile_image else None,
            'educations': edu_list, 
        }
        return JsonResponse(data)

    except Profile.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'স্টাফ প্রোফাইল খুঁজে পাওয়া যায়নি!'}, status=404)
    except Exception as e:
        print(f"Error in get_staff_data: {str(e)}")
        return JsonResponse({'status': 'error', 'message': f"সিস্টেম এরর: {str(e)}"}, status=500)

@login_required
def staff_report(request):
    staffs = Profile.objects.select_related('user', 'department', 'user_type').all()
    departments = Department.objects.all()
    user_roles = UserType.objects.all()
    
    dept_id = request.GET.get('department')
    search_query = request.GET.get('search', '').strip()
    
    if search_query:
        id_query = None
        if search_query.upper().startswith('HC-'):
            try:
                raw_id = search_query.upper().replace('HC-', '')
                id_query = int(raw_id) - 1000
            except ValueError:
                pass

        search_filter = Q(first_name__icontains=search_query) | \
                        Q(last_name__icontains=search_query) | \
                        Q(phone_number__icontains=search_query) | \
                        Q(designation__icontains=search_query) | \
                        Q(staff_id__icontains=search_query)
        
        if id_query is not None:
            search_filter |= Q(user__id=id_query)
            
        staffs = staffs.filter(search_filter)

    if dept_id:
        staffs = staffs.filter(department_id=dept_id)

    staffs = staffs.annotate(
        roll_int=Cast('designation', output_field=IntegerField())
    ).order_by('department__id', 'roll_int', 'first_name')

    context = {
        'staffs': staffs, 
        'departments': departments,
        'user_roles': user_roles,
        'selected_dept': int(dept_id) if dept_id and dept_id.isdigit() else None,
        'today': timezone.now(),
        'search_query': search_query,
    }
    return render(request, 'hrm/staff_report.html', context)

def single_id_card(request, staff_id):
    staff = get_object_or_404(Profile, staff_id=staff_id)
    return render(request, 'hrm/single_id_card.html', {'s': staff})

def staff_biodata(request, id):
    staff = get_object_or_404(Profile, id=id)
    context = {
        'staff': staff,
    }
    return render(request, 'mainsystem/biodata_template.html', context)

def generate_qr_code(request, staff_id):
    staff = get_object_or_404(Profile, id=staff_id)
    qr_data = f"Staff ID: {staff.id} | Name: {staff.first_name} {staff.last_name}" 
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=0,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return HttpResponse(buffer.getvalue(), content_type="image/png")