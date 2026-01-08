import os

import cadquery as cq
import numpy as np
from cadquery import exporters

# Modifiable parameters
height = 4  # mm, minimum is 0.8
chamferSize = 0.8  # mm
thickness = 4.0  # mm
caliperWidth = 0.5  # mm, width of the caliper stops
stopGap = 1.0  # mm, gap between caliper stops and the frame
# Recommend fullWidth/numMeasPoints does not fall below 40
fullWidth = 150  # mm
numMeasPoints = 5
diagWidth = 15
# adjustment at the corners to account for potentially
# uncalibrated pressure advance
pa = 0.8
# make chamfers?
fightElephantFoot = True

# The rest is all automated
sep = fullWidth / (numMeasPoints * 2)

halfWidth = fullWidth / 2


def thickLine(
    x0,
    x1,
    y0,
    y1,
    height=height,
    thickness=thickness,
    wp=cq.Workplane(),
    chamferStart=True,
    chamferEnd=True,
):
    dx = x1 - x0
    dy = y1 - y0

    xbar = (x0 + x1) / 2
    ybar = (y0 + y1) / 2

    theta = np.arctan2(dy, dx)
    print(theta)
    L = np.sqrt(dx**2 + dy**2)

    line = wp.center(0, 0).rect(L, thickness).extrude(height)

    if chamferStart:
        line = line.faces("-X").edges("|Z").chamfer(chamferSize)

    if chamferEnd:
        line = line.faces("+X").edges("|Z").chamfer(chamferSize)

    return line.rotate((0, 0, 0), (0, 0, 1), theta * 180 / np.pi).translate(
        (xbar, ybar, 0)
    )


def paWedge(
    sideLength=chamferSize,
    mirrorX=False,
    mirrorY=False,
    wp=cq.Workplane(),
    height=height * 2,
):

    wedge = (
        wp.moveTo(0, 0)
        .lineTo(0, sideLength)
        .lineTo(sideLength, 0)
        .close()
        .extrude(height)
    )
    if mirrorX:
        # negate x coords
        wedge = wedge.mirror((1, 0, 0), (0, 0, 0))
    if mirrorY:
        # negate y coords
        wedge = wedge.mirror((0, 1, 0), (0, 0, 0))
    return wedge


# Center line
result = thickLine(
    0,
    0,
    -fullWidth / 2 - thickness,
    fullWidth / 2 + thickness,
)

# left and right lines, top and bottom
result += thickLine(
    -sep + thickness / 2,
    -sep + thickness / 2,
    sep - thickness,
    fullWidth / 2,
)

result += thickLine(
    -sep + thickness / 2,
    -sep + thickness / 2,
    -sep + thickness,
    -fullWidth / 2,
)

result += thickLine(
    sep - thickness / 2,
    sep - thickness / 2,
    sep - thickness,
    fullWidth / 2 + thickness,
)

result += thickLine(
    sep - thickness / 2,
    sep - thickness / 2,
    0,
    -fullWidth / 2 - thickness,
)
caliperStops = cq.Workplane()

# Draw all vertical pieces first
for ii in range(numMeasPoints):
    # Basic frame
    result += thickLine(
        -(ii + 1) * sep + thickness / 2,
        -(ii + 1) * sep + thickness / 2,
        -sep,
        0,
    )
    caliperStops += thickLine(
        -(ii + 1) * sep + thickness / 2 + stopGap / 2,
        -(ii + 1) * sep + thickness / 2 + stopGap / 2,
        0,
        sep / 2 - thickness / 4,
        thickness=thickness - stopGap,
    )

    # Exterior caliper stops
    result += thickLine(
        -(ii + 1) * sep - thickness / 2,
        -(ii + 1) * sep - thickness / 2,
        0,
        sep,
    )
    result += thickLine(
        -(ii + 1) * sep - thickness / 2 - stopGap / 2,
        -(ii + 1) * sep - thickness / 2 - stopGap / 2,
        -sep / 2 + thickness / 4 + caliperWidth,
        0,
        thickness=thickness - stopGap,
    )

    result += thickLine(
        (ii + 1) * sep + thickness / 2,
        (ii + 1) * sep + thickness / 2,
        0,
        sep,
    )
    result += thickLine(
        (ii + 1) * sep + thickness / 2 + stopGap / 2,
        (ii + 1) * sep + thickness / 2 + stopGap / 2,
        0,
        -sep / 2 + thickness / 4 + caliperWidth,
        thickness=thickness - stopGap,
    )

    result += thickLine(
        (ii + 1) * sep - thickness / 2,
        (ii + 1) * sep - thickness / 2,
        -sep,
        0,
    )
    caliperStops += thickLine(
        (ii + 1) * sep - thickness / 2 - stopGap / 2,
        (ii + 1) * sep - thickness / 2 - stopGap / 2,
        sep / 2 - thickness / 4,
        sep,
        thickness=thickness - stopGap,
    )


# up til now everything has been vertical
# rotate and mirror to make the horizontal measure points
result += result.rotate((0, 0, 0), (0, 0, 1), -90).mirror((0, 1, 0), (0, 0, 0))
# Caliper stops shouldn't be mirrored
caliperStops += caliperStops.rotate((0, 0, 0), (0, 0, 1), -90)
result += caliperStops

# diagonal caliper stops
diag = thickLine(0, 0, 0, fullWidth / 2 + thickness)

diag += thickLine(-diagWidth, -diagWidth, 0, fullWidth / 2)
# Top left
for ii in range(numMeasPoints - 1):
    diag += thickLine(
        -diagWidth,
        0,
        (ii + 2) * sep - thickness / 2,
        (ii + 2) * sep - thickness / 2,
    )
    diag += thickLine(
        -diagWidth / 2 - thickness / 4 + caliperWidth,
        0,
        (ii + 2) * sep + thickness / 2 + stopGap / 2,
        (ii + 2) * sep + thickness / 2 + stopGap / 2,
        thickness=thickness - stopGap,
    )

# Other four corners
diag += diag.mirror((0, 1, 0), (0, 0, 0))
diag += diag.rotate((0, 0, 0), (0, 0, 1), 90)

# rotate the whole thing and cut out the central frame
diag = diag.rotate((0, 0, 0), (0, 0, 1), 45)
diag -= thickLine(
    0, 0, -fullWidth / 2 - thickness, fullWidth / 2 + thickness, thickness=sep * 2
) + thickLine(-fullWidth / 2, fullWidth / 2, 0, 0, thickness=sep * 2)

result += diag

# Center circle that indicates orientation
center = (
    cq.Workplane()
    .lineTo(0, sep / 3)
    .threePointArc((-sep / 3, 0), (sep / 3, 0))
    .close()
    .extrude(height)
)


if fightElephantFoot:
    result = result.faces("+Z").chamfer(0.4, 0.4)
    result = result.faces("-Z").chamfer(0.4, 0.4)
    center = center.faces("+Z").chamfer(0.4, 0.4)
    center = center.faces("-Z").chamfer(0.4, 0.4)

result += center
result -= (
    cq.Workplane()
    .lineTo(0, thickness / 2)
    .threePointArc((-thickness / 2, 0), (thickness / 2, 0))
    .close()
    .extrude(height)
    .translate((0, 0, height - 1))
)

wd = os.getcwd()
exporters.export(result, f"{wd}/calistar_{fullWidth}x{numMeasPoints}.stl")
exporters.export(result, f"{wd}/calistar_{fullWidth}x{numMeasPoints}.step")
