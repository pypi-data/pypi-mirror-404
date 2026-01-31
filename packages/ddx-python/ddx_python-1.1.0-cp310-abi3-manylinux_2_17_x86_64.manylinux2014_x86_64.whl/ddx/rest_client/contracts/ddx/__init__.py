"""Generated wrapper for DDX Solidity contract."""

# pylint: disable=too-many-arguments

import json
from typing import (  # pylint: disable=unused-import
    Any,
    List,
    Optional,
    Tuple,
    Union,
)

from eth_utils import to_checksum_address
from mypy_extensions import TypedDict  # pylint: disable=unused-import
from hexbytes import HexBytes
from web3 import Web3
from web3.datastructures import AttributeDict
from web3.providers.base import BaseProvider

from zero_ex.contract_wrappers.bases import ContractMethod, Validator
from zero_ex.contract_wrappers.tx_params import TxParams


# Try to import a custom validator class definition; if there isn't one,
# declare one that we can instantiate for the default argument to the
# constructor for DDX below.
try:
    # both mypy and pylint complain about what we're doing here, but this
    # works just fine, so their messages have been disabled here.
    from . import (  # type: ignore # pylint: disable=import-self
        DDXValidator,
    )
except ImportError:

    class DDXValidator(  # type: ignore
        Validator
    ):
        """No-op input validator."""


try:
    from .middleware import MIDDLEWARE  # type: ignore
except ImportError:
    pass





class MaxSupplyMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the MAX_SUPPLY method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address)
        self._underlying_method = contract_function

    def call(self, tx_params: Optional[TxParams] = None) -> int:
        """Execute underlying contract method via eth_call.

        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method().call(tx_params.as_dict())
        return int(returned)

    def send_transaction(self, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param tx_params: transaction parameters
        """
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method().transact(tx_params.as_dict())

    def build_transaction(self, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method().build_transaction(tx_params.as_dict())

    def estimate_gas(self, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method().estimate_gas(tx_params.as_dict())

class PreMineSupplyMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the PRE_MINE_SUPPLY method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address)
        self._underlying_method = contract_function

    def call(self, tx_params: Optional[TxParams] = None) -> int:
        """Execute underlying contract method via eth_call.

        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method().call(tx_params.as_dict())
        return int(returned)

    def send_transaction(self, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param tx_params: transaction parameters
        """
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method().transact(tx_params.as_dict())

    def build_transaction(self, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method().build_transaction(tx_params.as_dict())

    def estimate_gas(self, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method().estimate_gas(tx_params.as_dict())

class AllowanceMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the allowance method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, account: str, spender: str):
        """Validate the inputs to the allowance method."""
        self.validator.assert_valid(
            method_name='allowance',
            parameter_name='_account',
            argument_value=account,
        )
        account = self.validate_and_checksum_address(account)
        self.validator.assert_valid(
            method_name='allowance',
            parameter_name='_spender',
            argument_value=spender,
        )
        spender = self.validate_and_checksum_address(spender)
        return (account, spender)

    def call(self, account: str, spender: str, tx_params: Optional[TxParams] = None) -> int:
        """Execute underlying contract method via eth_call.

        :param _account: The address of the account holding the funds
        :param _spender: The address of the account spending the funds
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (account, spender) = self.validate_and_normalize_inputs(account, spender)
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method(account, spender).call(tx_params.as_dict())
        return int(returned)

    def send_transaction(self, account: str, spender: str, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param _account: The address of the account holding the funds
        :param _spender: The address of the account spending the funds
        :param tx_params: transaction parameters
        """
        (account, spender) = self.validate_and_normalize_inputs(account, spender)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(account, spender).transact(tx_params.as_dict())

    def build_transaction(self, account: str, spender: str, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (account, spender) = self.validate_and_normalize_inputs(account, spender)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(account, spender).build_transaction(tx_params.as_dict())

    def estimate_gas(self, account: str, spender: str, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (account, spender) = self.validate_and_normalize_inputs(account, spender)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(account, spender).estimate_gas(tx_params.as_dict())

class ApproveMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the approve method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, spender: str, amount: int):
        """Validate the inputs to the approve method."""
        self.validator.assert_valid(
            method_name='approve',
            parameter_name='_spender',
            argument_value=spender,
        )
        spender = self.validate_and_checksum_address(spender)
        self.validator.assert_valid(
            method_name='approve',
            parameter_name='_amount',
            argument_value=amount,
        )
        # safeguard against fractional inputs
        amount = int(amount)
        return (spender, amount)

    def call(self, spender: str, amount: int, tx_params: Optional[TxParams] = None) -> bool:
        """Execute underlying contract method via eth_call.

        This will overwrite the approval amount for `spender` and is subject to
        issues noted [here](https://eips.ethereum.org/EIPS/eip-20#approve)

        :param _amount: The number of tokens that are approved (2^256-1 means
            infinite)
        :param _spender: The address of the account which may transfer tokens
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (spender, amount) = self.validate_and_normalize_inputs(spender, amount)
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method(spender, amount).call(tx_params.as_dict())
        return bool(returned)

    def send_transaction(self, spender: str, amount: int, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        This will overwrite the approval amount for `spender` and is subject to
        issues noted [here](https://eips.ethereum.org/EIPS/eip-20#approve)

        :param _amount: The number of tokens that are approved (2^256-1 means
            infinite)
        :param _spender: The address of the account which may transfer tokens
        :param tx_params: transaction parameters
        """
        (spender, amount) = self.validate_and_normalize_inputs(spender, amount)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(spender, amount).transact(tx_params.as_dict())

    def build_transaction(self, spender: str, amount: int, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (spender, amount) = self.validate_and_normalize_inputs(spender, amount)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(spender, amount).build_transaction(tx_params.as_dict())

    def estimate_gas(self, spender: str, amount: int, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (spender, amount) = self.validate_and_normalize_inputs(spender, amount)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(spender, amount).estimate_gas(tx_params.as_dict())

class BalanceOfMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the balanceOf method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, account: str):
        """Validate the inputs to the balanceOf method."""
        self.validator.assert_valid(
            method_name='balanceOf',
            parameter_name='_account',
            argument_value=account,
        )
        account = self.validate_and_checksum_address(account)
        return (account)

    def call(self, account: str, tx_params: Optional[TxParams] = None) -> int:
        """Execute underlying contract method via eth_call.

        :param _account: The address of the account to get the balance of
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (account) = self.validate_and_normalize_inputs(account)
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method(account).call(tx_params.as_dict())
        return int(returned)

    def send_transaction(self, account: str, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param _account: The address of the account to get the balance of
        :param tx_params: transaction parameters
        """
        (account) = self.validate_and_normalize_inputs(account)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(account).transact(tx_params.as_dict())

    def build_transaction(self, account: str, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (account) = self.validate_and_normalize_inputs(account)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(account).build_transaction(tx_params.as_dict())

    def estimate_gas(self, account: str, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (account) = self.validate_and_normalize_inputs(account)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(account).estimate_gas(tx_params.as_dict())

class BurnMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the burn method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, amount: int):
        """Validate the inputs to the burn method."""
        self.validator.assert_valid(
            method_name='burn',
            parameter_name='_amount',
            argument_value=amount,
        )
        # safeguard against fractional inputs
        amount = int(amount)
        return (amount)

    def call(self, amount: int, tx_params: Optional[TxParams] = None) -> None:
        """Execute underlying contract method via eth_call.

        Creates `amount` tokens and assigns them to `account`, decreasing the
        total supply. Emits a {Transfer} event with `from` set to the zero
        address. Requirements - `to` cannot be the zero address.

        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (amount) = self.validate_and_normalize_inputs(amount)
        tx_params = super().normalize_tx_params(tx_params)
        self._underlying_method(amount).call(tx_params.as_dict())

    def send_transaction(self, amount: int, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        Creates `amount` tokens and assigns them to `account`, decreasing the
        total supply. Emits a {Transfer} event with `from` set to the zero
        address. Requirements - `to` cannot be the zero address.

        :param tx_params: transaction parameters
        """
        (amount) = self.validate_and_normalize_inputs(amount)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(amount).transact(tx_params.as_dict())

    def build_transaction(self, amount: int, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (amount) = self.validate_and_normalize_inputs(amount)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(amount).build_transaction(tx_params.as_dict())

    def estimate_gas(self, amount: int, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (amount) = self.validate_and_normalize_inputs(amount)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(amount).estimate_gas(tx_params.as_dict())

class BurnFromMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the burnFrom method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, account: str, amount: int):
        """Validate the inputs to the burnFrom method."""
        self.validator.assert_valid(
            method_name='burnFrom',
            parameter_name='_account',
            argument_value=account,
        )
        account = self.validate_and_checksum_address(account)
        self.validator.assert_valid(
            method_name='burnFrom',
            parameter_name='_amount',
            argument_value=amount,
        )
        # safeguard against fractional inputs
        amount = int(amount)
        return (account, amount)

    def call(self, account: str, amount: int, tx_params: Optional[TxParams] = None) -> None:
        """Execute underlying contract method via eth_call.

        Creates `amount` tokens and assigns them to `account`, increasing the
        total supply. Emits a {Transfer} event with `from` set to the zero
        address. Requirements - `to` cannot be the zero address.

        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (account, amount) = self.validate_and_normalize_inputs(account, amount)
        tx_params = super().normalize_tx_params(tx_params)
        self._underlying_method(account, amount).call(tx_params.as_dict())

    def send_transaction(self, account: str, amount: int, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        Creates `amount` tokens and assigns them to `account`, increasing the
        total supply. Emits a {Transfer} event with `from` set to the zero
        address. Requirements - `to` cannot be the zero address.

        :param tx_params: transaction parameters
        """
        (account, amount) = self.validate_and_normalize_inputs(account, amount)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(account, amount).transact(tx_params.as_dict())

    def build_transaction(self, account: str, amount: int, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (account, amount) = self.validate_and_normalize_inputs(account, amount)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(account, amount).build_transaction(tx_params.as_dict())

    def estimate_gas(self, account: str, amount: int, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (account, amount) = self.validate_and_normalize_inputs(account, amount)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(account, amount).estimate_gas(tx_params.as_dict())

class CheckpointsMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the checkpoints method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, index_0: str, index_1: int):
        """Validate the inputs to the checkpoints method."""
        self.validator.assert_valid(
            method_name='checkpoints',
            parameter_name='index_0',
            argument_value=index_0,
        )
        index_0 = self.validate_and_checksum_address(index_0)
        self.validator.assert_valid(
            method_name='checkpoints',
            parameter_name='index_1',
            argument_value=index_1,
        )
        # safeguard against fractional inputs
        index_1 = int(index_1)
        return (index_0, index_1)

    def call(self, index_0: str, index_1: int, tx_params: Optional[TxParams] = None) -> Tuple[int, int]:
        """Execute underlying contract method via eth_call.

        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (index_0, index_1) = self.validate_and_normalize_inputs(index_0, index_1)
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method(index_0, index_1).call(tx_params.as_dict())
        return (returned[0],returned[1],)

    def send_transaction(self, index_0: str, index_1: int, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param tx_params: transaction parameters
        """
        (index_0, index_1) = self.validate_and_normalize_inputs(index_0, index_1)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(index_0, index_1).transact(tx_params.as_dict())

    def build_transaction(self, index_0: str, index_1: int, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (index_0, index_1) = self.validate_and_normalize_inputs(index_0, index_1)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(index_0, index_1).build_transaction(tx_params.as_dict())

    def estimate_gas(self, index_0: str, index_1: int, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (index_0, index_1) = self.validate_and_normalize_inputs(index_0, index_1)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(index_0, index_1).estimate_gas(tx_params.as_dict())

class DecimalsMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the decimals method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address)
        self._underlying_method = contract_function

    def call(self, tx_params: Optional[TxParams] = None) -> int:
        """Execute underlying contract method via eth_call.

        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method().call(tx_params.as_dict())
        return int(returned)

    def send_transaction(self, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param tx_params: transaction parameters
        """
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method().transact(tx_params.as_dict())

    def build_transaction(self, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method().build_transaction(tx_params.as_dict())

    def estimate_gas(self, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method().estimate_gas(tx_params.as_dict())

class DecreaseAllowanceMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the decreaseAllowance method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, spender: str, subtracted_value: int):
        """Validate the inputs to the decreaseAllowance method."""
        self.validator.assert_valid(
            method_name='decreaseAllowance',
            parameter_name='_spender',
            argument_value=spender,
        )
        spender = self.validate_and_checksum_address(spender)
        self.validator.assert_valid(
            method_name='decreaseAllowance',
            parameter_name='_subtractedValue',
            argument_value=subtracted_value,
        )
        # safeguard against fractional inputs
        subtracted_value = int(subtracted_value)
        return (spender, subtracted_value)

    def call(self, spender: str, subtracted_value: int, tx_params: Optional[TxParams] = None) -> bool:
        """Execute underlying contract method via eth_call.

        Atomically decreases the allowance granted to `spender` by the caller.
        This is an alternative to {approve} that can be used as a mitigation
        for problems described in {IERC20-approve}. Emits an {Approval} event
        indicating the updated allowance. Requirements: - `spender` cannot be
        the zero address. - `spender` must have allowance for the caller of at
        least `subtractedValue`.

        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (spender, subtracted_value) = self.validate_and_normalize_inputs(spender, subtracted_value)
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method(spender, subtracted_value).call(tx_params.as_dict())
        return bool(returned)

    def send_transaction(self, spender: str, subtracted_value: int, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        Atomically decreases the allowance granted to `spender` by the caller.
        This is an alternative to {approve} that can be used as a mitigation
        for problems described in {IERC20-approve}. Emits an {Approval} event
        indicating the updated allowance. Requirements: - `spender` cannot be
        the zero address. - `spender` must have allowance for the caller of at
        least `subtractedValue`.

        :param tx_params: transaction parameters
        """
        (spender, subtracted_value) = self.validate_and_normalize_inputs(spender, subtracted_value)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(spender, subtracted_value).transact(tx_params.as_dict())

    def build_transaction(self, spender: str, subtracted_value: int, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (spender, subtracted_value) = self.validate_and_normalize_inputs(spender, subtracted_value)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(spender, subtracted_value).build_transaction(tx_params.as_dict())

    def estimate_gas(self, spender: str, subtracted_value: int, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (spender, subtracted_value) = self.validate_and_normalize_inputs(spender, subtracted_value)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(spender, subtracted_value).estimate_gas(tx_params.as_dict())

class DelegateMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the delegate method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, delegatee: str):
        """Validate the inputs to the delegate method."""
        self.validator.assert_valid(
            method_name='delegate',
            parameter_name='_delegatee',
            argument_value=delegatee,
        )
        delegatee = self.validate_and_checksum_address(delegatee)
        return (delegatee)

    def call(self, delegatee: str, tx_params: Optional[TxParams] = None) -> None:
        """Execute underlying contract method via eth_call.

        :param _delegatee: The address to delegate votes to
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (delegatee) = self.validate_and_normalize_inputs(delegatee)
        tx_params = super().normalize_tx_params(tx_params)
        self._underlying_method(delegatee).call(tx_params.as_dict())

    def send_transaction(self, delegatee: str, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param _delegatee: The address to delegate votes to
        :param tx_params: transaction parameters
        """
        (delegatee) = self.validate_and_normalize_inputs(delegatee)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(delegatee).transact(tx_params.as_dict())

    def build_transaction(self, delegatee: str, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (delegatee) = self.validate_and_normalize_inputs(delegatee)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(delegatee).build_transaction(tx_params.as_dict())

    def estimate_gas(self, delegatee: str, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (delegatee) = self.validate_and_normalize_inputs(delegatee)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(delegatee).estimate_gas(tx_params.as_dict())

class DelegateBySigMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the delegateBySig method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, delegatee: str, nonce: int, expiry: int, signature: Union[bytes, str]):
        """Validate the inputs to the delegateBySig method."""
        self.validator.assert_valid(
            method_name='delegateBySig',
            parameter_name='_delegatee',
            argument_value=delegatee,
        )
        delegatee = self.validate_and_checksum_address(delegatee)
        self.validator.assert_valid(
            method_name='delegateBySig',
            parameter_name='_nonce',
            argument_value=nonce,
        )
        # safeguard against fractional inputs
        nonce = int(nonce)
        self.validator.assert_valid(
            method_name='delegateBySig',
            parameter_name='_expiry',
            argument_value=expiry,
        )
        # safeguard against fractional inputs
        expiry = int(expiry)
        self.validator.assert_valid(
            method_name='delegateBySig',
            parameter_name='_signature',
            argument_value=signature,
        )
        return (delegatee, nonce, expiry, signature)

    def call(self, delegatee: str, nonce: int, expiry: int, signature: Union[bytes, str], tx_params: Optional[TxParams] = None) -> None:
        """Execute underlying contract method via eth_call.

        :param _delegatee: The address to delegate votes to
        :param _expiry: The time at which to expire the signature
        :param _nonce: The contract state required to match the signature
        :param _signature: Signature
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (delegatee, nonce, expiry, signature) = self.validate_and_normalize_inputs(delegatee, nonce, expiry, signature)
        tx_params = super().normalize_tx_params(tx_params)
        self._underlying_method(delegatee, nonce, expiry, signature).call(tx_params.as_dict())

    def send_transaction(self, delegatee: str, nonce: int, expiry: int, signature: Union[bytes, str], tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param _delegatee: The address to delegate votes to
        :param _expiry: The time at which to expire the signature
        :param _nonce: The contract state required to match the signature
        :param _signature: Signature
        :param tx_params: transaction parameters
        """
        (delegatee, nonce, expiry, signature) = self.validate_and_normalize_inputs(delegatee, nonce, expiry, signature)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(delegatee, nonce, expiry, signature).transact(tx_params.as_dict())

    def build_transaction(self, delegatee: str, nonce: int, expiry: int, signature: Union[bytes, str], tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (delegatee, nonce, expiry, signature) = self.validate_and_normalize_inputs(delegatee, nonce, expiry, signature)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(delegatee, nonce, expiry, signature).build_transaction(tx_params.as_dict())

    def estimate_gas(self, delegatee: str, nonce: int, expiry: int, signature: Union[bytes, str], tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (delegatee, nonce, expiry, signature) = self.validate_and_normalize_inputs(delegatee, nonce, expiry, signature)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(delegatee, nonce, expiry, signature).estimate_gas(tx_params.as_dict())

class DelegatesMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the delegates method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, index_0: str):
        """Validate the inputs to the delegates method."""
        self.validator.assert_valid(
            method_name='delegates',
            parameter_name='index_0',
            argument_value=index_0,
        )
        index_0 = self.validate_and_checksum_address(index_0)
        return (index_0)

    def call(self, index_0: str, tx_params: Optional[TxParams] = None) -> str:
        """Execute underlying contract method via eth_call.

        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (index_0) = self.validate_and_normalize_inputs(index_0)
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method(index_0).call(tx_params.as_dict())
        return str(returned)

    def send_transaction(self, index_0: str, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param tx_params: transaction parameters
        """
        (index_0) = self.validate_and_normalize_inputs(index_0)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(index_0).transact(tx_params.as_dict())

    def build_transaction(self, index_0: str, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (index_0) = self.validate_and_normalize_inputs(index_0)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(index_0).build_transaction(tx_params.as_dict())

    def estimate_gas(self, index_0: str, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (index_0) = self.validate_and_normalize_inputs(index_0)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(index_0).estimate_gas(tx_params.as_dict())

class GetCurrentVotesMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the getCurrentVotes method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, account: str):
        """Validate the inputs to the getCurrentVotes method."""
        self.validator.assert_valid(
            method_name='getCurrentVotes',
            parameter_name='_account',
            argument_value=account,
        )
        account = self.validate_and_checksum_address(account)
        return (account)

    def call(self, account: str, tx_params: Optional[TxParams] = None) -> int:
        """Execute underlying contract method via eth_call.

        :param _account: The address to get votes balance.
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (account) = self.validate_and_normalize_inputs(account)
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method(account).call(tx_params.as_dict())
        return int(returned)

    def send_transaction(self, account: str, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param _account: The address to get votes balance.
        :param tx_params: transaction parameters
        """
        (account) = self.validate_and_normalize_inputs(account)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(account).transact(tx_params.as_dict())

    def build_transaction(self, account: str, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (account) = self.validate_and_normalize_inputs(account)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(account).build_transaction(tx_params.as_dict())

    def estimate_gas(self, account: str, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (account) = self.validate_and_normalize_inputs(account)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(account).estimate_gas(tx_params.as_dict())

class GetPriorVotesMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the getPriorVotes method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, account: str, block_number: int):
        """Validate the inputs to the getPriorVotes method."""
        self.validator.assert_valid(
            method_name='getPriorVotes',
            parameter_name='_account',
            argument_value=account,
        )
        account = self.validate_and_checksum_address(account)
        self.validator.assert_valid(
            method_name='getPriorVotes',
            parameter_name='_blockNumber',
            argument_value=block_number,
        )
        # safeguard against fractional inputs
        block_number = int(block_number)
        return (account, block_number)

    def call(self, account: str, block_number: int, tx_params: Optional[TxParams] = None) -> int:
        """Execute underlying contract method via eth_call.

        Block number must be a finalized block or else this function will
        revert to prevent misinformation.

        :param _account: The address of the account to check
        :param _blockNumber: The block number to get the vote balance at
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (account, block_number) = self.validate_and_normalize_inputs(account, block_number)
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method(account, block_number).call(tx_params.as_dict())
        return int(returned)

    def send_transaction(self, account: str, block_number: int, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        Block number must be a finalized block or else this function will
        revert to prevent misinformation.

        :param _account: The address of the account to check
        :param _blockNumber: The block number to get the vote balance at
        :param tx_params: transaction parameters
        """
        (account, block_number) = self.validate_and_normalize_inputs(account, block_number)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(account, block_number).transact(tx_params.as_dict())

    def build_transaction(self, account: str, block_number: int, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (account, block_number) = self.validate_and_normalize_inputs(account, block_number)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(account, block_number).build_transaction(tx_params.as_dict())

    def estimate_gas(self, account: str, block_number: int, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (account, block_number) = self.validate_and_normalize_inputs(account, block_number)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(account, block_number).estimate_gas(tx_params.as_dict())

class IncreaseAllowanceMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the increaseAllowance method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, spender: str, added_value: int):
        """Validate the inputs to the increaseAllowance method."""
        self.validator.assert_valid(
            method_name='increaseAllowance',
            parameter_name='_spender',
            argument_value=spender,
        )
        spender = self.validate_and_checksum_address(spender)
        self.validator.assert_valid(
            method_name='increaseAllowance',
            parameter_name='_addedValue',
            argument_value=added_value,
        )
        # safeguard against fractional inputs
        added_value = int(added_value)
        return (spender, added_value)

    def call(self, spender: str, added_value: int, tx_params: Optional[TxParams] = None) -> bool:
        """Execute underlying contract method via eth_call.

        Atomically increases the allowance granted to `spender` by the caller.
        This is an alternative to {approve} that can be used as a mitigation
        for problems described in {IERC20-approve}. Emits an {Approval} event
        indicating the updated allowance. Requirements: - `spender` cannot be
        the zero address.

        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (spender, added_value) = self.validate_and_normalize_inputs(spender, added_value)
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method(spender, added_value).call(tx_params.as_dict())
        return bool(returned)

    def send_transaction(self, spender: str, added_value: int, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        Atomically increases the allowance granted to `spender` by the caller.
        This is an alternative to {approve} that can be used as a mitigation
        for problems described in {IERC20-approve}. Emits an {Approval} event
        indicating the updated allowance. Requirements: - `spender` cannot be
        the zero address.

        :param tx_params: transaction parameters
        """
        (spender, added_value) = self.validate_and_normalize_inputs(spender, added_value)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(spender, added_value).transact(tx_params.as_dict())

    def build_transaction(self, spender: str, added_value: int, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (spender, added_value) = self.validate_and_normalize_inputs(spender, added_value)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(spender, added_value).build_transaction(tx_params.as_dict())

    def estimate_gas(self, spender: str, added_value: int, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (spender, added_value) = self.validate_and_normalize_inputs(spender, added_value)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(spender, added_value).estimate_gas(tx_params.as_dict())

class IssuedSupplyMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the issuedSupply method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address)
        self._underlying_method = contract_function

    def call(self, tx_params: Optional[TxParams] = None) -> int:
        """Execute underlying contract method via eth_call.

        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method().call(tx_params.as_dict())
        return int(returned)

    def send_transaction(self, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param tx_params: transaction parameters
        """
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method().transact(tx_params.as_dict())

    def build_transaction(self, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method().build_transaction(tx_params.as_dict())

    def estimate_gas(self, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method().estimate_gas(tx_params.as_dict())

class IssuerMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the issuer method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address)
        self._underlying_method = contract_function

    def call(self, tx_params: Optional[TxParams] = None) -> str:
        """Execute underlying contract method via eth_call.

        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method().call(tx_params.as_dict())
        return str(returned)

    def send_transaction(self, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param tx_params: transaction parameters
        """
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method().transact(tx_params.as_dict())

    def build_transaction(self, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method().build_transaction(tx_params.as_dict())

    def estimate_gas(self, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method().estimate_gas(tx_params.as_dict())

class MintMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the mint method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, recipient: str, amount: int):
        """Validate the inputs to the mint method."""
        self.validator.assert_valid(
            method_name='mint',
            parameter_name='_recipient',
            argument_value=recipient,
        )
        recipient = self.validate_and_checksum_address(recipient)
        self.validator.assert_valid(
            method_name='mint',
            parameter_name='_amount',
            argument_value=amount,
        )
        # safeguard against fractional inputs
        amount = int(amount)
        return (recipient, amount)

    def call(self, recipient: str, amount: int, tx_params: Optional[TxParams] = None) -> None:
        """Execute underlying contract method via eth_call.

        Creates `amount` tokens and assigns them to `account`, increasing the
        total supply. Emits a {Transfer} event with `from` set to the zero
        address. Requirements - `to` cannot be the zero address.

        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (recipient, amount) = self.validate_and_normalize_inputs(recipient, amount)
        tx_params = super().normalize_tx_params(tx_params)
        self._underlying_method(recipient, amount).call(tx_params.as_dict())

    def send_transaction(self, recipient: str, amount: int, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        Creates `amount` tokens and assigns them to `account`, increasing the
        total supply. Emits a {Transfer} event with `from` set to the zero
        address. Requirements - `to` cannot be the zero address.

        :param tx_params: transaction parameters
        """
        (recipient, amount) = self.validate_and_normalize_inputs(recipient, amount)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(recipient, amount).transact(tx_params.as_dict())

    def build_transaction(self, recipient: str, amount: int, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (recipient, amount) = self.validate_and_normalize_inputs(recipient, amount)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(recipient, amount).build_transaction(tx_params.as_dict())

    def estimate_gas(self, recipient: str, amount: int, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (recipient, amount) = self.validate_and_normalize_inputs(recipient, amount)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(recipient, amount).estimate_gas(tx_params.as_dict())

class NameMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the name method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address)
        self._underlying_method = contract_function

    def call(self, tx_params: Optional[TxParams] = None) -> str:
        """Execute underlying contract method via eth_call.

        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method().call(tx_params.as_dict())
        return str(returned)

    def send_transaction(self, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param tx_params: transaction parameters
        """
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method().transact(tx_params.as_dict())

    def build_transaction(self, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method().build_transaction(tx_params.as_dict())

    def estimate_gas(self, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method().estimate_gas(tx_params.as_dict())

class NoncesMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the nonces method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, index_0: str):
        """Validate the inputs to the nonces method."""
        self.validator.assert_valid(
            method_name='nonces',
            parameter_name='index_0',
            argument_value=index_0,
        )
        index_0 = self.validate_and_checksum_address(index_0)
        return (index_0)

    def call(self, index_0: str, tx_params: Optional[TxParams] = None) -> int:
        """Execute underlying contract method via eth_call.

        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (index_0) = self.validate_and_normalize_inputs(index_0)
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method(index_0).call(tx_params.as_dict())
        return int(returned)

    def send_transaction(self, index_0: str, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param tx_params: transaction parameters
        """
        (index_0) = self.validate_and_normalize_inputs(index_0)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(index_0).transact(tx_params.as_dict())

    def build_transaction(self, index_0: str, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (index_0) = self.validate_and_normalize_inputs(index_0)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(index_0).build_transaction(tx_params.as_dict())

    def estimate_gas(self, index_0: str, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (index_0) = self.validate_and_normalize_inputs(index_0)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(index_0).estimate_gas(tx_params.as_dict())

class NumCheckpointsMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the numCheckpoints method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, index_0: str):
        """Validate the inputs to the numCheckpoints method."""
        self.validator.assert_valid(
            method_name='numCheckpoints',
            parameter_name='index_0',
            argument_value=index_0,
        )
        index_0 = self.validate_and_checksum_address(index_0)
        return (index_0)

    def call(self, index_0: str, tx_params: Optional[TxParams] = None) -> int:
        """Execute underlying contract method via eth_call.

        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (index_0) = self.validate_and_normalize_inputs(index_0)
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method(index_0).call(tx_params.as_dict())
        return int(returned)

    def send_transaction(self, index_0: str, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param tx_params: transaction parameters
        """
        (index_0) = self.validate_and_normalize_inputs(index_0)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(index_0).transact(tx_params.as_dict())

    def build_transaction(self, index_0: str, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (index_0) = self.validate_and_normalize_inputs(index_0)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(index_0).build_transaction(tx_params.as_dict())

    def estimate_gas(self, index_0: str, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (index_0) = self.validate_and_normalize_inputs(index_0)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(index_0).estimate_gas(tx_params.as_dict())

class OwnershipTransferredMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the ownershipTransferred method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address)
        self._underlying_method = contract_function

    def call(self, tx_params: Optional[TxParams] = None) -> bool:
        """Execute underlying contract method via eth_call.

        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method().call(tx_params.as_dict())
        return bool(returned)

    def send_transaction(self, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param tx_params: transaction parameters
        """
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method().transact(tx_params.as_dict())

    def build_transaction(self, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method().build_transaction(tx_params.as_dict())

    def estimate_gas(self, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method().estimate_gas(tx_params.as_dict())

class PermitMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the permit method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, spender: str, value: int, nonce: int, expiry: int, signature: Union[bytes, str]):
        """Validate the inputs to the permit method."""
        self.validator.assert_valid(
            method_name='permit',
            parameter_name='_spender',
            argument_value=spender,
        )
        spender = self.validate_and_checksum_address(spender)
        self.validator.assert_valid(
            method_name='permit',
            parameter_name='_value',
            argument_value=value,
        )
        # safeguard against fractional inputs
        value = int(value)
        self.validator.assert_valid(
            method_name='permit',
            parameter_name='_nonce',
            argument_value=nonce,
        )
        # safeguard against fractional inputs
        nonce = int(nonce)
        self.validator.assert_valid(
            method_name='permit',
            parameter_name='_expiry',
            argument_value=expiry,
        )
        # safeguard against fractional inputs
        expiry = int(expiry)
        self.validator.assert_valid(
            method_name='permit',
            parameter_name='_signature',
            argument_value=signature,
        )
        return (spender, value, nonce, expiry, signature)

    def call(self, spender: str, value: int, nonce: int, expiry: int, signature: Union[bytes, str], tx_params: Optional[TxParams] = None) -> None:
        """Execute underlying contract method via eth_call.

        :param _expiry: The time at which to expire the signature
        :param _nonce: The contract state required to match the signature
        :param _signature: Signature
        :param _spender: The spender being approved
        :param _value: The value being approved
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (spender, value, nonce, expiry, signature) = self.validate_and_normalize_inputs(spender, value, nonce, expiry, signature)
        tx_params = super().normalize_tx_params(tx_params)
        self._underlying_method(spender, value, nonce, expiry, signature).call(tx_params.as_dict())

    def send_transaction(self, spender: str, value: int, nonce: int, expiry: int, signature: Union[bytes, str], tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param _expiry: The time at which to expire the signature
        :param _nonce: The contract state required to match the signature
        :param _signature: Signature
        :param _spender: The spender being approved
        :param _value: The value being approved
        :param tx_params: transaction parameters
        """
        (spender, value, nonce, expiry, signature) = self.validate_and_normalize_inputs(spender, value, nonce, expiry, signature)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(spender, value, nonce, expiry, signature).transact(tx_params.as_dict())

    def build_transaction(self, spender: str, value: int, nonce: int, expiry: int, signature: Union[bytes, str], tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (spender, value, nonce, expiry, signature) = self.validate_and_normalize_inputs(spender, value, nonce, expiry, signature)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(spender, value, nonce, expiry, signature).build_transaction(tx_params.as_dict())

    def estimate_gas(self, spender: str, value: int, nonce: int, expiry: int, signature: Union[bytes, str], tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (spender, value, nonce, expiry, signature) = self.validate_and_normalize_inputs(spender, value, nonce, expiry, signature)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(spender, value, nonce, expiry, signature).estimate_gas(tx_params.as_dict())

class SymbolMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the symbol method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address)
        self._underlying_method = contract_function

    def call(self, tx_params: Optional[TxParams] = None) -> str:
        """Execute underlying contract method via eth_call.

        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method().call(tx_params.as_dict())
        return str(returned)

    def send_transaction(self, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param tx_params: transaction parameters
        """
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method().transact(tx_params.as_dict())

    def build_transaction(self, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method().build_transaction(tx_params.as_dict())

    def estimate_gas(self, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method().estimate_gas(tx_params.as_dict())

class TotalSupplyMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the totalSupply method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address)
        self._underlying_method = contract_function

    def call(self, tx_params: Optional[TxParams] = None) -> int:
        """Execute underlying contract method via eth_call.

        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method().call(tx_params.as_dict())
        return int(returned)

    def send_transaction(self, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param tx_params: transaction parameters
        """
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method().transact(tx_params.as_dict())

    def build_transaction(self, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method().build_transaction(tx_params.as_dict())

    def estimate_gas(self, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method().estimate_gas(tx_params.as_dict())

class TransferMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the transfer method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, recipient: str, amount: int):
        """Validate the inputs to the transfer method."""
        self.validator.assert_valid(
            method_name='transfer',
            parameter_name='_recipient',
            argument_value=recipient,
        )
        recipient = self.validate_and_checksum_address(recipient)
        self.validator.assert_valid(
            method_name='transfer',
            parameter_name='_amount',
            argument_value=amount,
        )
        # safeguard against fractional inputs
        amount = int(amount)
        return (recipient, amount)

    def call(self, recipient: str, amount: int, tx_params: Optional[TxParams] = None) -> bool:
        """Execute underlying contract method via eth_call.

        :param _amount: The number of tokens to transfer
        :param _recipient: The address of the destination account
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (recipient, amount) = self.validate_and_normalize_inputs(recipient, amount)
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method(recipient, amount).call(tx_params.as_dict())
        return bool(returned)

    def send_transaction(self, recipient: str, amount: int, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param _amount: The number of tokens to transfer
        :param _recipient: The address of the destination account
        :param tx_params: transaction parameters
        """
        (recipient, amount) = self.validate_and_normalize_inputs(recipient, amount)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(recipient, amount).transact(tx_params.as_dict())

    def build_transaction(self, recipient: str, amount: int, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (recipient, amount) = self.validate_and_normalize_inputs(recipient, amount)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(recipient, amount).build_transaction(tx_params.as_dict())

    def estimate_gas(self, recipient: str, amount: int, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (recipient, amount) = self.validate_and_normalize_inputs(recipient, amount)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(recipient, amount).estimate_gas(tx_params.as_dict())

class TransferFromMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the transferFrom method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, _from: str, recipient: str, amount: int):
        """Validate the inputs to the transferFrom method."""
        self.validator.assert_valid(
            method_name='transferFrom',
            parameter_name='_from',
            argument_value=_from,
        )
        _from = self.validate_and_checksum_address(_from)
        self.validator.assert_valid(
            method_name='transferFrom',
            parameter_name='_recipient',
            argument_value=recipient,
        )
        recipient = self.validate_and_checksum_address(recipient)
        self.validator.assert_valid(
            method_name='transferFrom',
            parameter_name='_amount',
            argument_value=amount,
        )
        # safeguard against fractional inputs
        amount = int(amount)
        return (_from, recipient, amount)

    def call(self, _from: str, recipient: str, amount: int, tx_params: Optional[TxParams] = None) -> bool:
        """Execute underlying contract method via eth_call.

        :param _amount: The number of tokens to transfer
        :param _from: The address of the source account
        :param _recipient: The address of the destination account
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (_from, recipient, amount) = self.validate_and_normalize_inputs(_from, recipient, amount)
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method(_from, recipient, amount).call(tx_params.as_dict())
        return bool(returned)

    def send_transaction(self, _from: str, recipient: str, amount: int, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param _amount: The number of tokens to transfer
        :param _from: The address of the source account
        :param _recipient: The address of the destination account
        :param tx_params: transaction parameters
        """
        (_from, recipient, amount) = self.validate_and_normalize_inputs(_from, recipient, amount)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(_from, recipient, amount).transact(tx_params.as_dict())

    def build_transaction(self, _from: str, recipient: str, amount: int, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (_from, recipient, amount) = self.validate_and_normalize_inputs(_from, recipient, amount)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(_from, recipient, amount).build_transaction(tx_params.as_dict())

    def estimate_gas(self, _from: str, recipient: str, amount: int, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (_from, recipient, amount) = self.validate_and_normalize_inputs(_from, recipient, amount)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(_from, recipient, amount).estimate_gas(tx_params.as_dict())

class TransferOwnershipToDerivaDexProxyMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the transferOwnershipToDerivaDEXProxy method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, deriva_dex_proxy: str):
        """Validate the inputs to the transferOwnershipToDerivaDEXProxy method."""
        self.validator.assert_valid(
            method_name='transferOwnershipToDerivaDEXProxy',
            parameter_name='_derivaDEXProxy',
            argument_value=deriva_dex_proxy,
        )
        deriva_dex_proxy = self.validate_and_checksum_address(deriva_dex_proxy)
        return (deriva_dex_proxy)

    def call(self, deriva_dex_proxy: str, tx_params: Optional[TxParams] = None) -> None:
        """Execute underlying contract method via eth_call.

        :param _derivaDEXProxy: DerivaDEX Proxy address
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (deriva_dex_proxy) = self.validate_and_normalize_inputs(deriva_dex_proxy)
        tx_params = super().normalize_tx_params(tx_params)
        self._underlying_method(deriva_dex_proxy).call(tx_params.as_dict())

    def send_transaction(self, deriva_dex_proxy: str, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param _derivaDEXProxy: DerivaDEX Proxy address
        :param tx_params: transaction parameters
        """
        (deriva_dex_proxy) = self.validate_and_normalize_inputs(deriva_dex_proxy)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(deriva_dex_proxy).transact(tx_params.as_dict())

    def build_transaction(self, deriva_dex_proxy: str, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (deriva_dex_proxy) = self.validate_and_normalize_inputs(deriva_dex_proxy)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(deriva_dex_proxy).build_transaction(tx_params.as_dict())

    def estimate_gas(self, deriva_dex_proxy: str, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (deriva_dex_proxy) = self.validate_and_normalize_inputs(deriva_dex_proxy)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(deriva_dex_proxy).estimate_gas(tx_params.as_dict())

class VersionMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the version method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address)
        self._underlying_method = contract_function

    def call(self, tx_params: Optional[TxParams] = None) -> str:
        """Execute underlying contract method via eth_call.

        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method().call(tx_params.as_dict())
        return str(returned)

    def send_transaction(self, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param tx_params: transaction parameters
        """
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method().transact(tx_params.as_dict())

    def build_transaction(self, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method().build_transaction(tx_params.as_dict())

    def estimate_gas(self, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method().estimate_gas(tx_params.as_dict())

# pylint: disable=too-many-public-methods,too-many-instance-attributes
class DDX:
    """Wrapper class for DDX Solidity contract.

    All method parameters of type `bytes`:code: should be encoded as UTF-8,
    which can be accomplished via `str.encode("utf_8")`:code:.
    """
    max_supply: MaxSupplyMethod
    """Constructor-initialized instance of
    :class:`MaxSupplyMethod`.
    """

    pre_mine_supply: PreMineSupplyMethod
    """Constructor-initialized instance of
    :class:`PreMineSupplyMethod`.
    """

    allowance: AllowanceMethod
    """Constructor-initialized instance of
    :class:`AllowanceMethod`.
    """

    approve: ApproveMethod
    """Constructor-initialized instance of
    :class:`ApproveMethod`.
    """

    balance_of: BalanceOfMethod
    """Constructor-initialized instance of
    :class:`BalanceOfMethod`.
    """

    burn: BurnMethod
    """Constructor-initialized instance of
    :class:`BurnMethod`.
    """

    burn_from: BurnFromMethod
    """Constructor-initialized instance of
    :class:`BurnFromMethod`.
    """

    checkpoints: CheckpointsMethod
    """Constructor-initialized instance of
    :class:`CheckpointsMethod`.
    """

    decimals: DecimalsMethod
    """Constructor-initialized instance of
    :class:`DecimalsMethod`.
    """

    decrease_allowance: DecreaseAllowanceMethod
    """Constructor-initialized instance of
    :class:`DecreaseAllowanceMethod`.
    """

    delegate: DelegateMethod
    """Constructor-initialized instance of
    :class:`DelegateMethod`.
    """

    delegate_by_sig: DelegateBySigMethod
    """Constructor-initialized instance of
    :class:`DelegateBySigMethod`.
    """

    delegates: DelegatesMethod
    """Constructor-initialized instance of
    :class:`DelegatesMethod`.
    """

    get_current_votes: GetCurrentVotesMethod
    """Constructor-initialized instance of
    :class:`GetCurrentVotesMethod`.
    """

    get_prior_votes: GetPriorVotesMethod
    """Constructor-initialized instance of
    :class:`GetPriorVotesMethod`.
    """

    increase_allowance: IncreaseAllowanceMethod
    """Constructor-initialized instance of
    :class:`IncreaseAllowanceMethod`.
    """

    issued_supply: IssuedSupplyMethod
    """Constructor-initialized instance of
    :class:`IssuedSupplyMethod`.
    """

    issuer: IssuerMethod
    """Constructor-initialized instance of
    :class:`IssuerMethod`.
    """

    mint: MintMethod
    """Constructor-initialized instance of
    :class:`MintMethod`.
    """

    name: NameMethod
    """Constructor-initialized instance of
    :class:`NameMethod`.
    """

    nonces: NoncesMethod
    """Constructor-initialized instance of
    :class:`NoncesMethod`.
    """

    num_checkpoints: NumCheckpointsMethod
    """Constructor-initialized instance of
    :class:`NumCheckpointsMethod`.
    """

    ownership_transferred: OwnershipTransferredMethod
    """Constructor-initialized instance of
    :class:`OwnershipTransferredMethod`.
    """

    permit: PermitMethod
    """Constructor-initialized instance of
    :class:`PermitMethod`.
    """

    symbol: SymbolMethod
    """Constructor-initialized instance of
    :class:`SymbolMethod`.
    """

    total_supply: TotalSupplyMethod
    """Constructor-initialized instance of
    :class:`TotalSupplyMethod`.
    """

    transfer: TransferMethod
    """Constructor-initialized instance of
    :class:`TransferMethod`.
    """

    transfer_from: TransferFromMethod
    """Constructor-initialized instance of
    :class:`TransferFromMethod`.
    """

    transfer_ownership_to_deriva_dex_proxy: TransferOwnershipToDerivaDexProxyMethod
    """Constructor-initialized instance of
    :class:`TransferOwnershipToDerivaDexProxyMethod`.
    """

    version: VersionMethod
    """Constructor-initialized instance of
    :class:`VersionMethod`.
    """


    def __init__(
        self,
        web3_or_provider: Union[Web3, BaseProvider],
        contract_address: str,
        validator: DDXValidator = None,
    ):
        """Get an instance of wrapper for smart contract.

        :param web3_or_provider: Either an instance of `web3.Web3`:code: or
            `web3.providers.base.BaseProvider`:code:
        :param contract_address: where the contract has been deployed
        :param validator: for validation of method inputs.
        """
        # pylint: disable=too-many-statements

        self.contract_address = contract_address

        if not validator:
            validator = DDXValidator(web3_or_provider, contract_address)

        web3 = None
        if isinstance(web3_or_provider, BaseProvider):
            web3 = Web3(web3_or_provider)
        elif isinstance(web3_or_provider, Web3):
            web3 = web3_or_provider
        else:
            raise TypeError(
                "Expected parameter 'web3_or_provider' to be an instance of either"
                + " Web3 or BaseProvider"
            )

        # if any middleware was imported, inject it
        try:
            MIDDLEWARE
        except NameError:
            pass
        else:
            try:
                for middleware in MIDDLEWARE:
                    web3.middleware_onion.inject(
                         middleware['function'], layer=middleware['layer'],
                    )
            except ValueError as value_error:
                if value_error.args == ("You can't add the same un-named instance twice",):
                    pass

        self._web3_eth = web3.eth

        functions = self._web3_eth.contract(address=to_checksum_address(contract_address), abi=DDX.abi()).functions

        self.max_supply = MaxSupplyMethod(web3_or_provider, contract_address, functions.MAX_SUPPLY)

        self.pre_mine_supply = PreMineSupplyMethod(web3_or_provider, contract_address, functions.PRE_MINE_SUPPLY)

        self.allowance = AllowanceMethod(web3_or_provider, contract_address, functions.allowance, validator)

        self.approve = ApproveMethod(web3_or_provider, contract_address, functions.approve, validator)

        self.balance_of = BalanceOfMethod(web3_or_provider, contract_address, functions.balanceOf, validator)

        self.burn = BurnMethod(web3_or_provider, contract_address, functions.burn, validator)

        self.burn_from = BurnFromMethod(web3_or_provider, contract_address, functions.burnFrom, validator)

        self.checkpoints = CheckpointsMethod(web3_or_provider, contract_address, functions.checkpoints, validator)

        self.decimals = DecimalsMethod(web3_or_provider, contract_address, functions.decimals)

        self.decrease_allowance = DecreaseAllowanceMethod(web3_or_provider, contract_address, functions.decreaseAllowance, validator)

        self.delegate = DelegateMethod(web3_or_provider, contract_address, functions.delegate, validator)

        self.delegate_by_sig = DelegateBySigMethod(web3_or_provider, contract_address, functions.delegateBySig, validator)

        self.delegates = DelegatesMethod(web3_or_provider, contract_address, functions.delegates, validator)

        self.get_current_votes = GetCurrentVotesMethod(web3_or_provider, contract_address, functions.getCurrentVotes, validator)

        self.get_prior_votes = GetPriorVotesMethod(web3_or_provider, contract_address, functions.getPriorVotes, validator)

        self.increase_allowance = IncreaseAllowanceMethod(web3_or_provider, contract_address, functions.increaseAllowance, validator)

        self.issued_supply = IssuedSupplyMethod(web3_or_provider, contract_address, functions.issuedSupply)

        self.issuer = IssuerMethod(web3_or_provider, contract_address, functions.issuer)

        self.mint = MintMethod(web3_or_provider, contract_address, functions.mint, validator)

        self.name = NameMethod(web3_or_provider, contract_address, functions.name)

        self.nonces = NoncesMethod(web3_or_provider, contract_address, functions.nonces, validator)

        self.num_checkpoints = NumCheckpointsMethod(web3_or_provider, contract_address, functions.numCheckpoints, validator)

        self.ownership_transferred = OwnershipTransferredMethod(web3_or_provider, contract_address, functions.ownershipTransferred)

        self.permit = PermitMethod(web3_or_provider, contract_address, functions.permit, validator)

        self.symbol = SymbolMethod(web3_or_provider, contract_address, functions.symbol)

        self.total_supply = TotalSupplyMethod(web3_or_provider, contract_address, functions.totalSupply)

        self.transfer = TransferMethod(web3_or_provider, contract_address, functions.transfer, validator)

        self.transfer_from = TransferFromMethod(web3_or_provider, contract_address, functions.transferFrom, validator)

        self.transfer_ownership_to_deriva_dex_proxy = TransferOwnershipToDerivaDexProxyMethod(web3_or_provider, contract_address, functions.transferOwnershipToDerivaDEXProxy, validator)

        self.version = VersionMethod(web3_or_provider, contract_address, functions.version)

    def get_approval_event(
        self, tx_hash: Union[HexBytes, bytes]
    ) -> Tuple[AttributeDict]:
        """Get log entry for Approval event.

        :param tx_hash: hash of transaction emitting Approval event
        """
        tx_receipt = self._web3_eth.get_transaction_receipt(tx_hash)
        return self._web3_eth.contract(address=to_checksum_address(self.contract_address), abi=DDX.abi()).events.Approval().process_receipt(tx_receipt)
    def get_delegate_changed_event(
        self, tx_hash: Union[HexBytes, bytes]
    ) -> Tuple[AttributeDict]:
        """Get log entry for DelegateChanged event.

        :param tx_hash: hash of transaction emitting DelegateChanged event
        """
        tx_receipt = self._web3_eth.get_transaction_receipt(tx_hash)
        return self._web3_eth.contract(address=to_checksum_address(self.contract_address), abi=DDX.abi()).events.DelegateChanged().process_receipt(tx_receipt)
    def get_delegate_votes_changed_event(
        self, tx_hash: Union[HexBytes, bytes]
    ) -> Tuple[AttributeDict]:
        """Get log entry for DelegateVotesChanged event.

        :param tx_hash: hash of transaction emitting DelegateVotesChanged event
        """
        tx_receipt = self._web3_eth.get_transaction_receipt(tx_hash)
        return self._web3_eth.contract(address=to_checksum_address(self.contract_address), abi=DDX.abi()).events.DelegateVotesChanged().process_receipt(tx_receipt)
    def get_transfer_event(
        self, tx_hash: Union[HexBytes, bytes]
    ) -> Tuple[AttributeDict]:
        """Get log entry for Transfer event.

        :param tx_hash: hash of transaction emitting Transfer event
        """
        tx_receipt = self._web3_eth.get_transaction_receipt(tx_hash)
        return self._web3_eth.contract(address=to_checksum_address(self.contract_address), abi=DDX.abi()).events.Transfer().process_receipt(tx_receipt)

    @staticmethod
    def abi():
        """Return the ABI to the underlying contract."""
        return json.loads(
            '[{"inputs":[],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"spender","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"delegator","type":"address"},{"indexed":true,"internalType":"address","name":"fromDelegate","type":"address"},{"indexed":true,"internalType":"address","name":"toDelegate","type":"address"}],"name":"DelegateChanged","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"delegate","type":"address"},{"indexed":false,"internalType":"uint96","name":"previousBalance","type":"uint96"},{"indexed":false,"internalType":"uint96","name":"newBalance","type":"uint96"}],"name":"DelegateVotesChanged","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"Transfer","type":"event"},{"inputs":[],"name":"MAX_SUPPLY","outputs":[{"internalType":"uint96","name":"","type":"uint96"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"PRE_MINE_SUPPLY","outputs":[{"internalType":"uint96","name":"","type":"uint96"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_account","type":"address"},{"internalType":"address","name":"_spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_spender","type":"address"},{"internalType":"uint256","name":"_amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_amount","type":"uint256"}],"name":"burn","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_account","type":"address"},{"internalType":"uint256","name":"_amount","type":"uint256"}],"name":"burnFrom","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"index_0","type":"address"},{"internalType":"uint256","name":"index_1","type":"uint256"}],"name":"checkpoints","outputs":[{"internalType":"uint32","name":"id","type":"uint32"},{"internalType":"uint96","name":"votes","type":"uint96"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_spender","type":"address"},{"internalType":"uint256","name":"_subtractedValue","type":"uint256"}],"name":"decreaseAllowance","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_delegatee","type":"address"}],"name":"delegate","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_delegatee","type":"address"},{"internalType":"uint256","name":"_nonce","type":"uint256"},{"internalType":"uint256","name":"_expiry","type":"uint256"},{"internalType":"bytes","name":"_signature","type":"bytes"}],"name":"delegateBySig","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"index_0","type":"address"}],"name":"delegates","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_account","type":"address"}],"name":"getCurrentVotes","outputs":[{"internalType":"uint96","name":"","type":"uint96"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_account","type":"address"},{"internalType":"uint256","name":"_blockNumber","type":"uint256"}],"name":"getPriorVotes","outputs":[{"internalType":"uint96","name":"","type":"uint96"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_spender","type":"address"},{"internalType":"uint256","name":"_addedValue","type":"uint256"}],"name":"increaseAllowance","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"issuedSupply","outputs":[{"internalType":"uint96","name":"","type":"uint96"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"issuer","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_recipient","type":"address"},{"internalType":"uint256","name":"_amount","type":"uint256"}],"name":"mint","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"index_0","type":"address"}],"name":"nonces","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"index_0","type":"address"}],"name":"numCheckpoints","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"ownershipTransferred","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_spender","type":"address"},{"internalType":"uint256","name":"_value","type":"uint256"},{"internalType":"uint256","name":"_nonce","type":"uint256"},{"internalType":"uint256","name":"_expiry","type":"uint256"},{"internalType":"bytes","name":"_signature","type":"bytes"}],"name":"permit","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint96","name":"","type":"uint96"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_recipient","type":"address"},{"internalType":"uint256","name":"_amount","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_from","type":"address"},{"internalType":"address","name":"_recipient","type":"address"},{"internalType":"uint256","name":"_amount","type":"uint256"}],"name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_derivaDEXProxy","type":"address"}],"name":"transferOwnershipToDerivaDEXProxy","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"version","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"}]'  # noqa: E501 (line-too-long)
        )

# pylint: disable=too-many-lines
