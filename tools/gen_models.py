#!/usr/bin/env python3
"""Cerceveli tablo icin gercek olculu GLB (Android/WebXR) ve USDZ (iPhone Quick Look, dikey yuzey capasi) uretir."""
import struct, json, io, zipfile, os
from PIL import Image

SRC = "/private/tmp/claude-501/-Users-yusufaltanpehlivan-claude/692f57a5-68e2-4602-af76-30fcfd93954f/scratchpad/out"
DST = "/Users/yusufaltanpehlivan/claude/odanda-gor-demo"
crops = json.load(open(f"{SRC}/crops.json"))
EN_M = 0.50      # dis genislik 50 cm
DERINLIK_M = 0.03  # cerceve derinligi varsayimi 3 cm

def srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def box_geometry(W, H, D, z0=0.0):
    """Dik duran ince kutu. Arka yuz z=z0 (duvar), on yuz z=z0+D (izleyiciye bakar). Saat yonu tersi sarim, disa normaller."""
    zF = z0 + D
    front = [(-W/2, -H/2, zF), (W/2, -H/2, zF), (W/2, H/2, zF), (-W/2, H/2, zF)]
    front_n = [(0.0, 0.0, 1.0)] * 4
    uv_gltf = [(0, 1), (1, 1), (1, 0), (0, 0)]   # glTF: (0,0) sol ust
    uv_usd = [(0, 0), (1, 0), (1, 1), (0, 1)]    # USD: (0,0) sol alt
    faces = [
        ([( W/2, -H/2, z0), (-W/2, -H/2, z0), (-W/2,  H/2, z0), ( W/2,  H/2, z0)], (0.0, 0.0, -1.0)),  # arka
        ([(-W/2, -H/2, z0), (-W/2, -H/2, zF), (-W/2,  H/2, zF), (-W/2,  H/2, z0)], (-1.0, 0.0, 0.0)),  # sol
        ([( W/2, -H/2, zF), ( W/2, -H/2, z0), ( W/2,  H/2, z0), ( W/2,  H/2, zF)], (1.0, 0.0, 0.0)),   # sag
        ([(-W/2,  H/2, zF), ( W/2,  H/2, zF), ( W/2,  H/2, z0), (-W/2,  H/2, z0)], (0.0, 1.0, 0.0)),   # ust
        ([(-W/2, -H/2, z0), ( W/2, -H/2, z0), ( W/2, -H/2, zF), (-W/2, -H/2, zF)], (0.0, -1.0, 0.0)),  # alt
    ]
    body_pos, body_n = [], []
    for verts, n in faces:
        body_pos += verts; body_n += [n] * 4
    return front, front_n, uv_gltf, uv_usd, body_pos, body_n

def pad4(b, fill=b"\0"):
    return b + fill * ((4 - len(b) % 4) % 4)

def quad_tris(nq):
    return [i for q in range(nq) for i in (4*q, 4*q+1, 4*q+2, 4*q, 4*q+2, 4*q+3)]

def build_glb(tex, W, H, D, side_rgb):
    front, front_n, uv_g, _, body_pos, body_n = box_geometry(W, H, D, z0=0.0)
    f32 = lambda arr: struct.pack("<%df" % (len(arr) * len(arr[0])), *[c for v in arr for c in v])
    u16 = lambda arr: struct.pack("<%dH" % len(arr), *arr)
    blobs = [f32(front), f32(front_n), f32(uv_g), u16(quad_tris(1)), f32(body_pos), f32(body_n), u16(quad_tris(5)), tex]
    targets = [34962, 34962, 34962, 34963, 34962, 34962, 34963, None]
    views, binbuf = [], b""
    for b, t in zip(blobs, targets):
        off = len(binbuf); binbuf += pad4(b)
        bv = {"buffer": 0, "byteOffset": off, "byteLength": len(b)}
        if t: bv["target"] = t
        views.append(bv)
    mm = lambda arr: ([min(v[i] for v in arr) for i in range(3)], [max(v[i] for v in arr) for i in range(3)])
    fmin, fmax = mm(front); bmin, bmax = mm(body_pos)
    lin = [round(srgb_to_linear(c), 4) for c in side_rgb]
    gltf = {
        "asset": {"version": "2.0", "generator": "odanda-gor-demo"},
        "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [{"mesh": 0, "name": "Tablo"}],
        "meshes": [{"name": "Tablo", "primitives": [
            {"attributes": {"POSITION": 0, "NORMAL": 1, "TEXCOORD_0": 2}, "indices": 3, "material": 0},
            {"attributes": {"POSITION": 4, "NORMAL": 5}, "indices": 6, "material": 1}]}],
        "materials": [
            {"name": "On", "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}, "metallicFactor": 0.0, "roughnessFactor": 0.7}},
            {"name": "Govde", "pbrMetallicRoughness": {"baseColorFactor": lin + [1.0], "metallicFactor": 0.2, "roughnessFactor": 0.55}}],
        "textures": [{"sampler": 0, "source": 0}],
        "images": [{"bufferView": 7, "mimeType": "image/jpeg"}],
        "samplers": [{"magFilter": 9729, "minFilter": 9987, "wrapS": 33071, "wrapT": 33071}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3", "min": fmin, "max": fmax},
            {"bufferView": 1, "componentType": 5126, "count": 4, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5126, "count": 4, "type": "VEC2"},
            {"bufferView": 3, "componentType": 5123, "count": 6, "type": "SCALAR"},
            {"bufferView": 4, "componentType": 5126, "count": 20, "type": "VEC3", "min": bmin, "max": bmax},
            {"bufferView": 5, "componentType": 5126, "count": 20, "type": "VEC3"},
            {"bufferView": 6, "componentType": 5123, "count": 30, "type": "SCALAR"}],
        "bufferViews": views, "buffers": [{"byteLength": len(pad4(binbuf))}]}
    js = pad4(json.dumps(gltf, separators=(",", ":")).encode(), b" ")
    binbuf = pad4(binbuf)
    total = 12 + 8 + len(js) + 8 + len(binbuf)
    return (b"glTF" + struct.pack("<II", 2, total) + struct.pack("<II", len(js), 0x4E4F534A) + js
            + struct.pack("<II", len(binbuf), 0x004E4942) + binbuf)

def fmt3(v): return "(%.6g, %.6g, %.6g)" % tuple(v)
def fmt2(v): return "(%.6g, %.6g)" % tuple(v)

def build_usda(W, H, D, side_rgb, alignment="vertical", rotate_flat=False):
    front, front_n, _, uv_u, body_pos, body_n = box_geometry(W, H, D, z0=0.0)
    if rotate_flat:  # X ekseninde -90 derece: on yuz +Y'ye bakar (ARKit ham duzlem cercevesi hipotezi icin test)
        R = lambda p: (p[0], p[2], -p[1])
        front = [R(p) for p in front]; front_n = [R(p) for p in front_n]
        body_pos = [R(p) for p in body_pos]; body_n = [R(p) for p in body_n]
    lin = [srgb_to_linear(c) for c in side_rgb]
    def mesh(name, pos, nrm, uv, mat, nq):
        idx = ", ".join(str(i) for i in range(4 * nq))
        s = f'''			def Mesh "{name}" (
				prepend apiSchemas = ["MaterialBindingAPI"]
			)
			{{
				int[] faceVertexCounts = [{", ".join(["4"] * nq)}]
				int[] faceVertexIndices = [{idx}]
				normal3f[] normals = [{", ".join(fmt3(n) for n in nrm)}] (
					interpolation = "vertex"
				)
				point3f[] points = [{", ".join(fmt3(p) for p in pos)}]
'''
        if uv:
            s += f'''				texCoord2f[] primvars:st = [{", ".join(fmt2(t) for t in uv)}] (
					interpolation = "vertex"
				)
'''
        s += f'''				uniform token subdivisionScheme = "none"
				rel material:binding = </Materials/{mat}>
			}}
'''
        return s
    usda = f'''#usda 1.0
(
	customLayerData = {{
		string creator = "Odanda Gor demo"
	}}
	defaultPrim = "Root"
	metersPerUnit = 1
	upAxis = "Y"
)

def Xform "Root"
{{
	def Scope "Scenes" (
		kind = "sceneLibrary"
	)
	{{
		def Xform "Scene" (
			customData = {{
				bool preliminary_collidesWithEnvironment = 0
				string sceneName = "Scene"
			}}
			sceneName = "Scene"
		)
		{{
			token preliminary:anchoring:type = "plane"
			token preliminary:planeAnchoring:alignment = "{alignment}"

{mesh("On", front, front_n, uv_u, "OnMat", 1)}
{mesh("Govde", body_pos, body_n, None, "GovdeMat", 5)}		}}
	}}
}}

def Scope "Materials"
{{
	def Material "OnMat"
	{{
		def Shader "PreviewSurface"
		{{
			uniform token info:id = "UsdPreviewSurface"
			color3f inputs:diffuseColor.connect = </Materials/OnMat/Texture_on.outputs:rgb>
			float inputs:roughness = 0.7
			float inputs:metallic = 0
			int inputs:useSpecularWorkflow = 0
			token outputs:surface
		}}
		def Shader "PrimvarReader_st"
		{{
			uniform token info:id = "UsdPrimvarReader_float2"
			float2 inputs:fallback = (0.0, 0.0)
			string inputs:varname = "st"
			float2 outputs:result
		}}
		def Shader "Texture_on"
		{{
			uniform token info:id = "UsdUVTexture"
			asset inputs:file = @textures/on.jpg@
			float2 inputs:st.connect = </Materials/OnMat/PrimvarReader_st.outputs:result>
			token inputs:sourceColorSpace = "sRGB"
			token inputs:wrapS = "clamp"
			token inputs:wrapT = "clamp"
			float outputs:r
			float outputs:g
			float outputs:b
			float3 outputs:rgb
		}}
		token outputs:surface.connect = </Materials/OnMat/PreviewSurface.outputs:surface>
	}}
	def Material "GovdeMat"
	{{
		def Shader "PreviewSurface"
		{{
			uniform token info:id = "UsdPreviewSurface"
			color3f inputs:diffuseColor = {fmt3(lin)}
			float inputs:roughness = 0.55
			float inputs:metallic = 0.2
			int inputs:useSpecularWorkflow = 0
			token outputs:surface
		}}
		token outputs:surface.connect = </Materials/GovdeMat/PreviewSurface.outputs:surface>
	}}
}}
'''
    return usda.encode("utf-8")

def write_usdz(path, files):
    """Sikistirmasiz zip, her dosyanin verisi 64 bayta hizali (Apple USDZ sarti)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_STORED) as zf:
        for name, data in files:
            zi = zipfile.ZipInfo(name, date_time=(2026, 9, 7, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_STORED
            zi.external_attr = 0o644 << 16
            hdr_off = buf.tell()
            base = hdr_off + 30 + len(name.encode("utf-8")) + 4
            pad = (64 - base % 64) % 64
            zi.extra = struct.pack("<HH", 0x1986, pad) + b"\0" * pad
            zf.writestr(zi, data)
    open(path, "wb").write(buf.getvalue())

def check_usdz_alignment(path):
    d = open(path, "rb").read(); off = 0; ok = True; names = []
    while d[off:off+4] == b"PK\x03\x04":
        nlen, xlen = struct.unpack_from("<HH", d, off + 26)
        csize = struct.unpack_from("<I", d, off + 18)[0]
        data_off = off + 30 + nlen + xlen
        names.append((d[off+30:off+30+nlen].decode(), data_off, data_off % 64))
        ok &= (data_off % 64 == 0)
        off = data_off + csize
    return ok, names

if __name__ == "__main__":
    os.makedirs(f"{DST}/models", exist_ok=True)
    rapor = {}
    for slug, info in crops.items():
        aspect = info["aspect"]; W = EN_M; H = round(W / aspect, 4); D = DERINLIK_M
        side = tuple(info["side_rgb"])
        tex = open(f"{SRC}/models/{slug}-tex.jpg", "rb").read()
        glb = build_glb(tex, W, H, D, side)
        open(f"{DST}/models/{slug}.glb", "wb").write(glb)
        write_usdz(f"{DST}/models/{slug}.usdz", [("model.usda", build_usda(W, H, D, side)), ("textures/on.jpg", tex)])
        ok, names = check_usdz_alignment(f"{DST}/models/{slug}.usdz")
        rapor[slug] = {"W_cm": W*100, "H_cm": round(H*100, 1), "D_cm": D*100, "glb_bytes": len(glb),
                       "usdz_bytes": os.path.getsize(f"{DST}/models/{slug}.usdz"), "usdz_hizali": ok, "girdiler": names}
        if slug == "eskitme-altin":
            write_usdz(f"{DST}/models/{slug}-yatik.usdz", [("model.usda", build_usda(W, H, D, side, rotate_flat=True)), ("textures/on.jpg", tex)])
    json.dump(rapor, open(f"{SRC}/models-rapor.json", "w"), indent=1)
    print(json.dumps(rapor, indent=1))
