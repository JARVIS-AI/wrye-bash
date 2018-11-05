# -*- coding: utf-8 -*-
#
# GPL License and Copyright Notice ============================================
#  This file is part of Wrye Bash.
#
#  Wrye Bash is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  Wrye Bash is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Wrye Bash; if not, write to the Free Software Foundation,
#  Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
#  Wrye Bash copyright (C) 2005-2009 Wrye, 2010-2015 Wrye Bash Team
#  https://github.com/wrye-bash
#
# =============================================================================

from .. import balt
from .. import bass
from .. import bolt
from .. import bosh
from .. import bush
from .. import env
import wx
import wx.wizard as wiz

from ..boop import Installer, MissingDependency


class WizardReturn(object):
    __slots__ = ('cancelled', 'installFiles', 'pageSize', 'pos')

    def __init__(self):
        # cancelled: true if the user canceled or if an error occurred
        self.cancelled = False
        # installFiles: file->dest mapping of files to install
        self.installFiles = bolt.LowerDict()
        # pageSize: Tuple/wxSize of the saved size of the Wizard
        self.pageSize = balt.defSize
        # pos: Tuple/wxPoint of the saved position of the Wizard
        self.pos = balt.defPos


class InstallerFomod(wiz.Wizard):
    def __init__(self, parentWindow, installer, pageSize, pos):
        wizStyle = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX
        wiz.Wizard.__init__(self, parentWindow, title=_(u'Fomod Installer'),
                            pos=pos, style=wizStyle)

        # 'dummy' page tricks the wizard into always showing the "Next" button
        self.dummy = wiz.PyWizardPage(self)
        self.next = None

        # True prevents actually moving to the 'next' page.
        # We use this after the "Next" button is pressed,
        # while the parser is running to return the _actual_ next page
        self.blockChange = True
        # 'finishing' is to allow the "Next" button to be used
        # when it's name is changed to 'Finish' on the last page of the wizard
        self.finishing = False

        self.isArchive = isinstance(installer, bosh.InstallerArchive)
        if self.isArchive:
            self.archivePath = bass.getTempDir().join(installer.archive)
        else:
            self.archivePath = bass.dirs['installers'].join(installer.archive)

        fomod_files = installer.fomod_files()
        fomod_files = (fomod_files[0].s, fomod_files[1].s)
        data_path = bass.dirs['mods']
        ver = env.get_file_version(bass.dirs['app'].join(bush.game.exe).s)
        game_ver = u'.'.join([unicode(i) for i in ver])
        self.parser = Installer(fomod_files, dest=data_path,
                                game_version=game_ver)

        # Intercept the changing event so we can implement 'blockChange'
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGING, self.OnChange)
        self.ret = WizardReturn()
        self.ret.pageSize = pageSize

        # So we can save window size
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wiz.EVT_WIZARD_CANCEL, self.OnClose)
        self.Bind(wiz.EVT_WIZARD_FINISHED, self.OnClose)

        # Set the minimum size for pages, and setup OnSize to resize the
        # First page to the saved size
        self.SetPageSize((600, 500))
        self.firstPage = True

    def OnClose(self, event):
        if not self.IsMaximized():
            # Only save the current size if the page isn't maximized
            self.ret.pageSize = self.GetSize()
            self.ret.pos = self.GetPosition()
        event.Skip()

    def OnSize(self, event):
        if self.firstPage:
            # On the first page, resize it to the saved size
            self.firstPage = False
            self.SetSize(self.ret.pageSize)
        else:
            # Otherwise, regular resize, save the size if we're not
            # maximized
            if not self.IsMaximized():
                self.ret.pageSize = self.GetSize()
                self.pos = self.GetPosition()
            event.Skip()

    def OnChange(self, event):
        if event.GetDirection():
            if not self.finishing:
                # Next, continue script execution
                if self.blockChange:
                    # Tell the current page that next was pressed,
                    # So the parser can continue parsing,
                    # Then show the page that the parser returns,
                    # rather than the dummy page
                    event.GetPage().OnNext()
                    event.Veto()
                    self.blockChange = False
                else:
                    self.blockChange = True
                    return
        else:
            # Previous, pop back to the last state,
            # and resume execution
            self.finishing = False
            event.Veto()
            answer = {'previous_step': True}
            self.parser.send(answer)
            self.blockChange = False
        try:
            step = next(self.parser)
            self.next = PageSelect(self, step['name'], step['groups'])
        except StopIteration:
            self.next = None
        self.ShowPage(self.next)

    def Run(self):
        try:
            self.parser.send(None)
        except MissingDependency as exc:
            page = PageError(self, "Missing Dependency", str(exc))
        else:
            step = next(self.parser)
            page = PageSelect(self, step['name'], step['groups'])
        self.ret.cancelled = not self.RunWizard(page)
        fileIter = ((y, x) for x, y in self.parser.collected_files.iteritems())
        self.ret.installFiles = bolt.LowerDict(fileIter)
        # Clean up temp files
        if self.isArchive:
            try:
                bass.rmTempDir()
            except Exception:
                pass
        return self.ret


# PageInstaller ----------------------------------------------
#  base class for all the parser wizard pages, just to handle
#  a couple simple things here
# ------------------------------------------------------------
class PageInstaller(wiz.PyWizardPage):
    def __init__(self, parent):
        wiz.PyWizardPage.__init__(self, parent)
        self.parent = parent
        self._enableForward(True)

    def _enableForward(self, enable):
        self.parent.FindWindowById(wx.ID_FORWARD).Enable(enable)

    def GetNext(self):
        return self.parent.dummy

    def GetPrev(self):
        return self.parent.dummy

    def OnNext(self):
        # This is what needs to be implemented by sub-classes,
        # this is where flow control objects etc should be
        # created
        pass


# PageError --------------------------------------------------
#  Page that shows an error message, has only a "Cancel"
#  button enabled, and cancels any changes made
# -------------------------------------------------------------
class PageError(PageInstaller):
    def __init__(self, parent, title, errorMsg):
        PageInstaller.__init__(self, parent)

        # Disable the "Finish"/"Next" button
        self._enableForward(False)

        # Layout stuff
        sizerMain = wx.FlexGridSizer(2, 1, 5, 5)
        textError = balt.RoTextCtrl(self, errorMsg, autotooltip=False)
        sizerMain.Add(balt.StaticText(parent, label=title))
        sizerMain.Add(textError, 0, wx.ALL | wx.CENTER | wx.EXPAND)
        sizerMain.AddGrowableCol(0)
        sizerMain.AddGrowableRow(1)
        self.SetSizer(sizerMain)
        self.Layout()

    def GetNext(self):
        return None

    def GetPrev(self):
        return None


# PageSelect -------------------------------------------------
#  A Page that shows a message up top, with a selection box on
#  the left (multi- or single- selection), with an optional
#  associated image and description for each option, shown when
#  that item is selected
# ------------------------------------------------------------
class PageSelect(PageInstaller):
    def __init__(self, parent, stepName, listGroups):
        PageInstaller.__init__(self, parent)

        # ListBox -> (group_id, group_type)
        self.boxGroupMap = {}
        # ListBox -> [(option_id, option_type, option_desc, option_img), ...]
        self.boxOptionMap = {}

        sizerMain = wx.FlexGridSizer(2, 1, 0, 0)
        sizerMain.Add(balt.StaticText(self, stepName))
        sizerContent = wx.GridSizer(1, 2, 0, 0)

        sizerExtra = wx.GridSizer(2, 1, 0, 0)
        self.bmpItem = balt.Picture(self, 0, 0, background=None)
        self.textItem = balt.RoTextCtrl(self, autotooltip=False)
        sizerExtra.Add(self.bmpItem, 1, wx.ALL | wx.EXPAND)
        sizerExtra.Add(self.textItem, 1, wx.EXPAND | wx.ALL)

        sizerGroups = wx.GridSizer(len(listGroups), 1, 0, 0)
        for group in listGroups:
            sizerGroup = wx.FlexGridSizer(2, 1, 0, 0)
            sizerGroup.Add(balt.StaticText(self, group['name']))

            if group['type'] == 'SelectExactlyOne':
                listType = 'list'
            else:
                listType = 'checklist'
            listBox = balt.listBox(self, kind=listType, isHScroll=True,
                                   onSelect=self.OnSelect,
                                   onCheck=self.OnCheck)
            self.boxGroupMap[listBox] = (group['id'], group['type'])
            self.boxOptionMap[listBox] = []

            for option in group['plugins']:
                idx = listBox.Append(option['name'])
                if option['type'] in ('Recommended', 'Required'):
                    if group['type'] == 'SelectExactlyOne':
                        listBox.SetSelection(idx)
                    else:
                        listBox.Check(idx, True)
                        self.Check(listBox, idx)
                self.boxOptionMap[listBox].append((option['id'],
                                                   option['type'],
                                                   option['description'],
                                                   option['image']))

            if group['type'] == 'SelectExactlyOne':
                listBox.SetSelection(listBox.GetSelection() or 0)
            elif group['type'] == 'SelectAtLeastOne':
                if not listBox.GetChecked():
                    listBox.Check(0, True)
            elif group['type'] == 'SelectAll':
                for idx in xrange(0, listBox.GetCount()):
                    listBox.Check(idx, True)

            if listGroups.index(group) == 0:
                self.Select(listBox, listBox.GetSelection() or 0)

            sizerGroup.Add(listBox, 1, wx.EXPAND | wx.ALL)
            sizerGroup.AddGrowableRow(1)
            sizerGroup.AddGrowableCol(0)
            sizerGroups.Add(sizerGroup, wx.ID_ANY, wx.EXPAND)

        sizerContent.Add(sizerGroups, wx.ID_ANY, wx.EXPAND)
        sizerContent.Add(sizerExtra, wx.ID_ANY, wx.EXPAND)
        sizerMain.Add(sizerContent, wx.ID_ANY, wx.EXPAND)
        sizerMain.AddGrowableRow(1)
        sizerMain.AddGrowableCol(0)

        self.SetSizer(sizerMain)
        self.Layout()

    # Handles option type
    def CheckOption(self, box, idx, check=True):
        option_type = self.boxOptionMap[box][idx][1]
        if check and option_type == 'NotUsable':
            box.Check(idx, False)
        elif not check and option_type == 'Required':
            box.Check(idx, True)
        else:
            box.Check(idx, check)

    # Handles group type
    def Check(self, box, idx):
        group_type = self.boxGroupMap[box][1]
        self.CheckOption(box, idx, box.IsChecked(idx))

        if group_type == 'SelectAtLeastOne':
            if not box.IsChecked(idx) and len(box.GetChecked()) == 0:
                box.Check(idx, True)
        elif group_type == 'SelectAtMostOne':
            checked = box.GetChecked()
            if box.IsChecked(idx) and len(checked) > 1:
                checked = (a for a in checked if a != idx)
                for i in checked:
                    self.CheckOption(box, i, False)
        elif group_type == 'SelectAll':
            box.Check(idx, True)

    def OnCheck(self, event):
        idx = event.GetInt()
        box = event.GetEventObject()
        self.Check(box, idx)

    def Select(self, box, idx):
        box.SetSelection(idx)
        option = self.boxOptionMap[box][idx]
        self._enableForward(True)
        self.textItem.SetValue(option[2])
        # Don't want the bitmap to resize until we call self.Layout()
        self.bmpItem.Freeze()
        img = self.parent.archivePath.join(option[3])
        if img.isfile():
            image = wx.Bitmap(img.s)
            self.bmpItem.SetBitmap(image)
            self.bmpItem.SetCursor(wx.StockCursor(wx.CURSOR_MAGNIFIER))
        else:
            self.bmpItem.SetBitmap(None)
            self.bmpItem.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
        self.bmpItem.Thaw()

    def OnSelect(self, event):
        idx = event.GetInt()
        box = event.GetEventObject()
        self.Select(box, idx)

    def OnNext(self):
        answer = {}

        for box, group in self.boxGroupMap.iteritems():
            group_id = group[0]
            group_type = group[1]
            answer[group_id] = []
            if group_type == 'SelectExactlyOne':
                idx = box.GetSelection()
                answer[group_id] = [self.boxOptionMap[box][idx][0]]
            else:
                for idx in box.GetChecked():
                    answer[group_id].append(self.boxOptionMap[box][idx][0])

            idxNum = len(answer[group_id])
            if group_type == 'SelectExactlyOne' and idxNum != 1:
                raise ValueError("Must select exatly one.")
            elif group_type == 'SelectAtMostOne' and idxNum > 1:
                raise ValueError("Must select at most one.")
            elif group_type == 'SelectAtLeast' and idxNum < 1:
                raise ValueError("Must select at most one.")
            elif (group_type == 'SelectAll'
                    and idxNum != len(self.boxOptionMap[box])):
                raise ValueError("Must select at most one.")

        self.parent.parser.send(answer)
