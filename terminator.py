# board3d_volume_img.py
# Mostra um tabuleiro 8x8 e um volume 8x8x8 com imagens (caveira/drone)
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from PIL import Image
import sys, os, math

GRID_SIZE = 8
VOL_Z = 8
CELL = 1.0
VERT_SPACING = 0.6
CAM_DISTANCE = 14.0
window_width = 1000
window_height = 720

scene = None
yaw = 0.0
pitch = 25.0
zoom = CAM_DISTANCE

# ---------- carregar imagens ----------
def load_texture(path):
    img = Image.open(path).convert("RGBA")
    img_data = img.tobytes("raw", "RGBA", 0, -1)
    w, h = img.size
    tex = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    return tex, (w, h)

tex_skull = None
tex_drone = None

# ---------- função loads ----------
def loads(texts):
    ll = True
    zi = 0
    xi = 0
    yi = 0
    a = []
    ttt = texts.split(";")
    zi = len(ttt)
    for t in range(zi):
        yyy = ttt[t].strip().split("\n")
        yi = len(yyy)
        for y in range(yi):
            xxx = yyy[y].split(",")
            xi = len(xxx)
            if ll:
                a = [[[" " for _ in range(xi)] for _ in range(yi)] for _ in range(zi)]
                ll = False
            for x in range(xi):
                b = xxx[x].strip()
                a[t][y][x] = b if b != "" else " "
    return a

# ---------- utilidades ----------
def world_pos_from_index(ix, iy, grid_size=GRID_SIZE, cell=CELL):
    HALF = grid_size * cell / 2.0
    wx = -HALF + (cell / 2.0) + ix * cell
    wz = -HALF + (cell / 2.0) + iy * cell
    return wx, wz

# ---------- OpenGL ----------
def init_gl():
    glClearColor(1.0, 1.0, 0.0, 1.0)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_NORMALIZE)
    glShadeModel(GL_SMOOTH)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION, [4.0, 10.0, 6.0, 1.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.9, 0.9, 0.9, 1.0])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [0.6, 0.6, 0.6, 1.0])
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_TEXTURE_2D)

# ---------- tabuleiro ----------
def draw_checkboard():
    glDisable(GL_LIGHTING)
    half = (GRID_SIZE - 1) * CELL / 2.0
    glBegin(GL_QUADS)
    for iy in range(GRID_SIZE):
        for ix in range(GRID_SIZE):
            wx = -half + ix * CELL
            wz = -half + iy * CELL
            if (ix + iy) % 2 == 0:
                glColor3f(0.9, 0.9, 0.9)
            else:
                glColor3f(1.0, 1.0, 0.2)
            glVertex3f(wx, 0, wz)
            glVertex3f(wx + CELL, 0, wz)
            glVertex3f(wx + CELL, 0, wz + CELL)
            glVertex3f(wx, 0, wz + CELL)
    glEnd()
    glEnable(GL_LIGHTING)

# ---------- desenho imagens ----------
def draw_textured_quad(tex, size=0.6):
    glBindTexture(GL_TEXTURE_2D, tex)
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0); glVertex3f(-size/2, 0, -size/2)
    glTexCoord2f(1, 0); glVertex3f(size/2, 0, -size/2)
    glTexCoord2f(1, 1); glVertex3f(size/2, 0, size/2)
    glTexCoord2f(0, 1); glVertex3f(-size/2, 0, size/2)
    glEnd()

def draw_volume(volume):
    for iz, layer in enumerate(volume):
        for iy, row in enumerate(layer):
            for ix, val in enumerate(row):
                if str(val).strip() != "":
                    wx, wz = world_pos_from_index(ix, iy)
                    y = iz * VERT_SPACING
                    glPushMatrix()
                    glTranslatef(wx, y + 0.3, wz)
                    glRotatef(90, 1, 0, 0)
                    if iy == 0:
                        draw_textured_quad(tex_skull[0])
                    else:
                        draw_textured_quad(tex_drone[0])
                    glPopMatrix()

# ---------- display ----------
def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    eye_x = zoom * math.sin(math.radians(yaw)) * math.cos(math.radians(pitch))
    eye_y = zoom * math.sin(math.radians(pitch))
    eye_z = zoom * math.cos(math.radians(yaw)) * math.cos(math.radians(pitch))
    gluLookAt(eye_x, eye_y, eye_z, 0, (VOL_Z * VERT_SPACING)/4.0, 0, 0, 1, 0)

    glPushMatrix()
    glTranslatef(0, -1.5, 0)
    draw_checkboard()
    if scene:
        draw_volume(scene)
    glPopMatrix()
    glutSwapBuffers()

# ---------- input ----------
def keyboard(key, x, y):
    global yaw, pitch, zoom
    key = key.decode() if isinstance(key, bytes) else key
    if key == '\x1b': sys.exit(0)
    elif key.lower() == 'a': yaw -= 8
    elif key.lower() == 'd': yaw += 8
    elif key.lower() == 'w': pitch = min(80, pitch + 5)
    elif key.lower() == 's': pitch = max(-10, pitch - 5)
    elif key == '+': zoom = max(4, zoom - 1)
    elif key == '-': zoom = min(40, zoom + 1)
    glutPostRedisplay()

def reshape(w, h):
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, float(w)/float(h if h>0 else 1), 0.1, 100)
    glMatrixMode(GL_MODELVIEW)

# ---------- main ----------
def main():
    global scene, tex_skull, tex_drone

    fn = "my.xyz"
    if os.path.exists(fn):
        with open(fn, "r", encoding="utf-8") as fh:
            scene = loads(fh.read())
    else:
        scene = [[["x" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)] for _ in range(VOL_Z)]

    # cria janela e contexto OpenGL primeiro
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(window_width, window_height)
    glutCreateWindow(b"Volume 3D com imagens (drone/caveira)")
    init_gl()

    # só agora podemos carregar texturas!
    fn_skull = "t2.png"
    fn_drone = "drone.png"
    tex_skull = load_texture(fn_skull)
    tex_drone = load_texture(fn_drone)

    # callbacks
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutIdleFunc(glutPostRedisplay)
    glutMainLoop()
if __name__ == "__main__":
    main()
