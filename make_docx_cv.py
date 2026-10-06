# -*- coding: utf-8 -*-
"""Generate DOCX from the final CV HTML."""
import os
import re
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

# Paths
html_path = os.path.join('C:', os.sep, 'CREWINTEL', 'cengiz_kilic_cv_final.html')
output_dir = os.path.join('C:', os.sep, 'Users', 'isitm', 'Desktop', 'Cengiz_Kilic_CV_Yenilenmis')

# Read HTML
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Parse sections from HTML
def extract_sections(html):
    """Extract content sections from HTML."""
    sections = []
    # Split by section titles
    parts = re.split(r'<div class="section-title">(.*?)</div>', html)
    for i in range(1, len(parts), 2):
        title = re.sub(r'<[^>]+>', '', parts[i]).strip()
        content = parts[i+1] if i+1 < len(parts) else ''
        sections.append((title, content))
    return sections

def strip_tags(html_text):
    """Strip HTML tags but preserve structure."""
    text = re.sub(r'<li>(.*?)</li>', r'\1', html_text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&middot;', '\u00b7', text)
    text = re.sub(r'&mdash;', '\u2014', text)
    text = re.sub(r'&uuml;', '\u00fc', text)
    text = re.sub(r'&ouml;', '\u00f6', text)
    text = re.sub(r'&ccedil;', '\u00e7', text)
    text = re.sub(r'&scedil;', '\u015f', text)
    text = re.sub(r'&gcedil;', '\u011f', text)
    text = re.sub(r'&icaron;', '\u0131', text)
    text = re.sub(r'&#304;', '\u0130', text)
    text = re.sub(r'&#305;', '\u0131', text)
    text = re.sub(r'&#231;', '\u00e7', text)
    text = re.sub(r'&#351;', '\u015f', text)
    text = re.sub(r'&#287;', '\u011f', text)
    text = re.sub(r'&#246;', '\u00f6', text)
    text = re.sub(r'&#252;', '\u00fc', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# Create document
doc = Document()
for s in doc.sections:
    s.top_margin = Cm(2)
    s.bottom_margin = Cm(2)
    s.left_margin = Cm(2.2)
    s.right_margin = Cm(2.2)

style = doc.styles['Normal']
style.font.name = 'Calibri'
style.font.size = Pt(10)
style.font.color.rgb = RGBColor(0x1a, 0x1a, 0x1a)
style.paragraph_format.space_after = Pt(4)
style.paragraph_format.line_spacing = 1.15

def hd(text, level=1, lv=None):
    if lv is not None:
        level = lv
    h = doc.add_heading(text, level=level)
    for r in h.runs:
        r.font.color.rgb = RGBColor(0x1a, 0x1a, 0x1a)
        r.font.name = 'Calibri'

def pp(text, bold=False, italic=False, sz=10, color=None, align=None, sa=4):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = bold
    r.italic = italic
    r.font.size = Pt(sz)
    r.font.name = 'Calibri'
    if color:
        r.font.color.rgb = RGBColor(*color)
    if align:
        p.alignment = align
    p.paragraph_format.space_after = Pt(sa)
    return p

def bb(text, bp=''):
    p = doc.add_paragraph(style='List Bullet')
    if bp:
        rb = p.add_run(bp)
        rb.bold = True
        rb.font.size = Pt(9.5)
        rb.font.name = 'Calibri'
    r = p.add_run(text)
    r.font.size = Pt(9.5)
    r.font.name = 'Calibri'
    p.paragraph_format.space_after = Pt(2)
    return p

def extract_header(html):
    """Extract header info."""
    # Name
    name_m = re.search(r'<h1>(.*?)</h1>', html)
    name = strip_tags(name_m.group(1)) if name_m else 'Cengiz Kilic'
    
    # Subtitle
    sub_m = re.search(r'class="subtitle">(.*?)</div>', html)
    subtitle = strip_tags(sub_m.group(1)) if sub_m else ''
    
    # Contact
    contact_m = re.search(r'class="contact">(.*?)</div>', html, re.DOTALL)
    contact = strip_tags(contact_m.group(1)) if contact_m else ''
    
    # Meta
    meta_m = re.search(r'class="meta">(.*?)</div>', html)
    meta = strip_tags(meta_m.group(1)) if meta_m else ''
    
    return name, subtitle, contact, meta

def extract_projects(html):
    """Extract project sections."""
    projects = []
    parts = re.split(r'<div class="project">', html)
    for part in parts[1:]:
        name_m = re.search(r'class="proj-name">(.*?)</div>', part)
        stack_m = re.search(r'class="proj-stack">(.*?)</div>', part)
        bullets = re.findall(r'<li>(.*?)</li>', part, re.DOTALL)
        
        name = strip_tags(name_m.group(1)) if name_m else ''
        stack = strip_tags(stack_m.group(1)) if stack_m else ''
        bullet_texts = [strip_tags(b) for b in bullets]
        
        projects.append((name, stack, bullet_texts))
    return projects

def extract_experience(html):
    """Extract experience items."""
    items = []
    parts = re.split(r'<div class="exp-item">', html)
    for part in parts[1:]:
        title_m = re.search(r'class="title">(.*?)</span>', part)
        date_m = re.search(r'class="date">(.*?)</span>', part)
        company_m = re.search(r'class="company">(.*?)</div>', part)
        bullets = re.findall(r'<li>(.*?)</li>', part, re.DOTALL)
        
        title = strip_tags(title_m.group(1)) if title_m else ''
        date = strip_tags(date_m.group(1)) if date_m else ''
        company = strip_tags(company_m.group(1)) if company_m else ''
        bullet_texts = [strip_tags(b) for b in bullets]
        
        items.append((title, date, company, bullet_texts))
    return items

def extract_education(html):
    """Extract education items."""
    items = []
    parts = re.split(r'<div class="edu-item">', html)
    for part in parts[1:]:
        school_m = re.search(r'class="school">(.*?)</span>', part)
        date_m = re.search(r'class="date">(.*?)</span>', part)
        dept_m = re.search(r'class="dept">(.*?)</div>', part)
        detail_m = re.search(r'class="detail">(.*?)</div>', part)
        
        school = strip_tags(school_m.group(1)) if school_m else ''
        date = strip_tags(date_m.group(1)) if date_m else ''
        dept = strip_tags(dept_m.group(1)) if dept_m else ''
        detail = strip_tags(detail_m.group(1)) if detail_m else ''
        
        items.append((school, date, dept, detail))
    return items

def extract_skills(html):
    """Extract skill groups."""
    groups = []
    parts = re.split(r'<div class="skill-group">', html)
    for part in parts[1:]:
        label_m = re.search(r'class="label">(.*?)</div>', part)
        items_m = re.search(r'class="items">(.*?)</div>', part)
        
        label = strip_tags(label_m.group(1)) if label_m else ''
        items = strip_tags(items_m.group(1)) if items_m else ''
        
        groups.append((label, items))
    return groups

# ========== BUILD DOCUMENT ==========

# HEADER
name, subtitle, contact, meta = extract_header(html)
pp(name, bold=True, sz=22, sa=2)
pp(subtitle, sz=10, color=(0x44,0x44,0x44), sa=4)
pp(contact, sz=9, color=(0x33,0x33,0x33), sa=1)
pp(meta, sz=9, color=(0x55,0x55,0x55), sa=8)
doc.add_paragraph().paragraph_format.space_after = Pt(8)

# PROFESYONEL OZET
hd('PROFESYONEL \u00d6ZET', level=2)
summary_m = re.search(r'class="summary">(.*?)</div>\s*</div>', html, re.DOTALL)
if summary_m:
    paragraphs = re.findall(r'<p>(.*?)</p>', summary_m.group(1))
    for p in paragraphs:
        pp(strip_tags(p), sa=4)

# EGITIM
hd('\u0130\u011e\u0130T\u0130M', level=2)
edu_items = extract_education(html)
for school, date, dept, detail in edu_items:
    p = doc.add_paragraph()
    r = p.add_run(school)
    r.bold = True; r.font.size = Pt(10); r.font.name = 'Calibri'
    r2 = p.add_run('  ' + ' ' * 60 + date)
    r2.font.size = Pt(9); r2.font.color.rgb = RGBColor(0x55,0x55,0x55); r2.font.name = 'Calibri'
    p.paragraph_format.space_after = Pt(1)
    pp(dept, sz=9.5, color=(0x33,0x33,0x33), sa=1)
    if detail:
        pp(detail, sz=9, color=(0x55,0x55,0x55), sa=6)
    else:
        pp('', sa=6)

# TEKNIK YETKINLIKLER
hd('TEKN\u0130K YETK\u0130NL\u0130KLER', level=2)
skills = extract_skills(html)
for label, items in skills:
    bb(items, bp=label + ': ')

# PROJELER
hd('PROJELER', level=2)
projects = extract_projects(html)
for name, stack, bullets in projects:
    pp(name, bold=True, sz=10.5, sa=1)
    pp(stack, italic=True, sz=9, color=(0x55,0x55,0x55), sa=3)
    for b in bullets:
        # Try to extract bold prefix
        bold_m = re.match(r'<strong>(.*?)</strong>\s*(.*)', b)
        if bold_m:
            bp = strip_tags(bold_m.group(1)) + ' '
            text = strip_tags(bold_m.group(2))
            bb(text, bp=bp)
        else:
            bb(strip_tags(b))
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

# GIRISIMCILIK
hd('G\u0130R\u0130\u015e\u0130MC\u0130L\u0130K DENEY\u0130M\u0130', level=2)
exp_items = extract_experience(html)
for title, date, company, bullets in exp_items:
    p = doc.add_paragraph()
    r = p.add_run(title)
    r.bold = True; r.font.size = Pt(10); r.font.name = 'Calibri'
    r2 = p.add_run('  ' + ' ' * 60 + date)
    r2.font.size = Pt(9); r2.font.color.rgb = RGBColor(0x55,0x55,0x55); r2.font.name = 'Calibri'
    p.paragraph_format.space_after = Pt(1)
    pp(company, sz=9.5, color=(0x44,0x44,0x44), sa=3)
    for b in bullets:
        bb(strip_tags(b))

# MESLEKI GECMIS
hd('MESLEK\u0130 GE\u00c7M\u0130\u015e', level=2)
# Find the mesleki gecmis section
mg_m = re.search(r'class="section-title">Mesleki Ge.*?</div>(.*?)<div class="two-col"', html, re.DOTALL)
if mg_m:
    mg_text = mg_m.group(1)
    paras = re.findall(r'<p[^>]*>(.*?)</p>', mg_text, re.DOTALL)
    for p_text in paras:
        pp(strip_tags(p_text), sz=9.5, color=(0x33,0x33,0x33), sa=3)
    bullets = re.findall(r'<li>(.*?)</li>', mg_text, re.DOTALL)
    for b in bullets:
        bb(strip_tags(b))

# NITELIKLER
hd('N\u0130TEL\u0130KLER', level=2)
quals_m = re.search(r'class="qualities">(.*?)</div>', html, re.DOTALL)
if quals_m:
    pp(strip_tags(quals_m.group(1)), sz=9.5, color=(0x33,0x33,0x33), sa=6)

# YABANCI DIL
hd('YABANCI D\u0130L', level=2)
lang_m = re.findall(r'class="lang-item">(.*?)</div>', html, re.DOTALL)
for l in lang_m:
    name_m2 = re.search(r'class="lang-name">(.*?)</span>', l)
    level_m2 = re.search(r'class="lang-level">(.*?)</span>', l)
    if name_m2 and level_m2:
        nm = strip_tags(name_m2.group(1))
        lv = strip_tags(level_m2.group(1))
        if 'Ana dil' in lv:
            pp(nm + ' \u2014 ' + lv, bold=True, sz=9.5, sa=1)
        else:
            pp(nm + ' \u2014 ' + lv, sz=9, color=(0x55,0x55,0x55), sa=6)

# KARIYER HEDEFI
hd('KAR\u0130YER HEDEF\u0130', level=2)
obj_m = re.search(r'class="objective">(.*?)</div>', html, re.DOTALL)
if obj_m:
    paras = re.findall(r'<p>(.*?)</p>', obj_m.group(1))
    for p_text in paras:
        pp(strip_tags(p_text), sz=9.5, sa=8)

# REFERANSLAR
hd('REFERANSLAR', level=2)
pp('Talep edilmesi halinde profesyonel referanslar\u0131m payla\u015f\u0131lacakt\u0131r.', sz=9, color=(0x55,0x55,0x55), sa=4)

# FOOTER
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run('CV Updated: September 2026')
r.font.size = Pt(8); r.font.color.rgb = RGBColor(0x99,0x99,0x99); r.font.name = 'Calibri'

# SAVE
docx_path = os.path.join(output_dir, 'cengiz_kilic_cv_final.docx')
doc.save(docx_path)
print('DOCX generated successfully: ' + docx_path)

# List output files
for f in os.listdir(output_dir):
    fpath = os.path.join(output_dir, f)
    sz = os.path.getsize(fpath)
    print(f'  {f} ({sz:,} bytes)')
