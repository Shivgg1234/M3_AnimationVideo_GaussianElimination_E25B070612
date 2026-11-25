"""Draw the light-theme visual lesson, including 2D and 3D geometry."""

from functools import lru_cache
from math import cos, sin, sqrt, pi
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from project import BATCH, CHAPTERS, STUDENT, STUDENT_ID

W, H = 1920, 1080
PAPER, WHITE, INK, SOFT = "#F5F0E6", "#FFFCF5", "#182B2B", "#4F615E"
EDGE, GRID = "#D9D3C6", "#EAE3D5"
TEAL, PALE_TEAL = "#006659", "#D7EEE5"
PURPLE, PALE_PURPLE = "#604298", "#EEE3FA"
RUST, PALE_RUST = "#9C441D", "#F8E4D4"
FOREST, MINT = "#153D37", "#BCE9D0"
PIVOTS = ((0, 0), (1, 1), (2, 2))
RAW = ((0, 1, 2, 5), (1, 2, -1, 7), (2, 3, 4, 17))
SWAPPED = RAW[1], RAW[0], RAW[2]

def combine(row, pivot, m):
    return tuple(a+m*b for a,b in zip(row,pivot))

AFTER_X = (*SWAPPED[:2], combine(SWAPPED[2], SWAPPED[0], -2))
ECHELON = (*AFTER_X[:2], combine(AFTER_X[2], AFTER_X[1], 1))
ANSWER = (2, 3, 1)
EQUATIONS = ("y + 2z = 5", "x + 2y − z = 7", "2x + 3y + 4z = 17")
SYMBOLS = ("x", "y", "z", "constant")

X_STEPS = (6.45, 8.55, 10.65, 12.75)
Y_STEPS = (2.25, 4.2, 6.5, 9.15)
XY = (380, 572, 764, 983)
RY = (462, 590, 718)

@lru_cache(maxsize=None)
def font(style, size):
    directory = Path("/System/Library/Fonts")
    names = {
        "text": ("Supplemental/Arial.ttf", "DejaVuSans.ttf"),
        "bold": ("Supplemental/Arial Bold.ttf", "DejaVuSans-Bold.ttf"),
        "serif": ("Supplemental/Georgia.ttf", "DejaVuSerif.ttf"),
        "italic": ("Supplemental/Georgia Italic.ttf", "DejaVuSerif-Italic.ttf"),
        "mono": ("Menlo.ttc", "DejaVuSansMono.ttf"),
    }
    preferred, fallback = names[style]
    local = directory / preferred
    return ImageFont.truetype(str(local) if local.exists() else fallback, size)

def label(d, xy, content, size, fill=INK, style="text", anchor="la"):
    d.text(xy, content, font=font(style, size), fill=fill, anchor=anchor)

def card(d, bounds, fill=WHITE, outline=EDGE, r=23, width=2):
    d.rounded_rectangle(bounds, r, fill=fill, outline=outline, width=width)

def clip(p):
    return max(0, min(1, p))

def ease(t, start=0, stop=1):
    p = clip((t-start)/(stop-start))
    return p*p*(3-2*p)

def mix(a,b,p):
    a,b = (bytes.fromhex(v[1:]) for v in (a,b))
    return "#" + bytes(round(x+(y-x)*p) for x,y in zip(a,b)).hex()

def wrapped(d, content, size, max_width, style="text"):
    result, line = [], []
    for word in content.split():
        trial = " ".join((*line,word))
        if line and d.textlength(trial,font=font(style,size))>max_width:
            result.append(" ".join(line))
            line = [word]
        else:
            line.append(word)
    return [*result, " ".join(line)] if line else result

def paragraph(d, xy, content, width, size=33, fill=SOFT):
    x,y = xy
    for i,line in enumerate(wrapped(d, content, size, width)):
        label(d,(x,y+size*1.29*i),line,size,fill)

def arrow(d, x1, y1, x2, y2, color=TEAL, width=4):
    d.line((x1,y1,x2,y2),fill=color,width=width)
    length = sqrt((x2-x1)**2+(y2-y1)**2)
    if length>16:
        ux,uy = (x2-x1)/length, (y2-y1)/length
        d.line((x2-15*ux+8*uy,y2-15*uy-8*ux,x2,y2,
                x2-15*ux-8*uy,y2-15*uy+8*ux), fill=color,width=width,joint="curve")

def num(n):
    return str(n).replace("-", "−")

def chrome(d, key, chapter, heading, caption, elapsed, total):
    d.line((76,97,1844,97),fill=EDGE,width=2)
    label(d,(76,53),"M3  /  LINEAR ALGEBRA AND CALCULUS",22,TEAL,"bold","lm")
    label(d,(1844,53),"GAUSSIAN ELIMINATION",22,SOFT,"bold","rm")
    if key!="cover":
        label(d,(76,128),f"{chapter:02d}   /   {CHAPTERS[chapter-1].upper()}",23,TEAL,"bold")
        label(d,(74,181),heading,66,INK,"serif")
    if caption:
        card(d,(120,923,1800,1018),FOREST,FOREST,19)
        lines = wrapped(d,caption,33,1564)
        for i,line in enumerate(lines):
            label(d,(960,970+39*(i-(len(lines)-1)/2)),line,33,WHITE,"text","mm")
    d.line((76,1044,1844,1044),fill=EDGE,width=4)
    x = 76+1768*min(1,elapsed/total) if total else 76
    d.line((76,1044,x,1044),fill=TEAL,width=4)
    d.ellipse((x-5,1039,x+5,1049),fill=TEAL)

def cover(d,t):
    label(d,(78,195),"A VISUAL GUIDE TO SOLVING A 3 × 3 SYSTEM",22,RUST,"bold")
    label(d,(72,259),"Gaussian",145,INK,"serif")
    label(d,(76,426),"elimination",129,TEAL,"italic")
    d.line((85,653,862,653),fill=EDGE,width=2)
    label(d,(85,696),STUDENT,37,INK,"bold")
    label(d,(85,755),f"{STUDENT_ID}   /   BATCH {BATCH.upper()}",24,SOFT,"bold")
    card(d,(1042,172,1844,869),FOREST,FOREST,r=28)
    label(d,(1101,229),"THE PIVOT STAIRCASE",24,MINT,"bold")
    for i in range(3):
        for j in range(3):
            x,y = 1110+j*228,303+i*174
            a = ease(t,1.1+0.42*(i+j),2.35+0.42*(i+j))
            pivot = i==j
            fill = mix("#24564B", MINT if pivot else "#214940",a)
            card(d,(x,y,x+196,y+140),fill,"#4E7568",17)
            v = ECHELON[i][j] if a>=0.5 else RAW[i][j]
            color = INK if pivot and a>=0.5 else WHITE
            label(d,(x+98,y+70),num(v),65,mix(fill,color,0.32+0.68*abs(2*a-1)),"mono","mm")

def system_visual(d,key,t):
    card(d,(76,280,1844,886))
    left = 128
    if key == "augment":
        augmented(d,t)
        return
    label(d,(left,328),"THREE EQUATIONS",24,TEAL,"bold")
    line_colors = (RUST, TEAL, PURPLE)
    for i,value in enumerate(EQUATIONS):
        y = 442+i*145
        a = ease(t,i*0.38,i*0.38+0.75)
        label(d,(left,y),f"0{i+1}",24,mix(WHITE,line_colors[i],a),"bold","lm")
        label(d,(left+118,y),value,63,mix(WHITE,INK,a),"mono","lm")
        if i<2:
            d.line((left,y+72,972,y+72),fill=EDGE,width=2)
    card(d,(1078,323,1789,842),PALE_RUST if key=="hook" else PALE_TEAL,None)
    label(d,(1132,378),"FIRST EQUATION" if key=="hook" else "ONE COMMON SOLUTION",24,
          RUST if key=="hook" else TEAL,"bold")
    title = "0x + y + 2z = 5" if key=="hook" else "(x, y, z)"
    label(d,(1133,491),title,47 if key=="hook" else 83,INK,"mono")
    info = ("The missing x term has coefficient zero." if key=="hook" else
            "The same three values must satisfy every row.")
    paragraph(d,(1134,662),info,580,38)

def augmented(d,t):
    label(d,(128,329),"EQUATIONS",24,TEAL,"bold")
    for i,equation in enumerate(EQUATIONS):
        label(d,(130,451+i*137),equation,44,INK,"mono")
    arrow(d,662,587,819,587)
    label(d,(874,329),"AUGMENTED MATRIX",24,TEAL,"bold")
    xs = (1085,1253,1421,1655)
    for x,name in zip(xs,SYMBOLS):
        label(d,(x,401),name,24,SOFT,"bold","mm")
    d.line((1532,439,1532,779),fill=EDGE,width=4)
    for i,row in enumerate(RAW):
        y=493+114*i
        a=ease(t,1.4+0.56*i,2.25+0.56*i)
        card(d,(873,y-44,1768,y+44),mix(WHITE,PAPER,0.75*a),None,13)
        d.line((1532,y-44,1532,y+44),fill=EDGE,width=4)
        label(d,(932,y),f"R{i+1}",29,SOFT,"mono","mm")
        for j,n in enumerate(row):
            label(d,(xs[j]+int(35*(1-a)),y),num(n),49,
                  mix(PAPER,RUST if (i,j)==(0,0) else INK,a),"mono","mm")

def rules(d,t):
    specs = (
        ("Swap", "R₁ ↔ R₂", "Undo by swapping the same two rows again.", TEAL, PALE_TEAL),
        ("Scale", "R₁ ← 2R₁", "Use a nonzero factor. Undo by multiplying by its reciprocal.", RUST, PALE_RUST),
        ("Replace", "R₂ ← R₂ + 2R₁", "Undo by subtracting the same multiple.", PURPLE, PALE_PURPLE),
    )
    for i,(name,formula,note,color,tint) in enumerate(specs):
        x=76+i*598
        a=ease(t,0.1+i*2.5,1+i*2.5)
        y=315+int(40*(1-a))
        card(d,(x,y,x+570,854),mix(WHITE,tint,a),EDGE)
        label(d,(x+47,y+64),name,57,mix(WHITE,color,a),"serif")
        label(d,(x+48,y+187),formula,41,mix(WHITE,INK,a),"mono")
        paragraph(d,(x+48,y+313),note,468,34,mix(WHITE,SOFT,a))

def graph(d,key,t):
    card(d,(76,280,1125,886))
    card(d,(1158,280,1844,886))
    xmin,xmax,ymin,ymax = -1,8.5,-0.4,5.5
    ox,oy,sx,sy = 231,811,98,88
    def pt(x,y):
        return(ox+sx*x,oy-sy*y)
    left,top=pt(xmin,ymax)
    right,bottom=pt(xmax,ymin)
    for x in range(-1,9):
        px,_=pt(x,0)
        d.line((px,top,px,bottom),fill=GRID,width=2)
        if x:
            label(d,(px,oy+10),str(x),21,SOFT,"mono","ma")
    for y in range(1,6):
        _,py=pt(0,y)
        d.line((left,py,right,py),fill=GRID,width=2)
        label(d,(ox-15,py),str(y),21,SOFT,"mono","rm")
    arrow(d,left,oy,right+20,oy,SOFT,3)
    arrow(d,ox,bottom,ox,top-15,SOFT,3)
    label(d,(right+27,oy-25),"x",27,SOFT,"bold","mm")
    label(d,(ox-22,top-14),"y",27,SOFT,"bold","mm")
    def line(a,b,c,color,progress=1,width=6):
        if progress<=0:
            return
        edges = []
        if abs(b)>1e-8:
            edges.extend((x,(c-a*x)/b) for x in (xmin,xmax) if ymin<=(c-a*x)/b<=ymax)
        if abs(a)>1e-8:
            edges.extend(((c-b*y)/a,y) for y in (ymin,ymax) if xmin<=(c-b*y)/a<=xmax)
        if len(edges)<2:
            return
        (x1,y1),(x2,y2)=sorted(edges)[0],sorted(edges)[-1]
        d.line((*pt(x1,y1),*pt(x1+(x2-x1)*progress,y1+(y2-y1)*progress)),fill=color,width=width)
    line(1,2,8,TEAL,ease(t,0.75,2.4) if key=="lines" else 1)
    phase = ease(t,5.5,12.2) if key=="rotate" else 1-ease(t,8.2,13.2) if key=="reverse" else 0
    if phase>0:
        line(2,3,13,"#D0BFDF",1,3)
    # At every stage the moving line is B minus a multiple of A.
    line(2-2*phase,3-4*phase,13-16*phase,PURPLE,ease(t,4.7,6.7) if key=="lines" else 1)
    if key=="slice":
        line(0,1,3,RUST,ease(t,8,11),6)
    if key!="lines" or t>=8.1:
        px,py=pt(2,3)
        d.ellipse((px-14,py-14,px+14,py+14),fill=WHITE,outline=INK,width=3)
        d.ellipse((px-5,py-5,px+5,py+5),fill=INK)
        card(d,(px+22,py-67,px+145,py-19),WHITE,EDGE,11)
        label(d,(px+84,py-43),"(2, 3)",25,INK,"mono","mm")
    x=1205
    label(d,(x,328),"CROSS-SECTION" if key=="slice" else "TWO EQUATIONS",23,SOFT,"bold")
    label(d,(x,420),"x + 2y = 8",47,TEAL,"mono")
    if key in ("lines","slice","rotate"):
        label(d,(x,514),"2x + 3y = 13",46,PURPLE,"mono")
    if key=="lines":
        paragraph(d,(x,675),"One point satisfies both equations.",567,37)
    elif key=="rotate":
        label(d,(x,623),"Second − 2 × first",30,SOFT,"bold")
        if t>=7.3:
            label(d,(x,710),"−y = −3   ⇒   y = 3",39,RUST,"mono")
    elif key=="reverse":
        label(d,(x,518),"−y = −3",48,PURPLE,"mono")
        label(d,(x,628),"Add 2 × first back",30,SOFT,"bold")
        if t>=10:
            label(d,(x,714),"2x + 3y = 13",43,PURPLE,"mono")
    else:
        label(d,(x,612),"y = 3",46,RUST,"mono")
        label(d,(x,768),"(x, y, z) = (2, 3, 1)",36,INK,"mono")

def matrix(d,rows,pivots=(),zeros=(),active=None,swap=None):
    card(d,(76,280,1136,886))
    label(d,(120,322),"AUGMENTED MATRIX",23,TEAL,"bold")
    for x,name in zip(XY,SYMBOLS):
        label(d,(x,390),name,24,SOFT,"bold","mm")
    for x,direction in ((276,1),(1084,-1)):
        d.line((x+19*direction,420,x,420,x,774,x+19*direction,774),fill=SOFT,width=3)
    d.line((875,420,875,774),fill=EDGE,width=4)
    for i,row in enumerate(rows):
        moving = swap is not None and i in (0,1)
        color_row = active==i or moving
        y = RY[i]
        compact = 0
        row_label_x = 141
        columns = XY
        if moving:
            y += (1-2*i)*128*swap
            compact = min(ease(swap,0,0.28), 1-ease(swap,0.72,1))
            narrow = (317,408,499,600) if i==0 else (693,793,893,994)
            columns = tuple(a+(b-a)*compact for a,b in zip(XY,narrow))
            row_label_x += (18+570*i)*compact
        if color_row:
            tint = PALE_PURPLE if i!=1 else PALE_TEAL
            left = columns[0]-86 if not moving else columns[0]-(86-65*compact)
            right = columns[-1]+77-47*compact
            card(d,(left,y-48,right,y+48),tint,EDGE,14)
            divider = (columns[2]+columns[3])/2
            d.line((divider,y-46,divider,y+46),fill=EDGE,width=3)
        if moving and compact>0.72:
            label(d,(row_label_x,y-45),f"R{i+1}",22,PURPLE,"mono","lm")
        else:
            label(d,(141,y),f"R{i+1}",30,PURPLE if color_row else SOFT,"mono","lm")
        for j,value in enumerate(row):
            x=columns[j]
            color = INK
            if (i,j) in pivots:
                card(d,(x-53,y-46,x+53,y+46),PALE_RUST,"#E2A988",13)
                color=RUST
            if (i,j) in zeros:
                card(d,(x-53,y-46,x+53,y+46),PALE_TEAL,"#B4D6C9",13)
                color=TEAL
            label(d,(x,y),num(value),round(61-16*compact),color,"mono","mm")

def side(d, name, color=TEAL, fill=WHITE):
    card(d,(1171,280,1844,886),fill,EDGE)
    label(d,(1218,324),name,23,color,"bold")

def op_worksheet(d,key,t):
    is_x = key=="eliminate_x"
    start = SWAPPED if is_x else AFTER_X
    end = AFTER_X if is_x else ECHELON
    steps = X_STEPS if is_x else Y_STEPS
    pivots = PIVOTS[:1 if is_x else 2]
    new_zeros=[(1,0)]
    if t>=steps[0]+0.45 or not is_x:
        new_zeros.append((2,0))
    if not is_x and t>=steps[1]+0.45:
        new_zeros.append((2,1))
    row=tuple(end[2][j] if t>=step+0.45 else start[2][j] for j,step in enumerate(steps))
    matrix(d,(*start[:2],row),pivots,new_zeros,active=2)
    side(d,"ROW REPLACEMENT",PURPLE)
    label(d,(1218,397),"R₃ ← R₃ − 2R₁" if is_x else "R₃ ← R₃ + R₂",46,INK,"mono")
    if is_x:
        a=ease(t,2.6,4)
        label(d,(1219,483),"2R₁ = (2, 4, −2 | 14)",30,mix(WHITE,PURPLE,a),"mono")
    else:
        label(d,(1219,483),"R₂ = (0, 1, 2 | 5)",30,PURPLE,"mono")
    d.line((1218,550,1798,550),fill=EDGE,width=2)
    terms = ("2 − 2 = 0","3 − 4 = −1","4 − (−2) = 6","17 − 14 = 3") if is_x else (
             "0 + 0 = 0","−1 + 1 = 0","6 + 2 = 8","3 + 5 = 8")
    for j,(name,expr,onset) in enumerate(zip(SYMBOLS,terms,steps)):
        a=ease(t,onset,onset+0.68)
        y=596+69*j
        label(d,(1220,y),name,23,mix(WHITE,SOFT,a),"bold","lm")
        label(d,(1397,y),expr,34,mix(WHITE,TEAL,a),"mono","lm")
        if 0<a<1:
            x=XY[j]
            card(d,(x-52,815,x+52,822),mix(WHITE,PURPLE,sin(pi*a)),None,3)

def matrix_scene(d,key,t):
    if key in ("eliminate_x","eliminate_y"):
        op_worksheet(d,key,t)
        return
    if key=="swap":
        p=ease(t,7.2,10.6)
        if p<1:
            matrix(d,RAW,active=None if p else 0,swap=p if p else None)
        else:
            matrix(d,SWAPPED,PIVOTS[:1],[(1,0)])
        side(d,"ROW SWAP",RUST,PALE_RUST)
        label(d,(1218,420),"R₁ ↔ R₂",65,INK,"mono")
        paragraph(d,(1219,585),"Bring a nonzero entry into the first pivot position.",557,39)
    elif key=="pivot":
        matrix(d,SWAPPED,PIVOTS[:1],[(1,0)],active=2)
        side(d,"TARGET ÷ PIVOT",RUST)
        label(d,(1220,465),"2 ÷ 1 = 2",64,RUST,"mono")
        paragraph(d,(1220,625),"Subtract two copies of the pivot row.",540,39)
    elif key=="predict":
        matrix(d,AFTER_X,PIVOTS[:2],[(1,0),(2,0)],active=2)
        side(d,"YOUR TURN",PURPLE,PALE_PURPLE)
        label(d,(1219,459),"−1 + ? × 1 = 0",48,PURPLE,"mono")
        paragraph(d,(1219,633),"What multiple of row 2 makes the y entry zero?",540,36)
        if t>=9.4:
            p=ease(t,9.4,14)
            card(d,(1219,793,1796,803),WHITE,None,4)
            if p:
                card(d,(1219,793,1219+577*p,803),PURPLE,None,4)
    else:
        count=1 if t<1 else 2 if t<2.1 else 3
        matrix(d,ECHELON,PIVOTS[:count],[(1,0),(2,0),(2,1)])
        side(d,"ROW ECHELON FORM",RUST)
        label(d,(1220,439),"Three pivots",60,INK,"serif")
        paragraph(d,(1220,584),"One in every variable column. Zeros below each pivot.",548,38)
        for i,letter in enumerate(("x","y","z")):
            color=mix(WHITE,RUST,ease(t,0.5+i,1+i))
            label(d,(1223+136*i,785),letter,44,color,"mono")

def substitution(d,key,t):
    slot=("solve_z","solve_y","solve_x").index(key)
    matrix(d,ECHELON,PIVOTS,[(1,0),(2,0),(2,1)],active=2-slot)
    side(d,"BACK SUBSTITUTION",PURPLE)
    formulas=(
        ("8z = 8","z = 8 ÷ 8","z = 1"),
        ("y + 2z = 5","y + 2(1) = 5","y = 5 − 2","y = 3"),
        ("x + 2y − z = 7","x + 2(3) − 1 = 7","x + 5 = 7","x = 2"),
    )[slot]
    starts=(0.22,4.6,7.15,9.8)
    for i,value in enumerate(formulas):
        a=ease(t,starts[i],starts[i]+0.63)
        last=i==len(formulas)-1
        label(d,(1218,420+83*i),value,57 if last else 43,mix(WHITE,TEAL if last else INK,a),"mono")
    if slot:
        p=ease(t,3.1,4.55)
        x,y=1219+240*p,798-26*sin(pi*p)
        values="z = 1" if slot==1 else "y = 3  ·  z = 1"
        w=159 if slot==1 else 293
        card(d,(x,y,x+w,y+49),PALE_TEAL,None,12)
        label(d,(x+w/2,y+25),values,24,TEAL,"mono","mm")

def verify(d,t):
    card(d,(76,280,1298,886))
    label(d,(124,326),"SUBSTITUTE INTO THE ORIGINAL SYSTEM",23,TEAL,"bold")
    data=("3 + 2(1) = 5","2 + 2(3) − 1 = 7","2(2) + 3(3) + 4(1) = 17")
    for i,line in enumerate(data):
        y=458+137*i
        a=ease(t,3.2+3.0*i,4+3.0*i)
        label(d,(128,y),f"R{i+1}",29,SOFT,"mono","lm")
        label(d,(225,y),line,46,mix(WHITE,INK,a),"mono","lm")
        card(d,(1169,y-28,1231,y+28),mix(WHITE,PALE_TEAL,a),None,12)
        d.line((1186,y,1197,y+10,1216,y-12),fill=mix(WHITE,TEAL,a),width=4,joint="curve")
    card(d,(1336,280,1844,886),FOREST,FOREST)
    label(d,(1382,329),"THE UNIQUE SOLUTION",22,MINT,"bold")
    for i,(name,value) in enumerate(zip(("x","y","z"),ANSWER)):
        label(d,(1384,450+i*114),f"{name} = {value}",62,WHITE,"mono")

def cross(a,b):
    return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])

def unit(vector):
    magnitude=sqrt(sum(c*c for c in vector))
    return tuple(c/magnitude for c in vector)

def geometry(image,d,t):
    card(d,(76,280,1136,886))
    side(d,"GEOMETRIC INTERPRETATION")
    angle=-0.35+1.2*ease(t,2.7,16.5)
    tilt=0.43
    def project(point):
        x,y,z=(point[i]-ANSWER[i] for i in range(3))
        return (607+93*(cos(angle)*x-sin(angle)*y),
                594+93*(sin(tilt)*(sin(angle)*x+cos(angle)*y)-cos(tilt)*z))
    def placed(direction,m):
        return tuple(x+m*v for x,v in zip(ANSWER,direction))
    for i,name in enumerate(("x","y","z")):
        origin=(0,0,0)
        endpoint=tuple((4.55 if i<2 else 3.05) if j==i else 0 for j in range(3))
        a,b=project(origin),project(endpoint)
        arrow(d,*a,*b,"#A9B6AD",3)
        label(d,(b[0]+12,b[1]+7),name,24,SOFT,"bold","mm")
    overlay=Image.new("RGBA",image.size)
    od=ImageDraw.Draw(overlay)
    colors = (RUST,TEAL,PURPLE)
    for row,color,start in zip(RAW,colors,(8.0,0.35,1.85)):
        a=ease(t,start,start+1.7)
        if a<=0:
            continue
        normal=row[:3]
        u=unit(cross(normal,(0,0,1)))
        v=unit(cross(normal,u))
        corners=[tuple(x+i*a*2.55*du+j*a*2.1*dv for x,du,dv in zip(ANSWER,u,v))
                 for i,j in ((-1,-1),(1,-1),(1,1),(-1,1))]
        polygon=[project(p) for p in corners]
        rgb=bytes.fromhex(color[1:])
        od.polygon(polygon,fill=(*rgb,58),outline=(*rgb,188),width=3)
    image.paste(overlay,(0,0),overlay)
    p=ease(t,4.7,6.3)
    if p:
        direction=unit(cross(RAW[1][:3],RAW[2][:3]))
        d.line((*project(placed(direction,-2.52*p)),*project(placed(direction,2.52*p))),
               fill=PURPLE,width=5)
    if t>=9.7:
        px,py=project(ANSWER)
        d.ellipse((px-14,py-14,px+14,py+14),fill=WHITE,outline=INK,width=4)
        d.ellipse((px-5,py-5,px+5,py+5),fill=INK)
        card(d,(px+27,py-71,px+249,py-21),WHITE,EDGE,11)
        label(d,(px+139,py-45),"(2, 3, 1)",26,INK,"mono","mm")
    for i,(eq,color) in enumerate(zip(EQUATIONS,colors)):
        label(d,(1218,417+88*i),eq,34,color,"mono")
    paragraph(d,(1218,737),"Two planes share a line. The third meets that line at one point.",555,31)

def summary(d,t,credits):
    if credits:
        card(d,(76,280,820,885),FOREST,FOREST)
        card(d,(855,280,1844,885))
        label(d,(128,330),"THE THREE STEPS",23,MINT,"bold")
        for i,value in enumerate(("Write the augmented matrix.", "Clear below nonzero pivots.", "Back substitute and check.")):
            label(d,(131,454+i*112),value,39,WHITE,"text")
        x=911
        label(d,(x,330),"PROJECT CREDITS",23,TEAL,"bold")
        sections=(
            ("References", "M3 Animation Video Project Instructions", "OpenStax  ·  Algebra and Trigonometry 2e, §11.6"),
            ("AI disclosure", "OpenAI Codex  ·  script, visuals and animation code", "Piper / Lessac  ·  synthetic narration in the guide version"),
        )
        for i,(title,one,two) in enumerate(sections):
            y=422+152*i
            label(d,(x,y),title,32,INK,"bold")
            label(d,(x,y+48),one,27,SOFT)
            label(d,(x,y+86),two,27,SOFT)
        label(d,(x,782),"Music  ·  None",27,SOFT)
    else:
        specs=(("Write","Map the equations to an augmented matrix.",TEAL,PALE_TEAL),
               ("Eliminate","Choose nonzero pivots and clear entries below.",RUST,PALE_RUST),
               ("Solve","Back substitute and check in the originals.",PURPLE,PALE_PURPLE))
        for i,(title,desc,color,tint) in enumerate(specs):
            x=76+598*i
            a=ease(t,0.26+2.5*i,1.2+2.5*i)
            y=324+int(50*(1-a))
            card(d,(x,y,x+570,864),mix(WHITE,tint,a))
            label(d,(x+47,y+69),f"0{i+1}",28,mix(WHITE,color,a),"mono")
            label(d,(x+44,y+176),title,64,mix(WHITE,INK,a),"serif")
            paragraph(d,(x+48,y+323),desc,467,37,mix(WHITE,SOFT,a))

def frame(key,chapter,heading,time,caption="",elapsed=0,total=0):
    image=Image.new("RGB",(W,H),PAPER)
    d=ImageDraw.Draw(image)
    chrome(d,key,chapter,heading,caption,elapsed,total)
    if key=="cover":
        cover(d,time)
    elif key in ("hook","system","augment"):
        system_visual(d,key,time)
    elif key=="rules":
        rules(d,time)
    elif key in ("lines","rotate","reverse","slice"):
        graph(d,key,time)
    elif key.startswith("solve_"):
        substitution(d,key,time)
    elif key=="verify":
        verify(d,time)
    elif key=="planes":
        geometry(image,d,time)
    elif key in ("recap","credits"):
        summary(d,time,key=="credits")
    else:
        matrix_scene(d,key,time)
    return image
