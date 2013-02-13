from django.db.models import Sum, Max, Min
from money.models import Balance, Entry, Bank
class BalanceManager(object):

    def get_or_create_balance(self, date, bank):
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

    def get_summary(self, queryset, compress=False):
        period = queryset.exclude(paid_date__isnull=True).aggregate(latest_date=Max('paid_date'), first_date=Min('paid_date'))
        bank_list = [Bank.objects.get(pk=data.get('bank')) for data in queryset.values('bank').annotate()]

        summary = []
        for bank in bank_list:

            balance = self.get_or_create_balance(date=period.get('first_date'), bank=bank)

            credit = queryset.filter(account__type='C', bank=bank, status=True).aggregate(value=Sum('amount')).get('value') or 0
            debit = queryset.filter(account__type='D', bank=bank, status=True).aggregate(value=Sum('amount')).get('value') or 0

            new_balance = balance.amount + credit - debit

            summary.append({
                'bank':bank,
                'last_balance' : balance.amount,
                'credit' : credit,
                'debit' : debit,
                'balance' : new_balance
            })

        if compress is True:
            summary = {
                'credit' : sum([balance.get('credit') for balance in summary]),
                'debit' : sum([balance.get('debit') for balance in summary]),
                'balance' : sum([balance.get('balance') for balance in summary]),
                'last_balance' : sum([balance.get('last_balance') for balance in summary]),
            }
        return summary

    def set_initial_balance(self, bank, value=0):
        date = datetime.today().date().replace(day=1)
        Balance(
            bank=bank,
            amount=value,
            date=date
        ).save()
