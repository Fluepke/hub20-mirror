# Generated by Django 3.2.3 on 2021-06-05 09:15

from django.conf import settings
import django.contrib.postgres.fields.ranges
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import hub20.apps.blockchain.fields
import hub20.apps.core.models.payments
import hub20.apps.ethereum_money.models
import model_utils.fields
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('blockchain', '0001_initial'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('ethereum_money', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('raiden', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('owner_id', models.PositiveIntegerField()),
                ('owner_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('token', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='books', to='ethereum_money.ethereumtoken')),
            ],
            options={
                'unique_together': {('token', 'owner_type', 'owner_id')},
            },
        ),
        migrations.CreateModel(
            name='Deposit',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('session_key', models.SlugField(null=True)),
                ('currency', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='ethereum_money.ethereumtoken')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ExternalAddressAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', hub20.apps.blockchain.fields.EthereumAddressField(unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('amount', hub20.apps.ethereum_money.models.EthereumTokenAmountField(decimal_places=18, max_digits=32)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('currency', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='ethereum_money.ethereumtoken')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PaymentRoute',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('deposit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='routes', to='core.deposit')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Store',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=300)),
                ('url', models.URLField()),
                ('accepted_currencies', models.ManyToManyField(to='ethereum_money.EthereumToken')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Transfer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', hub20.apps.ethereum_money.models.EthereumTokenAmountField(decimal_places=18, max_digits=32)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('address', hub20.apps.blockchain.fields.EthereumAddressField(db_index=True, null=True)),
                ('memo', models.TextField(blank=True, null=True)),
                ('identifier', models.CharField(blank=True, max_length=300, null=True)),
                ('execute_on', models.DateTimeField(auto_now_add=True)),
                ('currency', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='ethereum_money.ethereumtoken')),
                ('receiver', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='transfers_received', to=settings.AUTH_USER_MODEL)),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='transfers_sent', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TransferExecution',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('transfer', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='execution', to='core.transfer')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='InternalPayment',
            fields=[
                ('payment_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='core.payment')),
                ('memo', models.TextField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('core.payment',),
        ),
        migrations.CreateModel(
            name='InternalPaymentRoute',
            fields=[
                ('paymentroute_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='core.paymentroute')),
            ],
            options={
                'abstract': False,
            },
            bases=('core.paymentroute',),
        ),
        migrations.CreateModel(
            name='PaymentOrder',
            fields=[
                ('deposit_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='core.deposit')),
                ('amount', hub20.apps.ethereum_money.models.EthereumTokenAmountField(decimal_places=18, max_digits=32)),
            ],
            options={
                'abstract': False,
            },
            bases=('core.deposit', models.Model),
        ),
        migrations.CreateModel(
            name='WalletAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='onchain_account', to='blockchain.baseethereumaccount')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='UserAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='account', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Treasury',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chain', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='blockchain.chain')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TransferReceipt',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('network', models.CharField(choices=[('blockchain', 'blockchain'), ('raiden', 'raiden'), ('internal', 'internal')], max_length=64)),
                ('identifier', models.CharField(max_length=300, null=True)),
                ('transfer', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='receipt', to='core.transfer')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TransferFailure',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('transfer', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='failure', to='core.transfer')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TransferCancellation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('canceled_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('transfer', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='cancellation', to='core.transfer')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StoreRSAKeyPair',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('public_key_pem', models.TextField()),
                ('private_key_pem', models.TextField()),
                ('store', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='rsa', to='core.store')),
            ],
        ),
        migrations.CreateModel(
            name='RaidenClientAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('raiden', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='raiden_account', to='raiden.raiden')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PaymentConfirmation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('payment', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='confirmation', to='core.payment')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='payment',
            name='route',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.paymentroute'),
        ),
        migrations.CreateModel(
            name='RaidenTransferExecution',
            fields=[
                ('transferexecution_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='core.transferexecution')),
                ('payment', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='raiden.payment')),
            ],
            options={
                'abstract': False,
            },
            bases=('core.transferexecution',),
        ),
        migrations.CreateModel(
            name='RaidenPayment',
            fields=[
                ('payment_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='core.payment')),
                ('payment', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='raiden.payment')),
            ],
            options={
                'abstract': False,
            },
            bases=('core.payment',),
        ),
        migrations.CreateModel(
            name='Debit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', hub20.apps.ethereum_money.models.EthereumTokenAmountField(decimal_places=18, max_digits=32)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('reference_id', models.PositiveIntegerField()),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='debits', to='core.book')),
                ('currency', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='ethereum_money.ethereumtoken')),
                ('reference_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
            ],
            options={
                'abstract': False,
                'unique_together': {('book', 'reference_type', 'reference_id')},
            },
        ),
        migrations.CreateModel(
            name='Credit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', hub20.apps.ethereum_money.models.EthereumTokenAmountField(decimal_places=18, max_digits=32)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('reference_id', models.PositiveIntegerField()),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='credits', to='core.book')),
                ('currency', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='ethereum_money.ethereumtoken')),
                ('reference_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
            ],
            options={
                'abstract': False,
                'unique_together': {('book', 'reference_type', 'reference_id')},
            },
        ),
        migrations.CreateModel(
            name='BlockchainTransferExecution',
            fields=[
                ('transferexecution_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='core.transferexecution')),
                ('transaction', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='blockchain.transaction')),
            ],
            options={
                'abstract': False,
            },
            bases=('core.transferexecution',),
        ),
        migrations.CreateModel(
            name='BlockchainPaymentRoute',
            fields=[
                ('paymentroute_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='core.paymentroute')),
                ('payment_window', django.contrib.postgres.fields.ranges.IntegerRangeField(default=hub20.apps.core.models.payments.calculate_blockchain_payment_window)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blockchain_routes', to='blockchain.baseethereumaccount')),
                ('chain', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='blockchain.chain')),
            ],
            options={
                'abstract': False,
            },
            bases=('core.paymentroute',),
        ),
        migrations.CreateModel(
            name='BlockchainPayment',
            fields=[
                ('payment_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='core.payment')),
                ('transaction', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='blockchain.transaction')),
            ],
            options={
                'abstract': False,
            },
            bases=('core.payment',),
        ),
        migrations.CreateModel(
            name='RaidenPaymentRoute',
            fields=[
                ('paymentroute_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='core.paymentroute')),
                ('payment_window', models.DurationField(default=hub20.apps.core.models.payments.calculate_raiden_payment_window)),
                ('identifier', models.BigIntegerField(default=hub20.apps.core.models.payments.generate_payment_order_id, unique=True)),
                ('raiden', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_routes', to='raiden.raiden')),
            ],
            options={
                'unique_together': {('raiden', 'identifier')},
            },
            bases=('core.paymentroute',),
        ),
        migrations.CreateModel(
            name='Checkout',
            fields=[
                ('paymentorder_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='core.paymentorder')),
                ('external_identifier', models.TextField()),
                ('requester_ip', models.GenericIPAddressField(null=True)),
                ('store', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.store')),
            ],
            options={
                'abstract': False,
            },
            bases=('core.paymentorder',),
        ),
    ]
