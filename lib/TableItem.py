from math import sqrt

class TableItem(object):
    def __init__(self, element, screen, goodElements):
        self.search = goodElements
        self.tag = self.searchElement(element, "Variable")

        if self.tag:
            self.plvl = self.searchElement(element, "Passwordlevel")
            self.type = self.searchElement(element, "Type")
            self.changed = False
            self.name = element.findall("Name")[0].text
            self.element = element
            tmp = str(screen.attrib)
            self.screen = tmp[tmp.find(":")+3:-2]
            self.screenElement =  screen
            self.desired = ''
            self.valid = True
        else:
            self.valid = False

    def searchElement(self, element, tag):
        if tag == "Text":
            for prop in element:
                if prop.tag.startswith("ExpProps_"):
                    var = prop.findall("Name")[0].text
                    find = var.find(tag)

                    if find != -1:
                        xmlTag = "<Text>"

                        sTag = xmlTag
                        nTag = sTag[:-1] + "/" + sTag[-1]

                        tmp = prop.findall("ExpPropValue")[0].text

                        if tmp.find(nTag) != -1:
                            continue
                        else:
                            eTag = sTag[0] + "/" + sTag[1:]
                            tmp = tmp[tmp.find(sTag)+len(sTag):tmp.find(eTag)]
                            return tmp

        elif tag == "VariableLink":
            for prop in element:
                if prop.tag.startswith("ExpProps_"):
                    var = prop.findall("Name")[0].text
                    tag = "Variable"
                    find = var.find(tag)

                    if find != -1:
                        xmlTag = "0..TmpHmi"

                        tmp = prop.findall("ExpPropValue")[0].text

                        if tmp.find(xmlTag) == -1:
                            continue
                        else:
                            s = tmp.find(">") + 1
                            e = tmp.find("<")
                            n = 2
                            while e >= 0 and n > 1:
                                e = tmp.find("<", e+len("<"))
                                n -= 1
                            tmp = tmp[s:e]
                            return tmp

        else:
            for text in self.search:
                link = element.findall("LinkName")
                if len(link) != 0:
                    if link[0].text == text:
                        if tag == "Type":
                            return text
                        for prop in element:
                            if prop.tag.startswith("ExpProps_"):
                                var = prop.findall("Name")[0].text
                                find = var.find(tag)

                                if find != -1:
                                    if tag == "Passwordlevel":
                                        xmlTag = "<Passwordlevel>"
                                    else:
                                        xmlTag = "<SymVarTagNr>"

                                    sTag = xmlTag
                                    nTag = sTag[:-1] + "/" + sTag[-1]

                                    tmp = prop.findall("ExpPropValue")[0].text

                                    if tmp.find(nTag) != -1:
                                        continue
                                    else:
                                        eTag = sTag[0] + "/" + sTag[1:]
                                        tmp = tmp[tmp.find(sTag)+len(sTag):tmp.find(eTag)]
                                        return tmp

        return False

    def generateDesired(self, root):
        self.desired = "@General_St.@"

        self.desired += self.screen[2:5]

        self.desired += " "

        tableTypes = ["z_Table_CellInput", "z_Table_CellButtonSwitch", "z_Table_CellSwitch", "z_Table_CellSwitch", "z_Table_CellInputString"]

        if self.type in tableTypes:
            self = self.checkFormatTable()
        else:
            self = self.checkFormatGroup(root)

    def checkFormatGroup(self, root):
        groupBoxes = self.getGroupBoxes()

        myxy = self.getXY(self.element)

        if len(groupBoxes) != 0:
            myGroupBox = groupBoxes[0]

            for groupBox in groupBoxes:
                xy = self.getXY(groupBox)
                if xy[1] < myxy[1] and self.distance(myxy, xy) < self.distance(myxy, self.getXY(myGroupBox)):
                    myGroupBox = groupBox

            text = self.searchElement(myGroupBox, "Text")
            if text[0] == '@' and text[-1] != '@':
                text += '@'

            self.desired += text + ': '

            link = self.searchElement(self.element, "VariableLink")

            self.desired += self.findLinkedVar(link, root)

    def checkFormatTable(self):

        desired = [' ',' ',' ']

        for element in self.screenElement:
            if element.tag.startswith("Elements_"):
                link = element.findall("LinkName")
                if link:
                    link = link[0]
                    if link.text == "z_Table_Label":
                        name = element.findall("Name")[0].text.split("_")
                        itemName = self.name.split("_")

                        if len(itemName) == 3 and len(name) == 2:
                            if itemName[0] == name[0]:
                                desired[0] = self.getValue(element)

                        if len(itemName) == 4 and len(name) == 3:
                            if itemName[0] == name[0] and itemName[-1] == name[-1]:
                                desired[0] = self.getValue(element)

                    elif link.text == "z_Table_RowHeader":
                        name = element.findall("Name")[0].text.split("_")
                        itemName = self.name.split("_")

                        if len(itemName) == 3 and len(name) == 3:
                            if itemName[0] == name[0] and itemName[1] == name[1]:
                                desired[1] = self.getValue(element)

                        if len(itemName) == 4 and len(name) == 4:
                            if itemName[0] == name[0] and itemName[-1] == name[-1] and itemName[1] == name[1]:
                                desired[1] = self.getValue(element)

                    elif link.text == "z_Table_ColumnHeader":
                        name = element.findall("Name")[0].text.split("_")
                        itemName = self.name.split("_")

                        if len(itemName) == 3 and len(name) == 2:
                            if itemName[0] == name[0] and itemName[2][-1] == name[1][-1]:
                                desired[2] = self.getValue(element)

                        if len(itemName) == 4 and len(name) == 3:
                            if itemName[0] == name[0] and itemName[-1] == name[-1] and itemName[2][-1] == name[1][-1]:
                                desired[2] = self.getValue(element)

        for i in range(len(desired)-1):
            if desired[i][0] != '@' and desired[i][-1] != '@':
                desired[i] = '@' + desired[i] + '@'
            if desired[i][0] == '@' and desired[i][-1] != '@':
                desired[i] += '@'

        desired[0] += ": "
        desired[1] += " "

        self.desired += ''.join(desired)

    def findLinkedVar(self, link, root):
        for variable in root.iter("Variable"):
            if str(variable.attrib).find(str(link)) != -1:
                return variable.findall("Recourceslabel")[0].text

        return ""

    def distance(self, xy1, xy2):
        return sqrt((xy2[0] - xy1[0])**2 + (xy2[1] - xy1[1])**2)

    def getXY(self, element):
        x = int(element.findall("StartX")[0].text)
        y = int(element.findall("StartY")[0].text)
        return (x,y)

    def getGroupBoxes(self):
        groupBoxes = []
        for element in self.screenElement:
            if element.tag.startswith("Elements_"):
                link = element.findall("LinkName")
                if len(link) != 0:
                    link = link[0]
                    if link.text == "z_GroupBox":
                        groupBoxes.append(element)

        return groupBoxes

    def getValue(self, element):
        prop = element.findall("ExpProps_0")[0]
        value = prop.findall("ExpPropValue")[0].text
        value = value.replace("<Text>","")
        value = value.replace("</Text>","")
        return value
