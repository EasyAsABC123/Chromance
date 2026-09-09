"""CPU depth-buffer rendering of CAD triangles, with matplotlib captions.

Per-pixel depth avoids misleading painter-sort artifacts on concave CAD solids.
No display or GPU service is needed.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
import numpy as np
import trimesh

PALETTE = ["#476b86", "#e3a74e", "#518c7c", "#b1bac4", "#9675aa", "#7198c3"]


def _rasterize(meshes, elevation, azimuth, width=1600, height=950):
    az, el = np.radians([azimuth, elevation])
    camera = np.array([np.cos(el)*np.cos(az), np.cos(el)*np.sin(az), np.sin(el)])
    right = np.array([-np.sin(az), np.cos(az), 0.0])
    up = np.cross(camera, right)
    basis = np.stack([right, up, camera], axis=1)
    vertices = np.concatenate([m.vertices for _, m in meshes])
    projected = vertices @ basis
    lower, upper = projected[:, :2].min(axis=0), projected[:, :2].max(axis=0)
    scale = min((width-120)/max(upper[0]-lower[0], 1), (height-90)/max(upper[1]-lower[1], 1))
    center = (upper+lower)/2
    background = np.array(to_rgb("#f4f5f6"))
    pixels = np.broadcast_to(background, (height, width, 3)).copy()
    depth = np.full((height, width), -np.inf)
    light = (camera + np.array([-0.5, -0.3, 1.0])); light /= np.linalg.norm(light)
    for color, mesh in meshes:
        v = mesh.vertices @ basis
        xy = (v[:, :2]-center)*scale
        xy[:, 0] += width/2; xy[:, 1] = height/2-xy[:, 1]
        rgb = np.array(to_rgb(color))
        for face, normal in zip(mesh.faces, mesh.face_normals):
            a, b, c = xy[face]
            xmin = max(0, int(np.floor(min(a[0], b[0], c[0]))))
            xmax = min(width-1, int(np.ceil(max(a[0], b[0], c[0]))))
            ymin = max(0, int(np.floor(min(a[1], b[1], c[1]))))
            ymax = min(height-1, int(np.ceil(max(a[1], b[1], c[1]))))
            if xmin > xmax or ymin > ymax:
                continue
            den = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(den) < 1e-9:
                continue
            yy, xx = np.mgrid[ymin:ymax+1, xmin:xmax+1]
            xx = xx+0.5; yy = yy+0.5
            w0 = ((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
            w1 = ((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den
            w2 = 1-w0-w1
            inside = (w0 >= -1e-9) & (w1 >= -1e-9) & (w2 >= -1e-9)
            z = w0*v[face[0], 2]+w1*v[face[1], 2]+w2*v[face[2], 2]
            patch_depth = depth[ymin:ymax+1, xmin:xmax+1]
            visible = inside & (z > patch_depth)
            patch_depth[visible] = z[visible]
            shade = 0.53 + 0.44*max(float(normal @ light), 0)
            pixels[ymin:ymax+1, xmin:xmax+1][visible] = rgb*shade
    return pixels


def render(parts, output, title="FDM CAD / geometry preview", subtitle="", elevation=27, azimuth=-55):
    meshes, legend = [], []
    for index, (name, shape) in enumerate(parts.items()):
        vertices, faces = shape.tessellate(0.03, 0.1)
        mesh = trimesh.Trimesh(vertices=[list(v) for v in vertices], faces=faces, process=True)
        # Winding normalization is display-only; exports are separately verified.
        mesh.fix_normals(multibody=True)
        color = PALETTE[index % len(PALETTE)]
        meshes.append((color, mesh))
        legend.append(plt.Rectangle((0, 0), 1, 1, color=color, label=name.replace("_", " ")))
    pixels = _rasterize(meshes, elevation, azimuth)
    fig = plt.figure(figsize=(13.6, 10.2), dpi=140, facecolor="#f4f5f6")
    ax = fig.add_axes((0.02, 0.15, 0.96, 0.69))
    ax.imshow(pixels); ax.axis("off")
    fig.text(0.055, 0.93, title, size=22, weight="bold", color="#253343")
    fig.text(0.055, 0.89, subtitle, size=11, color="#536171")
    verts = np.concatenate([m.vertices for _, m in meshes])
    dimensions = verts.max(axis=0)-verts.min(axis=0)
    fig.text(0.055, 0.105, "Envelope: " + " × ".join(f"{x:.1f}" for x in dimensions) + " mm  (X × Y × Z)",
             size=11, color="#536171")
    fig.legend(handles=legend, loc="lower center", ncol=min(len(legend), 4),
               frameon=False, bbox_to_anchor=(0.5, 0.035), fontsize=10)
    fig.text(0.055, 0.012, "Actual CAD geometry • millimeters • physical fit and strength not yet tested", size=9, color="#77818b")
    fig.savefig(output, facecolor=fig.get_facecolor()); plt.close(fig)
