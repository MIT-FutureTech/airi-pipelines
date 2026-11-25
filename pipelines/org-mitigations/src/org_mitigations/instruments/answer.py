from pydantic import BaseModel

from org_mitigations.instrument_taxonomy import Modality


class Answer(BaseModel):
    lever: str
    modality: str
    instrument_code: str
    reasoning: str


def invalid_code_reason(answer: Answer, modalities: list[Modality]) -> str | None:
    modality_codes = {
        instrument.code: modality.code
        for modality in modalities
        for instrument in modality.instruments
    }
    if answer.instrument_code not in modality_codes:
        return f"Instrument code {answer.instrument_code!r} isn't in the taxonomy"
    if answer.modality != modality_codes[answer.instrument_code]:
        return (
            f"Modality {answer.modality!r} doesn't contain"
            + f" instrument code {answer.instrument_code!r}"
        )
    return None
