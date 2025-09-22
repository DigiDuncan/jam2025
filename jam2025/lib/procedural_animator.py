from __future__ import annotations
from math import pi, tau, ceil, exp, cos, cosh

from typing import Any


__all__ = (
    'ProceduralAnimator',
    'SecondOrderAnimator',
    'SecondOrderAnimatorBase',
    'SecondOrderAnimatorKClamped',
    'SecondOrderAnimatorPoleZero',
    'SecondOrderAnimatorTCritical',
    'update_default_animator'
)

Animatable = Any # god damn in nuitka
K = Any
A = Any

class SecondOrderAnimatorBase:

    def __init__(self, frequency: K, damping: K, response: K,  x_initial: A, y_initial: A, y_d_initial: A):
        self.xp: A = x_initial
        self.y: A = y_initial
        self.dy: A = y_d_initial

        self._freq: K = frequency
        self._damp: K = damping
        self._resp: K = response

        self.k1: K = damping / (pi * frequency)
        self.k2: K = 1.0 / (tau * frequency) ** 2.0
        self.k3: K = (response * damping) / (tau * frequency)

    @property
    def frequency(self) -> K:
        return self._freq

    @frequency.setter
    def frequency(self, frequency: K ):
        self._freq = frequency
        self.calc_k_vals()

    @property
    def damping(self) -> K:
        return self._damp

    @damping.setter
    def damping(self, damping: K) -> None:
        self._damp = damping
        self.calc_k_vals()

    @property
    def response(self) -> K:
        return self._damp

    @response.setter
    def response(self, response: K) -> None:
        self._resp = response
        self.calc_k_vals()

    def update_values(self, new_frequency: K | None = None, new_damping: K | None = None, new_response: K | None = None):
        self._freq = new_frequency if new_frequency is not None else self._freq
        self._damp = new_damping if new_damping is not None else self._damp
        self._resp = new_response if new_response is not None else self._resp

        self.calc_k_vals()

    def calc_k_vals(self) -> None:
        self.k1 = self._damp / (pi * self._freq)
        self.k2 = 1.0 / (tau * self._freq)**2.0
        self.k3 = (self._resp * self._damp) / (tau * self._freq)

    def update(self, dt: float, nx: A, dx: A | None = None) -> A:
        raise NotImplementedError()


class SecondOrderAnimator(SecondOrderAnimatorBase):
    """
    The most basic implementation of the second order procedural animator.

    Has stability issues that can cause jittering at high frequencies,
    and the sim can explode with lag spikes.
    """

    def update(self, dt: float, nx: A, dx: A | None = None):
        dx = dx or (nx - self.xp) / dt
        self.xp = nx
        self.y = self.y + self.dy * dt
        self.dy = self.dy + (self.xp + dx * self.k3 - self.y - self.dy * self.k1) * dt / self.k2

        return self.y


class SecondOrderAnimatorTCritical(SecondOrderAnimatorBase):
    """
    A slightly more complex implementation which tries to stay physically accurate.

    By adding extra smaller iteration steps when the delta time gets too large,
    the sim won't explode with lag spikes, but it adds extra calc steps.
    """

    def __init__(self, frequency: float, damping: float, response: float, x_initial: A, y_initial: A, y_d_initial: A):
        super().__init__(frequency, damping, response, x_initial, y_initial, y_d_initial)
        self.T_crit: float = 0.8 * ((4.0 * self.k2 + self.k1 * self.k1)**0.5 - self.k1)

    def calc_k_vals(self):
        super().calc_k_vals()
        self.T_crit = 0.8 * ((4.0 * self.k2 + self.k1 * self.k1)**0.5 - self.k1)

    def update(self, dt: float, nx: A, dx: A | None = None):
        dx = dx or (nx - self.xp) / dt
        self.xp = nx

        # Because we may be doing a bunch of iterations we don't want to use dot notation so much
        x, y, dy, k1, k2, k3 = self.xp, self.y, self.dy, self.k1, self.k2, self.k3

        # If the time step is above the critical time step it will freak out so lets make it happier
        iterations = int(ceil(dt / self.T_crit))
        dt = dt / iterations
        for _ in range(iterations):
            y = y + dy * dt
            dy = dy + (x + dx * k3 - y - dy * k1) * dt / k2

        self.y, self.dy = y, dy
        return y


class SecondOrderAnimatorKClamped(SecondOrderAnimatorBase):
    """
    A version of the sim that prioritises stability over physical accuracy.

    by changing the k2 value based on the delta_time it is possible to eliminate
    both sim explosions with lag spikes, and jittering at high frequencies.
    """

    def update(self, dt: float, nx: A, dx: A | None = None):
        dx = dx or (nx - self.xp) / dt
        self.xp = nx
        # Clamping k2 it isn't physically correct, but protects against the sim collapsing with lag spikes.
        # TODO: update to work with numpy array
        k2_stable = max(self.k2, dt*dt/2.0 + dt*self.k1/2.0, dt*self.k1)

        self.y = self.y + self.dy * dt
        self.dy = self.dy + (self.xp + dx * self.k3 - self.y - self.dy * self.k1) * dt / k2_stable

        return self.y


class SecondOrderAnimatorPoleZero(SecondOrderAnimatorBase):
    """
    The most complex version of the sim that is more accurate for higher speeds.

    By using a more complex algorithm to calc both k1 and k2 each frame lag
    spikes, jittering, and fast movement can all be improved.

    This adds alot of extra computation each frame, and may not be worth it.
    """

    def __init__(self, frequency: float, damping: float, response: float, x_initial: A, y_initial: A, y_d_initial: A):
        super().__init__(frequency, damping, response, x_initial, y_initial, y_d_initial)
        self._w = tau * frequency
        self._d = self._w * (abs(damping * damping - 1.0))

    def calc_k_vals(self):
        super().calc_k_vals()
        self._w = tau * self._freq
        self._d = self._w * (abs(self._damp * self._damp - 1.0))

    def update(self, dt: float, nx: A, dx: A | None = None):
        dx = dx or (nx - self.xp) / dt
        self.xp = nx
        if self._w * dt < self._damp:
            k1_stable = self.k1
            k2_stable = max(self.k2, dt*dt/2.0 + dt*k1_stable/2.0, dt*k1_stable)
        else:
            t1 = exp(-self._damp * self._w * dt)
            α = 2.0 * t1 * (cos(dt * self._d) if self._damp <= 1.0 else cosh(dt * self._d))
            β = t1 * t1
            t2 = dt / (1 + β - α)
            k1_stable = (1 - β) * t2
            k2_stable = dt * t2

        self.y = self.y + self.dy * dt
        self.dy = self.dy + (self.xp + dx * self.k3 - self.y - self.dy * k1_stable) * dt / k2_stable

        return self.y


ProceduralAnimator = SecondOrderAnimatorKClamped


def update_default_animator(new_default: type[SecondOrderAnimator]):
    assert issubclass(new_default, SecondOrderAnimatorBase)
    global ProceduralAnimator
    ProceduralAnimator = new_default
