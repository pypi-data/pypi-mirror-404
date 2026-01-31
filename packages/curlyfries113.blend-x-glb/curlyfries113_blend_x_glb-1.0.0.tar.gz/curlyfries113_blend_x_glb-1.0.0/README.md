# blend-x-glb

Simple and handy CLI to convert a bunch of blends to GLBs.

## Installaion

blend-x-glb can be installed from pypi. With [uv]

```
uv tool install blend-x-glb
```

```
pip install
```

## Using the tool

Convert blend files into GLB using blender by calling the tool like this:

```bash
blend-x-glb ./your_blend_dir ./GLBs
```

It's that easy! Or if you prefer an interactive mode `blend-x-glb --ask`

This tries to use your system's blender: if blender is not installed converting
won't work.
