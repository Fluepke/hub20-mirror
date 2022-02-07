import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from hub20.apps.blockchain.models import Transaction
from hub20.apps.core.models import (
    BlockchainTransfer,
    BlockchainTransferConfirmation,
    RaidenTransfer,
    RaidenTransferConfirmation,
)
from hub20.apps.ethereum_money.signals import outgoing_transfer_mined
from hub20.apps.raiden.models import Payment

logger = logging.getLogger(__name__)


@receiver(outgoing_transfer_mined, sender=Transaction)
def on_blockchain_transfer_mined_record_confirmation(sender, **kw):
    amount = kw["amount"]
    transaction = kw["transaction"]
    address = kw["address"]

    transfer = BlockchainTransfer.processed.filter(
        amount=amount.amount,
        currency=amount.currency,
        address=address,
        receipt__blockchaintransferreceipt__transaction_data__hash=transaction.hash,
    ).first()

    if transfer:
        BlockchainTransferConfirmation.objects.create(transfer=transfer, transaction=transaction)


@receiver(post_save, sender=Payment)
def on_raiden_payment_sent_record_confirmation(sender, **kw):
    if kw["created"]:
        payment = kw["instance"]

        transfer = RaidenTransfer.processed.filter(
            amount=payment.amount,
            currency=payment.token,
            address=payment.receiver_address,
            receipt__raidentransferreceipt__payment_data__identifier=payment.identifier,
        ).first()

        if transfer:
            RaidenTransferConfirmation.objects.create(transfer=transfer, payment=payment)


__all__ = [
    "on_blockchain_transfer_mined_record_confirmation",
    "on_raiden_payment_sent_record_confirmation",
]
