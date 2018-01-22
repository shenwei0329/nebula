#-*- coding: UTF-8 -*-
#
#   社会哲学体系
#   ============
#   Version 1.0
#
#   1）原始社会
#       面对大自然，求生存
#       原始社会是以亲族关系为基础，人口很少，经济生活采取平均主义分配办法，对社会的控制靠传统和家长来维系。
#

import curses, math, time, random, json, sys

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
                    self.stdscr.addstr(_y[0]+1, _x+1, _y[1], curses.color_pair(_y[2]))
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
        curses.noecho()
        curses.cbreak()
        self.stdscr.nodelay(1)
        self.stdscr.box()

    def unset_win(self):
        curses.nocbreak()
        self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()

class Obj:

    def __init__(self, name, init_x, init_y, ch, color):
        self.name = name
        self.chr = ch
        self.color = color
        self.V = (0., 0., 0., 0.,)
        try:
            self.load()
        except:
            self.X = init_x + random.random()
            self.Y = init_y + random.random()

    def move(self):
        self.V = (random.random(), random.random(), random.random(), random.random(),)
        self.X = self.X + (self.V[0]-self.V[2])
        self.Y = self.Y + (self.V[1]-self.V[3])

    def getPosition(self):
        return int(self.X), int(self.Y), self.chr, self.color

    def save(self):
        fp = open('dot%s.txt' % self.name, 'w')
        json.dump({"x":self.X, "y":self.Y, "ch":self.chr, "c":self.color}, fp)
        fp.close()

    def load(self):
        fp = open('dot%s.txt' % self.name, 'r')
        _info = json.load(fp)
        self.X = _info["x"]
        self.Y = _info["y"]
        self.chr = _info["ch"]
        self.color = _info["c"]
        fp.close()

def main():

    random.seed(time.clock())
    scr = Screen()

    try:
        scr.set_win()
        scr.refresh(force=True)

        scr.show_info("Press 'q' key to Quit...")

        dot = []
        for _i in range(5):
            dot.append(Obj("%d" % _i, 0, 0, 'o', _i+1))
        while True:
            for _d in dot:
                _d.move()
                _x,_y,_cr,_col = _d.getPosition()
                scr.display_dot(_x,_y,_cr,colorpair=_col)
            scr.refresh()
            time.sleep(0.01)
            chr = scr.get_ch_and_continue(False)
            if chr==ord('q'):
                scr.saveData()
                for _d in dot:
                    _d.save()
                return
    except Exception,e:
        scr.debug("Err:%s" % sys.exc_info()[0])
        scr.get_ch_and_continue(True)
        raise e
    finally:
        scr.unset_win()

if __name__=='__main__':

    main()
