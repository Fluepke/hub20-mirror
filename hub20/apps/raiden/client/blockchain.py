import asyncio
import logging
from concurrent.futures import TimeoutError
from typing import Optional

from asgiref.sync import sync_to_async
from eth_utils import to_checksum_address
from raiden_contracts.constants import (
    CONTRACT_CUSTOM_TOKEN,
    CONTRACT_SERVICE_REGISTRY,
    CONTRACT_TOKEN_NETWORK,
    CONTRACT_TOKEN_NETWORK_REGISTRY,
    CONTRACT_USER_DEPOSIT,
)
from raiden_contracts.contract_manager import (
    ContractManager,
    contracts_precompiled_path,
    get_contracts_deployment_info,
)
from web3 import Web3

from hub20.apps.blockchain.client import (
    BLOCK_CREATION_INTERVAL,
    get_transaction_by_hash,
    send_transaction,
)
from hub20.apps.blockchain.models import Block, Transaction
from hub20.apps.blockchain.typing import EthereumAccount_T
from hub20.apps.ethereum_money.abi import EIP20_ABI
from hub20.apps.ethereum_money.client import get_account_balance, make_token
from hub20.apps.ethereum_money.models import EthereumToken, EthereumTokenAmount
from hub20.apps.raiden import signals
from hub20.apps.raiden.exceptions import InsufficientBalanceError
from hub20.apps.raiden.models import Raiden, TokenNetwork, TokenNetworkChannel

GAS_REQUIRED_FOR_DEPOSIT: int = 200_000
GAS_REQUIRED_FOR_APPROVE: int = 70_000
GAS_REQUIRED_FOR_MINT: int = 100_000


logger = logging.getLogger(__name__)


def _get_contract_data(chain_id: int, contract_name: str):
    try:
        contract_data = get_contracts_deployment_info(chain_id)
        return contract_data["contracts"][contract_name]
    except KeyError:
        return None


def _get_user_deposit_contract(w3: Web3):
    contract_manager = ContractManager(contracts_precompiled_path())
    contract_address = get_contract_address(int(w3.net.version), CONTRACT_USER_DEPOSIT)
    return w3.eth.contract(
        address=contract_address, abi=contract_manager.get_contract_abi(CONTRACT_USER_DEPOSIT)
    )


def _get_contract(w3: Web3, contract_name: str):
    chain_id = int(w3.net.version)
    manager = ContractManager(contracts_precompiled_path())

    contract_data = _get_contract_data(chain_id, contract_name)
    assert contract_data

    abi = manager.get_contract_abi(contract_name)
    return w3.eth.contract(abi=abi, address=contract_data["address"])


def _get_token_network_contract(w3: Web3, token_network: TokenNetwork):
    manager = ContractManager(contracts_precompiled_path())
    abi = manager.get_contract_abi(CONTRACT_TOKEN_NETWORK)
    return w3.eth.contract(abi=abi, address=token_network.address)


def _get_channel_from_event(token_network: TokenNetwork, event) -> Optional[TokenNetworkChannel]:
    event_name = event.event
    if event_name == "ChannelOpened":
        participants = (event.args.participant1, event.args.participant2)
        channel_identifier = event.args.channel_identifier
        channel, _ = token_network.channels.get_or_create(
            identifier=channel_identifier, participant_addresses=participants
        )
        return channel

    if event_name == "ChannelClosed":
        channel_identifier = event.args.channel_identifier
        return token_network.channels.filter(identifier=channel_identifier).first()

    return None


def get_contract_address(chain_id, contract_name):
    try:
        contract_data = _get_contract_data(chain_id, contract_name)
        return contract_data["address"]
    except (TypeError, AssertionError, KeyError) as exc:
        raise ValueError(f"{contract_name} does not exist on chain id {chain_id}") from exc


def get_token_network_registry_contract(w3: Web3):
    return _get_contract(w3, CONTRACT_TOKEN_NETWORK_REGISTRY)


def get_service_token_address(chain_id: int):
    service_contract_data = _get_contract_data(chain_id, CONTRACT_SERVICE_REGISTRY)
    return service_contract_data["constructor_arguments"][0]


def get_service_token(w3: Web3) -> EthereumToken:
    chain_id = int(w3.net.version)
    service_token_address = get_service_token_address(chain_id)
    return make_token(w3=w3, address=service_token_address)


def get_service_token_contract(w3: Web3) -> EthereumToken:
    chain_id = int(w3.net.version)
    service_token_address = get_service_token_address(chain_id)
    return w3.eth.contract(address=service_token_address, abi=EIP20_ABI)


def mint_tokens(w3: Web3, account: EthereumAccount_T, amount: EthereumTokenAmount):
    logger.debug(f"Minting {amount.formatted}")
    contract_manager = ContractManager(contracts_precompiled_path())
    token_proxy = w3.eth.contract(
        address=to_checksum_address(amount.currency.address),
        abi=contract_manager.get_contract_abi(CONTRACT_CUSTOM_TOKEN),
    )

    send_transaction(
        w3=w3,
        contract_function=token_proxy.functions.mint,
        account=account,
        contract_args=(amount.as_wei,),
        gas=GAS_REQUIRED_FOR_MINT,
    )


def make_service_deposit(w3: Web3, account: EthereumAccount_T, amount: EthereumTokenAmount):
    token = amount.currency

    on_chain_balance = get_account_balance(w3=w3, token=token, address=account.address)

    if amount > on_chain_balance:
        raise InsufficientBalanceError(
            f"Current balance of {on_chain_balance.formatted} is insufficient"
        )

    user_deposit_contract = _get_user_deposit_contract(w3=w3)
    service_token_address = to_checksum_address(user_deposit_contract.functions.token().call())

    if service_token_address != token.address:
        raise ValueError(
            f"Deposit must be in {service_token_address}, {token.code} is {token.address}"
        )

    token_proxy = w3.eth.contract(address=token.address, abi=EIP20_ABI)
    current_deposit_amount = token.from_wei(
        user_deposit_contract.functions.total_deposit(account.address).call()
    )

    total_deposit = current_deposit_amount + amount

    old_allowance = token_proxy.functions.allowance(
        account.address, user_deposit_contract.address
    ).call()
    if old_allowance > 0:
        send_transaction(
            w3=w3,
            contract_function=token_proxy.functions.approve,
            account=account,
            contract_args=(user_deposit_contract.address, 0),
            gas=GAS_REQUIRED_FOR_APPROVE,
        )

    send_transaction(
        w3=w3,
        contract_function=token_proxy.functions.approve,
        account=account,
        contract_args=(user_deposit_contract.address, total_deposit.as_wei),
        gas=GAS_REQUIRED_FOR_APPROVE,
    )

    send_transaction(
        w3=w3,
        account=account,
        contract_function=user_deposit_contract.functions.deposit,
        contract_args=(account.address, total_deposit.as_wei),
        gas=GAS_REQUIRED_FOR_DEPOSIT,
    )


def get_service_deposit_balance(w3: Web3, raiden: Raiden) -> EthereumTokenAmount:
    user_deposit_contract = _get_user_deposit_contract(w3=w3)
    token = get_service_token(w3=w3)
    return token.from_wei(user_deposit_contract.functions.effectiveBalance(raiden.address).call())


def process_latest_deposits(w3: Web3, block_filter, user_deposit_contract, service_token):
    chain_id = int(w3.net.version)
    raidens_by_address = {a.address: a for a in Raiden.objects.all()}

    logger.info(f"Checking for UDC deposits on {raidens_by_address.keys()}")

    for block_hash in block_filter.get_new_entries():

        block_data = w3.eth.getBlock(block_hash.hex(), full_transactions=True)
        deposit_txs = [
            t for t in block_data.transactions if t["to"] == user_deposit_contract.address
        ]

        for tx_data in deposit_txs:
            fn, params = user_deposit_contract.decode_function_input(tx_data.input)

            deposit_identifier = user_deposit_contract.functions.deposit.function_identifier

            if fn.function_identifier == deposit_identifier:
                beneficiary = params["beneficiary"]

                if beneficiary in raidens_by_address.keys():
                    raiden = raidens_by_address[beneficiary]
                    tx_hash = tx_data.hash
                    amount = service_token.from_wei(params["new_total_deposit"])
                    logger.info(f"Deposit of {amount.formatted} from {raiden.address} detected")
                    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
                    block = Block.make(block_data, chain_id=chain_id)
                    tx = Transaction.make(tx_receipt=tx_receipt, tx_data=tx_data, block=block)
                    signals.service_deposit_sent.send(
                        sender=Transaction,
                        transaction=tx,
                        raiden=raiden,
                        amount=amount,
                        contract_address=user_deposit_contract.address,
                    )


def record_channel_events(w3: Web3, token_network: TokenNetwork, event_filter):
    try:
        for event in event_filter.get_all_entries():
            logger.info(f"Processing event {event.event} at {event.transactionHash.hex()}")

            tx = get_transaction_by_hash(w3, event.transactionHash)
            if not tx:
                logger.warning(f"Transaction {event.transactionHash} could not be synced")

            channel = _get_channel_from_event(token_network, event)
            if channel:
                token_network.events.get_or_create(
                    channel=channel, transaction=tx, name=event.event
                )
            else:
                logger.warning(f"Failed to find channel related to event {event}")
    except TimeoutError:
        logger.error(f"Timed-out while getting events for {token_network}")
    except Exception as exc:
        logger.error(f"Failed to get events for {token_network}: {exc}")


def record_token_network_events(w3: Web3, token_network: TokenNetwork):
    token_network_contract = _get_token_network_contract(w3=w3, token_network=token_network)
    event_blocks = Block.objects.filter(
        transactions__tokennetworkchannelevent__channel__token_network=token_network
    )
    from_block = Block.get_latest_block_number(event_blocks) + 1

    logger.info(f"Fetching {token_network.token} events since block {from_block}")

    channel_open_filter = token_network_contract.events.ChannelOpened.createFilter(
        fromBlock=from_block
    )
    channel_closed_filter = token_network_contract.events.ChannelClosed.createFilter(
        fromBlock=from_block
    )

    record_channel_events(w3=w3, token_network=token_network, event_filter=channel_open_filter)
    record_channel_events(w3=w3, token_network=token_network, event_filter=channel_closed_filter)


def get_all_service_deposits(w3: Web3, raiden: Raiden, **kw):
    user_deposit_contract_data = _get_contract_data(
        chain_id=int(w3.net.version), contract_name=CONTRACT_USER_DEPOSIT
    )
    user_deposit_contract = _get_user_deposit_contract(w3=w3)
    service_token = get_service_token(w3=w3)
    service_token_contract = get_service_token_contract(w3=w3)
    transfer_filter = service_token_contract.events.Transfer.createFilter(
        fromBlock=user_deposit_contract_data["block_number"],
        argument_filters={"_to": user_deposit_contract.address, "_from": raiden.address},
    )

    for entry in transfer_filter.get_all_entries():
        amount = service_token.from_wei(entry.args._value)
        tx = get_transaction_by_hash(w3=w3, transaction_hash=entry.transactionHash)
        signals.service_deposit_sent.send(
            sender=Transaction,
            transaction=tx,
            raiden=raiden,
            amount=amount,
            contract_address=user_deposit_contract.address,
        )


async def get_token_networks(w3: Web3, **kw):
    token_registry_contract = get_token_network_registry_contract(w3=w3)
    get_token_network_address = token_registry_contract.functions.token_to_token_networks

    erc20_tokens = await sync_to_async(EthereumToken.ERC20tokens.all)()
    for token in erc20_tokens:
        token_network_address = get_token_network_address(token.address).call()
        if token_network_address != EthereumToken.NULL_ADDRESS:
            sync_to_async(TokenNetwork.objects.update_or_create)(
                token=token, defaults={"address": token_network_address}
            )


async def listen_service_deposits(w3: Web3, **kw):
    block_filter = w3.eth.filter("latest")

    user_deposit_contract = _get_user_deposit_contract(w3=w3)
    service_token = await sync_to_async(get_service_token)(w3=w3)

    while True:
        await asyncio.sleep(BLOCK_CREATION_INTERVAL)
        await sync_to_async(process_latest_deposits)(
            w3, block_filter, user_deposit_contract, service_token
        )


async def listen_token_network_events(w3: Web3, **kw):
    while True:
        token_networks = await sync_to_async(list)(TokenNetwork.objects.all())
        for token_network in token_networks:
            await sync_to_async(record_token_network_events)(w3=w3, token_network=token_network)
            await asyncio.sleep(BLOCK_CREATION_INTERVAL)
