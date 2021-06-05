# Generated by Django 3.2.3 on 2021-06-05 09:15

import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import hub20.apps.blockchain.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Block',
            fields=[
                ('hash', hub20.apps.blockchain.fields.HexField(max_length=64, primary_key=True, serialize=False)),
                ('number', models.PositiveIntegerField(db_index=True)),
                ('timestamp', models.DateTimeField()),
                ('parent_hash', hub20.apps.blockchain.fields.HexField(max_length=64)),
                ('uncle_hashes', django.contrib.postgres.fields.ArrayField(base_field=hub20.apps.blockchain.fields.HexField(max_length=64), size=None)),
            ],
        ),
        migrations.CreateModel(
            name='Chain',
            fields=[
                ('id', models.PositiveIntegerField(choices=[(1, 'Mainnet'), (2, 'Test Network'), (3, 'Ropsten'), (4, 'Rinkeby'), (5, 'Görli'), (42, 'Kovan')], default=1, primary_key=True, serialize=False)),
                ('provider_url', models.URLField(unique=True)),
                ('synced', models.BooleanField()),
                ('online', models.BooleanField(default=False)),
                ('highest_block', models.PositiveIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hash', hub20.apps.blockchain.fields.HexField(db_index=True, max_length=64)),
                ('from_address', hub20.apps.blockchain.fields.EthereumAddressField(db_index=True)),
                ('to_address', hub20.apps.blockchain.fields.EthereumAddressField(db_index=True)),
                ('gas_used', hub20.apps.blockchain.fields.Uint256Field()),
                ('gas_price', hub20.apps.blockchain.fields.Uint256Field()),
                ('nonce', hub20.apps.blockchain.fields.Uint256Field()),
                ('index', hub20.apps.blockchain.fields.Uint256Field()),
                ('value', hub20.apps.blockchain.fields.Uint256Field()),
                ('data', models.TextField()),
                ('block', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='blockchain.block')),
            ],
        ),
        migrations.AddField(
            model_name='block',
            name='chain',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blocks', to='blockchain.chain'),
        ),
        migrations.CreateModel(
            name='BaseEthereumAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', hub20.apps.blockchain.fields.EthereumAddressField(db_index=True, unique=True)),
                ('transactions', models.ManyToManyField(to='blockchain.Transaction')),
            ],
        ),
        migrations.CreateModel(
            name='TransactionLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('index', models.SmallIntegerField()),
                ('data', models.TextField()),
                ('topics', django.contrib.postgres.fields.ArrayField(base_field=models.TextField(), size=None)),
                ('transaction', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='blockchain.transaction')),
            ],
            options={
                'unique_together': {('transaction', 'index')},
            },
        ),
        migrations.AlterUniqueTogether(
            name='block',
            unique_together={('chain', 'hash', 'number')},
        ),
    ]
