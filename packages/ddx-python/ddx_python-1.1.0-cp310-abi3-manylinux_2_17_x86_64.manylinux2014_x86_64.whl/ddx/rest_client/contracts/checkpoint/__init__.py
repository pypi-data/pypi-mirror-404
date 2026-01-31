"""Generated wrapper for Checkpoint Solidity contract."""

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
# constructor for Checkpoint below.
try:
    # both mypy and pylint complain about what we're doing here, but this
    # works just fine, so their messages have been disabled here.
    from . import (  # type: ignore # pylint: disable=import-self
        CheckpointValidator,
    )
except ImportError:

    class CheckpointValidator(  # type: ignore
        Validator
    ):
        """No-op input validator."""


try:
    from .middleware import MIDDLEWARE  # type: ignore
except ImportError:
    pass


class CheckpointDefsCheckpointData(TypedDict):
    """Python representation of a tuple or struct.

    Solidity compiler output does not include the names of structs that appear
    in method definitions.  A tuple found in an ABI may have been written in
    Solidity as a literal, anonymous tuple, or it may have been written as a
    named `struct`:code:, but there is no way to tell from the compiler
    output.  This class represents a tuple that appeared in a method
    definition.  Its name is derived from a hash of that tuple's field names,
    and every method whose ABI refers to a tuple with that same list of field
    names will have a generated wrapper method that refers to this class.

    Any members of type `bytes`:code: should be encoded as UTF-8, which can be
    accomplished via `str.encode("utf_8")`:code:
    """

    blockNumber: int

    blockHash: Union[bytes, str]

    stateRoot: Union[bytes, str]

    transactionRoot: Union[bytes, str]


class CheckpointDefsCheckpointSubmission(TypedDict):
    """Python representation of a tuple or struct.

    Solidity compiler output does not include the names of structs that appear
    in method definitions.  A tuple found in an ABI may have been written in
    Solidity as a literal, anonymous tuple, or it may have been written as a
    named `struct`:code:, but there is no way to tell from the compiler
    output.  This class represents a tuple that appeared in a method
    definition.  Its name is derived from a hash of that tuple's field names,
    and every method whose ABI refers to a tuple with that same list of field
    names will have a generated wrapper method that refers to this class.

    Any members of type `bytes`:code: should be encoded as UTF-8, which can be
    accomplished via `str.encode("utf_8")`:code:
    """

    checkpointData: CheckpointDefsCheckpointData

    signatures: List[Union[bytes, str]]


class CheckpointMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the checkpoint method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, majority_checkpoint_submission: CheckpointDefsCheckpointSubmission, minority_checkpoint_submissions: List[CheckpointDefsCheckpointSubmission], epoch_id: int):
        """Validate the inputs to the checkpoint method."""
        self.validator.assert_valid(
            method_name='checkpoint',
            parameter_name='_majorityCheckpointSubmission',
            argument_value=majority_checkpoint_submission,
        )
        self.validator.assert_valid(
            method_name='checkpoint',
            parameter_name='_minorityCheckpointSubmissions',
            argument_value=minority_checkpoint_submissions,
        )
        self.validator.assert_valid(
            method_name='checkpoint',
            parameter_name='_epochId',
            argument_value=epoch_id,
        )
        return (majority_checkpoint_submission, minority_checkpoint_submissions, epoch_id)

    def call(self, majority_checkpoint_submission: CheckpointDefsCheckpointSubmission, minority_checkpoint_submissions: List[CheckpointDefsCheckpointSubmission], epoch_id: int, tx_params: Optional[TxParams] = None) -> None:
        """Execute underlying contract method via eth_call.

        :param _epochId: The epoch id of the checkpoint being submitted. This
            id        must monotonically increase, but we permit skips in the
            id.
        :param _majorityCheckpointSubmission: Structured data that contains a
                 state root, a transaction root, block data, and signatures of
                  signers that have attested to the checkpoint.
        :param _minorityCheckpointSubmissions: Same as the valid checkpoints
            but        the hashes don't match that of the majority checkpoint.
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (majority_checkpoint_submission, minority_checkpoint_submissions, epoch_id) = self.validate_and_normalize_inputs(majority_checkpoint_submission, minority_checkpoint_submissions, epoch_id)
        tx_params = super().normalize_tx_params(tx_params)
        self._underlying_method(majority_checkpoint_submission, minority_checkpoint_submissions, epoch_id).call(tx_params.as_dict())

    def send_transaction(self, majority_checkpoint_submission: CheckpointDefsCheckpointSubmission, minority_checkpoint_submissions: List[CheckpointDefsCheckpointSubmission], epoch_id: int, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param _epochId: The epoch id of the checkpoint being submitted. This
            id        must monotonically increase, but we permit skips in the
            id.
        :param _majorityCheckpointSubmission: Structured data that contains a
                 state root, a transaction root, block data, and signatures of
                  signers that have attested to the checkpoint.
        :param _minorityCheckpointSubmissions: Same as the valid checkpoints
            but        the hashes don't match that of the majority checkpoint.
        :param tx_params: transaction parameters
        """
        (majority_checkpoint_submission, minority_checkpoint_submissions, epoch_id) = self.validate_and_normalize_inputs(majority_checkpoint_submission, minority_checkpoint_submissions, epoch_id)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(majority_checkpoint_submission, minority_checkpoint_submissions, epoch_id).transact(tx_params.as_dict())

    def build_transaction(self, majority_checkpoint_submission: CheckpointDefsCheckpointSubmission, minority_checkpoint_submissions: List[CheckpointDefsCheckpointSubmission], epoch_id: int, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (majority_checkpoint_submission, minority_checkpoint_submissions, epoch_id) = self.validate_and_normalize_inputs(majority_checkpoint_submission, minority_checkpoint_submissions, epoch_id)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(majority_checkpoint_submission, minority_checkpoint_submissions, epoch_id).build_transaction(tx_params.as_dict())

    def estimate_gas(self, majority_checkpoint_submission: CheckpointDefsCheckpointSubmission, minority_checkpoint_submissions: List[CheckpointDefsCheckpointSubmission], epoch_id: int, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (majority_checkpoint_submission, minority_checkpoint_submissions, epoch_id) = self.validate_and_normalize_inputs(majority_checkpoint_submission, minority_checkpoint_submissions, epoch_id)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(majority_checkpoint_submission, minority_checkpoint_submissions, epoch_id).estimate_gas(tx_params.as_dict())

class GetCheckpointInfoMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the getCheckpointInfo method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address)
        self._underlying_method = contract_function

    def call(self, tx_params: Optional[TxParams] = None) -> Tuple[int, int]:
        """Execute underlying contract method via eth_call.

        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method().call(tx_params.as_dict())
        return (returned[0],returned[1],)

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

class GetLatestCheckpointMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the getLatestCheckpoint method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address)
        self._underlying_method = contract_function

    def call(self, tx_params: Optional[TxParams] = None) -> Tuple[int, Union[bytes, str], Union[bytes, str], int]:
        """Execute underlying contract method via eth_call.

        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method().call(tx_params.as_dict())
        return (returned[0],returned[1],returned[2],returned[3],)

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

class InitializeMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the initialize method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, consensus_threshold: int, quorum: int):
        """Validate the inputs to the initialize method."""
        self.validator.assert_valid(
            method_name='initialize',
            parameter_name='_consensusThreshold',
            argument_value=consensus_threshold,
        )
        self.validator.assert_valid(
            method_name='initialize',
            parameter_name='_quorum',
            argument_value=quorum,
        )
        return (consensus_threshold, quorum)

    def call(self, consensus_threshold: int, quorum: int, tx_params: Optional[TxParams] = None) -> None:
        """Execute underlying contract method via eth_call.

        This function is intended to be the initialization target of the
        diamond cut function. This function is not included in the selectors
        being added to the diamond, meaning it cannot be called again.

        :param _consensusThreshold: The initial consensus threshold.
        :param _quorum: The quorum that will be enforced as a consensus rule.
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (consensus_threshold, quorum) = self.validate_and_normalize_inputs(consensus_threshold, quorum)
        tx_params = super().normalize_tx_params(tx_params)
        self._underlying_method(consensus_threshold, quorum).call(tx_params.as_dict())

    def send_transaction(self, consensus_threshold: int, quorum: int, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        This function is intended to be the initialization target of the
        diamond cut function. This function is not included in the selectors
        being added to the diamond, meaning it cannot be called again.

        :param _consensusThreshold: The initial consensus threshold.
        :param _quorum: The quorum that will be enforced as a consensus rule.
        :param tx_params: transaction parameters
        """
        (consensus_threshold, quorum) = self.validate_and_normalize_inputs(consensus_threshold, quorum)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(consensus_threshold, quorum).transact(tx_params.as_dict())

    def build_transaction(self, consensus_threshold: int, quorum: int, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (consensus_threshold, quorum) = self.validate_and_normalize_inputs(consensus_threshold, quorum)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(consensus_threshold, quorum).build_transaction(tx_params.as_dict())

    def estimate_gas(self, consensus_threshold: int, quorum: int, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (consensus_threshold, quorum) = self.validate_and_normalize_inputs(consensus_threshold, quorum)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(consensus_threshold, quorum).estimate_gas(tx_params.as_dict())

class SetConsensusThresholdMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the setConsensusThreshold method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, consensus_threshold: int):
        """Validate the inputs to the setConsensusThreshold method."""
        self.validator.assert_valid(
            method_name='setConsensusThreshold',
            parameter_name='_consensusThreshold',
            argument_value=consensus_threshold,
        )
        return (consensus_threshold)

    def call(self, consensus_threshold: int, tx_params: Optional[TxParams] = None) -> None:
        """Execute underlying contract method via eth_call.

        :param _consensusThreshold: A number between 50 and 100 that represents
                   the percentage of valid signers that have to agree for a
               submission to be considered valid.
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (consensus_threshold) = self.validate_and_normalize_inputs(consensus_threshold)
        tx_params = super().normalize_tx_params(tx_params)
        self._underlying_method(consensus_threshold).call(tx_params.as_dict())

    def send_transaction(self, consensus_threshold: int, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param _consensusThreshold: A number between 50 and 100 that represents
                   the percentage of valid signers that have to agree for a
               submission to be considered valid.
        :param tx_params: transaction parameters
        """
        (consensus_threshold) = self.validate_and_normalize_inputs(consensus_threshold)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(consensus_threshold).transact(tx_params.as_dict())

    def build_transaction(self, consensus_threshold: int, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (consensus_threshold) = self.validate_and_normalize_inputs(consensus_threshold)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(consensus_threshold).build_transaction(tx_params.as_dict())

    def estimate_gas(self, consensus_threshold: int, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (consensus_threshold) = self.validate_and_normalize_inputs(consensus_threshold)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(consensus_threshold).estimate_gas(tx_params.as_dict())

class SetQuorumMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the setQuorum method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, quorum: int):
        """Validate the inputs to the setQuorum method."""
        self.validator.assert_valid(
            method_name='setQuorum',
            parameter_name='_quorum',
            argument_value=quorum,
        )
        return (quorum)

    def call(self, quorum: int, tx_params: Optional[TxParams] = None) -> None:
        """Execute underlying contract method via eth_call.

        :param _quorum: The quorum value that will be enforced for consensus.
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (quorum) = self.validate_and_normalize_inputs(quorum)
        tx_params = super().normalize_tx_params(tx_params)
        self._underlying_method(quorum).call(tx_params.as_dict())

    def send_transaction(self, quorum: int, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param _quorum: The quorum value that will be enforced for consensus.
        :param tx_params: transaction parameters
        """
        (quorum) = self.validate_and_normalize_inputs(quorum)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(quorum).transact(tx_params.as_dict())

    def build_transaction(self, quorum: int, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (quorum) = self.validate_and_normalize_inputs(quorum)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(quorum).build_transaction(tx_params.as_dict())

    def estimate_gas(self, quorum: int, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (quorum) = self.validate_and_normalize_inputs(quorum)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(quorum).estimate_gas(tx_params.as_dict())

# pylint: disable=too-many-public-methods,too-many-instance-attributes
class Checkpoint:
    """Wrapper class for Checkpoint Solidity contract."""
    checkpoint: CheckpointMethod
    """Constructor-initialized instance of
    :class:`CheckpointMethod`.
    """

    get_checkpoint_info: GetCheckpointInfoMethod
    """Constructor-initialized instance of
    :class:`GetCheckpointInfoMethod`.
    """

    get_latest_checkpoint: GetLatestCheckpointMethod
    """Constructor-initialized instance of
    :class:`GetLatestCheckpointMethod`.
    """

    initialize: InitializeMethod
    """Constructor-initialized instance of
    :class:`InitializeMethod`.
    """

    set_consensus_threshold: SetConsensusThresholdMethod
    """Constructor-initialized instance of
    :class:`SetConsensusThresholdMethod`.
    """

    set_quorum: SetQuorumMethod
    """Constructor-initialized instance of
    :class:`SetQuorumMethod`.
    """


    def __init__(
        self,
        web3_or_provider: Union[Web3, BaseProvider],
        contract_address: str,
        validator: CheckpointValidator = None,
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
            validator = CheckpointValidator(web3_or_provider, contract_address)

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

        functions = self._web3_eth.contract(address=to_checksum_address(contract_address), abi=Checkpoint.abi()).functions

        self.checkpoint = CheckpointMethod(web3_or_provider, contract_address, functions.checkpoint, validator)

        self.get_checkpoint_info = GetCheckpointInfoMethod(web3_or_provider, contract_address, functions.getCheckpointInfo)

        self.get_latest_checkpoint = GetLatestCheckpointMethod(web3_or_provider, contract_address, functions.getLatestCheckpoint)

        self.initialize = InitializeMethod(web3_or_provider, contract_address, functions.initialize, validator)

        self.set_consensus_threshold = SetConsensusThresholdMethod(web3_or_provider, contract_address, functions.setConsensusThreshold, validator)

        self.set_quorum = SetQuorumMethod(web3_or_provider, contract_address, functions.setQuorum, validator)

    def get_checkpoint_initialized_event(
        self, tx_hash: Union[HexBytes, bytes]
    ) -> Tuple[AttributeDict]:
        """Get log entry for CheckpointInitialized event.

        :param tx_hash: hash of transaction emitting CheckpointInitialized
            event
        """
        tx_receipt = self._web3_eth.get_transaction_receipt(tx_hash)
        return self._web3_eth.contract(address=to_checksum_address(self.contract_address), abi=Checkpoint.abi()).events.CheckpointInitialized().process_receipt(tx_receipt)
    def get_checkpointed_event(
        self, tx_hash: Union[HexBytes, bytes]
    ) -> Tuple[AttributeDict]:
        """Get log entry for Checkpointed event.

        :param tx_hash: hash of transaction emitting Checkpointed event
        """
        tx_receipt = self._web3_eth.get_transaction_receipt(tx_hash)
        return self._web3_eth.contract(address=to_checksum_address(self.contract_address), abi=Checkpoint.abi()).events.Checkpointed().process_receipt(tx_receipt)
    def get_consensus_threshold_set_event(
        self, tx_hash: Union[HexBytes, bytes]
    ) -> Tuple[AttributeDict]:
        """Get log entry for ConsensusThresholdSet event.

        :param tx_hash: hash of transaction emitting ConsensusThresholdSet
            event
        """
        tx_receipt = self._web3_eth.get_transaction_receipt(tx_hash)
        return self._web3_eth.contract(address=to_checksum_address(self.contract_address), abi=Checkpoint.abi()).events.ConsensusThresholdSet().process_receipt(tx_receipt)
    def get_custodians_jailed_event(
        self, tx_hash: Union[HexBytes, bytes]
    ) -> Tuple[AttributeDict]:
        """Get log entry for CustodiansJailed event.

        :param tx_hash: hash of transaction emitting CustodiansJailed event
        """
        tx_receipt = self._web3_eth.get_transaction_receipt(tx_hash)
        return self._web3_eth.contract(address=to_checksum_address(self.contract_address), abi=Checkpoint.abi()).events.CustodiansJailed().process_receipt(tx_receipt)
    def get_quorum_set_event(
        self, tx_hash: Union[HexBytes, bytes]
    ) -> Tuple[AttributeDict]:
        """Get log entry for QuorumSet event.

        :param tx_hash: hash of transaction emitting QuorumSet event
        """
        tx_receipt = self._web3_eth.get_transaction_receipt(tx_hash)
        return self._web3_eth.contract(address=to_checksum_address(self.contract_address), abi=Checkpoint.abi()).events.QuorumSet().process_receipt(tx_receipt)

    @staticmethod
    def abi():
        """Return the ABI to the underlying contract."""
        return json.loads(
            '[{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint128","name":"consensusThreshold","type":"uint128"},{"indexed":true,"internalType":"uint128","name":"quorum","type":"uint128"}],"name":"CheckpointInitialized","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"bytes32","name":"stateRoot","type":"bytes32"},{"indexed":true,"internalType":"bytes32","name":"transactionRoot","type":"bytes32"},{"indexed":true,"internalType":"uint128","name":"epochId","type":"uint128"},{"indexed":false,"internalType":"address[]","name":"custodians","type":"address[]"},{"indexed":false,"internalType":"uint128[]","name":"bonds","type":"uint128[]"},{"indexed":false,"internalType":"address","name":"submitter","type":"address"}],"name":"Checkpointed","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint128","name":"consensusThreshold","type":"uint128"}],"name":"ConsensusThresholdSet","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address[]","name":"custodians","type":"address[]"}],"name":"CustodiansJailed","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint128","name":"quorum","type":"uint128"}],"name":"QuorumSet","type":"event"},{"inputs":[{"components":[{"components":[{"internalType":"uint128","name":"blockNumber","type":"uint128"},{"internalType":"bytes32","name":"blockHash","type":"bytes32"},{"internalType":"bytes32","name":"stateRoot","type":"bytes32"},{"internalType":"bytes32","name":"transactionRoot","type":"bytes32"}],"internalType":"struct CheckpointDefs.CheckpointData","name":"checkpointData","type":"tuple"},{"internalType":"bytes[]","name":"signatures","type":"bytes[]"}],"internalType":"struct CheckpointDefs.CheckpointSubmission","name":"_majorityCheckpointSubmission","type":"tuple"},{"components":[{"components":[{"internalType":"uint128","name":"blockNumber","type":"uint128"},{"internalType":"bytes32","name":"blockHash","type":"bytes32"},{"internalType":"bytes32","name":"stateRoot","type":"bytes32"},{"internalType":"bytes32","name":"transactionRoot","type":"bytes32"}],"internalType":"struct CheckpointDefs.CheckpointData","name":"checkpointData","type":"tuple"},{"internalType":"bytes[]","name":"signatures","type":"bytes[]"}],"internalType":"struct CheckpointDefs.CheckpointSubmission[]","name":"_minorityCheckpointSubmissions","type":"tuple[]"},{"internalType":"uint128","name":"_epochId","type":"uint128"}],"name":"checkpoint","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"getCheckpointInfo","outputs":[{"internalType":"uint128","name":"","type":"uint128"},{"internalType":"uint128","name":"","type":"uint128"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getLatestCheckpoint","outputs":[{"internalType":"uint128","name":"","type":"uint128"},{"internalType":"bytes32","name":"","type":"bytes32"},{"internalType":"bytes32","name":"","type":"bytes32"},{"internalType":"uint128","name":"","type":"uint128"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint128","name":"_consensusThreshold","type":"uint128"},{"internalType":"uint128","name":"_quorum","type":"uint128"}],"name":"initialize","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint128","name":"_consensusThreshold","type":"uint128"}],"name":"setConsensusThreshold","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint128","name":"_quorum","type":"uint128"}],"name":"setQuorum","outputs":[],"stateMutability":"nonpayable","type":"function"}]'  # noqa: E501 (line-too-long)
        )

# pylint: disable=too-many-lines
