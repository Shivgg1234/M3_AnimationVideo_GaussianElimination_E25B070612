"""Create the storyboard and recording script from the final video timeline."""

import argparse
from io import BytesIO
import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

from project import BATCH, CHAPTERS, STUDENT, STUDENT_ID
from visuals import frame

PAGE = (595.28, 841.89)
NAVY, INK, GREY, TEAL, LINE, SOFT = map(HexColor, (
    "#153D37", "#182B2B", "#4F615E", "#006659", "#D9D3C6", "#F5F0E6"
))
SOURCE = "https://openstax.org/books/algebra-and-trigonometry-2e/pages/11-6-solving-systems-with-gaussian-elimination"
LEARNING = "By the end, viewers can solve a 3 × 3 system using a row swap, pivot-based elimination and back substitution, and can use a graph to explain why row replacement preserves solutions."
FONT_DIR = Path("/System/Library/Fonts/Supplemental")
for alias, mac, linux in (
    ("Body", "Arial.ttf", "DejaVuSans.ttf"),
    ("Bold", "Arial Bold.ttf", "DejaVuSans-Bold.ttf"),
    ("Italic", "Arial Italic.ttf", "DejaVuSans-Oblique.ttf"),
    ("Title", "Georgia.ttf", "DejaVuSerif.ttf"),
):
    path = FONT_DIR/mac
    pdfmetrics.registerFont(TTFont(alias, str(path if path.is_file() else Path("/usr/share/fonts/truetype/dejavu")/linux)))

# chapter, thumbnail key and time, visual plan, narration plan, mathematics
STORY = [
    (1,"cover",5,
     "Reveal the pivot staircase, then show the equation with a missing x term.",
     "Introduce the goal of finding one common point in a three-equation system.",
     "The absent x term in y + 2z = 5 gives a zero in the top-left matrix entry."),
    (2,"augment",5,
     "Map each equation to a row. Introduce row swaps, nonzero scaling, and row replacement.",
     "Explain the coefficient and constant columns, then describe how to undo each row operation.",
     "The rows are (0, 1, 2 | 5), (1, 2, −1 | 7), and (2, 3, 4 | 17)."),
    (3,"rotate",9,
     "Draw two lines. Rotate the purple line through the fixed intersection, then reverse the operation.",
     "Walk through the cancellation and its inverse to justify preservation of the common point.",
     "Subtract twice x + 2y = 8 from 2x + 3y = 13 to get −y = −3. The intersection stays at (2, 3)."),
    (4,"eliminate_y",12,
     "Slide two rows past each other, build the pivot staircase, and pause for a prediction before the second elimination.",
     "Explain the swap, calculate each updated entry, then solve upward from the bottom row.",
     "R₁ ↔ R₂, R₃ ← R₃ − 2R₁, then R₃ ← R₃ + R₂. Read 8z = 8, y + 2z = 5, and x + 2y − z = 7."),
    (5,"planes",12,
     "Check the original equations, rotate three planes in space, then return to a horizontal slice.",
     "Connect the intersection of the planes to the ordered triple and the earlier two-line graph.",
     "The solution (2, 3, 1) gives 5, 7, 17. The z = 1 slice adds y = 3 to the two original graph lines."),
    (6,"credits",2,
     "Reveal the three recap cards and hold on the references and credits.",
     "Recap the general procedure and emphasize the invariant solution set.",
     "Write the matrix, eliminate below nonzero pivots, then back substitute and check."),
]
RECORDING_CUES = {
    "cover": "Pause briefly after “one point in space.” Let the pivot staircase finish forming.",
    "hook": "Emphasize “no x term” and pause on the zero coefficient.",
    "system": "Stress “all three equations” before moving to the matrix.",
    "augment": "Pause briefly at the bar. Read the column names individually.",
    "rules": "Give each operation a beat. Emphasize “nonzero” and “undone.”",
    "lines": "Read the teal equation first, then the purple one. Land on the marked point.",
    "rotate": "Slow down through “negative y equals negative three.” Keep attention on the fixed crossing.",
    "reverse": "Emphasize “reverse direction” as the purple line returns.",
    "swap": "Watch for the row movement as you say “swap rows one and two.”",
    "pivot": "Read “target entry divided by the pivot” deliberately.",
    "eliminate_x": "Give negative one, six, and three separate beats. Leave time to read the last column.",
    "predict": "After the question, leave the remaining seconds for the viewer to think.",
    "eliminate_y": "Stress the addition. Read the new entries from left to right.",
    "echelon": "Follow the orange pivots down the diagonal.",
    "solve_z": "Pause after “eight z equals eight.” Say “z equals one” clearly.",
    "solve_y": "Pause after “replace z by one.” End on the highlighted y value.",
    "solve_x": "Read both substitutions distinctly. Land on “x equals two.”",
    "verify": "Say the three right-hand-side values in the same order as the rows.",
    "planes": "Pause on the shared line, then on the dot where the third plane crosses it.",
    "slice": "Stress “z equals one” to connect the bottom row to this graph.",
    "recap": "Use a short pause between Write, Eliminate, and Solve.",
    "credits": "Finish speaking early so the credits remain readable in silence.",
}

def stamp(seconds):
    whole = int(seconds)
    return f"{whole//60}:{whole%60:02d}"

def text(doc, x, y, value, size=11, face="Body", color=INK):
    doc.setFont(face,size)
    doc.setFillColor(color)
    doc.drawString(x,y,value)

def paragraph(doc, x, top, value, width, size=11, color=INK, leading=None):
    for digit, subscript in enumerate("₁₂₃", 1):
        value = value.replace(subscript, f"<sub>{digit}</sub>")
    style = ParagraphStyle("Project",fontName="Body",fontSize=size,leading=leading or size*1.32,
                           alignment=TA_LEFT,textColor=color,allowWidows=0,allowOrphans=0)
    content = Paragraph(value,style)
    _, height = content.wrap(width,800)
    content.drawOn(doc,x,top-height)
    return top-height

def heading(doc, page, pages, tag, title, kicker):
    width,height = PAGE
    doc.setFillColor(NAVY)
    doc.rect(0,height-141,width,141,fill=1,stroke=0)
    text(doc,42,height-45,tag,10,"Bold",HexColor("#8CE8C7"))
    text(doc,42,height-91,title,31,"Title",white)
    text(doc,42,height-118,kicker,10,"Body",HexColor("#D7E1F3"))
    doc.setStrokeColor(LINE)
    doc.line(42,43,width-42,43)
    text(doc,42,27,f"{STUDENT}  •  {STUDENT_ID}  •  Batch {BATCH}",9,"Body",GREY)
    doc.setFont("Bold",9)
    doc.setFillColor(GREY)
    doc.drawRightString(width-42,27,f"{page} / {pages}")

def storyboard(timeline, destination):
    doc = canvas.Canvas(str(destination),pagesize=PAGE)
    doc.setTitle("Gaussian Elimination | Six-Scene Storyboard")
    doc.setAuthor(STUDENT)
    beats = {item["key"]:item for item in timeline}
    total = timeline[-1]["start"]+timeline[-1]["duration"]
    for page in range(2):
        heading(doc,page+1,2,"M3 ANIMATION PROJECT / STORYBOARD","Gaussian elimination",
                f"Solving a 3 × 3 system   •   {stamp(total)}   •   1080p landscape")
        y = 675
        if page == 0:
            doc.setFillColor(SOFT)
            doc.roundRect(42,604,511,82,10,fill=1,stroke=0)
            text(doc,55,665,"LEARNING OBJECTIVE",9,"Bold",TEAL)
            paragraph(doc,55,654,escape(LEARNING),487,10.5)
            y = 579
        for number,key,time,vis,narr,math in STORY[page*3:page*3+3]:
            span = [beat for beat in timeline if beat["chapter"] == number]
            start, end = span[0]["start"], span[-1]["start"]+span[-1]["duration"]
            text(doc,42,y,f"{number:02d}  {stamp(start)}–{stamp(end)}",9,"Bold",TEAL)
            text(doc,139,y,CHAPTERS[number-1],15,"Bold")
            y -= 17
            source = beats[key]
            preview = frame(key,number,source["heading"],time,"",source["start"]+time,total)
            preview.thumbnail((540,304))
            data = BytesIO()
            preview.save(data,format="PNG")
            data.seek(0)
            doc.drawImage(ImageReader(data),42,y-93,165,93)
            cursor = y+1
            for name, content in (("Visual",vis),("Narration",narr),("Math",math)):
                cursor = paragraph(doc,221,cursor,f"<b>{name}.</b> {escape(content)}",332,9.8,leading=12.5)-5
            y = min(y-94,cursor)-18
            doc.setStrokeColor(LINE)
            doc.line(42,y,553,y)
            y -= 21
        if page:
            paragraph(doc,42,min(y,139),
                      '<b>References</b><br/>M3 Animation Video Project Instructions.<br/>'
                      f'OpenStax, Algebra and Trigonometry 2e, <link href="{SOURCE}" color="#086655">§11.6 Solving Systems with Gaussian Elimination</link>.<br/>'
                      '<b>Production</b> OpenAI Codex assisted with script, visuals and code. Piper / Lessac supplies the synthetic guide narration. No music.',
                      511,9.4, leading=12)
        doc.showPage()
    doc.save()

def script(timeline, destination):
    doc = canvas.Canvas(str(destination),pagesize=PAGE)
    doc.setTitle("Gaussian Elimination | Voice-over Script")
    doc.setAuthor(STUDENT)
    groups = [timeline[:5], timeline[5:10], timeline[10:15], timeline[15:19], timeline[19:]]
    for i, group in enumerate(groups):
        heading(doc,i+1,len(groups),"M3 ANIMATION PROJECT / RECORDING SCRIPT","Gaussian elimination",
                "Six-minute cut  /  timed voice-over and recording cues")
        y = 672
        if i == 0:
            paragraph(doc,42,y+7,"Use the silent MP4 in your editor. Start each spoken block about half a second after its printed start time. Read the main paragraph aloud. The italic line gives a performance cue. Pronounce Gaussian as <b>GOW-see-un</b>.",511,10.5)
            y -= 58
        for beat in group:
            count = timeline.index(beat)+1
            start = stamp(beat["start"])
            end = stamp(beat["start"]+beat["duration"])
            text(doc,42,y,f"{count:02d}   {start}–{end}",9,"Bold",TEAL)
            text(doc,146,y,beat["heading"],14,"Bold")
            y = paragraph(doc,42,y-12,escape(beat["narration"]),511,11.2,leading=15.2)
            y = paragraph(doc,42,y-4,f"<i>{escape(RECORDING_CUES[beat['key']])}</i>",511,9.5,GREY,12.3)-12
            doc.setStrokeColor(LINE)
            doc.line(42,y,553,y)
            y -= 19
        if y < 54:
            raise ValueError(f"Script page {i+1} extends beyond the content area.")
        doc.showPage()
    doc.save()

pdfmetrics.registerFontFamily("Body", normal="Body", bold="Bold", italic="Italic", boldItalic="Bold")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("timing",type=Path)
    parser.add_argument("output",type=Path)
    args = parser.parse_args()
    timeline = json.loads(args.timing.read_text())
    storyboard(timeline,args.output/"Gaussian_Elimination_V2_Storyboard.pdf")
    script(timeline,args.output/"Gaussian_Elimination_V2_Voiceover_Script.pdf")

if __name__ == "__main__":
    main()
