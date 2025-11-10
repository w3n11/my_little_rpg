from data_structures import JSONObject, Metadata, register_object
from typing import Any, Optional


class AbilityScoreRV:
    def __init__(self) -> None:
        self._base: int = 0
        self._extra: int = 0

    def combined(self) -> int:
        return self._base + self._extra

    def bonus_per(self, val: int) -> int:
        return (self._base - 10 + self._extra) // val

    def __str__(self) -> str:
        cls = self.__class__.__name__
        attrs = ', '.join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"{cls}({attrs})"


@register_object
class AbilityScore(JSONObject):
    def __init__(self, json_data: dict[str, Any] | None = None) -> None:
        super().__init__(json_data)
        if json_data:
            attr_list: list[str] = [
                "str",  # physical power
                "dex",  # agility
                "con",  # endurance
                "int",  # reasoning, memory
                "wis",  # perception, insight
                "chr",  # force of personality
                "metadata"
            ]
            if self.have_flag("extra_ability_score"):
                attr_list.append("extra")
            self.complete(attr_list)
            self.validate()
            return
        self.str: int
        self.dex: int
        self.con: int
        self.int: int
        self.wis: int
        self.chr: int
        self.metadata: Metadata
        self.extra: AbilityScore

    def validate(self) -> None:
        def is_valid(val: Any) -> bool:
            return (isinstance(val, int) and
                    val <= self.metadata.get("max") and
                    val >= self.metadata.get("min"))

        if isinstance(self.metadata, Metadata):
            if not (is_valid(self.str) and is_valid(self.dex) and is_valid(self.con) and 
                    is_valid(self.int) and is_valid(self.wis) and is_valid(self.chr)):
                raise ValueError("Invalid AbilityScore parameters.")
        else:
            raise ValueError(f"Expected class 'Metadata' in {self.__class__.__name__}")
        return

    def modify(self, ability: str, modifier: int) -> bool:
        try:
            if not isinstance(ability, str) or len(ability) != 3:
                return False
            ability_score = self.__getattribute__(ability)
            ability_score += modifier
            max_val = self.metadata.get("max")
            min_val = self.metadata.get("min")
            if ability_score > max_val:
                ability_score = max_val
            elif ability_score < min_val:
                ability_score = min_val
            self.__setattr__(ability, ability_score)
            return True
        except AttributeError:
            return False

    def get(self, ability: str) -> Optional[AbilityScoreRV]:
        """Return an ability score by short name."""
        if ability not in ("str", "dex", "con", "int", "wis", "chr"):
            return None

        rv: AbilityScoreRV = AbilityScoreRV()
        rv._base = getattr(self, ability, 0)
        rv._extra = getattr(self.extra, ability, 0)
        return rv


def main() -> None:
    data = {
        "_object": "AbilityScore",
        "_flags": {"extra_ability_score"},
        "str": 10,
        "dex": 10,
        "con": 10,
        "int": 10,
        "wis": 10,
        "chr": 10,
        "extra": {
            "_object": "AbilityScore",
            "str": 0,
            "dex": 0,
            "con": 0,
            "int": 0,
            "wis": 0,
            "chr": 0,
            "metadata": {
                "_object": "Metadata", "min": 0, "max": 5
            }
        },
        "metadata": {
            "_object": "Metadata", "min": 1, "max": 20
        }
    }

    ability_score = AbilityScore(data)
    print(ability_score)
    print(ability_score.modify("str", 10))
    print(ability_score.modify("dex", -2))
    print(ability_score.modify("metadata", 10))
    print(ability_score)
    ability_score_rv: AbilityScoreRV = ability_score.get("str")
    print(ability_score_rv.combined())
    for i in range(1, 6):
        print(ability_score_rv.bonus_per(i))


if __name__ == "__main__":
    main()
