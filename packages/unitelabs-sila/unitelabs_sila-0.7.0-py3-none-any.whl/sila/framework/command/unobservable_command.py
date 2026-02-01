import dataclasses

import typing_extensions as typing

from .command import Command

if typing.TYPE_CHECKING:
    from ..common import Feature


@dataclasses.dataclass
class UnobservableCommand(Command):
    """Any command for which observing the progress of execution is not possible or does not make sense."""

    observable: bool = dataclasses.field(init=False, repr=False, default=False)

    @typing.override
    def add_to_feature(self, feature: "Feature") -> typing.Self:
        super().add_to_feature(feature)

        feature.context.protobuf.register_message(
            name=self.identifier + "_Parameters",
            message=self.parameters,
            package=feature.fully_qualified_identifier.rpc_package,
        )
        feature.context.protobuf.register_message(
            name=self.identifier + "_Responses",
            message=self.responses,
            package=feature.fully_qualified_identifier.rpc_package,
        )

        return self
