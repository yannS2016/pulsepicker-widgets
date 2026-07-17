#!/usr/bin/env python3
"""Generate candidate redesigns of pp_config3.ui from one shared catalog.

Model B (tabs, one per axis) is the chosen design; A (cards) and C (stacked) are
also emitted for reference. Restrained palette reused from the existing screens.
Each axis tab: its own settings + a Center button/LED + a button to open the
motor widget (MotorClassicFull) via pp_motor.ui.  Run:  python gen_pp_config.py
"""

import json

P = "ca://${prefix}"                     # channel prefix; ${prefix} expanded by pydm

GRAD = ("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
        "stop:0 #2C3E50, stop:1 #34495E); color: white; border-radius: 8px; "
        "font-size: 18pt; font-weight: bold; padding: 8px;")
SLATE = "background-color: #7F8C8D; color: white; font-weight: bold; padding: 3px; border-radius: 3px;"
FIELD = "background-color: rgb(249, 249, 249); color: rgb(12, 12, 12); border: 1px solid #A0A0A0; border-radius: 3px;"
# read-only readbacks look greyed-out; writable fields look crisp white.
RB_FIELD = "background-color: #e4e7ea; color: #4a5259; border: 1px solid #b6bcc2; border-radius: 3px;"
WR_FIELD = "background-color: #ffffff; color: #0c0c0c; border: 1px solid #546e7a; border-radius: 3px;"
BLUE = ("QPushButton { color: white; background-color: rgb(54,64,153); font-weight: bold; border-radius: 4px; }"
        " QPushButton:hover { background-color: #21618C; }")
CAP = "color: #333; font-weight: bold;"
STOP_BTN = "QPushButton { color: white; background-color: rgb(170,0,0); font-weight: bold; border-radius: 4px; } QPushButton:hover { background-color: #7a0000; }"
INOUT_RULE = ("[{&quot;name&quot;: &quot;InOut&quot;, &quot;property&quot;: &quot;Text&quot;, &quot;initial_value&quot;: &quot;--&quot;, "
  "&quot;expression&quot;: &quot;'Unknown' if (ch[0]==0) else 'In' if (ch[0]==1) else 'Out' if (ch[0]==2) else 'Unknown'&quot;, "
  "&quot;channels&quot;: [{&quot;channel&quot;: &quot;ca://${prefix}:MMS:03:eInOutStatus_RBV&quot;, &quot;trigger&quot;: true, &quot;use_enum&quot;: true}], &quot;notes&quot;: &quot;&quot;}]")
MODE_RULE = ("[{&quot;name&quot;: &quot;Mode&quot;, &quot;property&quot;: &quot;Text&quot;, &quot;initial_value&quot;: &quot;--&quot;, "
  "&quot;expression&quot;: &quot;'No Mode' if (ch[0]==0) else 'Flip Flop' if (ch[0]==1) else 'Burst' if (ch[0]==2) else 'Open' if (ch[0]==3) else 'Close' if (ch[0]==4) else 'Home' if (ch[0]==5) else 'Unknown'&quot;, "
  "&quot;channels&quot;: [{&quot;channel&quot;: &quot;ca://${prefix}:MMS:01:eModeSelector_RBV&quot;, &quot;trigger&quot;: true, &quot;use_enum&quot;: false}], &quot;notes&quot;: &quot;&quot;}]")

def rule_xml(rule):
    """JSON-encode a rules list and XML-escape it for a .ui <string> property."""
    return (json.dumps(rule).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))

# Consolidated status error: for each stage whose bError_RBV flag is set, decode
# its :sErrorMessage_RBV char waveform, tag it with the stage, and combine multiple
# with "; " -- else "No errors". Channels are paired per stage: [bError, message]
# x3, so ch[2*i] is the flag and ch[2*i+1] the message for stage i.
ALLERR_RULE = rule_xml([{
    "name": "AllErrors", "property": "Text", "initial_value": "--",
    "expression": ("'; '.join((bytes(int(c) for c in np.atleast_1d(ch[2*i+1]) if c)"
                   ".decode('latin-1', 'ignore').strip() or 'error') + ' [' + n + ']' "
                   "for i, n in enumerate(['Spindle', 'X', 'Y']) "
                   "if ch[2*i] and ch[2*i+1] is not None) or 'No errors'"),
    "channels": [
        {"channel": "ca://${prefix}:MMS:01:bError_RBV",        "trigger": True, "use_enum": False},
        {"channel": "ca://${prefix}:MMS:01:sErrorMessage_RBV", "trigger": True, "use_enum": False},
        {"channel": "ca://${prefix}:MMS:02:bError_RBV",        "trigger": True, "use_enum": False},
        {"channel": "ca://${prefix}:MMS:02:sErrorMessage_RBV", "trigger": True, "use_enum": False},
        {"channel": "ca://${prefix}:MMS:03:bError_RBV",        "trigger": True, "use_enum": False},
        {"channel": "ca://${prefix}:MMS:03:sErrorMessage_RBV", "trigger": True, "use_enum": False},
    ],
    "notes": "",
}])

# motor -> (title, mms, [ (caption, kind, rbv_suffix, set_suffix) ], [ (btn_text, pv_suffix, value) ])
# kind: ro | set | byte | bypass.  Suffixes are appended AFTER ":<mms>".
CATALOG = {
    "spindle": ("Spindle", "MMS:01", [
        # Frequency lives in the status bar above, so it is not repeated here.
        ("Center", "set", ":fCenter_RBV", ":fCenter"),
        ("Center Offset", "set", ":fCenterOffset_RBV", ":fCenterOffset"),
        ("+ Close", "set", ":fStopPos_RBV", ":fStopPos"),
        ("- Close", "set", ":fStopNeg_RBV", ":fStopNeg"),
        ("+ Viol Lim", "set", ":fLimitPos_RBV", ":fLimitPos"),
        ("- Viol Lim", "set", ":fLimitNeg_RBV", ":fLimitNeg"),
        ("+ Viol Cnt", "ro", ":nOvrCntPos_RBV", None),
        ("- Viol Cnt", "ro", ":nOvrCntNeg_RBV", None),
    ], [
        ("Reset", ":bReset", "1"),
        ("Reset Viol.", ":bResetCnt", "1"),
    ]),
    "x": ("X-axis", "MMS:02", [
        ("Travel Min", "ro", ":fXLimMin_RBV", None),
        ("Travel Max", "ro", ":fXLimMax_RBV", None),
        ("Center Min", "ro", ":fXCenterLimMin_RBV", None),
        ("Center Max", "ro", ":fXCenterLimMax_RBV", None),
        ("Center Offset", "set", ":fXCenterOffset_RBV", ":fXCenterOffset"),
        ("EPS Bypass", "bypass", ":bXEpsBypass_RBV", ":bXEpsBypass"),
    ], []),
    "y": ("Y-axis", "MMS:03", [
        ("Travel Min", "ro", ":fYLimMin_RBV", None),
        ("Travel Max", "ro", ":fYLimMax_RBV", None),
        ("Travel Mid", "ro", ":fYLimMedium_RBV", None),
        ("Center Offset", "set", ":fYCenterOffset_RBV", ":fYCenterOffset"),
        ("In/Out Thresh", "ro", ":fInOutThrsh_RBV", None),
        ("EPS Bypass", "bypass", ":bYEpsBypass_RBV", ":bYEpsBypass"),
    ], []),
}
ORDER = ["spindle", "x", "y"]

# Home: LED = <mms>:bCentered_RBV. The spindle sets its mode to Home
# (eModeSelector=5); the X/Y linear stages home via the tcmotor high-limit field
# (<mms>.HOMR, eHomeMode=2) from ioc-common-ads-ioc.
CENTER_LED = ":bCentered_RBV"
CENTER = {"MMS:01": (":eModeSelector", "5"), "MMS:02": (".HOMR", "1"), "MMS:03": (".HOMR", "1")}
def center_cmd(mms):
    return CENTER.get(mms, (".HOMR", "1"))

_n = [0]
def uid(base):
    _n[0] += 1
    return f"{base}_{_n[0]}"

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def chan(mms, suffix):
    return f"{P}:{mms}{suffix}"

def label(text, style, align="Qt::AlignCenter", minh=0, minw=0):
    ms = ""
    if minh or minw:
        ms = f'<property name="minimumSize"><size><width>{minw}</width><height>{minh}</height></size></property>'
    return (f'<widget class="QLabel" name="{uid("lbl")}">'
            f'<property name="styleSheet"><string notr="true">{style}</string></property>{ms}'
            f'<property name="text"><string>{esc(text)}</string></property>'
            f'<property name="alignment"><set>{align}</set></property></widget>')

def _fieldsize(minh, fix_w):
    # fix_w>0 -> fixed width (readback & write end up identical); else expanding.
    if fix_w:
        return (f'<property name="minimumSize"><size><width>{fix_w}</width><height>{minh}</height></size></property>'
                f'<property name="maximumSize"><size><width>{fix_w}</width><height>16777215</height></size></property>'
                f'<property name="sizePolicy"><sizepolicy hsizetype="Fixed" vsizetype="Fixed"><horstretch>0</horstretch><verstretch>0</verstretch></sizepolicy></property>')
    return (f'<property name="minimumSize"><size><width>0</width><height>{minh}</height></size></property>'
            f'<property name="sizePolicy"><sizepolicy hsizetype="Expanding" vsizetype="Fixed"><horstretch>1</horstretch><verstretch>0</verstretch></sizepolicy></property>')

def pydm_label(address, minh=30, fix_w=0, rules="", disp_fmt=None, hignore=False):
    rp = f'<property name="rules" stdset="0"><string>{rules}</string></property>' if rules else ''
    # displayFormat="String" decodes a char/byte waveform (e.g. an error message
    # PV) into text instead of showing the raw byte array.
    df = (f'<property name="displayFormat" stdset="0"><enum>PyDMLabel::{disp_fmt}</enum></property>'
          if disp_fmt else '')
    size = _fieldsize(minh, fix_w)
    if hignore:
        # Ignored horizontal policy: fills available width but never lets a long
        # string grow the layout, so the error text can't resize the window.
        size = (f'<property name="minimumSize"><size><width>0</width><height>{minh}</height></size></property>'
                f'<property name="sizePolicy"><sizepolicy hsizetype="Ignored" vsizetype="Fixed"><horstretch>1</horstretch><verstretch>0</verstretch></sizepolicy></property>')
    return (f'<widget class="PyDMLabel" name="{uid("rb")}">{size}'
            f'<property name="styleSheet"><string notr="true">{RB_FIELD}</string></property>'
            f'<property name="alignment"><set>Qt::AlignCenter</set></property>'
            f'<property name="text"><string>--</string></property>{rp}{df}'
            f'<property name="channel" stdset="0"><string>{address}</string></property></widget>')

def pydm_lineedit(address, minh=30, fix_w=0):
    return (f'<widget class="PyDMLineEdit" name="{uid("set")}">{_fieldsize(minh, fix_w)}'
            f'<property name="styleSheet"><string notr="true">{WR_FIELD}</string></property>'
            f'<property name="alignment"><set>Qt::AlignCenter</set></property>'
            f'<property name="channel" stdset="0"><string>{address}</string></property></widget>')

def pydm_byte(address):
    return (f'<widget class="PyDMByteIndicator" name="{uid("byte")}">'
            f'<property name="minimumSize"><size><width>20</width><height>20</height></size></property>'
            f'<property name="channel" stdset="0"><string>{address}</string></property>'
            f'<property name="showLabels" stdset="0"><bool>false</bool></property>'
            f'<property name="circles" stdset="0"><bool>true</bool></property>'
            f'<property name="numBits" stdset="0"><number>1</number></property></widget>')

def pydm_combo(address, fix_w=0):
    return (f'<widget class="PyDMEnumComboBox" name="{uid("cmb")}">{_fieldsize(30, fix_w)}'
            f'<property name="styleSheet"><string notr="true">{WR_FIELD}</string></property>'
            f'<property name="channel" stdset="0"><string>{address}</string></property></widget>')

def pydm_button(text, address, value, minh=30, expanding=False, style=None):
    sp = ('<property name="sizePolicy"><sizepolicy hsizetype="Expanding" vsizetype="Fixed">'
          '<horstretch>1</horstretch><verstretch>0</verstretch></sizepolicy></property>') if expanding else ''
    return (f'<widget class="PyDMPushButton" name="{uid("btn")}">'
            f'<property name="minimumSize"><size><width>0</width><height>{minh}</height></size></property>{sp}'
            f'<property name="styleSheet"><string notr="true">{style or BLUE}</string></property>'
            f'<property name="text"><string>{esc(text)}</string></property>'
            f'<property name="channel" stdset="0"><string>{address}</string></property>'
            f'<property name="pressValue" stdset="0"><string>{value}</string></property>'
            f'<property name="showConfirmDialog" stdset="0"><bool>true</bool></property>'
            f'<property name="confirmMessage" stdset="0"><string>Proceed with {esc(text)}?</string></property></widget>')

def reset_all_button(style=None):
    """Reset button with a dropdown: pick a single stage (Spindle / X / Y) or All.
    Each entry caputs 1 to that stage's MMS:0x:bReset; All chains the three. The
    'titles' give the menu friendly labels instead of the raw caput commands."""
    per = [f'caput ${{prefix}}:MMS:{m:02d}:bReset 1' for m in (1, 2, 3)]
    cmds = per + ['; '.join(per)]
    titles = ["Spindle", "X", "Y", "All"]
    cmd_xml = "".join(f'<string>{c}</string>' for c in cmds)
    ttl_xml = "".join(f'<string>{t}</string>' for t in titles)
    return (f'<widget class="PyDMShellCommand" name="{uid("reset")}">'
            f'<property name="minimumSize"><size><width>0</width><height>30</height></size></property>'
            f'<property name="styleSheet"><string notr="true">{style or BLUE}</string></property>'
            f'<property name="text"><string>Reset</string></property>'
            f'<property name="showIcon" stdset="0"><bool>false</bool></property>'
            f'<property name="runCommandsInFullShell" stdset="0"><bool>true</bool></property>'
            f'<property name="commands" stdset="0"><stringlist>{cmd_xml}</stringlist></property>'
            f'<property name="titles" stdset="0"><stringlist>{ttl_xml}</stringlist></property></widget>')

def motor_related_button(text, mms):
    # All motor buttons open the same pp_motor.ui (three MotorClassicRow); pass the
    # prefix macro so ${prefix} resolves in the popup.
    macro = '{&quot;prefix&quot;: &quot;${prefix}&quot;}'
    return (f'<widget class="PyDMRelatedDisplayButton" name="{uid("mbtn")}">'
            f'<property name="minimumSize"><size><width>0</width><height>32</height></size></property>'
            f'<property name="styleSheet"><string notr="true">{BLUE}</string></property>'
            f'<property name="text"><string>{esc(text)}</string></property>'
            f'<property name="filenames" stdset="0"><stringlist><string>pp_motor.ui</string></stringlist></property>'
            f'<property name="macros" stdset="0"><stringlist><string>{macro}</string></stringlist></property>'
            f'<property name="openInNewWindow" stdset="0"><bool>true</bool></property>'
            f'<property name="PyDMIcon" stdset="0"><string>cog</string></property>'
            f'<property name="showIcon" stdset="0"><bool>true</bool></property></widget>')

def item(x):
    return f'<item>{x}</item>'

def grid_item(x, r, c):
    return f'<item row="{r}" column="{c}">{x}</item>'

def hspacer():
    return ('<spacer name="' + uid("hs") + '"><property name="orientation"><enum>Qt::Horizontal</enum></property>'
            '<property name="sizeHint" stdset="0"><size><width>20</width><height>20</height></size></property></spacer>')

def vspacer():
    return ('<spacer name="' + uid("vs") + '"><property name="orientation"><enum>Qt::Vertical</enum></property>'
            '<property name="sizeHint" stdset="0"><size><width>20</width><height>20</height></size></property></spacer>')

def param_grid(mms, params, cap_w=130, field_fix_w=0):
    # Writable controls (set/bypass) first, read-only (ro/byte) last. Stable, so
    # it keeps relative order within each group. This pushes read-only rows down
    # (e.g. spindle Freq) and lines up the writable rows -- C Off / EPS Bypass --
    # at the same grid rows across the X and Y columns.
    params = sorted(params, key=lambda p: p[1] not in ("set", "bypass"))
    cells = []
    for i, (cap, kind, rbv, setp) in enumerate(params):
        cells.append(grid_item(label(cap, CAP, "Qt::AlignRight|Qt::AlignVCenter", 30, cap_w), i, 0))
        if kind == "byte":
            cells.append(grid_item(pydm_byte(chan(mms, rbv)), i, 1))
        else:
            cells.append(grid_item(pydm_label(chan(mms, rbv), fix_w=field_fix_w), i, 1))
        if kind == "set":
            cells.append(grid_item(pydm_lineedit(chan(mms, setp), fix_w=field_fix_w), i, 2))
        elif kind == "bypass":
            cells.append(grid_item(pydm_combo(chan(mms, setp), fix_w=field_fix_w), i, 2))
    # Center controls live in the same grid: caption | Center button | Center LED.
    r = len(params)
    cells.append(grid_item(label("Home", CAP, "Qt::AlignRight|Qt::AlignVCenter", 30, cap_w), r, 0))
    csuf, cval = center_cmd(mms)
    cells.append(grid_item(pydm_button("Home", chan(mms, csuf), cval), r, 1))
    cells.append(grid_item(pydm_byte(chan(mms, CENTER_LED)), r, 2))
    return (f'<layout class="QGridLayout" name="{uid("grid")}">'
            f'<property name="horizontalSpacing"><number>6</number></property>'
            f'<property name="verticalSpacing"><number>5</number></property>'
            f'{"".join(cells)}</layout>')

def center_row(mms):
    """A row styled like the param rows: 'Center' caption, a Center button that
    starts the centering routine, and a Center LED that lights when centered."""
    csuf, cval = center_cmd(mms)
    return (f'<layout class="QHBoxLayout" name="{uid("centerrow")}">'
            f'{item(label("Center", CAP, "Qt::AlignRight|Qt::AlignVCenter", 30, 130))}'
            f'{item(pydm_button("Center", chan(mms, csuf), cval, expanding=True))}'
            f'{item(pydm_byte(chan(mms, CENTER_LED)))}</layout>')

def tab_content(key):
    title, mms, params, actions = CATALOG[key]
    parts = [item(param_grid(mms, params))]
    if actions:
        act = "".join(item(pydm_button(t, chan(mms, pv), v)) for t, pv, v in actions)
        parts.append(item(f'<layout class="QHBoxLayout" name="{uid("acts")}">{act}</layout>'))
    parts.append(item(vspacer()))
    return (f'<layout class="QVBoxLayout" name="{uid("tv")}">'
            f'<property name="spacing"><number>8</number></property>'
            f'<property name="leftMargin"><number>10</number></property>'
            f'<property name="topMargin"><number>10</number></property>'
            f'<property name="rightMargin"><number>10</number></property>'
            f'<property name="bottomMargin"><number>10</number></property>'
            f'{"".join(parts)}</layout>')

def framed(inner_layout, name, max_w=0):
    mw = f'<property name="maximumSize"><size><width>{max_w}</width><height>16777215</height></size></property>' if max_w else ''
    return (f'<widget class="QFrame" name="{name}">'
            f'<property name="styleSheet"><string notr="true">QFrame#{name} {{ border: 1px solid #A0A0A0; border-radius: 6px; }}</string></property>'
            f'<property name="frameShape"><enum>QFrame::StyledPanel</enum></property>{mw}'
            f'{inner_layout}</widget>')

CUSTOM = """
 <customwidgets>
  <customwidget><class>PyDMLabel</class><extends>QLabel</extends><header>pydm.widgets.label</header></customwidget>
  <customwidget><class>PyDMLineEdit</class><extends>QLineEdit</extends><header>pydm.widgets.line_edit</header></customwidget>
  <customwidget><class>PyDMByteIndicator</class><extends>QWidget</extends><header>pydm.widgets.byte</header></customwidget>
  <customwidget><class>PyDMEnumComboBox</class><extends>QComboBox</extends><header>pydm.widgets.enum_combo_box</header></customwidget>
  <customwidget><class>PyDMPushButton</class><extends>QPushButton</extends><header>pydm.widgets.pushbutton</header></customwidget>
  <customwidget><class>PyDMRelatedDisplayButton</class><extends>QPushButton</extends><header>pydm.widgets.related_display_button</header></customwidget>
  <customwidget><class>PyDMShellCommand</class><extends>QPushButton</extends><header>pydm.widgets.shell_command</header></customwidget>
  <customwidget><class>MotorClassicRow</class><extends>QWidget</extends><header>pcdswidgets.motion.common.motor_classic_row</header></customwidget>
  <customwidget><class>MotorClassicVert</class><extends>QWidget</extends><header>pcdswidgets.motion.common.motor_classic_vert</header></customwidget>
 </customwidgets>
"""

def document(body, w, h):
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n<ui version="4.0">\n <class>Form</class>\n'
            f' <widget class="QWidget" name="Form">\n'
            f'  <property name="geometry"><rect><x>0</x><y>0</y><width>{w}</width><height>{h}</height></rect></property>\n'
            f'  <property name="windowTitle"><string>Pulse Picker Config</string></property>\n'
            f'  <layout class="QVBoxLayout" name="mainLayout">'
            f'<property name="spacing"><number>8</number></property>'
            f'{item(label("Pulse Picker Config", GRAD))}'
            f'{body}</layout>\n </widget>\n{CUSTOM} <resources/>\n <connections/>\n</ui>\n')

def expert_row():
    """A single horizontal row of per-axis Expert buttons, outside the tabs."""
    btns = "".join(item(motor_related_button(f"{CATALOG[k][0]} Expert", CATALOG[k][1])) for k in ORDER)
    hbox = (f'<layout class="QHBoxLayout" name="{uid("erow")}">'
            f'<property name="spacing"><number>8</number></property>{btns}</layout>')
    inner = (f'<layout class="QVBoxLayout" name="{uid("ev")}">'
             f'<property name="spacing"><number>6</number></property>'
             f'{item(label("Motor Expert Screens", SLATE))}{item(hbox)}</layout>')
    return item(framed(inner, uid("expertbox")))

def model_B():
    tabs = []
    for k in ORDER:
        title = CATALOG[k][0]
        page = (f'<widget class="QWidget" name="{uid("tab")}">'
                f'<attribute name="title"><string>{title}</string></attribute>'
                f'{tab_content(k)}</widget>')
        tabs.append(page)
    tabw = (f'<widget class="QTabWidget" name="motorTabs">'
            f'<property name="styleSheet"><string notr="true">'
            f'QTabBar::tab {{ padding: 7px 18px; min-width: 68px; font-weight: bold; }} '
            f'QTabBar::tab:selected {{ background: #34495E; color: white; }}</string></property>'
            f'{"".join(tabs)}</widget>')
    return document(item(tabw) + expert_row(), 560, 560)

def motor_classic_row(mms):
    return (f'<widget class="MotorClassicRow" name="{uid("motor")}">'
            f'<property name="minimumSize"><size><width>0</width><height>46</height></size></property>'
            f'<property name="motor" stdset="0"><string>${{prefix}}:{mms}</string></property></widget>')

def tab_content_embedded(key):
    """Per-axis tab with the motor control (MotorClassicRow) embedded inline below
    the config -- no popup / expert button needed."""
    title, mms, params, actions = CATALOG[key]
    parts = [item(param_grid(mms, params))]
    if actions:
        act = "".join(item(pydm_button(t, chan(mms, pv), v)) for t, pv, v in actions)
        parts.append(item(f'<layout class="QHBoxLayout" name="{uid("acts")}">{act}</layout>'))
    parts.append(item(label("Motor Control", SLATE)))
    parts.append(item(motor_classic_row(mms)))
    parts.append(item(vspacer()))
    return (f'<layout class="QVBoxLayout" name="{uid("tv")}">'
            f'<property name="spacing"><number>8</number></property>'
            f'<property name="leftMargin"><number>10</number></property>'
            f'<property name="topMargin"><number>10</number></property>'
            f'<property name="rightMargin"><number>10</number></property>'
            f'<property name="bottomMargin"><number>10</number></property>'
            f'{"".join(parts)}</layout>')

def model_B_embedded():
    tabs = []
    for k in ORDER:
        title = CATALOG[k][0]
        page = (f'<widget class="QWidget" name="{uid("tab")}">'
                f'<attribute name="title"><string>{title}</string></attribute>'
                f'{tab_content_embedded(k)}</widget>')
        tabs.append(page)
    tabw = (f'<widget class="QTabWidget" name="motorTabs">'
            f'<property name="styleSheet"><string notr="true">'
            f'QTabBar::tab {{ padding: 7px 18px; min-width: 68px; font-weight: bold; }} '
            f'QTabBar::tab:selected {{ background: #34495E; color: white; }}</string></property>'
            f'{"".join(tabs)}</widget>')
    return document(item(tabw), 710, 560)

def model_A():
    cols = "".join(item(framed(tab_content(k), uid("card"))) for k in ORDER)
    body = item(f'<layout class="QHBoxLayout" name="cardsRow"><property name="spacing"><number>8</number></property>{cols}</layout>')
    return document(body, 900, 520)

def model_C():
    panels = "".join(item(framed(tab_content(k), uid("panel"))) for k in ORDER)
    return document(panels, 560, 900)

ABBREV = {
    "Frequency": "Freq", "Center Offset": "C Off", "+ Close": "+Close", "- Close": "-Close",
    "+ Viol Lim": "+VLim", "- Viol Lim": "-VLim", "+ Viol Cnt": "+VCnt", "- Viol Cnt": "-VCnt",
    "Travel Min": "T Min", "Travel Max": "T Max", "Travel Mid": "T Mid",
    "Center Min": "C Min", "Center Max": "C Max", "In/Out Thresh": "Thresh", "EPS Bypass": "Byp",
}

def motor_classic_vert(mms):
    # Expand horizontally only (fill the column width); keep the natural height.
    return (f'<widget class="MotorClassicVert" name="{uid("motorv")}">'
            f'<property name="sizePolicy"><sizepolicy hsizetype="Expanding" vsizetype="Fixed"><horstretch>1</horstretch><verstretch>0</verstretch></sizepolicy></property>'
            f'<property name="minimumSize"><size><width>148</width><height>145</height></size></property>'
            f'<property name="motor" stdset="0"><string>${{prefix}}:{mms}</string></property></widget>')

def compact_column(key):
    """A narrow per-axis column: header, compact params (abbreviated captions,
    readback/write fields the same width), actions, and the vertical motor widget
    expanded to fill the column."""
    title, mms, params, actions = CATALOG[key]
    params = [(ABBREV.get(cap, cap), kind, rbv, setp) for (cap, kind, rbv, setp) in params]
    parts = [item(header_bar(f"{title}", mms)), item(param_grid(mms, params, cap_w=58, field_fix_w=62))]
    if actions:
        act = "".join(item(pydm_button(t, chan(mms, pv), v)) for t, pv, v in actions)
        parts.append(item(f'<layout class="QHBoxLayout" name="{uid("acts")}"><property name="spacing"><number>4</number></property>{act}</layout>'))
    # Expanding spacer above the motor widget pushes it to the bottom of the
    # (equal-height) column, so all three motor sections line up at the same top.
    parts.append(item(vspacer()))
    parts.append(item(motor_classic_vert(mms)))
    return (f'<layout class="QVBoxLayout" name="{uid("cv")}"><property name="spacing"><number>6</number></property>'
            f'<property name="leftMargin"><number>6</number></property><property name="topMargin"><number>6</number></property>'
            f'<property name="rightMargin"><number>6</number></property><property name="bottomMargin"><number>6</number></property>'
            f'{"".join(parts)}</layout>')

def header_bar(title, mms):
    return label(f"{title} ({mms})", SLATE)

def picker_bar():
    """Global picker status (Blade / Frequency / Mode / consolidated Error across
    all stages) + a Reset that propagates to every stage's reset PV."""
    def cap(t): return label(t, CAP, "Qt::AlignRight|Qt::AlignVCenter", 30, 0)
    blade = pydm_label(chan("MMS:03", ":eInOutStatus_RBV"), fix_w=64, rules=INOUT_RULE)
    freq = pydm_label(chan("MMS:01", ":fCurrentTriggerFrequency_RBV"), fix_w=84)
    mode = pydm_label(chan("MMS:01", ":eModeSelector_RBV"), fix_w=90, rules=MODE_RULE)
    error = pydm_label("", rules=ALLERR_RULE, hignore=True)  # consolidated; never resizes the window
    # Home lives on each axis's centering button; a single Reset propagates to
    # every stage's reset PV (replaces the old Stop button).
    reset = reset_all_button()
    row = (f'<layout class="QHBoxLayout" name="{uid("statrow")}"><property name="spacing"><number>6</number></property>'
           f'{item(cap("Blade"))}{item(blade)}{item(cap("Freq"))}{item(freq)}{item(cap("Mode"))}{item(mode)}'
           f'{item(hspacer())}{item(reset)}</layout>')
    erow = (f'<layout class="QHBoxLayout" name="{uid("errrow")}"><property name="spacing"><number>6</number></property>'
            f'{item(cap("Error"))}{item(error)}</layout>')
    inner = (f'<layout class="QVBoxLayout" name="{uid("pbv")}"><property name="spacing"><number>6</number></property>'
             f'<property name="leftMargin"><number>8</number></property><property name="topMargin"><number>6</number></property>'
             f'<property name="rightMargin"><number>8</number></property><property name="bottomMargin"><number>8</number></property>'
             f'{item(label("Status", SLATE))}{item(row)}{item(erow)}</layout>')
    return item(framed(inner, uid("pbar")))

def model_D():
    # Space-optimized: three narrow columns, each with the vertical motor widget.
    cols = "".join(item(framed(compact_column(k), uid("vcol"), max_w=210)) for k in ORDER)
    body = item(f'<layout class="QHBoxLayout" name="vcolsRow"><property name="spacing"><number>6</number></property>{cols}</layout>')
    return document(picker_bar() + body, 664, 777)

def hspacer():
    return ('<spacer name="'+uid("chs")+'"><property name="orientation"><enum>Qt::Horizontal</enum></property>'
            '<property name="sizeHint" stdset="0"><size><width>6</width><height>6</height></size></property></spacer>')


if __name__ == "__main__":
    out = {"pp_config3_A.ui": model_A, "pp_config3_B.ui": model_B,
           "pp_config3_B2.ui": model_B_embedded, "pp_config3_C.ui": model_C,
           "pp_config3_D.ui": model_D,
           # pp_config.ui is the deployed copy of model D (what the pp_widget
           # Expert button opens); emit it here so it never drifts out of sync.
           "pp_config.ui": model_D}
    for fname, fn in out.items():
        _n[0] = 0
        with open(fname, "w") as fd:
            fd.write(fn())
        print("wrote", fname)
