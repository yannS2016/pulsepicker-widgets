#!/usr/bin/env python3
"""Generate the pp_widget variants from one shared layout builder.

pp_widget_static.ui : static wheel, OPEN/CLOSE top, wheel, FLIP FLOP/BURST bottom,
                      HOME/STOP in a Control area.
pp_widget_v3.ui     : static wheel, OPEN/CLOSE top, HOME|wheel|STOP, FLIP FLOP/BURST
                      bottom (all six around the wheel).
pp_widget_anim.ui   : live PulsePicker, modern layout (wheel in status + 2x3 grid).

Restrained palette. Readback fields are greyed out to distinguish them from
writable fields. Run: python gen_pp_widget.py
"""

import json

P = "ca://${prefix}"
CONFIG = "pp_config3.ui"

def _xml(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def mode_hl_rule(value):
    """Rule: the selected mode button (mode readback == its press value) stays at
    full opacity while the others dim -- highlighting the active mode."""
    rule = [{"name": "ModeHL", "property": "Opacity", "initial_value": 1.0,
             "expression": "1.0 if ch[0]==" + str(value) + " else 0.45",
             "channels": [{"channel": "ca://${prefix}:MMS:01:eModeSelector_RBV", "trigger": True}],
             "notes": ""}]
    return _xml(json.dumps(rule))

# Wheel-centre pill: show OPENED / CLOSED from the blade in/out status.
STATE_RULE = ("[{&quot;name&quot;: &quot;State&quot;, &quot;property&quot;: &quot;Text&quot;, &quot;initial_value&quot;: &quot;--&quot;, "
              "&quot;expression&quot;: &quot;'OPENED' if (ch[0]==2) else 'CLOSED' if (ch[0]==1) else '--'&quot;, "
              "&quot;channels&quot;: [{&quot;channel&quot;: &quot;ca://${prefix}:MMS:03:eInOutStatus_RBV&quot;, "
              "&quot;trigger&quot;: true, &quot;use_enum&quot;: false}], &quot;notes&quot;: &quot;&quot;}]")

GRAD = ("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2C3E50, stop:1 #34495E);"
        " color: white; border-radius: 8px; font-size: 20pt; font-weight: bold; padding: 8px;")
SLATE = "background-color: #7F8C8D; color: white; font-weight: bold; padding: 3px; border-radius: 3px;"
# greyed read-only vs crisp white writable (kept for symmetry with the config screen)
RB_FIELD = "background-color: #e4e7ea; color: #4a5259; border: 1px solid #b6bcc2; border-radius: 3px;"
WR_FIELD = "background-color: #ffffff; color: #0c0c0c; border: 1px solid #546e7a; border-radius: 3px;"
CAP = "color: #333; font-weight: bold;"
GREEN = "#1E8449"; RED = "#E74C3C"; BLUE = "rgb(54,64,153)"; SLATEC = "#7F8C8D"
STOP_COLOR = "rgb(170, 0, 0)"  # matches the Stop button in MotorClassicFull

INOUT = ("[{&quot;name&quot;: &quot;InOutString&quot;, &quot;property&quot;: &quot;Text&quot;, "
         "&quot;initial_value&quot;: &quot;--&quot;, &quot;expression&quot;: &quot;'Unknown' if (ch[0]==0) "
         "else 'In' if (ch[0]==1) else 'Out' if (ch[0]==2) else 'Unknown'&quot;, &quot;channels&quot;: "
         "[{&quot;channel&quot;: &quot;ca://${prefix}:MMS:03:eInOutStatus_RBV&quot;, &quot;trigger&quot;: true, "
         "&quot;use_enum&quot;: true}], &quot;notes&quot;: &quot;&quot;}]")
MODE = ("[{&quot;name&quot;: &quot;ModeString&quot;, &quot;property&quot;: &quot;Text&quot;, "
        "&quot;initial_value&quot;: &quot;--&quot;, &quot;expression&quot;: &quot;'No Mode' if (ch[0]==0) else "
        "'Flip Flop' if (ch[0]==1) else 'Burst' if (ch[0]==2) else 'Open' if (ch[0]==3) else 'Close' if "
        "(ch[0]==4) else 'Home' if (ch[0]==5) else 'Unknown'&quot;, &quot;channels&quot;: [{&quot;channel&quot;: "
        "&quot;ca://${prefix}:MMS:01:eModeSelector_RBV&quot;, &quot;trigger&quot;: true, &quot;use_enum&quot;: "
        "false}], &quot;notes&quot;: &quot;&quot;}]")

_n = [0]
def uid(b):
    _n[0] += 1; return f"{b}_{_n[0]}"

def item(x): return f'<item>{x}</item>'
def gitem(x, r, c): return f'<item row="{r}" column="{c}">{x}</item>'

def hspacer():
    return ('<spacer name="'+uid("hs")+'"><property name="orientation"><enum>Qt::Horizontal</enum></property>'
            '<property name="sizeHint" stdset="0"><size><width>20</width><height>20</height></size></property></spacer>')

def hbox(*widgets, spacing=8):
    inner = "".join(item(w) for w in widgets)
    return f'<layout class="QHBoxLayout" name="{uid("hb")}"><property name="spacing"><number>{spacing}</number></property>{inner}</layout>'

def vspacer():
    return ('<spacer name="'+uid("vs")+'"><property name="orientation"><enum>Qt::Vertical</enum></property>'
            '<property name="sizeHint" stdset="0"><size><width>20</width><height>20</height></size></property></spacer>')

def label(text, style, align="Qt::AlignCenter", minh=0, minw=0, maxh=0):
    ms = f'<property name="minimumSize"><size><width>{minw}</width><height>{minh}</height></size></property>' if (minh or minw) else ''
    mx = f'<property name="maximumSize"><size><width>16777215</width><height>{maxh}</height></size></property>' if maxh else ''
    return (f'<widget class="QLabel" name="{uid("lbl")}"><property name="styleSheet"><string notr="true">{style}</string></property>{ms}{mx}'
            f'<property name="text"><string>{text}</string></property><property name="alignment"><set>{align}</set></property></widget>')

def header(text):
    return label(text, SLATE)

def pydm_label(chan, rules=""):
    rp = f'<property name="rules" stdset="0"><string>{rules}</string></property>' if rules else ''
    return (f'<widget class="PyDMLabel" name="{uid("rb")}"><property name="minimumSize"><size><width>0</width><height>30</height></size></property>'
            f'<property name="sizePolicy"><sizepolicy hsizetype="Expanding" vsizetype="Fixed"><horstretch>1</horstretch><verstretch>0</verstretch></sizepolicy></property>'
            f'<property name="styleSheet"><string notr="true">{RB_FIELD}</string></property><property name="alignment"><set>Qt::AlignCenter</set></property>'
            f'<property name="text"><string>--</string></property>{rp}'
            f'<property name="channel" stdset="0"><string>{chan}</string></property></widget>')

def pydm_lineedit(chan, fmt=False):
    df = '<property name="displayFormat" stdset="0"><enum>PyDMLineEdit::String</enum></property>' if fmt else ''
    return (f'<widget class="PyDMLineEdit" name="{uid("le")}"><property name="minimumSize"><size><width>0</width><height>30</height></size></property>'
            f'<property name="sizePolicy"><sizepolicy hsizetype="Expanding" vsizetype="Fixed"><horstretch>1</horstretch><verstretch>0</verstretch></sizepolicy></property>'
            f'<property name="styleSheet"><string notr="true">{RB_FIELD}</string></property><property name="alignment"><set>Qt::AlignCenter</set></property>'
            f'<property name="readOnly"><bool>true</bool></property>{df}'
            f'<property name="channel" stdset="0"><string>{chan}</string></property></widget>')

def readrow(cap, field):
    return (f'<layout class="QHBoxLayout" name="{uid("rr")}"><property name="spacing"><number>6</number></property>'
            f'{item(label(cap, CAP, "Qt::AlignRight|Qt::AlignVCenter", 30, 78))}{item(field)}</layout>')

def mode_btn(text, value, color, confirm, expand=True, highlight=True):
    cd = ('<property name="showConfirmDialog" stdset="0"><bool>true</bool></property>'
          f'<property name="confirmMessage" stdset="0"><string>Set mode to {text}?</string></property>') if confirm else \
         '<property name="showConfirmDialog" stdset="0"><bool>false</bool></property>'
    sp = ('<property name="sizePolicy"><sizepolicy hsizetype="Expanding" vsizetype="Fixed"><horstretch>1</horstretch><verstretch>0</verstretch></sizepolicy></property>') if expand else ''
    ss = f'QPushButton {{ color: white; background-color: {color}; font-size: 10pt; font-weight: bold; border-radius: 5px; padding: 3px 10px; }}'
    rules = f'<property name="rules" stdset="0"><string>{mode_hl_rule(value)}</string></property>' if highlight else ''
    return (f'<widget class="PyDMPushButton" name="{uid("mb")}"><property name="minimumSize"><size><width>0</width><height>30</height></size></property>'
            f'<property name="maximumSize"><size><width>16777215</width><height>32</height></size></property>{sp}'
            f'<property name="styleSheet"><string notr="true">{ss}</string></property><property name="text"><string>{text}</string></property>{rules}'
            f'<property name="channel" stdset="0"><string>{P}:MMS:01:eModeSelector</string></property>'
            f'<property name="pressValue" stdset="0"><string>{value}</string></property>{cd}'
            f'<property name="releaseValue" stdset="0"><string>None</string></property></widget>')

def static_wheel():
    # Fixed 200x196 frame so the absolute ring/bars never stretch out of alignment.
    # Ring centered at (100, 98); the two slit bars are symmetric about y=98.
    ring = ('<widget class="QLabel" name="StaticRing"><property name="geometry"><rect><x>12</x><y>10</y><width>176</width><height>176</height></rect></property>'
            '<property name="styleSheet"><string notr="true">background: transparent; border: 15px solid #546e7a; border-radius: 88px;</string></property>'
            '<property name="text"><string/></property></widget>')
    bar1 = ('<widget class="QLabel" name="StaticBar1"><property name="geometry"><rect><x>40</x><y>77</y><width>120</width><height>18</height></rect></property>'
            '<property name="styleSheet"><string notr="true">background: #00c853; border-radius: 4px;</string></property><property name="text"><string/></property></widget>')
    bar2 = ('<widget class="QLabel" name="StaticBar2"><property name="geometry"><rect><x>40</x><y>101</y><width>120</width><height>18</height></rect></property>'
            '<property name="styleSheet"><string notr="true">background: #00c853; border-radius: 4px;</string></property><property name="text"><string/></property></widget>')
    # Centre pill: OPENED / CLOSED from the blade in/out status.
    state = ('<widget class="PyDMLabel" name="PickerState"><property name="geometry"><rect><x>42</x><y>82</y><width>116</width><height>32</height></rect></property>'
             '<property name="styleSheet"><string notr="true">background: rgba(38,50,56,0.9); color: white; border-radius: 6px; font-weight: bold; font-size: 12pt;</string></property>'
             '<property name="alignment"><set>Qt::AlignCenter</set></property><property name="text"><string>--</string></property>'
             f'<property name="rules" stdset="0"><string>{STATE_RULE}</string></property>'
             '<property name="channel" stdset="0"><string>ca://${prefix}:MMS:03:eInOutStatus_RBV</string></property></widget>')
    return (f'<widget class="QFrame" name="StaticWheel">'
            f'<property name="sizePolicy"><sizepolicy hsizetype="Fixed" vsizetype="Fixed"><horstretch>0</horstretch><verstretch>0</verstretch></sizepolicy></property>'
            f'<property name="minimumSize"><size><width>200</width><height>196</height></size></property>'
            f'<property name="maximumSize"><size><width>200</width><height>196</height></size></property>{ring}{bar1}{bar2}{state}</widget>')

def pulse_picker():
    return ('<widget class="PulsePicker" name="PulsePicker"><property name="minimumSize"><size><width>150</width><height>145</height></size></property>'
            f'<property name="channelsPrefix" stdset="0"><string>{P}</string></property>'
            '<property name="stateSuffix" stdset="0"><string>:MMS:03:eInOutStatus_RBV</string></property>'
            '<property name="positionSuffix" stdset="0"><string/></property></widget>')

def expert_button():
    return ('<widget class="PyDMRelatedDisplayButton" name="ExpertButton"><property name="minimumSize"><size><width>0</width><height>28</height></size></property>'
            f'<property name="styleSheet"><string notr="true">QPushButton {{ background-color: {SLATEC}; color: white; font-weight: bold; padding: 4px 14px; border-radius: 5px; }}</string></property>'
            '<property name="text"><string>Expert</string></property>'
            f'<property name="filenames" stdset="0"><stringlist><string>{CONFIG}</string></stringlist></property>'
            '<property name="macros" stdset="0"><stringlist><string>{&quot;prefix&quot;: &quot;${prefix}&quot;}</string></stringlist></property>'
            '<property name="openInNewWindow" stdset="0"><bool>true</bool></property>'
            '<property name="PyDMIcon" stdset="0"><string>cog</string></property>'
            '<property name="showIcon" stdset="0"><bool>true</bool></property></widget>')

def framed(name, headertxt, inner_items):
    return (f'<widget class="QFrame" name="{name}"><property name="styleSheet"><string notr="true">QFrame#{name} {{ border: 1px solid #A0A0A0; border-radius: 5px; }}</string></property>'
            f'<property name="frameShape"><enum>QFrame::StyledPanel</enum></property>'
            f'<layout class="QVBoxLayout" name="{uid("fv")}"><property name="spacing"><number>7</number></property>'
            f'<property name="leftMargin"><number>8</number></property><property name="topMargin"><number>8</number></property>'
            f'<property name="rightMargin"><number>8</number></property><property name="bottomMargin"><number>8</number></property>'
            f'{item(header(headertxt))}{inner_items}</layout></widget>')

CUSTOM_STATIC = """
 <customwidgets>
  <customwidget><class>PyDMLabel</class><extends>QLabel</extends><header>pydm.widgets.label</header></customwidget>
  <customwidget><class>PyDMLineEdit</class><extends>QLineEdit</extends><header>pydm.widgets.line_edit</header></customwidget>
  <customwidget><class>PyDMPushButton</class><extends>QPushButton</extends><header>pydm.widgets.pushbutton</header></customwidget>
  <customwidget><class>PyDMRelatedDisplayButton</class><extends>QPushButton</extends><header>pydm.widgets.related_display_button</header></customwidget>
 </customwidgets>
"""
CUSTOM_ANIM = CUSTOM_STATIC.replace(" </customwidgets>",
  '  <customwidget><class>PulsePicker</class><extends>QWidget</extends><header>pcdswidgets.beam.pulse_picker</header></customwidget>\n </customwidgets>')

def build(wheel, custom, layout="modern"):
    reads = (f'{item(readrow("Blade", pydm_label(P+":MMS:03:eInOutStatus_RBV", INOUT)))}'
             f'{item(readrow("Frequency", pydm_lineedit(P+":MMS:01:fCurrentTriggerFrequency_RBV")))}'
             f'{item(readrow("Mode", pydm_label(P+":MMS:01:eModeSelector_RBV", MODE)))}')
    rb_vbox = f'<layout class="QVBoxLayout" name="{uid("rv")}"><property name="spacing"><number>7</number></property>{reads}</layout>'
    err = readrow("Error", pydm_lineedit(P+":MMS:01:sErrorMessage_RBV", fmt=True))
    footer = (f'<layout class="QHBoxLayout" name="footer">'
              f'<item><spacer name="fsp"><property name="orientation"><enum>Qt::Horizontal</enum></property>'
              f'<property name="sizeHint" stdset="0"><size><width>40</width><height>20</height></size></property></spacer></item>'
              f'{item(expert_button())}</layout>')
    title = label("Pulse Picker", GRAD, maxh=62)

    o = mode_btn("OPEN", "3", GREEN, True); c = mode_btn("CLOSE", "4", RED, True)
    ff = mode_btn("FLIP FLOP", "1", BLUE, False); bu = mode_btn("BURST", "2", BLUE, False)

    if layout == "stacked":
        # Just the mode block: OPEN/CLOSE on top, wheel (shows OPENED/CLOSED), FLIP
        # FLOP/BURST below. Status + HOME/STOP live on the config screen now.
        inner = item(hbox(o, c)) + item(hbox(hspacer(), wheel, hspacer())) + item(hbox(ff, bu))
        mode = framed("ModeFrame", "Mode", inner)
        body_items = item(title) + item(mode) + item(vspacer()) + item(footer)
    elif layout == "surround":
        # OPEN/CLOSE on top, HOME | wheel | STOP, FLIP FLOP/BURST below.
        # HOME/STOP fit their text so the wheel keeps the central space.
        ho = mode_btn("HOME", "5", BLUE, True, expand=False); st = mode_btn("STOP", "0", STOP_COLOR, False, expand=False)
        status = framed("StatusFrame", "Current Status", item(rb_vbox) + item(err))
        inner = item(hbox(o, c)) + item(hbox(ho, wheel, st)) + item(hbox(ff, bu))
        mode = framed("ModeFrame", "Mode", inner)
        body_items = item(title) + item(status) + item(mode) + item(footer)
    else:
        # modern: wheel in status, 2x3 mode grid
        ho = mode_btn("HOME", "5", BLUE, True); st = mode_btn("STOP", "0", STOP_COLOR, False)
        body = f'<layout class="QHBoxLayout" name="{uid("sb")}"><property name="spacing"><number>10</number></property>{item(wheel)}{item(rb_vbox)}</layout>'
        status = framed("StatusFrame", "Current Status", item(body) + item(err))
        grid = (f'<layout class="QGridLayout" name="modeGrid"><property name="horizontalSpacing"><number>8</number></property>'
                f'<property name="verticalSpacing"><number>8</number></property>'
                f'{gitem(o,0,0)}{gitem(c,0,1)}{gitem(ff,1,0)}{gitem(bu,1,1)}{gitem(ho,2,0)}{gitem(st,2,1)}</layout>')
        mode = framed("ModeFrame", "Mode Control", item(grid))
        body_items = item(title) + item(status) + item(mode) + item(footer)

    return (f'<?xml version="1.0" encoding="UTF-8"?>\n<ui version="4.0">\n <class>Form</class>\n'
            f' <widget class="QWidget" name="Form"><property name="geometry"><rect><x>0</x><y>0</y><width>420</width><height>560</height></rect></property>'
            f'<property name="minimumSize"><size><width>420</width><height>0</height></size></property>'
            f'<property name="windowTitle"><string>Pulse Picker</string></property>'
            f'<layout class="QVBoxLayout" name="mainLayout"><property name="spacing"><number>8</number></property>'
            f'<property name="leftMargin"><number>8</number></property><property name="topMargin"><number>8</number></property>'
            f'<property name="rightMargin"><number>8</number></property><property name="bottomMargin"><number>8</number></property>'
            f'{body_items}</layout></widget>\n{custom} <resources/>\n <connections/>\n</ui>\n')

if __name__ == "__main__":
    _n[0] = 0; open("pp_widget_static.ui", "w").write(build(static_wheel(), CUSTOM_STATIC, layout="stacked"))
    _n[0] = 0; open("pp_widget_v3.ui", "w").write(build(static_wheel(), CUSTOM_STATIC, layout="surround"))
    _n[0] = 0; open("pp_widget_anim.ui", "w").write(build(pulse_picker(), CUSTOM_ANIM, layout="modern"))
    print("wrote pp_widget_static.ui, pp_widget_v3.ui, pp_widget_anim.ui")
