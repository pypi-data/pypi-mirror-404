from typing import Literal


def construct_includes_query_parameter(
    includes: list[str] | None,
) -> dict[Literal["includes"], str]:
    if includes is None:
        return {}

    return {
        "includes": ",".join(includes),
    }
