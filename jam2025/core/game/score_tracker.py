class ScoreTracker:
    def __init__(self) -> None:
        self.wave: int = 1
        self.time: float = 0.0
        self.kills: int = 0

        self.time_mult = 1
        self.kill_mult = 1
        self._score: int = 0

    @property
    def score(self) -> int:
        return int(self.time * self.time_mult) + self._score

    def get_kill(self) -> None:
        self._score += self.wave * self.kill_mult

    def update(self, delta_time: float) -> None:
        self.time += delta_time

    def reset(self) -> None:
        self.wave = 1
        self.time = 0.0
        self.kills = 0
