from django.db.models import Sum
from money.models import Balance, Entry
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
