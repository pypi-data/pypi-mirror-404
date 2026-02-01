import dataclasses

import typing_extensions as typing

from .command import Command

if typing.TYPE_CHECKING:
    from ..common import Feature
    from ..data_types import Element


@dataclasses.dataclass
class ObservableCommand(Command):
    """Any command for which observing the progress of execution is possible or does make sense."""

    observable: bool = dataclasses.field(init=False, repr=False, default=True)

    intermediate_responses: dict[str, "Element"] = dataclasses.field(default_factory=dict)
    """An intermediate response of the command execution."""

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
        if self.intermediate_responses:
            feature.context.protobuf.register_message(
                name=self.identifier + "_IntermediateResponses",
                message=self.intermediate_responses,
                package=feature.fully_qualified_identifier.rpc_package,
            )

        return self
