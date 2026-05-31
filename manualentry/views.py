from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from .models import Terminal, ManualEntry
from .forms import ManualEntryForm

# ==========================================
# 🎛️ HARDWARE TERMINAL WORKSPACE VIEWS
# ==========================================

class TerminalListView(ListView):
    model = Terminal
    template_name = 'manualentry/terminal_list.html'
    context_object_name = 'terminals'
    ordering = ['-id']


# (অন্যান্য কোড আগের মতোই থাকবে, শুধু টার্মিনাল ক্রিয়েট ও আপডেট ভিউ দুটি নিচে দেওয়া কোড দিয়ে রিপ্লেস করুন)

class TerminalCreateView(SuccessMessageMixin, CreateView):
    model = Terminal
    template_name = 'manualentry/terminal_form.html'  # 👈 নতুন ডেডিকেটেড টেমপ্লেট
    fields = ['code', 'value', 'description']
    success_url = reverse_lazy('manualentry:terminal_list')
    success_message = "Hardware Terminal registered into the core infrastructure with session trail."

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.created_by = self.request.user
        return super().form_valid(form)


class TerminalUpdateView(SuccessMessageMixin, UpdateView):
    model = Terminal
    template_name = 'manualentry/terminal_form.html'  # 👈 নতুন ডেডিকেটেড টেমপ্লেট
    fields = ['code', 'value', 'description']
    success_url = reverse_lazy('manualentry:terminal_list')
    success_message = "Terminal system configurations updated with audit log track."

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.updated_by = self.request.user
        return super().form_valid(form)


class TerminalDeleteView(DeleteView):
    model = Terminal
    template_name = 'manualentry/confirm_delete.html'
    success_url = reverse_lazy('manualentry:terminal_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Terminal hardware repository purged from master registry.")
        return super().delete(request, *args, **kwargs)


# ==========================================
# 📊 MANUAL LOG DATA SYNC WORKSPACE VIEWS
# ==========================================
from django.views.generic import ListView
from django.contrib.auth import get_user_model
from django.utils.dateparse import parse_date
from datetime import datetime, time
from .models import ManualEntry, Terminal
from django.views.generic import TemplateView
from django.utils import timezone
from manualentry.models import ManualEntry, Terminal

class DashboardView(TemplateView):
    template_name = 'mainsystem/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()

        # 📊 ১. কোয়ান্টিটেটিভ মেট্রিক্স ক্যালকুলেশন
        total_entries = ManualEntry.objects.count()
        total_terminals = Terminal.objects.count()
        
        # 📅 ২. আজকের লাইভ এন্ট্রি কাউন্ট
        today_entries = ManualEntry.objects.filter(created_at__date=today).count()

        # ⚙️ ৩. সিস্টেম হেলথ সিঙ্ক রেশিও (ধরি, টোটাল এন্ট্রির মধ্যে টার্মিনাল বাউন্ড কত পার্সেন্ট)
        bound_entries = ManualEntry.objects.filter(total_terminal__isnull=False).count()
        sync_ratio = round((bound_entries / total_entries * 100), 1) if total_entries > 0 else 100.0

        # 📑 ৪. রিসেন্ট ডেটা স্ট্রিম (সর্বশেষ ৫টি এন্ট্রি এবং ৫টি টার্মিনাল)
        context['recent_entries'] = ManualEntry.objects.select_related('total_terminal', 'created_by').order_by('-id')[:5]
        context['recent_terminals'] = Terminal.objects.select_related('created_by').order_by('-id')[:5]

        # কনটেক্সট পুশ
        context['stat_total_entries'] = total_entries
        context['stat_total_terminals'] = total_terminals
        context['stat_today_entries'] = today_entries
        context['stat_sync_ratio'] = sync_ratio

        return context
    
User = get_user_model()

class EntryListView(ListView):
    model = ManualEntry
    template_name = 'manualentry/entry_list.html'
    context_object_name = 'entries'

    def get_queryset(self):
        queryset = ManualEntry.objects.select_related('total_terminal', 'created_by').order_by('-id')

        # 📥 ফিল্টার প্যারামিটার রিসিভ করা হচ্ছে
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')
        user_id = self.request.GET.get('user')
        terminal_id = self.request.GET.get('terminal')

        # ১. 📅 ডেট-টু-ডেট ফিল্টারিং লজিক (DateTime-এর কারণে সময় বাউন্ড করে দেওয়া হয়েছে)
        if start_date_str:
            start_date = parse_date(start_date_str)
            if start_date:
                queryset = queryset.filter(created_at__gte=datetime.combine(start_date, time.min))
        
        if end_date_str:
            end_date = parse_date(end_date_str)
            if end_date:
                queryset = queryset.filter(created_at__lte=datetime.combine(end_date, time.max))

        # ২. 👤 ইউজার (Created By) ফিল্টারিং
        if user_id and user_id.isdigit():
            queryset = queryset.filter(created_by_id=int(user_id))

        # ৩. 🎛️ টার্মিনাল ফিল্টারিং
        if terminal_id and terminal_id.isdigit():
            queryset = queryset.filter(total_terminal_id=int(terminal_id))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # ফিল্টার ড্রপডাউনগুলো ডাইনামিকালি লোড করার জন্য ডেটা পাঠানো হলো
        context['all_users'] = User.objects.filter(is_active=True).order_by('username')
        context['all_terminals'] = Terminal.objects.all().order_by('code')
        
        # ইউজার ফিল্টার করার পর যাতে ইনপুট বক্সে মানগুলো থেকে যায় (Retain State)
        context['selected_start_date'] = self.request.GET.get('start_date', '')
        context['selected_end_date'] = self.request.GET.get('end_date', '')
        context['selected_user'] = self.request.GET.get('user', '')
        context['selected_terminal'] = self.request.GET.get('terminal', '')
        return context


class EntryCreateView(SuccessMessageMixin, CreateView):
    model = ManualEntry
    form_class = ManualEntryForm
    template_name = 'manualentry/form.html'
    success_url = reverse_lazy('manualentry:entry_list')
    success_message = "Data log model verified, calculated, and securely deployed."

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.created_by = self.request.user
        return super().form_valid(form)


class EntryUpdateView(SuccessMessageMixin, UpdateView):
    model = ManualEntry
    form_class = ManualEntryForm
    template_name = 'manualentry/form.html'
    success_url = reverse_lazy('manualentry:entry_list')
    success_message = "Arithmetic dataset logs rewritten with updated audit context."

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.updated_by = self.request.user
        return super().form_valid(form)


class EntryDeleteView(DeleteView):
    model = ManualEntry
    template_name = 'manualentry/confirm_delete.html'
    success_url = reverse_lazy('manualentry:entry_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Biometric data log node permanently dropped.")
        return super().delete(request, *args, **kwargs)