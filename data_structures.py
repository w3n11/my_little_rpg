from __future__ import annotations
from typing import Any, Type, Optional
from abc import abstractmethod, ABC
import logging
from PIL import Image
from numpy import array


OBJECT_REGISTRY: dict[str, Type["JSONObject"]] = {}
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def register_object(cls: Type["JSONObject"]):
    OBJECT_REGISTRY[cls.__name__] = cls
    return cls


class JSONObject(ABC):
    def __init__(self, json_data: dict[str, Any] | None = None) -> None:
        self._object = self.__class__.__name__
        if not json_data:
            return
        for key, value in json_data.items():
            try:
                if isinstance(value, dict):
                    object_type = value.get("_object")
                    if object_type and object_type in OBJECT_REGISTRY:
                        value = OBJECT_REGISTRY[object_type](value)
                    elif object_type:
                        logging.warning(f"Skipping unknown object type: {object_type}")
                elif isinstance(value, list):
                    value = [
                        OBJECT_REGISTRY[v["_object"]](v)
                        if isinstance(v, dict) and "_object" in v and v["_object"] in OBJECT_REGISTRY
                        else v
                        for v in value
                    ]
                setattr(self, key, value)
            except Exception as e:
                logging.error(f"[Object creation error] key={key}, error={e}")

    def to_dict(self) -> dict[str, Any]:
        """Rekurzivní převod zpět do dict (např. před uložením)."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, JSONObject):
                result[key] = value.to_dict()
            elif isinstance(value, list):
                result[key] = [
                    v.to_dict() if isinstance(v, JSONObject) else v
                    for v in value
                ]
            else:
                result[key] = value
        return result

    def __repr__(self) -> str:
        cls = self.__class__.__name__
        attrs = ', '.join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"{cls}({attrs})"

    def complete(self, required: list[str]) -> None:
        existing = set(self.__dict__.keys()) - {"_object", "_flags"}
        missing = [r for r in required if r not in existing]
        extra = [k for k in existing if k not in required]

        if missing:
            logging.error(f"Missing attributes {missing} in '{self.__class__.__name__}'.")
            raise AttributeError("Missing attribute")
        if extra:
            logging.warning(f"Extra attributes {extra} in '{self.__class__.__name__}'.")

    def have_flag(self, flag: str) -> bool:
        try:
            return flag in self.__getattribute__("_flags")
        except AttributeError:
            return False

    @abstractmethod
    def validate(self) -> None:
        """
        Shall raise ValueError if attributes don't meet specified criteria.

        This function is an @abstractmethod and shall be implemented in each
        child class.
        """
        return


@register_object
class Metadata(JSONObject):
    def __init__(self, json_data: dict[str, Any] | None = None) -> None:
        super().__init__(json_data)

    def validate(self) -> None:
        return

    def get(self, attr: str) -> Any | None:
        try:
            return self.__getattribute__(attr)
        except AttributeError:
            return None

    def set(self, attr: str, val: Any) -> None:
        self.__setattr__(attr, val)

    def rm(self, attr: str) -> None:
        try:
            self.__delattr__(attr)
        except AttributeError:
            logging.warning(f"Tried to remove non-existent attribute '{attr}'")


@register_object
class AsciiImage(JSONObject):
    data: str
    metadata: Metadata

    def __init__(self, json_data: dict[str, Any] | None = None) -> None:
        super().__init__(json_data)
        self.__charset: str = " .:-=+*#%@"
        if json_data:
            self.complete(["data", "metadata"])
            if not isinstance(self.metadata, Metadata):
                self.metadata = Metadata()
            return
        self.data = ""
        self.metadata: Metadata = Metadata()

    def charset(self, new_charset: str | None = None) -> Optional[str]:
        if new_charset:
            self.__charset = new_charset
            return
        return self.__charset

    def validate(self):
        return

    def new(self, width: int, height: int, data: str) -> bool:
        if len(data) != width * height:
            return False
        self.metadata.set("width", width)
        self.metadata.set("height", height)
        self.data = data
        return True

    def from_file(self, filepath: str, max_height: int | None = None, max_width: int | None = None):
        try:
            img = Image.open(filepath)
        except Exception as e:
            logging.error(f"{e}")
            return
        height: int
        width: int
        aspect_ratio = img.width / img.height
        if max_width is not None or max_height is not None:
            if max_height is not None and max_width is None:
                height = max_height
                width = int(aspect_ratio * max_height * 2)  # ×2 because terminal has chars taller than wider
            elif max_height is None and max_width is not None:
                width = max_width
                height = int(max_width / aspect_ratio / 2)
            elif max_height is not None and max_width is not None:
                width = max_width
                height = max_height
            img = img.resize((width, height), Image.LANCZOS)
        img = img.convert("L")
        pixels = array(img)
        ascii_image = []
        scale_factor = 255 // (len(self.__charset) - 1)  # Scale factor for pixel values

        for row in pixels:
            ascii_image_row = ''.join(self.__charset[pixel // scale_factor] for pixel in row)
            ascii_image.append(ascii_image_row)

        self.metadata.set("width", width)
        self.metadata.set("height", height)
        self.data = "".join(ascii_image)

    @property
    def width(self) -> int:
        return self.metadata.get("width") or 0

    @property
    def height(self) -> int:
        return self.metadata.get("height") or 0

    def __str__(self) -> str:
        w = self.width
        h = self.height
        if not isinstance(w, int) or not isinstance(h, int) or w <= 0 or h <= 0:
            return "<Invalid AsciiImage>"
        return "\n".join([self.data[i * w : (i + 1) * w] for i in range(h)])


@register_object
class Race(JSONObject):
    def __init__(self, json_data: dict[str, Any] | None = None) -> None:
        super().__init__(json_data)
        if json_data:
            self.complete(["name"])
            self.name: str


@register_object
class Creature(JSONObject):
    def __init__(self, json_data: dict[str, Any] | None = None) -> None:
        super().__init__(json_data)
        if json_data:
            self.complete(["metadata", "stats", "traits", "actions", "inventory"])
            self.metadata: Metadata
            self.stats: dict[str, Any]
            self.validate()
            return
        self.metadata = Metadata()
        self.ability_score = AbilityScore()

    def new(
        self,
        name: str | None = None,
        race: str | None = None
    ):
        self.metadata.set()


def main():
    pass


if __name__ == "__main__":
    main()
