# Generated by Django 3.2.9 on 2021-12-16 01:15

from django.db import migrations


def set_chain_on_udc_orders(apps, schema_editor):
    DepositOrder = apps.get_model("raiden", "UserDepositContractOrder")
    Chain = apps.get_model("blockchain", "Chain")

    for order in DepositOrder.objects.filter(chain=None):
        order.chain = (
            Chain.objects.filter(tokens__tokennetwork__channel__raiden=order.raiden)
            .distinct()
            .first()
        )
        order.save()


class Migration(migrations.Migration):

    dependencies = [
        ("raiden", "0005_userdepositcontractorder_chain"),
    ]

    operations = [migrations.RunPython(set_chain_on_udc_orders)]
