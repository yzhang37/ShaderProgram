"""
Define Torus here.
First version in 11/01/2021

:author: micou(Zezhou Sun)
:version: 2021.1.1
"""

from Displayable import Displayable
from GLBuffer import VAO, VBO, EBO
from Point import Point
import numpy as np
import ColorType
import math

try:
    import OpenGL

    try:
        import OpenGL.GL as gl
        import OpenGL.GLU as glu
    except ImportError:
        from ctypes import util

        orig_util_find_library = util.find_library


        def new_util_find_library(name):
            res = orig_util_find_library(name)
            if res:
                return res
            return '/System/Library/Frameworks/' + name + '.framework/' + name


        util.find_library = new_util_find_library
        import OpenGL.GL as gl
        import OpenGL.GLU as glu
except ImportError:
    raise ImportError("Required dependency PyOpenGL not present")


##### 6: Texture Mapping
# Requirements:
#   1. Set up each object's vertex texture coordinates(2D) to the self.vertices 9:11 columns
#   (i.e. the last two columns). Tell OpenGL how to interpret these two columns:
#   you need to set up attribPointer in the Displayable object's initialize method.
#   2. Generate texture coordinates for the torus and sphere. Use “./assets/marble.jpg” for the torus and
#   “./assets/earth.jpg” for the sphere as the texture image.
#   There should be no seams in the resulting texture-mapped model.

class DisplayableTorus(Displayable):
    vao = None
    vbo = None
    ebo = None
    shaderProg = None

    # stores current torus's information, read-only
    nsides = 0
    rings = 0
    innerRadius = 0
    outerRadius = 0
    color = None

    vertices = None
    indices = None

    def __init__(self, shaderProg, innerRadius=0.25, outerRadius=0.5, nsides=36, rings=36, color=ColorType.SOFTBLUE):
        super(DisplayableTorus, self).__init__()
        self.shaderProg = shaderProg
        self.shaderProg.use()

        self.vao = VAO()
        self.vbo = VBO()  # vbo can only be initiate with glProgram activated
        self.ebo = EBO()

        self.generate(innerRadius, outerRadius, nsides, rings, color)

    def generate(self, innerRadius=0.25, outerRadius=0.5, nsides=36, rings=36, color=ColorType.SOFTBLUE):
        # The function generates a torus shape by setting its inner and outer radii,
        # number of sides and rings, and color.

        # The surface parameter of a torus can be represented by the following equations:
        #   x = (a + b * cos(v)) * cos(u)
        #   y = (a + b * cos(v)) * sin(u)
        #   z = b * sin(v)
        # where a = (outer + inner) / 2, b = (outer - inner) / 2

        # The normal vector equation of a torus is:
        #   nx = b * cos(u) * cos(v) * (a + b * cos(v))
        #   ny = b * sin(u) * cos(v) * (a + b * cos(v))
        #   nz = b * sin(v) * (a + b * cos(v))
        # We can simplify and normalize this equation as follows:
        #   nx = sign(b) * cos(u) * cos(v) * sign(a + b * cos(v))
        #   ny = sign(b) * sin(u) * cos(v) * sign(a + b * cos(v))
        #   nz = sign(b) * sin(v) * sign(a + b * cos(v))
        #
        # Among then, a + b * cos(v), cos(u), sin(u), cos(v), sin(v) appears many times, so we can
        #   pre-compute them.
        #
        # Binding nsides to u, rings to v.

        if innerRadius > outerRadius:
            # Make sure the inner radius is smaller than the outer radius.
            innerRadius, outerRadius = outerRadius, innerRadius

        self.innerRadius = innerRadius
        self.outerRadius = outerRadius
        self.nsides = nsides
        self.rings = rings
        self.color = color

        a = (outerRadius + innerRadius) / 2
        b = (outerRadius - innerRadius) / 2

        if b == 0:
            # If the torus has no thickness (b = 0),
            # set its vertices and indices to empty arrays.
            self.vertices = np.zeros((0, 11))
            self.indices = np.zeros(0)
            return

        # We need to pad one extra row for both the number of sides and rings,
        # to assign the correct texture coordinates to them.
        nsides_1 = nsides + 1
        rings_1 = rings + 1
        self.vertices = np.zeros((nsides_1 * rings_1, 11))
        self.indices = np.zeros((nsides_1 * rings_1, 6), dtype=np.uint32)

        pi = np.pi
        for i, u in enumerate(np.linspace(-pi, pi, nsides_1)):
            for j, v in enumerate(np.linspace(-pi, pi, rings_1)):
                # pre_compute
                cos_u = np.cos(u)
                sin_u = np.sin(u)
                cos_v = np.cos(v)
                sin_v = np.sin(v)
                # a + b * np.cos(v)
                comm_patt = a + b * cos_v

                # compute the vertex position
                x = comm_patt * cos_u
                y = comm_patt * sin_u
                z = b * sin_v
                i_by_j = i * rings_1 + j

                # compute the vertex normal
                nx = np.sign(b) * cos_u * cos_v * np.sign(comm_patt)
                ny = np.sign(b) * sin_u * cos_v * np.sign(comm_patt)
                nz = np.sign(b) * sin_v * np.sign(comm_patt)

                # compute the vertex color
                self.vertices[i_by_j] = [x, y, z, nx, ny, nz, *color, i / nsides, j / rings]

                # # compute the vertex texture coordinates
                # self.vertices[vert_index, 9:11] = [u / (2 * pi), v / (2 * pi)]

                i_by_jp1 = i * rings_1 + (j + 1) % rings_1
                ip1_by_j = (i + 1) % nsides_1 * rings_1 + j
                ip1_by_jp1 = (i + 1) % nsides_1 * rings_1 + (j + 1) % rings_1

                # readjust the order to match CCW.
                self.indices[i_by_j, 0:6] = [
                    i_by_j, ip1_by_j, i_by_jp1,
                    ip1_by_jp1, ip1_by_j, i_by_jp1]

        self.indices = self.indices.flatten("C")

    def draw(self):
        self.vao.bind()
        self.ebo.draw()
        self.vao.unbind()

    def initialize(self):
        """
        Remember to bind VAO before this initialization. If VAO is not bind, program might throw an error
        in systems which don't enable a default VAO after GLProgram compilation
        """
        self.vao.bind()
        self.vbo.setBuffer(self.vertices, 11)
        self.ebo.setBuffer(self.indices)

        self.vbo.setAttribPointer(self.shaderProg.getAttribLocation("vertexPos"),
                                  stride=11, offset=0, attribSize=3)
        self.vbo.setAttribPointer(self.shaderProg.getAttribLocation("vertexNormal"),
                                  stride=11, offset=3, attribSize=3)
        self.vbo.setAttribPointer(self.shaderProg.getAttribLocation("vertexColor"),
                                  stride=11, offset=6, attribSize=3)
        self.vbo.setAttribPointer(self.shaderProg.getAttribLocation("vertexTexture"),
                                  stride=11, offset=9, attribSize=2)
        self.vao.unbind()
