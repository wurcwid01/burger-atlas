"""Generate Burger Atlas marker-style burger illustrations (Warm Diner palette)."""
import random, sys
OUT = sys.argv[1]
INK="#25251F"; IVORY="#F7F5F0"; TERRA="#BE6641"; SAGE="#A8B5A0"; MUST="#E3A93B"
BUN="#E0A464"; BUN2="#D99A5B"; LET="#8FA77F"; CHE="#F2B33D"; BEEF="#6B4130"
BLOBS={"sage":SAGE,"terra":"#E4B29C","mustard":"#EED39A","oat":"#DCCFB8"}

def defs(seed):
    return f'''<defs>
<filter id="w" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed="{seed}" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="7" xChannelSelector="R" yChannelSelector="G"/></filter>
<filter id="k" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency="0.9 0.04" numOctaves="2" seed="{seed+5}" result="s"/><feColorMatrix in="s" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -1.1 1.35" result="m"/><feComposite in="SourceGraphic" in2="m" operator="in" result="t"/><feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="2" seed="{seed+2}" result="n2"/><feDisplacementMap in="t" in2="n2" scale="9" xChannelSelector="R" yChannelSelector="G"/></filter>
<pattern id="p" width="6" height="6" patternUnits="userSpaceOnUse"><rect width="6" height="6" fill="{IVORY}"/><circle cx="1" cy="2" r=".5" fill="#ECE7DC"/></pattern></defs>'''

def wave(x0,x1,y,amp,n):
    step=(x1-x0)/n; d=f"M{x0},{y}"
    for i in range(n):
        d+=f" Q{x0+step*(i+.5):.0f},{y+(amp if i%2==0 else -amp)} {x0+step*(i+1):.0f},{y}"
    return d

def burger(kind, seed, blob, doodle):
    random.seed(seed)
    cx=400; w=350 if kind!="budget" else 320
    L=cx-w/2; R=cx+w/2
    fills=[]; lines=[]; extra=[]
    y=300  # bottom of top bun
    top_h=150 if kind!="gourmet" else 165
    # top bun
    fills.append(f'<path d="M{L+8},{y} C{L+12},{y-top_h+40} {cx-90},{y-top_h} {cx},{y-top_h} C{cx+90},{y-top_h} {R-12},{y-top_h+40} {R-8},{y} Z" fill="{BUN if kind!="gourmet" else "#D8924F"}"/>')
    lines.append(f'<path d="M{L-2},{y+4} C{L},{y-top_h+36} {cx-92},{y-top_h-6} {cx},{y-top_h-6} C{cx+96},{y-top_h-4} {R+4},{y-top_h+36} {R+6},{y+2} C{cx+120},{y+8} {cx-140},{y+8} {L-10},{y}"/>')
    # seeds / shine
    if kind in ("smash","budget","plant"):
        for _ in range(8):
            sx=cx+random.uniform(-w*.32,w*.32); sy=random.uniform(y-top_h+40,y-30)
            a=random.choice([-1,1])*random.uniform(4,8)
            extra.append(f'<path d="M{sx:.0f},{sy:.0f} l14,{a:.0f}" stroke="{INK}" stroke-width="5"/>')
    if kind=="gourmet":  # glaze + flaky salt dots
        for _ in range(10):
            sx=cx+random.uniform(-w*.3,w*.3); sy=random.uniform(y-top_h+45,y-30)
            extra.append(f'<circle cx="{sx:.0f}" cy="{sy:.0f}" r="3.2" fill="{IVORY}"/>')
    extra.append(f'<path d="M{L+48},{y-60} C{L+60},{y-100} {cx-70},{y-top_h+18} {cx-30},{y-top_h+12}" stroke="{IVORY}" stroke-width="9" fill="none" opacity=".85"/>')
    y+=8
    # lettuce
    if kind!="budget":
        fills.append(f'<path d="{wave(L-12,R+12,y+6,9,8)} L{R+8},{y+24} L{L-8},{y+24} Z" fill="{LET}"/>')
        lines.append(f'<path d="{wave(L-14,R+14,y+6,9,8)}"/>'); y+=24
    # tomato / pickles
    if kind in ("smash","gourmet"):
        fills.append(f'<rect x="{L+14}" y="{y}" width="{w-28}" height="20" rx="9" fill="{TERRA}"/>')
        lines.append(f'<path d="M{L+18},{y+20} L{R-16},{y+20}" stroke-width="5"/>'); y+=20
    if kind=="chicken":  # mayo squiggle
        extra.append(f'<path d="{wave(L+20,R-20,y+4,6,10)}" stroke="{IVORY}" stroke-width="8" fill="none"/>'); y+=8
    # cheese
    if kind in ("smash","budget","gourmet"):
        dr=" ".join(f"L{L+(i+.5)*w/6:.0f},{y+random.randint(24,40)} L{L+(i+1)*w/6:.0f},{y+10}" for i in range(6))
        fills.append(f'<path d="M{L-6},{y} L{R+6},{y} L{R+2},{y+10} {dr} L{L},{y+10} Z" fill="{CHE}"/>')
        lines.append(f'<path d="M{L-4},{y+2} L{L+6},{y+12} {dr}"/>'); y+=12
    # patties
    def patty(y, col, bumpy=False, h=54):
        fills.append(f'<rect x="{L-12}" y="{y}" width="{w+24}" height="{h}" rx="{h/2}" fill="{col}"/>')
        if bumpy:
            d=f"M{L-4},{y+h/2}"
            for i in range(9):
                x=L+i*(w/8); d+=f" Q{x+w/16:.0f},{y-8} {x+w/8:.0f},{y+4}"
            lines.append(f'<path d="{d}"/>')
            lines.append(f'<path d="M{L-8},{y+h*.6} C{L-14},{y+h+6} {L+20},{y+h+4} {cx},{y+h+2} C{R-20},{y+h+4} {R+16},{y+h+6} {R+8},{y+h*.5}"/>')
            for _ in range(7):
                bx=cx+random.uniform(-w*.42,w*.42); by=y+random.uniform(14,h-10)
                extra.append(f'<path d="M{bx:.0f},{by:.0f} l8,-4" stroke="#9A5B22" stroke-width="5"/>')
        else:
            lines.append(f'<path d="M{L+8},{y-2} C{L-22},{y+4} {L-22},{y+h+2} {L+10},{y+h+4} L{R-8},{y+h+2} C{R+24},{y+h} {R+22},{y-2} {R-10},{y-2} Z"/>')
            for i in range(4):
                gx=L+50+i*(w-100)/3
                extra.append(f'<path d="M{gx-14:.0f},{y+14} L{gx+12:.0f},{y+h-14}" stroke="{INK}" stroke-width="5" opacity=".6"/>')
        return y+h
    if kind=="chicken": y=patty(y,"#D9953F",bumpy=True,h=60)
    elif kind=="plant": y=patty(y,"#7C7A45")
    else: y=patty(y,BEEF)
    if kind=="smash":  # double
        y+=4; dr=" ".join(f"L{L+(i+.5)*w/6:.0f},{y+random.randint(18,30)} L{L+(i+1)*w/6:.0f},{y+8}" for i in range(6))
        fills.append(f'<path d="M{L-6},{y} L{R+6},{y} L{R+2},{y+8} {dr} L{L},{y+8} Z" fill="{CHE}"/>')
        y+=6; y=patty(y,BEEF,h=46)
    if kind=="plant":  # avocado slices
        for i in range(3):
            ax=L+70+i*(w-140)/2
            fills.append(f'<ellipse cx="{ax:.0f}" cy="{y-58}" rx="34" ry="12" fill="#B9C78A"/>')
    y+=8
    # bottom bun
    bb=62 if kind!="budget" else 52
    fills.append(f'<path d="M{L+4},{y} L{R-4},{y} C{R-6},{y+bb} {cx+120},{y+bb+8} {cx},{y+bb+8} C{cx-120},{y+bb+8} {L+6},{y+bb} {L+4},{y} Z" fill="{BUN2}"/>')
    lines.append(f'<path d="M{L-6},{y+2} C{L},{y+bb+8} {cx-110},{y+bb+12} {cx},{y+bb+12} C{cx+120},{y+bb+12} {R},{y+bb+6} {R+4},{y} C{cx+100},{y+4} {cx-120},{y+4} {L-12},{y}"/>')
    # budget: paper wrapper over bottom
    if kind=="budget":
        wy=y+10
        fills.append(f'<path d="M{L-24},{wy} L{R+24},{wy} L{R-6},{y+bb+40} L{L+6},{y+bb+40} Z" fill="{IVORY}"/>')
        for i in range(6):
            sx=L-10+i*(w+20)/5
            extra.append(f'<path d="M{sx:.0f},{wy+6} L{sx+18:.0f},{y+bb+34}" stroke="{TERRA}" stroke-width="9" opacity=".8"/>')
        lines.append(f'<path d="M{L-26},{wy} L{R+26},{wy-2} L{R-4},{y+bb+42} L{L+4},{y+bb+42} Z"/>')
    bottom=y+bb+12
    # blob + doodles
    bc=BLOBS[blob]
    blobsvg=f'<g filter="url(#k)" opacity=".6"><path d="M{cx-270},{bottom-150} C{cx-250},{120} {cx-60},{90} {cx+70},{110} C{cx+230},{140} {cx+300},{230} {cx+270},{bottom-110} C{cx+240},{bottom+20} {cx+60},{bottom+40} {cx-70},{bottom+20} C{cx-200},{bottom} {cx-285},{bottom-60} {cx-270},{bottom-150}Z" fill="{bc}"/></g>'
    d=[]
    if doodle=="rays":
        d+= [f'<path d="M176 210 l-26 -16 M170 246 l-34 0 M182 178 l-14 -24" stroke="{TERRA}"/>', f'<path d="M624 206 l26 -16 M630 242 l34 0 M618 174 l14 -24" stroke="{TERRA}"/>']
    steam=""
    if doodle=="steam":
        sy=300-top_h-24
        steam=f'<g filter="url(#w)" fill="none" stroke-width="6" stroke-linecap="round"><path d="M372 {sy} c10 -18 -10 -28 0 -46 M428 {sy-4} c10 -18 -10 -28 0 -46" stroke="{SAGE if blob!="sage" else TERRA}"/></g>'
    if doodle=="stars":
        for (sx,sy) in [(150,190),(650,170),(640,420)]:
            d.append(f'<path d="M{sx},{sy-16} L{sx},{sy+16} M{sx-16},{sy} L{sx+16},{sy}" stroke="{MUST}"/>')
    if doodle=="hearts":
        for (sx,sy) in [(160,200),(648,190)]:
            d.append(f'<path d="M{sx},{sy+14} C{sx-22},{sy-2} {sx-12},{sy-22} {sx},{sy-8} C{sx+12},{sy-22} {sx+22},{sy-2} {sx},{sy+14}Z" stroke="{TERRA}"/>')
    # vertical centering: shift whole burger so it's centred in 600
    top=300-top_h-(60 if doodle=="steam" else 6); shift=(600-(bottom-top))/2-top
    T=f'translate(400,300) scale(1.04) translate(-400,{-300+shift:.0f})'
    burger_g=(f'<g transform="{T}">{steam}'
              f'<g filter="url(#k)">{"".join(fills)}</g>'
              f'<g filter="url(#w)" fill="none" stroke="{INK}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round">{"".join(lines)}</g>'
              f'<g filter="url(#w)" stroke-linecap="round" fill="none">{"".join(extra)}</g></g>')
    blob_g=f'<g transform="{T}">{blobsvg}</g>'
    doodle_g=f'<g filter="url(#w)" fill="none" stroke-width="6" stroke-linecap="round">{"".join(d)}</g>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" preserveAspectRatio="xMidYMid slice">'
            f'{defs(seed)}<rect width="800" height="600" fill="url(#p)"/>{blob_g}{doodle_g}{burger_g}</svg>')

SET=[("smash","sage","rays"),("smash","mustard","stars"),("smash","terra","steam"),
     ("gourmet","oat","stars"),("gourmet","sage","steam"),
     ("chicken","mustard","rays"),("chicken","terra","hearts"),
     ("plant","sage","hearts"),("plant","oat","rays"),
     ("budget","terra","stars"),("budget","mustard","steam"),("budget","sage","rays")]
for i,(k,b,d) in enumerate(SET,1):
    open(f"{OUT}/burger-{i:02d}.svg","w").write(burger(k,i*7,b,d))
print("ok")
