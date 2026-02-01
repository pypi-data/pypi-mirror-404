import pygame, sys
from dataclasses import dataclass


@dataclass
class Keyboard:
    A = pygame.K_a
    B = pygame.K_b
    C = pygame.K_c
    D = pygame.K_d
    E = pygame.K_e
    F = pygame.K_f
    G = pygame.K_g
    H = pygame.K_h
    I = pygame.K_i
    J = pygame.K_j
    K = pygame.K_k
    L = pygame.K_l
    M = pygame.K_m
    N = pygame.K_n
    O = pygame.K_o
    P = pygame.K_p
    Q = pygame.K_q
    R = pygame.K_r
    S = pygame.K_s
    T = pygame.K_t
    U = pygame.K_u
    V = pygame.K_v
    W = pygame.K_w
    X = pygame.K_x
    Y = pygame.K_y
    Z = pygame.K_z
    SPACE = pygame.K_SPACE


class Image:
    def __init__(self, path):
        self.image = pygame.image.load(path)

    def __call__(self):
        return self.image

    def resize(self, width, height):
        self.image = pygame.transform.scale(self.image, (width, height))
        return self.image

    def resize_and_convert_alpha(self, width, height):
        self.image = self.resize(width, height).convert_alpha()
        return self.image

    @classmethod
    def quick_resize(cls, path, width, height):
        return cls(path).resize(width, height)

    @classmethod
    def quick_resize_and_convert_alpha(cls, path, width, height):
        return cls(path).resize_and_convert_alpha(width, height)


def quit():
    pygame.quit()
    sys.exit()


def quit_if_quit(event):
    if event.type == pygame.QUIT:
        quit()

