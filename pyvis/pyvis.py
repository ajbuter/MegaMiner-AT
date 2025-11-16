import json
import subprocess
import sys
import time
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import *

class BoardState:
    def __init__(self, data):
        self.name = {'R':data['TeamNameR'],'B':data['TeamNameB']}
        self.turn = data['CurrentTurn']
        self.grid = data['EntityGrid']
        self.floor = data['FloorTiles']
        self.towers = data['Towers']
        self.mercs = data['Mercenaries']
        self.demons = data['Demons']
        self.demon_spawners = data['DemonSpawners']
        self.player = {'R': data['PlayerBaseR'],'B': data['PlayerBaseB'] }

class Cell(QLabel):
    def __init__(self, color):
        super().__init__("")
        self.setAutoFillBackground(True)
        self.setAlignment( Qt.AlignHCenter | Qt.AlignVCenter )

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(color))
        self.setPalette(palette)
        self.reset()

    def creature(self, l1, l2, color):
        self.setFontSize(15)
        self.setText( f"{l1}\n{l2}")
        self.setTextColor( color )

    def setFontSize(self,size):
        font = self.font()
        font.setPointSize(size)
        self.setFont(font)

    def setTextColor(self, color):
        p = self.palette()
        p.setColor(QPalette.Foreground, QColor(color))
        self.setPalette(p)

    def reset(self):
        self.setText('')
        self.setTextColor('black')
        self.setFontSize(30)

class PyQtExample(QWidget):
    TEAM_COLORS = {'r':'red','b':'blue'}
    OTHER_COLORS = {'r':'blue','b':'red'}
    def __init__(self, proc):
        super().__init__()
        self.proc = proc
        self.lines = proc.stdout.readlines()
        self.rx()
        self.board = BoardState( json.loads(self.rx()) )
        self.rx()
        self.rx()
        self.rx()
        self.initUI()

    def rx(self):
        data = self.lines.pop(0)
        print(data)
        return data

    def initUI(self):
        self.setWindowTitle("MegaMiner2025")
        self.setGeometry(100, 100, 300, 150)

        layout = QVBoxLayout()

        upper_bar = QHBoxLayout()

        ct_lbl = QLabel("Current Turn:",self)
        upper_bar.addWidget(ct_lbl)
        self.current_turn = QLabel(str(self.board.turn), self)
        upper_bar.addWidget(self.current_turn)

        self.turn_btn = QPushButton("Next", self)
        self.turn_btn.clicked.connect(self.turn)
        upper_bar.addWidget(self.turn_btn)


        self.field = QGridLayout()
        self.grid = []
        self.field.setSpacing(0)

        lower_bar = QHBoxLayout()
        self.sts = {"R" : QLabel(), "B" : QLabel() }
        for s in self.sts:
            lower_bar.addWidget( self.sts[s] )
        self.sts['B'].setAlignment( Qt.AlignRight )
        self.generate_field()

        layout.addLayout( upper_bar )
        layout.addLayout( self.field )
        layout.addLayout( lower_bar )
        self.setLayout(layout)

    def turn(self):
        data = self.rx()
        try:
            self.board = BoardState( json.loads(data) )
            self.current_turn.setText(f"{self.board.turn}")
            self.update_field()
            return True
        except json.decoder.JSONDecodeError:
            print(data)
            self.current_turn.setText(data.replace("-",""))
            self.turn_btn.setEnabled(False)
            return False

    def generate_field(self):
        ri = 0
        for row in self.board.floor:
            self.grid.append( [] )
            self.field.setRowMinimumHeight(ri, 50)
            for c in range(len(row)):
                if row[c] in self.TEAM_COLORS:
                    self.grid[ri].append( Cell(self.TEAM_COLORS[row[c]]) )
                elif row[c] == 'O':
                    self.grid[ri].append( Cell('grey') )
                else:
                    self.grid[ri].append( Cell('white') )
                self.field.addWidget(self.grid[ri][c], ri, c)
            ri += 1
        for ci in range(len(self.board.floor[0])):
            self.field.setColumnMinimumWidth(ci, 50)
        self.update_field()


    def update_field(self):
        for ri in range(len(self.board.floor)):
            for ci in range(len(self.board.floor[0])):
                self.grid[ri][ci].reset()
        for spawner in self.board.demon_spawners:
            self.grid[spawner['y']][spawner['x']].setText( 'X' )
            self.grid[spawner['y']][spawner['x']].setTextColor( self.TEAM_COLORS[spawner['Target']] )
        for player in self.board.player:
            pdata = self.board.player[player]
            self.grid[pdata['y']][pdata['x']].setText( 'B' )
            self.grid[pdata['y']][pdata['x']].setTextColor( self.TEAM_COLORS[player.lower()] )
        for tower in self.board.towers:
            self.grid[tower['y']][tower['x']].setText( tower['Type'][0:2] )
        for merc in self.board.mercs:
            self.grid[merc['y']][merc['x']].creature('M', merc['Health'], self.TEAM_COLORS[merc['Team']] )
        for demon in self.board.demons:
            self.grid[demon['y']][demon['x']].creature('D', demon['Health'], self.OTHER_COLORS[demon['Team']] )

        for s in self.sts:
            spawner = list( filter(lambda sp: sp['Target'] == s.lower(),self.board.demon_spawners))[0]
            sts_txt = [
                    f"{self.board.name[s]}",
                    f"Health: {self.board.player[s]['Health']}",
                    f"Money: ${self.board.player[s]['Money']}",
                    f"Next Demon: {spawner['ReloadTime']}"
                    ]
            self.sts[s].setText("\n".join(sts_txt))
        self.update()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    args = ["python3","../backend/main.py"]
    args.extend( sys.argv[1:] )
    print(args)
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    ex = PyQtExample( p )
    ex.show()
    if not p.poll():
        p.kill()
    sys.exit(app.exec_())
