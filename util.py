import numpy as np

import ColorType
from Component import Component
from DisplayableCylinder import DisplayableCylinder
from GLProgram import GLProgram
from Material import Material

from Point import Point
from Quaternion import Quaternion


def vec1_to_vec2(v1: Point, v2: Point) -> np.ndarray:
    rotate_axis = v1.cross3d(v2)
    rotate_angle = v1.angleWith(v2)
    rotate_q = Quaternion.axisAngleToQuaternion(rotate_axis, rotate_angle)
    return rotate_q.toMatrix()


_mat_flash_light_core = Material(np.array((0, 0, 0, 0)), np.array((0, 0, 0, 1)),
                                 np.array((1, 1, 1, 1)), 256)


def create_flash_light(shaderProg: GLProgram,) -> Component:
    flashlight_core = Component(Point((0, 0, 0)), DisplayableCylinder(
        shaderProg, 0.4, 0.5, 0.8, 36, color=ColorType.WHITE))
    flashlight_core.setDefaultAngle(180, flashlight_core.vAxis)
    flashlight_core.setDefaultAngle(180, flashlight_core.wAxis)
    flashlight_core.renderingRouting = "texture"
    flashlight_core.setTexture(shaderProg, "assets/flashlight.jpg")
    flashlight_core.setMaterial(_mat_flash_light_core)

    def turn_on(component):
        component.setTexture(shaderProg, "assets/flashlight.jpg")
        component.renderingRouting = "texture"

    def turn_off(component):
        component.renderingRouting = "lighting"

    flashlight_core.turn_on = turn_on
    flashlight_core.turn_off = turn_off

    mat_flashshell = Material(np.array((0, 0, 0, 0.1)), np.array((0.4, 0.4, 0.4, 1)),
                              np.array((1, 1, 1, 0.1)), 8)
    outshell_color = ColorType.getGrayColor(0.7)
    flashlight_front = Component(Point((0, 0, -0.01)),
                                 DisplayableCylinder(shaderProg, 0.5, 0.7, 0.8, 36, color=outshell_color))
    flashlight_front.renderingRouting = "lighting"
    flashlight_front.setMaterial(mat_flashshell)
    flashlight_body = Component(Point((0, 0, -(2 + 0.8) / 2)),
                                DisplayableCylinder(shaderProg, 0.35, 0.35, 2, 36, color=outshell_color))
    flashlight_body.renderingRouting = "lighting"
    flashlight_body.setMaterial(mat_flashshell)
    flashlight_front.addChild(flashlight_body)
    flashlight_core.addChild(flashlight_front)
    return flashlight_core
