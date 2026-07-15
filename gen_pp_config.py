#!/usr/bin/env python3
"""Generate candidate redesigns of pp_config3.ui from one shared catalog.

Model B (tabs, one per axis) is the chosen design; A (cards) and C (stacked) are
also emitted for reference. Restrained palette reused from the existing screens.
Each axis tab: its own settings + a Center button/LED + a button to open the
motor widget (MotorClassicFull) via pp_motor.ui.  Run:  python gen_pp_config.py
"""

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

# motor -> (title, mms, [ (caption, kind, rbv_suffix, set_suffix) ], [ (btn_text, pv_suffix, value) ])
# kind: ro | set | byte | bypass.  Suffixes are appended AFTER ":<mms>".
CATALOG = {
    "spindle": ("Spindle", "MMS:01", [
        ("Frequency", "ro", ":fCurrentTriggerFrequency_RBV", None),
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

# Centering: LED = <mms>:bCentered_RBV (real for spindle; assumed same for X/Y),
# command = <mms>:bCenter (PLACEHOLDER -- confirm real centering-routine PV).
CENTER_LED = ":bCentered_RBV"
CENTER_CMD = ":bCenter"

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

def pydm_label(address, minh=30):
    return (f'<widget class="PyDMLabel" name="{uid("rb")}">'
            f'<property name="minimumSize"><size><width>0</width><height>{minh}</height></size></property>'
            f'<property name="sizePolicy"><sizepolicy hsizetype="Expanding" vsizetype="Fixed"><horstretch>1</horstretch><verstretch>0</verstretch></sizepolicy></property>'
            f'<property name="styleSheet"><string notr="true">{RB_FIELD}</string></property>'
            f'<property name="alignment"><set>Qt::AlignCenter</set></property>'
            f'<property name="text"><string>--</string></property>'
            f'<property name="channel" stdset="0"><string>{address}</string></property></widget>')

def pydm_lineedit(address, minh=30):
    return (f'<widget class="PyDMLineEdit" name="{uid("set")}">'
            f'<property name="minimumSize"><size><width>0</width><height>{minh}</height></size></property>'
            f'<property name="sizePolicy"><sizepolicy hsizetype="Expanding" vsizetype="Fixed"><horstretch>1</horstretch><verstretch>0</verstretch></sizepolicy></property>'
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

def pydm_combo(address):
    return (f'<widget class="PyDMEnumComboBox" name="{uid("cmb")}">'
            f'<property name="minimumSize"><size><width>0</width><height>30</height></size></property>'
            f'<property name="sizePolicy"><sizepolicy hsizetype="Expanding" vsizetype="Fixed"><horstretch>1</horstretch><verstretch>0</verstretch></sizepolicy></property>'
            f'<property name="styleSheet"><string notr="true">{WR_FIELD}</string></property>'
            f'<property name="channel" stdset="0"><string>{address}</string></property></widget>')

def pydm_button(text, address, value, minh=30, expanding=False):
    sp = ('<property name="sizePolicy"><sizepolicy hsizetype="Expanding" vsizetype="Fixed">'
          '<horstretch>1</horstretch><verstretch>0</verstretch></sizepolicy></property>') if expanding else ''
    return (f'<widget class="PyDMPushButton" name="{uid("btn")}">'
            f'<property name="minimumSize"><size><width>0</width><height>{minh}</height></size></property>{sp}'
            f'<property name="styleSheet"><string notr="true">{BLUE}</string></property>'
            f'<property name="text"><string>{esc(text)}</string></property>'
            f'<property name="channel" stdset="0"><string>{address}</string></property>'
            f'<property name="pressValue" stdset="0"><string>{value}</string></property>'
            f'<property name="showConfirmDialog" stdset="0"><bool>true</bool></property>'
            f'<property name="confirmMessage" stdset="0"><string>Proceed with {esc(text)}?</string></property></widget>')

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

def param_grid(mms, params):
    cells = []
    for i, (cap, kind, rbv, setp) in enumerate(params):
        cells.append(grid_item(label(cap, CAP, "Qt::AlignRight|Qt::AlignVCenter", 30, 130), i, 0))
        if kind == "byte":
            cells.append(grid_item(pydm_byte(chan(mms, rbv)), i, 1))
        else:
            cells.append(grid_item(pydm_label(chan(mms, rbv)), i, 1))
        if kind == "set":
            cells.append(grid_item(pydm_lineedit(chan(mms, setp)), i, 2))
        elif kind == "bypass":
            cells.append(grid_item(pydm_combo(chan(mms, setp)), i, 2))
    # Center controls live in the same grid: caption | Center button | Center LED.
    r = len(params)
    cells.append(grid_item(label("Center", CAP, "Qt::AlignRight|Qt::AlignVCenter", 30, 130), r, 0))
    cells.append(grid_item(pydm_button("Center", chan(mms, CENTER_CMD), "1"), r, 1))
    cells.append(grid_item(pydm_byte(chan(mms, CENTER_LED)), r, 2))
    return (f'<layout class="QGridLayout" name="{uid("grid")}">'
            f'<property name="horizontalSpacing"><number>6</number></property>'
            f'<property name="verticalSpacing"><number>5</number></property>'
            f'{"".join(cells)}</layout>')

def center_row(mms):
    """A row styled like the param rows: 'Center' caption, a Center button that
    starts the centering routine, and a Center LED that lights when centered."""
    return (f'<layout class="QHBoxLayout" name="{uid("centerrow")}">'
            f'{item(label("Center", CAP, "Qt::AlignRight|Qt::AlignVCenter", 30, 130))}'
            f'{item(pydm_button("Center", chan(mms, CENTER_CMD), "1", expanding=True))}'
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

def framed(inner_layout, name):
    return (f'<widget class="QFrame" name="{name}">'
            f'<property name="styleSheet"><string notr="true">QFrame#{name} {{ border: 1px solid #A0A0A0; border-radius: 6px; }}</string></property>'
            f'<property name="frameShape"><enum>QFrame::StyledPanel</enum></property>'
            f'{inner_layout}</widget>')

CUSTOM = """
 <customwidgets>
  <customwidget><class>PyDMLabel</class><extends>QLabel</extends><header>pydm.widgets.label</header></customwidget>
  <customwidget><class>PyDMLineEdit</class><extends>QLineEdit</extends><header>pydm.widgets.line_edit</header></customwidget>
  <customwidget><class>PyDMByteIndicator</class><extends>QWidget</extends><header>pydm.widgets.byte</header></customwidget>
  <customwidget><class>PyDMEnumComboBox</class><extends>QComboBox</extends><header>pydm.widgets.enum_combo_box</header></customwidget>
  <customwidget><class>PyDMPushButton</class><extends>QPushButton</extends><header>pydm.widgets.pushbutton</header></customwidget>
  <customwidget><class>PyDMRelatedDisplayButton</class><extends>QPushButton</extends><header>pydm.widgets.related_display_button</header></customwidget>
  <customwidget><class>MotorClassicRow</class><extends>QWidget</extends><header>pcdswidgets.motion.common.motor_classic_row</header></customwidget>
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


if __name__ == "__main__":
    out = {"pp_config3_A.ui": model_A, "pp_config3_B.ui": model_B,
           "pp_config3_B2.ui": model_B_embedded, "pp_config3_C.ui": model_C}
    for fname, fn in out.items():
        _n[0] = 0
        with open(fname, "w") as fd:
            fd.write(fn())
        print("wrote", fname)
