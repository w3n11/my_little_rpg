class Hex:
    """Hexagonální buňka."""
    DIRECTIONS = [
        (1, 0), (1, -1), (0, -1),
        (-1, 0), (-1, 1), (0, 1)
    ]

    def __init__(self, q: int, r: int, terrain: str = "plain"):
        self.q = q  # column
        self.r = r  # row
        self.terrain = terrain
        self.occupant = None  # například Creature

    def neighbors(self):
        return [(self.q + dq, self.r + dr) for dq, dr in Hex.DIRECTIONS]

    def __repr__(self):
        return f"Hex(q={self.q}, r={self.r}, terrain={self.terrain})"


class HexMap:
    def __init__(self, radius: int):
        """Vytvoří hex mapu s daným poloměrem (hexy kolem centra)."""
        self.hexes: dict[tuple[int,int], Hex] = {}
        for q in range(-radius, radius + 1):
            r1 = max(-radius, -q - radius)
            r2 = min(radius, -q + radius)
            for r in range(r1, r2 + 1):
                self.hexes[(q, r)] = Hex(q, r)

    def get(self, q: int, r: int) -> Hex | None:
        return self.hexes.get((q, r))

    def distance(self, a: Hex, b: Hex) -> int:
        """Vzdálenost mezi dvěma hexy (axial coords)."""
        return (abs(a.q - b.q) + abs(a.q + a.r - b.q - b.r) + abs(a.r - b.r)) // 2

    def neighbors(self, hex_: Hex):
        return [self.hexes.get(n) for n in hex_.neighbors() if n in self.hexes]


def main() -> None:
    m = HexMap(radius=10)

    center = m.get(0, 0)
    print(center)
    print("Neighbors:", m.neighbors(center))

    # vzdálenost dvou hexů
    h1 = m.get(-2, 0)
    h2 = m.get(5, -2)
    print("Distance:", m.distance(h1, h2))


if __name__ == "__main__":
    main()
