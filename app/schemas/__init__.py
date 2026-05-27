from pydantic import BaseModel, ConfigDict

from .auth import MemberResponse, LoginBase, SignUpBase, TokenResponse


def convert_to_camel(word: str) -> str:
    parts = word.split("_")
    if len(parts) == 1:
        return word
    return parts[0] + "".join(p.title() for p in parts[1:])


class BaseSerializer(BaseModel):
    model_config = ConfigDict(
        alias_generator=convert_to_camel,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        use_enum_values=True,
        from_attributes=True,
        extra="forbid",
    )
