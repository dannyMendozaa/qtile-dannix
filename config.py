# Copyright (c) 2010 Aldo Cortesi
# Copyright (c) 2010, 2014 dequis
# Copyright (c) 2012 Randall Ma
# Copyright (c) 2012-2014 Tycho Andersen
# Copyright (c) 2012 Craig Barnes
# Copyright (c) 2013 horsik
# Copyright (c) 2013 Tao Sauvage
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import subprocess as sp
import dbus
import re
import time

from typing import List  # noqa: F401

from libqtile import bar, layout, widget, hook, qtile
from libqtile.config import Click, Drag, Group, Key, Screen, ScratchPad, \
        DropDown, KeyChord, Match
from libqtile.lazy import lazy
from libqtile.utils import guess_terminal
from libqtile.widget import base
from Xlib import display as xdisplay

mod = "mod4" # Super Key
mod1 = "mod1" # Alt key

terminal = guess_terminal()

keys = [
    Key([mod], "period", lazy.next_screen(),
        desc='Move focus to next monitor'),
    Key([mod], "s", lazy.window.toggle_floating(),
        desc="Toggle floeating screen"),
    Key([mod], "f", lazy.window.toggle_fullscreen(),
        desc="Toggle fullscreen"),
    Key([mod1], "Tab", lazy.screen.toggle_group(),
        desc="Move to the last visited group"),
    Key(["control"], "Return", lazy.group['scratchpad'].dropdown_toggle('term'),
        desc="toggle visibiliy of above defined DropDown named 'term'"),
    Key([], "XF86MonBrightnessUp", lazy.spawn("xbacklight -inc 2"),
        desc="Increase the bright"),
    Key([], "XF86MonBrightnessDown", lazy.spawn("xbacklight -dec 2"),
        desc="Decrease the bright"),
    Key([], "XF86AudioRaiseVolume", lazy.spawn("amixer set Master 5%+"),
        desc="Increase Volume"),
    Key([], "XF86AudioLowerVolume", lazy.spawn("amixer set Master 5%-"),
        desc="Decrease Volume"),
    Key([], "XF86AudioMute", lazy.spawn("amixer set Master toggle"),
        desc="Toggle Volume"),
    Key([], 'XF86AudioPlay', lazy.spawn("playerctl play-pause"),
        desc="Play or Pause current player"),
    Key([], 'XF86AudioNext', lazy.spawn("playerctl next"),
        desc="Next Track"),
    Key([], 'XF86AudioPrev', lazy.spawn("playerctl previous"),
        desc="Previous Track"),
    Key([mod], "j", lazy.layout.down(),
        desc="Move focus down in stack pane"),
    Key([mod], "k", lazy.layout.up(),
        desc="Move focus up in stack pane"),
    Key([mod], "h", lazy.layout.left()),
    Key([mod], "l", lazy.layout.right()),
    Key([mod, "shift"], "h", lazy.layout.swap_left()),
    Key([mod, "shift"], "l", lazy.layout.swap_right()),
    Key([mod, "shift"], "j", lazy.layout.shuffle_down()),
    Key([mod, "shift"], "k", lazy.layout.shuffle_up()),
    Key([mod, "control"], "space", lazy.layout.flip(),
        desc="flip windows"),
    Key([mod], "Tab", lazy.layout.next(),
        desc="Switch window focus to other pane(s) of stack"),
    Key([mod], "h", lazy.hide_show_bar(),
        desc="Hide or Show current screen bar"),
    Key([mod, "shift"], "space", lazy.layout.rotate(),
        desc="Swap panes of split stack"),
    Key([mod, "shift"], "Return", lazy.layout.toggle_split(),
        desc="Toggle between split and unsplit sides of stack"),
    Key([mod], "Return", lazy.spawn(terminal),
            desc="Launch terminal"),
    Key([mod], "space", lazy.next_layout(),
            desc="Toggle between layouts"),
    Key([mod], "q", lazy.window.kill(),
            desc="Kill focused window"),
    Key([mod, "control"], "r", lazy.restart(),
            desc="Restart qtile"),
    Key([mod, "control"], "q", lazy.shutdown(),
            desc="Shutdown qtile"),
    #Key([mod], "d", lazy.spawn("rofi -combi-modi window,drun,ssh  -show combi"),
    #    desc="Spawn a command using a prompt widget"),
    Key([mod], "d", lazy.spawncmd(),
        desc="Spawn a command using a prompt widget"),
    KeyChord([mod], "r", [
        Key([], "g", lazy.layout.grow()),
        Key([], "s", lazy.layout.shrink()),
        Key([], "n", lazy.layout.normalize()),
        Key([], "m", lazy.layout.maximize())],
        mode="Adjust"
    ),
#    KeyChord([mod], "l", [
#        Key([], "t", lazy.spawn("xterm")),
#        Key([], "f", lazy.spawn("firefox")),
#        Key([], "c", lazy.spawn("chromium")),
#        Key([], "p", lazy.spawn("pcmanfm"))],
#        mode="  "
#    ),
]


group_names = [
        (u"", {'layout': 'monadwide'}),
        (u"", {'layout': 'max'}),
        (u"", {'layout': 'monadtall'}),
        (u"", {'layout': 'max'}),
        (u"", {'layout': 'floating'}),
        (u"", {'layout': 'max'}),
]

groups = [Group(name, **kwargs) for name, kwargs in group_names]
groups.append(
        ScratchPad("scratchpad", [
            # define a drop down terminal.
            DropDown("term",
                "xterm -name FXTerm -fa 'Envy Code R' -fs 16",
                opacity=1.0,
                width=0.8,
                on_focus_lost_hide=True)])
        )

for i, (name, kwargs) in enumerate(group_names, 1):
    keys.append(Key([mod], str(i), lazy.group[name].toscreen()))
    keys.append(Key([mod, "shift"], str(i), lazy.window.togroup(name)))

layouts = [
    layout.Max(),
    layout.MonadWide(
        margin=10,
        border_focus='a6d0e2',
        border_width=4,
        new_at_current=False,
        ),
    layout.MonadTall(
        margin=12,
        border_focus='a6d0e2',
        border_width=4,
        ),
]

def get_num_monitors():
    num_monitors = 0
    try:
        display = xdisplay.Display()
        screen = display.screen()
        resources = screen.root.xrandr_get_screen_resources()

        for output in resources.outputs:
            monitor = display.xrandr_get_output_info(output, resources.config_timestamp)
            preferred = False
            if hasattr(monitor, "preferred"):
                preferred = monitor.preferred
            elif hasattr(monitor, "num_preferred"):
                preferred = monitor.num_preferred
            if preferred:
                num_monitors += 1
    except Exception as e:
        # always setup at least one monitor
        return 1
    else:
        return num_monitors

num_monitors = get_num_monitors()

widget_defaults = dict(
    font='Noto Emoji Nerd Font',
    fontsize=25,
    padding=3,
)

external_monitor = dict(
    font='JetBrains Mono Light',
    fontsize=28,
    padding=3,
)

prompt_settings = dict(
    background='1c1b22a4',
    cursor_color = "00ff00",
    prompt = '{prompt} '.format(prompt="->"),
    fmt = " {}",
    bell_style = 'visual',
    visual_bell_color = 'ebf1f4',
    ignore_dups_history=True,
)

photo = r'[ -z $(wmctrl -l | grep -E "DM.Scre.*") ] && \
        ~/Documents/Bash/Screenshot-tool-linux/screenShot'

n_mon = 32 if num_monitors > 1 else 30

systray = widget.Systray(icon_size=n_mon)
prompt = widget.Prompt(**external_monitor,**prompt_settings,) \
        if num_monitors > 1 else widget.Prompt(font='Iosevka',**prompt_settings)

sep = widget.Sep(
        padding=4,
        linewidth=0,
        size_percent=100
        )

def window_class():
    #x = sp.run('xdotool getactivewindow getwindowname',shell=True,stdout=sp.PIPE)
    #x = sp.run('xdotool getactivewindow getwindowclassname',shell=True,stdout=sp.PIPE)
    y = sp.run('xdotool getactivewindow getwindowname',shell=True,stdout=sp.PIPE)
    #xy =  str(
    #        x.stdout.decode('utf-8') + y.stdout.decode('utf-8')
    #        ).replace('\n',':')
    lista.append(y.stdout.decode('utf-8'))
    pass

def my_func(text):
    #sub = re.sub('[a-zA-Z]+','Daniel',text)
    dictionary = {'XTerm':'daniel@dannix','Spotify':'Spotify Premium'}
    for key,value in dictionary.items():
        #y = sp.run('xdotool getactivewindow getwindowname',shell=True,stdout=sp.PIPE)
        #y = y.stdout.decode("utf-8")
        if value in text:
            text = text.replace(value,key)
    return text

## Used in both monitors
qtilelogo = "~/.config/qtile/baricons/qtilepng.png"
qtile_mousecallbacks={
    'Button1': lambda: qtile.cmd_spawn(
        "rofi -combi-modi window,drun,ssh  -show combi"),
    'Button2': lambda: qtile.cmd_spawn(
        "qtile cmd-obj -o window -f toggle_minimize"),
    'Button3': lambda: qtile.cmd_findwindow(),
    'Button4': lambda: qtile.cmd_spawn(
        "qtile cmd-obj -o window -f down_opacity"),
    'Button5': lambda: qtile.cmd_spawn(
        "qtile cmd-obj -o window -f up_opacity")
}
screenshot = "~/.config/qtile/baricons/retrocamera.png"
screenshot_mousecallbacks={
    'Button1': lambda: qtile.cmd_spawn(
        photo,
        shell=True,
        )
    }
walldict = dict(
    wallpapers="~/Pictures/wallpapers",
    foreground="05141b",
    background="8a9ea8",
    label="",
    random_selection=True,
)

list_widgets = [
    widget.Image(
        filename = qtilelogo,
        mouse_callbacks = qtile_mousecallbacks,
    ),
    widget.GroupBox(
        padding_x = 0,
        borderwidth = 8,
        highlight_method="block",
        active = "000000",
        inactive = "000000",
        other_current_screen_border = "1c1b22a4",
        other_screen_border = "1c1b22a4",
        this_screen_border = "9e9e9e",
        this_current_screen_border = "ebf1f4",
        hide_unused=True,
        rounded = True,
        ),
    widget.Backlight(
            backlight_name="intel_backlight",
            format="",
        ),
    prompt if num_monitors < 2 else widget.TextBox(""),
    widget.CurrentScreen(
        **external_monitor,
        active_text='·',
        inactive_text='·'
        ),
    widget.WindowName(
        font='Iosevka',
        foreground='f4f5f6',
        for_current_screen = False,
        format = '{name}',
        fmt = '{}',
        max_chars = 55,
        ),
    widget.Chord(
        chords_colors={
            'launch': ("#ff0000", "#000000")
        },
        font='ShureTechMono Nerd Font',
        fontsize=22,
        foreground="dedcd7",
        name_transform=lambda name: name.upper(),
    ),
    widget.Volume(
            font='Iosevka',
            fontsize = 24,
            fmt='{}',
            ),
    systray if num_monitors < 2 else widget.TextBox(""),
    widget.Image(
        filename=screenshot,
        mouse_callbacks=screenshot_mousecallbacks,
    ),
    widget.Wallpaper(
        **walldict,
        fontsize=26,
    ),
    widget.Clock(
        background='ebf1f4',
        foreground='000000',
        font='Iosevka',
        fontsize=24,
        format='%d/%m/%Y %H:%M',
        mouse_callbacks={
            'Button1': lambda: qtile.cmd_spawn(
                'notify-send -t 0 -u normal "$(cal -n 9)"',
                shell=True),
            'Button3': lambda: qtile.cmd_spawn(
                'pkill dunst',
                shell=True),
            }
        ),
    widget.WidgetBox(
        close_button_location="right",
        text_open="",
        text_closed="",
        foreground="05141b",
        background="8a9ea8",
        widgets=[
        widget.TextBox(
            font='Iosevka',
            fontsize=24,
            foreground="282a36",
            background="bd93f9",
            text="Exit",
            mouse_callbacks={'Button1':
                lambda: qtile.cmd_shutdown()},
            ),
        widget.TextBox(
            font='Iosevka',
            fontsize=24,
            text="Reboot",
            foreground="282a36",
            background="ff5555",
            mouse_callbacks={'Button1':
                lambda: qtile.cmd_spawn("poweroff")}
            ),
        widget.TextBox(
            font='Iosevka',
            fontsize=24,
            text="Poweroff",
            foreground="282a36",
            background="f1fa8c",
            mouse_callbacks={'Button1':
                lambda: qtile.cmd_spawn("poweroff")}
            ),
        ]
    ),
]

list_widgets_1 = [
    widget.Image(
        filename = qtilelogo,
        mouse_callbacks = qtile_mousecallbacks,
    ),
    widget.GroupBox(
        padding_x = 0,
        borderwidth = 6,
        fontsize = 36,
        highlight_method="block",
        active = "bde7f2",
        inactive = "bde7f2",
        other_current_screen_border = "1c1b2200",
        other_screen_border = "1c1b2200",
        this_screen_border = "191a22ff",
        this_current_screen_border = "5a66c7",
        hide_unused=True,
        rounded=False,
        ),
    prompt,
    widget.CurrentScreen(
        **external_monitor,
        active_text='·',
        inactive_text='·'
        ),
    widget.TaskList(
        **external_monitor,
        highlight_method = "block",
        background = "1c1b2200",
        border = "5a66c7",
        icon_size=36,
        borderwidth=0,
        margin_x=0,
        margin_y=0,
        spacing=0,
        rounded=False,
        txt_floating='🗗 ',
        txt_maximized='🗖 ',
        txt_minimized='🗕 ',
        parse_text = my_func,
        #parse_text = lambda string: string.replace(string,window_class()),
        ),
    widget.Mpris2(
        **external_monitor,
        background='ebf1f4',
        foreground='000000',
        #background='55f287',
        #foreground='000000',
        fmt='{}',
        stop_pause_text='',
        display_metadata=['xesam:artist'],
        #display_metadata=['xesam:title', 'xesam:album', 'xesam:artist'],
        scroll_wait_intervals=1000,
        objname='org.mpris.MediaPlayer2.spotify'),
    #widget.Spacer(length=bar.STRETCH),
    #widget.WindowName(
    #    **external_monitor,
    #    for_current_screen = False,
    #    format = '{name}',
    #    fmt = '{}',
    #    max_chars = 60,
    #    ),
    widget.Volume(
            **external_monitor,
            emoji=False,
            fmt='{}'
            ),
    systray,
    widget.Image(
        filename=screenshot,
        mouse_callbacks=screenshot_mousecallbacks,
    ),
    widget.Wallpaper(
        **walldict,
        fontsize=34,
    ),
    widget.Clock(
        **external_monitor,
        background='ebf1f4',
        foreground='000000',
        format='%d/%m/%Y %H:%M',
        mouse_callbacks={
            'Button1': lambda: qtile.cmd_spawn(
                'notify-send -t 0 -u normal "$(cal -n 9)"',
                shell=True),
            'Button3': lambda: qtile.cmd_spawn(
                'pkill dunst',
                shell=True),
            }
        ),
    widget.WidgetBox(
        close_button_location="right",
        text_open="",
        text_closed="",
        foreground="05141b",
        background="8a9ea8",
        fontsize=34,
        widgets=[
        widget.TextBox(
            **external_monitor,
            foreground="282a36",
            background="bd93f9",
            text="Exit",
            mouse_callbacks={'Button1':
                lambda: qtile.cmd_shutdown()},
            ),
        widget.TextBox(
            **external_monitor,
            text="Reboot",
            foreground="282a36",
            background="ff5555",
            mouse_callbacks={'Button1':
                lambda: qtile.cmd_spawn("reboot")}
            ),
        widget.TextBox(
            **external_monitor,
            text="PowerOff",
            foreground="282a36",
            background="f1fa8c",
            mouse_callbacks={'Button1':
                lambda: qtile.cmd_spawn("poweroff")}
            ),
        ]
    ),
]

screens = [
    Screen(
        top=bar.Bar(
            list_widgets,
            30,
            background='1c1b22a4',
            margin=[0, 0, 0, 0],
            opacity=1,
        ),
    ),
]

if num_monitors > 1:
    for m in range(num_monitors - 1):
        screens.append(
            Screen(
                top=bar.Bar(
                    list_widgets_1,  # second monitor widgets
                    40,
                    background='272935a4',
                    margin=[0, 0, 0, 0],
                    opacity=1,
                ),
            )
        )


# Drag floating layouts.
mouse = [
    Drag([mod], "Button1", lazy.window.set_position_floating(),
         start=lazy.window.get_position()),
    Drag([mod], "Button3", lazy.window.set_size_floating(),
         start=lazy.window.get_size()),
    Click([mod], "Button2", lazy.window.bring_to_front())
]

floating_layout = layout.Floating(
    border_focus = 'f0f3f4',
    border_width = 3,
    # Run the utility of `xprop` to see the wm class and name of an X client.
    float_rules=[
    *layout.Floating.default_float_rules,
    Match(wm_class='confirmreset'),  # gitk
    Match(wm_class='makebranch'),  # gitk
    Match(wm_class='maketag'),  # gitk
    Match(wm_class='ssh-askpass'),  # ssh-askpass
    Match(wm_class='confirm'),
    Match(wm_class='feh'),
    Match(wm_class='xcalc'),
    Match(wm_class='sxiv'),
    Match(wm_class='ocs-url'),
    Match(wm_class='Places'),
    Match(wm_class='Dialog'),
    Match(wm_class='download'),
    Match(wm_class='error'),
    Match(wm_class='file_progress'),
    Match(wm_class='notification'),
    Match(wm_class='splash'),
    Match(wm_class='toolbar'),
    Match(wm_class='zenity'),
    Match(title='branchdialog'),  # gitk
    Match(title='pinentry'),  # GPG key password entry
    Match(title='gtk_calc'),  # Python  GTK calculators
])

@hook.subscribe.startup_once
def autostart():
    home = os.path.expanduser("~/.config/qtile/autostart.sh")
    sp.call([home])

@hook.subscribe.client_new
def moveclient(client):
    c = dict()
    c[u""] = ["xterm"]
    c[u""] = ["Navigator","Chromium","chromium"]
    c[u""] = ["pcmanfm","Pcmanfm","thunar"]
    c[u""] = ["org.pwmt.zathura","Zathura","gimp","Gimp"]
    c[u""] = ["Spotify","spotify","Spotify Premium"]
    wm_class = client.window.get_wm_class()[0]
    for k,v in c.items():
        if wm_class in c[k]:
            client.togroup(k,switch_group=True)

@hook.subscribe.client_new
def spotify(window):
    time.sleep(0.05)
    wm_class = window.window.get_wm_class()[0]
    w_name = window.window.get_name()
    if wm_class ==  "spotify" or w_name == "Spotify Premium":
        window.togroup("",switch_group=True)

@hook.subscribe.client_new
def firefox_videos(window):
    wm_class = window.window.get_wm_class()[0]
    w_name = window.window.get_name()
    if wm_class ==  "Toolkit" and w_name == "Picture-in-Picture":
        window.togroup("",switch_group=True)
        window.toggle_maximize()

@hook.subscribe.client_new
def float_to_front(qtile):
    """
    Bring all floating windows of the group to front
    """
    global floating_windows
    floating_windows = []
    for window in qtile.currentGroup.windows:
        if window.floating:
            window.cmd_bring_to_front()
            floating_windows.append(window)
    floating_windows[-1].cmd_focus()

dgroups_key_binder = None
dgroups_app_rules = []  # type: List
follow_mouse_focus = True
cursor_warp = False
bring_front_click = True
auto_fullscreen = True
focus_on_window_activation = "focus"
reconfigure_screens = True
auto_minimize = True

# XXX: Gasp! We're lying here. In fact, nobody really uses or cares about this
# string besides java UI toolkits; you can see several discussions on the
# mailing lists, GitHub issues, and other WM documentation that suggest setting
# this string if your java app doesn't work correctly. We may as well just lie
# and say that we're a working one by default.
#
# We choose LG3D to maximize irony: it is a 3D non-reparenting WM written in
# java that happens to be on java's whitelist.
wmname = "LG3D"
