import random
import math
from typing import Any, Dict, List, Optional
from data_structures import JSONObject, register_object
from json import loads


def safe_eval(expr: str, context: Dict[str, Any]) -> bool:
    """Vyhodnotí výraz v bezpečném omezeném prostředí."""
    safe_names = {
        "min": min, "max": max, "abs": abs, "math": math,
        **{k: v for k, v in context.items() if isinstance(v, (int, float, bool))}
    }
    try:
        return bool(eval(expr, {"__builtins__": {}}, safe_names))
    except Exception:
        return False


class BehaviourState:
    def __init__(self, name: str, data: Dict[str, Any]):
        self.name = name
        self.actions: List[str] = data.get("actions", [])
        self.transitions: List[Dict[str, Any]] = data.get("transitions", [])
        self.type: str = data.get("type", "idle")
        self.context: Dict[str, Any] = data.get("context", {})

    def get_next_state(self, context: Dict[str, Any], ignored: list[str]) -> Optional[str]:
        """Vrátí první splněný přechod podle kontextu."""
        for t in self.transitions:
            if safe_eval(t.get("condition", "True"), context):
                if t.get("to") not in ignored:
                    return t.get("to")
        return None


@register_object
class Behaviour(JSONObject):
    def __init__(self, json_data: dict[str, Any] | None = None):
        # kontrola flagu "_flags": ["to_load"]
        if json_data and "_flags" in json_data and "to_load" in json_data["_flags"]:
            filename = json_data.get("loadfile")
            if not filename:
                raise ValueError("Behaviour has 'to_load' flag but no 'loadfile' specified.")
            json_data = self.load(filename)

        super().__init__(json_data)

        self.complete(["initial", "states", "extra", "global_triggers"])
        self.current = self.initial

        self.state_objects: Dict[str, BehaviourState] = {
            name: BehaviourState(name, data)
            for name, data in self.states.items()
        }

        self.global_triggers: List[Dict[str, Any]] = json_data.get("global_triggers", [])

    def validate(self) -> None:
        return

    def check_global_triggers(self, context: Dict[str, Any]) -> Optional[str]:
        """Zkontroluje, zda nějaký globální trigger neaktivuje přechod."""
        for trigger in self.global_triggers:
            if safe_eval(trigger.get("condition", "False"), context):
                return trigger.get("to")
        return None

    def step(self, context: Dict[str, Any]) -> List[str]:
        """
        Provede akce aktuálního stavu, poté zkontroluje přechody.
        Transition stavy se vyhodnocují okamžitě a nespouští akce.
        """
        actions: List[str] = []
        if not hasattr(self, "cooldown_tracker"):
            self.cooldown_tracker: Dict[str, int] = {}

        state = self.state_objects[self.current]
        transition_loop = False
        on_cooldown_detected: list[str] = []
        while True:

            # global triggers
            global_next = self.check_global_triggers(context)
            if global_next and global_next in self.state_objects:
                self.current = global_next

            # regular states
            next_state_name = state.get_next_state(context, on_cooldown_detected)
            if next_state_name and next_state_name in self.state_objects:
                next_state = self.state_objects[next_state_name]

                # ❌ Skip pokud je na cooldownu
                cd = next_state.context.get("cooldown", 0)
                if cd and self.cooldown_tracker.get(next_state_name, 0) > 0:
                    on_cooldown_detected.append(next_state_name)
                    continue

                # 🔋 Check cost
                cost = next_state.context.get("cost", {})
                if all(context.get(res, 0) >= val for res, val in cost.items()):
                    # odečti cost
                    for res, val in cost.items():
                        context[res] -= val
                else:
                    next_state_name = None  # ignoruj, pokud nemá resources

                if next_state_name:
                    self.current = next_state_name
                    state = self.state_objects[self.current]
                    # pokud je transition, pokračuj bez akcí
                    if state.type == "transition":
                        continue
                    # nastav cooldown
                    if cd:
                        self.cooldown_tracker[next_state_name] = cd + 1
            if state.type != "transition":
                actions.extend(state.actions)
                break
            else:
                transition_loop = True
            if transition_loop:
                break

        # cooldown decrement
        for k in list(self.cooldown_tracker.keys()):
            self.cooldown_tracker[k] = max(0, self.cooldown_tracker[k] - 1)
            if self.cooldown_tracker[k] == 0:
                self.cooldown_tracker.pop(k)

        return actions

    def load(self, filename: str) -> dict[str, Any]:
        """Načte JSON ze složky behaviours/"""
        with open(f"behaviours/{filename}.json", "r", encoding="utf-8") as f:
            return loads(f.read())
