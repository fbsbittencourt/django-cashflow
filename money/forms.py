from django import forms
from money import models
from money import utils
from money import settings
import datetime

YESNO = (
    ('', ''),
    ('Y', 'Yes'),
    ('N', 'No'),
)


# Inputs
class DatepickerInput(forms.widgets.DateInput):

    attrs = {'class' : 'datepicker'}

    def __init__(self):
        super(DatepickerInput,self).__init__(self.attrs)


# Forms
class EntryForm(forms.ModelForm):
    class Meta:
        exclude = ('user',)
        model = models.Entry
        widgets={
            'pay_date' : DatepickerInput(),
            'paid_date' : DatepickerInput(),
        }

class BankForm(forms.ModelForm):
    class Meta:
        exclude = ('user',)
        model = models.Bank

class AccountForm(forms.ModelForm):
    class Meta:
        exclude = ('user',)
        model = models.Account

class PersonForm(forms.ModelForm):
    class Meta:
        exclude = ('user',)
        model = models.Person

class EntryFilterForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(EntryFilterForm, self).__init__(*args, **kwargs)
        self.fields['bank'].choices = [('','')] + [(obj.id, str(obj)) for obj in models.Bank.objects.all()]
        self.fields['person'].choices = [('','')] + [(obj.id, str(obj)) for obj in models.Person.objects.all()]
        self.fields['account'].choices = [('','')] + [(obj.id, str(obj)) for obj in models.Account.objects.all()]

    period = forms.ChoiceField(choices=utils.date_shortcuts(), widget=forms.widgets.Select(attrs={'class':'span2'}))
    start_date = forms.CharField(max_length=20, widget=forms.widgets.TextInput(attrs={'class':'span2 datepicker'}))
    end_date = forms.CharField(max_length=20, widget=forms.widgets.TextInput(attrs={'class':'span2 datepicker'}))
    bank = forms.ChoiceField(widget=forms.widgets.Select(attrs={'class':'span2'}))
    person = forms.ChoiceField(widget=forms.widgets.Select(attrs={'class':'span2'}))
    account = forms.ChoiceField(widget=forms.widgets.Select(attrs={'class':'span2'}))
    doc = forms.CharField(max_length=20, widget=forms.widgets.TextInput(attrs={'class':'span2'}))
    check = forms.CharField(max_length=20, widget=forms.widgets.TextInput(attrs={'class':'span2'}))
    discharge = forms.ChoiceField(choices=YESNO, widget=forms.widgets.Select(attrs={'class':'span2'}))
