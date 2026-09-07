import json, re, os
SP = "/private/tmp/claude-501/-Users-yusufaltanpehlivan-claude/692f57a5-68e2-4602-af76-30fcfd93954f/scratchpad"
DST = "/Users/yusufaltanpehlivan/claude/odanda-gor-demo"
tpl = open(f"{SP}/odanda-gor.template.html", encoding="utf-8").read()
bundle = json.load(open(f"{SP}/bundle.json"))
def render(variant, assets):
    s = tpl.replace("{{VARIANT}}", variant).replace("{{ASSETS_JSON}}", json.dumps(assets, ensure_ascii=False))
    if variant == "hosted":
        s = s.replace("{{HOSTED_ONLY}}", "").replace("{{/HOSTED_ONLY}}", "")
    else:
        s = re.sub(r"\{\{HOSTED_ONLY\}\}.*?\{\{/HOSTED_ONLY\}\}", "", s, flags=re.S)
    return s
# Artifact: tek dosya, gomulu veri
art = render("artifact", bundle)
open(f"{SP}/odanda-gor.html", "w", encoding="utf-8").write(art)
# Barindirilan: dosya yollari
paths = {}
for k in bundle:
    kind, name = k.split(":", 1)
    paths[k] = {"img": f"assets/{name}.webp", "thumb": f"assets/{name}-thumb.webp", "glb": f"models/{name}.glb", "usdz": f"models/{name}.usdz"}[kind]
hosted = ('<!doctype html>\n<html lang="tr">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n<meta name="theme-color" content="#EEF1F5">\n' 
          + render("hosted", paths) + '\n</body>\n</html>\n')
hosted = hosted.replace("</style>\n\n<div class=\"wrap\">", "</style>\n</head>\n<body>\n<div class=\"wrap\">", 1)
open(f"{DST}/index.html", "w", encoding="utf-8").write(hosted)
print("artifact:", round(os.path.getsize(f"{SP}/odanda-gor.html")/1024), "KB; hosted:", round(os.path.getsize(f"{DST}/index.html")/1024), "KB")
print("title ilk 8KB icinde:", "<title>" in art[:8192], "| hosted head/body:", hosted.count("<head>"), hosted.count("<body>"), hosted.count("</head>"))
