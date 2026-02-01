import dataclasses

import typing_extensions as typing

from ..data_types import Element
from .property import Property

if typing.TYPE_CHECKING:
    from ..common import Feature


@dataclasses.dataclass
class UnobservableProperty(Property):
    """A property describes certain aspects of a SiLA server that do not require an action on the SiLA server."""

    observable: bool = dataclasses.field(init=False, repr=False, default=False)

    @typing.override
    def add_to_feature(self, feature: "Feature") -> typing.Self:
        super().add_to_feature(feature)

        feature.context.protobuf.register_message(
            name=f"Get_{self.identifier}_Responses",
            message={
                self.identifier: Element(
                    identifier=self.identifier,
                    display_name=self.display_name,
                    description=self.description,
                    data_type=self.data_type,
                )
            },
            package=feature.fully_qualified_identifier.rpc_package,
        )

        return self
