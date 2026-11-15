from pathlib import Path
from string import Template

from pydantic import BaseModel

_SYSTEM_MARKER = "<!-- SYSTEM -->"
_USER_MARKER = "<!-- USER -->"
_SYSTEM_PLACEHOLDERS = {"taxonomy"}
_USER_PLACEHOLDERS = {"company", "context", "code", "match_id"}


class Prompt(BaseModel):
    system: str
    user_template: str

    def render_user(
        self, *, company: str, context: str, code: str, match_id: str
    ) -> str:
        return Template(self.user_template).substitute(
            company=company, context=context, code=code, match_id=match_id
        )


def load_prompt(path: Path, *, taxonomy: str) -> Prompt:
    system, user = _split_sections(path.read_text(encoding="utf-8"))
    _check_placeholders("system", system, _SYSTEM_PLACEHOLDERS)
    _check_placeholders("user", user, _USER_PLACEHOLDERS)
    return Prompt(
        system=Template(system).substitute(taxonomy=taxonomy),
        user_template=user,
    )


def _split_sections(text: str) -> tuple[str, str]:
    if text.count(_SYSTEM_MARKER) != 1 or text.count(_USER_MARKER) != 1:
        raise ValueError(f"A prompt needs one {_SYSTEM_MARKER} and one {_USER_MARKER}")
    preamble, rest = text.split(_SYSTEM_MARKER)
    if preamble.strip():
        raise ValueError(f"A prompt must start with {_SYSTEM_MARKER}")
    system, user = rest.split(_USER_MARKER)
    return system.strip(), user.strip()


def _check_placeholders(section: str, text: str, expected: set[str]) -> None:
    found = set(Template(text).get_identifiers())
    if found != expected:
        raise ValueError(
            f"The {section} section has placeholders {sorted(found)},"
            + f" not {sorted(expected)}"
        )
