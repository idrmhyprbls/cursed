#!/usr/bin/env python
'''
cursed.window

This contains the core logic used by cursed to create the window and offer the
ncurses interface to display everything.
'''

import curses
import gevent
from cursed.exceptions import CursedSizeError, CursedCallbackError
from cursed.meta import CursedWindowClass
from cursed.version import PY3

def _debug(s):
    '''
    It's pretty hard to debug with all the threads running updates constantly...
    '''
    with open('debug.log', 'a') as f:
        f.write(s + '\n')


class CursedWindow(object):
    __metaclass__ = CursedWindowClass

    _CW_WINDOW_SWAP_FUNCS = (
        'mvwin',
    )
    _CW_SCREEN_SWAP_FUNCS = (
    )
    _CW_WINDOW_FUNCS = (
        'refresh', 'clear', 'deleteln', 'erase', 'insertln', 'border',
        'nodelay', 'notimeout', 'clearok', 'is_linetouched', 'is_wintouched',
    )
    _CW_SCREEN_FUNCS = (
    )

    @classmethod
    def getlkey(cls):
        key = cls.getkey()
        if key is None:
            return None
        return key.lower()

    @classmethod
    def getch(cls):
        if cls.KEY_EVENTS.empty():
            return None
        return cls.KEY_EVENTS.get()

    @classmethod
    def getkey(cls):
        if cls.KEY_EVENTS.empty():
            return None
        nchar = cls.KEY_EVENTS.get()
        return chr(nchar)

    @classmethod
    def addch(cls, c, x=None, y=None, attr=None):
        attr = cls._fix_attr(attr)
        x, y = cls._fix_xy(x, y)
        if isinstance(c, int):
            c = chr(c)
        if attr is None:
            return cls.WINDOW.addch(y, x, c)
        else:
            return cls.WINDOW.addch(y, x, c, attr)

    @classmethod
    def delch(cls, x=None, y=None):
        x, y = cls._fix_xy(x, y)
        return cls.WINDOW.delch(y, x)

    @classmethod
    def getwh(cls):
        h, w = cls.WINDOW.getmaxyx()
        return w, h

    @classmethod
    def getxy(cls):
        y, x = cls.WINDOW.getyx()
        if cls.BORDERED:
            x -= 1
            y -= 1
        if cls.MENU:
            y -= 1
        return x, y

    @classmethod
    def inch(cls, x=None, y=None):
        x, y = cls._fix_xy(x, y)
        return cls.WINDOW.inch(y, x)

    @classmethod
    def insch(cls, ch, x=None, y=None, attr=None):
        x, y = cls._fix_xy(x, y)
        attr = cls._fix_attr(attr)
        if attr is None:
            return cls.WINDOW.insch(y, x, ch)
        else:
            return cls.WINDOW.insch(y, x, ch, attr)

    @classmethod
    def instr(cls, x=None, y=None, n=None):
        x, y = cls._fix_xy(x, y)
        if n is None:
            return cls.WINDOW.instr(y, x)
        else:
            return cls.WINDOW.instr(y, x, n)

    @classmethod
    def insstr(cls, s, x=None, y=None, attr=None):
        x, y = cls._fix_xy(x, y)
        attr = cls._fix_attr(attr)
        if attr is None:
            return cls.WINDOW.insstr(y, x, s)
        else:
            return cls.WINDOW.insstr(y, x, s, attr)

    @classmethod
    def insnstr(cls, s, x=None, y=None, n=None, attr=None):
        x, y = cls._fix_xy(x, y)
        attr = cls._fix_attr(attr)
        n = n if n is not None else cls.WIDTH
        if attr is None:
            return cls.WINDOW.insnstr(y, x, s, n)
        else:
            return cls.WINDOW.insnstr(y, x, s, n, attr)

    @classmethod
    def nextline(cls, cr=True):
        x, y = cls.getxy()
        if cr:
            x = 0
        x, y = cls._fix_xy(x, y)
        if y + 1 == cls.HEIGHT:
            if cls.SCROLL:
                cls.WINDOW.scroll()
                cls.WINDOW.move(y, 0)
            else:
                raise CursedSizeError('Window %s reached height at %d' % (
                    cls.__name__, y + 1))
        else:
            cls.WINDOW.move(y + 1, x)

    @classmethod
    def write(cls, msg):
        cls.addstr(str(msg))
        cls.nextline()

    @classmethod
    def _fix_xy(cls, x, y):
        y0, x0 = cls.WINDOW.getyx()
        rawx, rawy = False, False
        if x is None:
            x = x0
            rawx = True
        if y is None:
            y = y0
            rawy = True
        if cls.BORDERED:
            if not rawx:
                x += 1
            if not rawy:
                y += 1
        if cls.MENU:
            if not rawy:
                y += 1
        return x, y

    @classmethod
    def _fix_attr(cls, attr):
        if PY3:
            if isinstance(attr, str):
                return getattr(curses, 'A_%s' % attr.upper())
        else:
            if isinstance(attr, basestring):
                return getattr(curses, 'A_%s' % attr.upper())
        return attr

    @classmethod
    def addstr(cls, s, x=None, y=None, attr=None):
        x, y = cls._fix_xy(x, y)
        attr = cls._fix_attr(attr)
        if attr is None:
            return cls.WINDOW.addstr(y, x, s)
        else:
            return cls.WINDOW.addstr(y, x, s, attr)

    @classmethod
    def addnstr(cls, s, x=None, y=None, n=None, attr=None):
        x, y = cls._fix_xy(x, y)
        attr = cls._fix_attr(attr)
        n = cls.WIDTH if n is None else n
        if attr is None:
            return cls.WINDOW.addnstr(y, x, s, n)
        else:
            return cls.WINDOW.addnstr(y, x, s, n, attr)

    @classmethod
    def getstr(cls, *args):
        if args:
            x, y = cls._fix_xy(*args)
            return cls.WINDOW.getstr(x, y)
        return cls.WINDOW.getstr()

    @classmethod
    def hline(cls, x=None, y=None, char='-', n=None):
        x, y = cls._fix_xy(x, y)
        n = cls.WIDTH if n is None else n
        return cls.WINDOW.hline(y, x, char, n)

    @classmethod
    def vline(cls, x=None, y=None, char='|', n=None):
        x, y = cls._fix_xy(x, y)
        n = cls.HEIGHT if n is None else n
        return cls.WINDOW.vline(y, x, char, n)

    @classmethod
    def _cw_set_window_func(cls, attr):
        setattr(cls, attr, getattr(cls.WINDOW, attr))

    @classmethod
    def _cw_set_screen_func(cls, attr):
        setattr(cls, attr, getattr(cls.APP.scr, attr))

    @classmethod
    def _cw_swap_window_func(cls, attr):
        func = getattr(cls.WINDOW, attr)

        def new_func(s, x, y, *args, **kwargs):
            x, y = cls._fix_xy(x, y)
            return func(y, x, *args, **kwargs)
        setattr(cls, attr, new_func)

    @classmethod
    def _cw_swap_screen_func(cls, attr):
        func = getattr(cls.APP.scr, attr)

        def new_func(s, x, y, *args, **kwargs):
            x, y = cls._fix_xy(x, y)
            return func(y, x, *args, **kwargs)
        setattr(cls, attr, new_func)

    @classmethod
    def app_get(cls, var):
        return getattr(cls.APP, var)

    @classmethod
    def app_set(cls, var, val):
        return setattr(cls.APP, var, val)

    @classmethod
    def cx(cls, *args):
        x, y = cls.getxy()
        if not args:
            return x
        return cls.move(args[0], y)

    @classmethod
    def cy(cls, *args):
        x, y = cls.getxy()
        if not args:
            return y
        return cls.move(x, args[0])

    @classmethod
    def move(cls, x, y):
        x, y = cls._fix_xy(x, y)
        cls.WINDOW.move(y, x)

    @classmethod
    def _cw_setup_run(cls, app, window):
        cls.RUNNING = True
        cls.APP = app
        height, width = window.getmaxyx()
        if width < cls.WIDTH:
            raise CursedSizeError('terminal width is %d and window width is '
                                  '%d' % (width, cls.WIDTH))
        if height < cls.HEIGHT:
            raise CursedSizeError('terminal height is %d and window height '
                                  'is %d' % (height, cls.HEIGHT))
        cls.WINDOW = window.subwin(cls.HEIGHT, cls.WIDTH, cls.Y, cls.X)
        if cls.SCROLL:
            cls.WINDOW.scrollok(True)
            cls.WINDOW.idlok(1)
        if cls.BORDERED:
            cls.WINDOW.border()
        for attr in cls._CW_WINDOW_FUNCS:
            cls._cw_set_window_func(attr)
        for attr in cls._CW_SCREEN_FUNCS:
            cls._cw_set_screen_func(attr)
        for attr in cls._CW_WINDOW_SWAP_FUNCS:
            cls._cw_swap_window_func(attr)
        for attr in cls._CW_SCREEN_SWAP_FUNCS:
            cls._cw_swap_screen_func(attr)

    @classmethod
    def redraw(cls):
        cls.erase()
        if cls.BORDERED:
            cls.WINDOW.border()
        if cls.MENU:
            cls._cw_menu_display()
        cls.WINDOW.refresh()

    @classmethod
    def _cw_handle_events(cls):
        while not cls.EVENTS.empty():
            func_name, args, kwargs = cls.EVENTS.get()
            if func_name == 'quit':
                if hasattr(cls, 'quit') and callable(cls.quit):
                    result = cls.quit(*args, **kwargs)
                    cls.RESULTS.put(('quit', args, kwargs, result))
                cls.RUNNING = False
                break
            if not hasattr(cls, func_name):
                raise CursedCallbackError('%s has no function %s' % (
                    cls.__name__, func_name))
            func = getattr(cls, func_name)
            if not callable(func):
                raise CursedCallbackError('%s has no callable %s' % (
                    cls.__name__, func_name))
            cls.RESULTS.put(
                (func_name, args, kwargs, func(*args, **kwargs))
            )

    @classmethod
    def _cw_setup_menu(cls):
        for mkey, title, menu in cls.MENU.menus:
            key_d = {}
            cls._KEYMAP[mkey] = (title, key_d)
            for name, key, cb in menu:
                if key:
                    key_d[key] = cb

    @classmethod
    def _cw_menu_display(cls):
        x = 0
        # Because cls with MENU will add 1 to y in _fix_xy, we need true origin
        y = -1
        # Makes the menu standout
        menu_attrs = curses.A_REVERSE | curses.A_BOLD
        saved_pos = cls.getxy()
        for mkey, title, menu in cls.MENU.menus:
            # double check we're not going to write out of bounds
            if x + len(title) + 2 >= cls.WIDTH:
                raise CursedSizeError('Menu %s exceeds width of window: x=%d' %
                                      (title, x))
            y = -1
            cls.addstr(title + '  ', x, y, attr=menu_attrs)
            if cls._OPENED_MENU and cls._OPENED_MENU[0] == title:
                for name, key, cb in menu:
                    y += 1
                    if key:
                        s = '[{1}] {0}'.format(name, key)
                    else:
                        s = name
                    cls.addstr(s, x, y, attr=curses.A_REVERSE)
            # For the empty space filler
            x += len(title) + 2
        # color the rest of the top of the window
        extra = 2 if cls.BORDERED else 0
        cls.addstr(' ' * (cls.WIDTH - x - extra), x, -1, attr=menu_attrs)
        cls.move(*saved_pos)

    @classmethod
    def _cw_menu_update(cls):
        c = cls.getch()
        if c is None:
            return
        if not (0 < c < 256):
            return
        if cls._OPENED_MENU is None:
            if chr(c) in cls._KEYMAP:
                cls._OPENED_MENU = cls._KEYMAP[chr(c)]
                cls.redraw()
        else:
            cb = cls._OPENED_MENU[1].get(chr(c))
            cls._OPENED_MENU = None
            cls.redraw()
            if cb:
                # Run callback associated with menu item
                cls.trigger(cb)

    @classmethod
    def _cw_run(cls, app, window):
        cls._cw_setup_run(app, window)
        if cls.MENU:
            cls._cw_setup_menu()
        cls.redraw()
        has_update = hasattr(cls, 'update') and callable(cls.update)
        if hasattr(cls, 'init') and callable(cls.init):
            cls.trigger('init')
        while cls.RUNNING:
            # Yield to others for a bit
            gevent.sleep(0)
            if cls.MENU and cls.RUNNING:
                cls._cw_menu_update()
            cls._cw_handle_events()
            if has_update and cls.RUNNING:
                cls.update()

    @classmethod
    def trigger(cls, func_name, *args, **kwargs):
        cls.EVENTS.put((func_name, args, kwargs))
