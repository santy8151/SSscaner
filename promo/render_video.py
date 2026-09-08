"""Original motion graphics + actual dashboard capture. No OEM/AI claims.
Install optional media dependencies: python -m pip install pillow imageio-ffmpeg
Run from any directory after artifacts/dashboard.png has been captured.
"""
import array
import math
import subprocess
import wave
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
W, H, FPS, DURATION = 1080, 1920, 24, 24
MINT = (106, 233, 193)
WHITE = (235, 245, 243)
MUTED = (153, 179, 178)
font_dir = Path("C:/Windows/Fonts")


def font(size, bold=False):
    return ImageFont.truetype(str(font_dir / ("segoeuib.ttf" if bold else "segoeui.ttf")), size)


background = Image.new("RGB", (W, H))
draw = ImageDraw.Draw(background)
for y in range(H):
    glow = math.exp(-((y - 1150) / 650) ** 2)
    draw.line((0, y, W, y), fill=(int(9 + 6 * glow), int(19 + 23 * glow), int(25 + 13 * glow)))
for x in range(0, W, 90):
    draw.line((x, 0, x, H), fill=(22, 41, 46))
for y in range(0, H, 90):
    draw.line((0, y, W, y), fill=(22, 41, 46))

capture = Image.open(ROOT / "artifacts/investor-neural.png").convert("RGB")
capture.thumbnail((960, 680), Image.Resampling.LANCZOS)
scenes = [
    (["Entiende el sistema.", "Decide con", "evidencia."], "SSScanner", ["Una nueva base técnica para", "vehículos y maquinaria."]),
    (["Configura.", "Entrena.", "Compara."], "UN LABORATORIO PARA EXPERIMENTAR", ["Modelos experimentales con datos SAMPLE.", "Batch size · Épocas · Learning rate"]),
    (["La calibración", "empieza en", "la fuente."], "CRITERIO TÉCNICO DESDE EL DISEÑO", ["Sin ficha OEM validada:", "SOURCE_REQUIRED. Sin parámetros inventados."]),
    (["El próximo paso", "de tu taller", "empieza aquí."], "CONOCE SSScanner BETA", ["Explora el laboratorio de desarrollo.", "Construyamos el diagnóstico del futuro."]),
]


def frame(index):
    t = index / FPS
    scene = min(3, int(t / 6))
    local = t % 6
    progress = min(1, local / 0.7)
    offset = round(35 * (1 - progress) ** 3)
    image = background.copy()
    d = ImageDraw.Draw(image)
    d.rounded_rectangle((60, 75, 140, 155), radius=16, fill=(29, 69, 57), outline=MINT, width=2)
    d.text((77, 90), "SS", font=font(35, True), fill=MINT)
    d.text((165, 79), "SSScanner", font=font(48, True), fill=WHITE)
    d.rounded_rectangle((790, 87, 1018, 138), radius=12, outline=(82, 119, 100), width=2)
    d.text((810, 95), "BETA / 0.3", font=font(24, True), fill=MINT)
    title, eyebrow, lines = scenes[scene]
    if scene == 0:
        eyebrow = "INGENIERÍA CON EVIDENCIA"
    d.text((64, 222), eyebrow, font=font(24, True), fill=MINT)
    for row, text in enumerate(title):
        d.text((60, 293 + row * 100 + offset), text, font=font(76, True), fill=MINT if row == 2 else WHITE)
    d.rounded_rectangle((48, 692, 1032, 1490), radius=25, fill=(12, 23, 29), outline=(59, 104, 88), width=2)
    d.text((78, 716), "INTERFAZ REAL · SESIÓN DE DEMOSTRACIÓN", font=font(22, True), fill=MUTED)
    image.paste(capture, ((W - capture.width) // 2, 780 + (700 - capture.height) // 2))
    d = ImageDraw.Draw(image)
    for row, text in enumerate(lines):
        size = 33 if len(text) < 45 else 28
        d.text((64, 1540 + row * 55), text, font=font(size, row == 0), fill=WHITE if row == 0 else MUTED)
    if scene == 3:
        d.rounded_rectangle((64, 1695, 1016, 1768), radius=12, fill=MINT)
        d.text((278, 1708), "CONOCE EL PROYECTO", font=font(32, True), fill=(9, 39, 29))
    else:
        points = [(64 + x, 1730 + 18 * math.sin(x / 32 - t * 3) * math.sin(x / 140)) for x in range(952)]
        d.line(points, fill=MINT, width=3)
    d.text((64, 1805), "BETA técnica · Hardware pendiente de validar.", font=font(23), fill=MUTED)
    for marker in range(4):
        start = 64 + marker * 245
        d.rounded_rectangle((start, 1865, start + 224, 1871), radius=3, fill=(49, 71, 73))
        if marker <= scene:
            fraction = 1 if marker < scene else local / 6
            d.rounded_rectangle((start, 1865, start + max(1, round(224 * fraction)), 1871), radius=3, fill=MINT)
    fade = min(1, t / 0.35, (DURATION - t) / 0.5)
    if fade < 1:
        image = Image.blend(Image.new("RGB", (W, H), (9, 19, 25)), image, max(0, fade))
    return image


def soundtrack():
    rate = 44100
    samples = array.array("h")
    chords = [(130.81, 164.81, 196), (110, 130.81, 164.81), (87.31, 110, 130.81), (98, 123.47, 146.83)]
    for index in range(rate * DURATION):
        t = index / rate
        chord = chords[min(3, int(t / 6))]
        fade = min(1, t / 1.5, (DURATION - t) / 2)
        local = t % 0.625
        pad = sum(math.sin(2 * math.pi * note * t) for note in chord) / 3
        pulse = math.sin(2 * math.pi * chord[int(t * 1.6) % 3] * 4 * t) * math.exp(-local * 12)
        kick = math.sin(2 * math.pi * (45 * local + 2 * (1 - math.exp(-local * 25)))) * math.exp(-local * 28)
        sample = int(32767 * fade * (0.09 * pad + 0.045 * pulse + 0.11 * kick))
        samples.append(sample)
    path = HERE / "original-soundtrack.wav"
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(rate)
        output.writeframes(samples.tobytes())
    return path


if __name__ == "__main__":
    audio = soundtrack()
    output = HERE / "SSScanner-promo-BETA.mp4"
    command = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-f", "rawvideo", "-vcodec", "rawvideo", "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS), "-i", "-", "-i", str(audio), "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(output)]
    with (HERE / "render.log").open("wb") as log:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=log)
        for index in range(FPS * DURATION):
            process.stdin.write(frame(index).tobytes())
        process.stdin.close()
        if process.wait() != 0:
            raise SystemExit("FFmpeg failed; see render.log")
    frame(8 * FPS).save(HERE / "poster.png")
    print(f"Created {output} · {DURATION}s · {W}x{H} · {FPS}fps")
