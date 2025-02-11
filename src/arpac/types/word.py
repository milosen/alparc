from typing import TypeVar, List, Dict, Any

from pydantic import BaseModel

from arpac.types.base_types import Register, Element, RegisterType
from arpac.types.syllable import Syllable, SyllableType


WordType = TypeVar("WordType", bound="Word")


class Word(Element, BaseModel):
    id: str
    syllables: List[SyllableType]
    info: Dict[str, Any]

    def get_elements(self):
        return self.syllables
