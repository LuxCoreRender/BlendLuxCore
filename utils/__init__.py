import re

def to_luxcore_name(string):
    return re.sub('[^_0-9a-zA-Z]+', '__', string)


def matrix_to_list(matrix, apply_worldscale=False, invert=False):
    """
    Flatten a 4x4 matrix into a list
    Returns list[16]
    """

    if apply_worldscale:
        matrix = matrix.copy()
        sm = get_worldscale()  # TODO
        matrix *= sm
        ws = get_worldscale(as_scalematrix=False)
        matrix[0][3] *= ws
        matrix[1][3] *= ws
        matrix[2][3] *= ws

    if invert:
        matrix = matrix.inverted()

    l = [matrix[0][0], matrix[1][0], matrix[2][0], matrix[3][0],
         matrix[0][1], matrix[1][1], matrix[2][1], matrix[3][1],
         matrix[0][2], matrix[1][2], matrix[2][2], matrix[3][2],
         matrix[0][3], matrix[1][3], matrix[2][3], matrix[3][3]]

    return [float(i) for i in l]


def calc_filmsize(scene, context=None):
    if context:
        width = context.region.width
        height = context.region.height
    else:
        scale = scene.render.resolution_percentage / 100
        width = int(scene.render.resolution_x * scale)
        height = int(scene.render.resolution_y * scale)

    # TODO: account for border render
    return width, height