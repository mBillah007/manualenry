from mainsystem.models import ModuleGroup, Permission

def sidebar_menu(request):
    if not request.user.is_authenticated or not request.user.role:
        return {}

    # ইউজারের রোলের জন্য অনুমোদিত মডিউল আইডিগুলো বের করা
    allowed_module_ids = Permission.objects.filter(
        role=request.user.role, 
        is_allowed=True
    ).values_list('module_id', flat=True).distinct()

    # গ্রুপ অনুযায়ী মডিউলগুলো সাজানো
    groups = ModuleGroup.objects.prefetch_related('modules').order_by('order')
    
    sidebar = []
    for group in groups:
        modules = group.modules.filter(
            id__in=allowed_module_ids, 
            is_visible=True, 
            parent__isnull=True
        ).order_by('order')
        
        if modules.exists():
            sidebar.append({
                'group': group,
                'modules': modules
            })

    return {'sidebar_menu': sidebar}