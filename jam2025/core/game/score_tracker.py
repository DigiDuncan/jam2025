class ScoreTracker:
    def __init__(self) -> None:
        self._wave: int = 1
        self.time: float = 0.0
        self.kills: int = 0

        self.kills_per_wave = {}

        self.time_mult = 1
        self.kill_mult = 1
        self._score: int = 0

    @property
    def score(self) -> int:
        return int(self.time * self.time_mult) + self._score

    @property
    def wave(self) -> int:
        return self._wave

    @wave.setter
    def wave(self, v: int) -> None:
        self._wave = v
        self.kills_per_wave[v] = 0

    def get_kill(self) -> None:
        self._score += self.wave * self.kill_mult
        self.kills_per_wave[self.wave] = self.kills_per_wave[self.wave] + 1 if self.wave in self.kills_per_wave else 1

    def update(self, delta_time: float) -> None:
        self.time += delta_time

    def reset(self) -> None:
        self.wave = 1
        self.time = 0.0
        self.kills = 0
