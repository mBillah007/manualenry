# mainsystem/templatetags/custom_tags.py

from django import template
from mainsystem.models import Module, Permission, ActionType
import calendar

register = template.Library()

# --- ১. বেসিক ডিকশনারি ফিল্টার (এটেনডেন্স লিস্টের জন্য) ---
@register.filter
def get_item(dictionary, key):
    if not dictionary:
        return None
    return dictionary.get(str(key)) or dictionary.get(key)

@register.filter
def dict_get(d, key):
    return d.get(key, False)

@register.filter 
def dict_gets(d, key): 
    return d.get(key, "—")
@register.filter
def get_day_data(dictionary, key):
    return dictionary.get(key)
@register.simple_tag
def set_var(val):
    return val
# --- ২. সিডিউল ও মানথলি রোস্টার ফিল্টার ---
@register.filter
def get_item_by_keys(dictionary, staff_id):
    """মানথলি রোস্টার ডিকশনারি থেকে নির্দিষ্ট স্টাফের সব ডেট-শিফট রিটার্ন করে"""
    if not dictionary: return {}
    return {k[1]: v for k, v in dictionary.items() if k[0] == staff_id}
@register.filter
def month_name(month_number):
    """মাস নম্বর (1-12) থেকে মাসের নাম পাওয়ার জন্য"""
    try:
        return calendar.month_name[int(month_number)]
    except (ValueError, IndexError):
        return month_number
@register.filter
def get_item_by_day(staff_dict, day):
    """নির্দিষ্ট দিনের শিফট অবজেক্ট রিটার্ন করে"""
    if not staff_dict: return None
    return staff_dict.get(day)
@register.filter
def get_att_status(dictionary, staff_id):
    return dictionary.get(staff_id, {})

@register.filter
def get_att_count(dictionary, staff_id):
    staff_data = dictionary.get(staff_id, {})
    # শুধুমাত্র 'Present' স্ট্যাটাস গুনে বের করা
    return sum(1 for status in staff_data.values() if status == 'Present')
# --- ৩. পারমিশন ও এক্সেস কন্ট্রোল ট্যাগস ---
@register.simple_tag(takes_context=True)
def can_access(context, module_url_name):
    return _check_permission(context, module_url_name, 'access')

@register.simple_tag(takes_context=True)
def can_create(context, module_url_name):
    return _check_permission(context, module_url_name, 'create')

@register.simple_tag(takes_context=True)
def can_edit(context, module_url_name):
    return _check_permission(context, module_url_name, 'edit')

@register.simple_tag(takes_context=True)
def can_delete(context, module_url_name):
    return _check_permission(context, module_url_name, 'delete')

def _check_permission(context, module_url_name, action_key):
    request = context.get('request')
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated: return False
    
    role = getattr(user, 'role', None)
    if not role: return False

    try:
        module = Module.objects.get(url_name=module_url_name)
        action = ActionType.objects.get(key=action_key)
        perm = Permission.objects.get(role=role, module=module, action=action)
        return perm.is_allowed
    except (Module.DoesNotExist, ActionType.DoesNotExist, Permission.DoesNotExist):
        return False

# --- ৪. অন্যান্য হেল্পার ফিল্টার ---
@register.filter
def get_matrix_value(matrix, args):
    try:
        role_id, module_id, action_key = args.split(',')
        return matrix.get(int(role_id), {}).get(int(module_id), {}).get(action_key, False)
    except:
        return False

@register.filter
def json_safe(value):
    import json
    from django.utils.safestring import mark_safe
    return mark_safe(json.dumps(value))