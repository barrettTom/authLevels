from PyQt5.QtCore import Qt, QAbstractTableModel, QVariant
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import QMessageBox, QProgressDialog, QApplication
from datetime import datetime
import csv
import chardet

import xml.etree.ElementTree as ET

from lib.TableItem import TableItem

class TableModel(QAbstractTableModel):
    def __init__(self, masterView, path, goodElements, parent=None):
        super(TableModel, self).__init__(parent)

        self.masterView = masterView

        self.show = False

        self.changes = []

        self.path = path
        self.tree = ET.parse(self.path)
        self.root = self.tree.getroot()

        self.items = self.getItems(goodElements)

    def getItems(self, goodElements):
        items = []

        for screen in self.root.iter("Picture"):

            badScreens = ["Kopie", "z_", "p_", "_Popup"]
            bad = False
            for badScreen in badScreens:
                if str(screen.attrib).find(badScreen) != -1:
                    bad = True
            if bad:
                continue

            for element in screen:
                if element.tag.startswith("Elements_"):
                    item = TableItem(element, screen, goodElements)
                    if item.valid:
                        items.append(item)

        return items

    def giveCSV(self, path, language):
        if language[0] == "ZENONSTR.TXT":
            col = 1
        elif language[0] == "FR_FR.TXT":
            col = 2
        elif language[0] == "GB_EN.TXT":
            col = 3

        with open(path, 'rb') as f:
            result = chardet.detect(f.read())

        with open(path, encoding=result['encoding']) as csvfile:
            reader = csv.reader(csvfile, delimiter='\t')
            for item in self.items:
                if item.desired == item.tag:
                    parts = item.tag.split("@")
                    for line in reader:
                        if line[0] == parts[1]:
                            first = line[col]
                        if line[0] == parts[3]:
                            third = line[col]
                        if line[0] == parts[5]:
                            fifth = line[col]

                    item.tag = item.tag.replace(parts[1], first)
                    item.tag = item.tag.replace(parts[3], third)
                    item.tag = item.tag.replace(parts[5], fifth)
                    item.tag = item.tag.replace("@","")

    def toggleShow(self):
        self.show = not self.show

    def generateFormat(self):

        pb = QProgressDialog("Generating...", "Cancel", 0, len(self.items), self.masterView)
        i = 0
        pb.setValue(i)
        while i < len(self.items):
            self.items[i].generateDesired(self.root)
            i += 1
            pb.setValue(i)
            QApplication.processEvents()

    def save(self,path=None):
        if path is None:
            path = self.path

        f = open('changelog.txt','a')
        f.write(str(datetime.now())+'\n')
        for change in self.changes:
            f.write(self.items[change['index'].row()].tag + " from " + change['before'] + " to " + change['after'] + '\n')
        f.close()

        self.changes = []

        for item in self.items:
            item.changed = False

        self.tree.write(path)

    def undo(self):
        try:
            change = self.changes.pop()
            self.setData(change['index'], change['before'],2,True)

        except:
            print("nothing to undo")

    def isChanges(self):
        if len(self.changes) > 0:
            return True
        else:
            return False

    def flipI(self, x):
        if x == '1':
            return 'A'
        if x == '2':
            return 'B'
        if x == '3':
            return 'C'
        if x == '4':
            return 'D'
        if x == '5':
            return 'E'
        if x == '0':
            return '0'
        return False

    def flipS(self, x):
        if x == 'A':
            return '1'
        if x == 'B':
            return '2'
        if x == 'C':
            return '3'
        if x == 'D':
            return '4'
        if x == 'E':
            return '5'
        if x == '0':
            return '0'
        return False

    def columnCount(self, parent):
        return 4

    def rowCount(self, parent):
        return len(self.items)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0:
                return "Tag"
            elif section == 1:
                return "Password Level"
            elif section == 2:
                return "Screen"
            else:
                return "Standard"

        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        if index.column() == 1:
            return Qt.ItemIsEnabled | Qt.ItemIsEditable

        return Qt.ItemIsEnabled

    def data(self, index, role):
        if not index.isValid():
            return None

        row = index.row()
        column = index.column()

        text = self.flipI(self.items[row].plvl)

        if role == Qt.BackgroundRole:
            if self.items[row].changed:
                return QBrush(Qt.red)
            elif self.items[row].desired != self.items[row].tag and self.show:
                return QBrush(Qt.yellow)
            else:
                return QBrush(Qt.transparent)

        if role == Qt.EditRole:
            return QVariant(text)

        if role != Qt.DisplayRole:
            return None

        if column == 0:
            return QVariant(self.items[row].tag)
        elif column == 1:
            return QVariant(text)
        elif column == 2:
            return QVariant(self.items[row].screen)
        elif column == 3:
            return QVariant(self.items[row].desired)

        return QVariant()

    def setData(self, index, value, role, undo = False):

        value = self.flipS(value)

        if not value:
            QMessageBox.warning(self.masterView,"Error:","Only the values A, B, C, D, E or 0 are allowed.", QMessageBox.Ok)
            return False

        if index.column() == 1:
            if undo:
                self.items[index.row()].changed = False
            elif self.items[index.row()].plvl != value:
                self.items[index.row()].changed = True
                self.changes.append({'index' : index, 'before' : self.flipI(self.items[index.row()].plvl), 'after' : self.flipI(value)})

            self.items[index.row()].plvl = value

            for prop in self.items[index.row()].element:
                if prop.tag.startswith("ExpProps_"):
                    var = prop.findall("Name")[0].text
                    find = var.find("Passwordlevel")
                    if find != -1:
                        prop.findall("ExpPropValue")[0].text = "<Passwordlevel>"+value+"</Passwordlevel>"

        return True

    def sort(self, col, order):
        self.layoutAboutToBeChanged.emit()
        if col == 0:
            if order == 0:
                self.items = sorted(self.items, key = lambda k: k.tag)
            else:
                self.items = sorted(self.items, key = lambda k: k.tag, reverse = True)
        elif col == 1:
            if order == 0:
                self.items = sorted(self.items, key = lambda k: k.plvl)
            else:
                self.items = sorted(self.items, key = lambda k: k.plvl, reverse = True)
        elif col == 2:
            if order == 0:
                self.items = sorted(self.items, key = lambda k: k.screen)
            else:
                self.items = sorted(self.items, key = lambda k: k.screen, reverse = True)

        self.layoutChanged.emit()
