import os

# from ddx._rust import common
from ddx._rust.common import reinit_operator_context

# FIXME: might need to change these environment variables to `DDX_CONTRACT_DEPLOYMENT` for better convention


def load_mainnet():
    os.environ["CONTRACT_DEPLOYMENT"] = "derivadex"
    # common.reinit_operator_context()
    reinit_operator_context()


def load_testnet():
    os.environ["CONTRACT_DEPLOYMENT"] = "testnet"
    reinit_operator_context()
