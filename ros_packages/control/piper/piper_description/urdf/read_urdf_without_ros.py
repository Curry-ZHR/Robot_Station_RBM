#!/bin/python3
from urdfpy import URDF

robot = URDF.load('piper_description.urdf')

print("Robot name:", robot.name)

for link in robot.links:
    print("Link:", link.name)
    if link.collision:
        print("  Collision geometry:", link.collision.geometry)

for joint in robot.joints:
    print("Joint:", joint.name)
    print("  Type:", joint.type)
    print("  Parent:", joint.parent)
    print("  Child:", joint.child)
