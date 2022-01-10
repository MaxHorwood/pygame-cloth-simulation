from __future__ import annotations
from dataclasses import dataclass

from pygame import color
from data_types import PointMass, Link, FeatureToggle
import pygame
import math

SCREEN_SIZE = (800, 900)
total_points = 50
gap = 10
offsetx, offsety = (SCREEN_SIZE[0] - (total_points * gap)) / 2, 50


def generate_cloth_grid():
    thingy_list = []
    points: list[PointMass] = [
        PointMass(pygame.Vector2((x * gap) + offsetx, (y * gap) + offsety), 1, pygame.Vector2(0, 0), y == 0)
        for x in range(total_points)
        for y in range(15)
    ]

    def get_point_by_pos(pos: pygame.Vector2):
        p = [p for p in points if p.pos == pos]
        assert len(p) == 1
        return p[0]

    links: list[Link] = []
    for p1 in points:
        if p1.pos.y > offsety:
            p2 = get_point_by_pos(pygame.Vector2(p1.pos.x, p1.pos.y - gap))
            links.append(Link(p1, p2))
        if p1.pos.x > offsetx:
            p2 = get_point_by_pos(pygame.Vector2(p1.pos.x - gap, p1.pos.y))
            links.append(Link(p1, p2))
        if p1.pos.y > offsety and p1.pos.x > offsetx:
            p2 = get_point_by_pos(pygame.Vector2(p1.pos.x - gap, p1.pos.y))
            p3 = get_point_by_pos(pygame.Vector2(p1.pos.x, p1.pos.y - gap))
            p4 = get_point_by_pos(pygame.Vector2(p1.pos.x - gap, p1.pos.y - gap))
            thingy_list.append([p1, p2, p3, p4])
    return points, links, thingy_list


pygame.init()
pygame.display.set_caption("Cloth Simulation")


@dataclass
class Cloth:
    points: list[PointMass]
    links: list[Link]
    pretty_cloth: list[list[PointMass]]

    screen: pygame.Surface = pygame.display.set_mode(SCREEN_SIZE)
    main_surface: pygame.Surface = pygame.Surface(SCREEN_SIZE)
    camera: pygame.Vector2 = pygame.Vector2(0, 0)
    font = pygame.font.SysFont(None, 24)
    clock = pygame.time.Clock()
    leftOverTime = 0
    fps = 144
    timestep_amount = round(1 / 60 * 1000)
    gravity = 0.2
    show_wireframe = False
    show_cloth = True
    show_ui = True

    def __post_init__(self):
        # TODO: Add more ways to 'reset' the grid - just different options to layout the cloth
        # TODO: Add it so can change the amount of points / links
        self.shortcuts: list[FeatureToggle] = [
            FeatureToggle(pygame.K_r, callback=self.reset_grid),
            FeatureToggle(pygame.K_g, callback=self.toggle_gravity),
            FeatureToggle(pygame.K_h, callback=self.toggle_ui),
            FeatureToggle(pygame.K_w, callback=self.toggle_wireframe),
            FeatureToggle(pygame.K_c, callback=self.toggle_cloth),
        ]

    def run(self):
        while True:
            self.process_events()
            self.update()
            self.draw()

    def reset_grid(self):
        self.points, self.links, self.pretty_cloth = generate_cloth_grid()

    def toggle_wireframe(self):
        self.show_wireframe = not self.show_wireframe

    def toggle_cloth(self):
        self.show_cloth = not self.show_cloth

    def toggle_ui(self):
        self.show_ui = not self.show_ui

    def toggle_gravity(self):
        if self.gravity:
            self.gravity = 0
        else:
            self.gravity = 0.2

    def process_events(self):
        pressed_keys = pygame.key.get_pressed()
        for shortcut in self.shortcuts:
            shortcut.toggle(pressed_keys)
            shortcut.call()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEMOTION:
                self.handle_mouse_motion_events(event)

    def handle_mouse_motion_events(self, event):
        pos = pygame.Vector2(event.rel)
        if event.buttons[2]:
            self.camera = pos
            for p in self.points:
                if p.pos.distance_to(pygame.Vector2(event.pos)) < 20:
                    p.pos += pos * 2
        if event.buttons[0]:
            ppp = pygame.Vector2(event.pos)
            for link in self.links:
                if link.deleted:
                    continue
                if math.floor(link.p1.pos.distance_to(ppp) + link.p2.pos.distance_to(ppp)) == math.floor(
                    link.p1.pos.distance_to(link.p2.pos)
                ):
                    link.deleted = True
                    link.p1.deleted = True
                    link.p2.deleted = True

    def update(self):
        elapsedTime = self.clock.tick(144)
        # Timestemp
        # 16 is simulating at 60fps
        elapsedTime += self.leftOverTime
        timesteps = math.floor(elapsedTime / self.timestep_amount)
        self.leftOverTime = elapsedTime - (timesteps * self.timestep_amount)
        # Draw for each timestep, this would happen if we slowly fall out of sync.
        for _ in range(timesteps):
            for link in self.links:
                if link.deleted:
                    continue
                link.solve()
            for point in self.points:
                point.update(self.timestep_amount, self.gravity, SCREEN_SIZE)
        self.camera = self.camera.lerp(pygame.Vector2(0, 0), 0.5)

    def draw(self):
        self.screen.fill((0, 0, 0))
        self.main_surface.fill((0, 0, 0))

        # The "Cloth"
        if self.show_cloth:
            for p in self.pretty_cloth:
                if p[0].deleted or p[1].deleted or p[2].deleted or p[3].deleted:
                    continue
                polygon_rect: list[pygame.Vector2] = [p[1].pos, p[0].pos, p[2].pos, p[3].pos]
                # Colour the rect based on the area just to make it look pretty
                # Would be interesting to try and colour this more authentically
                # but then you might need to use 3d geometry.
                # You could probably do something with the velocity each point is moving in.
                width = polygon_rect[0].distance_to(polygon_rect[1])
                height = polygon_rect[2].distance_to(polygon_rect[3])
                area = width * height / 2
                pygame.draw.polygon(self.main_surface, (min(area, 255), 50, 150), polygon_rect)

        # Points and Links
        if self.show_wireframe:
            for point in self.points:
                if not point.deleted:
                    pygame.draw.circle(self.main_surface, (200, 100, 100), point.pos, 3)
            for link in self.links:
                if not link.deleted:
                    pygame.draw.line(self.main_surface, link.color, link.p1.pos, link.p2.pos)

        # Cursor position
        pygame.draw.circle(self.main_surface, (0, 255, 0), pygame.mouse.get_pos(), 10, 2)
        if self.show_ui:
            self.display_text((0, 0), f"FPS: {int(self.clock.get_fps())}")
            self.display_text((0, 20), f"[G]ravity: {'ON' if self.gravity else 'OFF' }")
            self.display_text((0, 40), f"[W]ireframe: {'ON' if self.show_wireframe else 'OFF' }")
            self.display_text((0, 60), f"[C]loth: {'ON' if self.show_cloth else 'OFF' }")

        self.screen.blit(self.main_surface, self.camera)
        pygame.display.update()

    def display_text(self, pos: tuple[int, int], msg: str):
        img = self.font.render(f"{msg}", 0, (255, 255, 0))
        rect = img.get_rect(left=pos[0], top=pos[1])
        self.main_surface.blit(img, rect)


points, links, cloth = generate_cloth_grid()
Cloth(points, links, cloth).run()
