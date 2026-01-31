import bpy
import sys

# Convert blend files to glb.
# call this like so
#
# blender -b --python blener_export.py -- filename.glb
if len(sys.argv) < 7:
    print("didn't get a name to export to: skipping")
    exit(1)

outname = sys.argv[6]

# see https://docs.blender.org/api/current/bpy.ops.export_scene.html#bpy.ops.export_scene.gltf
# for full options
bpy.ops.export_scene.gltf(
    filepath=outname,
    export_format="GLB",
    # export_apply=True,  # Apply modifiers
    # For higher res / compressable models
    # export_draco_mesh_compression_enable=True,
    # export_draco_mesh_compression_level=7
    export_materials='EXPORT',
    export_cameras=False,
    export_lights=False
)
print("exported")
