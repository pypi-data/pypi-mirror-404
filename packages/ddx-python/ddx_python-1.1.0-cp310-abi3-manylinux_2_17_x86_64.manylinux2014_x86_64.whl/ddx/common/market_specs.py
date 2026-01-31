import logging

import sexpdata
from ddx._rust.common.specs import (
    ProductSpecs,
    QuarterlyExpiryFuture,
    SingleNamePerpetual,
    SpecsKind,
)
from ddx._rust.common.state.keys import SpecsKey

logger = logging.getLogger(__name__)


class MarketSpecs:
    """
    Defines the MarketSpecs of all symbols

    Attributes:
        market_specs: SpecsKey <> ProductSpecs
    """

    def __init__(self, genesis_params: dict):
        self.market_specs = {}
        for spec_key, spec in genesis_params["specs"].items():
            if spec_key.startswith("SINGLENAMEPERP"):
                spec_kind = SpecsKind.SingleNamePerpetual
                spec_type = SingleNamePerpetual
            elif spec_key.startswith("INDEXFUNDPERP"):
                # TODO: implement this
                # spec_kind = SpecsKind.IndexFundPerpetual
                # spec_type = IndexFundPerpetual
                raise NotImplementedError("IndexFundPerpetual is not implemented")
            elif spec_key.startswith("QUARTERLYFUTURE"):
                spec_kind = SpecsKind.QuarterlyExpiryFuture
                spec_type = QuarterlyExpiryFuture
            else:
                continue
            spec = sexpdata.loads(spec)
            inner = spec_type(
                **{
                    str(k)[1:].replace("-", "_"): v
                    for k, v in zip(spec[1::2], spec[2::2])
                }
            )
            if isinstance(inner, SingleNamePerpetual):
                product_specs = ProductSpecs.SingleNamePerpetual(inner)
            elif isinstance(inner, QuarterlyExpiryFuture):
                product_specs = ProductSpecs.QuarterlyExpiryFuture(inner)
            else:
                raise NotImplementedError("Unknown product specs type")
            self.market_specs[SpecsKey(spec_kind, spec_key.split("-")[1])] = (
                product_specs
            )
        logger.info(f"Loaded market specs: {self.market_specs}")

    def __getitem__(self, specs_key: SpecsKey) -> ProductSpecs:
        return self.market_specs[specs_key]

    def keys(self):
        return self.market_specs.keys()

    def items(self):
        return self.market_specs.items()
