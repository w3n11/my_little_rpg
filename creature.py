from data_structures import JSONObject, register_object
from typing import Any, Optional, Dict, List
from abilityscore import AbilityScore
from behaviour import Behaviour


@register_object
class Creature(JSONObject):
    def __init__(self, json_data: dict[str, Any] | None = None) -> None:
        super().__init__(json_data)
        self.complete([
            "name",
            "race",
            "ability_score",
            "inventory",
            "behaviour",
            "tags",
            "reactions"
        ])

        if isinstance(self.behaviour, dict):
            self.behaviour = Behaviour(self.behaviour)

        if isinstance(self.ability_score, dict):
            self.ability_score = AbilityScore(self.ability_score)

    def think(self, context: Dict[str, Any]) -> List[str]:
        """
        Simulace jednoho rozhodovacího kroku tvora.
        Vrací seznam akcí, které chce tvor provést.
        """
        if not self.behaviour:
            return []

        actions = self.behaviour.step(context)
        # Zde můžeš doplnit logiku "post-processing" – např. převod akce na konkrétní příkaz v enginu
        return actions

    def validate(self) -> None:
        """Volitelná validace dat."""
        return


def main():
    # Dummy ability score
    ability_score_data = {
        "_object": "AbilityScore",
        "_flags": {"extra_ability_score"},
        "str": 20,
        "dex": 14,
        "con": 20,
        "int": 14,
        "wis": 18,
        "chr": 15,
        "extra": {
            "_object": "AbilityScore",
            "str": 0, "dex": 0, "con": 0, "int": 0, "wis": 0, "chr": 0,
            "metadata": {"_object": "Metadata", "min": 0, "max": 5}
        },
        "metadata": {"_object": "Metadata", "min": 1, "max": 20}
    }

    # Načteme behaviour draka z JSON
    dragon_data = {
        "_object": "Creature",
        "_flags": {},
        "name": "Johnny",
        "race": "Dragon",
        "ability_score": ability_score_data,
        "inventory": [],
        "behaviour": {"_flags": {"to_load"}, "loadfile": "dragon"},
        "tags": {},
        "reactions": {}
    }

    dragon = Creature(dragon_data)

    # Simulační scénáře
    contexts = [
        {"enemies_in_sight": 0, "health_ratio": 0.9, "stamina": 10},
        {"enemies_in_sight": 5, "health_ratio": 1, "stamina": 10},
        {"enemies_in_sight": 10, "distance_to_nearest_enemy": 8, "stamina": 10},
        {"enemies_in_sight": 2, "distance_to_nearest_enemy": 7, "stamina": 10},
        {"enemies_in_sight": 2, "distance_to_nearest_enemy": 6, "stamina": 5},
        {"enemies_in_sight": 1, "distance_to_nearest_enemy": 2, "stamina": 4},
    ]

    print(f"=== Simulace draka: {dragon.name} ===\n")
    for step, ctx in enumerate(contexts):
        actions = dragon.think(ctx)
        print(f"Step {step}: state={dragon.behaviour.current}")
        print(f"Cooldowns: {dragon.behaviour.cooldown_tracker}")
        print(f"Context: {ctx}")
        print(f"Actions: {actions}\n")


if __name__ == "__main__":
    main()
