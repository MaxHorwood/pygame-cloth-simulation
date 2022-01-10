from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
from datetime import datetime, timedelta
import pygame as pg


@dataclass
class PointMass:
    pos: pg.Vector2
    mass: float
    vel: pg.Vector2
    is_anchor: bool = False
    last_pos: pg.Vector2 | None = None
    acc: pg.Vector2 | None = None
    deleted: bool = False

    def __post_init__(self):
        self.last_pos = self.pos
        self.acc = pg.Vector2(0, 0)

    def position_constraints(self, screen_size):
        if self.pos.x < 0:
            self.pos.x = 0
            if self.vel.x < 0:
                self.vel.x = self.vel.x * -1
        if self.pos.x > screen_size[0]:
            self.pos.x = screen_size[0]
            if self.vel.x > 0:
                self.vel.x = self.vel.x * -1
        if self.pos.y < 0:
            self.pos.y = 0
            if self.vel.y < 0:
                self.vel.y = self.vel.y * -1
        if self.pos.y > screen_size[1]:
            self.pos.y = screen_size[1]
            if self.vel.y > 0:
                self.vel.y = self.vel.y * -1

    def applyForce(self, fX: float, fY: float):
        self.acc.x += fX / self.mass
        self.acc.y += fY / self.mass

    def update(self, updateRate: int, gravity: float, screen_size: tuple[int, int]):
        if self.is_anchor:
            return
        self.applyForce(0, gravity * self.mass)
        self.vel = self.pos - self.last_pos
        next_pos_x = self.pos.x + self.vel.x + 0.05 * self.acc.x * updateRate
        next_pos_y = self.pos.y + self.vel.y + 0.05 * self.acc.y * updateRate
        next_pos = pg.Vector2(next_pos_x, next_pos_y)
        self.last_pos = pg.Vector2(self.pos)
        self.pos = pg.Vector2(next_pos)

        self.position_constraints(screen_size)
        self.acc = pg.Vector2(0, 0)


@dataclass
class Link:
    p1: PointMass
    p2: PointMass

    color: pg.Color = pg.Color(255, 255, 255)

    stiffness: float = 1
    tear_distance: float = 100
    resting_distance: float = 10
    deleted: bool = False

    def solve(self):
        d = self.p1.pos.distance_to(self.p2.pos)
        if not d:
            return

        # Set color
        amount_red = int(min(d, self.tear_distance) / self.tear_distance * 255)
        lerp_amount = int(min(d, self.tear_distance) / self.tear_distance * 100) / 100
        self.color = pg.Color(255, 255, 255).lerp(pg.Color(amount_red, 0, 0), lerp_amount)

        difference = (self.resting_distance - d) / d
        # print(difference, d)
        translate = (self.p1.pos - self.p2.pos) * 0.5 * difference

        im1 = 1 / self.p1.mass
        im2 = 1 / self.p2.mass
        scalarP1 = (im1 / (im1 + im2)) * self.stiffness

        if d > self.tear_distance:
            self.deleted = True
            self.p1.deleted = True
            self.p2.deleted = True
        if not self.p1.is_anchor:
            self.p1.pos += translate * scalarP1
        if not self.p2.is_anchor:
            self.p2.pos -= translate * (self.stiffness - scalarP1)


@dataclass
class FeatureToggle:
    # Key combo list to toggle is_enabled
    key: any
    is_enabled: bool = False
    hold: bool = False
    # Function that gets called when is_enabled is on
    callback: Callable = None
    last_called: datetime = datetime.now()

    def call(self):
        if self.is_enabled:
            self.callback()
            if not self.hold:
                self.is_enabled = False

    def toggle(self, pressed_keys):
        # Todo: Add a debounce so can't be toggle between straight away
        if not self.hold and self.last_called + timedelta(0, 0.2) > datetime.now():
            return
        if not pressed_keys[self.key]:
            self.is_enabled = False
            return
        self.last_called = datetime.now()
        self.is_enabled = True
