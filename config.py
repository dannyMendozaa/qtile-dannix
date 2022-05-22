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
import socket
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
    Key([], "XF86AudioRaiseVolume", lazy.spawn("amixer set Master 4%+"),
        desc="Increase Volume"),
    Key([], "XF86AudioLowerVolume", lazy.spawn("amixer set Master 4%-"),
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
    Key(["control"], "space", lazy.layout.flip(),
        desc="flip windows"),
    Key([mod], "Tab", lazy.layout.next(),
        desc="Switch window focus to oither pane(s) of stack"),
    Key([mod], "t", lazy.hide_show_bar(),
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
        (u"", {'layout': 'monadwide'}),
        (u"", {'layout': 'max'}),
        (u"", {'layout': 'monadtall'}),
        (u"", {'layout': 'max'}),
        (u"", {'layout': 'floating'}),
        (u"", {'layout': 'max'}),
]

groups = [Group(name, **kwargs) for name, kwargs in group_names]
groups.append(
        ScratchPad("scratchpad", [
            # define a drop down terminal.
            DropDown("term",
                #"xterm -name FXTerm -fa 'Envy Code R' -fs 16",
                "alacritty --class TERM",
                opacity=1.0,
                width=0.8,
                on_focus_lost_hide=True)])
        )

for i, (name, kwargs) in enumerate(group_names, 1):
    keys.append(Key([mod], str(i), lazy.group[name].toscreen()))
    keys.append(Key([mod, "shift"], str(i), lazy.window.togroup(name)))

layouts = [
    layout.Max(),
    layout.MonadTall(
        margin=10,
        border_focus='a6d0e2',
        border_width=6,
        ),
    layout.MonadWide(
        margin=10,
        border_focus='a6d0e2',
        border_width=6,
        new_at_current=False,
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
    fontsize=44,
    padding=3,
)

external_monitor = dict(
    #font='VictorMono Nerd Font',
    #font='JetBrains Mono Light',
    font='Iosevka',
    fontsize=50,
    padding=2,
)

prompt_settings = dict(
    background='1c1b22a4',
    cursor_color = "ffffff",
    #prompt = '{prompt} '.format(prompt="\U0001F6F8"),
    prompt = "{0}@{1}: ".format(os.environ["USER"], socket.gethostname()),
    fmt = " {}",
    bell_style = 'visual',
    visual_bell_color = 'afc1ca',
    ignore_dups_history=True,
)

photo = r'[ -z $(wmctrl -l | grep -E "DM.Scre.*") ] && \
        ~/Documents/Bash/Screenshot-tool-linux/screenShot'

n_mon = 55 if num_monitors > 1 else 45

systray = widget.Systray(icon_size=n_mon)
prompt = widget.Prompt(**external_monitor,markup=False,**prompt_settings,) \
        if num_monitors > 1 else widget.Prompt(font='Iosevka',**prompt_settings)

sep = widget.Sep(
        padding=4,
        linewidth=0,
        size_percent=100
        )


class SPOTIFY(base.InLoopPollText):

    def __init__(self, **config):
        base.InLoopPollText.__init__(self, **config)
        self.update_interval = 0.2

    def poll(self):
        bus = dbus.SessionBus()
        for service in bus.list_names():
            if service.startswith('org.mpris.MediaPlayer2.'):
                players = re.findall(r'\bf[irefox]*\b|\bs[potify]*\b',service)
                p = players[0]
                if re.search(p,service):
                    player = dbus.SessionBus().get_object(service, '/org/mpris/MediaPlayer2')
                    meta = dbus.Interface(player,
                            dbus_interface='org.freedesktop.DBus.Properties')
                    metas = meta.GetAll('org.mpris.MediaPlayer2.Player')
                    if metas['PlaybackStatus'] == 'Playing':
                        artist = f"{p.title()}: {metas['Metadata']['xesam:artist'][0]}"
                        # track = f"{p.title()}: {metas['Metadata']['xesam:title']}"
                        return artist

        return f""


def my_func(text):
    '''Used in TaskList to replace certain task names as vim, spotify, etc.'''
    #for string in [' - ','Mozilla Firefox','VIM']:
    #    text = text.replace(string,"")
    #py = str(re.findall("[a-zA-Z0-9]*.py",text)[0])
    dictionary = {
            ' @ ':'daniel@dannix:',
            'Spotify':'Spotify',
            #'👨‍🎤Spotify':'Spotify',
            '':'— Mozilla Firefox',
            ' \U0001F4DDVIMROOT':'svim',
            ' \U0001F4DDVIM':' - VIM',
            ' \U0001F427PACMAN':'pacman',
            #' \U0001F40D' + str(re.findall("[a-zA-Z0-9]*.py",text)[0]):str(re.findall("[a-zA-Z0-9]*.py",text)[0])
            #' \U0001F4DDPYTHON':py,
            }
    for key,value in dictionary.items():
        if value in text:
            text = text.replace(value,key)
    return text

## Used in both monitors
qtilelogo = "~/.config/qtile/baricons/qtilelogo"
qtile_mousecallbacks={
    'Button1': lambda: qtile.cmd_findwindow(),
    'Button3': lambda: qtile.cmd_spawn(
        "qtile cmd-obj -o window -f toggle_minimize"),
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

icon = '/home/daniel/.local/share/icons/'\
        + 'Nordic-Darker/apps/scalable/Calendar.svg'
print(icon)

def f_widgets_external():
    list_widgets_1 = [
        widget.Image(
            filename = qtilelogo,
            mouse_callbacks = qtile_mousecallbacks,
        ),
        widget.GroupBox(
            margin_y = 5,
            borderwidth = 8,
            fontsize = 50,
            highlight_method="line",
            highlight_color = ['005590'],
            active = "ffffff",
            inactive = "ffffff",
            other_current_screen_border = "2980B900",
            other_screen_border = "B5B5B8",
            this_screen_border = "B5B5B8",
            this_current_screen_border = "005590",
            hide_unused=True,
            rounded=False,
            ),
        widget.Backlight(
            backlight_name="intel_backlight",
            format="",
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
            foreground="ffffff",
            background = "1c1b2200",
            border = "005590",
            #icon_size=38,
            icon_size=60,
            borderwidth=0,
            margin_x=0,
            margin_y=0,
            spacing=20,
            rounded=False,
            txt_floating='🗗 ',
            txt_maximized='🗖 ',
            txt_minimized='',
            parse_text = my_func,
            ),
        SPOTIFY(**external_monitor,
                background = "272727",
                ),
        widget.Volume(
                **external_monitor,
                emoji=False,
                fmt='{}',
                background="005590",
                ),
        systray,
        widget.Image(
            filename=screenshot,
            mouse_callbacks=screenshot_mousecallbacks,
        ),
        widget.Wallpaper(
            **walldict,
        ),
        widget.Clock(
            **external_monitor,
            background='ebf1f4',
            foreground='000000',
            format='%d/%m/%Y %H:%M',
            mouse_callbacks={
                'Button1': lambda: qtile.cmd_spawn(
                    f'notify-send \
                        -i {icon} \
                        -t 10000 -u normal "$(cal -n 1)"',
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
            # fontsize=34,
            fontsize=60,
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
    return list_widgets_1

primary = f_widgets_external()
if num_monitors > 1:
    del primary[2]
secondary = f_widgets_external()
del secondary[-5]

screens = [
    Screen(
        top=bar.Bar(
            primary,
            65,
            background='272935a4',
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
                    secondary,  # second monitor widgets
                    65,
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
    Match(wm_class='gl'), # mpv
    Match(wm_class='mpv'), # mpv
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

@hook.subscribe.startup
def startup():
    xr = '''
    xrandr --dpi 192 --output eDP1 --mode 1366x768 
    --panning 1920x1080_60.00 --scale 1.4055636896046853x1.40625 
    --pos 0x0 --output HDMI1 --mode 1920x1080_60.00 
    --panning 1920x1080+1920+0 --primary
    '''
    # xr = '''
    # xrandr --dpi 192 --output eDP1 --mode 1366x768 
    # --panning 2732x1536+0+0 --scale 2x2
    # --pos 0x0 --output HDMI1 --mode 1920x1080_60.00 
    # --panning 1920x1080+2732+0 --primary
    # '''
    # xr = '''
    # xrandr --dpi 192 --output eDP1 --mode 1366x768 
    # --panning 2732x1536+0+0 --scale 2x2 --pos 0x0
    # --output HDMI1 --mode 1920x1080_60.00 
    # --panning 3072x1728+2732+0 --primary --scale 1.6x1.6
    # '''
    if num_monitors > 1:
        pass
        #sp.call(xr.split())

@hook.subscribe.startup_once
def autostart():
    home = os.path.expanduser("~/.config/qtile/autostart.sh")
    sp.call([home])

@hook.subscribe.client_new
def moveclient(client):
    c = dict()
    c[u""] = ["Alacritty","alacritty","xterm"]
    c[u""] = ["Navigator","Chromium","chromium"]
    c[u""] = ["pcmanfm","Pcmanfm","thunar"]
    c[u""] = ["org.pwmt.zathura","Zathura","gimp","Gimp"]
    c[u""] = ["zoom ","Zoom"]
    wm_class = client.window.get_wm_class()[0]
    for k,v in c.items():
        if wm_class in c[k]:
            client.togroup(k,switch_group=True)

@hook.subscribe.client_new
def spotify(window):
    time.sleep(0.07)
    wm_class = window.window.get_wm_class()[0]
    w_name = window.window.get_name()
    if wm_class in ("spotify",) or w_name in ("Spotify",):
        window.togroup("",switch_group=True)

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
cursor_warp = True
bring_front_click = False
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
