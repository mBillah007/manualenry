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
from django.db.models import Count, F, FloatField, Q, Sum
from django.db.models.functions import Cast
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import get_resolver
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_POST

# --- প্রজেক্ট অ্যাপস ও কাস্টম মডিউলস ইမপোর্ট ---
from mainsystem.context_processors import has_permission
from mainsystem.models import ActionType, Module, ModuleGroup  # নির্দিষ্ট মডেল ইমপোর্ট করা হলো

# নোট: লোকাল অ্যাপের ওয়াইল্ডকার্ড (*) ইমপোর্টগুলো সবার নিচে রাখা হয়েছে নেমস্পেস ক্ল্যাশ এড়াতে
from mainsystem.forms import *
from mainsystem.models import *
from .models import *


# =========================================================================
#                             VIEWS LOGIC START
# =========================================================================

@login_required
def role_list(request):
    # নেমস্পেস অনুযায়ী পারমিশন চেক
    if not has_permission(request, 'mainsystem:role_list', 'access'):
        return render(request, 'mainsystem/403.html', {
            'reason': "❌ আপনি Role Management পৃষ্ঠায় প্রবেশের অনুমতি রাখেন না"
        })

    roles = Role.objects.all()
    for role in roles:
        role.is_protected = bool(role.is_protected)

    modules = Module.objects.filter(is_visible=True, parent=None).order_by('order')
    actions = ActionType.objects.all()

    return render(request, 'mainsystem/role_list.html', {
        'page_title': 'Role Management',
        'roles': roles,
        'modules': modules,
        'actions': actions
    })


@require_POST
@login_required
def role_form(request, role_id=None):
    """রোল ক্রিয়েট ও এডিটের প্রধান ভিউ (সিকিউরিটি সহ)"""
    name = request.POST.get('name', '').strip()
    is_protected = request.POST.get('is_protected') == 'on'

    if not name:
        return JsonResponse({'success': False, 'error': {'name': ['রোলের নাম আবশ্যক']}})

    if role_id:
        if not has_permission(request, 'mainsystem:role_edit', 'edit'):
            return JsonResponse({'success': False, 'error': {'permission': ['আপনার সম্পাদনার অনুমতি নেই']}}, status=403)
        role = get_object_or_404(Role, id=role_id)
        role.name = name
        role.is_protected = is_protected
        role.save()
    else:
        if not has_permission(request, 'mainsystem:role_create', 'create'):
            return JsonResponse({'success': False, 'error': {'permission': ['আপনার নতুন রোল যোগ করার অনুমতি নেই']}}, status=403)
        
        try:
            role = Role.objects.create(name=name, is_protected=is_protected)
        except IntegrityError:
            return JsonResponse({'success': False, 'error': {'name': ['এই নামের রোল ইতিমধ্যে বিদ্যমান আছে']}}, status=400)

    return JsonResponse({'success': True, 'role_id': role.id})


@require_POST
@login_required
def role_delete(request, role_id):
    # ডিলিট পারমিশন চেক
    if not has_permission(request, 'mainsystem:role_delete', 'delete'):
        return render(request, 'mainsystem/403.html', {'reason': '❌ আপনার রোল মুছে ফেলার অনুমতি নেই'})

    role = get_object_or_404(Role, id=role_id)
    if role.is_protected:
        return render(request, 'mainsystem/403.html', {'reason': '🔒 সুরক্ষিত রোল মুছে ফেলা যাবে না'})
    
    role.delete()
    messages.success(request, 'রোলটি সফলভাবে মুছে ফেলা হয়েছে।')
    return redirect('mainsystem:role_list')


@login_required
def role_clone_view(request, source_role_id):
    # ক্লোন করার পারমিশন চেক
    if not has_permission(request, 'mainsystem:role_create', 'create'):
        return render(request, 'mainsystem/403.html', {'reason': '❌ আপনার রোল ক্লোন করার অনুমতি নেই'})

    source = get_object_or_404(Role, id=source_role_id)
    clone = Role.objects.create(
        name=f"{source.name} (Clone) - {timezone.now().strftime('%H%M%S')}",
        is_protected=False
    )
    
    # বাল্ক ক্রিয়েট অডিট ট্রেইল বা পারমিশন লগের জন্য তৈরি করা
    old_perms = Permission.objects.filter(role=source)
    new_perms = [
        Permission(
            role=clone, 
            module=p.module, 
            action=p.action, 
            is_allowed=p.is_allowed,
            created_by=request.user
        ) for p in old_perms
    ]
    Permission.objects.bulk_create(new_perms)
    
    messages.success(request, f"'{source.name}' সফলভাবে ক্লোন করা হয়েছে।")
    return redirect('mainsystem:role_list')


@login_required
def permission_matrix_view(request):
    if not has_permission(request, 'mainsystem:permission_matrix', 'access'):
        return render(request, 'mainsystem/403.html', {'reason': '❌ পারমিশন ম্যাট্রিক্স দেখার অনুমতি আপনার নেই'})

    roles = Role.objects.all()
    role_id = request.GET.get('role_id')
    selected_role = get_object_or_404(Role, id=role_id) if role_id else roles.first()

    modules = Module.objects.select_related('group').all()
    actions = ActionType.objects.all()

    grouped_modules = {}
    for module in modules:
        group_name = module.group.name if module.group else 'Other'
        grouped_modules.setdefault(group_name, []).append(module)

        module.permission_map = {}
        module.allowed_count = 0
        module.denied_count = 0

        for action in actions:
            perm = Permission.objects.filter(role=selected_role, module=module, action=action).first()
            is_allowed = perm.is_allowed if perm else False
            module.permission_map[action.id] = is_allowed

            if is_allowed:
                module.allowed_count += 1
            else:
                module.denied_count += 1

    return render(request, 'mainsystem/permission_matrix.html', {
        'roles': roles,
        'selected_role': selected_role,
        'grouped_modules': grouped_modules,
        'actions': actions,
    })


@require_POST
@login_required
def update_permission(request):
    """সিঙ্গেল চেকবক্স টগল আপডেট (Audit Trail সহ)"""
    if not has_permission(request, 'mainsystem:permission_matrix', 'edit'):
        return JsonResponse({'success': False, 'error': '🚫 আপনার পারমিশন পরিবর্তনের অনুমতি নেই'}, status=403)

    data = json.loads(request.body)
    role = get_object_or_404(Role, id=data['role_id'])
    module = get_object_or_404(Module, id=data['module_id'])
    action = get_object_or_404(ActionType, id=data['action_id'])

    if role.is_protected:
        return JsonResponse({'success': False, 'error': '🚫 এই রোলটি সুরক্ষিত, পরিবর্তনযোগ্য নয়'})

    perm, created = Permission.objects.get_or_create(
        role=role,
        module=module,
        action=action,
        defaults={'is_allowed': data['is_allowed'], 'created_by': request.user}
    )
    if not created:
        perm.is_allowed = data['is_allowed']
        perm.updated_by = request.user  # কে মডিফাই করল তার ট্র্যাকিং
        perm.save()

    return JsonResponse({'success': True})


@require_POST
@login_required
def grant_all_permissions_view(request):
    if not has_permission(request, 'mainsystem:permission_matrix', 'edit'):
        return JsonResponse({'success': False, 'error': '🚫 পারমিশন পরিবর্তনের অনুমতি নেই'}, status=403)

    data = json.loads(request.body)
    role = get_object_or_404(Role, id=data['role_id'])

    if role.is_protected:
        return JsonResponse({'success': False, 'error': '🚫 এই রোল পরিবর্তনযোগ্য নয়'})

    for module in Module.objects.all():
        for action in ActionType.objects.all():
            perm, created = Permission.objects.get_or_create(
                role=role, module=module, action=action,
                defaults={'is_allowed': True, 'created_by': request.user}
            )
            if not created:
                perm.is_allowed = True
                perm.updated_by = request.user
                perm.save()

    return JsonResponse({'success': True})


@require_POST
@login_required
def revoke_all_permissions_view(request):
    if not has_permission(request, 'mainsystem:permission_matrix', 'edit'):
        return JsonResponse({'success': False, 'error': '🚫 পারমিশন পরিবর্তনের অনুমতি নেই'}, status=403)

    data = json.loads(request.body)
    role = get_object_or_404(Role, id=data['role_id'])

    if role.is_protected:
        return JsonResponse({'success': False, 'error': '🚫 এই রোল পরিবর্তনযোগ্য নয়'})

    Permission.objects.filter(role=role).update(is_allowed=False, updated_by=request.user)
    return JsonResponse({'success': True})


# 🔍 ইউজার তালিকা
@login_required
def user_list(request):
    current_url = request.resolver_match.view_name if request.resolver_match else None
    access_action = ActionType.objects.filter(key='access').first()

    # ✅ Permission check with graceful fallback
    if not access_action or not current_url or not has_permission(request, current_url, 'access'):
        return render(request, 'mainsystem/403.html', {
            'reason': f"❌ আপনি '{current_url}' পৃষ্ঠায় প্রবেশের অনুমতি রাখেন না"
        })

    current_user = request.user
    role = current_user.role

    # ✅ Role filtering logic
    if role.name == 'SystemAdmin':
        roles = Role.objects.all()
    else:
        roles = Role.objects.exclude(name__in=['SystemAdmin', 'SuperAdmin'])

    users = CustomUser.objects.all()

    return render(request, 'mainsystem/user_list.html', {
        'page_title': 'User Management',
        'welcome_text': f"স্বাগতম, {current_user.get_full_name()}!",
        'user': current_user,
        'role': role,
        'users': users,
        'roles': roles
    })


@login_required
def user_form_handler(request, user_id=None):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid Method'}, status=405)

    data = request.POST
    user = get_object_or_404(CustomUser, id=user_id) if user_id else CustomUser()

    try:
        user.username = data.get('username', '').strip()
        user.email = data.get('email', '').strip()
        user.department = data.get('department', '').strip() 
        
        role_id = data.get('role')
        if role_id:
            user.role_id = role_id

        user.is_active = 'is_active' in data
        user.is_staff = 'is_staff' in data
        user.is_superuser = 'is_superuser' in data
        user.is_protected = 'is_protected' in data

        if not user_id:
            password = data.get('password')
            confirm_password = data.get('confirm_password')
            if password and password == confirm_password:
                user.set_password(password)
            else:
                return JsonResponse({'success': False, 'error': 'Passwords do not match or are empty'}, status=400)
            user.date_joined = timezone.now()

        user.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def user_delete(request, user_id):
    if request.method == 'POST':
        if not has_permission(request, 'mainsystem:user_list', 'delete'):
            return redirect('no_permission')

        user = get_object_or_404(CustomUser, id=user_id)
        if user.is_protected:
            messages.error(request, "❌ এই ইউজার সুরক্ষিত, ডিলেট করা যাবে না")
        else:
            user.delete()
            messages.success(request, "✅ ইউজার সফলভাবে মুছে ফেলা হয়েছে")
        return redirect('mainsystem:user_list')
    return redirect('mainsystem:user_list')


@require_POST
@login_required
def user_password_update(request, user_id):
    if not has_permission(request, 'user_list', 'edit'):
        return JsonResponse({'success': False, 'error': {'permission': ['পাসওয়ার্ড পরিবর্তনের অনুমতি নেই']}}, status=403)

    new_password = request.POST.get('new_password', '').strip()
    confirm = request.POST.get('confirm_password', '').strip()

    if not new_password:
        return JsonResponse({'success': False, 'error': {'new_password': ['পাসওয়ার্ড আবশ্যক']}}, status=400)
    if new_password != confirm:
        return JsonResponse({'success': False, 'error': {'new_password': ['পাসওয়ার্ড মিলছে না']}}, status=400)

    user = get_object_or_404(CustomUser, id=user_id)

    try:
        validate_password(new_password, user=user)
    except ValidationError as e:
        return JsonResponse({'success': False, 'error': {'new_password': list(e.messages)}}, status=400)

    user.set_password(new_password)
    user.save()

    AuditLog.objects.create(
        user=request.user,
        action='password_change',
        target_user=user,
        message=f"{request.user.username} changed password for {user.username}"
    )

    if request.headers.get('x-requested-with') != 'XMLHttpRequest':
        messages.success(request, "পাসওয়ার্ড সফলভাবে পরিবর্তন হয়েছে")
        return redirect('mainsystem:profile_view', user_id=user.id)

    return JsonResponse({'success': True})


@login_required
def password_modal_view(request):
    return render(request, 'mainsystem/modals/password_update.html')


@csrf_exempt
@login_required
def sync_modules_ajax(request):
    if request.method == 'POST' and request.user.is_authenticated:
        resolver = get_resolver()
        url_names = [name for name in resolver.reverse_dict.keys() if isinstance(name, str)]
        added = 0

        for url_name in url_names:
            if not Module.objects.filter(url_name=url_name).exists():
                Module.objects.create(
                    name=url_name.replace('_', ' ').title(),
                    url_name=url_name,
                    icon='bi-circle'
                )
                added += 1

        return JsonResponse({'success': True, 'added': added})
    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def module_list(request):
    q = request.GET.get('q', '').strip()
    group_id = request.GET.get('group', '')
    visible = request.GET.get('visible', '')
    sort_field = request.GET.get('sort', 'order')
    direction = request.GET.get('dir', 'asc')
    page_number = request.GET.get('page', 1)

    modules = Module.objects.select_related('group', 'parent')

    if q:
        modules = modules.filter(
            Q(name__icontains=q) |
            Q(label__icontains=q) |
            Q(url_name__icontains=q) |
            Q(group__name__icontains=q)
        )

    if group_id:
        modules = modules.filter(group_id=group_id)

    if visible == '1':
        modules = modules.filter(is_visible=True)
    elif visible == '0':
        modules = modules.filter(is_visible=False)

    total_count = modules.count()

    actual_sort = f"-{sort_field}" if direction == 'desc' else sort_field
    modules = modules.order_by(actual_sort)

    paginator = Paginator(modules, 20)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': q,
        'group_id': group_id,
        'visible': visible,
        'sort': sort_field,
        'dir': direction,
        'total': total_count,
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'mainsystem/partials/module_table.html', context)

    groups = ModuleGroup.objects.all()
    actions = ActionType.objects.all()
    
    try:
        with open(settings.BASE_DIR / 'static/icons.json', 'r', encoding='utf-8') as f:
            icon_list = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        icon_list = []

    context.update({
        'module_groups': groups,
        'icon_list': icon_list,
        'actions': actions
    })

    return render(request, 'mainsystem/module_list.html', context)


@login_required
def module_form_handler(request, module_id=None):
    instance = get_object_or_404(Module, pk=module_id) if module_id else None

    if request.method == 'POST':
        form = ModuleForm(request.POST, instance=instance)
        if form.is_valid():
            module = form.save()
            return JsonResponse({'success': True})
        else:
            errors = {field: [str(e) for e in errs] for field, errs in form.errors.items()}
            return JsonResponse({'success': False, 'errors': errors}, status=400)

    form = ModuleForm(instance=instance)
    return render(request, 'mainsystem/modals/add_module.html', {
        'form': form,
        'modules': Module.objects.all(),
        'module_groups': ModuleGroup.objects.all()
    })


@login_required
def module_delete(request, module_id):
    if request.method == 'POST':
        module = get_object_or_404(Module, id=module_id)
        module.delete()

        modules = Module.objects.select_related('group', 'parent').order_by('order')
        paginator = Paginator(modules, 10)
        page_obj = paginator.get_page(1)

        table_html = render(request, 'mainsystem/partials/module_table.html', {
            'page_obj': page_obj,
        }).content.decode('utf-8')

        return JsonResponse({'success': True, 'message': f"Module '{module.name}' deleted successfully", 'table_html': table_html})

    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


@login_required
def module_group_list_view(request):
    groups = ModuleGroup.objects.all().order_by('order')

    context = {
        'module_groups': groups,
        'can_edit': has_permission(request, 'mainsystem:module_group_list', 'edit'),
        'can_delete': has_permission(request, 'mainsystem:module_group_delete', 'delete'),
    }
    return render(request, 'mainsystem/modals/module_group.html', context)   


@csrf_exempt
@login_required
def module_group_save_ajax(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)

    group_id = request.POST.get("id")
    name = request.POST.get("name", "").strip()
    icon = request.POST.get("icon", "").strip()
    order = request.POST.get("order", "0")

    if not name:
        return JsonResponse({"success": False, "error": "Group name is required"}, status=400)

    try:
        order = int(order)
    except ValueError:
        return JsonResponse({"success": False, "error": "Order must be a number"}, status=400)

    if group_id:
        group = ModuleGroup.objects.filter(id=group_id).first()
        if not group:
            return JsonResponse({"success": False, "error": "Group not found"}, status=404)
        group.name = name
        group.icon = icon
        group.order = order
        group.updated_by = request.user
        group.save()
        return JsonResponse({"success": True, "created": False, "group": {
            "id": group.id, "name": group.name, "icon": group.icon, "order": group.order
        }})
    else:
        group = ModuleGroup.objects.create(
            name=name,
            icon=icon,
            order=order,
            created_by=request.user
        )
        return JsonResponse({"success": True, "created": True, "group": {
            "id": group.id, "name": group.name, "icon": group.icon, "order": group.order
        }})


@csrf_exempt
@login_required
def module_group_delete_ajax(request, id):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)

    group = get_object_or_404(ModuleGroup, pk=id)
    group.delete()
    return JsonResponse({"success": True, "message": f"Group '{group.name}' deleted successfully"})