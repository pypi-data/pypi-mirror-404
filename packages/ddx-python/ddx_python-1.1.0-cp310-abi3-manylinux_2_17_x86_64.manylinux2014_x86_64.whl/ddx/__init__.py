"""
ddx/__init__.py

Package initializer for the mixed Rust/Python ddx library.

Responsibilities:
  * Dynamically load the compiled Rust extension module (`ddx._rust`).
  * In development/editable mode (when APP_SHARE is set), prepend the
    on-disk wheel directory so that `import ddx._rust` resolves locally.
  * Re-export all public symbols from the Rust extension module,
    plus Python helpers `reinit_operator_context` and `load_testnet`.
  * Configure the application data directory via APP_CONFIG and
    enforce CONTRACT_DEPLOYMENT when a custom config is used.
  * Define constants like `DDX_APPLICATION_ID`.
"""

import os
import importlib
from importlib.resources import files

# Step 1: Load the installed ddx package (the Rust wheel).
_pkg = importlib.import_module("ddx")

# Step 2: If APP_SHARE is set (dev mode), include the local wheel so ddx._rust resolves
if share := os.environ.get("APP_SHARE"):
    wheel_dir = os.path.join(share, "ddx", "wheels", "ddx")
    _pkg.__path__.append(wheel_dir)

# Step 3: Application configuration
from .config import *

if "APP_CONFIG" not in os.environ:
    default_cfg = files("ddx") / "app_config"
    os.environ["APP_CONFIG"] = str(default_cfg)

    # To use testnet or other environments in the default `app_config` set that variable upfront.
    # Otherwise, it defaults to "derivadex" (mainnet).
    if not os.environ.get("CONTRACT_DEPLOYMENT"):
        os.environ["CONTRACT_DEPLOYMENT"] = "derivadex"

    reinit_operator_context()
else:
    # HACK: This happens during the docker build state when validating the install.
    if not os.environ.get("CONTRACT_DEPLOYMENT"):
        os.environ["CONTRACT_DEPLOYMENT"] = "snapshot"

# Step 4: Import the Rust extension and re-export its public API
# This internally reads APP_CONFIG nd CONTRACT_DEPLOYMENT so it must be done after step 3.
import ddx._rust as _rust  # noqa: F401,F403

__doc__ = _rust.__doc__  # mirror the Rust module's docstring
__all__ = list(getattr(_rust, "__all__", []))
__all__.extend(["load_mainnet", "load_testnet"])

# Step 5: Constants
from eth_abi.utils.padding import zpad32_right

DDX_APPLICATION_ID = zpad32_right(b"exchange-operator")
