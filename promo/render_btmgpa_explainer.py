"""Original animated technician, EV, three displays and speech-synchronized mouth."""
import json
import math
import subprocess
import wave
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
W, H, FPS = 1280, 720, 24
MINT, WHITE, MUTED = '#79edc2', '#e6f7f0', '#95b6b0'
def font(size, bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf' if bold else 'C:/Windows/Fonts/segoeui.ttf', size)

scenes = json.loads((HERE/'btmgpa-story.json').read_text(encoding='utf-8'))
segments, cursor, audio_parts = [], 0, []
for i, scene in enumerate(scenes):
    with wave.open(str(HERE/'narration-v2'/f'scene-{i}.wav'),'rb') as f:
        rate, channels, width = f.getframerate(), f.getnchannels(), f.getsampwidth()
        assert channels == 1 and width == 2
        samples = np.frombuffer(f.readframes(f.getnframes()), dtype='<i2').copy()
    if i == 0: audio_rate=rate
    assert rate == audio_rate
    samples = np.concatenate([samples, np.zeros(int(rate*0.7),dtype=np.int16)])
    seconds = len(samples)/rate
    segments.append((cursor,cursor+seconds,scene,samples))
    cursor += seconds
    audio_parts.append(samples)
audio = np.concatenate(audio_parts)
with wave.open(str(HERE/'btmgpa-narration.wav'),'wb') as f:
    f.setnchannels(1); f.setsampwidth(2); f.setframerate(audio_rate); f.writeframes(audio.tobytes())

background = Image.new('RGB',(W,H),'#081916')
draw = ImageDraw.Draw(background)
for y in range(H):
    glow=math.exp(-((y-350)/260)**2)
    draw.line((0,y,W,y),fill=(int(8+9*glow),int(23+18*glow),int(22+17*glow)))
for x in range(400,1280,55): draw.line((x,125,x-160,585),fill='#17322c')
draw.rectangle((0,574,W,600),fill='#1a3630')
draw.line((40,109,1240,109),fill='#305048',width=1)

def wrap(text, draw, font_, max_width):
    lines=['']
    for word in text.split():
        candidate=(lines[-1]+' '+word).strip()
        if draw.textlength(candidate,font=font_)>max_width: lines.append(word)
        else: lines[-1]=candidate
    return lines

def frame(t):
    index=next((i for i,(_,end,_,_) in enumerate(segments) if t<end),len(segments)-1)
    start,end,scene,samples=segments[index];local=t-start
    begin=int(local*audio_rate);chunk=samples[begin:begin+int(audio_rate/FPS)].astype(float)
    amplitude=float(np.sqrt(np.mean(chunk**2))) if len(chunk) else 0
    mouth=min(13,int(amplitude/500))
    im=background.copy();d=ImageDraw.Draw(im)
    d.rounded_rectangle((38,24,92,78),12,fill=MINT)
    d.text((48,29),'SS',font=font(27,True),fill='#10271f')
    d.text((108,27),'Ssscaner',font=font(34,True),fill=WHITE)
    d.text((310,40),'BTMGPA / INGENIERÍA CON EVIDENCIA',font=font(15,True),fill=MINT)
    d.rounded_rectangle((1000,30,1240,73),10,outline='#588071')
    d.text((1020,40),'ANIMACIÓN CONCEPTUAL',font=font(14,True),fill=MINT)
    d.text((42,126),scene['title'],font=font(27,True),fill=WHITE)
    # Three instrument screens.
    for n,title in enumerate(['01  CIRCUITO TÉRMICO','02  OSCILOSCOPIO','03  VISIÓN DE LUCES']):
        x=480+n*250;y=196;active=n==scene['focus']
        d.rounded_rectangle((x,y,x+232,y+165),12,fill='#0a1c18',outline=MINT if active else '#416257',width=3 if active else 1)
        d.text((x+13,y+12),title,font=font(14,True),fill=MINT)
        if n==0:
            for k in range(2):
                cx=x+62+k*107;cy=y+85
                d.arc((cx-34,cy-34,cx+34,cy+34),135,405,fill='#52796a',width=6)
                ang=(-130+70*k+8*math.sin(t))*math.pi/180
                d.line((cx,cy,cx+27*math.cos(ang),cy+27*math.sin(ang)),fill=MINT,width=3)
                d.ellipse((cx-3,cy-3,cx+3,cy+3),fill=WHITE)
            d.text((x+20,y+133),'Esquema · sin lectura real',font=font(12),fill=MUTED)
        elif n==1:
            for h in range(4):d.line((x+15,y+46+h*22,x+216,y+46+h*22),fill='#244239')
            pts=[(x+15+j,y+92+24*math.sin(j/9-t*4)) for j in range(202)]
            d.line(pts,fill=MINT,width=2)
            d.text((x+15,y+138),'Señal ilustrativa',font=font(12),fill=MUTED)
        else:
            d.rounded_rectangle((x+40,y+53,x+190,y+104),13,fill='#91b5bb',outline=WHITE,width=2)
            d.polygon([(x+55,y+62),(x+170,y+62),(x+150,y+84),(x+65,y+84)],fill='#faf6c5')
            for xx,yy in [(x+31,y+45),(x+179,y+45),(x+31,y+108),(x+179,y+108)]:d.line((xx,yy,xx+22,yy),fill=MINT,width=3)
            d.text((x+20,y+132),'Modelo de luces por validar',font=font(12),fill=MUTED)
        d.line((x+116,y+165,x+116,390),fill='#43675b',width=4)
    # Stylized electric car, original vector geometry.
    d.ellipse((420,535,1100,585),fill='#06130f')
    d.polygon([(420,454),(478,430),(550,369),(807,369),(908,431),(1065,455),(1100,490),(1094,532),(435,532)],fill='#7c9ca6',outline='#b3d0d5')
    d.polygon([(555,385),(665,385),(665,434),(497,434)],fill='#163638')
    d.polygon([(680,385),(800,385),(874,434),(680,434)],fill='#193e40')
    d.line((678,382,678,513),fill='#4b6a72',width=3)
    d.line((440,471,1067,471),fill='#c6dee0',width=2)
    d.rounded_rectangle((617,447,650,452),2,fill='#143638')
    d.rounded_rectangle((800,447,833,452),2,fill='#143638')
    d.polygon([(1027,461),(1080,477),(1086,489),(1022,480)],fill='#f2f4c7')
    d.rounded_rectangle((547,493,904,524),7,fill='#183a30',outline=MINT,width=2)
    for k in range(12):d.rectangle((555+k*28,499,576+k*28,518),fill='#2b6953')
    d.text((701,536),'VEHÍCULO ELÉCTRICO',font=font(13,True),fill=MINT)
    for cx in [530,974]:
        d.ellipse((cx-42,495,cx+42,579),fill='#07120f',outline='#536b66',width=3)
        d.ellipse((cx-27,510,cx+27,564),fill='#42605b',outline='#b5c9c5',width=3)
        d.ellipse((cx-8,529,cx+8,545),fill='#91b5a7')
        for a in range(0,360,60):
            rad=math.radians(a);d.line((cx+10*math.cos(rad),537+10*math.sin(rad),cx+25*math.cos(rad),537+25*math.sin(rad)),fill='#afc8c2',width=3)
    # Service cart: no physical connection instructions, symbolic data path.
    d.rounded_rectangle((1113,399,1238,550),8,fill='#24433a',outline='#619d87',width=2)
    d.text((1125,417),'MÓDULO',font=font(14,True),fill=WHITE)
    d.text((1122,438),'BTMGPA',font=font(19,True),fill=MINT)
    for k,c in enumerate(['#78dfb9','#e9bd65','#7eabcf']):d.ellipse((1130+k*32,480,1144+k*32,494),fill=c)
    d.text((1127,516),'CONCEPTO',font=font(12),fill=MUTED)
    for x in [1128,1210]:d.ellipse((x,544,x+18,566),fill='#06120f',outline='#66867a')
    # Animated technician, fictional adult with speech-driven mouth.
    d.ellipse((87,560,340,584),fill='#06130f')
    d.rounded_rectangle((140,431,190,558),13,fill='#263b43')
    d.rounded_rectangle((205,431,254,558),13,fill='#263b43')
    d.rounded_rectangle((126,547,192,575),9,fill='#0a171b')
    d.rounded_rectangle((204,547,270,575),9,fill='#0a171b')
    d.rounded_rectangle((116,302,280,453),25,fill='#226151',outline='#459880',width=2)
    d.polygon([(164,306),(197,341),(226,305)],fill='#dfece5')
    d.rectangle((174,280,219,317),fill='#c8916e')
    d.ellipse((146,205,244,299),fill='#dba782')
    d.pieslice((143,189,247,259),180,360,fill='#243137')
    d.polygon([(146,221),(157,197),(216,191),(244,219),(211,212),(181,218)],fill='#243137')
    blink=t%4.2<0.12
    for x in [173,217]:
        d.line((x-5,238,x+5,238),fill='#293333',width=2) if blink else d.ellipse((x-3,233,x+3,240),fill='#243137')
    d.line((194,239,190,252,198,254),fill='#b57b5d',width=2)
    d.ellipse((181,265-mouth//3,211,269+mouth),fill='#5e3230')
    if mouth>4:d.rectangle((186,267,207,270),fill='#fff4dc')
    # One arm rests on a tablet; the other gestures toward the instruments.
    d.line((128,331,105,381,153,404),fill='#27745f',width=28)
    d.rounded_rectangle((137,364,214,414),5,fill='#0e2924',outline='#8bb1a3',width=2)
    d.ellipse((146,396,174,411),fill='#dba782')
    hand_y=335+int(8*math.sin(t*1.3))
    d.line((269,331,308,368,357,hand_y),fill='#27745f',width=26)
    d.ellipse((344,hand_y-11,375,hand_y+12),fill='#dba782')
    d.text((140,348),'SS',font=font(19,True),fill=MINT)
    d.text((91,180),'TÉCNICO VIRTUAL',font=font(14,True),fill=MINT)
    # Readable narration captions divided into timed phrases, with exact full transcript in SRT.
    phrases=wrap(scene['speech'],d,font(23),1130)
    groups=[phrases[i:i+2] for i in range(0,len(phrases),2)]
    group=min(len(groups)-1,int(local/max(0.1,end-start)*len(groups)))
    d.rounded_rectangle((35,602,1245,694),12,fill='#061410',outline='#38584a')
    for row,line in enumerate(groups[group]):d.text((61,611+row*31),line,font=font(23),fill=WHITE)
    d.text((44,582),'Visualización ilustrativa · Voz sintética · Sin operación física',font=font(12),fill=MUTED)
    d.rectangle((0,714,int(W*t/cursor),719),fill=MINT)
    return im

def timestamp(t):
    ms=int(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'

if __name__=='__main__':
    out=HERE/'SSScanner-BTMGPA-presentador.mp4'
    command=[imageio_ffmpeg.get_ffmpeg_exe(),'-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i',str(HERE/'btmgpa-narration.wav'),'-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-shortest','-movflags','+faststart',str(out)]
    with (HERE/'render-presenter.log').open('wb') as log:
        p=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=log)
        for i in range(math.ceil(cursor*FPS)):p.stdin.write(frame(i/FPS).tobytes())
        p.stdin.close();assert p.wait()==0
    for i,(start,end,scene,_) in enumerate(segments):frame(start+1).save(HERE/f'presenter-scene-{i}.png')
    (HERE/'SSScanner-BTMGPA-presentador.srt').write_text('\n\n'.join(f'{i+1}\n{timestamp(start)} --> {timestamp(end)}\n{scene["speech"]}' for i,(start,end,scene,_) in enumerate(segments)),encoding='utf-8')
    print(f'{out}\nDuration: {cursor:.2f}s; {W}x{H}; {FPS}fps')
