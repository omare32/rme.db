from django import forms

class CostDistForm(forms.Form):
    PROJECT_IDENTIFIER_CHOICES = [
        ('project_no', 'Project Number'),
        ('project_name', 'Project Name'),
    ]

    project_identifier_type = forms.ChoiceField(choices=PROJECT_IDENTIFIER_CHOICES, widget=forms.RadioSelect)
    project_identifier = forms.CharField(max_length=200)
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    show_details = forms.BooleanField(required=False, label='Show Detailed List')