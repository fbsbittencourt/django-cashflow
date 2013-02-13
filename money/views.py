from django.db.models import Sum
from django.views.generic import TemplateView
from django.views.generic.edit import FormMixin
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect, HttpResponseNotFound, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from money import generic
from money import settings
from money.models import Entry, Bank, Account, Person, Balance
from money import forms
from money.utils import last_day_of_this_month
from datetime import datetime

class DashBoard(generic.LoginRequired, TemplateView):
    template_name='money/dashboard.html'

    def get_graph_data(self):
        output = []
        output.append(['01/01',1000, 1100])
        output.append(['02/01',2500, 2000])
        output.append(['03/01',3000, 3500])
        output.append(['04/01',1500, 1500])
        output.append(['05/01',1700, 2000])
        output.append(['06/01',5800, 6000])
        output.append(['07/01',3400, 3500])
        output.append(['08/01',4000, 2000])
        output.append(['09/01',1500, 2000])
        return output

    def get_context_data(self, **kwargs):
        context = super(DashBoard, self).get_context_data(**kwargs)
        context['graph_01'] = self.get_graph_data()
        return context

class EntryList(generic.RestrictedListView, FormMixin):
    model=Entry
    form_class=forms.EntryFilterForm

    def get(self, request, *args, **kwargs):
        self.today = datetime.today().date()
        if request.GET.get('start_date') and request.GET.get('end_date'):
            self.start_date = datetime.strptime(request.GET.get('start_date'), settings.DATE_FORMAT)
            self.end_date = datetime.strptime(request.GET.get('end_date'), settings.DATE_FORMAT)
        else:
            self.start_date = self.today.replace(day=1)
            self.end_date = last_day_of_this_month(self.today)

        return super(EntryList, self).get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Entry.objects.filter(pay_date__range=(self.start_date, self.end_date))

        if self.request.GET.get('bank', None):
            queryset = queryset.filter(bank=self.request.GET.get('bank'))

        if self.request.GET.get('person', None):
            queryset = queryset.filter(person=self.request.GET.get('person'))

        if self.request.GET.get('account', None):
            queryset = queryset.filter(account=self.request.GET.get('account'))

        if self.request.GET.get('doc', None):
            queryset = queryset.filter(doc=self.request.GET.get('doc'))

        if self.request.GET.get('check', None):
            queryset = queryset.filter(check=self.request.GET.get('check'))

        if self.request.GET.get('discharge', None):
            if self.request.GET.get('discharge') == 'Y':
                queryset = queryset.filter(pay_date__lt=self.today, status=0)
            elif self.request.GET.get('discharge') == 'N':
                queryset = queryset.filter(pay_date__gte=self.today, status=0)

        return queryset

    def get_initial(self):
        initial = super(EntryList, self).get_initial()
        initial['start_date'] = datetime.strftime(self.start_date, settings.DATE_FORMAT)
        initial['end_date'] = datetime.strftime(self.end_date, settings.DATE_FORMAT)
        initial['bank'] = self.request.GET.get('bank', None)
        initial['person'] = self.request.GET.get('person', None)
        initial['account'] = self.request.GET.get('account', None)
        initial['doc'] = self.request.GET.get('doc', None)
        initial['check'] = self.request.GET.get('check', None)
        initial['discharge'] = self.request.GET.get('discharge', None)
        return initial

    def get_context_data(self, **kwargs):
        context = super(EntryList, self).get_context_data(**kwargs)
        context['form'] = self.get_form(self.get_form_class())
        context['entry_discharge_form'] = forms.EntryDischargeForm()
        return context

class BalanceManager(object):

    def get_latest_balance(self, date, bank):
        balance_date = date.replace(day=1)
        try:
            balance = Balance.objects.get(date=balance_date, bank=bank)
        except Balance.DoesNotExist:

            #get latest balance
            latest_balance = Balance.objects.filter(bank=bank).latest('date')

            #get paid entries in period
            queryset = Entry.objects.filter(
                bank=bank,
                status=True,
                paid_date__range=(latest_balance.date, balance_date)
            )

            credit = queryset.filter(account__type='C').aggregate(value=Sum('amount')).get('value') or 0
            debit = queryset.filter(account__type='D').aggregate(value=Sum('amount')).get('value') or 0

            new_amount = latest_balance.amount + credit - debit

            new_balance = Balance(date=balance_date, bank=bank, amount=new_amount).save()
            return new_balance
        else:
            return balance

    def set_initial_balance(self, bank, value=0):
        date = datetime.today().date().replace(day=1)
        Balance(
            bank=bank,
            amount=value,
            date=date
        ).save()

class EntryCreate(generic.RestrictedCreateView, BalanceManager):
    model=Entry
    form_class=forms.EntryForm
    success_url = reverse_lazy('entry_list')

class EntryDischargeReverse(generic.RestrictedUpdateView, BalanceManager):
    model=Entry
    success_url= reverse_lazy('entry_list')

    def post(self, request, *args, **kwargs):

        self.object = self.get_object()

        if request.POST.get('action', False) == 'reverse':
            self.object.status = False
            self.object.paid_date = None
            self.object.check = None
            self.object.doc = None
            self.object.save()


        return HttpResponse([], content_type='application/json')

    def get_object(self):
        return get_object_or_404(Entry, pk=self.request.POST.get('entry', None))

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(EntryDischargeReverse, self).dispatch(*args, **kwargs)


class EntryDischarge(generic.RestrictedUpdateView, BalanceManager):
    model=Entry
    form_class=forms.EntryDischargeForm
    success_url= reverse_lazy('entry_list')

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.status = True
        self.object.save()

        return HttpResponseRedirect(self.get_success_url())

class BankList(generic.ModelFormWithListView, BalanceManager):
    model=Bank
    form_class=forms.BankForm
    success_url = reverse_lazy('bank_list')

    def form_valid(self, form):

        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()

        self.set_initial_balance(self.object, self.request.POST.get('initial_balance',0))

        return HttpResponseRedirect(self.get_success_url())


class BankDelete(generic.RestrictedDeleteView):
    model=Bank
    success_url = reverse_lazy('bank_list')

class AccountList(generic.ModelFormWithListView):
    model=Account
    form_class=forms.AccountForm
    success_url = reverse_lazy('account_list')

class PersonList(generic.ModelFormWithListView):
    model=Person
    form_class=forms.PersonForm
    success_url = reverse_lazy('person_list')
