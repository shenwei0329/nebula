# -*- coding: utf-8 -*-
#
#   基类 Screen
#   ===========
#

import curses
import json


class Screen:

    def __init__(self):
        self.stdscr = curses.initscr()
        self._max_y, self._max_x = self.stdscr.getmaxyx()
        self._max_x -= 3
        self._max_y -= 3
        self.screen = {}
        self.loadData('screen.txt')

    def loadData(self, file_name):
        try:
            fp = open(file_name, 'r')
            _screen = json.load(fp)
            for _k in _screen:
                self.screen[int(_k)] = _screen[_k]
            fp.close()
        except:
            for _x in range(0, self._max_x+1):
                self.screen[_x] = []
                for _y in range(0, self._max_y+1):
                    self.screen[_x].append([_y, ' ', 0, False])

    def saveData(self):
        fp = open('screen.txt', 'w')
        json.dump(self.screen, fp)
        fp.close()

    def getX(self):
        return self._max_x

    def getY(self):
        return self._max_y

    def display_info(self, str, x, y, colorpair=2):

        if x<0:
            x = self._max_x - (x % self._max_x)
        else:
            x = (x % self._max_x)
            if x>0:
                x -= 1

        if y<0:
            y = self._max_y - (y % self._max_y)
        else:
            y = (y % self._max_y)
            if y>0:
                y -= 1

        if self.screen[x][y][1] != str or self.screen[x][y][2] != colorpair:
            self.screen[x][y][1] = str
            self.screen[x][y][2] = colorpair
            self.screen[x][y][3] = True

    def show_info(self, str):
        self.display_info(str, self._max_x/2, self._max_y-1)

    def clr_dot(self, x, y):
        self.display_info(' ', x, y, colorpair=10)

    def display_dot(self, x, y, chr, colorpair=2):
        self.display_info(chr, x, y, colorpair=colorpair)

    def debug(self, str):
        self.stdscr.addstr(self._max_y-1, 2, str, curses.color_pair(3))

    def refresh(self, force=False):
        for _x in self.screen:
            for _y in self.screen[_x]:
                if force or _y[3]:
                    self.stdscr.addstr(_y[0]+1, _x+1, _y[1], curses.color_pair(_y[2]) | curses.A_BOLD)
                    self.screen[_x][_y[0]][3] = False
        self.stdscr.refresh()

    def get_ch_and_continue(self, wait):
        if wait:
            self.stdscr.nodelay(0)
        ch = self.stdscr.getch()
        self.stdscr.nodelay(1)
        return ch

    def set_win(self):
        curses.start_color()
        curses.init_pair(10, curses.COLOR_BLACK, curses.COLOR_BLACK)
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.noecho()
        curses.cbreak()
        self.stdscr.nodelay(1)
        self.stdscr.box()

    def unset_win(self):
        curses.nocbreak()
        self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()
