from django import forms
from .models import ManualEntry

class ManualEntryForm(forms.ModelForm):
    class Meta:
        model = ManualEntry
        fields = ['first_entry', 'second_entry', 'default_entry', 'total_terminal']
        widgets = {
            'first_entry': forms.NumberInput(attrs={'class': 'form-control calc-trigger', 'id': 'id_first_entry'}),
            'second_entry': forms.NumberInput(attrs={'class': 'form-control calc-trigger', 'id': 'id_second_entry'}),
            'default_entry': forms.NumberInput(attrs={'class': 'form-control bg-light calc-trigger', 'id': 'id_default_entry', 'readonly': 'readonly'}),
            'total_terminal': forms.Select(attrs={'class': 'form-select border shadow-none calc-trigger', 'id': 'id_total_terminal'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['total_terminal'].empty_label = "--- Select Target Terminal ---"
        # ড্রপডাউনে দেখাবে: "কোড - ভ্যালু"
        self.fields['total_terminal'].label_from_instance = lambda obj: f"{obj.code} - {obj.value}"

    def clean(self):
        cleaned_data = super().clean()
        first = cleaned_data.get('first_entry', 0)
        second = cleaned_data.get('second_entry', 0)
        default = cleaned_data.get('default_entry', 1)
        terminal = cleaned_data.get('total_terminal')

        # ১. নেট আউটপুট ক্যালকুলেশন
        if second > first:
            calculated_net = second - first - default
        else:
            calculated_net = first - second - default

        # ২. 🔒 ব্যাকএন্ড ভ্যালিডেশন: ক্যালকুলেটেড নেট টোটালের সাথে টার্মিনাল কোড মিলছে কি না
        if terminal:
            # ⚡ এখানে মেথডটি ফিক্স করা হয়েছে (permanent_string বাদ দিয়ে শুধু strip() রাখা হয়েছে)
            terminal_code_str = str(terminal.code).strip()
            calculated_net_str = str(calculated_net).strip()
            
            if calculated_net_str != terminal_code_str:
                raise forms.ValidationError(
                    f"Data Mismatch! The calculated net total is '{calculated_net}', "
                    f"but the selected Terminal code is '{terminal.code}'. "
                    f"The calculation must match the Terminal Code to save."
                )

        return cleaned_data