#!/usr/bin/env python3
"""Montage « Le loup et les démons » : voix off améliorée + illustrations + personnage masqué + sous-titres."""
import json, os, subprocess, re

ICI = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(ICI, "..", "..", "assets", "personnage")
I = os.path.join(ICI, "illustrations")
TMP = os.path.join(ICI, "tmp")
os.makedirs(TMP, exist_ok=True)
W, H, FPS = 1080, 1920, 30

def sh(cmd):
    subprocess.run(cmd, check=True)

# ---------- 1. Voix off améliorée ----------
VOIX = os.path.join(TMP, "voix_propre.wav")
sh(["ffmpeg", "-loglevel", "error", "-y", "-i", os.path.join(ICI, "source", "voix_brute.wav"), "-af",
    "highpass=f=80,lowpass=f=13000,afftdn=nf=-28:tn=1,"
    "equalizer=f=200:t=q:w=1:g=-2,equalizer=f=3500:t=q:w=1.2:g=3,"
    "acompressor=threshold=-20dB:ratio=3:attack=5:release=80:makeup=2,"
    "loudnorm=I=-14:TP=-1.5:LRA=9", "-ar", "48000", VOIX])

# ---------- 2. Plan de montage (début, fin en secondes) ----------
# type: img (illustration), perso (personnage masqué), vid (clip vidéo)
# look: nb = noir et blanc gravure, sombre = photo désaturée sombre, chaud = couleurs du personnage
PLAN = [
    (0.0,  3.0,  "vid",   "loups_vicart.webm", 15.0, "sombre"),
    (3.0,  6.3,  "perso", "hd_bras_ouverts_v1.webp", "in", "chaud"),
    (6.3,  9.05, "perso", "pose3_reflexion_livre.png", "out", "chaud"),
    (9.05, 11.4, "vid",   "loups_vicart.webm", 19.0, "sombre"),
    (11.4, 14.7, "img",   "Gustave_Doré_-_Chant_22._Calcabrina_and_Alichino_(c._1880).jpg", "out", "nb"),
    (14.7, 17.4, "perso", "pose6_globe.png", "in", "chaud"),
    (17.4, 21.55,"vid",   "loups_vicart.webm", 10.0, "sombre"),
    (21.55,23.35,"img",   "8-Mile_Pack_wolf_pups_(15245339149).jpg", "in", "sombre"),
    (23.35,26.25,"img",   "Yellowstone_Delta_Pack_wolf_(15273417887).jpg", "out", "sombre"),
    (26.25,28.75,"vid",   "loups_vicart.webm", 23.0, "sombre"),
    (28.75,31.6, "img",   "Alpha_female,_Canyon_Pack_(27399813305).jpg", "in", "sombre"),
    (31.6, 35.0, "perso", "hd_bras_ouverts_v2.webp", "out", "chaud"),
    (35.0, 39.05,"img",   "Yellowstone_Delta_Pack_wolf_(15273417887).jpg", "in", "sombre"),
    (39.05,40.65,"perso", "pose5_pointe_doigt.png", "in", "chaud"),
    (40.65,44.3, "img",   "Varney_the_Vampire_or_the_Feast_of_Blood.jpg", "in", "nb"),
    (44.3, 47.35,"img",   "The_Werewolf_or_the_Cannibal_MET_DP842190.jpg", "out", "nb"),
    (47.35,50.65,"perso", "pose2_explique.png", "in", "chaud"),
    (50.65,54.5, "img",   "Ethiopian_wolf_(Canis_simensis_citernii)_head.jpg", "out", "sombre"),
    (54.5, 58.55,"img",   "Quran_page_-_Al-Baqara_Sura_-_Egyptian_National_Library.jpg", "in", "chaud"),
    (58.55,60.0, "perso", "pose4_bras_ouverts.png", "in", "chaud"),
    (60.0, 64.0, "perso", "hd_bras_ouverts_v1.webp", "out", "chaud"),
]

LOOK = {
    "nb": "hue=s=0,eq=contrast=1.25:brightness=-0.04,vignette=PI/4",
    "sombre": "eq=saturation=0.55:contrast=1.15:brightness=-0.05,colorbalance=bs=0.06:bm=0.03,vignette=PI/4",
    "chaud": "eq=contrast=1.08:saturation=1.1,vignette=PI/5",
}

def clip_image(src, dur, sens, look, out):
    n = int(round(dur * FPS))
    z0, z1 = (1.0, 1.18) if sens == "in" else (1.18, 1.0)
    z = f"{z0}+({z1}-{z0})*on/{max(n-1,1)}"
    vf = (f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},"
          f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps={FPS},"
          f"{LOOK[look]},format=yuv420p")
    sh(["ffmpeg", "-loglevel", "error", "-y", "-loop", "1", "-i", src, "-vf", vf,
        "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", out])

def clip_video(src, debut, dur, look, out):
    n = int(round(dur * FPS))
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},"
          f"{LOOK[look]},format=yuv420p")
    sh(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(debut), "-i", src, "-an", "-vf", vf,
        "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", out])

morceaux = []
for k, (a, b, typ, f, opt, look) in enumerate(PLAN):
    out = os.path.join(TMP, f"c{k:02d}.mp4")
    if typ == "vid":
        clip_video(os.path.join(I, f), opt, b - a, look, out)
    else:
        clip_image(os.path.join(P if typ == "perso" else I, f), b - a, opt, look, out)
    morceaux.append(out)
    print(f"plan {k+1}/{len(PLAN)} ok")

liste = os.path.join(TMP, "liste.txt")
open(liste, "w").write("".join(f"file '{m}'\n" for m in morceaux))
IMAGES = os.path.join(TMP, "images.mp4")
sh(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", liste, "-c", "copy", IMAGES])

# ---------- 3. Sous-titres (2-3 mots, jaunes, centrés) ----------
CORR = {"current": "Coran", "ventre": "vampires", "mal": "mâle", "main": "mort"}
mots = []
for seg in json.load(open(os.path.join(ICI, "source", "voix_brute.json")))["segments"]:
    for w in seg["words"]:
        t = w["word"].strip()
        cle = re.sub(r"[^\wà-ÿ]", "", t.lower())
        if cle in CORR:
            t = t.replace(re.sub(r"[^\wà-ÿ]", "", t), CORR[cle])
        mots.append((w["start"], w["end"], t))
# colle les mots à apostrophe (l', t', qu') au mot suivant
fus = []
for m in mots:
    if fus and (re.search(r"['’]$", fus[-1][2]) or re.match(r"['’]", m[2])):
        a = fus.pop(); m = (a[0], m[1], a[2] + m[2])
    fus.append(m)
mots = fus
# « qui ne commet pas à l'inceste » -> « qui ne commet pas l'inceste »
mots = [m for i, m in enumerate(mots) if not (m[2] == "à" and i + 1 < len(mots) and "inceste" in mots[i + 1][2])]
mots = [(m[0], m[1], "certaines") if m[2] == "certains" and i + 1 < len(mots) and mots[i + 1][2].startswith("traditions") else m for i, m in enumerate(mots)]
fus = []
for m in mots:
    if fus and m[2].startswith("-"):
        a = fus.pop(); m = (a[0], m[1], a[2] + m[2])
    fus.append(m)
mots = fus
print("CONTROLE:", " ".join(m[2] for m in mots))

def ts(s):
    return f"{int(s//3600)}:{int(s%3600//60):02d}:{s%60:05.2f}"

groupes, cur = [], []
for m in mots:
    cur.append(m)
    if len(cur) == 3 or re.search(r"[.,?!]$", m[2]):
        groupes.append(cur); cur = []
if cur: groupes.append(cur)

ass = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "",
       "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: Sous,Anton,108,&H0000E5FF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,1,0,1,6,3,5,60,60,0,1",
       "Style: Titre,Anton,120,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,2,0,1,7,4,8,60,60,260,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
for i, g in enumerate(groupes):
    debut = g[0][0]
    fin = groupes[i + 1][0][0] if i + 1 < len(groupes) else g[-1][1] + 0.4
    fin = min(fin, g[-1][1] + 0.6)
    txt = " ".join(x[2] for x in g).upper()
    ass.append(f"Dialogue: 0,{ts(debut)},{ts(fin)},Sous,,0,0,0,,{{\\fscx80\\fscy80\\t(0,90,\\fscx100\\fscy100)}}{txt}")
ass.append(r"Dialogue: 1,0:00:00.00,0:00:03.00,Titre,,0,0,0,,{\fad(0,250)\c&H0000E5FF&}LE LOUP{\c&HFFFFFF&}\NTUEUR DE DÉMONS ?")
ass.append(r"Dialogue: 1,0:01:00.00,0:01:04.00,Titre,,0,0,0,,{\fad(250,0)}LIKE • COMMENTE\N{\c&H0000E5FF&}ABONNE-TOI")
SUB = os.path.join(TMP, "sous.ass")
open(SUB, "w").write("\n".join(ass) + "\n")

# ---------- 4. Assemblage final ----------
FINAL = os.path.join(ICI, "loup_demons.mp4")
sh(["ffmpeg", "-loglevel", "error", "-y", "-i", IMAGES, "-i", VOIX,
    "-vf", f"ass={SUB},fade=t=in:st=0:d=0.3,fade=t=out:st=63.4:d=0.6",
    "-af", "afade=t=out:st=63.4:d=0.6",
    "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
    "-c:a", "aac", "-b:a", "192k", "-t", "64", "-movflags", "+faststart", FINAL])
print("FINI", FINAL)
