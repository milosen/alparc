import json
from os import PathLike
from typing import TypeVar, List, Dict, Any, Union

from pydantic import BaseModel

from arpac.types.base_types import Register, Element, RegisterType
from arpac.types.syllable import Syllable, SyllableType


StreamType = TypeVar("StreamType", bound="Stream")


class Stream(Element, BaseModel):
    id: str
    syllables: List[SyllableType]
    info: Dict[str, Any]

    def get_elements(self):
        return self.syllables
        
    def __str__(self):
        return "_".join([syll.id for syll in self.syllables[:5]]) + "..." + "_".join([syll.id for syll in self.syllables[-5:]])
    
    def save(self, path: Union[str, PathLike] = None):
        if path is None:
            path = f"stream.json"

        if isinstance(path, str) and not path.endswith(".json"):
            path = path + ".json"

        with open(path, "w", encoding='utf-8') as file:
            json.dump(self, file,
                      default=lambda o: o.model_dump(), sort_keys=False, ensure_ascii=False)
