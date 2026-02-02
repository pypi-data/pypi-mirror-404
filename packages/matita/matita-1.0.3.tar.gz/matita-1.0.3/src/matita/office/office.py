from . import com_arguments, unwrap
from .office import *

import win32com.client

# BackstageGroupStyle enumeration
BackstageGroupStyleError = 2
BackstageGroupStyleNormal = 0
BackstageGroupStyleWarning = 1

class BulletFormat2:

    def __init__(self, bulletformat2=None):
        self.com_object= bulletformat2

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Character(self):
        return self.com_object.Character

    @Character.setter
    def Character(self, value):
        self.com_object.Character = value

    @property
    def character(self):
        """Alias for Character"""
        return self.Character

    @character.setter
    def character(self, value):
        """Alias for Character.setter"""
        self.Character = value

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Font(self):
        return self.com_object.Font

    @property
    def font(self):
        """Alias for Font"""
        return self.Font

    @property
    def Number(self):
        return self.com_object.Number

    @property
    def number(self):
        """Alias for Number"""
        return self.Number

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    @property
    def RelativeSize(self):
        return self.com_object.RelativeSize

    @RelativeSize.setter
    def RelativeSize(self, value):
        self.com_object.RelativeSize = value

    @property
    def relativesize(self):
        """Alias for RelativeSize"""
        return self.RelativeSize

    @relativesize.setter
    def relativesize(self, value):
        """Alias for RelativeSize.setter"""
        self.RelativeSize = value

    @property
    def relative_size(self):
        """Alias for RelativeSize"""
        return self.RelativeSize

    @relative_size.setter
    def relative_size(self, value):
        """Alias for RelativeSize.setter"""
        self.RelativeSize = value

    @property
    def StartValue(self):
        return self.com_object.StartValue

    @StartValue.setter
    def StartValue(self, value):
        self.com_object.StartValue = value

    @property
    def startvalue(self):
        """Alias for StartValue"""
        return self.StartValue

    @startvalue.setter
    def startvalue(self, value):
        """Alias for StartValue.setter"""
        self.StartValue = value

    @property
    def start_value(self):
        """Alias for StartValue"""
        return self.StartValue

    @start_value.setter
    def start_value(self, value):
        """Alias for StartValue.setter"""
        self.StartValue = value

    @property
    def Style(self):
        return self.com_object.Style

    @Style.setter
    def Style(self, value):
        self.com_object.Style = value

    @property
    def style(self):
        """Alias for Style"""
        return self.Style

    @style.setter
    def style(self, value):
        """Alias for Style.setter"""
        self.Style = value

    @property
    def Type(self):
        return self.com_object.Type

    @Type.setter
    def Type(self, value):
        self.com_object.Type = value

    @property
    def type(self):
        """Alias for Type"""
        return self.Type

    @type.setter
    def type(self, value):
        """Alias for Type.setter"""
        self.Type = value

    @property
    def UseTextColor(self):
        return self.com_object.UseTextColor

    @UseTextColor.setter
    def UseTextColor(self, value):
        self.com_object.UseTextColor = value

    @property
    def usetextcolor(self):
        """Alias for UseTextColor"""
        return self.UseTextColor

    @usetextcolor.setter
    def usetextcolor(self, value):
        """Alias for UseTextColor.setter"""
        self.UseTextColor = value

    @property
    def use_text_color(self):
        """Alias for UseTextColor"""
        return self.UseTextColor

    @use_text_color.setter
    def use_text_color(self, value):
        """Alias for UseTextColor.setter"""
        self.UseTextColor = value

    @property
    def UseTextFont(self):
        return self.com_object.UseTextFont

    @UseTextFont.setter
    def UseTextFont(self, value):
        self.com_object.UseTextFont = value

    @property
    def usetextfont(self):
        """Alias for UseTextFont"""
        return self.UseTextFont

    @usetextfont.setter
    def usetextfont(self, value):
        """Alias for UseTextFont.setter"""
        self.UseTextFont = value

    @property
    def use_text_font(self):
        """Alias for UseTextFont"""
        return self.UseTextFont

    @use_text_font.setter
    def use_text_font(self, value):
        """Alias for UseTextFont.setter"""
        self.UseTextFont = value

    @property
    def Visible(self):
        return self.com_object.Visible

    @Visible.setter
    def Visible(self, value):
        self.com_object.Visible = value

    @property
    def visible(self):
        """Alias for Visible"""
        return self.Visible

    @visible.setter
    def visible(self, value):
        """Alias for Visible.setter"""
        self.Visible = value

    def Picture(self, FileName=None):
        arguments = com_arguments([unwrap(a) for a in [FileName]])
        return self.com_object.Picture(*arguments)

    def picture(self, FileName=None):
        """Alias for Picture"""
        arguments = [FileName]
        return self.Picture(*arguments)


# CertificateDetail enumeration
certdetAvailable = 0
certdetExpirationDate = 3
certdetIssuer = 2
certdetSubject = 1
certdetThumbprint = 4

# CertificateVerificationResults enumeration
certverresError = 0
certverresExpired = 5
certverresInvalid = 4
certverresRevoked = 6
certverresUntrusted = 7
certverresUnverified = 2
certverresValid = 3
certverresVerifying = 1

class COMAddIn:

    def __init__(self, comaddin=None):
        self.com_object= comaddin

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Connect(self):
        return self.com_object.Connect

    @Connect.setter
    def Connect(self, value):
        self.com_object.Connect = value

    @property
    def connect(self):
        """Alias for Connect"""
        return self.Connect

    @connect.setter
    def connect(self, value):
        """Alias for Connect.setter"""
        self.Connect = value

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Description(self):
        return self.com_object.Description

    @Description.setter
    def Description(self, value):
        self.com_object.Description = value

    @property
    def description(self):
        """Alias for Description"""
        return self.Description

    @description.setter
    def description(self, value):
        """Alias for Description.setter"""
        self.Description = value

    @property
    def Guid(self):
        return self.com_object.Guid

    @property
    def guid(self):
        """Alias for Guid"""
        return self.Guid

    @property
    def Object(self):
        return self.com_object.Object

    @Object.setter
    def Object(self, value):
        self.com_object.Object = value

    @property
    def object(self):
        """Alias for Object"""
        return self.Object

    @object.setter
    def object(self, value):
        """Alias for Object.setter"""
        self.Object = value

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    @property
    def ProgId(self):
        return self.com_object.ProgId

    @property
    def progid(self):
        """Alias for ProgId"""
        return self.ProgId

    @property
    def prog_id(self):
        """Alias for ProgId"""
        return self.ProgId


class COMAddIns:

    def __init__(self, comaddins=None):
        self.com_object= comaddins

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        return self.com_object.Item(*arguments)

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)

    def Update(self):
        return self.com_object.Update()

    def update(self):
        """Alias for Update"""
        return self.Update()


class CommandBar:

    def __init__(self, commandbar=None):
        self.com_object= commandbar

    @property
    def AdaptiveMenu(self):
        return self.com_object.AdaptiveMenu

    @AdaptiveMenu.setter
    def AdaptiveMenu(self, value):
        self.com_object.AdaptiveMenu = value

    @property
    def adaptivemenu(self):
        """Alias for AdaptiveMenu"""
        return self.AdaptiveMenu

    @adaptivemenu.setter
    def adaptivemenu(self, value):
        """Alias for AdaptiveMenu.setter"""
        self.AdaptiveMenu = value

    @property
    def adaptive_menu(self):
        """Alias for AdaptiveMenu"""
        return self.AdaptiveMenu

    @adaptive_menu.setter
    def adaptive_menu(self, value):
        """Alias for AdaptiveMenu.setter"""
        self.AdaptiveMenu = value

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def BuiltIn(self):
        return self.com_object.BuiltIn

    @property
    def builtin(self):
        """Alias for BuiltIn"""
        return self.BuiltIn

    @property
    def built_in(self):
        """Alias for BuiltIn"""
        return self.BuiltIn

    @property
    def Context(self):
        return self.com_object.Context

    @Context.setter
    def Context(self, value):
        self.com_object.Context = value

    @property
    def context(self):
        """Alias for Context"""
        return self.Context

    @context.setter
    def context(self, value):
        """Alias for Context.setter"""
        self.Context = value

    @property
    def Controls(self):
        return self.com_object.Controls

    @property
    def controls(self):
        """Alias for Controls"""
        return self.Controls

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Enabled(self):
        return self.com_object.Enabled

    @Enabled.setter
    def Enabled(self, value):
        self.com_object.Enabled = value

    @property
    def enabled(self):
        """Alias for Enabled"""
        return self.Enabled

    @enabled.setter
    def enabled(self, value):
        """Alias for Enabled.setter"""
        self.Enabled = value

    @property
    def Height(self):
        return self.com_object.Height

    @Height.setter
    def Height(self, value):
        self.com_object.Height = value

    @property
    def height(self):
        """Alias for Height"""
        return self.Height

    @height.setter
    def height(self, value):
        """Alias for Height.setter"""
        self.Height = value

    @property
    def Index(self):
        return self.com_object.Index

    @property
    def index(self):
        """Alias for Index"""
        return self.Index

    @property
    def Left(self):
        return self.com_object.Left

    @Left.setter
    def Left(self, value):
        self.com_object.Left = value

    @property
    def left(self):
        """Alias for Left"""
        return self.Left

    @left.setter
    def left(self, value):
        """Alias for Left.setter"""
        self.Left = value

    @property
    def Name(self):
        return self.com_object.Name

    @property
    def name(self):
        """Alias for Name"""
        return self.Name

    @property
    def NameLocal(self):
        return self.com_object.NameLocal

    @NameLocal.setter
    def NameLocal(self, value):
        self.com_object.NameLocal = value

    @property
    def namelocal(self):
        """Alias for NameLocal"""
        return self.NameLocal

    @namelocal.setter
    def namelocal(self, value):
        """Alias for NameLocal.setter"""
        self.NameLocal = value

    @property
    def name_local(self):
        """Alias for NameLocal"""
        return self.NameLocal

    @name_local.setter
    def name_local(self, value):
        """Alias for NameLocal.setter"""
        self.NameLocal = value

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    @property
    def Position(self):
        return self.com_object.Position

    @Position.setter
    def Position(self, value):
        self.com_object.Position = value

    @property
    def position(self):
        """Alias for Position"""
        return self.Position

    @position.setter
    def position(self, value):
        """Alias for Position.setter"""
        self.Position = value

    @property
    def Protection(self):
        return self.com_object.Protection

    @Protection.setter
    def Protection(self, value):
        self.com_object.Protection = value

    @property
    def protection(self):
        """Alias for Protection"""
        return self.Protection

    @protection.setter
    def protection(self, value):
        """Alias for Protection.setter"""
        self.Protection = value

    @property
    def RowIndex(self):
        return self.com_object.RowIndex

    @RowIndex.setter
    def RowIndex(self, value):
        self.com_object.RowIndex = value

    @property
    def rowindex(self):
        """Alias for RowIndex"""
        return self.RowIndex

    @rowindex.setter
    def rowindex(self, value):
        """Alias for RowIndex.setter"""
        self.RowIndex = value

    @property
    def row_index(self):
        """Alias for RowIndex"""
        return self.RowIndex

    @row_index.setter
    def row_index(self, value):
        """Alias for RowIndex.setter"""
        self.RowIndex = value

    @property
    def Top(self):
        return self.com_object.Top

    @Top.setter
    def Top(self, value):
        self.com_object.Top = value

    @property
    def top(self):
        """Alias for Top"""
        return self.Top

    @top.setter
    def top(self, value):
        """Alias for Top.setter"""
        self.Top = value

    @property
    def Type(self):
        return self.com_object.Type

    @property
    def type(self):
        """Alias for Type"""
        return self.Type

    @property
    def Visible(self):
        return self.com_object.Visible

    @Visible.setter
    def Visible(self, value):
        self.com_object.Visible = value

    @property
    def visible(self):
        """Alias for Visible"""
        return self.Visible

    @visible.setter
    def visible(self, value):
        """Alias for Visible.setter"""
        self.Visible = value

    @property
    def Width(self):
        return self.com_object.Width

    @Width.setter
    def Width(self, value):
        self.com_object.Width = value

    @property
    def width(self):
        """Alias for Width"""
        return self.Width

    @width.setter
    def width(self, value):
        """Alias for Width.setter"""
        self.Width = value

    def Delete(self):
        return self.com_object.Delete()

    def delete(self):
        """Alias for Delete"""
        return self.Delete()

    def FindControl(self, Type=None, Id=None, Tag=None, Visible=None, Recursive=None):
        arguments = com_arguments([unwrap(a) for a in [Type, Id, Tag, Visible, Recursive]])
        return CommandBarControl(self.com_object.FindControl(*arguments))

    def findcontrol(self, Type=None, Id=None, Tag=None, Visible=None, Recursive=None):
        """Alias for FindControl"""
        arguments = [Type, Id, Tag, Visible, Recursive]
        return self.FindControl(*arguments)

    def find_control(self, Type=None, Id=None, Tag=None, Visible=None, Recursive=None):
        """Alias for FindControl"""
        arguments = [Type, Id, Tag, Visible, Recursive]
        return self.FindControl(*arguments)

    def Reset(self):
        return self.com_object.Reset()

    def reset(self):
        """Alias for Reset"""
        return self.Reset()

    def ShowPopup(self, x=None, y=None):
        arguments = com_arguments([unwrap(a) for a in [x, y]])
        return self.com_object.ShowPopup(*arguments)

    def showpopup(self, x=None, y=None):
        """Alias for ShowPopup"""
        arguments = [x, y]
        return self.ShowPopup(*arguments)

    def show_popup(self, x=None, y=None):
        """Alias for ShowPopup"""
        arguments = [x, y]
        return self.ShowPopup(*arguments)


class CommandBarButton:

    def __init__(self, commandbarbutton=None):
        self.com_object= commandbarbutton

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def BeginGroup(self):
        return self.com_object.BeginGroup

    @BeginGroup.setter
    def BeginGroup(self, value):
        self.com_object.BeginGroup = value

    @property
    def begingroup(self):
        """Alias for BeginGroup"""
        return self.BeginGroup

    @begingroup.setter
    def begingroup(self, value):
        """Alias for BeginGroup.setter"""
        self.BeginGroup = value

    @property
    def begin_group(self):
        """Alias for BeginGroup"""
        return self.BeginGroup

    @begin_group.setter
    def begin_group(self, value):
        """Alias for BeginGroup.setter"""
        self.BeginGroup = value

    @property
    def BuiltIn(self):
        return self.com_object.BuiltIn

    @property
    def builtin(self):
        """Alias for BuiltIn"""
        return self.BuiltIn

    @property
    def built_in(self):
        """Alias for BuiltIn"""
        return self.BuiltIn

    @property
    def BuiltInFace(self):
        return self.com_object.BuiltInFace

    @BuiltInFace.setter
    def BuiltInFace(self, value):
        self.com_object.BuiltInFace = value

    @property
    def builtinface(self):
        """Alias for BuiltInFace"""
        return self.BuiltInFace

    @builtinface.setter
    def builtinface(self, value):
        """Alias for BuiltInFace.setter"""
        self.BuiltInFace = value

    @property
    def built_in_face(self):
        """Alias for BuiltInFace"""
        return self.BuiltInFace

    @built_in_face.setter
    def built_in_face(self, value):
        """Alias for BuiltInFace.setter"""
        self.BuiltInFace = value

    @property
    def Caption(self):
        return self.com_object.Caption

    @Caption.setter
    def Caption(self, value):
        self.com_object.Caption = value

    @property
    def caption(self):
        """Alias for Caption"""
        return self.Caption

    @caption.setter
    def caption(self, value):
        """Alias for Caption.setter"""
        self.Caption = value

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def DescriptionText(self):
        return self.com_object.DescriptionText

    @DescriptionText.setter
    def DescriptionText(self, value):
        self.com_object.DescriptionText = value

    @property
    def descriptiontext(self):
        """Alias for DescriptionText"""
        return self.DescriptionText

    @descriptiontext.setter
    def descriptiontext(self, value):
        """Alias for DescriptionText.setter"""
        self.DescriptionText = value

    @property
    def description_text(self):
        """Alias for DescriptionText"""
        return self.DescriptionText

    @description_text.setter
    def description_text(self, value):
        """Alias for DescriptionText.setter"""
        self.DescriptionText = value

    @property
    def Enabled(self):
        return self.com_object.Enabled

    @Enabled.setter
    def Enabled(self, value):
        self.com_object.Enabled = value

    @property
    def enabled(self):
        """Alias for Enabled"""
        return self.Enabled

    @enabled.setter
    def enabled(self, value):
        """Alias for Enabled.setter"""
        self.Enabled = value

    @property
    def FaceId(self):
        return self.com_object.FaceId

    @FaceId.setter
    def FaceId(self, value):
        self.com_object.FaceId = value

    @property
    def faceid(self):
        """Alias for FaceId"""
        return self.FaceId

    @faceid.setter
    def faceid(self, value):
        """Alias for FaceId.setter"""
        self.FaceId = value

    @property
    def face_id(self):
        """Alias for FaceId"""
        return self.FaceId

    @face_id.setter
    def face_id(self, value):
        """Alias for FaceId.setter"""
        self.FaceId = value

    @property
    def Height(self):
        return self.com_object.Height

    @Height.setter
    def Height(self, value):
        self.com_object.Height = value

    @property
    def height(self):
        """Alias for Height"""
        return self.Height

    @height.setter
    def height(self, value):
        """Alias for Height.setter"""
        self.Height = value

    @property
    def HelpContextId(self):
        return self.com_object.HelpContextId

    @HelpContextId.setter
    def HelpContextId(self, value):
        self.com_object.HelpContextId = value

    @property
    def helpcontextid(self):
        """Alias for HelpContextId"""
        return self.HelpContextId

    @helpcontextid.setter
    def helpcontextid(self, value):
        """Alias for HelpContextId.setter"""
        self.HelpContextId = value

    @property
    def help_context_id(self):
        """Alias for HelpContextId"""
        return self.HelpContextId

    @help_context_id.setter
    def help_context_id(self, value):
        """Alias for HelpContextId.setter"""
        self.HelpContextId = value

    @property
    def HelpFile(self):
        return self.com_object.HelpFile

    @HelpFile.setter
    def HelpFile(self, value):
        self.com_object.HelpFile = value

    @property
    def helpfile(self):
        """Alias for HelpFile"""
        return self.HelpFile

    @helpfile.setter
    def helpfile(self, value):
        """Alias for HelpFile.setter"""
        self.HelpFile = value

    @property
    def help_file(self):
        """Alias for HelpFile"""
        return self.HelpFile

    @help_file.setter
    def help_file(self, value):
        """Alias for HelpFile.setter"""
        self.HelpFile = value

    @property
    def HyperlinkType(self):
        return self.com_object.HyperlinkType

    @HyperlinkType.setter
    def HyperlinkType(self, value):
        self.com_object.HyperlinkType = value

    @property
    def hyperlinktype(self):
        """Alias for HyperlinkType"""
        return self.HyperlinkType

    @hyperlinktype.setter
    def hyperlinktype(self, value):
        """Alias for HyperlinkType.setter"""
        self.HyperlinkType = value

    @property
    def hyperlink_type(self):
        """Alias for HyperlinkType"""
        return self.HyperlinkType

    @hyperlink_type.setter
    def hyperlink_type(self, value):
        """Alias for HyperlinkType.setter"""
        self.HyperlinkType = value

    @property
    def Id(self):
        return self.com_object.Id

    @property
    def id(self):
        """Alias for Id"""
        return self.Id

    @property
    def Index(self):
        return self.com_object.Index

    @property
    def index(self):
        """Alias for Index"""
        return self.Index

    @property
    def IsPriorityDropped(self):
        return self.com_object.IsPriorityDropped

    @property
    def isprioritydropped(self):
        """Alias for IsPriorityDropped"""
        return self.IsPriorityDropped

    @property
    def is_priority_dropped(self):
        """Alias for IsPriorityDropped"""
        return self.IsPriorityDropped

    @property
    def Left(self):
        return CommandBarButton(self.com_object.Left)

    @property
    def left(self):
        """Alias for Left"""
        return self.Left

    @property
    def Mask(self):
        return self.com_object.Mask

    @Mask.setter
    def Mask(self, value):
        self.com_object.Mask = value

    @property
    def mask(self):
        """Alias for Mask"""
        return self.Mask

    @mask.setter
    def mask(self, value):
        """Alias for Mask.setter"""
        self.Mask = value

    @property
    def OLEUsage(self):
        return self.com_object.OLEUsage

    @OLEUsage.setter
    def OLEUsage(self, value):
        self.com_object.OLEUsage = value

    @property
    def oleusage(self):
        """Alias for OLEUsage"""
        return self.OLEUsage

    @oleusage.setter
    def oleusage(self, value):
        """Alias for OLEUsage.setter"""
        self.OLEUsage = value

    @property
    def o_l_e_usage(self):
        """Alias for OLEUsage"""
        return self.OLEUsage

    @o_l_e_usage.setter
    def o_l_e_usage(self, value):
        """Alias for OLEUsage.setter"""
        self.OLEUsage = value

    @property
    def OnAction(self):
        return self.com_object.OnAction

    @OnAction.setter
    def OnAction(self, value):
        self.com_object.OnAction = value

    @property
    def onaction(self):
        """Alias for OnAction"""
        return self.OnAction

    @onaction.setter
    def onaction(self, value):
        """Alias for OnAction.setter"""
        self.OnAction = value

    @property
    def on_action(self):
        """Alias for OnAction"""
        return self.OnAction

    @on_action.setter
    def on_action(self, value):
        """Alias for OnAction.setter"""
        self.OnAction = value

    @property
    def Parameter(self):
        return self.com_object.Parameter

    @Parameter.setter
    def Parameter(self, value):
        self.com_object.Parameter = value

    @property
    def parameter(self):
        """Alias for Parameter"""
        return self.Parameter

    @parameter.setter
    def parameter(self, value):
        """Alias for Parameter.setter"""
        self.Parameter = value

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    @property
    def Picture(self):
        return self.com_object.Picture

    @Picture.setter
    def Picture(self, value):
        self.com_object.Picture = value

    @property
    def picture(self):
        """Alias for Picture"""
        return self.Picture

    @picture.setter
    def picture(self, value):
        """Alias for Picture.setter"""
        self.Picture = value

    @property
    def Priority(self):
        return self.com_object.Priority

    @Priority.setter
    def Priority(self, value):
        self.com_object.Priority = value

    @property
    def priority(self):
        """Alias for Priority"""
        return self.Priority

    @priority.setter
    def priority(self, value):
        """Alias for Priority.setter"""
        self.Priority = value

    @property
    def ShortcutText(self):
        return self.com_object.ShortcutText

    @ShortcutText.setter
    def ShortcutText(self, value):
        self.com_object.ShortcutText = value

    @property
    def shortcuttext(self):
        """Alias for ShortcutText"""
        return self.ShortcutText

    @shortcuttext.setter
    def shortcuttext(self, value):
        """Alias for ShortcutText.setter"""
        self.ShortcutText = value

    @property
    def shortcut_text(self):
        """Alias for ShortcutText"""
        return self.ShortcutText

    @shortcut_text.setter
    def shortcut_text(self, value):
        """Alias for ShortcutText.setter"""
        self.ShortcutText = value

    @property
    def State(self):
        return self.com_object.State

    @State.setter
    def State(self, value):
        self.com_object.State = value

    @property
    def state(self):
        """Alias for State"""
        return self.State

    @state.setter
    def state(self, value):
        """Alias for State.setter"""
        self.State = value

    @property
    def Style(self):
        return self.com_object.Style

    @Style.setter
    def Style(self, value):
        self.com_object.Style = value

    @property
    def style(self):
        """Alias for Style"""
        return self.Style

    @style.setter
    def style(self, value):
        """Alias for Style.setter"""
        self.Style = value

    @property
    def Tag(self):
        return self.com_object.Tag

    @Tag.setter
    def Tag(self, value):
        self.com_object.Tag = value

    @property
    def tag(self):
        """Alias for Tag"""
        return self.Tag

    @tag.setter
    def tag(self, value):
        """Alias for Tag.setter"""
        self.Tag = value

    @property
    def TooltipText(self):
        return self.com_object.TooltipText

    @TooltipText.setter
    def TooltipText(self, value):
        self.com_object.TooltipText = value

    @property
    def tooltiptext(self):
        """Alias for TooltipText"""
        return self.TooltipText

    @tooltiptext.setter
    def tooltiptext(self, value):
        """Alias for TooltipText.setter"""
        self.TooltipText = value

    @property
    def tooltip_text(self):
        """Alias for TooltipText"""
        return self.TooltipText

    @tooltip_text.setter
    def tooltip_text(self, value):
        """Alias for TooltipText.setter"""
        self.TooltipText = value

    @property
    def Top(self):
        return self.com_object.Top

    @property
    def top(self):
        """Alias for Top"""
        return self.Top

    @property
    def Type(self):
        return self.com_object.Type

    @property
    def type(self):
        """Alias for Type"""
        return self.Type

    @property
    def Visible(self):
        return self.com_object.Visible

    @Visible.setter
    def Visible(self, value):
        self.com_object.Visible = value

    @property
    def visible(self):
        """Alias for Visible"""
        return self.Visible

    @visible.setter
    def visible(self, value):
        """Alias for Visible.setter"""
        self.Visible = value

    @property
    def Width(self):
        return self.com_object.Width

    @Width.setter
    def Width(self, value):
        self.com_object.Width = value

    @property
    def width(self):
        """Alias for Width"""
        return self.Width

    @width.setter
    def width(self, value):
        """Alias for Width.setter"""
        self.Width = value

    def Copy(self, Bar=None, Before=None):
        arguments = com_arguments([unwrap(a) for a in [Bar, Before]])
        return CommandBarControl(self.com_object.Copy(*arguments))

    def copy(self, Bar=None, Before=None):
        """Alias for Copy"""
        arguments = [Bar, Before]
        return self.Copy(*arguments)

    def CopyFace(self):
        return self.com_object.CopyFace()

    def copyface(self):
        """Alias for CopyFace"""
        return self.CopyFace()

    def copy_face(self):
        """Alias for CopyFace"""
        return self.CopyFace()

    def Delete(self, Temporary=None):
        arguments = com_arguments([unwrap(a) for a in [Temporary]])
        return self.com_object.Delete(*arguments)

    def delete(self, Temporary=None):
        """Alias for Delete"""
        arguments = [Temporary]
        return self.Delete(*arguments)

    def Execute(self):
        return self.com_object.Execute()

    def execute(self):
        """Alias for Execute"""
        return self.Execute()

    def Move(self, Bar=None, Before=None):
        arguments = com_arguments([unwrap(a) for a in [Bar, Before]])
        return self.com_object.Move(*arguments)

    def move(self, Bar=None, Before=None):
        """Alias for Move"""
        arguments = [Bar, Before]
        return self.Move(*arguments)

    def PasteFace(self):
        return self.com_object.PasteFace()

    def pasteface(self):
        """Alias for PasteFace"""
        return self.PasteFace()

    def paste_face(self):
        """Alias for PasteFace"""
        return self.PasteFace()

    def Reset(self):
        return self.com_object.Reset()

    def reset(self):
        """Alias for Reset"""
        return self.Reset()

    def SetFocus(self):
        return self.com_object.SetFocus()

    def setfocus(self):
        """Alias for SetFocus"""
        return self.SetFocus()

    def set_focus(self):
        """Alias for SetFocus"""
        return self.SetFocus()


class CommandBarComboBox:

    def __init__(self, commandbarcombobox=None):
        self.com_object= commandbarcombobox

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def BeginGroup(self):
        return self.com_object.BeginGroup

    @BeginGroup.setter
    def BeginGroup(self, value):
        self.com_object.BeginGroup = value

    @property
    def begingroup(self):
        """Alias for BeginGroup"""
        return self.BeginGroup

    @begingroup.setter
    def begingroup(self, value):
        """Alias for BeginGroup.setter"""
        self.BeginGroup = value

    @property
    def begin_group(self):
        """Alias for BeginGroup"""
        return self.BeginGroup

    @begin_group.setter
    def begin_group(self, value):
        """Alias for BeginGroup.setter"""
        self.BeginGroup = value

    @property
    def BuiltIn(self):
        return self.com_object.BuiltIn

    @property
    def builtin(self):
        """Alias for BuiltIn"""
        return self.BuiltIn

    @property
    def built_in(self):
        """Alias for BuiltIn"""
        return self.BuiltIn

    @property
    def Caption(self):
        return self.com_object.Caption

    @Caption.setter
    def Caption(self, value):
        self.com_object.Caption = value

    @property
    def caption(self):
        """Alias for Caption"""
        return self.Caption

    @caption.setter
    def caption(self, value):
        """Alias for Caption.setter"""
        self.Caption = value

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def DescriptionText(self):
        return self.com_object.DescriptionText

    @DescriptionText.setter
    def DescriptionText(self, value):
        self.com_object.DescriptionText = value

    @property
    def descriptiontext(self):
        """Alias for DescriptionText"""
        return self.DescriptionText

    @descriptiontext.setter
    def descriptiontext(self, value):
        """Alias for DescriptionText.setter"""
        self.DescriptionText = value

    @property
    def description_text(self):
        """Alias for DescriptionText"""
        return self.DescriptionText

    @description_text.setter
    def description_text(self, value):
        """Alias for DescriptionText.setter"""
        self.DescriptionText = value

    @property
    def DropDownLines(self):
        return self.com_object.DropDownLines

    @DropDownLines.setter
    def DropDownLines(self, value):
        self.com_object.DropDownLines = value

    @property
    def dropdownlines(self):
        """Alias for DropDownLines"""
        return self.DropDownLines

    @dropdownlines.setter
    def dropdownlines(self, value):
        """Alias for DropDownLines.setter"""
        self.DropDownLines = value

    @property
    def drop_down_lines(self):
        """Alias for DropDownLines"""
        return self.DropDownLines

    @drop_down_lines.setter
    def drop_down_lines(self, value):
        """Alias for DropDownLines.setter"""
        self.DropDownLines = value

    @property
    def DropDownWidth(self):
        return self.com_object.DropDownWidth

    @DropDownWidth.setter
    def DropDownWidth(self, value):
        self.com_object.DropDownWidth = value

    @property
    def dropdownwidth(self):
        """Alias for DropDownWidth"""
        return self.DropDownWidth

    @dropdownwidth.setter
    def dropdownwidth(self, value):
        """Alias for DropDownWidth.setter"""
        self.DropDownWidth = value

    @property
    def drop_down_width(self):
        """Alias for DropDownWidth"""
        return self.DropDownWidth

    @drop_down_width.setter
    def drop_down_width(self, value):
        """Alias for DropDownWidth.setter"""
        self.DropDownWidth = value

    @property
    def Enabled(self):
        return self.com_object.Enabled

    @Enabled.setter
    def Enabled(self, value):
        self.com_object.Enabled = value

    @property
    def enabled(self):
        """Alias for Enabled"""
        return self.Enabled

    @enabled.setter
    def enabled(self, value):
        """Alias for Enabled.setter"""
        self.Enabled = value

    @property
    def Height(self):
        return self.com_object.Height

    @Height.setter
    def Height(self, value):
        self.com_object.Height = value

    @property
    def height(self):
        """Alias for Height"""
        return self.Height

    @height.setter
    def height(self, value):
        """Alias for Height.setter"""
        self.Height = value

    @property
    def HelpContextId(self):
        return self.com_object.HelpContextId

    @HelpContextId.setter
    def HelpContextId(self, value):
        self.com_object.HelpContextId = value

    @property
    def helpcontextid(self):
        """Alias for HelpContextId"""
        return self.HelpContextId

    @helpcontextid.setter
    def helpcontextid(self, value):
        """Alias for HelpContextId.setter"""
        self.HelpContextId = value

    @property
    def help_context_id(self):
        """Alias for HelpContextId"""
        return self.HelpContextId

    @help_context_id.setter
    def help_context_id(self, value):
        """Alias for HelpContextId.setter"""
        self.HelpContextId = value

    @property
    def HelpFile(self):
        return self.com_object.HelpFile

    @HelpFile.setter
    def HelpFile(self, value):
        self.com_object.HelpFile = value

    @property
    def helpfile(self):
        """Alias for HelpFile"""
        return self.HelpFile

    @helpfile.setter
    def helpfile(self, value):
        """Alias for HelpFile.setter"""
        self.HelpFile = value

    @property
    def help_file(self):
        """Alias for HelpFile"""
        return self.HelpFile

    @help_file.setter
    def help_file(self, value):
        """Alias for HelpFile.setter"""
        self.HelpFile = value

    @property
    def Id(self):
        return self.com_object.Id

    @property
    def id(self):
        """Alias for Id"""
        return self.Id

    @property
    def Index(self):
        return self.com_object.Index

    @property
    def index(self):
        """Alias for Index"""
        return self.Index

    @property
    def IsPriorityDropped(self):
        return self.com_object.IsPriorityDropped

    @property
    def isprioritydropped(self):
        """Alias for IsPriorityDropped"""
        return self.IsPriorityDropped

    @property
    def is_priority_dropped(self):
        """Alias for IsPriorityDropped"""
        return self.IsPriorityDropped

    @property
    def Left(self):
        return CommandBarComboBox(self.com_object.Left)

    @property
    def left(self):
        """Alias for Left"""
        return self.Left

    @property
    def List(self):
        return self.com_object.List

    @List.setter
    def List(self, value):
        self.com_object.List = value

    @property
    def list(self):
        """Alias for List"""
        return self.List

    @list.setter
    def list(self, value):
        """Alias for List.setter"""
        self.List = value

    @property
    def ListCount(self):
        return self.com_object.ListCount

    @property
    def listcount(self):
        """Alias for ListCount"""
        return self.ListCount

    @property
    def list_count(self):
        """Alias for ListCount"""
        return self.ListCount

    @property
    def ListHeaderCount(self):
        return self.com_object.ListHeaderCount

    @ListHeaderCount.setter
    def ListHeaderCount(self, value):
        self.com_object.ListHeaderCount = value

    @property
    def listheadercount(self):
        """Alias for ListHeaderCount"""
        return self.ListHeaderCount

    @listheadercount.setter
    def listheadercount(self, value):
        """Alias for ListHeaderCount.setter"""
        self.ListHeaderCount = value

    @property
    def list_header_count(self):
        """Alias for ListHeaderCount"""
        return self.ListHeaderCount

    @list_header_count.setter
    def list_header_count(self, value):
        """Alias for ListHeaderCount.setter"""
        self.ListHeaderCount = value

    @property
    def ListIndex(self):
        return self.com_object.ListIndex

    @ListIndex.setter
    def ListIndex(self, value):
        self.com_object.ListIndex = value

    @property
    def listindex(self):
        """Alias for ListIndex"""
        return self.ListIndex

    @listindex.setter
    def listindex(self, value):
        """Alias for ListIndex.setter"""
        self.ListIndex = value

    @property
    def list_index(self):
        """Alias for ListIndex"""
        return self.ListIndex

    @list_index.setter
    def list_index(self, value):
        """Alias for ListIndex.setter"""
        self.ListIndex = value

    @property
    def OLEUsage(self):
        return self.com_object.OLEUsage

    @OLEUsage.setter
    def OLEUsage(self, value):
        self.com_object.OLEUsage = value

    @property
    def oleusage(self):
        """Alias for OLEUsage"""
        return self.OLEUsage

    @oleusage.setter
    def oleusage(self, value):
        """Alias for OLEUsage.setter"""
        self.OLEUsage = value

    @property
    def o_l_e_usage(self):
        """Alias for OLEUsage"""
        return self.OLEUsage

    @o_l_e_usage.setter
    def o_l_e_usage(self, value):
        """Alias for OLEUsage.setter"""
        self.OLEUsage = value

    @property
    def OnAction(self):
        return self.com_object.OnAction

    @OnAction.setter
    def OnAction(self, value):
        self.com_object.OnAction = value

    @property
    def onaction(self):
        """Alias for OnAction"""
        return self.OnAction

    @onaction.setter
    def onaction(self, value):
        """Alias for OnAction.setter"""
        self.OnAction = value

    @property
    def on_action(self):
        """Alias for OnAction"""
        return self.OnAction

    @on_action.setter
    def on_action(self, value):
        """Alias for OnAction.setter"""
        self.OnAction = value

    @property
    def Parameter(self):
        return self.com_object.Parameter

    @Parameter.setter
    def Parameter(self, value):
        self.com_object.Parameter = value

    @property
    def parameter(self):
        """Alias for Parameter"""
        return self.Parameter

    @parameter.setter
    def parameter(self, value):
        """Alias for Parameter.setter"""
        self.Parameter = value

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    @property
    def Priority(self):
        return self.com_object.Priority

    @Priority.setter
    def Priority(self, value):
        self.com_object.Priority = value

    @property
    def priority(self):
        """Alias for Priority"""
        return self.Priority

    @priority.setter
    def priority(self, value):
        """Alias for Priority.setter"""
        self.Priority = value

    @property
    def Style(self):
        return self.com_object.Style

    @Style.setter
    def Style(self, value):
        self.com_object.Style = value

    @property
    def style(self):
        """Alias for Style"""
        return self.Style

    @style.setter
    def style(self, value):
        """Alias for Style.setter"""
        self.Style = value

    @property
    def Tag(self):
        return self.com_object.Tag

    @Tag.setter
    def Tag(self, value):
        self.com_object.Tag = value

    @property
    def tag(self):
        """Alias for Tag"""
        return self.Tag

    @tag.setter
    def tag(self, value):
        """Alias for Tag.setter"""
        self.Tag = value

    @property
    def Text(self):
        return self.com_object.Text

    @Text.setter
    def Text(self, value):
        self.com_object.Text = value

    @property
    def text(self):
        """Alias for Text"""
        return self.Text

    @text.setter
    def text(self, value):
        """Alias for Text.setter"""
        self.Text = value

    @property
    def TooltipText(self):
        return self.com_object.TooltipText

    @TooltipText.setter
    def TooltipText(self, value):
        self.com_object.TooltipText = value

    @property
    def tooltiptext(self):
        """Alias for TooltipText"""
        return self.TooltipText

    @tooltiptext.setter
    def tooltiptext(self, value):
        """Alias for TooltipText.setter"""
        self.TooltipText = value

    @property
    def tooltip_text(self):
        """Alias for TooltipText"""
        return self.TooltipText

    @tooltip_text.setter
    def tooltip_text(self, value):
        """Alias for TooltipText.setter"""
        self.TooltipText = value

    @property
    def Top(self):
        return self.com_object.Top

    @property
    def top(self):
        """Alias for Top"""
        return self.Top

    @property
    def Type(self):
        return self.com_object.Type

    @property
    def type(self):
        """Alias for Type"""
        return self.Type

    @property
    def Visible(self):
        return self.com_object.Visible

    @Visible.setter
    def Visible(self, value):
        self.com_object.Visible = value

    @property
    def visible(self):
        """Alias for Visible"""
        return self.Visible

    @visible.setter
    def visible(self, value):
        """Alias for Visible.setter"""
        self.Visible = value

    @property
    def Width(self):
        return self.com_object.Width

    @Width.setter
    def Width(self, value):
        self.com_object.Width = value

    @property
    def width(self):
        """Alias for Width"""
        return self.Width

    @width.setter
    def width(self, value):
        """Alias for Width.setter"""
        self.Width = value

    def AddItem(self, Text=None, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Text, Index]])
        return self.com_object.AddItem(*arguments)

    def additem(self, Text=None, Index=None):
        """Alias for AddItem"""
        arguments = [Text, Index]
        return self.AddItem(*arguments)

    def add_item(self, Text=None, Index=None):
        """Alias for AddItem"""
        arguments = [Text, Index]
        return self.AddItem(*arguments)

    def Clear(self):
        return self.com_object.Clear()

    def clear(self):
        """Alias for Clear"""
        return self.Clear()

    def Copy(self, Bar=None, Before=None):
        arguments = com_arguments([unwrap(a) for a in [Bar, Before]])
        return CommandBarControl(self.com_object.Copy(*arguments))

    def copy(self, Bar=None, Before=None):
        """Alias for Copy"""
        arguments = [Bar, Before]
        return self.Copy(*arguments)

    def Delete(self, Temporary=None):
        arguments = com_arguments([unwrap(a) for a in [Temporary]])
        return self.com_object.Delete(*arguments)

    def delete(self, Temporary=None):
        """Alias for Delete"""
        arguments = [Temporary]
        return self.Delete(*arguments)

    def Execute(self):
        return self.com_object.Execute()

    def execute(self):
        """Alias for Execute"""
        return self.Execute()

    def Move(self, Bar=None, Before=None):
        arguments = com_arguments([unwrap(a) for a in [Bar, Before]])
        return self.com_object.Move(*arguments)

    def move(self, Bar=None, Before=None):
        """Alias for Move"""
        arguments = [Bar, Before]
        return self.Move(*arguments)

    def RemoveItem(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        return self.com_object.RemoveItem(*arguments)

    def removeitem(self, Index=None):
        """Alias for RemoveItem"""
        arguments = [Index]
        return self.RemoveItem(*arguments)

    def remove_item(self, Index=None):
        """Alias for RemoveItem"""
        arguments = [Index]
        return self.RemoveItem(*arguments)

    def Reset(self):
        return self.com_object.Reset()

    def reset(self):
        """Alias for Reset"""
        return self.Reset()

    def SetFocus(self):
        return self.com_object.SetFocus()

    def setfocus(self):
        """Alias for SetFocus"""
        return self.SetFocus()

    def set_focus(self):
        """Alias for SetFocus"""
        return self.SetFocus()


class CommandBarControl:

    def __init__(self, commandbarcontrol=None):
        self.com_object= commandbarcontrol

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def BeginGroup(self):
        return self.com_object.BeginGroup

    @BeginGroup.setter
    def BeginGroup(self, value):
        self.com_object.BeginGroup = value

    @property
    def begingroup(self):
        """Alias for BeginGroup"""
        return self.BeginGroup

    @begingroup.setter
    def begingroup(self, value):
        """Alias for BeginGroup.setter"""
        self.BeginGroup = value

    @property
    def begin_group(self):
        """Alias for BeginGroup"""
        return self.BeginGroup

    @begin_group.setter
    def begin_group(self, value):
        """Alias for BeginGroup.setter"""
        self.BeginGroup = value

    @property
    def BuiltIn(self):
        return self.com_object.BuiltIn

    @property
    def builtin(self):
        """Alias for BuiltIn"""
        return self.BuiltIn

    @property
    def built_in(self):
        """Alias for BuiltIn"""
        return self.BuiltIn

    @property
    def Caption(self):
        return self.com_object.Caption

    @Caption.setter
    def Caption(self, value):
        self.com_object.Caption = value

    @property
    def caption(self):
        """Alias for Caption"""
        return self.Caption

    @caption.setter
    def caption(self, value):
        """Alias for Caption.setter"""
        self.Caption = value

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def DescriptionText(self):
        return self.com_object.DescriptionText

    @DescriptionText.setter
    def DescriptionText(self, value):
        self.com_object.DescriptionText = value

    @property
    def descriptiontext(self):
        """Alias for DescriptionText"""
        return self.DescriptionText

    @descriptiontext.setter
    def descriptiontext(self, value):
        """Alias for DescriptionText.setter"""
        self.DescriptionText = value

    @property
    def description_text(self):
        """Alias for DescriptionText"""
        return self.DescriptionText

    @description_text.setter
    def description_text(self, value):
        """Alias for DescriptionText.setter"""
        self.DescriptionText = value

    @property
    def Enabled(self):
        return self.com_object.Enabled

    @Enabled.setter
    def Enabled(self, value):
        self.com_object.Enabled = value

    @property
    def enabled(self):
        """Alias for Enabled"""
        return self.Enabled

    @enabled.setter
    def enabled(self, value):
        """Alias for Enabled.setter"""
        self.Enabled = value

    @property
    def Height(self):
        return self.com_object.Height

    @Height.setter
    def Height(self, value):
        self.com_object.Height = value

    @property
    def height(self):
        """Alias for Height"""
        return self.Height

    @height.setter
    def height(self, value):
        """Alias for Height.setter"""
        self.Height = value

    @property
    def HelpContextId(self):
        return self.com_object.HelpContextId

    @HelpContextId.setter
    def HelpContextId(self, value):
        self.com_object.HelpContextId = value

    @property
    def helpcontextid(self):
        """Alias for HelpContextId"""
        return self.HelpContextId

    @helpcontextid.setter
    def helpcontextid(self, value):
        """Alias for HelpContextId.setter"""
        self.HelpContextId = value

    @property
    def help_context_id(self):
        """Alias for HelpContextId"""
        return self.HelpContextId

    @help_context_id.setter
    def help_context_id(self, value):
        """Alias for HelpContextId.setter"""
        self.HelpContextId = value

    @property
    def HelpFile(self):
        return self.com_object.HelpFile

    @HelpFile.setter
    def HelpFile(self, value):
        self.com_object.HelpFile = value

    @property
    def helpfile(self):
        """Alias for HelpFile"""
        return self.HelpFile

    @helpfile.setter
    def helpfile(self, value):
        """Alias for HelpFile.setter"""
        self.HelpFile = value

    @property
    def help_file(self):
        """Alias for HelpFile"""
        return self.HelpFile

    @help_file.setter
    def help_file(self, value):
        """Alias for HelpFile.setter"""
        self.HelpFile = value

    @property
    def Id(self):
        return self.com_object.Id

    @property
    def id(self):
        """Alias for Id"""
        return self.Id

    @property
    def Index(self):
        return self.com_object.Index

    @property
    def index(self):
        """Alias for Index"""
        return self.Index

    @property
    def IsPriorityDropped(self):
        return self.com_object.IsPriorityDropped

    @property
    def isprioritydropped(self):
        """Alias for IsPriorityDropped"""
        return self.IsPriorityDropped

    @property
    def is_priority_dropped(self):
        """Alias for IsPriorityDropped"""
        return self.IsPriorityDropped

    @property
    def Left(self):
        return CommandBarControl(self.com_object.Left)

    @property
    def left(self):
        """Alias for Left"""
        return self.Left

    @property
    def OLEUsage(self):
        return self.com_object.OLEUsage

    @OLEUsage.setter
    def OLEUsage(self, value):
        self.com_object.OLEUsage = value

    @property
    def oleusage(self):
        """Alias for OLEUsage"""
        return self.OLEUsage

    @oleusage.setter
    def oleusage(self, value):
        """Alias for OLEUsage.setter"""
        self.OLEUsage = value

    @property
    def o_l_e_usage(self):
        """Alias for OLEUsage"""
        return self.OLEUsage

    @o_l_e_usage.setter
    def o_l_e_usage(self, value):
        """Alias for OLEUsage.setter"""
        self.OLEUsage = value

    @property
    def OnAction(self):
        return self.com_object.OnAction

    @OnAction.setter
    def OnAction(self, value):
        self.com_object.OnAction = value

    @property
    def onaction(self):
        """Alias for OnAction"""
        return self.OnAction

    @onaction.setter
    def onaction(self, value):
        """Alias for OnAction.setter"""
        self.OnAction = value

    @property
    def on_action(self):
        """Alias for OnAction"""
        return self.OnAction

    @on_action.setter
    def on_action(self, value):
        """Alias for OnAction.setter"""
        self.OnAction = value

    @property
    def Parameter(self):
        return self.com_object.Parameter

    @Parameter.setter
    def Parameter(self, value):
        self.com_object.Parameter = value

    @property
    def parameter(self):
        """Alias for Parameter"""
        return self.Parameter

    @parameter.setter
    def parameter(self, value):
        """Alias for Parameter.setter"""
        self.Parameter = value

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    @property
    def Priority(self):
        return self.com_object.Priority

    @Priority.setter
    def Priority(self, value):
        self.com_object.Priority = value

    @property
    def priority(self):
        """Alias for Priority"""
        return self.Priority

    @priority.setter
    def priority(self, value):
        """Alias for Priority.setter"""
        self.Priority = value

    @property
    def Tag(self):
        return self.com_object.Tag

    @Tag.setter
    def Tag(self, value):
        self.com_object.Tag = value

    @property
    def tag(self):
        """Alias for Tag"""
        return self.Tag

    @tag.setter
    def tag(self, value):
        """Alias for Tag.setter"""
        self.Tag = value

    @property
    def TooltipText(self):
        return self.com_object.TooltipText

    @TooltipText.setter
    def TooltipText(self, value):
        self.com_object.TooltipText = value

    @property
    def tooltiptext(self):
        """Alias for TooltipText"""
        return self.TooltipText

    @tooltiptext.setter
    def tooltiptext(self, value):
        """Alias for TooltipText.setter"""
        self.TooltipText = value

    @property
    def tooltip_text(self):
        """Alias for TooltipText"""
        return self.TooltipText

    @tooltip_text.setter
    def tooltip_text(self, value):
        """Alias for TooltipText.setter"""
        self.TooltipText = value

    @property
    def Top(self):
        return self.com_object.Top

    @property
    def top(self):
        """Alias for Top"""
        return self.Top

    @property
    def Type(self):
        return self.com_object.Type

    @property
    def type(self):
        """Alias for Type"""
        return self.Type

    @property
    def Visible(self):
        return self.com_object.Visible

    @Visible.setter
    def Visible(self, value):
        self.com_object.Visible = value

    @property
    def visible(self):
        """Alias for Visible"""
        return self.Visible

    @visible.setter
    def visible(self, value):
        """Alias for Visible.setter"""
        self.Visible = value

    @property
    def Width(self):
        return self.com_object.Width

    @Width.setter
    def Width(self, value):
        self.com_object.Width = value

    @property
    def width(self):
        """Alias for Width"""
        return self.Width

    @width.setter
    def width(self, value):
        """Alias for Width.setter"""
        self.Width = value

    def Copy(self, Bar=None, Before=None):
        arguments = com_arguments([unwrap(a) for a in [Bar, Before]])
        return CommandBarControl(self.com_object.Copy(*arguments))

    def copy(self, Bar=None, Before=None):
        """Alias for Copy"""
        arguments = [Bar, Before]
        return self.Copy(*arguments)

    def Delete(self, Temporary=None):
        arguments = com_arguments([unwrap(a) for a in [Temporary]])
        return self.com_object.Delete(*arguments)

    def delete(self, Temporary=None):
        """Alias for Delete"""
        arguments = [Temporary]
        return self.Delete(*arguments)

    def Execute(self):
        return self.com_object.Execute()

    def execute(self):
        """Alias for Execute"""
        return self.Execute()

    def Move(self, Bar=None, Before=None):
        arguments = com_arguments([unwrap(a) for a in [Bar, Before]])
        return self.com_object.Move(*arguments)

    def move(self, Bar=None, Before=None):
        """Alias for Move"""
        arguments = [Bar, Before]
        return self.Move(*arguments)

    def Reset(self):
        return self.com_object.Reset()

    def reset(self):
        """Alias for Reset"""
        return self.Reset()

    def SetFocus(self):
        return self.com_object.SetFocus()

    def setfocus(self):
        """Alias for SetFocus"""
        return self.SetFocus()

    def set_focus(self):
        """Alias for SetFocus"""
        return self.SetFocus()


class CommandBarControls:

    def __init__(self, commandbarcontrols=None):
        self.com_object= commandbarcontrols

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        if hasattr(self.com_object, "GetItem"):
            return self.com_object.GetItem(*arguments)
        else:
            return self.com_object.Item(*arguments)

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    def Add(self, Type=None, Id=None, Parameter=None, Before=None, Temporary=None):
        arguments = com_arguments([unwrap(a) for a in [Type, Id, Parameter, Before, Temporary]])
        return self.com_object.Add(*arguments)

    def add(self, Type=None, Id=None, Parameter=None, Before=None, Temporary=None):
        """Alias for Add"""
        arguments = [Type, Id, Parameter, Before, Temporary]
        return self.Add(*arguments)


class CommandBarPopup:

    def __init__(self, commandbarpopup=None):
        self.com_object= commandbarpopup

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def BeginGroup(self):
        return self.com_object.BeginGroup

    @BeginGroup.setter
    def BeginGroup(self, value):
        self.com_object.BeginGroup = value

    @property
    def begingroup(self):
        """Alias for BeginGroup"""
        return self.BeginGroup

    @begingroup.setter
    def begingroup(self, value):
        """Alias for BeginGroup.setter"""
        self.BeginGroup = value

    @property
    def begin_group(self):
        """Alias for BeginGroup"""
        return self.BeginGroup

    @begin_group.setter
    def begin_group(self, value):
        """Alias for BeginGroup.setter"""
        self.BeginGroup = value

    @property
    def BuiltIn(self):
        return self.com_object.BuiltIn

    @property
    def builtin(self):
        """Alias for BuiltIn"""
        return self.BuiltIn

    @property
    def built_in(self):
        """Alias for BuiltIn"""
        return self.BuiltIn

    @property
    def Caption(self):
        return self.com_object.Caption

    @Caption.setter
    def Caption(self, value):
        self.com_object.Caption = value

    @property
    def caption(self):
        """Alias for Caption"""
        return self.Caption

    @caption.setter
    def caption(self, value):
        """Alias for Caption.setter"""
        self.Caption = value

    @property
    def CommandBar(self):
        return self.com_object.CommandBar

    @property
    def commandbar(self):
        """Alias for CommandBar"""
        return self.CommandBar

    @property
    def command_bar(self):
        """Alias for CommandBar"""
        return self.CommandBar

    @property
    def Controls(self):
        return self.com_object.Controls

    @property
    def controls(self):
        """Alias for Controls"""
        return self.Controls

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def DescriptionText(self):
        return self.com_object.DescriptionText

    @DescriptionText.setter
    def DescriptionText(self, value):
        self.com_object.DescriptionText = value

    @property
    def descriptiontext(self):
        """Alias for DescriptionText"""
        return self.DescriptionText

    @descriptiontext.setter
    def descriptiontext(self, value):
        """Alias for DescriptionText.setter"""
        self.DescriptionText = value

    @property
    def description_text(self):
        """Alias for DescriptionText"""
        return self.DescriptionText

    @description_text.setter
    def description_text(self, value):
        """Alias for DescriptionText.setter"""
        self.DescriptionText = value

    @property
    def Enabled(self):
        return self.com_object.Enabled

    @Enabled.setter
    def Enabled(self, value):
        self.com_object.Enabled = value

    @property
    def enabled(self):
        """Alias for Enabled"""
        return self.Enabled

    @enabled.setter
    def enabled(self, value):
        """Alias for Enabled.setter"""
        self.Enabled = value

    @property
    def Height(self):
        return self.com_object.Height

    @Height.setter
    def Height(self, value):
        self.com_object.Height = value

    @property
    def height(self):
        """Alias for Height"""
        return self.Height

    @height.setter
    def height(self, value):
        """Alias for Height.setter"""
        self.Height = value

    @property
    def HelpContextId(self):
        return self.com_object.HelpContextId

    @HelpContextId.setter
    def HelpContextId(self, value):
        self.com_object.HelpContextId = value

    @property
    def helpcontextid(self):
        """Alias for HelpContextId"""
        return self.HelpContextId

    @helpcontextid.setter
    def helpcontextid(self, value):
        """Alias for HelpContextId.setter"""
        self.HelpContextId = value

    @property
    def help_context_id(self):
        """Alias for HelpContextId"""
        return self.HelpContextId

    @help_context_id.setter
    def help_context_id(self, value):
        """Alias for HelpContextId.setter"""
        self.HelpContextId = value

    @property
    def HelpFile(self):
        return self.com_object.HelpFile

    @HelpFile.setter
    def HelpFile(self, value):
        self.com_object.HelpFile = value

    @property
    def helpfile(self):
        """Alias for HelpFile"""
        return self.HelpFile

    @helpfile.setter
    def helpfile(self, value):
        """Alias for HelpFile.setter"""
        self.HelpFile = value

    @property
    def help_file(self):
        """Alias for HelpFile"""
        return self.HelpFile

    @help_file.setter
    def help_file(self, value):
        """Alias for HelpFile.setter"""
        self.HelpFile = value

    @property
    def Id(self):
        return self.com_object.Id

    @property
    def id(self):
        """Alias for Id"""
        return self.Id

    @property
    def Index(self):
        return self.com_object.Index

    @property
    def index(self):
        """Alias for Index"""
        return self.Index

    @property
    def IsPriorityDropped(self):
        return self.com_object.IsPriorityDropped

    @property
    def isprioritydropped(self):
        """Alias for IsPriorityDropped"""
        return self.IsPriorityDropped

    @property
    def is_priority_dropped(self):
        """Alias for IsPriorityDropped"""
        return self.IsPriorityDropped

    @property
    def Left(self):
        return CommandBarPopup(self.com_object.Left)

    @property
    def left(self):
        """Alias for Left"""
        return self.Left

    @property
    def OLEMenuGroup(self):
        return self.com_object.OLEMenuGroup

    @OLEMenuGroup.setter
    def OLEMenuGroup(self, value):
        self.com_object.OLEMenuGroup = value

    @property
    def olemenugroup(self):
        """Alias for OLEMenuGroup"""
        return self.OLEMenuGroup

    @olemenugroup.setter
    def olemenugroup(self, value):
        """Alias for OLEMenuGroup.setter"""
        self.OLEMenuGroup = value

    @property
    def o_l_e_menu_group(self):
        """Alias for OLEMenuGroup"""
        return self.OLEMenuGroup

    @o_l_e_menu_group.setter
    def o_l_e_menu_group(self, value):
        """Alias for OLEMenuGroup.setter"""
        self.OLEMenuGroup = value

    @property
    def OLEUsage(self):
        return self.com_object.OLEUsage

    @OLEUsage.setter
    def OLEUsage(self, value):
        self.com_object.OLEUsage = value

    @property
    def oleusage(self):
        """Alias for OLEUsage"""
        return self.OLEUsage

    @oleusage.setter
    def oleusage(self, value):
        """Alias for OLEUsage.setter"""
        self.OLEUsage = value

    @property
    def o_l_e_usage(self):
        """Alias for OLEUsage"""
        return self.OLEUsage

    @o_l_e_usage.setter
    def o_l_e_usage(self, value):
        """Alias for OLEUsage.setter"""
        self.OLEUsage = value

    @property
    def OnAction(self):
        return self.com_object.OnAction

    @OnAction.setter
    def OnAction(self, value):
        self.com_object.OnAction = value

    @property
    def onaction(self):
        """Alias for OnAction"""
        return self.OnAction

    @onaction.setter
    def onaction(self, value):
        """Alias for OnAction.setter"""
        self.OnAction = value

    @property
    def on_action(self):
        """Alias for OnAction"""
        return self.OnAction

    @on_action.setter
    def on_action(self, value):
        """Alias for OnAction.setter"""
        self.OnAction = value

    @property
    def Parameter(self):
        return self.com_object.Parameter

    @Parameter.setter
    def Parameter(self, value):
        self.com_object.Parameter = value

    @property
    def parameter(self):
        """Alias for Parameter"""
        return self.Parameter

    @parameter.setter
    def parameter(self, value):
        """Alias for Parameter.setter"""
        self.Parameter = value

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    @property
    def Priority(self):
        return self.com_object.Priority

    @Priority.setter
    def Priority(self, value):
        self.com_object.Priority = value

    @property
    def priority(self):
        """Alias for Priority"""
        return self.Priority

    @priority.setter
    def priority(self, value):
        """Alias for Priority.setter"""
        self.Priority = value

    @property
    def Tag(self):
        return self.com_object.Tag

    @Tag.setter
    def Tag(self, value):
        self.com_object.Tag = value

    @property
    def tag(self):
        """Alias for Tag"""
        return self.Tag

    @tag.setter
    def tag(self, value):
        """Alias for Tag.setter"""
        self.Tag = value

    @property
    def TooltipText(self):
        return self.com_object.TooltipText

    @TooltipText.setter
    def TooltipText(self, value):
        self.com_object.TooltipText = value

    @property
    def tooltiptext(self):
        """Alias for TooltipText"""
        return self.TooltipText

    @tooltiptext.setter
    def tooltiptext(self, value):
        """Alias for TooltipText.setter"""
        self.TooltipText = value

    @property
    def tooltip_text(self):
        """Alias for TooltipText"""
        return self.TooltipText

    @tooltip_text.setter
    def tooltip_text(self, value):
        """Alias for TooltipText.setter"""
        self.TooltipText = value

    @property
    def Top(self):
        return self.com_object.Top

    @property
    def top(self):
        """Alias for Top"""
        return self.Top

    @property
    def Type(self):
        return self.com_object.Type

    @property
    def type(self):
        """Alias for Type"""
        return self.Type

    @property
    def Visible(self):
        return self.com_object.Visible

    @Visible.setter
    def Visible(self, value):
        self.com_object.Visible = value

    @property
    def visible(self):
        """Alias for Visible"""
        return self.Visible

    @visible.setter
    def visible(self, value):
        """Alias for Visible.setter"""
        self.Visible = value

    @property
    def Width(self):
        return self.com_object.Width

    @Width.setter
    def Width(self, value):
        self.com_object.Width = value

    @property
    def width(self):
        """Alias for Width"""
        return self.Width

    @width.setter
    def width(self, value):
        """Alias for Width.setter"""
        self.Width = value

    def Copy(self, Bar=None, Before=None):
        arguments = com_arguments([unwrap(a) for a in [Bar, Before]])
        return CommandBarControl(self.com_object.Copy(*arguments))

    def copy(self, Bar=None, Before=None):
        """Alias for Copy"""
        arguments = [Bar, Before]
        return self.Copy(*arguments)

    def Delete(self, Temporary=None):
        arguments = com_arguments([unwrap(a) for a in [Temporary]])
        return self.com_object.Delete(*arguments)

    def delete(self, Temporary=None):
        """Alias for Delete"""
        arguments = [Temporary]
        return self.Delete(*arguments)

    def Execute(self):
        return self.com_object.Execute()

    def execute(self):
        """Alias for Execute"""
        return self.Execute()

    def Move(self, Bar=None, Before=None):
        arguments = com_arguments([unwrap(a) for a in [Bar, Before]])
        return self.com_object.Move(*arguments)

    def move(self, Bar=None, Before=None):
        """Alias for Move"""
        arguments = [Bar, Before]
        return self.Move(*arguments)

    def Reset(self):
        return self.com_object.Reset()

    def reset(self):
        """Alias for Reset"""
        return self.Reset()

    def SetFocus(self):
        return self.com_object.SetFocus()

    def setfocus(self):
        """Alias for SetFocus"""
        return self.SetFocus()

    def set_focus(self):
        """Alias for SetFocus"""
        return self.SetFocus()


class CommandBars:

    def __init__(self, commandbars=None):
        self.com_object= commandbars

    @property
    def ActionControl(self):
        return self.com_object.ActionControl

    @property
    def actioncontrol(self):
        """Alias for ActionControl"""
        return self.ActionControl

    @property
    def action_control(self):
        """Alias for ActionControl"""
        return self.ActionControl

    @property
    def ActiveMenuBar(self):
        return self.com_object.ActiveMenuBar

    @property
    def activemenubar(self):
        """Alias for ActiveMenuBar"""
        return self.ActiveMenuBar

    @property
    def active_menu_bar(self):
        """Alias for ActiveMenuBar"""
        return self.ActiveMenuBar

    @property
    def AdaptiveMenus(self):
        return self.com_object.AdaptiveMenus

    @AdaptiveMenus.setter
    def AdaptiveMenus(self, value):
        self.com_object.AdaptiveMenus = value

    @property
    def adaptivemenus(self):
        """Alias for AdaptiveMenus"""
        return self.AdaptiveMenus

    @adaptivemenus.setter
    def adaptivemenus(self, value):
        """Alias for AdaptiveMenus.setter"""
        self.AdaptiveMenus = value

    @property
    def adaptive_menus(self):
        """Alias for AdaptiveMenus"""
        return self.AdaptiveMenus

    @adaptive_menus.setter
    def adaptive_menus(self, value):
        """Alias for AdaptiveMenus.setter"""
        self.AdaptiveMenus = value

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def DisableAskAQuestionDropdown(self):
        return self.com_object.DisableAskAQuestionDropdown

    @DisableAskAQuestionDropdown.setter
    def DisableAskAQuestionDropdown(self, value):
        self.com_object.DisableAskAQuestionDropdown = value

    @property
    def disableaskaquestiondropdown(self):
        """Alias for DisableAskAQuestionDropdown"""
        return self.DisableAskAQuestionDropdown

    @disableaskaquestiondropdown.setter
    def disableaskaquestiondropdown(self, value):
        """Alias for DisableAskAQuestionDropdown.setter"""
        self.DisableAskAQuestionDropdown = value

    @property
    def disable_ask_a_question_dropdown(self):
        """Alias for DisableAskAQuestionDropdown"""
        return self.DisableAskAQuestionDropdown

    @disable_ask_a_question_dropdown.setter
    def disable_ask_a_question_dropdown(self, value):
        """Alias for DisableAskAQuestionDropdown.setter"""
        self.DisableAskAQuestionDropdown = value

    @property
    def DisableCustomize(self):
        return self.com_object.DisableCustomize

    @DisableCustomize.setter
    def DisableCustomize(self, value):
        self.com_object.DisableCustomize = value

    @property
    def disablecustomize(self):
        """Alias for DisableCustomize"""
        return self.DisableCustomize

    @disablecustomize.setter
    def disablecustomize(self, value):
        """Alias for DisableCustomize.setter"""
        self.DisableCustomize = value

    @property
    def disable_customize(self):
        """Alias for DisableCustomize"""
        return self.DisableCustomize

    @disable_customize.setter
    def disable_customize(self, value):
        """Alias for DisableCustomize.setter"""
        self.DisableCustomize = value

    @property
    def DisplayFonts(self):
        return self.com_object.DisplayFonts

    @DisplayFonts.setter
    def DisplayFonts(self, value):
        self.com_object.DisplayFonts = value

    @property
    def displayfonts(self):
        """Alias for DisplayFonts"""
        return self.DisplayFonts

    @displayfonts.setter
    def displayfonts(self, value):
        """Alias for DisplayFonts.setter"""
        self.DisplayFonts = value

    @property
    def display_fonts(self):
        """Alias for DisplayFonts"""
        return self.DisplayFonts

    @display_fonts.setter
    def display_fonts(self, value):
        """Alias for DisplayFonts.setter"""
        self.DisplayFonts = value

    @property
    def DisplayKeysInTooltips(self):
        return self.com_object.DisplayKeysInTooltips

    @DisplayKeysInTooltips.setter
    def DisplayKeysInTooltips(self, value):
        self.com_object.DisplayKeysInTooltips = value

    @property
    def displaykeysintooltips(self):
        """Alias for DisplayKeysInTooltips"""
        return self.DisplayKeysInTooltips

    @displaykeysintooltips.setter
    def displaykeysintooltips(self, value):
        """Alias for DisplayKeysInTooltips.setter"""
        self.DisplayKeysInTooltips = value

    @property
    def display_keys_in_tooltips(self):
        """Alias for DisplayKeysInTooltips"""
        return self.DisplayKeysInTooltips

    @display_keys_in_tooltips.setter
    def display_keys_in_tooltips(self, value):
        """Alias for DisplayKeysInTooltips.setter"""
        self.DisplayKeysInTooltips = value

    @property
    def DisplayTooltips(self):
        return self.com_object.DisplayTooltips

    @DisplayTooltips.setter
    def DisplayTooltips(self, value):
        self.com_object.DisplayTooltips = value

    @property
    def displaytooltips(self):
        """Alias for DisplayTooltips"""
        return self.DisplayTooltips

    @displaytooltips.setter
    def displaytooltips(self, value):
        """Alias for DisplayTooltips.setter"""
        self.DisplayTooltips = value

    @property
    def display_tooltips(self):
        """Alias for DisplayTooltips"""
        return self.DisplayTooltips

    @display_tooltips.setter
    def display_tooltips(self, value):
        """Alias for DisplayTooltips.setter"""
        self.DisplayTooltips = value

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        if hasattr(self.com_object, "GetItem"):
            return self.com_object.GetItem(*arguments)
        else:
            return self.com_object.Item(*arguments)

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)

    @property
    def LargeButtons(self):
        return self.com_object.LargeButtons

    @LargeButtons.setter
    def LargeButtons(self, value):
        self.com_object.LargeButtons = value

    @property
    def largebuttons(self):
        """Alias for LargeButtons"""
        return self.LargeButtons

    @largebuttons.setter
    def largebuttons(self, value):
        """Alias for LargeButtons.setter"""
        self.LargeButtons = value

    @property
    def large_buttons(self):
        """Alias for LargeButtons"""
        return self.LargeButtons

    @large_buttons.setter
    def large_buttons(self, value):
        """Alias for LargeButtons.setter"""
        self.LargeButtons = value

    @property
    def MenuAnimationStyle(self):
        return self.com_object.MenuAnimationStyle

    @MenuAnimationStyle.setter
    def MenuAnimationStyle(self, value):
        self.com_object.MenuAnimationStyle = value

    @property
    def menuanimationstyle(self):
        """Alias for MenuAnimationStyle"""
        return self.MenuAnimationStyle

    @menuanimationstyle.setter
    def menuanimationstyle(self, value):
        """Alias for MenuAnimationStyle.setter"""
        self.MenuAnimationStyle = value

    @property
    def menu_animation_style(self):
        """Alias for MenuAnimationStyle"""
        return self.MenuAnimationStyle

    @menu_animation_style.setter
    def menu_animation_style(self, value):
        """Alias for MenuAnimationStyle.setter"""
        self.MenuAnimationStyle = value

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    def Add(self, Name=None, Position=None, MenuBar=None, Temporary=None):
        arguments = com_arguments([unwrap(a) for a in [Name, Position, MenuBar, Temporary]])
        return self.com_object.Add(*arguments)

    def add(self, Name=None, Position=None, MenuBar=None, Temporary=None):
        """Alias for Add"""
        arguments = [Name, Position, MenuBar, Temporary]
        return self.Add(*arguments)

    def CommitRenderingTransaction(self, hwnd=None):
        arguments = com_arguments([unwrap(a) for a in [hwnd]])
        return self.com_object.CommitRenderingTransaction(*arguments)

    def commitrenderingtransaction(self, hwnd=None):
        """Alias for CommitRenderingTransaction"""
        arguments = [hwnd]
        return self.CommitRenderingTransaction(*arguments)

    def commit_rendering_transaction(self, hwnd=None):
        """Alias for CommitRenderingTransaction"""
        arguments = [hwnd]
        return self.CommitRenderingTransaction(*arguments)

    def ExecuteMso(self, idMso=None):
        arguments = com_arguments([unwrap(a) for a in [idMso]])
        return self.com_object.ExecuteMso(*arguments)

    def executemso(self, idMso=None):
        """Alias for ExecuteMso"""
        arguments = [idMso]
        return self.ExecuteMso(*arguments)

    def execute_mso(self, idMso=None):
        """Alias for ExecuteMso"""
        arguments = [idMso]
        return self.ExecuteMso(*arguments)

    def FindControl(self, Type=None, Id=None, Tag=None, Visible=None):
        arguments = com_arguments([unwrap(a) for a in [Type, Id, Tag, Visible]])
        return CommandBarControl(self.com_object.FindControl(*arguments))

    def findcontrol(self, Type=None, Id=None, Tag=None, Visible=None):
        """Alias for FindControl"""
        arguments = [Type, Id, Tag, Visible]
        return self.FindControl(*arguments)

    def find_control(self, Type=None, Id=None, Tag=None, Visible=None):
        """Alias for FindControl"""
        arguments = [Type, Id, Tag, Visible]
        return self.FindControl(*arguments)

    def FindControls(self, Type=None, Id=None, Tag=None, Visible=None):
        arguments = com_arguments([unwrap(a) for a in [Type, Id, Tag, Visible]])
        return CommandBarControls(self.com_object.FindControls(*arguments))

    def findcontrols(self, Type=None, Id=None, Tag=None, Visible=None):
        """Alias for FindControls"""
        arguments = [Type, Id, Tag, Visible]
        return self.FindControls(*arguments)

    def find_controls(self, Type=None, Id=None, Tag=None, Visible=None):
        """Alias for FindControls"""
        arguments = [Type, Id, Tag, Visible]
        return self.FindControls(*arguments)

    def GetEnabledMso(self, idMso=None):
        arguments = com_arguments([unwrap(a) for a in [idMso]])
        return self.com_object.GetEnabledMso(*arguments)

    def getenabledmso(self, idMso=None):
        """Alias for GetEnabledMso"""
        arguments = [idMso]
        return self.GetEnabledMso(*arguments)

    def get_enabled_mso(self, idMso=None):
        """Alias for GetEnabledMso"""
        arguments = [idMso]
        return self.GetEnabledMso(*arguments)

    def GetImageMso(self, idMso=None, Width=None, Height=None):
        arguments = com_arguments([unwrap(a) for a in [idMso, Width, Height]])
        return self.com_object.GetImageMso(*arguments)

    def getimagemso(self, idMso=None, Width=None, Height=None):
        """Alias for GetImageMso"""
        arguments = [idMso, Width, Height]
        return self.GetImageMso(*arguments)

    def get_image_mso(self, idMso=None, Width=None, Height=None):
        """Alias for GetImageMso"""
        arguments = [idMso, Width, Height]
        return self.GetImageMso(*arguments)

    def GetLabelMso(self, idMso=None):
        arguments = com_arguments([unwrap(a) for a in [idMso]])
        return self.com_object.GetLabelMso(*arguments)

    def getlabelmso(self, idMso=None):
        """Alias for GetLabelMso"""
        arguments = [idMso]
        return self.GetLabelMso(*arguments)

    def get_label_mso(self, idMso=None):
        """Alias for GetLabelMso"""
        arguments = [idMso]
        return self.GetLabelMso(*arguments)

    def GetPressedMso(self, idMso=None):
        arguments = com_arguments([unwrap(a) for a in [idMso]])
        return self.com_object.GetPressedMso(*arguments)

    def getpressedmso(self, idMso=None):
        """Alias for GetPressedMso"""
        arguments = [idMso]
        return self.GetPressedMso(*arguments)

    def get_pressed_mso(self, idMso=None):
        """Alias for GetPressedMso"""
        arguments = [idMso]
        return self.GetPressedMso(*arguments)

    def GetScreentipMso(self, idMso=None):
        arguments = com_arguments([unwrap(a) for a in [idMso]])
        return self.com_object.GetScreentipMso(*arguments)

    def getscreentipmso(self, idMso=None):
        """Alias for GetScreentipMso"""
        arguments = [idMso]
        return self.GetScreentipMso(*arguments)

    def get_screentip_mso(self, idMso=None):
        """Alias for GetScreentipMso"""
        arguments = [idMso]
        return self.GetScreentipMso(*arguments)

    def GetSupertipMso(self, idMso=None):
        arguments = com_arguments([unwrap(a) for a in [idMso]])
        return self.com_object.GetSupertipMso(*arguments)

    def getsupertipmso(self, idMso=None):
        """Alias for GetSupertipMso"""
        arguments = [idMso]
        return self.GetSupertipMso(*arguments)

    def get_supertip_mso(self, idMso=None):
        """Alias for GetSupertipMso"""
        arguments = [idMso]
        return self.GetSupertipMso(*arguments)

    def GetVisibleMso(self, idMso=None):
        arguments = com_arguments([unwrap(a) for a in [idMso]])
        return self.com_object.GetVisibleMso(*arguments)

    def getvisiblemso(self, idMso=None):
        """Alias for GetVisibleMso"""
        arguments = [idMso]
        return self.GetVisibleMso(*arguments)

    def get_visible_mso(self, idMso=None):
        """Alias for GetVisibleMso"""
        arguments = [idMso]
        return self.GetVisibleMso(*arguments)

    def ReleaseFocus(self):
        return self.com_object.ReleaseFocus()

    def releasefocus(self):
        """Alias for ReleaseFocus"""
        return self.ReleaseFocus()

    def release_focus(self):
        """Alias for ReleaseFocus"""
        return self.ReleaseFocus()


class ContactCard:

    def __init__(self, contactcard=None):
        self.com_object= contactcard

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    def Close(self):
        return self.com_object.Close()

    def close(self):
        """Alias for Close"""
        return self.Close()

    def Show(self, Style=None, Left=None, Right=None, Top=None, Bottom=None, xcord=None, fDelay=None):
        arguments = com_arguments([unwrap(a) for a in [Style, Left, Right, Top, Bottom, xcord, fDelay]])
        return self.com_object.Show(*arguments)

    def show(self, Style=None, Left=None, Right=None, Top=None, Bottom=None, xcord=None, fDelay=None):
        """Alias for Show"""
        arguments = [Style, Left, Right, Top, Bottom, xcord, fDelay]
        return self.Show(*arguments)


# ContentVerificationResults enumeration
contverresError = 0
contverresModified = 4
contverresUnverified = 2
contverresValid = 3
contverresVerifying = 1

class Crop:

    def __init__(self, crop=None):
        self.com_object= crop

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def PictureHeight(self):
        return self.com_object.PictureHeight

    @PictureHeight.setter
    def PictureHeight(self, value):
        self.com_object.PictureHeight = value

    @property
    def pictureheight(self):
        """Alias for PictureHeight"""
        return self.PictureHeight

    @pictureheight.setter
    def pictureheight(self, value):
        """Alias for PictureHeight.setter"""
        self.PictureHeight = value

    @property
    def picture_height(self):
        """Alias for PictureHeight"""
        return self.PictureHeight

    @picture_height.setter
    def picture_height(self, value):
        """Alias for PictureHeight.setter"""
        self.PictureHeight = value

    @property
    def PictureOffsetX(self):
        return self.com_object.PictureOffsetX

    @PictureOffsetX.setter
    def PictureOffsetX(self, value):
        self.com_object.PictureOffsetX = value

    @property
    def pictureoffsetx(self):
        """Alias for PictureOffsetX"""
        return self.PictureOffsetX

    @pictureoffsetx.setter
    def pictureoffsetx(self, value):
        """Alias for PictureOffsetX.setter"""
        self.PictureOffsetX = value

    @property
    def picture_offset_x(self):
        """Alias for PictureOffsetX"""
        return self.PictureOffsetX

    @picture_offset_x.setter
    def picture_offset_x(self, value):
        """Alias for PictureOffsetX.setter"""
        self.PictureOffsetX = value

    @property
    def PictureOffsetY(self):
        return self.com_object.PictureOffsetY

    @PictureOffsetY.setter
    def PictureOffsetY(self, value):
        self.com_object.PictureOffsetY = value

    @property
    def pictureoffsety(self):
        """Alias for PictureOffsetY"""
        return self.PictureOffsetY

    @pictureoffsety.setter
    def pictureoffsety(self, value):
        """Alias for PictureOffsetY.setter"""
        self.PictureOffsetY = value

    @property
    def picture_offset_y(self):
        """Alias for PictureOffsetY"""
        return self.PictureOffsetY

    @picture_offset_y.setter
    def picture_offset_y(self, value):
        """Alias for PictureOffsetY.setter"""
        self.PictureOffsetY = value

    @property
    def PictureWidth(self):
        return self.com_object.PictureWidth

    @PictureWidth.setter
    def PictureWidth(self, value):
        self.com_object.PictureWidth = value

    @property
    def picturewidth(self):
        """Alias for PictureWidth"""
        return self.PictureWidth

    @picturewidth.setter
    def picturewidth(self, value):
        """Alias for PictureWidth.setter"""
        self.PictureWidth = value

    @property
    def picture_width(self):
        """Alias for PictureWidth"""
        return self.PictureWidth

    @picture_width.setter
    def picture_width(self, value):
        """Alias for PictureWidth.setter"""
        self.PictureWidth = value

    @property
    def ShapeHeight(self):
        return self.com_object.ShapeHeight

    @ShapeHeight.setter
    def ShapeHeight(self, value):
        self.com_object.ShapeHeight = value

    @property
    def shapeheight(self):
        """Alias for ShapeHeight"""
        return self.ShapeHeight

    @shapeheight.setter
    def shapeheight(self, value):
        """Alias for ShapeHeight.setter"""
        self.ShapeHeight = value

    @property
    def shape_height(self):
        """Alias for ShapeHeight"""
        return self.ShapeHeight

    @shape_height.setter
    def shape_height(self, value):
        """Alias for ShapeHeight.setter"""
        self.ShapeHeight = value

    @property
    def ShapeLeft(self):
        return self.com_object.ShapeLeft

    @ShapeLeft.setter
    def ShapeLeft(self, value):
        self.com_object.ShapeLeft = value

    @property
    def shapeleft(self):
        """Alias for ShapeLeft"""
        return self.ShapeLeft

    @shapeleft.setter
    def shapeleft(self, value):
        """Alias for ShapeLeft.setter"""
        self.ShapeLeft = value

    @property
    def shape_left(self):
        """Alias for ShapeLeft"""
        return self.ShapeLeft

    @shape_left.setter
    def shape_left(self, value):
        """Alias for ShapeLeft.setter"""
        self.ShapeLeft = value

    @property
    def ShapeTop(self):
        return self.com_object.ShapeTop

    @ShapeTop.setter
    def ShapeTop(self, value):
        self.com_object.ShapeTop = value

    @property
    def shapetop(self):
        """Alias for ShapeTop"""
        return self.ShapeTop

    @shapetop.setter
    def shapetop(self, value):
        """Alias for ShapeTop.setter"""
        self.ShapeTop = value

    @property
    def shape_top(self):
        """Alias for ShapeTop"""
        return self.ShapeTop

    @shape_top.setter
    def shape_top(self, value):
        """Alias for ShapeTop.setter"""
        self.ShapeTop = value

    @property
    def ShapeWidth(self):
        return self.com_object.ShapeWidth

    @ShapeWidth.setter
    def ShapeWidth(self, value):
        self.com_object.ShapeWidth = value

    @property
    def shapewidth(self):
        """Alias for ShapeWidth"""
        return self.ShapeWidth

    @shapewidth.setter
    def shapewidth(self, value):
        """Alias for ShapeWidth.setter"""
        self.ShapeWidth = value

    @property
    def shape_width(self):
        """Alias for ShapeWidth"""
        return self.ShapeWidth

    @shape_width.setter
    def shape_width(self, value):
        """Alias for ShapeWidth.setter"""
        self.ShapeWidth = value


class CustomTaskPane:

    def __init__(self, customtaskpane=None):
        self.com_object= customtaskpane

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def ContentControl(self):
        return self.com_object.ContentControl

    @property
    def contentcontrol(self):
        """Alias for ContentControl"""
        return self.ContentControl

    @property
    def content_control(self):
        """Alias for ContentControl"""
        return self.ContentControl

    @property
    def DockPosition(self):
        return self.com_object.DockPosition

    @DockPosition.setter
    def DockPosition(self, value):
        self.com_object.DockPosition = value

    @property
    def dockposition(self):
        """Alias for DockPosition"""
        return self.DockPosition

    @dockposition.setter
    def dockposition(self, value):
        """Alias for DockPosition.setter"""
        self.DockPosition = value

    @property
    def dock_position(self):
        """Alias for DockPosition"""
        return self.DockPosition

    @dock_position.setter
    def dock_position(self, value):
        """Alias for DockPosition.setter"""
        self.DockPosition = value

    @property
    def DockPositionRestrict(self):
        return self.com_object.DockPositionRestrict

    @DockPositionRestrict.setter
    def DockPositionRestrict(self, value):
        self.com_object.DockPositionRestrict = value

    @property
    def dockpositionrestrict(self):
        """Alias for DockPositionRestrict"""
        return self.DockPositionRestrict

    @dockpositionrestrict.setter
    def dockpositionrestrict(self, value):
        """Alias for DockPositionRestrict.setter"""
        self.DockPositionRestrict = value

    @property
    def dock_position_restrict(self):
        """Alias for DockPositionRestrict"""
        return self.DockPositionRestrict

    @dock_position_restrict.setter
    def dock_position_restrict(self, value):
        """Alias for DockPositionRestrict.setter"""
        self.DockPositionRestrict = value

    @property
    def Height(self):
        return self.com_object.Height

    @Height.setter
    def Height(self, value):
        self.com_object.Height = value

    @property
    def height(self):
        """Alias for Height"""
        return self.Height

    @height.setter
    def height(self, value):
        """Alias for Height.setter"""
        self.Height = value

    @property
    def Title(self):
        return self.com_object.Title

    @property
    def title(self):
        """Alias for Title"""
        return self.Title

    @property
    def Visible(self):
        return self.com_object.Visible

    @Visible.setter
    def Visible(self, value):
        self.com_object.Visible = value

    @property
    def visible(self):
        """Alias for Visible"""
        return self.Visible

    @visible.setter
    def visible(self, value):
        """Alias for Visible.setter"""
        self.Visible = value

    @property
    def Width(self):
        return self.com_object.Width

    @Width.setter
    def Width(self, value):
        self.com_object.Width = value

    @property
    def width(self):
        """Alias for Width"""
        return self.Width

    @width.setter
    def width(self, value):
        """Alias for Width.setter"""
        self.Width = value

    @property
    def Window(self):
        return self.com_object.Window

    @property
    def window(self):
        """Alias for Window"""
        return self.Window

    def Delete(self):
        return self.com_object.Delete()

    def delete(self):
        """Alias for Delete"""
        return self.Delete()


class CustomXMLNode:

    def __init__(self, customxmlnode=None):
        self.com_object= customxmlnode

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Attributes(self):
        return self.com_object.Attributes

    @property
    def attributes(self):
        """Alias for Attributes"""
        return self.Attributes

    @property
    def BaseName(self):
        return self.com_object.BaseName

    @property
    def basename(self):
        """Alias for BaseName"""
        return self.BaseName

    @property
    def base_name(self):
        """Alias for BaseName"""
        return self.BaseName

    @property
    def ChildNodes(self):
        return self.com_object.ChildNodes

    @property
    def childnodes(self):
        """Alias for ChildNodes"""
        return self.ChildNodes

    @property
    def child_nodes(self):
        """Alias for ChildNodes"""
        return self.ChildNodes

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def FirstChild(self):
        return self.com_object.FirstChild

    @property
    def firstchild(self):
        """Alias for FirstChild"""
        return self.FirstChild

    @property
    def first_child(self):
        """Alias for FirstChild"""
        return self.FirstChild

    @property
    def LastChild(self):
        return self.com_object.LastChild

    @property
    def lastchild(self):
        """Alias for LastChild"""
        return self.LastChild

    @property
    def last_child(self):
        """Alias for LastChild"""
        return self.LastChild

    @property
    def NamespaceURI(self):
        return self.com_object.NamespaceURI

    @property
    def namespaceuri(self):
        """Alias for NamespaceURI"""
        return self.NamespaceURI

    @property
    def namespace_u_r_i(self):
        """Alias for NamespaceURI"""
        return self.NamespaceURI

    @property
    def NextSibling(self):
        return self.com_object.NextSibling

    @property
    def nextsibling(self):
        """Alias for NextSibling"""
        return self.NextSibling

    @property
    def next_sibling(self):
        """Alias for NextSibling"""
        return self.NextSibling

    @property
    def NodeType(self):
        return self.com_object.NodeType

    @property
    def nodetype(self):
        """Alias for NodeType"""
        return self.NodeType

    @property
    def node_type(self):
        """Alias for NodeType"""
        return self.NodeType

    @property
    def NodeValue(self):
        return self.com_object.NodeValue

    @NodeValue.setter
    def NodeValue(self, value):
        self.com_object.NodeValue = value

    @property
    def nodevalue(self):
        """Alias for NodeValue"""
        return self.NodeValue

    @nodevalue.setter
    def nodevalue(self, value):
        """Alias for NodeValue.setter"""
        self.NodeValue = value

    @property
    def node_value(self):
        """Alias for NodeValue"""
        return self.NodeValue

    @node_value.setter
    def node_value(self, value):
        """Alias for NodeValue.setter"""
        self.NodeValue = value

    @property
    def OwnerDocument(self):
        return self.com_object.OwnerDocument

    @property
    def ownerdocument(self):
        """Alias for OwnerDocument"""
        return self.OwnerDocument

    @property
    def owner_document(self):
        """Alias for OwnerDocument"""
        return self.OwnerDocument

    @property
    def OwnerPart(self):
        return self.com_object.OwnerPart

    @property
    def ownerpart(self):
        """Alias for OwnerPart"""
        return self.OwnerPart

    @property
    def owner_part(self):
        """Alias for OwnerPart"""
        return self.OwnerPart

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    @property
    def ParentNode(self):
        return self.com_object.ParentNode

    @property
    def parentnode(self):
        """Alias for ParentNode"""
        return self.ParentNode

    @property
    def parent_node(self):
        """Alias for ParentNode"""
        return self.ParentNode

    @property
    def PreviousSibling(self):
        return self.com_object.PreviousSibling

    @property
    def previoussibling(self):
        """Alias for PreviousSibling"""
        return self.PreviousSibling

    @property
    def previous_sibling(self):
        """Alias for PreviousSibling"""
        return self.PreviousSibling

    @property
    def Text(self):
        return self.com_object.Text

    @Text.setter
    def Text(self, value):
        self.com_object.Text = value

    @property
    def text(self):
        """Alias for Text"""
        return self.Text

    @text.setter
    def text(self, value):
        """Alias for Text.setter"""
        self.Text = value

    @property
    def XML(self):
        return self.com_object.XML

    @property
    def xml(self):
        """Alias for XML"""
        return self.XML

    @property
    def x_m_l(self):
        """Alias for XML"""
        return self.XML

    @property
    def XPath(self):
        return self.com_object.XPath

    @property
    def xpath(self):
        """Alias for XPath"""
        return self.XPath

    @property
    def x_path(self):
        """Alias for XPath"""
        return self.XPath

    def AppendChildNode(self, Name=None, NamespaceURI=None, NodeType=None, NodeValue=None):
        arguments = com_arguments([unwrap(a) for a in [Name, NamespaceURI, NodeType, NodeValue]])
        return self.com_object.AppendChildNode(*arguments)

    def appendchildnode(self, Name=None, NamespaceURI=None, NodeType=None, NodeValue=None):
        """Alias for AppendChildNode"""
        arguments = [Name, NamespaceURI, NodeType, NodeValue]
        return self.AppendChildNode(*arguments)

    def append_child_node(self, Name=None, NamespaceURI=None, NodeType=None, NodeValue=None):
        """Alias for AppendChildNode"""
        arguments = [Name, NamespaceURI, NodeType, NodeValue]
        return self.AppendChildNode(*arguments)

    def AppendChildSubtree(self, XML=None):
        arguments = com_arguments([unwrap(a) for a in [XML]])
        return self.com_object.AppendChildSubtree(*arguments)

    def appendchildsubtree(self, XML=None):
        """Alias for AppendChildSubtree"""
        arguments = [XML]
        return self.AppendChildSubtree(*arguments)

    def append_child_subtree(self, XML=None):
        """Alias for AppendChildSubtree"""
        arguments = [XML]
        return self.AppendChildSubtree(*arguments)

    def Delete(self):
        return self.com_object.Delete()

    def delete(self):
        """Alias for Delete"""
        return self.Delete()

    def HasChildNodes(self):
        return self.com_object.HasChildNodes()

    def haschildnodes(self):
        """Alias for HasChildNodes"""
        return self.HasChildNodes()

    def has_child_nodes(self):
        """Alias for HasChildNodes"""
        return self.HasChildNodes()

    def InsertNodeBefore(self, Name=None, NamespaceURI=None, NodeType=None, NodeValue=None, NextSibling=None):
        arguments = com_arguments([unwrap(a) for a in [Name, NamespaceURI, NodeType, NodeValue, NextSibling]])
        return self.com_object.InsertNodeBefore(*arguments)

    def insertnodebefore(self, Name=None, NamespaceURI=None, NodeType=None, NodeValue=None, NextSibling=None):
        """Alias for InsertNodeBefore"""
        arguments = [Name, NamespaceURI, NodeType, NodeValue, NextSibling]
        return self.InsertNodeBefore(*arguments)

    def insert_node_before(self, Name=None, NamespaceURI=None, NodeType=None, NodeValue=None, NextSibling=None):
        """Alias for InsertNodeBefore"""
        arguments = [Name, NamespaceURI, NodeType, NodeValue, NextSibling]
        return self.InsertNodeBefore(*arguments)

    def InsertSubtreeBefore(self, XML=None, NextSibling=None):
        arguments = com_arguments([unwrap(a) for a in [XML, NextSibling]])
        return self.com_object.InsertSubtreeBefore(*arguments)

    def insertsubtreebefore(self, XML=None, NextSibling=None):
        """Alias for InsertSubtreeBefore"""
        arguments = [XML, NextSibling]
        return self.InsertSubtreeBefore(*arguments)

    def insert_subtree_before(self, XML=None, NextSibling=None):
        """Alias for InsertSubtreeBefore"""
        arguments = [XML, NextSibling]
        return self.InsertSubtreeBefore(*arguments)

    def RemoveChild(self, Child=None):
        arguments = com_arguments([unwrap(a) for a in [Child]])
        return self.com_object.RemoveChild(*arguments)

    def removechild(self, Child=None):
        """Alias for RemoveChild"""
        arguments = [Child]
        return self.RemoveChild(*arguments)

    def remove_child(self, Child=None):
        """Alias for RemoveChild"""
        arguments = [Child]
        return self.RemoveChild(*arguments)

    def ReplaceChildNode(self, OldNode=None, Name=None, NamespaceURI=None, NodeType=None, NodeValue=None):
        arguments = com_arguments([unwrap(a) for a in [OldNode, Name, NamespaceURI, NodeType, NodeValue]])
        return self.com_object.ReplaceChildNode(*arguments)

    def replacechildnode(self, OldNode=None, Name=None, NamespaceURI=None, NodeType=None, NodeValue=None):
        """Alias for ReplaceChildNode"""
        arguments = [OldNode, Name, NamespaceURI, NodeType, NodeValue]
        return self.ReplaceChildNode(*arguments)

    def replace_child_node(self, OldNode=None, Name=None, NamespaceURI=None, NodeType=None, NodeValue=None):
        """Alias for ReplaceChildNode"""
        arguments = [OldNode, Name, NamespaceURI, NodeType, NodeValue]
        return self.ReplaceChildNode(*arguments)

    def ReplaceChildSubtree(self, XML=None, OldNode=None):
        arguments = com_arguments([unwrap(a) for a in [XML, OldNode]])
        return self.com_object.ReplaceChildSubtree(*arguments)

    def replacechildsubtree(self, XML=None, OldNode=None):
        """Alias for ReplaceChildSubtree"""
        arguments = [XML, OldNode]
        return self.ReplaceChildSubtree(*arguments)

    def replace_child_subtree(self, XML=None, OldNode=None):
        """Alias for ReplaceChildSubtree"""
        arguments = [XML, OldNode]
        return self.ReplaceChildSubtree(*arguments)

    def SelectNodes(self, XPath=None):
        arguments = com_arguments([unwrap(a) for a in [XPath]])
        return CustomXMLNodes(self.com_object.SelectNodes(*arguments))

    def selectnodes(self, XPath=None):
        """Alias for SelectNodes"""
        arguments = [XPath]
        return self.SelectNodes(*arguments)

    def select_nodes(self, XPath=None):
        """Alias for SelectNodes"""
        arguments = [XPath]
        return self.SelectNodes(*arguments)

    def SelectSingleNode(self, XPath=None):
        arguments = com_arguments([unwrap(a) for a in [XPath]])
        return CustomXMLNode(self.com_object.SelectSingleNode(*arguments))

    def selectsinglenode(self, XPath=None):
        """Alias for SelectSingleNode"""
        arguments = [XPath]
        return self.SelectSingleNode(*arguments)

    def select_single_node(self, XPath=None):
        """Alias for SelectSingleNode"""
        arguments = [XPath]
        return self.SelectSingleNode(*arguments)


class CustomXMLNodes:

    def __init__(self, customxmlnodes=None):
        self.com_object= customxmlnodes

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        if hasattr(self.com_object, "GetItem"):
            return self.com_object.GetItem(*arguments)
        else:
            return self.com_object.Item(*arguments)

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent


class CustomXMLPart:

    def __init__(self, customxmlpart=None):
        self.com_object= customxmlpart

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def BuiltIn(self):
        return self.com_object.BuiltIn

    @property
    def builtin(self):
        """Alias for BuiltIn"""
        return self.BuiltIn

    @property
    def built_in(self):
        """Alias for BuiltIn"""
        return self.BuiltIn

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def DocumentElement(self):
        return self.com_object.DocumentElement

    @property
    def documentelement(self):
        """Alias for DocumentElement"""
        return self.DocumentElement

    @property
    def document_element(self):
        """Alias for DocumentElement"""
        return self.DocumentElement

    @property
    def Errors(self):
        return self.com_object.Errors

    @property
    def errors(self):
        """Alias for Errors"""
        return self.Errors

    @property
    def Id(self):
        return self.com_object.Id

    @property
    def id(self):
        """Alias for Id"""
        return self.Id

    @property
    def NamespaceManager(self):
        return self.com_object.NamespaceManager

    @property
    def namespacemanager(self):
        """Alias for NamespaceManager"""
        return self.NamespaceManager

    @property
    def namespace_manager(self):
        """Alias for NamespaceManager"""
        return self.NamespaceManager

    @property
    def NamespaceURI(self):
        return self.com_object.NamespaceURI

    @property
    def namespaceuri(self):
        """Alias for NamespaceURI"""
        return self.NamespaceURI

    @property
    def namespace_u_r_i(self):
        """Alias for NamespaceURI"""
        return self.NamespaceURI

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    @property
    def SchemaCollection(self):
        return self.com_object.SchemaCollection

    @SchemaCollection.setter
    def SchemaCollection(self, value):
        self.com_object.SchemaCollection = value

    @property
    def schemacollection(self):
        """Alias for SchemaCollection"""
        return self.SchemaCollection

    @schemacollection.setter
    def schemacollection(self, value):
        """Alias for SchemaCollection.setter"""
        self.SchemaCollection = value

    @property
    def schema_collection(self):
        """Alias for SchemaCollection"""
        return self.SchemaCollection

    @schema_collection.setter
    def schema_collection(self, value):
        """Alias for SchemaCollection.setter"""
        self.SchemaCollection = value

    @property
    def XML(self):
        return self.com_object.XML

    @property
    def xml(self):
        """Alias for XML"""
        return self.XML

    @property
    def x_m_l(self):
        """Alias for XML"""
        return self.XML

    def AddNode(self, Parent=None, Name=None, NamespaceURI=None, NextSibling=None, NodeType=None, NodeValue=None):
        arguments = com_arguments([unwrap(a) for a in [Parent, Name, NamespaceURI, NextSibling, NodeType, NodeValue]])
        return self.com_object.AddNode(*arguments)

    def addnode(self, Parent=None, Name=None, NamespaceURI=None, NextSibling=None, NodeType=None, NodeValue=None):
        """Alias for AddNode"""
        arguments = [Parent, Name, NamespaceURI, NextSibling, NodeType, NodeValue]
        return self.AddNode(*arguments)

    def add_node(self, Parent=None, Name=None, NamespaceURI=None, NextSibling=None, NodeType=None, NodeValue=None):
        """Alias for AddNode"""
        arguments = [Parent, Name, NamespaceURI, NextSibling, NodeType, NodeValue]
        return self.AddNode(*arguments)

    def Delete(self):
        return self.com_object.Delete()

    def delete(self):
        """Alias for Delete"""
        return self.Delete()

    def Load(self, FilePath=None):
        arguments = com_arguments([unwrap(a) for a in [FilePath]])
        return self.com_object.Load(*arguments)

    def load(self, FilePath=None):
        """Alias for Load"""
        arguments = [FilePath]
        return self.Load(*arguments)

    def LoadXML(self, XML=None):
        arguments = com_arguments([unwrap(a) for a in [XML]])
        return self.com_object.LoadXML(*arguments)

    def loadxml(self, XML=None):
        """Alias for LoadXML"""
        arguments = [XML]
        return self.LoadXML(*arguments)

    def load_x_m_l(self, XML=None):
        """Alias for LoadXML"""
        arguments = [XML]
        return self.LoadXML(*arguments)

    def SelectNodes(self, XPath=None):
        arguments = com_arguments([unwrap(a) for a in [XPath]])
        return CustomXMLNodes(self.com_object.SelectNodes(*arguments))

    def selectnodes(self, XPath=None):
        """Alias for SelectNodes"""
        arguments = [XPath]
        return self.SelectNodes(*arguments)

    def select_nodes(self, XPath=None):
        """Alias for SelectNodes"""
        arguments = [XPath]
        return self.SelectNodes(*arguments)

    def SelectSingleNode(self, XPath=None):
        arguments = com_arguments([unwrap(a) for a in [XPath]])
        return CustomXMLNode(self.com_object.SelectSingleNode(*arguments))

    def selectsinglenode(self, XPath=None):
        """Alias for SelectSingleNode"""
        arguments = [XPath]
        return self.SelectSingleNode(*arguments)

    def select_single_node(self, XPath=None):
        """Alias for SelectSingleNode"""
        arguments = [XPath]
        return self.SelectSingleNode(*arguments)


class CustomXMLParts:

    def __init__(self, customxmlparts=None):
        self.com_object= customxmlparts

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        if hasattr(self.com_object, "GetItem"):
            return self.com_object.GetItem(*arguments)
        else:
            return self.com_object.Item(*arguments)

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    def Add(self, XML=None, SchemaCollection=None):
        arguments = com_arguments([unwrap(a) for a in [XML, SchemaCollection]])
        return CustomXMLPart(self.com_object.Add(*arguments))

    def add(self, XML=None, SchemaCollection=None):
        """Alias for Add"""
        arguments = [XML, SchemaCollection]
        return self.Add(*arguments)

    def SelectByID(self, Id=None):
        arguments = com_arguments([unwrap(a) for a in [Id]])
        return CustomXMLPart(self.com_object.SelectByID(*arguments))

    def selectbyid(self, Id=None):
        """Alias for SelectByID"""
        arguments = [Id]
        return self.SelectByID(*arguments)

    def select_by_i_d(self, Id=None):
        """Alias for SelectByID"""
        arguments = [Id]
        return self.SelectByID(*arguments)

    def SelectByNamespace(self, NamespaceURI=None):
        arguments = com_arguments([unwrap(a) for a in [NamespaceURI]])
        return CustomXMLParts(self.com_object.SelectByNamespace(*arguments))

    def selectbynamespace(self, NamespaceURI=None):
        """Alias for SelectByNamespace"""
        arguments = [NamespaceURI]
        return self.SelectByNamespace(*arguments)

    def select_by_namespace(self, NamespaceURI=None):
        """Alias for SelectByNamespace"""
        arguments = [NamespaceURI]
        return self.SelectByNamespace(*arguments)


class CustomXMLPrefixMapping:

    def __init__(self, customxmlprefixmapping=None):
        self.com_object= customxmlprefixmapping

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def NamespaceURI(self):
        return self.com_object.NamespaceURI

    @property
    def namespaceuri(self):
        """Alias for NamespaceURI"""
        return self.NamespaceURI

    @property
    def namespace_u_r_i(self):
        """Alias for NamespaceURI"""
        return self.NamespaceURI

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    @property
    def Prefix(self):
        return self.com_object.Prefix

    @property
    def prefix(self):
        """Alias for Prefix"""
        return self.Prefix


class CustomXMLPrefixMappings:

    def __init__(self, customxmlprefixmappings=None):
        self.com_object= customxmlprefixmappings

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        if hasattr(self.com_object, "GetItem"):
            return self.com_object.GetItem(*arguments)
        else:
            return self.com_object.Item(*arguments)

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    def AddNamespace(self, Prefix=None, NamespaceURI=None):
        arguments = com_arguments([unwrap(a) for a in [Prefix, NamespaceURI]])
        return self.com_object.AddNamespace(*arguments)

    def addnamespace(self, Prefix=None, NamespaceURI=None):
        """Alias for AddNamespace"""
        arguments = [Prefix, NamespaceURI]
        return self.AddNamespace(*arguments)

    def add_namespace(self, Prefix=None, NamespaceURI=None):
        """Alias for AddNamespace"""
        arguments = [Prefix, NamespaceURI]
        return self.AddNamespace(*arguments)

    def LookupNamespace(self, Prefix=None):
        arguments = com_arguments([unwrap(a) for a in [Prefix]])
        return self.com_object.LookupNamespace(*arguments)

    def lookupnamespace(self, Prefix=None):
        """Alias for LookupNamespace"""
        arguments = [Prefix]
        return self.LookupNamespace(*arguments)

    def lookup_namespace(self, Prefix=None):
        """Alias for LookupNamespace"""
        arguments = [Prefix]
        return self.LookupNamespace(*arguments)

    def LookupPrefix(self, NamespaceURI=None):
        arguments = com_arguments([unwrap(a) for a in [NamespaceURI]])
        return self.com_object.LookupPrefix(*arguments)

    def lookupprefix(self, NamespaceURI=None):
        """Alias for LookupPrefix"""
        arguments = [NamespaceURI]
        return self.LookupPrefix(*arguments)

    def lookup_prefix(self, NamespaceURI=None):
        """Alias for LookupPrefix"""
        arguments = [NamespaceURI]
        return self.LookupPrefix(*arguments)


class CustomXMLSchema:

    def __init__(self, customxmlschema=None):
        self.com_object= customxmlschema

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Location(self):
        return self.com_object.Location

    @property
    def location(self):
        """Alias for Location"""
        return self.Location

    @property
    def NamespaceURI(self):
        return self.com_object.NamespaceURI

    @property
    def namespaceuri(self):
        """Alias for NamespaceURI"""
        return self.NamespaceURI

    @property
    def namespace_u_r_i(self):
        """Alias for NamespaceURI"""
        return self.NamespaceURI

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    def Delete(self):
        return self.com_object.Delete()

    def delete(self):
        """Alias for Delete"""
        return self.Delete()

    def Reload(self):
        return self.com_object.Reload()

    def reload(self):
        """Alias for Reload"""
        return self.Reload()


class CustomXMLSchemaCollection:

    def __init__(self, customxmlschemacollection=None):
        self.com_object= customxmlschemacollection

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        if hasattr(self.com_object, "GetItem"):
            return self.com_object.GetItem(*arguments)
        else:
            return self.com_object.Item(*arguments)

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)

    def NamespaceURI(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        if hasattr(self.com_object, "GetNamespaceURI"):
            return self.com_object.GetNamespaceURI(*arguments)
        else:
            return self.com_object.NamespaceURI(*arguments)

    def namespaceuri(self, Index=None):
        """Alias for NamespaceURI"""
        arguments = [Index]
        return self.NamespaceURI(*arguments)

    def namespace_u_r_i(self, Index=None):
        """Alias for NamespaceURI"""
        arguments = [Index]
        return self.NamespaceURI(*arguments)

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    def Add(self, NamespaceURI=None, Alias=None, FileName=None, InstallForAllUsers=None):
        arguments = com_arguments([unwrap(a) for a in [NamespaceURI, Alias, FileName, InstallForAllUsers]])
        return CustomXMLSchema(self.com_object.Add(*arguments))

    def add(self, NamespaceURI=None, Alias=None, FileName=None, InstallForAllUsers=None):
        """Alias for Add"""
        arguments = [NamespaceURI, Alias, FileName, InstallForAllUsers]
        return self.Add(*arguments)

    def AddCollection(self, SchemaCollection=None):
        arguments = com_arguments([unwrap(a) for a in [SchemaCollection]])
        return self.com_object.AddCollection(*arguments)

    def addcollection(self, SchemaCollection=None):
        """Alias for AddCollection"""
        arguments = [SchemaCollection]
        return self.AddCollection(*arguments)

    def add_collection(self, SchemaCollection=None):
        """Alias for AddCollection"""
        arguments = [SchemaCollection]
        return self.AddCollection(*arguments)

    def Validate(self):
        return self.com_object.Validate()

    def validate(self):
        """Alias for Validate"""
        return self.Validate()


class CustomXMLValidationError:

    def __init__(self, customxmlvalidationerror=None):
        self.com_object= customxmlvalidationerror

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def ErrorCode(self):
        return self.com_object.ErrorCode

    @property
    def errorcode(self):
        """Alias for ErrorCode"""
        return self.ErrorCode

    @property
    def error_code(self):
        """Alias for ErrorCode"""
        return self.ErrorCode

    @property
    def Name(self):
        return self.com_object.Name

    @property
    def name(self):
        """Alias for Name"""
        return self.Name

    @property
    def Node(self):
        return self.com_object.Node

    @property
    def node(self):
        """Alias for Node"""
        return self.Node

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    @property
    def Text(self):
        return self.com_object.Text

    @property
    def text(self):
        """Alias for Text"""
        return self.Text

    @property
    def Type(self):
        return self.com_object.Type

    @property
    def type(self):
        """Alias for Type"""
        return self.Type

    def Delete(self):
        return self.com_object.Delete()

    def delete(self):
        """Alias for Delete"""
        return self.Delete()


class CustomXMLValidationErrors:

    def __init__(self, customxmlvalidationerrors=None):
        self.com_object= customxmlvalidationerrors

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        if hasattr(self.com_object, "GetItem"):
            return self.com_object.GetItem(*arguments)
        else:
            return self.com_object.Item(*arguments)

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    def Add(self, Node=None, ErrorName=None, ErrorText=None, ClearedOnUpdate=None):
        arguments = com_arguments([unwrap(a) for a in [Node, ErrorName, ErrorText, ClearedOnUpdate]])
        return self.com_object.Add(*arguments)

    def add(self, Node=None, ErrorName=None, ErrorText=None, ClearedOnUpdate=None):
        """Alias for Add"""
        arguments = [Node, ErrorName, ErrorText, ClearedOnUpdate]
        return self.Add(*arguments)


class DocumentInspector:

    def __init__(self, documentinspector=None):
        self.com_object= documentinspector

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Description(self):
        return self.com_object.Description

    @property
    def description(self):
        """Alias for Description"""
        return self.Description

    @property
    def Name(self):
        return self.com_object.Name

    @property
    def name(self):
        """Alias for Name"""
        return self.Name

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    def Fix(self, Status=None, Results=None):
        arguments = com_arguments([unwrap(a) for a in [Status, Results]])
        return self.com_object.Fix(*arguments)

    def fix(self, Status=None, Results=None):
        """Alias for Fix"""
        arguments = [Status, Results]
        return self.Fix(*arguments)

    def Inspect(self, Status=None, Results=None):
        arguments = com_arguments([unwrap(a) for a in [Status, Results]])
        return self.com_object.Inspect(*arguments)

    def inspect(self, Status=None, Results=None):
        """Alias for Inspect"""
        arguments = [Status, Results]
        return self.Inspect(*arguments)


class DocumentInspectors:

    def __init__(self, documentinspectors=None):
        self.com_object= documentinspectors

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        if hasattr(self.com_object, "GetItem"):
            return self.com_object.GetItem(*arguments)
        else:
            return self.com_object.Item(*arguments)

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent


class DocumentLibraryVersion:

    def __init__(self, documentlibraryversion=None):
        self.com_object= documentlibraryversion

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Comments(self):
        return self.com_object.Comments

    @property
    def comments(self):
        """Alias for Comments"""
        return self.Comments

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Index(self):
        return self.com_object.Index

    @property
    def index(self):
        """Alias for Index"""
        return self.Index

    @property
    def Modified(self):
        return self.com_object.Modified

    @property
    def modified(self):
        """Alias for Modified"""
        return self.Modified

    @property
    def ModifiedBy(self):
        return self.com_object.ModifiedBy

    @property
    def modifiedby(self):
        """Alias for ModifiedBy"""
        return self.ModifiedBy

    @property
    def modified_by(self):
        """Alias for ModifiedBy"""
        return self.ModifiedBy

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    def Delete(self):
        return self.com_object.Delete()

    def delete(self):
        """Alias for Delete"""
        return self.Delete()

    def Open(self):
        return self.com_object.Open()

    def open(self):
        """Alias for Open"""
        return self.Open()

    def Restore(self):
        return self.com_object.Restore()

    def restore(self):
        """Alias for Restore"""
        return self.Restore()


class DocumentLibraryVersions:

    def __init__(self, documentlibraryversions=None):
        self.com_object= documentlibraryversions

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def IsVersioningEnabled(self):
        return self.com_object.IsVersioningEnabled

    @property
    def isversioningenabled(self):
        """Alias for IsVersioningEnabled"""
        return self.IsVersioningEnabled

    @property
    def is_versioning_enabled(self):
        """Alias for IsVersioningEnabled"""
        return self.IsVersioningEnabled

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        if hasattr(self.com_object, "GetItem"):
            return self.com_object.GetItem(*arguments)
        else:
            return self.com_object.Item(*arguments)

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent


class DocumentProperties:

    def __init__(self, documentproperties=None):
        self.com_object= documentproperties

    def Application(self, ppidisp=None):
        arguments = com_arguments([unwrap(a) for a in [ppidisp]])
        if hasattr(self.com_object, "GetApplication"):
            return self.com_object.GetApplication(*arguments)
        else:
            return self.com_object.Application(*arguments)

    def application(self, ppidisp=None):
        """Alias for Application"""
        arguments = [ppidisp]
        return self.Application(*arguments)

    def Count(self, pc=None):
        arguments = com_arguments([unwrap(a) for a in [pc]])
        if hasattr(self.com_object, "GetCount"):
            return self.com_object.GetCount(*arguments)
        else:
            return self.com_object.Count(*arguments)

    def count(self, pc=None):
        """Alias for Count"""
        arguments = [pc]
        return self.Count(*arguments)

    def Creator(self, plCreator=None):
        arguments = com_arguments([unwrap(a) for a in [plCreator]])
        if hasattr(self.com_object, "GetCreator"):
            return self.com_object.GetCreator(*arguments)
        else:
            return self.com_object.Creator(*arguments)

    def creator(self, plCreator=None):
        """Alias for Creator"""
        arguments = [plCreator]
        return self.Creator(*arguments)

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        if hasattr(self.com_object, "GetItem"):
            return self.com_object.GetItem(*arguments)
        else:
            return self.com_object.Item(*arguments)

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    def Add(self, Name=None, LinkToContent=None, Type=None, Value=None, LinkSource=None):
        arguments = com_arguments([unwrap(a) for a in [Name, LinkToContent, Type, Value, LinkSource]])
        return self.com_object.Add(*arguments)

    def add(self, Name=None, LinkToContent=None, Type=None, Value=None, LinkSource=None):
        """Alias for Add"""
        arguments = [Name, LinkToContent, Type, Value, LinkSource]
        return self.Add(*arguments)


class DocumentProperty:

    def __init__(self, documentproperty=None):
        self.com_object= documentproperty

    def Application(self, ppidisp=None):
        arguments = com_arguments([unwrap(a) for a in [ppidisp]])
        if hasattr(self.com_object, "GetApplication"):
            return self.com_object.GetApplication(*arguments)
        else:
            return self.com_object.Application(*arguments)

    def application(self, ppidisp=None):
        """Alias for Application"""
        arguments = [ppidisp]
        return self.Application(*arguments)

    def Creator(self, plCreator=None):
        arguments = com_arguments([unwrap(a) for a in [plCreator]])
        if hasattr(self.com_object, "GetCreator"):
            return self.com_object.GetCreator(*arguments)
        else:
            return self.com_object.Creator(*arguments)

    def creator(self, plCreator=None):
        """Alias for Creator"""
        arguments = [plCreator]
        return self.Creator(*arguments)

    @property
    def LinkSource(self):
        return self.com_object.LinkSource

    @LinkSource.setter
    def LinkSource(self, value):
        self.com_object.LinkSource = value

    @property
    def linksource(self):
        """Alias for LinkSource"""
        return self.LinkSource

    @linksource.setter
    def linksource(self, value):
        """Alias for LinkSource.setter"""
        self.LinkSource = value

    @property
    def link_source(self):
        """Alias for LinkSource"""
        return self.LinkSource

    @link_source.setter
    def link_source(self, value):
        """Alias for LinkSource.setter"""
        self.LinkSource = value

    @property
    def LinkToContent(self):
        return self.com_object.LinkToContent

    @LinkToContent.setter
    def LinkToContent(self, value):
        self.com_object.LinkToContent = value

    @property
    def linktocontent(self):
        """Alias for LinkToContent"""
        return self.LinkToContent

    @linktocontent.setter
    def linktocontent(self, value):
        """Alias for LinkToContent.setter"""
        self.LinkToContent = value

    @property
    def link_to_content(self):
        """Alias for LinkToContent"""
        return self.LinkToContent

    @link_to_content.setter
    def link_to_content(self, value):
        """Alias for LinkToContent.setter"""
        self.LinkToContent = value

    @property
    def Name(self):
        return self.com_object.Name

    @Name.setter
    def Name(self, value):
        self.com_object.Name = value

    @property
    def name(self):
        """Alias for Name"""
        return self.Name

    @name.setter
    def name(self, value):
        """Alias for Name.setter"""
        self.Name = value

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    @property
    def Type(self):
        return self.com_object.Type

    @property
    def type(self):
        """Alias for Type"""
        return self.Type

    @property
    def Value(self):
        return self.com_object.Value

    @Value.setter
    def Value(self, value):
        self.com_object.Value = value

    @property
    def value(self):
        """Alias for Value"""
        return self.Value

    @value.setter
    def value(self, value):
        """Alias for Value.setter"""
        self.Value = value

    def Delete(self):
        return self.com_object.Delete()

    def delete(self):
        """Alias for Delete"""
        return self.Delete()


class EffectParameter:

    def __init__(self, effectparameter=None):
        self.com_object= effectparameter

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Name(self):
        return self.com_object.Name

    @property
    def name(self):
        """Alias for Name"""
        return self.Name

    @property
    def Value(self):
        return self.com_object.Value

    @Value.setter
    def Value(self, value):
        self.com_object.Value = value

    @property
    def value(self):
        """Alias for Value"""
        return self.Value

    @value.setter
    def value(self, value):
        """Alias for Value.setter"""
        self.Value = value


class EffectParameters:

    def __init__(self, effectparameters=None):
        self.com_object= effectparameters

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        if hasattr(self.com_object, "GetItem"):
            return self.com_object.GetItem(*arguments)
        else:
            return self.com_object.Item(*arguments)

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)


# EncryptionCipherMode enumeration
cipherModeECB = 0
cipherModeCBC = 1

class EncryptionProvider:

    def __init__(self, encryptionprovider=None):
        self.com_object= encryptionprovider

    def Authenticate(self, ParentWindow=None, EncryptionData=None, PermissionsMask=None):
        arguments = com_arguments([unwrap(a) for a in [ParentWindow, EncryptionData, PermissionsMask]])
        return self.com_object.Authenticate(*arguments)

    def authenticate(self, ParentWindow=None, EncryptionData=None, PermissionsMask=None):
        """Alias for Authenticate"""
        arguments = [ParentWindow, EncryptionData, PermissionsMask]
        return self.Authenticate(*arguments)

    def CloneSession(self, SessionHandle=None):
        arguments = com_arguments([unwrap(a) for a in [SessionHandle]])
        return self.com_object.CloneSession(*arguments)

    def clonesession(self, SessionHandle=None):
        """Alias for CloneSession"""
        arguments = [SessionHandle]
        return self.CloneSession(*arguments)

    def clone_session(self, SessionHandle=None):
        """Alias for CloneSession"""
        arguments = [SessionHandle]
        return self.CloneSession(*arguments)

    def DecryptStream(self, SessionHandle=None, StreamName=None, EncryptedStream=None, UnencryptedStream=None):
        arguments = com_arguments([unwrap(a) for a in [SessionHandle, StreamName, EncryptedStream, UnencryptedStream]])
        return self.com_object.DecryptStream(*arguments)

    def decryptstream(self, SessionHandle=None, StreamName=None, EncryptedStream=None, UnencryptedStream=None):
        """Alias for DecryptStream"""
        arguments = [SessionHandle, StreamName, EncryptedStream, UnencryptedStream]
        return self.DecryptStream(*arguments)

    def decrypt_stream(self, SessionHandle=None, StreamName=None, EncryptedStream=None, UnencryptedStream=None):
        """Alias for DecryptStream"""
        arguments = [SessionHandle, StreamName, EncryptedStream, UnencryptedStream]
        return self.DecryptStream(*arguments)

    def EncryptStream(self, SessionHandle=None, StreamName=None, UnencryptedStream=None, EncryptedStream=None):
        arguments = com_arguments([unwrap(a) for a in [SessionHandle, StreamName, UnencryptedStream, EncryptedStream]])
        return self.com_object.EncryptStream(*arguments)

    def encryptstream(self, SessionHandle=None, StreamName=None, UnencryptedStream=None, EncryptedStream=None):
        """Alias for EncryptStream"""
        arguments = [SessionHandle, StreamName, UnencryptedStream, EncryptedStream]
        return self.EncryptStream(*arguments)

    def encrypt_stream(self, SessionHandle=None, StreamName=None, UnencryptedStream=None, EncryptedStream=None):
        """Alias for EncryptStream"""
        arguments = [SessionHandle, StreamName, UnencryptedStream, EncryptedStream]
        return self.EncryptStream(*arguments)

    def EndSession(self, SessionHandle=None):
        arguments = com_arguments([unwrap(a) for a in [SessionHandle]])
        return self.com_object.EndSession(*arguments)

    def endsession(self, SessionHandle=None):
        """Alias for EndSession"""
        arguments = [SessionHandle]
        return self.EndSession(*arguments)

    def end_session(self, SessionHandle=None):
        """Alias for EndSession"""
        arguments = [SessionHandle]
        return self.EndSession(*arguments)

    def GetProviderDetail(self, encprovdet=None):
        arguments = com_arguments([unwrap(a) for a in [encprovdet]])
        return self.com_object.GetProviderDetail(*arguments)

    def getproviderdetail(self, encprovdet=None):
        """Alias for GetProviderDetail"""
        arguments = [encprovdet]
        return self.GetProviderDetail(*arguments)

    def get_provider_detail(self, encprovdet=None):
        """Alias for GetProviderDetail"""
        arguments = [encprovdet]
        return self.GetProviderDetail(*arguments)

    def NewSession(self, ParentWindow=None):
        arguments = com_arguments([unwrap(a) for a in [ParentWindow]])
        return self.com_object.NewSession(*arguments)

    def newsession(self, ParentWindow=None):
        """Alias for NewSession"""
        arguments = [ParentWindow]
        return self.NewSession(*arguments)

    def new_session(self, ParentWindow=None):
        """Alias for NewSession"""
        arguments = [ParentWindow]
        return self.NewSession(*arguments)

    def Save(self, SessionHandle=None, EncryptionData=None):
        arguments = com_arguments([unwrap(a) for a in [SessionHandle, EncryptionData]])
        return self.com_object.Save(*arguments)

    def save(self, SessionHandle=None, EncryptionData=None):
        """Alias for Save"""
        arguments = [SessionHandle, EncryptionData]
        return self.Save(*arguments)

    def ShowSettings(self, SessionHandle=None, ParentWindow=None, ReadOnly=None, Remove=None):
        arguments = com_arguments([unwrap(a) for a in [SessionHandle, ParentWindow, ReadOnly, Remove]])
        return self.com_object.ShowSettings(*arguments)

    def showsettings(self, SessionHandle=None, ParentWindow=None, ReadOnly=None, Remove=None):
        """Alias for ShowSettings"""
        arguments = [SessionHandle, ParentWindow, ReadOnly, Remove]
        return self.ShowSettings(*arguments)

    def show_settings(self, SessionHandle=None, ParentWindow=None, ReadOnly=None, Remove=None):
        """Alias for ShowSettings"""
        arguments = [SessionHandle, ParentWindow, ReadOnly, Remove]
        return self.ShowSettings(*arguments)


# EncryptionProviderDetail enumeration
encprovdetURL = 0
encprovdetAlgorithm = 1
encprovdetBlockCipher = 2
encprovdetCipherBlockSize = 3
encprovdetCipherMode = 4

class FileDialog:

    def __init__(self, filedialog=None):
        self.com_object= filedialog

    @property
    def AllowMultiSelect(self):
        return self.com_object.AllowMultiSelect

    @AllowMultiSelect.setter
    def AllowMultiSelect(self, value):
        self.com_object.AllowMultiSelect = value

    @property
    def allowmultiselect(self):
        """Alias for AllowMultiSelect"""
        return self.AllowMultiSelect

    @allowmultiselect.setter
    def allowmultiselect(self, value):
        """Alias for AllowMultiSelect.setter"""
        self.AllowMultiSelect = value

    @property
    def allow_multi_select(self):
        """Alias for AllowMultiSelect"""
        return self.AllowMultiSelect

    @allow_multi_select.setter
    def allow_multi_select(self, value):
        """Alias for AllowMultiSelect.setter"""
        self.AllowMultiSelect = value

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def ButtonName(self):
        return self.com_object.ButtonName

    @ButtonName.setter
    def ButtonName(self, value):
        self.com_object.ButtonName = value

    @property
    def buttonname(self):
        """Alias for ButtonName"""
        return self.ButtonName

    @buttonname.setter
    def buttonname(self, value):
        """Alias for ButtonName.setter"""
        self.ButtonName = value

    @property
    def button_name(self):
        """Alias for ButtonName"""
        return self.ButtonName

    @button_name.setter
    def button_name(self, value):
        """Alias for ButtonName.setter"""
        self.ButtonName = value

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def DialogType(self):
        return self.com_object.DialogType

    @property
    def dialogtype(self):
        """Alias for DialogType"""
        return self.DialogType

    @property
    def dialog_type(self):
        """Alias for DialogType"""
        return self.DialogType

    @property
    def FilterIndex(self):
        return self.com_object.FilterIndex

    @FilterIndex.setter
    def FilterIndex(self, value):
        self.com_object.FilterIndex = value

    @property
    def filterindex(self):
        """Alias for FilterIndex"""
        return self.FilterIndex

    @filterindex.setter
    def filterindex(self, value):
        """Alias for FilterIndex.setter"""
        self.FilterIndex = value

    @property
    def filter_index(self):
        """Alias for FilterIndex"""
        return self.FilterIndex

    @filter_index.setter
    def filter_index(self, value):
        """Alias for FilterIndex.setter"""
        self.FilterIndex = value

    @property
    def Filters(self):
        return self.com_object.Filters

    @property
    def filters(self):
        """Alias for Filters"""
        return self.Filters

    @property
    def InitialFileName(self):
        return self.com_object.InitialFileName

    @InitialFileName.setter
    def InitialFileName(self, value):
        self.com_object.InitialFileName = value

    @property
    def initialfilename(self):
        """Alias for InitialFileName"""
        return self.InitialFileName

    @initialfilename.setter
    def initialfilename(self, value):
        """Alias for InitialFileName.setter"""
        self.InitialFileName = value

    @property
    def initial_file_name(self):
        """Alias for InitialFileName"""
        return self.InitialFileName

    @initial_file_name.setter
    def initial_file_name(self, value):
        """Alias for InitialFileName.setter"""
        self.InitialFileName = value

    @property
    def InitialView(self):
        return self.com_object.InitialView

    @InitialView.setter
    def InitialView(self, value):
        self.com_object.InitialView = value

    @property
    def initialview(self):
        """Alias for InitialView"""
        return self.InitialView

    @initialview.setter
    def initialview(self, value):
        """Alias for InitialView.setter"""
        self.InitialView = value

    @property
    def initial_view(self):
        """Alias for InitialView"""
        return self.InitialView

    @initial_view.setter
    def initial_view(self, value):
        """Alias for InitialView.setter"""
        self.InitialView = value

    @property
    def Item(self):
        return self.com_object.Item

    @property
    def item(self):
        """Alias for Item"""
        return self.Item

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    @property
    def SelectedItems(self):
        return self.com_object.SelectedItems

    @property
    def selecteditems(self):
        """Alias for SelectedItems"""
        return self.SelectedItems

    @property
    def selected_items(self):
        """Alias for SelectedItems"""
        return self.SelectedItems

    @property
    def Title(self):
        return self.com_object.Title

    @Title.setter
    def Title(self, value):
        self.com_object.Title = value

    @property
    def title(self):
        """Alias for Title"""
        return self.Title

    @title.setter
    def title(self, value):
        """Alias for Title.setter"""
        self.Title = value

    def Execute(self):
        return self.com_object.Execute()

    def execute(self):
        """Alias for Execute"""
        return self.Execute()

    def Show(self):
        return self.com_object.Show()

    def show(self):
        """Alias for Show"""
        return self.Show()


class FileDialogFilter:

    def __init__(self, filedialogfilter=None):
        self.com_object= filedialogfilter

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Description(self):
        return self.com_object.Description

    @property
    def description(self):
        """Alias for Description"""
        return self.Description

    @property
    def Extensions(self):
        return self.com_object.Extensions

    @property
    def extensions(self):
        """Alias for Extensions"""
        return self.Extensions

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent


class FileDialogFilters:

    def __init__(self, filedialogfilters=None):
        self.com_object= filedialogfilters

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    def Add(self, Description=None, Extensions=None, Position=None):
        arguments = com_arguments([unwrap(a) for a in [Description, Extensions, Position]])
        return self.com_object.Add(*arguments)

    def add(self, Description=None, Extensions=None, Position=None):
        """Alias for Add"""
        arguments = [Description, Extensions, Position]
        return self.Add(*arguments)

    def Clear(self):
        return self.com_object.Clear()

    def clear(self):
        """Alias for Clear"""
        return self.Clear()

    def Delete(self, filter=None):
        arguments = com_arguments([unwrap(a) for a in [filter]])
        return self.com_object.Delete(*arguments)

    def delete(self, filter=None):
        """Alias for Delete"""
        arguments = [filter]
        return self.Delete(*arguments)

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        return self.com_object.Item(*arguments)

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)


class FileDialogSelectedItems:

    def __init__(self, filedialogselecteditems=None):
        self.com_object= filedialogselecteditems

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        return self.com_object.Item(*arguments)

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)


class FileTypes:

    def __init__(self, filetypes=None):
        self.com_object= filetypes

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        if hasattr(self.com_object, "GetItem"):
            return self.com_object.GetItem(*arguments)
        else:
            return self.com_object.Item(*arguments)

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)

    def Add(self, FileType=None):
        arguments = com_arguments([unwrap(a) for a in [FileType]])
        return self.com_object.Add(*arguments)

    def add(self, FileType=None):
        """Alias for Add"""
        arguments = [FileType]
        return self.Add(*arguments)

    def Remove(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        return self.com_object.Remove(*arguments)

    def remove(self, Index=None):
        """Alias for Remove"""
        arguments = [Index]
        return self.Remove(*arguments)


class Font2:

    def __init__(self, font2=None):
        self.com_object= font2

    @property
    def Allcaps(self):
        return self.com_object.Allcaps

    @Allcaps.setter
    def Allcaps(self, value):
        self.com_object.Allcaps = value

    @property
    def allcaps(self):
        """Alias for Allcaps"""
        return self.Allcaps

    @allcaps.setter
    def allcaps(self, value):
        """Alias for Allcaps.setter"""
        self.Allcaps = value

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def AutorotateNumbers(self):
        return self.com_object.AutorotateNumbers

    @AutorotateNumbers.setter
    def AutorotateNumbers(self, value):
        self.com_object.AutorotateNumbers = value

    @property
    def autorotatenumbers(self):
        """Alias for AutorotateNumbers"""
        return self.AutorotateNumbers

    @autorotatenumbers.setter
    def autorotatenumbers(self, value):
        """Alias for AutorotateNumbers.setter"""
        self.AutorotateNumbers = value

    @property
    def autorotate_numbers(self):
        """Alias for AutorotateNumbers"""
        return self.AutorotateNumbers

    @autorotate_numbers.setter
    def autorotate_numbers(self, value):
        """Alias for AutorotateNumbers.setter"""
        self.AutorotateNumbers = value

    @property
    def BaselineOffset(self):
        return self.com_object.BaselineOffset

    @BaselineOffset.setter
    def BaselineOffset(self, value):
        self.com_object.BaselineOffset = value

    @property
    def baselineoffset(self):
        """Alias for BaselineOffset"""
        return self.BaselineOffset

    @baselineoffset.setter
    def baselineoffset(self, value):
        """Alias for BaselineOffset.setter"""
        self.BaselineOffset = value

    @property
    def baseline_offset(self):
        """Alias for BaselineOffset"""
        return self.BaselineOffset

    @baseline_offset.setter
    def baseline_offset(self, value):
        """Alias for BaselineOffset.setter"""
        self.BaselineOffset = value

    @property
    def Bold(self):
        return self.com_object.Bold

    @Bold.setter
    def Bold(self, value):
        self.com_object.Bold = value

    @property
    def bold(self):
        """Alias for Bold"""
        return self.Bold

    @bold.setter
    def bold(self, value):
        """Alias for Bold.setter"""
        self.Bold = value

    @property
    def Caps(self):
        return self.com_object.Caps

    @Caps.setter
    def Caps(self, value):
        self.com_object.Caps = value

    @property
    def caps(self):
        """Alias for Caps"""
        return self.Caps

    @caps.setter
    def caps(self, value):
        """Alias for Caps.setter"""
        self.Caps = value

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def DoubleStrikeThrough(self):
        return self.com_object.DoubleStrikeThrough

    @DoubleStrikeThrough.setter
    def DoubleStrikeThrough(self, value):
        self.com_object.DoubleStrikeThrough = value

    @property
    def doublestrikethrough(self):
        """Alias for DoubleStrikeThrough"""
        return self.DoubleStrikeThrough

    @doublestrikethrough.setter
    def doublestrikethrough(self, value):
        """Alias for DoubleStrikeThrough.setter"""
        self.DoubleStrikeThrough = value

    @property
    def double_strike_through(self):
        """Alias for DoubleStrikeThrough"""
        return self.DoubleStrikeThrough

    @double_strike_through.setter
    def double_strike_through(self, value):
        """Alias for DoubleStrikeThrough.setter"""
        self.DoubleStrikeThrough = value

    @property
    def Embeddable(self):
        return self.com_object.Embeddable

    @property
    def embeddable(self):
        """Alias for Embeddable"""
        return self.Embeddable

    @property
    def Embedded(self):
        return self.com_object.Embedded

    @property
    def embedded(self):
        """Alias for Embedded"""
        return self.Embedded

    @property
    def Equalize(self):
        return self.com_object.Equalize

    @Equalize.setter
    def Equalize(self, value):
        self.com_object.Equalize = value

    @property
    def equalize(self):
        """Alias for Equalize"""
        return self.Equalize

    @equalize.setter
    def equalize(self, value):
        """Alias for Equalize.setter"""
        self.Equalize = value

    @property
    def Fill(self):
        return self.com_object.Fill

    @property
    def fill(self):
        """Alias for Fill"""
        return self.Fill

    @property
    def Glow(self):
        return self.com_object.Glow

    @property
    def glow(self):
        """Alias for Glow"""
        return self.Glow

    @property
    def Highlight(self):
        return self.com_object.Highlight

    @property
    def highlight(self):
        """Alias for Highlight"""
        return self.Highlight

    @property
    def Italic(self):
        return self.com_object.Italic

    @Italic.setter
    def Italic(self, value):
        self.com_object.Italic = value

    @property
    def italic(self):
        """Alias for Italic"""
        return self.Italic

    @italic.setter
    def italic(self, value):
        """Alias for Italic.setter"""
        self.Italic = value

    @property
    def Kerning(self):
        return self.com_object.Kerning

    @Kerning.setter
    def Kerning(self, value):
        self.com_object.Kerning = value

    @property
    def kerning(self):
        """Alias for Kerning"""
        return self.Kerning

    @kerning.setter
    def kerning(self, value):
        """Alias for Kerning.setter"""
        self.Kerning = value

    @property
    def Line(self):
        return self.com_object.Line

    @property
    def line(self):
        """Alias for Line"""
        return self.Line

    @property
    def Name(self):
        return self.com_object.Name

    @Name.setter
    def Name(self, value):
        self.com_object.Name = value

    @property
    def name(self):
        """Alias for Name"""
        return self.Name

    @name.setter
    def name(self, value):
        """Alias for Name.setter"""
        self.Name = value

    @property
    def NameAscii(self):
        return self.com_object.NameAscii

    @NameAscii.setter
    def NameAscii(self, value):
        self.com_object.NameAscii = value

    @property
    def nameascii(self):
        """Alias for NameAscii"""
        return self.NameAscii

    @nameascii.setter
    def nameascii(self, value):
        """Alias for NameAscii.setter"""
        self.NameAscii = value

    @property
    def name_ascii(self):
        """Alias for NameAscii"""
        return self.NameAscii

    @name_ascii.setter
    def name_ascii(self, value):
        """Alias for NameAscii.setter"""
        self.NameAscii = value

    @property
    def NameComplexScript(self):
        return self.com_object.NameComplexScript

    @NameComplexScript.setter
    def NameComplexScript(self, value):
        self.com_object.NameComplexScript = value

    @property
    def namecomplexscript(self):
        """Alias for NameComplexScript"""
        return self.NameComplexScript

    @namecomplexscript.setter
    def namecomplexscript(self, value):
        """Alias for NameComplexScript.setter"""
        self.NameComplexScript = value

    @property
    def name_complex_script(self):
        """Alias for NameComplexScript"""
        return self.NameComplexScript

    @name_complex_script.setter
    def name_complex_script(self, value):
        """Alias for NameComplexScript.setter"""
        self.NameComplexScript = value

    @property
    def NameFarEast(self):
        return self.com_object.NameFarEast

    @NameFarEast.setter
    def NameFarEast(self, value):
        self.com_object.NameFarEast = value

    @property
    def namefareast(self):
        """Alias for NameFarEast"""
        return self.NameFarEast

    @namefareast.setter
    def namefareast(self, value):
        """Alias for NameFarEast.setter"""
        self.NameFarEast = value

    @property
    def name_far_east(self):
        """Alias for NameFarEast"""
        return self.NameFarEast

    @name_far_east.setter
    def name_far_east(self, value):
        """Alias for NameFarEast.setter"""
        self.NameFarEast = value

    @property
    def NameOther(self):
        return self.com_object.NameOther

    @NameOther.setter
    def NameOther(self, value):
        self.com_object.NameOther = value

    @property
    def nameother(self):
        """Alias for NameOther"""
        return self.NameOther

    @nameother.setter
    def nameother(self, value):
        """Alias for NameOther.setter"""
        self.NameOther = value

    @property
    def name_other(self):
        """Alias for NameOther"""
        return self.NameOther

    @name_other.setter
    def name_other(self, value):
        """Alias for NameOther.setter"""
        self.NameOther = value

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    @property
    def Reflection(self):
        return self.com_object.Reflection

    @property
    def reflection(self):
        """Alias for Reflection"""
        return self.Reflection

    @property
    def Shadow(self):
        return self.com_object.Shadow

    @property
    def shadow(self):
        """Alias for Shadow"""
        return self.Shadow

    @property
    def Size(self):
        return self.com_object.Size

    @Size.setter
    def Size(self, value):
        self.com_object.Size = value

    @property
    def size(self):
        """Alias for Size"""
        return self.Size

    @size.setter
    def size(self, value):
        """Alias for Size.setter"""
        self.Size = value

    @property
    def Smallcaps(self):
        return self.com_object.Smallcaps

    @Smallcaps.setter
    def Smallcaps(self, value):
        self.com_object.Smallcaps = value

    @property
    def smallcaps(self):
        """Alias for Smallcaps"""
        return self.Smallcaps

    @smallcaps.setter
    def smallcaps(self, value):
        """Alias for Smallcaps.setter"""
        self.Smallcaps = value

    @property
    def SoftEdgeFormat(self):
        return self.com_object.SoftEdgeFormat

    @SoftEdgeFormat.setter
    def SoftEdgeFormat(self, value):
        self.com_object.SoftEdgeFormat = value

    @property
    def softedgeformat(self):
        """Alias for SoftEdgeFormat"""
        return self.SoftEdgeFormat

    @softedgeformat.setter
    def softedgeformat(self, value):
        """Alias for SoftEdgeFormat.setter"""
        self.SoftEdgeFormat = value

    @property
    def soft_edge_format(self):
        """Alias for SoftEdgeFormat"""
        return self.SoftEdgeFormat

    @soft_edge_format.setter
    def soft_edge_format(self, value):
        """Alias for SoftEdgeFormat.setter"""
        self.SoftEdgeFormat = value

    @property
    def Spacing(self):
        return self.com_object.Spacing

    @Spacing.setter
    def Spacing(self, value):
        self.com_object.Spacing = value

    @property
    def spacing(self):
        """Alias for Spacing"""
        return self.Spacing

    @spacing.setter
    def spacing(self, value):
        """Alias for Spacing.setter"""
        self.Spacing = value

    @property
    def Strike(self):
        return self.com_object.Strike

    @Strike.setter
    def Strike(self, value):
        self.com_object.Strike = value

    @property
    def strike(self):
        """Alias for Strike"""
        return self.Strike

    @strike.setter
    def strike(self, value):
        """Alias for Strike.setter"""
        self.Strike = value

    @property
    def StrikeThrough(self):
        return self.com_object.StrikeThrough

    @StrikeThrough.setter
    def StrikeThrough(self, value):
        self.com_object.StrikeThrough = value

    @property
    def strikethrough(self):
        """Alias for StrikeThrough"""
        return self.StrikeThrough

    @strikethrough.setter
    def strikethrough(self, value):
        """Alias for StrikeThrough.setter"""
        self.StrikeThrough = value

    @property
    def strike_through(self):
        """Alias for StrikeThrough"""
        return self.StrikeThrough

    @strike_through.setter
    def strike_through(self, value):
        """Alias for StrikeThrough.setter"""
        self.StrikeThrough = value

    @property
    def Subscript(self):
        return self.com_object.Subscript

    @Subscript.setter
    def Subscript(self, value):
        self.com_object.Subscript = value

    @property
    def subscript(self):
        """Alias for Subscript"""
        return self.Subscript

    @subscript.setter
    def subscript(self, value):
        """Alias for Subscript.setter"""
        self.Subscript = value

    @property
    def Superscript(self):
        return self.com_object.Superscript

    @Superscript.setter
    def Superscript(self, value):
        self.com_object.Superscript = value

    @property
    def superscript(self):
        """Alias for Superscript"""
        return self.Superscript

    @superscript.setter
    def superscript(self, value):
        """Alias for Superscript.setter"""
        self.Superscript = value

    @property
    def UnderlineColor(self):
        return self.com_object.UnderlineColor

    @property
    def underlinecolor(self):
        """Alias for UnderlineColor"""
        return self.UnderlineColor

    @property
    def underline_color(self):
        """Alias for UnderlineColor"""
        return self.UnderlineColor

    @property
    def UnderlineStyle(self):
        return self.com_object.UnderlineStyle

    @UnderlineStyle.setter
    def UnderlineStyle(self, value):
        self.com_object.UnderlineStyle = value

    @property
    def underlinestyle(self):
        """Alias for UnderlineStyle"""
        return self.UnderlineStyle

    @underlinestyle.setter
    def underlinestyle(self, value):
        """Alias for UnderlineStyle.setter"""
        self.UnderlineStyle = value

    @property
    def underline_style(self):
        """Alias for UnderlineStyle"""
        return self.UnderlineStyle

    @underline_style.setter
    def underline_style(self, value):
        """Alias for UnderlineStyle.setter"""
        self.UnderlineStyle = value

    @property
    def WordArtformat(self):
        return self.com_object.WordArtformat

    @WordArtformat.setter
    def WordArtformat(self, value):
        self.com_object.WordArtformat = value

    @property
    def wordartformat(self):
        """Alias for WordArtformat"""
        return self.WordArtformat

    @wordartformat.setter
    def wordartformat(self, value):
        """Alias for WordArtformat.setter"""
        self.WordArtformat = value

    @property
    def word_artformat(self):
        """Alias for WordArtformat"""
        return self.WordArtformat

    @word_artformat.setter
    def word_artformat(self, value):
        """Alias for WordArtformat.setter"""
        self.WordArtformat = value


class GlowFormat:

    def __init__(self, glowformat=None):
        self.com_object= glowformat

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Color(self):
        return self.com_object.Color

    @property
    def color(self):
        """Alias for Color"""
        return self.Color

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Radius(self):
        return self.com_object.Radius

    @Radius.setter
    def Radius(self, value):
        self.com_object.Radius = value

    @property
    def radius(self):
        """Alias for Radius"""
        return self.Radius

    @radius.setter
    def radius(self, value):
        """Alias for Radius.setter"""
        self.Radius = value

    @property
    def Transparency(self):
        return self.com_object.Transparency

    @Transparency.setter
    def Transparency(self, value):
        self.com_object.Transparency = value

    @property
    def transparency(self):
        """Alias for Transparency"""
        return self.Transparency

    @transparency.setter
    def transparency(self, value):
        """Alias for Transparency.setter"""
        self.Transparency = value


class GradientStop:

    def __init__(self, gradientstop=None):
        self.com_object= gradientstop

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Color(self):
        return self.com_object.Color

    @property
    def color(self):
        """Alias for Color"""
        return self.Color

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Position(self):
        return self.com_object.Position

    @Position.setter
    def Position(self, value):
        self.com_object.Position = value

    @property
    def position(self):
        """Alias for Position"""
        return self.Position

    @position.setter
    def position(self, value):
        """Alias for Position.setter"""
        self.Position = value

    @property
    def Transparency(self):
        return self.com_object.Transparency

    @Transparency.setter
    def Transparency(self, value):
        self.com_object.Transparency = value

    @property
    def transparency(self):
        """Alias for Transparency"""
        return self.Transparency

    @transparency.setter
    def transparency(self, value):
        """Alias for Transparency.setter"""
        self.Transparency = value


class GradientStops:

    def __init__(self, gradientstops=None):
        self.com_object= gradientstops

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        if hasattr(self.com_object, "GetItem"):
            return self.com_object.GetItem(*arguments)
        else:
            return self.com_object.Item(*arguments)

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)

    def Delete(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        return self.com_object.Delete(*arguments)

    def delete(self, Index=None):
        """Alias for Delete"""
        arguments = [Index]
        return self.Delete(*arguments)

    def Insert(self, RGB=None, Position=None, Transparency=None, Index=None):
        arguments = com_arguments([unwrap(a) for a in [RGB, Position, Transparency, Index]])
        return self.com_object.Insert(*arguments)

    def insert(self, RGB=None, Position=None, Transparency=None, Index=None):
        """Alias for Insert"""
        arguments = [RGB, Position, Transparency, Index]
        return self.Insert(*arguments)

    def Insert2(self, RGB=None, Position=None, Transparency=None, Index=None, Brightness=None):
        arguments = com_arguments([unwrap(a) for a in [RGB, Position, Transparency, Index, Brightness]])
        return self.com_object.Insert2(*arguments)

    def insert2(self, RGB=None, Position=None, Transparency=None, Index=None, Brightness=None):
        """Alias for Insert2"""
        arguments = [RGB, Position, Transparency, Index, Brightness]
        return self.Insert2(*arguments)


class IAssistance:

    def __init__(self, iassistance=None):
        self.com_object= iassistance

    def ClearDefaultContext(self, HelpId=None):
        arguments = com_arguments([unwrap(a) for a in [HelpId]])
        return self.com_object.ClearDefaultContext(*arguments)

    def cleardefaultcontext(self, HelpId=None):
        """Alias for ClearDefaultContext"""
        arguments = [HelpId]
        return self.ClearDefaultContext(*arguments)

    def clear_default_context(self, HelpId=None):
        """Alias for ClearDefaultContext"""
        arguments = [HelpId]
        return self.ClearDefaultContext(*arguments)

    def SearchHelp(self, Query=None, Scope=None):
        arguments = com_arguments([unwrap(a) for a in [Query, Scope]])
        return self.com_object.SearchHelp(*arguments)

    def searchhelp(self, Query=None, Scope=None):
        """Alias for SearchHelp"""
        arguments = [Query, Scope]
        return self.SearchHelp(*arguments)

    def search_help(self, Query=None, Scope=None):
        """Alias for SearchHelp"""
        arguments = [Query, Scope]
        return self.SearchHelp(*arguments)

    def SetDefaultContext(self, HelpId=None):
        arguments = com_arguments([unwrap(a) for a in [HelpId]])
        return self.com_object.SetDefaultContext(*arguments)

    def setdefaultcontext(self, HelpId=None):
        """Alias for SetDefaultContext"""
        arguments = [HelpId]
        return self.SetDefaultContext(*arguments)

    def set_default_context(self, HelpId=None):
        """Alias for SetDefaultContext"""
        arguments = [HelpId]
        return self.SetDefaultContext(*arguments)

    def ShowHelp(self, HelpId=None, Scope=None):
        arguments = com_arguments([unwrap(a) for a in [HelpId, Scope]])
        return self.com_object.ShowHelp(*arguments)

    def showhelp(self, HelpId=None, Scope=None):
        """Alias for ShowHelp"""
        arguments = [HelpId, Scope]
        return self.ShowHelp(*arguments)

    def show_help(self, HelpId=None, Scope=None):
        """Alias for ShowHelp"""
        arguments = [HelpId, Scope]
        return self.ShowHelp(*arguments)


class IBlogExtensibility:

    def __init__(self, iblogextensibility=None):
        self.com_object= iblogextensibility

    def BlogProviderProperties(self, BlogProvider=None, FriendlyName=None, CategorySupport=None, Padding=None, NoCredentials=None):
        arguments = com_arguments([unwrap(a) for a in [BlogProvider, FriendlyName, CategorySupport, Padding, NoCredentials]])
        return self.com_object.BlogProviderProperties(*arguments)

    def blogproviderproperties(self, BlogProvider=None, FriendlyName=None, CategorySupport=None, Padding=None, NoCredentials=None):
        """Alias for BlogProviderProperties"""
        arguments = [BlogProvider, FriendlyName, CategorySupport, Padding, NoCredentials]
        return self.BlogProviderProperties(*arguments)

    def blog_provider_properties(self, BlogProvider=None, FriendlyName=None, CategorySupport=None, Padding=None, NoCredentials=None):
        """Alias for BlogProviderProperties"""
        arguments = [BlogProvider, FriendlyName, CategorySupport, Padding, NoCredentials]
        return self.BlogProviderProperties(*arguments)

    def GetCategories(self, Account=None, ParentWindow=None, Document=None, userName=None, Password=None, Categories=None):
        arguments = com_arguments([unwrap(a) for a in [Account, ParentWindow, Document, userName, Password, Categories]])
        return self.com_object.GetCategories(*arguments)

    def getcategories(self, Account=None, ParentWindow=None, Document=None, userName=None, Password=None, Categories=None):
        """Alias for GetCategories"""
        arguments = [Account, ParentWindow, Document, userName, Password, Categories]
        return self.GetCategories(*arguments)

    def get_categories(self, Account=None, ParentWindow=None, Document=None, userName=None, Password=None, Categories=None):
        """Alias for GetCategories"""
        arguments = [Account, ParentWindow, Document, userName, Password, Categories]
        return self.GetCategories(*arguments)

    def GetRecentPosts(self, Account=None, ParentWindow=None, Document=None, userName=None, Password=None, PostTitles=None, PostDates=None, PostIDs=None):
        arguments = com_arguments([unwrap(a) for a in [Account, ParentWindow, Document, userName, Password, PostTitles, PostDates, PostIDs]])
        return self.com_object.GetRecentPosts(*arguments)

    def getrecentposts(self, Account=None, ParentWindow=None, Document=None, userName=None, Password=None, PostTitles=None, PostDates=None, PostIDs=None):
        """Alias for GetRecentPosts"""
        arguments = [Account, ParentWindow, Document, userName, Password, PostTitles, PostDates, PostIDs]
        return self.GetRecentPosts(*arguments)

    def get_recent_posts(self, Account=None, ParentWindow=None, Document=None, userName=None, Password=None, PostTitles=None, PostDates=None, PostIDs=None):
        """Alias for GetRecentPosts"""
        arguments = [Account, ParentWindow, Document, userName, Password, PostTitles, PostDates, PostIDs]
        return self.GetRecentPosts(*arguments)

    def GetUserBlogs(self, Account=None, ParentWindow=None, Document=None, userName=None, Password=None, BlogNames=None, BlogIDs=None, BlogURLs=None):
        arguments = com_arguments([unwrap(a) for a in [Account, ParentWindow, Document, userName, Password, BlogNames, BlogIDs, BlogURLs]])
        return self.com_object.GetUserBlogs(*arguments)

    def getuserblogs(self, Account=None, ParentWindow=None, Document=None, userName=None, Password=None, BlogNames=None, BlogIDs=None, BlogURLs=None):
        """Alias for GetUserBlogs"""
        arguments = [Account, ParentWindow, Document, userName, Password, BlogNames, BlogIDs, BlogURLs]
        return self.GetUserBlogs(*arguments)

    def get_user_blogs(self, Account=None, ParentWindow=None, Document=None, userName=None, Password=None, BlogNames=None, BlogIDs=None, BlogURLs=None):
        """Alias for GetUserBlogs"""
        arguments = [Account, ParentWindow, Document, userName, Password, BlogNames, BlogIDs, BlogURLs]
        return self.GetUserBlogs(*arguments)

    def Open(self, Account=None, PostID=None, ParentWindow=None, userName=None, Password=None, xHTML=None, Title=None, DatePosted=None, Categories=None):
        arguments = com_arguments([unwrap(a) for a in [Account, PostID, ParentWindow, userName, Password, xHTML, Title, DatePosted, Categories]])
        return self.com_object.Open(*arguments)

    def open(self, Account=None, PostID=None, ParentWindow=None, userName=None, Password=None, xHTML=None, Title=None, DatePosted=None, Categories=None):
        """Alias for Open"""
        arguments = [Account, PostID, ParentWindow, userName, Password, xHTML, Title, DatePosted, Categories]
        return self.Open(*arguments)

    def PublishPost(self, Account=None, ParentWindow=None, Document=None, userName=None, Password=None, xHTML=None, Title=None, DateTime=None, Categories=None, Draft=None, PostID=None, PublishMessage=None):
        arguments = com_arguments([unwrap(a) for a in [Account, ParentWindow, Document, userName, Password, xHTML, Title, DateTime, Categories, Draft, PostID, PublishMessage]])
        return self.com_object.PublishPost(*arguments)

    def publishpost(self, Account=None, ParentWindow=None, Document=None, userName=None, Password=None, xHTML=None, Title=None, DateTime=None, Categories=None, Draft=None, PostID=None, PublishMessage=None):
        """Alias for PublishPost"""
        arguments = [Account, ParentWindow, Document, userName, Password, xHTML, Title, DateTime, Categories, Draft, PostID, PublishMessage]
        return self.PublishPost(*arguments)

    def publish_post(self, Account=None, ParentWindow=None, Document=None, userName=None, Password=None, xHTML=None, Title=None, DateTime=None, Categories=None, Draft=None, PostID=None, PublishMessage=None):
        """Alias for PublishPost"""
        arguments = [Account, ParentWindow, Document, userName, Password, xHTML, Title, DateTime, Categories, Draft, PostID, PublishMessage]
        return self.PublishPost(*arguments)

    def RepublishPost(self, Account=None, ParentWindow=None, Document=None, userName=None, Password=None, PostID=None, xHTML=None, Title=None, DateTime=None, Categories=None, Draft=None, PublishMessage=None):
        arguments = com_arguments([unwrap(a) for a in [Account, ParentWindow, Document, userName, Password, PostID, xHTML, Title, DateTime, Categories, Draft, PublishMessage]])
        return self.com_object.RepublishPost(*arguments)

    def republishpost(self, Account=None, ParentWindow=None, Document=None, userName=None, Password=None, PostID=None, xHTML=None, Title=None, DateTime=None, Categories=None, Draft=None, PublishMessage=None):
        """Alias for RepublishPost"""
        arguments = [Account, ParentWindow, Document, userName, Password, PostID, xHTML, Title, DateTime, Categories, Draft, PublishMessage]
        return self.RepublishPost(*arguments)

    def republish_post(self, Account=None, ParentWindow=None, Document=None, userName=None, Password=None, PostID=None, xHTML=None, Title=None, DateTime=None, Categories=None, Draft=None, PublishMessage=None):
        """Alias for RepublishPost"""
        arguments = [Account, ParentWindow, Document, userName, Password, PostID, xHTML, Title, DateTime, Categories, Draft, PublishMessage]
        return self.RepublishPost(*arguments)

    def SetupBlogAccount(self, Account=None, ParentWindow=None, Document=None, NewAccount=None, ShowPictureUI=None):
        arguments = com_arguments([unwrap(a) for a in [Account, ParentWindow, Document, NewAccount, ShowPictureUI]])
        return self.com_object.SetupBlogAccount(*arguments)

    def setupblogaccount(self, Account=None, ParentWindow=None, Document=None, NewAccount=None, ShowPictureUI=None):
        """Alias for SetupBlogAccount"""
        arguments = [Account, ParentWindow, Document, NewAccount, ShowPictureUI]
        return self.SetupBlogAccount(*arguments)

    def setup_blog_account(self, Account=None, ParentWindow=None, Document=None, NewAccount=None, ShowPictureUI=None):
        """Alias for SetupBlogAccount"""
        arguments = [Account, ParentWindow, Document, NewAccount, ShowPictureUI]
        return self.SetupBlogAccount(*arguments)


class IBlogPictureExtensibility:

    def __init__(self, iblogpictureextensibility=None):
        self.com_object= iblogpictureextensibility

    def BlogPictureProviderProperties(self, BlogPictureProvider=None, FriendlyName=None):
        arguments = com_arguments([unwrap(a) for a in [BlogPictureProvider, FriendlyName]])
        return self.com_object.BlogPictureProviderProperties(*arguments)

    def blogpictureproviderproperties(self, BlogPictureProvider=None, FriendlyName=None):
        """Alias for BlogPictureProviderProperties"""
        arguments = [BlogPictureProvider, FriendlyName]
        return self.BlogPictureProviderProperties(*arguments)

    def blog_picture_provider_properties(self, BlogPictureProvider=None, FriendlyName=None):
        """Alias for BlogPictureProviderProperties"""
        arguments = [BlogPictureProvider, FriendlyName]
        return self.BlogPictureProviderProperties(*arguments)

    def CreatePictureAccount(self, Account=None, BlogProvider=None, ParentWindow=None, Document=None, userName=None, Password=None):
        arguments = com_arguments([unwrap(a) for a in [Account, BlogProvider, ParentWindow, Document, userName, Password]])
        return self.com_object.CreatePictureAccount(*arguments)

    def createpictureaccount(self, Account=None, BlogProvider=None, ParentWindow=None, Document=None, userName=None, Password=None):
        """Alias for CreatePictureAccount"""
        arguments = [Account, BlogProvider, ParentWindow, Document, userName, Password]
        return self.CreatePictureAccount(*arguments)

    def create_picture_account(self, Account=None, BlogProvider=None, ParentWindow=None, Document=None, userName=None, Password=None):
        """Alias for CreatePictureAccount"""
        arguments = [Account, BlogProvider, ParentWindow, Document, userName, Password]
        return self.CreatePictureAccount(*arguments)

    def PublishPicture(self, Account=None, ParentWindow=None, Document=None, userName=None, Password=None, Image=None, PictureURI=None):
        arguments = com_arguments([unwrap(a) for a in [Account, ParentWindow, Document, userName, Password, Image, PictureURI]])
        return self.com_object.PublishPicture(*arguments)

    def publishpicture(self, Account=None, ParentWindow=None, Document=None, userName=None, Password=None, Image=None, PictureURI=None):
        """Alias for PublishPicture"""
        arguments = [Account, ParentWindow, Document, userName, Password, Image, PictureURI]
        return self.PublishPicture(*arguments)

    def publish_picture(self, Account=None, ParentWindow=None, Document=None, userName=None, Password=None, Image=None, PictureURI=None):
        """Alias for PublishPicture"""
        arguments = [Account, ParentWindow, Document, userName, Password, Image, PictureURI]
        return self.PublishPicture(*arguments)


class IConverter:

    def __init__(self, iconverter=None):
        self.com_object= iconverter

    def HrExport(self, bstrSourcePath=None, bstrDestPath=None, bstrClass=None, pcap=None, ppcp=None, pcuic=None):
        arguments = com_arguments([unwrap(a) for a in [bstrSourcePath, bstrDestPath, bstrClass, pcap, ppcp, pcuic]])
        return self.com_object.HrExport(*arguments)

    def hrexport(self, bstrSourcePath=None, bstrDestPath=None, bstrClass=None, pcap=None, ppcp=None, pcuic=None):
        """Alias for HrExport"""
        arguments = [bstrSourcePath, bstrDestPath, bstrClass, pcap, ppcp, pcuic]
        return self.HrExport(*arguments)

    def hr_export(self, bstrSourcePath=None, bstrDestPath=None, bstrClass=None, pcap=None, ppcp=None, pcuic=None):
        """Alias for HrExport"""
        arguments = [bstrSourcePath, bstrDestPath, bstrClass, pcap, ppcp, pcuic]
        return self.HrExport(*arguments)

    def HrGetErrorString(self, hrErr=None, pbstrErrorMsg=None, pcap=None):
        arguments = com_arguments([unwrap(a) for a in [hrErr, pbstrErrorMsg, pcap]])
        return self.com_object.HrGetErrorString(*arguments)

    def hrgeterrorstring(self, hrErr=None, pbstrErrorMsg=None, pcap=None):
        """Alias for HrGetErrorString"""
        arguments = [hrErr, pbstrErrorMsg, pcap]
        return self.HrGetErrorString(*arguments)

    def hr_get_error_string(self, hrErr=None, pbstrErrorMsg=None, pcap=None):
        """Alias for HrGetErrorString"""
        arguments = [hrErr, pbstrErrorMsg, pcap]
        return self.HrGetErrorString(*arguments)

    def HrGetFormat(self, bstrPath=None, pbstrClass=None, pcap=None, ppcp=None, pcuic=None):
        arguments = com_arguments([unwrap(a) for a in [bstrPath, pbstrClass, pcap, ppcp, pcuic]])
        return self.com_object.HrGetFormat(*arguments)

    def hrgetformat(self, bstrPath=None, pbstrClass=None, pcap=None, ppcp=None, pcuic=None):
        """Alias for HrGetFormat"""
        arguments = [bstrPath, pbstrClass, pcap, ppcp, pcuic]
        return self.HrGetFormat(*arguments)

    def hr_get_format(self, bstrPath=None, pbstrClass=None, pcap=None, ppcp=None, pcuic=None):
        """Alias for HrGetFormat"""
        arguments = [bstrPath, pbstrClass, pcap, ppcp, pcuic]
        return self.HrGetFormat(*arguments)

    def HrImport(self, bstrSourcePath=None, bstrDestPath=None, pcap=None, ppcp=None, pcuic=None):
        arguments = com_arguments([unwrap(a) for a in [bstrSourcePath, bstrDestPath, pcap, ppcp, pcuic]])
        return self.com_object.HrImport(*arguments)

    def hrimport(self, bstrSourcePath=None, bstrDestPath=None, pcap=None, ppcp=None, pcuic=None):
        """Alias for HrImport"""
        arguments = [bstrSourcePath, bstrDestPath, pcap, ppcp, pcuic]
        return self.HrImport(*arguments)

    def hr_import(self, bstrSourcePath=None, bstrDestPath=None, pcap=None, ppcp=None, pcuic=None):
        """Alias for HrImport"""
        arguments = [bstrSourcePath, bstrDestPath, pcap, ppcp, pcuic]
        return self.HrImport(*arguments)

    def HrInitConverter(self, pcap=None, ppcp=None, pcuic=None):
        arguments = com_arguments([unwrap(a) for a in [pcap, ppcp, pcuic]])
        return self.com_object.HrInitConverter(*arguments)

    def hrinitconverter(self, pcap=None, ppcp=None, pcuic=None):
        """Alias for HrInitConverter"""
        arguments = [pcap, ppcp, pcuic]
        return self.HrInitConverter(*arguments)

    def hr_init_converter(self, pcap=None, ppcp=None, pcuic=None):
        """Alias for HrInitConverter"""
        arguments = [pcap, ppcp, pcuic]
        return self.HrInitConverter(*arguments)

    def HrUninitConverter(self, pcuic=None):
        arguments = com_arguments([unwrap(a) for a in [pcuic]])
        return self.com_object.HrUninitConverter(*arguments)

    def hruninitconverter(self, pcuic=None):
        """Alias for HrUninitConverter"""
        arguments = [pcuic]
        return self.HrUninitConverter(*arguments)

    def hr_uninit_converter(self, pcuic=None):
        """Alias for HrUninitConverter"""
        arguments = [pcuic]
        return self.HrUninitConverter(*arguments)


class IConverterApplicationPreferences:

    def __init__(self, iconverterapplicationpreferences=None):
        self.com_object= iconverterapplicationpreferences

    def HrCheckFormat(self, pFormat=None):
        arguments = com_arguments([unwrap(a) for a in [pFormat]])
        return self.com_object.HrCheckFormat(*arguments)

    def hrcheckformat(self, pFormat=None):
        """Alias for HrCheckFormat"""
        arguments = [pFormat]
        return self.HrCheckFormat(*arguments)

    def hr_check_format(self, pFormat=None):
        """Alias for HrCheckFormat"""
        arguments = [pFormat]
        return self.HrCheckFormat(*arguments)

    def HrGetApplication(self, pbstrApplication=None):
        arguments = com_arguments([unwrap(a) for a in [pbstrApplication]])
        return self.com_object.HrGetApplication(*arguments)

    def hrgetapplication(self, pbstrApplication=None):
        """Alias for HrGetApplication"""
        arguments = [pbstrApplication]
        return self.HrGetApplication(*arguments)

    def hr_get_application(self, pbstrApplication=None):
        """Alias for HrGetApplication"""
        arguments = [pbstrApplication]
        return self.HrGetApplication(*arguments)

    def HrGetHwnd(self, phwnd=None):
        arguments = com_arguments([unwrap(a) for a in [phwnd]])
        return self.com_object.HrGetHwnd(*arguments)

    def hrgethwnd(self, phwnd=None):
        """Alias for HrGetHwnd"""
        arguments = [phwnd]
        return self.HrGetHwnd(*arguments)

    def hr_get_hwnd(self, phwnd=None):
        """Alias for HrGetHwnd"""
        arguments = [phwnd]
        return self.HrGetHwnd(*arguments)

    def HrGetLcid(self, plcid=None):
        arguments = com_arguments([unwrap(a) for a in [plcid]])
        return self.com_object.HrGetLcid(*arguments)

    def hrgetlcid(self, plcid=None):
        """Alias for HrGetLcid"""
        arguments = [plcid]
        return self.HrGetLcid(*arguments)

    def hr_get_lcid(self, plcid=None):
        """Alias for HrGetLcid"""
        arguments = [plcid]
        return self.HrGetLcid(*arguments)


class IConverterPreferences:

    def __init__(self, iconverterpreferences=None):
        self.com_object= iconverterpreferences

    def HrCheckFormat(self, pFormat=None):
        arguments = com_arguments([unwrap(a) for a in [pFormat]])
        return self.com_object.HrCheckFormat(*arguments)

    def hrcheckformat(self, pFormat=None):
        """Alias for HrCheckFormat"""
        arguments = [pFormat]
        return self.HrCheckFormat(*arguments)

    def hr_check_format(self, pFormat=None):
        """Alias for HrCheckFormat"""
        arguments = [pFormat]
        return self.HrCheckFormat(*arguments)

    def HrGetLossySave(self, pfLossySave=None):
        arguments = com_arguments([unwrap(a) for a in [pfLossySave]])
        return self.com_object.HrGetLossySave(*arguments)

    def hrgetlossysave(self, pfLossySave=None):
        """Alias for HrGetLossySave"""
        arguments = [pfLossySave]
        return self.HrGetLossySave(*arguments)

    def hr_get_lossy_save(self, pfLossySave=None):
        """Alias for HrGetLossySave"""
        arguments = [pfLossySave]
        return self.HrGetLossySave(*arguments)

    def HrGetMacroEnabled(self, pfMacroEnabled=None):
        arguments = com_arguments([unwrap(a) for a in [pfMacroEnabled]])
        return self.com_object.HrGetMacroEnabled(*arguments)

    def hrgetmacroenabled(self, pfMacroEnabled=None):
        """Alias for HrGetMacroEnabled"""
        arguments = [pfMacroEnabled]
        return self.HrGetMacroEnabled(*arguments)

    def hr_get_macro_enabled(self, pfMacroEnabled=None):
        """Alias for HrGetMacroEnabled"""
        arguments = [pfMacroEnabled]
        return self.HrGetMacroEnabled(*arguments)


class IConverterUICallback:

    def __init__(self, iconverteruicallback=None):
        self.com_object= iconverteruicallback

    def HrInputBox(self, bstrText=None, bstrCaption=None, pbstrInput=None, fPassword=None):
        arguments = com_arguments([unwrap(a) for a in [bstrText, bstrCaption, pbstrInput, fPassword]])
        return self.com_object.HrInputBox(*arguments)

    def hrinputbox(self, bstrText=None, bstrCaption=None, pbstrInput=None, fPassword=None):
        """Alias for HrInputBox"""
        arguments = [bstrText, bstrCaption, pbstrInput, fPassword]
        return self.HrInputBox(*arguments)

    def hr_input_box(self, bstrText=None, bstrCaption=None, pbstrInput=None, fPassword=None):
        """Alias for HrInputBox"""
        arguments = [bstrText, bstrCaption, pbstrInput, fPassword]
        return self.HrInputBox(*arguments)

    def HrMessageBox(self, bstrText=None, bstrCaption=None, uType=None, pidResult=None):
        arguments = com_arguments([unwrap(a) for a in [bstrText, bstrCaption, uType, pidResult]])
        return self.com_object.HrMessageBox(*arguments)

    def hrmessagebox(self, bstrText=None, bstrCaption=None, uType=None, pidResult=None):
        """Alias for HrMessageBox"""
        arguments = [bstrText, bstrCaption, uType, pidResult]
        return self.HrMessageBox(*arguments)

    def hr_message_box(self, bstrText=None, bstrCaption=None, uType=None, pidResult=None):
        """Alias for HrMessageBox"""
        arguments = [bstrText, bstrCaption, uType, pidResult]
        return self.HrMessageBox(*arguments)

    def HrReportProgress(self, uPercentComplete=None):
        arguments = com_arguments([unwrap(a) for a in [uPercentComplete]])
        return self.com_object.HrReportProgress(*arguments)

    def hrreportprogress(self, uPercentComplete=None):
        """Alias for HrReportProgress"""
        arguments = [uPercentComplete]
        return self.HrReportProgress(*arguments)

    def hr_report_progress(self, uPercentComplete=None):
        """Alias for HrReportProgress"""
        arguments = [uPercentComplete]
        return self.HrReportProgress(*arguments)


class ICTPFactory:

    def __init__(self, ictpfactory=None):
        self.com_object= ictpfactory

    def CreateCTP(self, CTPAxID=None, CTPTitle=None, CTPParentWindow=None):
        arguments = com_arguments([unwrap(a) for a in [CTPAxID, CTPTitle, CTPParentWindow]])
        return CustomTaskPane(self.com_object.CreateCTP(*arguments))

    def createctp(self, CTPAxID=None, CTPTitle=None, CTPParentWindow=None):
        """Alias for CreateCTP"""
        arguments = [CTPAxID, CTPTitle, CTPParentWindow]
        return self.CreateCTP(*arguments)

    def create_c_t_p(self, CTPAxID=None, CTPTitle=None, CTPParentWindow=None):
        """Alias for CreateCTP"""
        arguments = [CTPAxID, CTPTitle, CTPParentWindow]
        return self.CreateCTP(*arguments)


class ICustomTaskPaneConsumer:

    def __init__(self, icustomtaskpaneconsumer=None):
        self.com_object= icustomtaskpaneconsumer

    def CTPFactoryAvailable(self, CTPFactoryInst=None):
        arguments = com_arguments([unwrap(a) for a in [CTPFactoryInst]])
        return self.com_object.CTPFactoryAvailable(*arguments)

    def ctpfactoryavailable(self, CTPFactoryInst=None):
        """Alias for CTPFactoryAvailable"""
        arguments = [CTPFactoryInst]
        return self.CTPFactoryAvailable(*arguments)

    def c_t_p_factory_available(self, CTPFactoryInst=None):
        """Alias for CTPFactoryAvailable"""
        arguments = [CTPFactoryInst]
        return self.CTPFactoryAvailable(*arguments)


class IDocumentInspector:

    def __init__(self, idocumentinspector=None):
        self.com_object= idocumentinspector

    def Fix(self, Doc=None, Hwnd=None, Status=None, Result=None):
        arguments = com_arguments([unwrap(a) for a in [Doc, Hwnd, Status, Result]])
        return self.com_object.Fix(*arguments)

    def fix(self, Doc=None, Hwnd=None, Status=None, Result=None):
        """Alias for Fix"""
        arguments = [Doc, Hwnd, Status, Result]
        return self.Fix(*arguments)

    def GetInfo(self, Name=None, Desc=None):
        arguments = com_arguments([unwrap(a) for a in [Name, Desc]])
        return self.com_object.GetInfo(*arguments)

    def getinfo(self, Name=None, Desc=None):
        """Alias for GetInfo"""
        arguments = [Name, Desc]
        return self.GetInfo(*arguments)

    def get_info(self, Name=None, Desc=None):
        """Alias for GetInfo"""
        arguments = [Name, Desc]
        return self.GetInfo(*arguments)

    def Inspect(self, Doc=None, Status=None, Result=None, Action=None):
        arguments = com_arguments([unwrap(a) for a in [Doc, Status, Result, Action]])
        return self.com_object.Inspect(*arguments)

    def inspect(self, Doc=None, Status=None, Result=None, Action=None):
        """Alias for Inspect"""
        arguments = [Doc, Status, Result, Action]
        return self.Inspect(*arguments)


class IMsoContactCard:

    def __init__(self, imsocontactcard=None):
        self.com_object= imsocontactcard

    @property
    def Address(self):
        return self.com_object.Address

    @property
    def address(self):
        """Alias for Address"""
        return self.Address

    @property
    def AddressType(self):
        return self.com_object.AddressType

    @property
    def addresstype(self):
        """Alias for AddressType"""
        return self.AddressType

    @property
    def address_type(self):
        """Alias for AddressType"""
        return self.AddressType

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def CardType(self):
        return self.com_object.CardType

    @property
    def cardtype(self):
        """Alias for CardType"""
        return self.CardType

    @property
    def card_type(self):
        """Alias for CardType"""
        return self.CardType

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent


class IRibbonControl:

    def __init__(self, iribboncontrol=None):
        self.com_object= iribboncontrol

    @property
    def Context(self):
        return self.com_object.Context

    @property
    def context(self):
        """Alias for Context"""
        return self.Context

    @property
    def Id(self):
        return self.com_object.Id

    @property
    def id(self):
        """Alias for Id"""
        return self.Id

    @property
    def Tag(self):
        return self.com_object.Tag

    @property
    def tag(self):
        """Alias for Tag"""
        return self.Tag


class IRibbonExtensibility:

    def __init__(self, iribbonextensibility=None):
        self.com_object= iribbonextensibility

    def GetCustomUI(self, RibbonID=None):
        arguments = com_arguments([unwrap(a) for a in [RibbonID]])
        return self.com_object.GetCustomUI(*arguments)

    def getcustomui(self, RibbonID=None):
        """Alias for GetCustomUI"""
        arguments = [RibbonID]
        return self.GetCustomUI(*arguments)

    def get_custom_u_i(self, RibbonID=None):
        """Alias for GetCustomUI"""
        arguments = [RibbonID]
        return self.GetCustomUI(*arguments)


class IRibbonUI:

    def __init__(self, iribbonui=None):
        self.com_object= iribbonui

    def ActivateTab(self, ControlID=None):
        arguments = com_arguments([unwrap(a) for a in [ControlID]])
        return self.com_object.ActivateTab(*arguments)

    def activatetab(self, ControlID=None):
        """Alias for ActivateTab"""
        arguments = [ControlID]
        return self.ActivateTab(*arguments)

    def activate_tab(self, ControlID=None):
        """Alias for ActivateTab"""
        arguments = [ControlID]
        return self.ActivateTab(*arguments)

    def ActivateTabMso(self, ControlID=None):
        arguments = com_arguments([unwrap(a) for a in [ControlID]])
        return self.com_object.ActivateTabMso(*arguments)

    def activatetabmso(self, ControlID=None):
        """Alias for ActivateTabMso"""
        arguments = [ControlID]
        return self.ActivateTabMso(*arguments)

    def activate_tab_mso(self, ControlID=None):
        """Alias for ActivateTabMso"""
        arguments = [ControlID]
        return self.ActivateTabMso(*arguments)

    def ActivateTabQ(self, ControlID=None, Namespace=None):
        arguments = com_arguments([unwrap(a) for a in [ControlID, Namespace]])
        return self.com_object.ActivateTabQ(*arguments)

    def activatetabq(self, ControlID=None, Namespace=None):
        """Alias for ActivateTabQ"""
        arguments = [ControlID, Namespace]
        return self.ActivateTabQ(*arguments)

    def activate_tab_q(self, ControlID=None, Namespace=None):
        """Alias for ActivateTabQ"""
        arguments = [ControlID, Namespace]
        return self.ActivateTabQ(*arguments)

    def Invalidate(self):
        return self.com_object.Invalidate()

    def invalidate(self):
        """Alias for Invalidate"""
        return self.Invalidate()

    def InvalidateControl(self, bstrControlID=None):
        arguments = com_arguments([unwrap(a) for a in [bstrControlID]])
        return self.com_object.InvalidateControl(*arguments)

    def invalidatecontrol(self, bstrControlID=None):
        """Alias for InvalidateControl"""
        arguments = [bstrControlID]
        return self.InvalidateControl(*arguments)

    def invalidate_control(self, bstrControlID=None):
        """Alias for InvalidateControl"""
        arguments = [bstrControlID]
        return self.InvalidateControl(*arguments)

    def InvalidateControlMso(self, ControlID=None):
        arguments = com_arguments([unwrap(a) for a in [ControlID]])
        return self.com_object.InvalidateControlMso(*arguments)

    def invalidatecontrolmso(self, ControlID=None):
        """Alias for InvalidateControlMso"""
        arguments = [ControlID]
        return self.InvalidateControlMso(*arguments)

    def invalidate_control_mso(self, ControlID=None):
        """Alias for InvalidateControlMso"""
        arguments = [ControlID]
        return self.InvalidateControlMso(*arguments)


class LabelInfo:

    def __init__(self, labelinfo=None):
        self.com_object= labelinfo


class LanguageSettings:

    def __init__(self, languagesettings=None):
        self.com_object= languagesettings

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    def LanguageID(self, Id=None):
        arguments = com_arguments([unwrap(a) for a in [Id]])
        if hasattr(self.com_object, "GetLanguageID"):
            return self.com_object.GetLanguageID(*arguments)
        else:
            return self.com_object.LanguageID(*arguments)

    def languageid(self, Id=None):
        """Alias for LanguageID"""
        arguments = [Id]
        return self.LanguageID(*arguments)

    def language_i_d(self, Id=None):
        """Alias for LanguageID"""
        arguments = [Id]
        return self.LanguageID(*arguments)

    def LanguagePreferredForEditing(self, lid=None):
        arguments = com_arguments([unwrap(a) for a in [lid]])
        if hasattr(self.com_object, "GetLanguagePreferredForEditing"):
            return self.com_object.GetLanguagePreferredForEditing(*arguments)
        else:
            return self.com_object.LanguagePreferredForEditing(*arguments)

    def languagepreferredforediting(self, lid=None):
        """Alias for LanguagePreferredForEditing"""
        arguments = [lid]
        return self.LanguagePreferredForEditing(*arguments)

    def language_preferred_for_editing(self, lid=None):
        """Alias for LanguagePreferredForEditing"""
        arguments = [lid]
        return self.LanguagePreferredForEditing(*arguments)

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent


# MailFormat enumeration
mfHTML = 2
mfPlainText = 1
mfRTF = 3

class MetaProperties:

    def __init__(self, metaproperties=None):
        self.com_object= metaproperties

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        if hasattr(self.com_object, "GetItem"):
            return self.com_object.GetItem(*arguments)
        else:
            return self.com_object.Item(*arguments)

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    @property
    def SchemaXml(self):
        return self.com_object.SchemaXml

    @property
    def schemaxml(self):
        """Alias for SchemaXml"""
        return self.SchemaXml

    @property
    def schema_xml(self):
        """Alias for SchemaXml"""
        return self.SchemaXml

    def GetItemByInternalName(self, InternalName=None):
        arguments = com_arguments([unwrap(a) for a in [InternalName]])
        return MetaProperty(self.com_object.GetItemByInternalName(*arguments))

    def getitembyinternalname(self, InternalName=None):
        """Alias for GetItemByInternalName"""
        arguments = [InternalName]
        return self.GetItemByInternalName(*arguments)

    def get_item_by_internal_name(self, InternalName=None):
        """Alias for GetItemByInternalName"""
        arguments = [InternalName]
        return self.GetItemByInternalName(*arguments)

    def Validate(self):
        return self.com_object.Validate()

    def validate(self):
        """Alias for Validate"""
        return self.Validate()


class MetaProperty:

    def __init__(self, metaproperty=None):
        self.com_object= metaproperty

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Id(self):
        return self.com_object.Id

    @property
    def id(self):
        """Alias for Id"""
        return self.Id

    @property
    def IsReadOnly(self):
        return self.com_object.IsReadOnly

    @property
    def isreadonly(self):
        """Alias for IsReadOnly"""
        return self.IsReadOnly

    @property
    def is_read_only(self):
        """Alias for IsReadOnly"""
        return self.IsReadOnly

    @property
    def IsRequired(self):
        return self.com_object.IsRequired

    @property
    def isrequired(self):
        """Alias for IsRequired"""
        return self.IsRequired

    @property
    def is_required(self):
        """Alias for IsRequired"""
        return self.IsRequired

    @property
    def Name(self):
        return self.com_object.Name

    @property
    def name(self):
        """Alias for Name"""
        return self.Name

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    @property
    def Type(self):
        return self.com_object.Type

    @property
    def type(self):
        """Alias for Type"""
        return self.Type

    @property
    def Value(self):
        return self.com_object.Value

    @Value.setter
    def Value(self, value):
        self.com_object.Value = value

    @property
    def value(self):
        """Alias for Value"""
        return self.Value

    @value.setter
    def value(self, value):
        """Alias for Value.setter"""
        self.Value = value

    def Validate(self):
        return self.com_object.Validate()

    def validate(self):
        """Alias for Validate"""
        return self.Validate()


# MsoAlertCancelType enumeration
msoAlertCancelDefault = -1
msoAlertCancelFifth = 4
msoAlertCancelFirst = 0
msoAlertCancelFourth = 3
msoAlertCancelSecond = 1
msoAlertCancelThird = 2

# MsoAlertIconType enumeration
msoAlertIconCritical = 1
msoAlertIconInfo = 4
msoAlertIconNoIcon = 0
msoAlertIconQuery = 2
msoAlertIconWarning = 3

# MsoAlignCmd enumeration
msoAlignBottoms = 5
msoAlignCenters = 1
msoAlignLefts = 0
msoAlignMiddles = 4
msoAlignRights = 2
msoAlignTops = 3

# MsoAppLanguageID enumeration
msoLanguageIDExeMode = 4
msoLanguageIDHelp = 3
msoLanguageIDInstall = 1
msoLanguageIDUI = 2
msoLanguageIDUIPrevious = 5

# MsoArrowheadLength enumeration
msoArrowheadLengthMedium = 2
msoArrowheadLengthMixed = -2
msoArrowheadLong = 3
msoArrowheadShort = 1

# MsoArrowheadStyle enumeration
msoArrowheadDiamond = 5
msoArrowheadNone = 1
msoArrowheadOpen = 3
msoArrowheadOval = 6
msoArrowheadStealth = 4
msoArrowheadStyleMixed = -2
msoArrowheadTriangle = 2

# MsoArrowheadWidth enumeration
msoArrowheadNarrow = 1
msoArrowheadWide = 3
msoArrowheadWidthMedium = 2
msoArrowheadWidthMixed = -2

# MsoAutomationSecurity enumeration
msoAutomationSecurityByUI = 2
msoAutomationSecurityForceDisable = 3
msoAutomationSecurityLow = 1

# MsoAutoShapeType enumeration
msoShape10pointStar = 149
msoShape12pointStar = 150
msoShape16pointStar = 94
msoShape24pointStar = 95
msoShape32pointStar = 96
msoShape4pointStar = 91
msoShape5pointStar = 92
msoShape6pointStar = 147
msoShape7pointStar = 148
msoShape8pointStar = 93
msoShapeActionButtonBackorPrevious = 129
msoShapeActionButtonBeginning = 131
msoShapeActionButtonCustom = 125
msoShapeActionButtonDocument = 134
msoShapeActionButtonEnd = 132
msoShapeActionButtonForwardorNext = 130
msoShapeActionButtonHelp = 127
msoShapeActionButtonHome = 126
msoShapeActionButtonInformation = 128
msoShapeActionButtonMovie = 136
msoShapeActionButtonReturn = 133
msoShapeActionButtonSound = 135
msoShapeArc = 25
msoShapeBalloon = 137
msoShapeBentArrow = 41
msoShapeBentUpArrow = 44
msoShapeBevel = 15
msoShapeBlockArc = 20
msoShapeCan = 13
msoShapeChartPlus = 182
msoShapeChartStar = 181
msoShapeChartX = 180
msoShapeChevron = 52
msoShapeChord = 161
msoShapeCircularArrow = 60
msoShapeCloud = 179
msoShapeCloudCallout = 108
msoShapeCorner = 162
msoShapeCornerTabs = 169
msoShapeCross = 11
msoShapeCube = 14
msoShapeCurvedDownArrow = 48
msoShapeCurvedDownRibbon = 100
msoShapeCurvedLeftArrow = 46
msoShapeCurvedRightArrow = 45
msoShapeCurvedUpArrow = 47
msoShapeCurvedUpRibbon = 99
msoShapeDecagon = 144
msoShapeDiagonalStripe = 141
msoShapeDiamond = 4
msoShapeDodecagon = 146
msoShapeDonut = 18
msoShapeDoubleBrace = 27
msoShapeDoubleBracket = 26
msoShapeDoubleWave = 104
msoShapeDownArrow = 36
msoShapeDownArrowCallout = 56
msoShapeDownRibbon = 98
msoShapeExplosion1 = 89
msoShapeExplosion2 = 90
msoShapeFlowchartAlternateProcess = 62
msoShapeFlowchartCard = 75
msoShapeFlowchartCollate = 79
msoShapeFlowchartConnector = 73
msoShapeFlowchartData = 64
msoShapeFlowchartDecision = 63
msoShapeFlowchartDelay = 84
msoShapeFlowchartDirectAccessStorage = 87
msoShapeFlowchartDisplay = 88
msoShapeFlowchartDocument = 67
msoShapeFlowchartExtract = 81
msoShapeFlowchartInternalStorage = 66
msoShapeFlowchartMagneticDisk = 86
msoShapeFlowchartManualInput = 71
msoShapeFlowchartManualOperation = 72
msoShapeFlowchartMerge = 82
msoShapeFlowchartMultidocument = 68
msoShapeFlowchartOfflineStorage = 139
msoShapeFlowchartOffpageConnector = 74
msoShapeFlowchartOr = 78
msoShapeFlowchartPredefinedProcess = 65
msoShapeFlowchartPreparation = 70
msoShapeFlowchartProcess = 61
msoShapeFlowchartPunchedTape = 76
msoShapeFlowchartSequentialAccessStorage = 85
msoShapeFlowchartSort = 80
msoShapeFlowchartStoredData = 83
msoShapeFlowchartSummingJunction = 77
msoShapeFlowchartTerminator = 69
msoShapeFoldedCorner = 16
msoShapeFrame = 158
msoShapeFunnel = 174
msoShapeGear6 = 172
msoShapeGear9 = 173
msoShapeHalfFrame = 159
msoShapeHeart = 21
msoShapeHeptagon = 145
msoShapeHexagon = 10
msoShapeHorizontalScroll = 102
msoShapeIsoscelesTriangle = 7
msoShapeLeftArrow = 34
msoShapeLeftArrowCallout = 54
msoShapeLeftBrace = 31
msoShapeLeftBracket = 29
msoShapeLeftCircularArrow = 176
msoShapeLeftRightArrow = 37
msoShapeLeftRightArrowCallout = 57
msoShapeLeftRightCircularArrow = 177
msoShapeLeftRightRibbon = 140
msoShapeLeftRightUpArrow = 40
msoShapeLeftUpArrow = 43
msoShapeLightningBolt = 22
msoShapeLineCallout1 = 109
msoShapeLineCallout1AccentBar = 113
msoShapeLineCallout1BorderandAccentBar = 121
msoShapeLineCallout1NoBorder = 117
msoShapeLineCallout2 = 110
msoShapeLineCallout2AccentBar = 114
msoShapeLineCallout2BorderandAccentBar = 122
msoShapeLineCallout2NoBorder = 118
msoShapeLineCallout3 = 111
msoShapeLineCallout3AccentBar = 115
msoShapeLineCallout3BorderandAccentBar = 123
msoShapeLineCallout3NoBorder = 119
msoShapeLineCallout4 = 112
msoShapeLineCallout4AccentBar = 116
msoShapeLineCallout4BorderandAccentBar = 124
msoShapeLineCallout4NoBorder = 120
msoShapeLineInverse = 183
msoShapeMathDivide = 166
msoShapeMathEqual = 167
msoShapeMathMinus = 164
msoShapeMathMultiply = 165
msoShapeMathNotEqual = 168
msoShapeMathPlus = 163
msoShapeMixed = -2
msoShapeMoon = 24
msoShapeNonIsoscelesTrapezoid = 143
msoShapeNoSymbol = 19
msoShapeNotchedRightArrow = 50
msoShapeNotPrimitive = 138
msoShapeOctagon = 6
msoShapeOval = 9
msoShapeOvalCallout = 107
msoShapeParallelogram = 2
msoShapePentagon = 51
msoShapePie = 142
msoShapePieWedge = 175
msoShapePlaque = 28
msoShapePlaqueTabs = 171
msoShapeQuadArrow = 39
msoShapeQuadArrowCallout = 59
msoShapeRectangle = 1
msoShapeRectangularCallout = 105
msoShapeRegularPentagon = 12
msoShapeRightArrow = 33
msoShapeRightArrowCallout = 53
msoShapeRightBrace = 32
msoShapeRightBracket = 30
msoShapeRightTriangle = 8
msoShapeRound1Rectangle = 151
msoShapeRound2DiagRectangle = 157
msoShapeRound2SameRectangle = 152
msoShapeRoundedRectangle = 5
msoShapeRoundedRectangularCallout = 106
msoShapeSmileyFace = 17
msoShapeSnip1Rectangle = 155
msoShapeSnip2DiagRectangle = 157
msoShapeSnip2SameRectangle = 156
msoShapeSnipRoundRectangle = 154
msoShapeSquareTabs = 170
msoShapeStripedRightArrow = 49
msoShapeSun = 23
msoShapeSwooshArrow = 178
msoShapeTear = 160
msoShapeTrapezoid = 3
msoShapeUpArrow = 35
msoShapeUpArrowCallout = 55
msoShapeUpDownArrow = 38
msoShapeUpDownArrowCallout = 58
msoShapeUpRibbon = 97
msoShapeUTurnArrow = 42
msoShapeVerticalScroll = 101
msoShapeWave = 103

# MsoAutoSize enumeration
msoAutoSizeMixed = -2
msoAutoSizeNone = 0
msoAutoSizeShapeToFitText = 1
msoAutoSizeTextToFitShape = 2

# MsoBackgroundStyleIndex enumeration
msoBackgroundStyle1 = 1
msoBackgroundStyle10 = 10
msoBackgroundStyle11 = 11
msoBackgroundStyle12 = 12
msoBackgroundStyle2 = 2
msoBackgroundStyle3 = 3
msoBackgroundStyle4 = 4
msoBackgroundStyle5 = 5
msoBackgroundStyle6 = 6
msoBackgroundStyle7 = 7
msoBackgroundStyle8 = 8
msoBackgroundStyle9 = 9
msoBackgroundStyleMixed = -2
msoBackgroundStyleNone = 0

# MsoBarPosition enumeration
msoBarBottom = 3
msoBarFloating = 4
msoBarLeft = 0
msoBarMenuBar = 6
msoBarPopup = 5
msoBarRight = 2
msoBarTop = 1

# MsoBarProtection enumeration
msoBarNoChangeDock = 16
msoBarNoChangeVisible = 8
msoBarNoCustomize = 1
msoBarNoHorizontalDock = 64
msoBarNoMove = 4
msoBarNoProtection = 0
msoBarNoResize = 2
msoBarNoVerticalDock = 32

# MsoBarRow enumeration
msoBarRowFirst = 0
msoBarRowLast = -1

# MsoBarType enumeration
msoBarTypeMenuBar = 1
msoBarTypeNormal = 0
msoBarTypePopup = 2

# MsoBaselineAlignment enumeration
msoBaselineAlignAuto = 5
msoBaselineAlignBaseline = 1
msoBaselineAlignCenter = 3
msoBaselineAlignFarEast50 = 4
msoBaselineAlignMixed = -2
msoBaselineAlignTop = 2

# MsoBevelType enumeration
msoBevelAngle = 6
msoBevelArtDeco = 13
msoBevelCircle = 3
msoBevelConvex = 8
msoBevelCoolSlant = 9
msoBevelCross = 5
msoBevelDivot = 10
msoBevelHardEdge = 12
msoBevelNone = 1
msoBevelRelaxedInset = 2
msoBevelRiblet = 11
msoBevelSlope = 4
msoBevelSoftRound = 7
msoBevelTypeMixed = -2

# MsoBlackWhiteMode enumeration
msoBlackWhiteAutomatic = 1
msoBlackWhiteBlack = 8
msoBlackWhiteBlackTextAndLine = 6
msoBlackWhiteDontShow = 10
msoBlackWhiteGrayOutline = 5
msoBlackWhiteGrayScale = 2
msoBlackWhiteHighContrast = 7
msoBlackWhiteInverseGrayScale = 4
msoBlackWhiteLightGrayScale = 3
msoBlackWhiteMixed = -2
msoBlackWhiteWhite = 9

# MsoBlogCategorySupport enumeration
msoBlogMultipleCategories = 2
msoBlogNoCategories = 0
msoBlogOneCategory = 1

# MsoBlogImageType enumeration
msoBlogImageTypeGIF = 2
msoBlogImageTypeJPEG = 1
msoBlogImageTypePNG = 3

# MsoBulletType enumeration
msoBulletMixed = -2
msoBulletNone = 0
msoBulletNumbered = 2
msoBulletPicture = 3
msoBulletUnnumbered = 1

# MsoButtonState enumeration
msoButtonDown = -1
msoButtonMixed = 2
msoButtonUp = 0

# MsoButtonStyle enumeration
msoButtonAutomatic = 0
msoButtonCaption = 2
msoButtonIcon = 1
msoButtonIconAndCaption = 3
msoButtonIconAndCaptionBelow = 11
msoButtonIconAndWrapCaption = 7
msoButtonIconAndWrapCaptionBelow = 15
msoButtonWrapCaption = 14

# MsoCalloutAngleType enumeration
msoCalloutAngle30 = 2
msoCalloutAngle45 = 3
msoCalloutAngle60 = 4
msoCalloutAngle90 = 5
msoCalloutAngleAutomatic = 1
msoCalloutAngleMixed = -2

# MsoCalloutDropType enumeration
msoCalloutDropBottom = 4
msoCalloutDropCenter = 3
msoCalloutDropCustom = 1
msoCalloutDropMixed = -2
msoCalloutDropTop = 2

# MsoCalloutType enumeration
msoCalloutFour = 4
msoCalloutMixed = -2
msoCalloutOne = 1
msoCalloutThree = 3
msoCalloutTwo = 2

# MsoCharacterSet enumeration
msoCharacterSetArabic = 1
msoCharacterSetCyrillic = 2
msoCharacterSetEnglishWesternEuropeanOtherLatinScript = 3
msoCharacterSetGreek = 4
msoCharacterSetHebrew = 5
msoCharacterSetJapanese = 6
msoCharacterSetKorean = 7
msoCharacterSetMultilingualUnicode = 8
msoCharacterSetSimplifiedChinese = 9
msoCharacterSetThai = 10
msoCharacterSetTraditionalChinese = 11
msoCharacterSetVietnamese = 12

# MsoChartElementType enumeration
msoElementChartFloorNone = 1200
msoElementChartFloorShow = 1201
msoElementChartTitleAboveChart = 2
msoElementChartTitleCenteredOverlay = 1
msoElementChartTitleNone = 0
msoElementChartWallNone = 1100
msoElementChartWallShow = 1101
msoElementDataLabelBestFit = 210
msoElementDataLabelBottom = 209
msoElementDataLabelCallout = 211
msoElementDataLabelCenter = 202
msoElementDataLabelInsideBase = 204
msoElementDataLabelInsideEnd = 203
msoElementDataLabelLeft = 206
msoElementDataLabelNone = 200
msoElementDataLabelOutSideEnd = 205
msoElementDataLabelRight = 207
msoElementDataLabelShow = 201
msoElementDataLabelTop = 208
msoElementDataTableNone = 500
msoElementDataTableShow = 501
msoElementDataTableWithLegendKeys = 502
msoElementErrorBarNone = 700
msoElementErrorBarPercentage = 702
msoElementErrorBarStandardDeviation = 703
msoElementErrorBarStandardError = 701
msoElementLegendBottom = 104
msoElementLegendLeft = 103
msoElementLegendLeftOverlay = 106
msoElementLegendNone = 100
msoElementLegendRight = 101
msoElementLegendRightOverlay = 105
msoElementLegendTop = 102
msoElementLineDropHiLoLine = 804
msoElementLineDropLine = 801
msoElementLineHiLoLine = 802
msoElementLineNone = 800
msoElementLineSeriesLine = 803
msoElementPlotAreaNone = 1000
msoElementPlotAreaShow = 1001
msoElementPrimaryCategoryAxisBillions = 374
msoElementPrimaryCategoryAxisLogScale = 375
msoElementPrimaryCategoryAxisMillions = 373
msoElementPrimaryCategoryAxisNone = 348
msoElementPrimaryCategoryAxisReverse = 351
msoElementPrimaryCategoryAxisShow = 349
msoElementPrimaryCategoryAxisThousands = 372
msoElementPrimaryCategoryAxisTitleAdjacentToAxis = 301
msoElementPrimaryCategoryAxisTitleBelowAxis = 302
msoElementPrimaryCategoryAxisTitleHorizontal = 305
msoElementPrimaryCategoryAxisTitleNone = 300
msoElementPrimaryCategoryAxisTitleRotated = 303
msoElementPrimaryCategoryAxisTitleVertical = 304
msoElementPrimaryCategoryAxisWithoutLabels = 350
msoElementPrimaryCategoryGridLinesMajor = 334
msoElementPrimaryCategoryGridLinesMinor = 333
msoElementPrimaryCategoryGridLinesMinorMajor = 335
msoElementPrimaryCategoryGridLinesNone = 332
msoElementPrimaryValueAxisBillions = 356
msoElementPrimaryValueAxisLogScale = 357
msoElementPrimaryValueAxisMillions = 355
msoElementPrimaryValueAxisNone = 352
msoElementPrimaryValueAxisShow = 353
msoElementPrimaryValueAxisThousands = 354
msoElementPrimaryValueAxisTitleAdjacentToAxis = 307
msoElementPrimaryValueAxisTitleBelowAxis = 308
msoElementPrimaryValueAxisTitleHorizontal = 311
msoElementPrimaryValueAxisTitleNone = 306
msoElementPrimaryValueAxisTitleRotated = 309
msoElementPrimaryValueAxisTitleVertical = 310
msoElementPrimaryValueGridLinesMajor = 330
msoElementPrimaryValueGridLinesMinor = 329
msoElementPrimaryValueGridLinesMinorMajor = 331
msoElementPrimaryValueGridLinesNone = 328
msoElementSecondaryCategoryAxisBillions = 378
msoElementSecondaryCategoryAxisLogScale = 379
msoElementSecondaryCategoryAxisMillions = 377
msoElementSecondaryCategoryAxisNone = 358
msoElementSecondaryCategoryAxisReverse = 361
msoElementSecondaryCategoryAxisShow = 359
msoElementSecondaryCategoryAxisThousands = 376
msoElementSecondaryCategoryAxisTitleAdjacentToAxis = 313
msoElementSecondaryCategoryAxisTitleBelowAxis = 314
msoElementSecondaryCategoryAxisTitleHorizontal = 317
msoElementSecondaryCategoryAxisTitleNone = 312
msoElementSecondaryCategoryAxisTitleRotated = 315
msoElementSecondaryCategoryAxisTitleVertical = 316
msoElementSecondaryCategoryAxisWithoutLabels = 360
msoElementSecondaryCategoryGridLinesMajor = 342
msoElementSecondaryCategoryGridLinesMinor = 341
msoElementSecondaryCategoryGridLinesMinorMajor = 343
msoElementSecondaryCategoryGridLinesNone = 340
msoElementSecondaryValueAxisBillions = 366
msoElementSecondaryValueAxisLogScale = 367
msoElementSecondaryValueAxisMillions = 365
msoElementSecondaryValueAxisNone = 362
msoElementSecondaryValueAxisShow = 363
msoElementSecondaryValueAxisThousands = 364
msoElementSecondaryValueAxisTitleAdjacentToAxis = 319
msoElementSecondaryValueAxisTitleBelowAxis = 320
msoElementSecondaryValueAxisTitleHorizontal = 323
msoElementSecondaryValueAxisTitleNone = 318
msoElementSecondaryValueAxisTitleRotated = 321
msoElementSecondaryValueAxisTitleVertical = 322
msoElementSecondaryValueGridLinesMajor = 338
msoElementSecondaryValueGridLinesMinor = 337
msoElementSecondaryValueGridLinesMinorMajor = 339
msoElementSecondaryValueGridLinesNone = 336
msoElementSeriesAxisGridLinesMajor = 346
msoElementSeriesAxisGridLinesMinor = 345
msoElementSeriesAxisGridLinesMinorMajor = 347
msoElementSeriesAxisGridLinesNone = 344
msoElementSeriesAxisNone = 368
msoElementSeriesAxisReverse = 371
msoElementSeriesAxisShow = 369
msoElementSeriesAxisTitleHorizontal = 327
msoElementSeriesAxisTitleNone = 324
msoElementSeriesAxisTitleRotated = 325
msoElementSeriesAxisTitleVertical = 326
msoElementSeriesAxisWithoutLabeling = 370
msoElementTrendlineAddExponential = 602
msoElementTrendlineAddLinear = 601
msoElementTrendlineAddLinearForecast = 603
msoElementTrendlineAddTwoPeriodMovingAverage = 604
msoElementTrendlineNone = 600
msoElementUpDownBarsNone = 900
msoElementUpDownBarsShow = 901

# MsoClipboardFormat enumeration
msoClipboardFormatHTML = 2
msoClipboardFormatMixed = -2
msoClipboardFormatNative = 1
msoClipboardFormatPlainText = 4
msoClipboardFormatRTF = 3

# MsoColorType enumeration
msoColorTypeCMS = 4
msoColorTypeCMYK = 3
msoColorTypeInk = 5
msoColorTypeMixed = -2
msoColorTypeRGB = 1
msoColorTypeScheme = 2

# MsoComboStyle enumeration
msoComboLabel = 1
msoComboNormal = 0

# MsoCommandBarButtonHyperlinkType enumeration
msoCommandBarButtonHyperlinkInsertPicture = 2
msoCommandBarButtonHyperlinkNone = 0
msoCommandBarButtonHyperlinkOpen = 1

# MsoConnectorType enumeration
msoConnectorCurve = 3
msoConnectorElbow = 2
msoConnectorStraight = 1
msoConnectorTypeMixed = -2

# MsoContactCardAddressType enumeration
msoContactCardAddressTypeUnknown = 0
msoContactCardAddressTypeOutlook = 1
msoContactCardAddressTypeSMTP = 2
msoContactCardAddressTypeIM = 1

# MsoContactCardStyle enumeration
msoContactCardFull = 1
msoContactCardHover = 0

# MsoContactCardType enumeration
msoContactCardTypeEnterpriseContact = 0
msoContactCardTypePersonalContact = 1
msoContactCardTypeUnknownContact = 2
msoContactCardTypeEnterpriseGroup = 3
msoContactCardTypePersonalDistributionList = 4

# MsoControlOLEUsage enumeration
msoControlOLEUsageBoth = 3
msoControlOLEUsageClient = 2
msoControlOLEUsageNeither = 0
msoControlOLEUsageServer = 1

# MsoControlType enumeration
msoControlActiveX = 22
msoControlAutoCompleteCombo = 26
msoControlButton = 1
msoControlButtonDropdown = 5
msoControlButtonPopup = 12
msoControlComboBox = 4
msoControlCustom = 0
msoControlDropdown = 3
msoControlEdit = 2
msoControlExpandingGrid = 16
msoControlGauge = 19
msoControlGenericDropdown = 8
msoControlGraphicCombo = 20
msoControlGraphicDropdown = 9
msoControlGraphicPopup = 11
msoControlGrid = 18
msoControlLabel = 15
msoControlLabelEx = 24
msoControlOCXDropdown = 7
msoControlPane = 21
msoControlPopup = 10
msoControlSpinner = 23
msoControlSplitButtonMRUPopup = 14
msoControlSplitButtonPopup = 13
msoControlSplitDropdown = 6
msoControlSplitExpandingGrid = 17
msoControlWorkPane = 25

# MsoCTPDockPosition enumeration
msoCTPDockPositionBottom = 3
msoCTPDockPositionFloating = 4
msoCTPDockPositionLeft = 0
msoCTPDockPositionRight = 2
msoCTPDockPositionTop = 1

# MsoCTPDockPositionRestrict enumeration
msoCTPDockPositionRestrictNoChange = 1
msoCTPDockPositionRestrictNoHorizontal = 2
msoCTPDockPositionRestrictNone = 0
msoCTPDockPositionRestrictNoVertical = 3

# MsoCustomXMLNodeType enumeration
msoCustomXMLNodeAttribute = 2
msoCustomXMLNodeCData = 4
msoCustomXMLNodeComment = 8
msoCustomXMLNodeDocument = 9
msoCustomXMLNodeElement = 1
msoCustomXMLNodeProcessingInstruction = 7
msoCustomXMLNodeText = 3

# MsoCustomXMLValidationErrorType enumeration
msoCustomXMLValidationErrorAutomaticallyCleared = 1
msoCustomXMLValidationErrorManual = 2
msoCustomXMLValidationErrorSchemaGenerated = 0

# MsoDateTimeFormat enumeration
msoDateTimeddddMMMMddyyyy = 2
msoDateTimedMMMMyyyy = 3
msoDateTimedMMMyy = 5
msoDateTimeFigureOut = 14
msoDateTimeFormatMixed = -2
msoDateTimeHmm = 10
msoDateTimehmmAMPM = 12
msoDateTimeHmmss = 11
msoDateTimehmmssAMPM = 13
msoDateTimeMdyy = 1
msoDateTimeMMddyyHmm = 8
msoDateTimeMMddyyhmmAMPM = 9
msoDateTimeMMMMdyyyy = 4
msoDateTimeMMMMyy = 6
msoDateTimeMMyy = 7

# MsoDistributeCmd enumeration
msoDistributeHorizontally = 0
msoDistributeVertically = 1

# MsoDocInspectorStatus enumeration
msoDocInspectorStatusDocOk = 0
msoDocInspectorStatusError = 2
msoDocInspectorStatusIssueFound = 1

# MsoDocProperties enumeration
msoPropertyTypeBoolean = 2
msoPropertyTypeDate = 3
msoPropertyTypeFloat = 5
msoPropertyTypeNumber = 1
msoPropertyTypeString = 4

# MsoEditingType enumeration
msoEditingAuto = 0
msoEditingCorner = 1
msoEditingSmooth = 2
msoEditingSymmetric = 3

# MsoEncoding enumeration
msoEncodingArabic = 1256
msoEncodingArabicASMO = 708
msoEncodingArabicAutoDetect = 51256
msoEncodingArabicTransparentASMO = 720
msoEncodingAutoDetect = 50001
msoEncodingBaltic = 1257
msoEncodingCentralEuropean = 1250
msoEncodingCyrillic = 1251
msoEncodingCyrillicAutoDetect = 51251
msoEncodingEBCDICArabic = 20420
msoEncodingEBCDICDenmarkNorway = 20277
msoEncodingEBCDICFinlandSweden = 20278
msoEncodingEBCDICFrance = 20297
msoEncodingEBCDICGermany = 20273
msoEncodingEBCDICGreek = 20423
msoEncodingEBCDICGreekModern = 875
msoEncodingEBCDICHebrew = 20424
msoEncodingEBCDICIcelandic = 20871
msoEncodingEBCDICInternational = 500
msoEncodingEBCDICItaly = 20280
msoEncodingEBCDICJapaneseKatakanaExtended = 20290
msoEncodingEBCDICJapaneseKatakanaExtendedAndJapanese = 50930
msoEncodingEBCDICJapaneseLatinExtendedAndJapanese = 50939
msoEncodingEBCDICKoreanExtended = 20833
msoEncodingEBCDICKoreanExtendedAndKorean = 50933
msoEncodingEBCDICLatinAmericaSpain = 20284
msoEncodingEBCDICMultilingualROECELatin2 = 870
msoEncodingEBCDICRussian = 20880
msoEncodingEBCDICSerbianBulgarian = 21025
msoEncodingEBCDICSimplifiedChineseExtendedAndSimplifiedChinese = 50935
msoEncodingEBCDICThai = 20838
msoEncodingEBCDICTurkish = 20905
msoEncodingEBCDICTurkishLatin5 = 1026
msoEncodingEBCDICUnitedKingdom = 20285
msoEncodingEBCDICUSCanada = 37
msoEncodingEBCDICUSCanadaAndJapanese = 50931
msoEncodingEBCDICUSCanadaAndTraditionalChinese = 50937
msoEncodingEUCChineseSimplifiedChinese = 51936
msoEncodingEUCJapanese = 51932
msoEncodingEUCKorean = 51949
msoEncodingEUCTaiwaneseTraditionalChinese = 51950
msoEncodingEuropa3 = 29001
msoEncodingExtAlphaLowercase = 21027
msoEncodingGreek = 1253
msoEncodingGreekAutoDetect = 51253
msoEncodingHebrew = 1255
msoEncodingHZGBSimplifiedChinese = 52936
msoEncodingIA5German = 20106
msoEncodingIA5IRV = 20105
msoEncodingIA5Norwegian = 20108
msoEncodingIA5Swedish = 20107
msoEncodingISCIIAssamese = 57006
msoEncodingISCIIBengali = 57003
msoEncodingISCIIDevanagari = 57002
msoEncodingISCIIGujarati = 57010
msoEncodingISCIIKannada = 57008
msoEncodingISCIIMalayalam = 57009
msoEncodingISCIIOriya = 57007
msoEncodingISCIIPunjabi = 57011
msoEncodingISCIITamil = 57004
msoEncodingISCIITelugu = 57005
msoEncodingISO2022CNSimplifiedChinese = 50229
msoEncodingISO2022CNTraditionalChinese = 50227
msoEncodingISO2022JPJISX02011989 = 50222
msoEncodingISO2022JPJISX02021984 = 50221
msoEncodingISO2022JPNoHalfwidthKatakana = 50220
msoEncodingISO2022KR = 50225
msoEncodingISO6937NonSpacingAccent = 20269
msoEncodingISO885915Latin9 = 28605
msoEncodingISO88591Latin1 = 28591
msoEncodingISO88592CentralEurope = 28592
msoEncodingISO88593Latin3 = 28593
msoEncodingISO88594Baltic = 28594
msoEncodingISO88595Cyrillic = 28595
msoEncodingISO88596Arabic = 28596
msoEncodingISO88597Greek = 28597
msoEncodingISO88598Hebrew = 28598
msoEncodingISO88598HebrewLogical = 38598
msoEncodingISO88599Turkish = 28599
msoEncodingJapaneseAutoDetect = 50932
msoEncodingJapaneseShiftJIS = 932
msoEncodingKOI8R = 20866
msoEncodingKOI8U = 21866
msoEncodingKorean = 949
msoEncodingKoreanAutoDetect = 50949
msoEncodingKoreanJohab = 1361
msoEncodingMacArabic = 10004
msoEncodingMacCroatia = 10082
msoEncodingMacCyrillic = 10007
msoEncodingMacGreek1 = 10006
msoEncodingMacHebrew = 10005
msoEncodingMacIcelandic = 10079
msoEncodingMacJapanese = 10001
msoEncodingMacKorean = 10003
msoEncodingMacLatin2 = 10029
msoEncodingMacRoman = 10000
msoEncodingMacRomania = 10010
msoEncodingMacSimplifiedChineseGB2312 = 10008
msoEncodingMacTraditionalChineseBig5 = 10002
msoEncodingMacTurkish = 10081
msoEncodingMacUkraine = 10017
msoEncodingOEMArabic = 864
msoEncodingOEMBaltic = 775
msoEncodingOEMCanadianFrench = 863
msoEncodingOEMCyrillic = 855
msoEncodingOEMCyrillicII = 866
msoEncodingOEMGreek437G = 737
msoEncodingOEMHebrew = 862
msoEncodingOEMIcelandic = 861
msoEncodingOEMModernGreek = 869
msoEncodingOEMMultilingualLatinI = 850
msoEncodingOEMMultilingualLatinII = 852
msoEncodingOEMNordic = 865
msoEncodingOEMPortuguese = 860
msoEncodingOEMTurkish = 857
msoEncodingOEMUnitedStates = 437
msoEncodingSimplifiedChineseAutoDetect = 50936
msoEncodingSimplifiedChineseGB18030 = 54936
msoEncodingSimplifiedChineseGBK = 936
msoEncodingT61 = 20261
msoEncodingTaiwanCNS = 20000
msoEncodingTaiwanEten = 20002
msoEncodingTaiwanIBM5550 = 20003
msoEncodingTaiwanTCA = 20001
msoEncodingTaiwanTeleText = 20004
msoEncodingTaiwanWang = 20005
msoEncodingThai = 874
msoEncodingTraditionalChineseAutoDetect = 50950
msoEncodingTraditionalChineseBig5 = 950
msoEncodingTurkish = 1254
msoEncodingUnicodeBigEndian = 1201
msoEncodingUnicodeLittleEndian = 1200
msoEncodingUSASCII = 20127
msoEncodingUTF7 = 65000
msoEncodingUTF8 = 65001
msoEncodingVietnamese = 1258
msoEncodingWestern = 1252

class MsoEnvelope:

    def __init__(self, msoenvelope=None):
        self.com_object= msoenvelope

    @property
    def CommandBars(self):
        return self.com_object.CommandBars

    @property
    def commandbars(self):
        """Alias for CommandBars"""
        return self.CommandBars

    @property
    def command_bars(self):
        """Alias for CommandBars"""
        return self.CommandBars

    @property
    def Introduction(self):
        return self.com_object.Introduction

    @Introduction.setter
    def Introduction(self, value):
        self.com_object.Introduction = value

    @property
    def introduction(self):
        """Alias for Introduction"""
        return self.Introduction

    @introduction.setter
    def introduction(self, value):
        """Alias for Introduction.setter"""
        self.Introduction = value

    @property
    def Item(self):
        return self.com_object.Item

    @property
    def item(self):
        """Alias for Item"""
        return self.Item

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent


# MsoExtraInfoMethod enumeration
msoMethodGet = 0
msoMethodPost = 1

# MsoExtrusionColorType enumeration
msoExtrusionColorAutomatic = 1
msoExtrusionColorCustom = 2
msoExtrusionColorTypeMixed = -2

# MsoFarEastLineBreakLanguageID enumeration
msoFarEastLineBreakLanguageJapanese = 1041
msoFarEastLineBreakLanguageKorean = 1042
msoFarEastLineBreakLanguageSimplifiedChinese = 2052
msoFarEastLineBreakLanguageTraditionalChinese = 1028

# MsoFeatureInstall enumeration
msoFeatureInstallNone = 0
msoFeatureInstallOnDemand = 1
msoFeatureInstallOnDemandWithUI = 2

# MsoFileDialogType enumeration
msoFileDialogFilePicker = 3
msoFileDialogFolderPicker = 4
msoFileDialogOpen = 1
msoFileDialogSaveAs = 2

# MsoFileDialogView enumeration
msoFileDialogViewDetails = 2
msoFileDialogViewLargeIcons = 6
msoFileDialogViewList = 1
msoFileDialogViewPreview = 4
msoFileDialogViewProperties = 3
msoFileDialogViewSmallIcons = 7
msoFileDialogViewThumbnail = 5
msoFileDialogViewTiles = 9
msoFileDialogViewWebView = 8

# MsoFileNewAction enumeration
msoCreateNewFile = 1
msoEditFile = 0
msoOpenFile = 2

# MsoFileNewSection enumeration
msoBottomSection = 4
msoNew = 1
msoNewfromExistingFile = 2
msoNewfromTemplate = 3
msoOpenDocument = 0

# MsoFileValidationMode enumeration
msoFileValidationDefault = 0
msoFileValidationSkip = 1

# MsoFillType enumeration
msoFillBackground = 5
msoFillGradient = 3
msoFillMixed = -2
msoFillPatterned = 2
msoFillPicture = 6
msoFillSolid = 1
msoFillTextured = 4

# MsoFilterComparison enumeration
msoFilterComparisonContains = 8
msoFilterComparisonEqual = 0
msoFilterComparisonGreaterThan = 3
msoFilterComparisonGreaterThanEqual = 5
msoFilterComparisonIsBlank = 6
msoFilterComparisonIsNotBlank = 7
msoFilterComparisonLessThan = 2
msoFilterComparisonLessThanEqual = 4
msoFilterComparisonNotContains = 9
msoFilterComparisonNotEqual = 1

# MsoFilterConjunction enumeration
msoFilterConjunctionAnd = 0
msoFilterConjunctionOr = 1

# MsoFlipCmd enumeration
msoFlipHorizontal = 0
msoFlipVertical = 1

# MsoFontLanguageIndex enumeration
msoThemeComplexScript = 2
msoThemeEastAsian = 3
msoThemeLatin = 1

# MsoGradientColorType enumeration
msoGradientColorMixed = -2
msoGradientMultiColor = 4
msoGradientOneColor = 1
msoGradientPresetColors = 3
msoGradientTwoColors = 2

# MsoGradientStyle enumeration
msoGradientDiagonalDown = 4
msoGradientDiagonalUp = 3
msoGradientFromCenter = 7
msoGradientFromCorner = 5
msoGradientFromTitle = 6
msoGradientHorizontal = 1
msoGradientMixed = -2
msoGradientVertical = 2

# MsoGraphicStyleIndex enumeration
msoGraphicStylePreset1 = 1
msoGraphicStylePreset10 = 10
msoGraphicStylePreset11 = 11
msoGraphicStylePreset12 = 12
msoGraphicStylePreset13 = 13
msoGraphicStylePreset14 = 14
msoGraphicStylePreset15 = 15
msoGraphicStylePreset16 = 16
msoGraphicStylePreset17 = 17
msoGraphicStylePreset18 = 18
msoGraphicStylePreset19 = 19
msoGraphicStylePreset2 = 2
msoGraphicStylePreset20 = 20
msoGraphicStylePreset21 = 21
msoGraphicStylePreset22 = 22
msoGraphicStylePreset23 = 23
msoGraphicStylePreset24 = 24
msoGraphicStylePreset25 = 25
msoGraphicStylePreset26 = 26
msoGraphicStylePreset27 = 27
msoGraphicStylePreset28 = 28
msoGraphicStylePreset3 = 3
msoGraphicStylePreset4 = 4
msoGraphicStylePreset5 = 5
msoGraphicStylePreset6 = 6
msoGraphicStylePreset7 = 7
msoGraphicStylePreset8 = 8
msoGraphicStylePreset9 = 9
msoGraphicStyleMixed = -2
msoGraphicStyleNotAPreset = 0

# MsoHorizontalAnchor enumeration
msoAnchorCenter = 2
msoAnchorNone = 1
msoHorizontalAnchorMixed = -2

# MsoHyperlinkType enumeration
msoHyperlinkInlineShape = 2
msoHyperlinkRange = 0
msoHyperlinkShape = 1

# MsoLanguageID enumeration
msoLanguageIDAfrikaans = 1078
msoLanguageIDAlbanian = 1052
msoLanguageIDAmharic = 1118
msoLanguageIDArabic = 1025
msoLanguageIDArabicAlgeria = 5121
msoLanguageIDArabicBahrain = 15361
msoLanguageIDArabicEgypt = 3073
msoLanguageIDArabicIraq = 2049
msoLanguageIDArabicJordan = 11265
msoLanguageIDArabicKuwait = 13313
msoLanguageIDArabicLebanon = 12289
msoLanguageIDArabicLibya = 4097
msoLanguageIDArabicMorocco = 6145
msoLanguageIDArabicOman = 8193
msoLanguageIDArabicQatar = 16385
msoLanguageIDArabicSyria = 10241
msoLanguageIDArabicTunisia = 7169
msoLanguageIDArabicUAE = 14337
msoLanguageIDArabicYemen = 9217
msoLanguageIDArmenian = 1067
msoLanguageIDAssamese = 1101
msoLanguageIDAzeriCyrillic = 2092
msoLanguageIDAzeriLatin = 1068
msoLanguageIDBasque = 1069
msoLanguageIDBelgianDutch = 2067
msoLanguageIDBelgianFrench = 2060
msoLanguageIDBengali = 1093
msoLanguageIDBosnian = 4122
msoLanguageIDBosnianBosniaHerzegovinaCyrillic = 8218
msoLanguageIDBosnianBosniaHerzegovinaLatin = 5146
msoLanguageIDBrazilianPortuguese = 1046
msoLanguageIDBulgarian = 1026
msoLanguageIDBurmese = 1109
msoLanguageIDByelorussian = 1059
msoLanguageIDCatalan = 1027
msoLanguageIDCherokee = 1116
msoLanguageIDChineseHongKongSAR = 3076
msoLanguageIDChineseMacaoSAR = 5124
msoLanguageIDChineseSingapore = 4100
msoLanguageIDCroatian = 1050
msoLanguageIDCzech = 1029
msoLanguageIDDanish = 1030
msoLanguageIDDivehi = 1125
msoLanguageIDDutch = 1043
msoLanguageIDEdo = 1126
msoLanguageIDEnglishAUS = 3081
msoLanguageIDEnglishBelize = 10249
msoLanguageIDEnglishCanadian = 4105
msoLanguageIDEnglishCaribbean = 9225
msoLanguageIDEnglishIndonesia = 14345
msoLanguageIDEnglishIreland = 6153
msoLanguageIDEnglishJamaica = 8201
msoLanguageIDEnglishNewZealand = 5129
msoLanguageIDEnglishPhilippines = 13321
msoLanguageIDEnglishSouthAfrica = 7177
msoLanguageIDEnglishTrinidadTobago = 11273
msoLanguageIDEnglishUK = 2057
msoLanguageIDEnglishUS = 1033
msoLanguageIDEnglishZimbabwe = 12297
msoLanguageIDEstonian = 1061
msoLanguageIDFaeroese = 1080
msoLanguageIDFarsi = 1065
msoLanguageIDFilipino = 1124
msoLanguageIDFinnish = 1035
msoLanguageIDFrench = 1036
msoLanguageIDFrenchCameroon = 11276
msoLanguageIDFrenchCanadian = 3084
msoLanguageIDFrenchCotedIvoire = 12300
msoLanguageIDFrenchHaiti = 15372
msoLanguageIDFrenchLuxembourg = 5132
msoLanguageIDFrenchMali = 13324
msoLanguageIDFrenchMonaco = 6156
msoLanguageIDFrenchMorocco = 14348
msoLanguageIDFrenchReunion = 8204
msoLanguageIDFrenchSenegal = 10252
msoLanguageIDFrenchWestIndies = 7180
msoLanguageIDFrenchCongoDRC = 9228
msoLanguageIDFrisianNetherlands = 1122
msoLanguageIDFulfulde = 1127
msoLanguageIDGaelicIreland = 2108
msoLanguageIDGaelicScotland = 1084
msoLanguageIDGalician = 1110
msoLanguageIDGeorgian = 1079
msoLanguageIDGerman = 1031
msoLanguageIDGermanAustria = 3079
msoLanguageIDGermanLiechtenstein = 5127
msoLanguageIDGermanLuxembourg = 4103
msoLanguageIDGreek = 1032
msoLanguageIDGuarani = 1140
msoLanguageIDGujarati = 1095
msoLanguageIDHausa = 1128
msoLanguageIDHawaiian = 1141
msoLanguageIDHebrew = 1037
msoLanguageIDHindi = 1081
msoLanguageIDHungarian = 1038
msoLanguageIDIbibio = 1129
msoLanguageIDIcelandic = 1039
msoLanguageIDIgbo = 1136
msoLanguageIDIndonesian = 1057
msoLanguageIDInuktitut = 1117
msoLanguageIDItalian = 1040
msoLanguageIDJapanese = 1041
msoLanguageIDKannada = 1099
msoLanguageIDKanuri = 1137
msoLanguageIDKashmiri = 1120
msoLanguageIDKashmiriDevanagari = 2144
msoLanguageIDKazakh = 1087
msoLanguageIDKhmer = 1107
msoLanguageIDKirghiz = 1088
msoLanguageIDKonkani = 1111
msoLanguageIDKorean = 1042
msoLanguageIDKyrgyz = 1088
msoLanguageIDLao = 1108
msoLanguageIDLatin = 1142
msoLanguageIDLatvian = 1062
msoLanguageIDLithuanian = 1063
msoLanguageIDMacedonianFYROM = 1071
msoLanguageIDMalayalam = 1100
msoLanguageIDMalayBruneiDarussalam = 2110
msoLanguageIDMalaysian = 1086
msoLanguageIDMaltese = 1082
msoLanguageIDManipuri = 1112
msoLanguageIDMaori = 1153
msoLanguageIDMarathi = 1102
msoLanguageIDMexicanSpanish = 2058
msoLanguageIDMixed = -2
msoLanguageIDMongolian = 1104
msoLanguageIDNepali = 1121
msoLanguageIDNone = 0
msoLanguageIDNoProofing = 1024
msoLanguageIDNorwegianBokmol = 1044
msoLanguageIDNorwegianNynorsk = 2068
msoLanguageIDOriya = 1096
msoLanguageIDOromo = 1138
msoLanguageIDPashto = 1123
msoLanguageIDPolish = 1045
msoLanguageIDPortuguese = 2070
msoLanguageIDPunjabi = 1094
msoLanguageIDQuechuaBolivia = 1131
msoLanguageIDQuechuaEcuador = 2155
msoLanguageIDQuechuaPeru = 3179
msoLanguageIDRhaetoRomanic = 1047
msoLanguageIDRomanian = 1048
msoLanguageIDRomanianMoldova = 2072
msoLanguageIDRussian = 1049
msoLanguageIDRussianMoldova = 2073
msoLanguageIDSamiLappish = 1083
msoLanguageIDSanskrit = 1103
msoLanguageIDSepedi = 1132
msoLanguageIDSerbianBosniaHerzegovinaCyrillic = 7194
msoLanguageIDSerbianBosniaHerzegovinaLatin = 6170
msoLanguageIDSerbianCyrillic = 3098
msoLanguageIDSerbianLatin = 2074
msoLanguageIDSesotho = 1072
msoLanguageIDSimplifiedChinese = 2052
msoLanguageIDSindhi = 1113
msoLanguageIDSindhiPakistan = 2137
msoLanguageIDSinhalese = 1115
msoLanguageIDSlovak = 1051
msoLanguageIDSlovenian = 1060
msoLanguageIDSomali = 1143
msoLanguageIDSorbian = 1070
msoLanguageIDSpanish = 1034
msoLanguageIDSpanishArgentina = 11274
msoLanguageIDSpanishBolivia = 16394
msoLanguageIDSpanishChile = 13322
msoLanguageIDSpanishColombia = 9226
msoLanguageIDSpanishCostaRica = 5130
msoLanguageIDSpanishDominicanRepublic = 7178
msoLanguageIDSpanishEcuador = 12298
msoLanguageIDSpanishElSalvador = 17418
msoLanguageIDSpanishGuatemala = 4106
msoLanguageIDSpanishHonduras = 18442
msoLanguageIDSpanishModernSort = 3082
msoLanguageIDSpanishNicaragua = 19466
msoLanguageIDSpanishPanama = 6154
msoLanguageIDSpanishParaguay = 15370
msoLanguageIDSpanishPeru = 10250
msoLanguageIDSpanishPuertoRico = 20490
msoLanguageIDSpanishUruguay = 14346
msoLanguageIDSpanishVenezuela = 8202
msoLanguageIDSutu = 1072
msoLanguageIDSwahili = 1089
msoLanguageIDSwedish = 1053
msoLanguageIDSwedishFinland = 2077
msoLanguageIDSwissFrench = 4108
msoLanguageIDSwissGerman = 2055
msoLanguageIDSwissItalian = 2064
msoLanguageIDSyriac = 1114
msoLanguageIDTajik = 1064
msoLanguageIDTamazight = 1119
msoLanguageIDTamazightLatin = 2143
msoLanguageIDTamil = 1097
msoLanguageIDTatar = 1092
msoLanguageIDTelugu = 1098
msoLanguageIDThai = 1054
msoLanguageIDTibetan = 1105
msoLanguageIDTigrignaEritrea = 2163
msoLanguageIDTigrignaEthiopic = 1139
msoLanguageIDTraditionalChinese = 1028
msoLanguageIDTsonga = 1073
msoLanguageIDTswana = 1074
msoLanguageIDTurkish = 1055
msoLanguageIDTurkmen = 1090
msoLanguageIDUkrainian = 1058
msoLanguageIDUrdu = 1056
msoLanguageIDUzbekCyrillic = 2115
msoLanguageIDUzbekLatin = 1091
msoLanguageIDVenda = 1075
msoLanguageIDVietnamese = 1066
msoLanguageIDWelsh = 1106
msoLanguageIDXhosa = 1076
msoLanguageIDYi = 1144
msoLanguageIDYiddish = 1085
msoLanguageIDYoruba = 1130
msoLanguageIDZulu = 1077

# MsoLightRigType enumeration
msoLightRigBalanced = 14
msoLightRigBrightRoom = 27
msoLightRigChilly = 22
msoLightRigContrasting = 18
msoLightRigFlat = 24
msoLightRigFlood = 17
msoLightRigFreezing = 23
msoLightRigGlow = 26
msoLightRigHarsh = 16
msoLightRigLegacyFlat1 = 1
msoLightRigLegacyFlat2 = 2
msoLightRigLegacyFlat3 = 3
msoLightRigLegacyFlat4 = 4
msoLightRigLegacyHarsh1 = 9
msoLightRigLegacyHarsh2 = 10
msoLightRigLegacyHarsh3 = 11
msoLightRigLegacyHarsh4 = 12
msoLightRigLegacyNormal1 = 5
msoLightRigLegacyNormal2 = 6
msoLightRigLegacyNormal3 = 7
msoLightRigLegacyNormal4 = 8
msoLightRigMixed = -2
msoLightRigMorning = 19
msoLightRigSoft = 15
msoLightRigSunrise = 20
msoLightRigSunset = 21
msoLightRigThreePoint = 13
msoLightRigTwoPoint = 25

# MsoLineDashStyle enumeration
msoLineDash = 4
msoLineDashDot = 5
msoLineDashDotDot = 6
msoLineDashStyleMixed = -2
msoLineLongDash = 7
msoLineLongDashDot = 8
msoLineRoundDot = 3
msoLineSolid = 1
msoLineSquareDot = 2

# MsoLineStyle enumeration
msoLineSingle = 1
msoLineStyleMixed = -2
msoLineThickBetweenThin = 5
msoLineThickThin = 4
msoLineThinThick = 3
msoLineThinThin = 2

# MsoMenuAnimation enumeration
msoMenuAnimationNone = 0
msoMenuAnimationRandom = 1
msoMenuAnimationSlide = 3
msoMenuAnimationUnfold = 2

# MsoMetaPropertyType enumeration
msoMetaPropertyTypeBoolean = 1
msoMetaPropertyTypeCalculated = 3
msoMetaPropertyTypeChoice = 2
msoMetaPropertyTypeComputed = 4
msoMetaPropertyTypeCurrency = 5
msoMetaPropertyTypeDateTime = 6
msoMetaPropertyTypeFillInChoice = 7
msoMetaPropertyTypeGuid = 8
msoMetaPropertyTypeInteger = 9
msoMetaPropertyTypeLookup = 10
msoMetaPropertyTypeMax = 19
msoMetaPropertyTypeMultiChoice = 12
msoMetaPropertyTypeMultiChoiceFillIn = 13
msoMetaPropertyTypeMultiChoiceLookup = 11
msoMetaPropertyTypeNote = 14
msoMetaPropertyTypeNumber = 15
msoMetaPropertyTypeText = 16
msoMetaPropertyTypeUnknown = 0
msoMetaPropertyTypeUrl = 17
msoMetaPropertyTypeUser = 18

# MsoMixedType enumeration
msoIntegerMixed = 32768
msoSingleMixed = -2147483648

# MsoMoveRow enumeration
msoMoveRowFirst = -4
msoMoveRowNbr = -1
msoMoveRowNext = -2
msoMoveRowPrev = -3

# MsoNumberedBulletStyle enumeration
msoBulletAlphaLCParenBoth = 8
msoBulletAlphaLCParenRight = 9
msoBulletAlphaLCPeriod = 0
msoBulletAlphaUCParenBoth = 10
msoBulletAlphaUCParenRight = 11
msoBulletAlphaUCPeriod = 1
msoBulletArabicAbjadDash = 24
msoBulletArabicAlphaDash = 23
msoBulletArabicDBPeriod = 29
msoBulletArabicDBPlain = 28
msoBulletArabicParenBoth = 12
msoBulletArabicParenRight = 2
msoBulletArabicPeriod = 3
msoBulletArabicPlain = 13
msoBulletCircleNumDBPlain = 18
msoBulletCircleNumWDBlackPlain = 20
msoBulletCircleNumWDWhitePlain = 19
msoBulletHebrewAlphaDash = 25
msoBulletHindiAlpha1Period = 40
msoBulletHindiAlphaPeriod = 36
msoBulletHindiNumParenRight = 39
msoBulletHindiNumPeriod = 37
msoBulletKanjiKoreanPeriod = 27
msoBulletKanjiKoreanPlain = 26
msoBulletKanjiSimpChinDBPeriod = 38
msoBulletRomanLCParenBoth = 4
msoBulletRomanLCParenRight = 5
msoBulletRomanLCPeriod = 6
msoBulletRomanUCParenBoth = 14
msoBulletRomanUCParenRight = 15
msoBulletRomanUCPeriod = 7
msoBulletSimpChinPeriod = 17
msoBulletSimpChinPlain = 16
msoBulletStyleMixed = -2
msoBulletThaiAlphaParenBoth = 32
msoBulletThaiAlphaParenRight = 31
msoBulletThaiAlphaPeriod = 30
msoBulletThaiNumParenBoth = 35
msoBulletThaiNumParenRight = 34
msoBulletThaiNumPeriod = 33
msoBulletTradChinPeriod = 22
msoBulletTradChinPlain = 21

# MsoOLEMenuGroup enumeration
msoOLEMenuGroupContainer = 2
msoOLEMenuGroupEdit = 1
msoOLEMenuGroupFile = 0
msoOLEMenuGroupHelp = 5
msoOLEMenuGroupNone = -1
msoOLEMenuGroupObject = 3
msoOLEMenuGroupWindow = 4

# MsoOrgChartLayoutType enumeration
msoOrgChartLayoutBothHanging = 2
msoOrgChartLayoutLeftHanging = 3
msoOrgChartLayoutMixed = -2
msoOrgChartLayoutRightHanging = 4
msoOrgChartLayoutStandard = 1

# MsoOrgChartOrientation enumeration
msoOrgChartOrientationMixed = -2
msoOrgChartOrientationVertical = 1

# MsoOrientation enumeration
msoOrientationHorizontal = 1
msoOrientationMixed = -2
msoOrientationVertical = 2

# MsoParagraphAlignment enumeration
msoAlignCenter = 1
msoAlignDistribute = 4
msoAlignJustify = 3
msoAlignJustifyLow = 6
msoAlignLeft = 0
msoAlignMixed = -2
msoAlignRight = 2
msoAlignThaiDistribute = 5

# MsoPathFormat enumeration
msoPathType1 = 1
msoPathType2 = 2
msoPathType3 = 3
msoPathType4 = 4
msoPathType5 = 5
msoPathType6 = 6
msoPathType7 = 7
msoPathType8 = 8
msoPathType9 = 9
msoPathTypeMixed = -2
msoPathTypeNone = 0

# MsoPatternType enumeration
msoPattern10Percent = 2
msoPattern20Percent = 3
msoPattern25Percent = 4
msoPattern30Percent = 5
msoPattern40Percent = 6
msoPattern50Percent = 7
msoPattern5Percent = 1
msoPattern60Percent = 8
msoPattern70Percent = 9
msoPattern75Percent = 10
msoPattern80Percent = 11
msoPattern90Percent = 12
msoPatternCross = 51
msoPatternDarkDownwardDiagonal = 15
msoPatternDarkHorizontal = 13
msoPatternDarkUpwardDiagonal = 16
msoPatternDarkVertical = 14
msoPatternDashedDownwardDiagonal = 28
msoPatternDashedHorizontal = 32
msoPatternDashedUpwardDiagonal = 27
msoPatternDashedVertical = 31
msoPatternDiagonalBrick = 40
msoPatternDiagonalCross = 54
msoPatternDivot = 46
msoPatternDottedDiamond = 24
msoPatternDottedGrid = 45
msoPatternDownwardDiagonal = 52
msoPatternHorizontal = 49
msoPatternHorizontalBrick = 35
msoPatternLargeCheckerBoard = 36
msoPatternLargeConfetti = 33
msoPatternLargeGrid = 34
msoPatternLightDownwardDiagonal = 21
msoPatternLightHorizontal = 19
msoPatternLightUpwardDiagonal = 22
msoPatternLightVertical = 20
msoPatternMixed = -2
msoPatternNarrowHorizontal = 30
msoPatternNarrowVertical = 29
msoPatternOutlinedDiamond = 41
msoPatternPlaid = 42
msoPatternShingle = 47
msoPatternSmallCheckerBoard = 17
msoPatternSmallConfetti = 37
msoPatternSmallGrid = 23
msoPatternSolidDiamond = 39
msoPatternSphere = 43
msoPatternTrellis = 18
msoPatternUpwardDiagonal = 53
msoPatternVertical = 50
msoPatternWave = 48
msoPatternWeave = 44
msoPatternWideDownwardDiagonal = 25
msoPatternWideUpwardDiagonal = 26
msoPatternZigZag = 38

# MsoPermission enumeration
msoPermissionChange = 15
msoPermissionEdit = 2
msoPermissionExtract = 8
msoPermissionFullControl = 64
msoPermissionObjModel = 32
msoPermissionPrint = 16
msoPermissionRead = 1
msoPermissionSave = 4
msoPermissionView = 1

# MsoPickerField enumeration
msoPickerFieldUnknown = 0
msoPickerFieldDateTime = 1
msoPickerFieldNumber = 2
msoPickerFieldText = 3
msoPickerFieldUser = 4
msoPickerFieldMax = 5

# MsoPictureColorType enumeration
msoPictureAutomatic = 1
msoPictureBlackAndWhite = 3
msoPictureGrayscale = 2
msoPictureMixed = -2
msoPictureWatermark = 4

# MsoPictureEffectType enumeration
msoEffectBackgroundRemoval = 1
msoEffectBlur = 2
msoEffectBrightnessContrast = 3
msoEffectCement = 4
msoEffectChalkSketch = 5
msoEffectColorTemperature = 6
msoEffectCrisscrossEtching = 7
msoEffectCutout = 8
msoEffectFilmGrain = 9
msoEffectGlass = 10
msoEffectGlowDiffused = 11
msoEffectGlowEdges = 12
msoEffectLightScreen = 13
msoEffectLineDrawing = 14
msoEffectMarker = 15
msoEffectMosaicBubbles = 16
msoEffectNone = 17
msoEffectPaintBrush = 18
msoEffectPaintStrokes = 19
msoEffectPastelsSmooth = 20
msoEffectPencilGrayscale = 21
msoEffectPencilSketch = 22
msoEffectPhotocopy = 23
msoEffectPlasticWrap = 24
msoEffectSaturation = 25
msoEffectSharpenSoften = 26
msoEffectTexturizer = 27
msoEffectWatercolorSponge = 28

# MsoPresetCamera enumeration
msoCameraIsometricBottomDown = 23
msoCameraIsometricBottomUp = 22
msoCameraIsometricLeftDown = 25
msoCameraIsometricLeftUp = 24
msoCameraIsometricOffAxis1Left = 28
msoCameraIsometricOffAxis1Right = 29
msoCameraIsometricOffAxis1Top = 30
msoCameraIsometricOffAxis2Left = 31
msoCameraIsometricOffAxis2Right = 32
msoCameraIsometricOffAxis2Top = 33
msoCameraIsometricOffAxis3Bottom = 36
msoCameraIsometricOffAxis3Left = 34
msoCameraIsometricOffAxis3Right = 35
msoCameraIsometricOffAxis4Bottom = 39
msoCameraIsometricOffAxis4Left = 37
msoCameraIsometricOffAxis4Right = 38
msoCameraIsometricRightDown = 27
msoCameraIsometricRightUp = 26
msoCameraIsometricTopDown = 21
msoCameraIsometricTopUp = 20
msoCameraLegacyObliqueBottom = 8
msoCameraLegacyObliqueBottomLeft = 7
msoCameraLegacyObliqueBottomRight = 9
msoCameraLegacyObliqueFront = 5
msoCameraLegacyObliqueLeft = 4
msoCameraLegacyObliqueRight = 6
msoCameraLegacyObliqueTop = 2
msoCameraLegacyObliqueTopLeft = 1
msoCameraLegacyObliqueTopRight = 3
msoCameraLegacyPerspectiveBottom = 17
msoCameraLegacyPerspectiveBottomLeft = 16
msoCameraLegacyPerspectiveBottomRight = 18
msoCameraLegacyPerspectiveFront = 14
msoCameraLegacyPerspectiveLeft = 13
msoCameraLegacyPerspectiveRight = 15
msoCameraLegacyPerspectiveTop = 11
msoCameraLegacyPerspectiveTopLeft = 10
msoCameraLegacyPerspectiveTopRight = 12
msoCameraObliqueBottom = 46
msoCameraObliqueBottomLeft = 45
msoCameraObliqueBottomRight = 47
msoCameraObliqueLeft = 43
msoCameraObliqueRight = 44
msoCameraObliqueTop = 41
msoCameraObliqueTopLeft = 40
msoCameraObliqueTopRight = 42
msoCameraOrthographicFront = 19
msoCameraPerspectiveAbove = 51
msoCameraPerspectiveAboveLeftFacing = 53
msoCameraPerspectiveAboveRightFacing = 54
msoCameraPerspectiveBelow = 52
msoCameraPerspectiveContrastingLeftFacing = 55
msoCameraPerspectiveContrastingRightFacing = 56
msoCameraPerspectiveFront = 48
msoCameraPerspectiveHeroicExtremeLeftFacing = 59
msoCameraPerspectiveHeroicExtremeRightFacing = 60
msoCameraPerspectiveHeroicLeftFacing = 57
msoCameraPerspectiveHeroicRightFacing = 58
msoCameraPerspectiveLeft = 49
msoCameraPerspectiveRelaxed = 61
msoCameraPerspectiveRelaxedModerately = 62
msoCameraPerspectiveRight = 50
msoPresetCameraMixed = -2

# MsoPresetExtrusionDirection enumeration
msoExtrusionBottom = 2
msoExtrusionBottomLeft = 3
msoExtrusionBottomRight = 1
msoExtrusionLeft = 6
msoExtrusionNone = 5
msoExtrusionRight = 4
msoExtrusionTop = 8
msoExtrusionTopLeft = 9
msoExtrusionTopRight = 7
msoPresetExtrusionDirectionMixed = -2

# MsoPresetGradientType enumeration
msoGradientBrass = 20
msoGradientCalmWater = 8
msoGradientChrome = 21
msoGradientChromeII = 22
msoGradientDaybreak = 4
msoGradientDesert = 6
msoGradientEarlySunset = 1
msoGradientFire = 9
msoGradientFog = 10
msoGradientGold = 18
msoGradientGoldII = 19
msoGradientHorizon = 5
msoGradientLateSunset = 2
msoGradientMahogany = 15
msoGradientMoss = 11
msoGradientNightfall = 3
msoGradientOcean = 7
msoGradientParchment = 14
msoGradientPeacock = 12
msoGradientRainbow = 16
msoGradientRainbowII = 17
msoGradientSapphire = 24
msoGradientSilver = 23
msoGradientWheat = 13
msoPresetGradientMixed = -2

# MsoPresetLightingDirection enumeration
msoLightingBottom = 8
msoLightingBottomLeft = 7
msoLightingBottomRight = 9
msoLightingLeft = 4
msoLightingNone = 5
msoLightingRight = 6
msoLightingTop = 2
msoLightingTopLeft = 1
msoLightingTopRight = 3
msoPresetLightingDirectionMixed = -2

# MsoPresetLightingSoftness enumeration
msoLightingBright = 3
msoLightingDim = 1
msoLightingNormal = 2
msoPresetLightingSoftnessMixed = -2

# MsoPresetMaterial enumeration
msoMaterialClear = 13
msoMaterialDarkEdge = 11
msoMaterialFlat = 14
msoMaterialMatte = 1
msoMaterialMatte2 = 5
msoMaterialMetal = 3
msoMaterialMetal2 = 7
msoMaterialPlastic = 2
msoMaterialPlastic2 = 6
msoMaterialPowder = 10
msoMaterialSoftEdge = 12
msoMaterialSoftMetal = 15
msoMaterialTranslucentPowder = 9
msoMaterialWarmMatte = 8
msoMaterialWireFrame = 4
msoPresetMaterialMixed = -2

# MsoPresetTextEffect enumeration
msoTextEffect1 = 0
msoTextEffect10 = 9
msoTextEffect11 = 10
msoTextEffect12 = 11
msoTextEffect13 = 12
msoTextEffect14 = 13
msoTextEffect15 = 14
msoTextEffect16 = 15
msoTextEffect17 = 16
msoTextEffect18 = 17
msoTextEffect19 = 18
msoTextEffect2 = 1
msoTextEffect20 = 19
msoTextEffect21 = 20
msoTextEffect22 = 21
msoTextEffect23 = 22
msoTextEffect24 = 23
msoTextEffect25 = 24
msoTextEffect26 = 25
msoTextEffect27 = 26
msoTextEffect28 = 27
msoTextEffect29 = 28
msoTextEffect3 = 2
msoTextEffect30 = 29
msoTextEffect31 = 30
msoTextEffect32 = 31
msoTextEffect33 = 32
msoTextEffect34 = 33
msoTextEffect35 = 34
msoTextEffect36 = 35
msoTextEffect37 = 36
msoTextEffect38 = 37
msoTextEffect39 = 38
msoTextEffect4 = 3
msoTextEffect40 = 39
msoTextEffect41 = 40
msoTextEffect42 = 41
msoTextEffect43 = 42
msoTextEffect44 = 43
msoTextEffect45 = 44
msoTextEffect46 = 45
msoTextEffect47 = 46
msoTextEffect48 = 47
msoTextEffect49 = 48
msoTextEffect5 = 4
msoTextEffect50 = 49
msoTextEffect6 = 5
msoTextEffect7 = 6
msoTextEffect8 = 7
msoTextEffect9 = 8
msoTextEffectMixed = -2

# MsoPresetTextEffectShape enumeration
msoTextEffectShapeArchDownCurve = 10
msoTextEffectShapeArchDownPour = 14
msoTextEffectShapeArchUpCurve = 9
msoTextEffectShapeArchUpPour = 13
msoTextEffectShapeButtonCurve = 12
msoTextEffectShapeButtonPour = 16
msoTextEffectShapeCanDown = 20
msoTextEffectShapeCanUp = 19
msoTextEffectShapeCascadeDown = 40
msoTextEffectShapeCascadeUp = 39
msoTextEffectShapeChevronDown = 6
msoTextEffectShapeChevronUp = 5
msoTextEffectShapeCircleCurve = 11
msoTextEffectShapeCirclePour = 15
msoTextEffectShapeCurveDown = 18
msoTextEffectShapeCurveUp = 17
msoTextEffectShapeDeflate = 26
msoTextEffectShapeDeflateBottom = 28
msoTextEffectShapeDeflateInflate = 31
msoTextEffectShapeDeflateInflateDeflate = 32
msoTextEffectShapeDeflateTop = 30
msoTextEffectShapeDoubleWave1 = 23
msoTextEffectShapeDoubleWave2 = 24
msoTextEffectShapeFadeDown = 36
msoTextEffectShapeFadeLeft = 34
msoTextEffectShapeFadeRight = 33
msoTextEffectShapeFadeUp = 35
msoTextEffectShapeInflate = 25
msoTextEffectShapeInflateBottom = 27
msoTextEffectShapeInflateTop = 29
msoTextEffectShapeMixed = -2
msoTextEffectShapePlainText = 1
msoTextEffectShapeRingInside = 7
msoTextEffectShapeRingOutside = 8
msoTextEffectShapeSlantDown = 38
msoTextEffectShapeSlantUp = 37
msoTextEffectShapeStop = 2
msoTextEffectShapeTriangleDown = 4
msoTextEffectShapeTriangleUp = 3
msoTextEffectShapeWave1 = 21
msoTextEffectShapeWave2 = 22

# MsoPresetTexture enumeration
msoPresetTextureMixed = -2
msoTextureBlueTissuePaper = 17
msoTextureBouquet = 20
msoTextureBrownMarble = 11
msoTextureCanvas = 2
msoTextureCork = 21
msoTextureDenim = 3
msoTextureFishFossil = 7
msoTextureGranite = 12
msoTextureGreenMarble = 9
msoTextureMediumWood = 24
msoTextureNewsprint = 13
msoTextureOak = 23
msoTexturePaperBag = 6
msoTexturePapyrus = 1
msoTextureParchment = 15
msoTexturePinkTissuePaper = 18
msoTexturePurpleMesh = 19
msoTextureRecycledPaper = 14
msoTextureSand = 8
msoTextureStationery = 16
msoTextureWalnut = 22
msoTextureWaterDroplets = 5
msoTextureWhiteMarble = 10
msoTextureWovenMat = 4

# MsoPresetThreeDFormat enumeration
msoPresetThreeDFormatMixed = -2
msoThreeD1 = 1
msoThreeD10 = 10
msoThreeD11 = 11
msoThreeD12 = 12
msoThreeD13 = 13
msoThreeD14 = 14
msoThreeD15 = 15
msoThreeD16 = 16
msoThreeD17 = 17
msoThreeD18 = 18
msoThreeD19 = 19
msoThreeD2 = 2
msoThreeD20 = 20
msoThreeD3 = 3
msoThreeD4 = 4
msoThreeD5 = 5
msoThreeD6 = 6
msoThreeD7 = 7
msoThreeD8 = 8
msoThreeD9 = 9

# MsoRecolorType enumeration
msoRecolorType1 = 1
msoRecolorType10 = 10
msoRecolorType2 = 2
msoRecolorType3 = 3
msoRecolorType4 = 4
msoRecolorType5 = 5
msoRecolorType6 = 6
msoRecolorType7 = 7
msoRecolorType8 = 8
msoRecolorType9 = 9
msoRecolorTypeMixed = -2
msoRecolorTypeNone = 0

# MsoReflectionType enumeration
msoReflectionType1 = 1
msoReflectionType2 = 2
msoReflectionType3 = 3
msoReflectionType4 = 4
msoReflectionType5 = 5
msoReflectionType6 = 6
msoReflectionType7 = 7
msoReflectionType8 = 8
msoReflectionType9 = 9
msoReflectionTypeMixed = -2
msoReflectionTypeNone = 0

# MsoRelativeNodePosition enumeration
msoAfterLastSibling = 4
msoAfterNode = 2
msoBeforeFirstSibling = 3
msoBeforeNode = 1

# MsoScaleFrom enumeration
msoScaleFromBottomRight = 2
msoScaleFromMiddle = 1
msoScaleFromTopLeft = 0

# MsoScreenSize enumeration
msoScreenSize1024x768 = 4
msoScreenSize1152x882 = 5
msoScreenSize1152x900 = 6
msoScreenSize1280x1024 = 7
msoScreenSize1600x1200 = 8
msoScreenSize1800x1440 = 9
msoScreenSize1920x1200 = 10
msoScreenSize544x376 = 0
msoScreenSize640x480 = 1
msoScreenSize720x512 = 2
msoScreenSize800x600 = 3

# MsoSegmentType enumeration
msoSegmentCurve = 1
msoSegmentLine = 0

# MsoShadowStyle enumeration
msoShadowStyleInnerShadow = 1
msoShadowStyleMixed = -2
msoShadowStyleOuterShadow = 2

# MsoShadowType enumeration
msoShadow1 = 1
msoShadow10 = 10
msoShadow11 = 11
msoShadow12 = 12
msoShadow13 = 13
msoShadow14 = 14
msoShadow15 = 15
msoShadow16 = 16
msoShadow17 = 17
msoShadow18 = 18
msoShadow19 = 19
msoShadow2 = 2
msoShadow20 = 20
msoShadow3 = 3
msoShadow4 = 4
msoShadow5 = 5
msoShadow6 = 6
msoShadow7 = 7
msoShadow8 = 8
msoShadow9 = 9
msoShadowMixed = -2

# MsoShapeStyleIndex enumeration
msoLineStylePreset1 = 10001
msoLineStylePreset10 = 10010
msoLineStylePreset11 = 10011
msoLineStylePreset12 = 10012
msoLineStylePreset13 = 10013
msoLineStylePreset14 = 10014
msoLineStylePreset15 = 10015
msoLineStylePreset16 = 10016
msoLineStylePreset17 = 10017
msoLineStylePreset18 = 10018
msoLineStylePreset19 = 10019
msoLineStylePreset2 = 10002
msoLineStylePreset20 = 10020
msoLineStylePreset3 = 10003
msoLineStylePreset4 = 10004
msoLineStylePreset5 = 10005
msoLineStylePreset6 = 10006
msoLineStylePreset7 = 10007
msoLineStylePreset8 = 10008
msoLineStylePreset9 = 10009
msoShapeStylePreset1 = 1
msoShapeStylePreset10 = 10
msoShapeStylePreset11 = 11
msoShapeStylePreset12 = 12
msoShapeStylePreset13 = 13
msoShapeStylePreset14 = 14
msoShapeStylePreset15 = 15
msoShapeStylePreset16 = 16
msoShapeStylePreset17 = 17
msoShapeStylePreset18 = 18
msoShapeStylePreset19 = 19
msoShapeStylePreset2 = 2
msoShapeStylePreset20 = 20
msoShapeStylePreset3 = 3
msoShapeStylePreset4 = 4
msoShapeStylePreset5 = 5
msoShapeStylePreset6 = 6
msoShapeStylePreset7 = 7
msoShapeStylePreset8 = 8
msoShapeStylePreset9 = 9
msoShapeStyleMixed = -2
msoShapeStyleNotAPreset = 0

# MsoShapeType enumeration
mso3DModel = 30
msoAutoShape = 1
msoCallout = 2
msoCanvas = 20
msoChart = 3
msoComment = 4
msoContentApp = 27
msoDiagram = 21
msoEmbeddedOLEObject = 7
msoFormControl = 8
msoFreeform = 5
msoGraphic = 28
msoGroup = 6
msoIgxGraphic = 24
msoInk = 22
msoInkComment = 23
msoLine = 9
msoLinked3DModel = 31
msoLinkedGraphic = 29
msoLinkedOLEObject = 10
msoLinkedPicture = 11
msoMedia = 16
msoOLEControlObject = 12
msoPicture = 13
msoPlaceholder = 14
msoScriptAnchor = 18
msoShapeTypeMixed = -2
msoSlicer = 25
msoTable = 19
msoTextBox = 17
msoTextEffect = 15
msoWebVideo = 26

# MsoSharedWorkspaceTaskPriority enumeration
msoSharedWorkspaceTaskPriorityHigh = 1
msoSharedWorkspaceTaskPriorityLow = 3
msoSharedWorkspaceTaskPriorityNormal = 2

# MsoSharedWorkspaceTaskStatus enumeration
msoSharedWorkspaceTaskStatusCompleted = 3
msoSharedWorkspaceTaskStatusDeferred = 4
msoSharedWorkspaceTaskStatusInProgress = 2
msoSharedWorkspaceTaskStatusNotStarted = 1
msoSharedWorkspaceTaskStatusWaiting = 5

# MsoSignatureSubset enumeration
msoSignatureSubsetAll = 5
msoSignatureSubsetSignatureLines = 2
msoSignatureSubsetSignatureLinesSigned = 3
msoSignatureSubsetSignatureLinesUnsigned = 4
msoSignatureSubsetSignaturesAllSigs = 0
msoSignatureSubsetSignaturesNonVisible = 1

# MsoSmartArtNodePosition enumeration
msoSmartArtNodeAbove = 4
msoSmartArtNodeAfter = 2
msoSmartArtNodeBefore = 3
msoSmartArtNodeBelow = 5
msoSmartArtNodeDefault = 1

# MsoSmartArtNodeType enumeration
msoSmartArtNodeTypeAssistant = 2
msoSmartArtNodeTypeDefault = 1

# MsoSoftEdgeType enumeration
msoSoftEdgeType1 = 1
msoSoftEdgeType2 = 2
msoSoftEdgeType3 = 3
msoSoftEdgeType4 = 4
msoSoftEdgeType5 = 5
msoSoftEdgeType6 = 6
msoSoftEdgeTypeNone = 0
SoftEdgeTypeMixed = -2

# MsoSyncConflictResolutionType enumeration
msoSyncConflictClientWins = 0
msoSyncConflictMerge = 2
msoSyncConflictServerWins = 1

# MsoSyncErrorType enumeration
msoSyncErrorCouldNotCompare = 13
msoSyncErrorCouldNotConnect = 2
msoSyncErrorCouldNotOpen = 11
msoSyncErrorCouldNotResolve = 14
msoSyncErrorCouldNotUpdate = 12
msoSyncErrorFileInUse = 6
msoSyncErrorFileNotFound = 4
msoSyncErrorFileTooLarge = 5
msoSyncErrorNone = 0
msoSyncErrorNoNetwork = 15
msoSyncErrorOutOfSpace = 3
msoSyncErrorUnauthorizedUser = 1
msoSyncErrorUnknown = 16
msoSyncErrorUnknownDownload = 10
msoSyncErrorUnknownUpload = 9
msoSyncErrorVirusDownload = 8
msoSyncErrorVirusUpload = 7

# MsoSyncEventType enumeration
msoSyncEventDownloadFailed = 2
msoSyncEventDownloadInitiated = 0
msoSyncEventDownloadNoChange = 6
msoSyncEventDownloadSucceeded = 1
msoSyncEventOffline = 7
msoSyncEventUploadFailed = 5
msoSyncEventUploadInitiated = 3
msoSyncEventUploadSucceeded = 4

# MsoSyncStatusType enumeration
msoSyncStatusConflict = 4
msoSyncStatusError = 6
msoSyncStatusLatest = 1
msoSyncStatusLocalChanges = 3
msoSyncStatusNewerAvailable = 2
msoSyncStatusNoSharedWorkspace = 0
msoSyncStatusNotRoaming = 0
msoSyncStatusSuspended = 5

# MsoSyncVersionType enumeration
msoSyncVersionLastViewed = 0
msoSyncVersionServer = 1

# MsoTabStopType enumeration
msoTabStopCenter = 2
msoTabStopDecimal = 4
msoTabStopLeft = 1
msoTabStopMixed = -2
msoTabStopRight = 3

# MsoTargetBrowser enumeration
msoTargetBrowserIE4 = 2
msoTargetBrowserIE5 = 3
msoTargetBrowserIE6 = 4
msoTargetBrowserV3 = 0
msoTargetBrowserV4 = 1

# MsoTextCaps enumeration
msoAllCaps = 2
msoCapsMixed = -2
msoNoCaps = 0
msoSmallCaps = 1

# MsoTextChangeCase enumeration
msoCaseLower = 2
msoCaseSentence = 1
msoCaseTitle = 4
msoCaseToggle = 5
msoCaseUpper = 3

# MsoTextCharWrap enumeration
msoCharWrapMixed = -2
msoCustomCharWrap = 3
msoNoCharWrap = 0
msoStandardCharWrap = 1
msoStrictCharWrap = 2

# MsoTextDirection enumeration
msoTextDirectionLeftToRight = 1
msoTextDirectionMixed = -2
msoTextDirectionRightToLeft = 2

# MsoTextEffectAlignment enumeration
msoTextEffectAlignmentCentered = 2
msoTextEffectAlignmentLeft = 1
msoTextEffectAlignmentLetterJustify = 4
msoTextEffectAlignmentMixed = -2
msoTextEffectAlignmentRight = 3
msoTextEffectAlignmentStretchJustify = 6
msoTextEffectAlignmentWordJustify = 5

# MsoTextFontAlign enumeration
msoFontAlignAuto = 0
msoFontAlignBaseline = 3
msoFontAlignBottom = 4
msoFontAlignCenter = 2
msoFontAlignMixed = -2
msoFontAlignTop = 1

# MsoTextOrientation enumeration
msoTextOrientationDownward = 3
msoTextOrientationHorizontal = 1
msoTextOrientationHorizontalRotatedFarEast = 6
msoTextOrientationMixed = -2
msoTextOrientationUpward = 2
msoTextOrientationVertical = 5
msoTextOrientationVerticalFarEast = 4

# MsoTextStrike enumeration
msoDoubleStrike = 2
msoNoStrike = 0
msoSingleStrike = 1
msoStrikeMixed = -2

# MsoTextTabAlign enumeration
msoTabAlignCenter = 1
msoTabAlignDecimal = 3
msoTabAlignLeft = 0
msoTabAlignMixed = -2
msoTabAlignRight = 2

# MsoTextUnderlineType enumeration
msoNoUnderline = 0
msoUnderlineDashHeavyLine = 8
msoUnderlineDashLine = 7
msoUnderlineDashLongHeavyLine = 10
msoUnderlineDashLongLine = 9
msoUnderlineDotDashHeavyLine = 12
msoUnderlineDotDashLine = 11
msoUnderlineDotDotDashHeavyLine = 14
msoUnderlineDotDotDashLine = 13
msoUnderlineDottedHeavyLine = 6
msoUnderlineDottedLine = 5
msoUnderlineDoubleLine = 3
msoUnderlineHeavyLine = 4
msoUnderlineMixed = -2
msoUnderlineSingleLine = 2
msoUnderlineWavyDoubleLine = 17
msoUnderlineWavyHeavyLine = 16
msoUnderlineWavyLine = 15
msoUnderlineWords = 1

# MsoTextureAlignment enumeration
msoTextureAlignmentMixed = -2
msoTextureBottom = 7
msoTextureBottomLeft = 6
msoTextureBottomRight = 8
msoTextureCenter = 4
msoTextureLeft = 3
msoTextureRight = 5
msoTextureTop = 1
msoTextureTopLeft = 0
msoTextureTopRight = 2

# MsoTextureType enumeration
msoTexturePreset = 1
msoTextureTypeMixed = -2
msoTextureUserDefined = 2

# MsoThemeColorIndex enumeration
msoNotThemeColor = 0
msoThemeColorAccent1 = 5
msoThemeColorAccent2 = 6
msoThemeColorAccent3 = 7
msoThemeColorAccent4 = 8
msoThemeColorAccent5 = 9
msoThemeColorAccent6 = 10
msoThemeColorBackground1 = 14
msoThemeColorBackground2 = 16
msoThemeColorDark1 = 1
msoThemeColorDark2 = 3
msoThemeColorFollowedHyperlink = 12
msoThemeColorHyperlink = 11
msoThemeColorLight1 = 2
msoThemeColorLight2 = 4
msoThemeColorMixed = -2
msoThemeColorText1 = 13
msoThemeColorText2 = 15

# MsoThemeColorSchemeIndex enumeration
msoThemeAccent1 = 5
msoThemeAccent2 = 6
msoThemeAccent3 = 7
msoThemeAccent4 = 8
msoThemeAccent5 = 9
msoThemeAccent6 = 10
msoThemeDark1 = 1
msoThemeDark2 = 3
msoThemeFollowedHyperlink = 12
msoThemeHyperlink = 11
msoThemeLight1 = 2
msoThemeLight2 = 4

# MsoTriState enumeration
msoCTrue = 1
msoFalse = 0
msoTriStateMixed = -2
msoTriStateToggle = -3
msoTrue = -1

# MsoVerticalAnchor enumeration
msoAnchorBottom = 4
msoAnchorBottomBaseLine = 5
msoAnchorMiddle = 3
msoAnchorTop = 1
msoAnchorTopBaseline = 2
msoVerticalAnchorMixed = -2

# MsoWarpFormat enumeration
msoWarpFormat1 = 0
msoWarpFormat10 = 9
msoWarpFormat11 = 10
msoWarpFormat12 = 11
msoWarpFormat13 = 12
msoWarpFormat14 = 13
msoWarpFormat15 = 14
msoWarpFormat16 = 15
msoWarpFormat17 = 16
msoWarpFormat18 = 17
msoWarpFormat19 = 18
msoWarpFormat2 = 1
msoWarpFormat20 = 19
msoWarpFormat21 = 20
msoWarpFormat22 = 21
msoWarpFormat23 = 22
msoWarpFormat24 = 23
msoWarpFormat25 = 24
msoWarpFormat26 = 25
msoWarpFormat27 = 26
msoWarpFormat28 = 27
msoWarpFormat29 = 28
msoWarpFormat3 = 2
msoWarpFormat30 = 29
msoWarpFormat31 = 30
msoWarpFormat32 = 31
msoWarpFormat33 = 32
msoWarpFormat34 = 33
msoWarpFormat35 = 34
msoWarpFormat36 = 35
msoWarpFormat37 = 36
msoWarpFormat4 = 3
msoWarpFormat5 = 4
msoWarpFormat6 = 5
msoWarpFormat7 = 6
msoWarpFormat8 = 7
msoWarpFormat9 = 8
msoWarpFormatMixed = -2

# MsoWizardMsgType enumeration
msoWizardMsgLocalStateOff = 2
msoWizardMsgLocalStateOn = 1
msoWizardMsgResuming = 5
msoWizardMsgShowHelp = 3
msoWizardMsgSuspending = 4

# MsoZOrderCmd enumeration
msoBringForward = 2
msoBringInFrontOfText = 4
msoBringToFront = 0
msoSendBackward = 3
msoSendBehindText = 5
msoSendToBack = 1

class NewFile:

    def __init__(self, newfile=None):
        self.com_object= newfile

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    def Add(self, FileName=None, Section=None, DisplayName=None, Action=None):
        arguments = com_arguments([unwrap(a) for a in [FileName, Section, DisplayName, Action]])
        return self.com_object.Add(*arguments)

    def add(self, FileName=None, Section=None, DisplayName=None, Action=None):
        """Alias for Add"""
        arguments = [FileName, Section, DisplayName, Action]
        return self.Add(*arguments)

    def Remove(self, FileName=None, Section=None, DisplayName=None, Action=None):
        arguments = com_arguments([unwrap(a) for a in [FileName, Section, DisplayName, Action]])
        return self.com_object.Remove(*arguments)

    def remove(self, FileName=None, Section=None, DisplayName=None, Action=None):
        """Alias for Remove"""
        arguments = [FileName, Section, DisplayName, Action]
        return self.Remove(*arguments)


class ODSOColumn:

    def __init__(self, odsocolumn=None):
        self.com_object= odsocolumn

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Index(self):
        return self.com_object.Index

    @property
    def index(self):
        """Alias for Index"""
        return self.Index

    @property
    def Name(self):
        return self.com_object.Name

    @property
    def name(self):
        """Alias for Name"""
        return self.Name

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    @property
    def Value(self):
        return self.com_object.Value

    @property
    def value(self):
        """Alias for Value"""
        return self.Value


class ODSOColumns:

    def __init__(self, odsocolumns=None):
        self.com_object= odsocolumns

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    def Item(self, varIndex=None):
        arguments = com_arguments([unwrap(a) for a in [varIndex]])
        return self.com_object.Item(*arguments)

    def item(self, varIndex=None):
        """Alias for Item"""
        arguments = [varIndex]
        return self.Item(*arguments)

    def __call__(self, varIndex=None):
        return self.Item(varIndex)


class ODSOFilter:

    def __init__(self, odsofilter=None):
        self.com_object= odsofilter

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Column(self):
        return self.com_object.Column

    @Column.setter
    def Column(self, value):
        self.com_object.Column = value

    @property
    def column(self):
        """Alias for Column"""
        return self.Column

    @column.setter
    def column(self, value):
        """Alias for Column.setter"""
        self.Column = value

    @property
    def CompareTo(self):
        return self.com_object.CompareTo

    @CompareTo.setter
    def CompareTo(self, value):
        self.com_object.CompareTo = value

    @property
    def compareto(self):
        """Alias for CompareTo"""
        return self.CompareTo

    @compareto.setter
    def compareto(self, value):
        """Alias for CompareTo.setter"""
        self.CompareTo = value

    @property
    def compare_to(self):
        """Alias for CompareTo"""
        return self.CompareTo

    @compare_to.setter
    def compare_to(self, value):
        """Alias for CompareTo.setter"""
        self.CompareTo = value

    @property
    def Comparison(self):
        return self.com_object.Comparison

    @Comparison.setter
    def Comparison(self, value):
        self.com_object.Comparison = value

    @property
    def comparison(self):
        """Alias for Comparison"""
        return self.Comparison

    @comparison.setter
    def comparison(self, value):
        """Alias for Comparison.setter"""
        self.Comparison = value

    @property
    def Conjunction(self):
        return self.com_object.Conjunction

    @Conjunction.setter
    def Conjunction(self, value):
        self.com_object.Conjunction = value

    @property
    def conjunction(self):
        """Alias for Conjunction"""
        return self.Conjunction

    @conjunction.setter
    def conjunction(self, value):
        """Alias for Conjunction.setter"""
        self.Conjunction = value

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Index(self):
        return self.com_object.Index

    @property
    def index(self):
        """Alias for Index"""
        return self.Index

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent


class ODSOFilters:

    def __init__(self, odsofilters=None):
        self.com_object= odsofilters

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    def Add(self, Column=None, Comparison=None, Conjunction=None, bstrCompareTo=None, DeferUpdate=None):
        arguments = com_arguments([unwrap(a) for a in [Column, Comparison, Conjunction, bstrCompareTo, DeferUpdate]])
        return self.com_object.Add(*arguments)

    def add(self, Column=None, Comparison=None, Conjunction=None, bstrCompareTo=None, DeferUpdate=None):
        """Alias for Add"""
        arguments = [Column, Comparison, Conjunction, bstrCompareTo, DeferUpdate]
        return self.Add(*arguments)

    def Delete(self, Index=None, DeferUpdate=None):
        arguments = com_arguments([unwrap(a) for a in [Index, DeferUpdate]])
        return self.com_object.Delete(*arguments)

    def delete(self, Index=None, DeferUpdate=None):
        """Alias for Delete"""
        arguments = [Index, DeferUpdate]
        return self.Delete(*arguments)

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        return self.com_object.Item(*arguments)

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)


class OfficeDataSourceObject:

    def __init__(self, officedatasourceobject=None):
        self.com_object= officedatasourceobject

    @property
    def Columns(self):
        return self.com_object.Columns

    @property
    def columns(self):
        """Alias for Columns"""
        return self.Columns

    @property
    def ConnectString(self):
        return self.com_object.ConnectString

    @ConnectString.setter
    def ConnectString(self, value):
        self.com_object.ConnectString = value

    @property
    def connectstring(self):
        """Alias for ConnectString"""
        return self.ConnectString

    @connectstring.setter
    def connectstring(self, value):
        """Alias for ConnectString.setter"""
        self.ConnectString = value

    @property
    def connect_string(self):
        """Alias for ConnectString"""
        return self.ConnectString

    @connect_string.setter
    def connect_string(self, value):
        """Alias for ConnectString.setter"""
        self.ConnectString = value

    @property
    def DataSource(self):
        return self.com_object.DataSource

    @DataSource.setter
    def DataSource(self, value):
        self.com_object.DataSource = value

    @property
    def datasource(self):
        """Alias for DataSource"""
        return self.DataSource

    @datasource.setter
    def datasource(self, value):
        """Alias for DataSource.setter"""
        self.DataSource = value

    @property
    def data_source(self):
        """Alias for DataSource"""
        return self.DataSource

    @data_source.setter
    def data_source(self, value):
        """Alias for DataSource.setter"""
        self.DataSource = value

    @property
    def Filters(self):
        return self.com_object.Filters

    @property
    def filters(self):
        """Alias for Filters"""
        return self.Filters

    @property
    def RowCount(self):
        return self.com_object.RowCount

    @property
    def rowcount(self):
        """Alias for RowCount"""
        return self.RowCount

    @property
    def row_count(self):
        """Alias for RowCount"""
        return self.RowCount

    @property
    def Table(self):
        return self.com_object.Table

    @property
    def table(self):
        """Alias for Table"""
        return self.Table

    def ApplyFilter(self):
        return self.com_object.ApplyFilter()

    def applyfilter(self):
        """Alias for ApplyFilter"""
        return self.ApplyFilter()

    def apply_filter(self):
        """Alias for ApplyFilter"""
        return self.ApplyFilter()

    def Move(self, MsoMoveRow=None, RowNbr=None):
        arguments = com_arguments([unwrap(a) for a in [MsoMoveRow, RowNbr]])
        return self.com_object.Move(*arguments)

    def move(self, MsoMoveRow=None, RowNbr=None):
        """Alias for Move"""
        arguments = [MsoMoveRow, RowNbr]
        return self.Move(*arguments)

    def Open(self, bstrSrc=None, bstrConnect=None, bstrTable=None, fOpenExclusive=None, fNeverPrompt=None):
        arguments = com_arguments([unwrap(a) for a in [bstrSrc, bstrConnect, bstrTable, fOpenExclusive, fNeverPrompt]])
        return self.com_object.Open(*arguments)

    def open(self, bstrSrc=None, bstrConnect=None, bstrTable=None, fOpenExclusive=None, fNeverPrompt=None):
        """Alias for Open"""
        arguments = [bstrSrc, bstrConnect, bstrTable, fOpenExclusive, fNeverPrompt]
        return self.Open(*arguments)

    def SetSortOrder(self, SortField1=None, SortAscending1=None, SortField2=None, SortAscending2=None, SortField3=None, SortAscending3=None):
        arguments = com_arguments([unwrap(a) for a in [SortField1, SortAscending1, SortField2, SortAscending2, SortField3, SortAscending3]])
        return self.com_object.SetSortOrder(*arguments)

    def setsortorder(self, SortField1=None, SortAscending1=None, SortField2=None, SortAscending2=None, SortField3=None, SortAscending3=None):
        """Alias for SetSortOrder"""
        arguments = [SortField1, SortAscending1, SortField2, SortAscending2, SortField3, SortAscending3]
        return self.SetSortOrder(*arguments)

    def set_sort_order(self, SortField1=None, SortAscending1=None, SortField2=None, SortAscending2=None, SortField3=None, SortAscending3=None):
        """Alias for SetSortOrder"""
        arguments = [SortField1, SortAscending1, SortField2, SortAscending2, SortField3, SortAscending3]
        return self.SetSortOrder(*arguments)


class OfficeTheme:

    def __init__(self, officetheme=None):
        self.com_object= officetheme

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    @property
    def ThemeColorScheme(self):
        return self.com_object.ThemeColorScheme

    @property
    def themecolorscheme(self):
        """Alias for ThemeColorScheme"""
        return self.ThemeColorScheme

    @property
    def theme_color_scheme(self):
        """Alias for ThemeColorScheme"""
        return self.ThemeColorScheme

    @property
    def ThemeEffectScheme(self):
        return self.com_object.ThemeEffectScheme

    @property
    def themeeffectscheme(self):
        """Alias for ThemeEffectScheme"""
        return self.ThemeEffectScheme

    @property
    def theme_effect_scheme(self):
        """Alias for ThemeEffectScheme"""
        return self.ThemeEffectScheme

    @property
    def ThemeFontScheme(self):
        return self.com_object.ThemeFontScheme

    @property
    def themefontscheme(self):
        """Alias for ThemeFontScheme"""
        return self.ThemeFontScheme

    @property
    def theme_font_scheme(self):
        """Alias for ThemeFontScheme"""
        return self.ThemeFontScheme


# OutSpaceSlabStyle enumeration
OutSpaceSlabStyleError = 2
OutSpaceSlabStyleNormal = 0
OutSpaceSlabStyleWarning = 1

class ParagraphFormat2:

    def __init__(self, paragraphformat2=None):
        self.com_object= paragraphformat2

    @property
    def Alignment(self):
        return self.com_object.Alignment

    @Alignment.setter
    def Alignment(self, value):
        self.com_object.Alignment = value

    @property
    def alignment(self):
        """Alias for Alignment"""
        return self.Alignment

    @alignment.setter
    def alignment(self, value):
        """Alias for Alignment.setter"""
        self.Alignment = value

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def BaselineAlignment(self):
        return self.com_object.BaselineAlignment

    @BaselineAlignment.setter
    def BaselineAlignment(self, value):
        self.com_object.BaselineAlignment = value

    @property
    def baselinealignment(self):
        """Alias for BaselineAlignment"""
        return self.BaselineAlignment

    @baselinealignment.setter
    def baselinealignment(self, value):
        """Alias for BaselineAlignment.setter"""
        self.BaselineAlignment = value

    @property
    def baseline_alignment(self):
        """Alias for BaselineAlignment"""
        return self.BaselineAlignment

    @baseline_alignment.setter
    def baseline_alignment(self, value):
        """Alias for BaselineAlignment.setter"""
        self.BaselineAlignment = value

    @property
    def Bullet(self):
        return self.com_object.Bullet

    @property
    def bullet(self):
        """Alias for Bullet"""
        return self.Bullet

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def FarEastLineBreakLevel(self):
        return self.com_object.FarEastLineBreakLevel

    @FarEastLineBreakLevel.setter
    def FarEastLineBreakLevel(self, value):
        self.com_object.FarEastLineBreakLevel = value

    @property
    def fareastlinebreaklevel(self):
        """Alias for FarEastLineBreakLevel"""
        return self.FarEastLineBreakLevel

    @fareastlinebreaklevel.setter
    def fareastlinebreaklevel(self, value):
        """Alias for FarEastLineBreakLevel.setter"""
        self.FarEastLineBreakLevel = value

    @property
    def far_east_line_break_level(self):
        """Alias for FarEastLineBreakLevel"""
        return self.FarEastLineBreakLevel

    @far_east_line_break_level.setter
    def far_east_line_break_level(self, value):
        """Alias for FarEastLineBreakLevel.setter"""
        self.FarEastLineBreakLevel = value

    @property
    def FirstLineIndent(self):
        return self.com_object.FirstLineIndent

    @FirstLineIndent.setter
    def FirstLineIndent(self, value):
        self.com_object.FirstLineIndent = value

    @property
    def firstlineindent(self):
        """Alias for FirstLineIndent"""
        return self.FirstLineIndent

    @firstlineindent.setter
    def firstlineindent(self, value):
        """Alias for FirstLineIndent.setter"""
        self.FirstLineIndent = value

    @property
    def first_line_indent(self):
        """Alias for FirstLineIndent"""
        return self.FirstLineIndent

    @first_line_indent.setter
    def first_line_indent(self, value):
        """Alias for FirstLineIndent.setter"""
        self.FirstLineIndent = value

    @property
    def HangingPunctuation(self):
        return self.com_object.HangingPunctuation

    @HangingPunctuation.setter
    def HangingPunctuation(self, value):
        self.com_object.HangingPunctuation = value

    @property
    def hangingpunctuation(self):
        """Alias for HangingPunctuation"""
        return self.HangingPunctuation

    @hangingpunctuation.setter
    def hangingpunctuation(self, value):
        """Alias for HangingPunctuation.setter"""
        self.HangingPunctuation = value

    @property
    def hanging_punctuation(self):
        """Alias for HangingPunctuation"""
        return self.HangingPunctuation

    @hanging_punctuation.setter
    def hanging_punctuation(self, value):
        """Alias for HangingPunctuation.setter"""
        self.HangingPunctuation = value

    @property
    def IndentLevel(self):
        return self.com_object.IndentLevel

    @IndentLevel.setter
    def IndentLevel(self, value):
        self.com_object.IndentLevel = value

    @property
    def indentlevel(self):
        """Alias for IndentLevel"""
        return self.IndentLevel

    @indentlevel.setter
    def indentlevel(self, value):
        """Alias for IndentLevel.setter"""
        self.IndentLevel = value

    @property
    def indent_level(self):
        """Alias for IndentLevel"""
        return self.IndentLevel

    @indent_level.setter
    def indent_level(self, value):
        """Alias for IndentLevel.setter"""
        self.IndentLevel = value

    @property
    def LeftIndent(self):
        return self.com_object.LeftIndent

    @LeftIndent.setter
    def LeftIndent(self, value):
        self.com_object.LeftIndent = value

    @property
    def leftindent(self):
        """Alias for LeftIndent"""
        return self.LeftIndent

    @leftindent.setter
    def leftindent(self, value):
        """Alias for LeftIndent.setter"""
        self.LeftIndent = value

    @property
    def left_indent(self):
        """Alias for LeftIndent"""
        return self.LeftIndent

    @left_indent.setter
    def left_indent(self, value):
        """Alias for LeftIndent.setter"""
        self.LeftIndent = value

    @property
    def LineRuleAfter(self):
        return self.com_object.LineRuleAfter

    @LineRuleAfter.setter
    def LineRuleAfter(self, value):
        self.com_object.LineRuleAfter = value

    @property
    def lineruleafter(self):
        """Alias for LineRuleAfter"""
        return self.LineRuleAfter

    @lineruleafter.setter
    def lineruleafter(self, value):
        """Alias for LineRuleAfter.setter"""
        self.LineRuleAfter = value

    @property
    def line_rule_after(self):
        """Alias for LineRuleAfter"""
        return self.LineRuleAfter

    @line_rule_after.setter
    def line_rule_after(self, value):
        """Alias for LineRuleAfter.setter"""
        self.LineRuleAfter = value

    @property
    def LineRuleBefore(self):
        return self.com_object.LineRuleBefore

    @LineRuleBefore.setter
    def LineRuleBefore(self, value):
        self.com_object.LineRuleBefore = value

    @property
    def linerulebefore(self):
        """Alias for LineRuleBefore"""
        return self.LineRuleBefore

    @linerulebefore.setter
    def linerulebefore(self, value):
        """Alias for LineRuleBefore.setter"""
        self.LineRuleBefore = value

    @property
    def line_rule_before(self):
        """Alias for LineRuleBefore"""
        return self.LineRuleBefore

    @line_rule_before.setter
    def line_rule_before(self, value):
        """Alias for LineRuleBefore.setter"""
        self.LineRuleBefore = value

    @property
    def LineRuleWithin(self):
        return self.com_object.LineRuleWithin

    @LineRuleWithin.setter
    def LineRuleWithin(self, value):
        self.com_object.LineRuleWithin = value

    @property
    def linerulewithin(self):
        """Alias for LineRuleWithin"""
        return self.LineRuleWithin

    @linerulewithin.setter
    def linerulewithin(self, value):
        """Alias for LineRuleWithin.setter"""
        self.LineRuleWithin = value

    @property
    def line_rule_within(self):
        """Alias for LineRuleWithin"""
        return self.LineRuleWithin

    @line_rule_within.setter
    def line_rule_within(self, value):
        """Alias for LineRuleWithin.setter"""
        self.LineRuleWithin = value

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    @property
    def RightIndent(self):
        return self.com_object.RightIndent

    @RightIndent.setter
    def RightIndent(self, value):
        self.com_object.RightIndent = value

    @property
    def rightindent(self):
        """Alias for RightIndent"""
        return self.RightIndent

    @rightindent.setter
    def rightindent(self, value):
        """Alias for RightIndent.setter"""
        self.RightIndent = value

    @property
    def right_indent(self):
        """Alias for RightIndent"""
        return self.RightIndent

    @right_indent.setter
    def right_indent(self, value):
        """Alias for RightIndent.setter"""
        self.RightIndent = value

    @property
    def SpaceAfter(self):
        return self.com_object.SpaceAfter

    @SpaceAfter.setter
    def SpaceAfter(self, value):
        self.com_object.SpaceAfter = value

    @property
    def spaceafter(self):
        """Alias for SpaceAfter"""
        return self.SpaceAfter

    @spaceafter.setter
    def spaceafter(self, value):
        """Alias for SpaceAfter.setter"""
        self.SpaceAfter = value

    @property
    def space_after(self):
        """Alias for SpaceAfter"""
        return self.SpaceAfter

    @space_after.setter
    def space_after(self, value):
        """Alias for SpaceAfter.setter"""
        self.SpaceAfter = value

    @property
    def SpaceBefore(self):
        return self.com_object.SpaceBefore

    @SpaceBefore.setter
    def SpaceBefore(self, value):
        self.com_object.SpaceBefore = value

    @property
    def spacebefore(self):
        """Alias for SpaceBefore"""
        return self.SpaceBefore

    @spacebefore.setter
    def spacebefore(self, value):
        """Alias for SpaceBefore.setter"""
        self.SpaceBefore = value

    @property
    def space_before(self):
        """Alias for SpaceBefore"""
        return self.SpaceBefore

    @space_before.setter
    def space_before(self, value):
        """Alias for SpaceBefore.setter"""
        self.SpaceBefore = value

    @property
    def SpaceWithin(self):
        return self.com_object.SpaceWithin

    @SpaceWithin.setter
    def SpaceWithin(self, value):
        self.com_object.SpaceWithin = value

    @property
    def spacewithin(self):
        """Alias for SpaceWithin"""
        return self.SpaceWithin

    @spacewithin.setter
    def spacewithin(self, value):
        """Alias for SpaceWithin.setter"""
        self.SpaceWithin = value

    @property
    def space_within(self):
        """Alias for SpaceWithin"""
        return self.SpaceWithin

    @space_within.setter
    def space_within(self, value):
        """Alias for SpaceWithin.setter"""
        self.SpaceWithin = value

    @property
    def TabStops(self):
        return self.com_object.TabStops

    @property
    def tabstops(self):
        """Alias for TabStops"""
        return self.TabStops

    @property
    def tab_stops(self):
        """Alias for TabStops"""
        return self.TabStops

    @property
    def TextDirection(self):
        return self.com_object.TextDirection

    @TextDirection.setter
    def TextDirection(self, value):
        self.com_object.TextDirection = value

    @property
    def textdirection(self):
        """Alias for TextDirection"""
        return self.TextDirection

    @textdirection.setter
    def textdirection(self, value):
        """Alias for TextDirection.setter"""
        self.TextDirection = value

    @property
    def text_direction(self):
        """Alias for TextDirection"""
        return self.TextDirection

    @text_direction.setter
    def text_direction(self, value):
        """Alias for TextDirection.setter"""
        self.TextDirection = value

    @property
    def WordWrap(self):
        return self.com_object.WordWrap

    @WordWrap.setter
    def WordWrap(self, value):
        self.com_object.WordWrap = value

    @property
    def wordwrap(self):
        """Alias for WordWrap"""
        return self.WordWrap

    @wordwrap.setter
    def wordwrap(self, value):
        """Alias for WordWrap.setter"""
        self.WordWrap = value

    @property
    def word_wrap(self):
        """Alias for WordWrap"""
        return self.WordWrap

    @word_wrap.setter
    def word_wrap(self, value):
        """Alias for WordWrap.setter"""
        self.WordWrap = value


class Permission:

    def __init__(self, permission=None):
        self.com_object= permission

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def DocumentAuthor(self):
        return self.com_object.DocumentAuthor

    @DocumentAuthor.setter
    def DocumentAuthor(self, value):
        self.com_object.DocumentAuthor = value

    @property
    def documentauthor(self):
        """Alias for DocumentAuthor"""
        return self.DocumentAuthor

    @documentauthor.setter
    def documentauthor(self, value):
        """Alias for DocumentAuthor.setter"""
        self.DocumentAuthor = value

    @property
    def document_author(self):
        """Alias for DocumentAuthor"""
        return self.DocumentAuthor

    @document_author.setter
    def document_author(self, value):
        """Alias for DocumentAuthor.setter"""
        self.DocumentAuthor = value

    @property
    def Enabled(self):
        return self.com_object.Enabled

    @Enabled.setter
    def Enabled(self, value):
        self.com_object.Enabled = value

    @property
    def enabled(self):
        """Alias for Enabled"""
        return self.Enabled

    @enabled.setter
    def enabled(self, value):
        """Alias for Enabled.setter"""
        self.Enabled = value

    @property
    def EnableTrustedBrowser(self):
        return self.com_object.EnableTrustedBrowser

    @EnableTrustedBrowser.setter
    def EnableTrustedBrowser(self, value):
        self.com_object.EnableTrustedBrowser = value

    @property
    def enabletrustedbrowser(self):
        """Alias for EnableTrustedBrowser"""
        return self.EnableTrustedBrowser

    @enabletrustedbrowser.setter
    def enabletrustedbrowser(self, value):
        """Alias for EnableTrustedBrowser.setter"""
        self.EnableTrustedBrowser = value

    @property
    def enable_trusted_browser(self):
        """Alias for EnableTrustedBrowser"""
        return self.EnableTrustedBrowser

    @enable_trusted_browser.setter
    def enable_trusted_browser(self, value):
        """Alias for EnableTrustedBrowser.setter"""
        self.EnableTrustedBrowser = value

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        if hasattr(self.com_object, "GetItem"):
            return self.com_object.GetItem(*arguments)
        else:
            return self.com_object.Item(*arguments)

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    @property
    def PermissionFromPolicy(self):
        return self.com_object.PermissionFromPolicy

    @property
    def permissionfrompolicy(self):
        """Alias for PermissionFromPolicy"""
        return self.PermissionFromPolicy

    @property
    def permission_from_policy(self):
        """Alias for PermissionFromPolicy"""
        return self.PermissionFromPolicy

    @property
    def PolicyDescription(self):
        return self.com_object.PolicyDescription

    @property
    def policydescription(self):
        """Alias for PolicyDescription"""
        return self.PolicyDescription

    @property
    def policy_description(self):
        """Alias for PolicyDescription"""
        return self.PolicyDescription

    @property
    def PolicyName(self):
        return self.com_object.PolicyName

    @property
    def policyname(self):
        """Alias for PolicyName"""
        return self.PolicyName

    @property
    def policy_name(self):
        """Alias for PolicyName"""
        return self.PolicyName

    @property
    def RequestPermissionURL(self):
        return self.com_object.RequestPermissionURL

    @RequestPermissionURL.setter
    def RequestPermissionURL(self, value):
        self.com_object.RequestPermissionURL = value

    @property
    def requestpermissionurl(self):
        """Alias for RequestPermissionURL"""
        return self.RequestPermissionURL

    @requestpermissionurl.setter
    def requestpermissionurl(self, value):
        """Alias for RequestPermissionURL.setter"""
        self.RequestPermissionURL = value

    @property
    def request_permission_u_r_l(self):
        """Alias for RequestPermissionURL"""
        return self.RequestPermissionURL

    @request_permission_u_r_l.setter
    def request_permission_u_r_l(self, value):
        """Alias for RequestPermissionURL.setter"""
        self.RequestPermissionURL = value

    @property
    def SensitivityLabelId(self):
        return self.com_object.SensitivityLabelId

    @SensitivityLabelId.setter
    def SensitivityLabelId(self, value):
        self.com_object.SensitivityLabelId = value

    @property
    def sensitivitylabelid(self):
        """Alias for SensitivityLabelId"""
        return self.SensitivityLabelId

    @sensitivitylabelid.setter
    def sensitivitylabelid(self, value):
        """Alias for SensitivityLabelId.setter"""
        self.SensitivityLabelId = value

    @property
    def sensitivity_label_id(self):
        """Alias for SensitivityLabelId"""
        return self.SensitivityLabelId

    @sensitivity_label_id.setter
    def sensitivity_label_id(self, value):
        """Alias for SensitivityLabelId.setter"""
        self.SensitivityLabelId = value

    @property
    def StoreLicenses(self):
        return self.com_object.StoreLicenses

    @StoreLicenses.setter
    def StoreLicenses(self, value):
        self.com_object.StoreLicenses = value

    @property
    def storelicenses(self):
        """Alias for StoreLicenses"""
        return self.StoreLicenses

    @storelicenses.setter
    def storelicenses(self, value):
        """Alias for StoreLicenses.setter"""
        self.StoreLicenses = value

    @property
    def store_licenses(self):
        """Alias for StoreLicenses"""
        return self.StoreLicenses

    @store_licenses.setter
    def store_licenses(self, value):
        """Alias for StoreLicenses.setter"""
        self.StoreLicenses = value

    def Add(self, UserID=None, Permission=None, ExpirationDate=None):
        arguments = com_arguments([unwrap(a) for a in [UserID, Permission, ExpirationDate]])
        return self.com_object.Add(*arguments)

    def add(self, UserID=None, Permission=None, ExpirationDate=None):
        """Alias for Add"""
        arguments = [UserID, Permission, ExpirationDate]
        return self.Add(*arguments)

    def ApplyPolicy(self, FileName=None):
        arguments = com_arguments([unwrap(a) for a in [FileName]])
        return self.com_object.ApplyPolicy(*arguments)

    def applypolicy(self, FileName=None):
        """Alias for ApplyPolicy"""
        arguments = [FileName]
        return self.ApplyPolicy(*arguments)

    def apply_policy(self, FileName=None):
        """Alias for ApplyPolicy"""
        arguments = [FileName]
        return self.ApplyPolicy(*arguments)

    def RemoveAll(self):
        return self.com_object.RemoveAll()

    def removeall(self):
        """Alias for RemoveAll"""
        return self.RemoveAll()

    def remove_all(self):
        """Alias for RemoveAll"""
        return self.RemoveAll()


class PickerDialog:

    def __init__(self, pickerdialog=None):
        self.com_object= pickerdialog

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def DataHandlerId(self):
        return self.com_object.DataHandlerId

    @DataHandlerId.setter
    def DataHandlerId(self, value):
        self.com_object.DataHandlerId = value

    @property
    def datahandlerid(self):
        """Alias for DataHandlerId"""
        return self.DataHandlerId

    @datahandlerid.setter
    def datahandlerid(self, value):
        """Alias for DataHandlerId.setter"""
        self.DataHandlerId = value

    @property
    def data_handler_id(self):
        """Alias for DataHandlerId"""
        return self.DataHandlerId

    @data_handler_id.setter
    def data_handler_id(self, value):
        """Alias for DataHandlerId.setter"""
        self.DataHandlerId = value

    @property
    def Properties(self):
        return PickerProperties(self.com_object.Properties)

    @property
    def properties(self):
        """Alias for Properties"""
        return self.Properties

    @property
    def Title(self):
        return self.com_object.Title

    @Title.setter
    def Title(self, value):
        self.com_object.Title = value

    @property
    def title(self):
        """Alias for Title"""
        return self.Title

    @title.setter
    def title(self, value):
        """Alias for Title.setter"""
        self.Title = value

    def CreatePickerResults(self):
        return PickerResults(self.com_object.CreatePickerResults())

    def createpickerresults(self):
        """Alias for CreatePickerResults"""
        return self.CreatePickerResults()

    def create_picker_results(self):
        """Alias for CreatePickerResults"""
        return self.CreatePickerResults()

    def Resolve(self, TokenText=None, duplicateDlgMode=None):
        arguments = com_arguments([unwrap(a) for a in [TokenText, duplicateDlgMode]])
        return PickerResults(self.com_object.Resolve(*arguments))

    def resolve(self, TokenText=None, duplicateDlgMode=None):
        """Alias for Resolve"""
        arguments = [TokenText, duplicateDlgMode]
        return self.Resolve(*arguments)

    def Show(self, IsMultiSelect=None, ExistingResults=None):
        arguments = com_arguments([unwrap(a) for a in [IsMultiSelect, ExistingResults]])
        return PickerResults(self.com_object.Show(*arguments))

    def show(self, IsMultiSelect=None, ExistingResults=None):
        """Alias for Show"""
        arguments = [IsMultiSelect, ExistingResults]
        return self.Show(*arguments)


class PickerField:

    def __init__(self, pickerfield=None):
        self.com_object= pickerfield

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def IsHidden(self):
        return self.com_object.IsHidden

    @property
    def ishidden(self):
        """Alias for IsHidden"""
        return self.IsHidden

    @property
    def is_hidden(self):
        """Alias for IsHidden"""
        return self.IsHidden

    @property
    def Name(self):
        return self.com_object.Name

    @property
    def name(self):
        """Alias for Name"""
        return self.Name

    @property
    def Type(self):
        return self.com_object.Type

    @property
    def type(self):
        """Alias for Type"""
        return self.Type


class PickerFields:

    def __init__(self, pickerfields=None):
        self.com_object= pickerfields

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        if hasattr(self.com_object, "GetItem"):
            return self.com_object.GetItem(*arguments)
        else:
            return self.com_object.Item(*arguments)

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)


class PickerProperties:

    def __init__(self, pickerproperties=None):
        self.com_object= pickerproperties

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        if hasattr(self.com_object, "GetItem"):
            return self.com_object.GetItem(*arguments)
        else:
            return self.com_object.Item(*arguments)

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)

    def Add(self, Id=None, Value=None, Type=None):
        arguments = com_arguments([unwrap(a) for a in [Id, Value, Type]])
        return PickerProperty(self.com_object.Add(*arguments))

    def add(self, Id=None, Value=None, Type=None):
        """Alias for Add"""
        arguments = [Id, Value, Type]
        return self.Add(*arguments)

    def Remove(self, Id=None):
        arguments = com_arguments([unwrap(a) for a in [Id]])
        return self.com_object.Remove(*arguments)

    def remove(self, Id=None):
        """Alias for Remove"""
        arguments = [Id]
        return self.Remove(*arguments)


class PickerProperty:

    def __init__(self, pickerproperty=None):
        self.com_object= pickerproperty

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Id(self):
        return self.com_object.Id

    @property
    def id(self):
        """Alias for Id"""
        return self.Id

    @property
    def Type(self):
        return self.com_object.Type

    @property
    def type(self):
        """Alias for Type"""
        return self.Type

    @property
    def Value(self):
        return self.com_object.Value

    @property
    def value(self):
        """Alias for Value"""
        return self.Value


class PickerResult:

    def __init__(self, pickerresult=None):
        self.com_object= pickerresult

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def DisplayName(self):
        return self.com_object.DisplayName

    @DisplayName.setter
    def DisplayName(self, value):
        self.com_object.DisplayName = value

    @property
    def displayname(self):
        """Alias for DisplayName"""
        return self.DisplayName

    @displayname.setter
    def displayname(self, value):
        """Alias for DisplayName.setter"""
        self.DisplayName = value

    @property
    def display_name(self):
        """Alias for DisplayName"""
        return self.DisplayName

    @display_name.setter
    def display_name(self, value):
        """Alias for DisplayName.setter"""
        self.DisplayName = value

    @property
    def DuplicateResults(self):
        return self.com_object.DuplicateResults

    @property
    def duplicateresults(self):
        """Alias for DuplicateResults"""
        return self.DuplicateResults

    @property
    def duplicate_results(self):
        """Alias for DuplicateResults"""
        return self.DuplicateResults

    @property
    def Fields(self):
        return self.com_object.Fields

    @property
    def fields(self):
        """Alias for Fields"""
        return self.Fields

    @property
    def Id(self):
        return self.com_object.Id

    @property
    def id(self):
        """Alias for Id"""
        return self.Id

    @property
    def ItemData(self):
        return self.com_object.ItemData

    @ItemData.setter
    def ItemData(self, value):
        self.com_object.ItemData = value

    @property
    def itemdata(self):
        """Alias for ItemData"""
        return self.ItemData

    @itemdata.setter
    def itemdata(self, value):
        """Alias for ItemData.setter"""
        self.ItemData = value

    @property
    def item_data(self):
        """Alias for ItemData"""
        return self.ItemData

    @item_data.setter
    def item_data(self, value):
        """Alias for ItemData.setter"""
        self.ItemData = value

    @property
    def SIPId(self):
        return self.com_object.SIPId

    @SIPId.setter
    def SIPId(self, value):
        self.com_object.SIPId = value

    @property
    def sipid(self):
        """Alias for SIPId"""
        return self.SIPId

    @sipid.setter
    def sipid(self, value):
        """Alias for SIPId.setter"""
        self.SIPId = value

    @property
    def s_i_p_id(self):
        """Alias for SIPId"""
        return self.SIPId

    @s_i_p_id.setter
    def s_i_p_id(self, value):
        """Alias for SIPId.setter"""
        self.SIPId = value

    @property
    def SubItems(self):
        return self.com_object.SubItems

    @SubItems.setter
    def SubItems(self, value):
        self.com_object.SubItems = value

    @property
    def subitems(self):
        """Alias for SubItems"""
        return self.SubItems

    @subitems.setter
    def subitems(self, value):
        """Alias for SubItems.setter"""
        self.SubItems = value

    @property
    def sub_items(self):
        """Alias for SubItems"""
        return self.SubItems

    @sub_items.setter
    def sub_items(self, value):
        """Alias for SubItems.setter"""
        self.SubItems = value

    @property
    def Type(self):
        return self.com_object.Type

    @Type.setter
    def Type(self, value):
        self.com_object.Type = value

    @property
    def type(self):
        """Alias for Type"""
        return self.Type

    @type.setter
    def type(self, value):
        """Alias for Type.setter"""
        self.Type = value


class PickerResults:

    def __init__(self, pickerresults=None):
        self.com_object= pickerresults

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        if hasattr(self.com_object, "GetItem"):
            return self.com_object.GetItem(*arguments)
        else:
            return self.com_object.Item(*arguments)

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)

    def Add(self, Id=None, DisplayName=None, Type=None, SIPId=None, ItemData=None, SubItems=None):
        arguments = com_arguments([unwrap(a) for a in [Id, DisplayName, Type, SIPId, ItemData, SubItems]])
        return PickerResult(self.com_object.Add(*arguments))

    def add(self, Id=None, DisplayName=None, Type=None, SIPId=None, ItemData=None, SubItems=None):
        """Alias for Add"""
        arguments = [Id, DisplayName, Type, SIPId, ItemData, SubItems]
        return self.Add(*arguments)


class PictureEffect:

    def __init__(self, pictureeffect=None):
        self.com_object= pictureeffect

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def EffectParameters(self):
        return EffectParameter(self.com_object.EffectParameters)

    @property
    def effectparameters(self):
        """Alias for EffectParameters"""
        return self.EffectParameters

    @property
    def effect_parameters(self):
        """Alias for EffectParameters"""
        return self.EffectParameters

    @property
    def Position(self):
        return self.com_object.Position

    @Position.setter
    def Position(self, value):
        self.com_object.Position = value

    @property
    def position(self):
        """Alias for Position"""
        return self.Position

    @position.setter
    def position(self, value):
        """Alias for Position.setter"""
        self.Position = value

    @property
    def Type(self):
        return self.com_object.Type

    @property
    def type(self):
        """Alias for Type"""
        return self.Type

    @property
    def Visible(self):
        return self.com_object.Visible

    @Visible.setter
    def Visible(self, value):
        self.com_object.Visible = value

    @property
    def visible(self):
        """Alias for Visible"""
        return self.Visible

    @visible.setter
    def visible(self, value):
        """Alias for Visible.setter"""
        self.Visible = value

    def Delete(self):
        return self.com_object.Delete()

    def delete(self):
        """Alias for Delete"""
        return self.Delete()


class PictureEffects:

    def __init__(self, pictureeffects=None):
        self.com_object= pictureeffects

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        if hasattr(self.com_object, "GetItem"):
            return self.com_object.GetItem(*arguments)
        else:
            return self.com_object.Item(*arguments)

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)

    def Delete(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        return self.com_object.Delete(*arguments)

    def delete(self, Index=None):
        """Alias for Delete"""
        arguments = [Index]
        return self.Delete(*arguments)

    def Insert(self, EffectType=None, Position=None):
        arguments = com_arguments([unwrap(a) for a in [EffectType, Position]])
        return PictureEffect(self.com_object.Insert(*arguments))

    def insert(self, EffectType=None, Position=None):
        """Alias for Insert"""
        arguments = [EffectType, Position]
        return self.Insert(*arguments)


class PolicyItem:

    def __init__(self, policyitem=None):
        self.com_object= policyitem

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Data(self):
        return self.com_object.Data

    @property
    def data(self):
        """Alias for Data"""
        return self.Data

    @property
    def Description(self):
        return self.com_object.Description

    @property
    def description(self):
        """Alias for Description"""
        return self.Description

    @property
    def Id(self):
        return self.com_object.Id

    @property
    def id(self):
        """Alias for Id"""
        return self.Id

    @property
    def Name(self):
        return self.com_object.Name

    @property
    def name(self):
        """Alias for Name"""
        return self.Name

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent


class ReflectionFormat:

    def __init__(self, reflectionformat=None):
        self.com_object= reflectionformat

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Blur(self):
        return self.com_object.Blur

    @Blur.setter
    def Blur(self, value):
        self.com_object.Blur = value

    @property
    def blur(self):
        """Alias for Blur"""
        return self.Blur

    @blur.setter
    def blur(self, value):
        """Alias for Blur.setter"""
        self.Blur = value

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Offset(self):
        return self.com_object.Offset

    @Offset.setter
    def Offset(self, value):
        self.com_object.Offset = value

    @property
    def offset(self):
        """Alias for Offset"""
        return self.Offset

    @offset.setter
    def offset(self, value):
        """Alias for Offset.setter"""
        self.Offset = value

    @property
    def Size(self):
        return self.com_object.Size

    @Size.setter
    def Size(self, value):
        self.com_object.Size = value

    @property
    def size(self):
        """Alias for Size"""
        return self.Size

    @size.setter
    def size(self, value):
        """Alias for Size.setter"""
        self.Size = value

    @property
    def Transparency(self):
        return self.com_object.Transparency

    @Transparency.setter
    def Transparency(self, value):
        self.com_object.Transparency = value

    @property
    def transparency(self):
        """Alias for Transparency"""
        return self.Transparency

    @transparency.setter
    def transparency(self, value):
        """Alias for Transparency.setter"""
        self.Transparency = value

    @property
    def Type(self):
        return self.com_object.Type

    @Type.setter
    def Type(self, value):
        self.com_object.Type = value

    @property
    def type(self):
        """Alias for Type"""
        return self.Type

    @type.setter
    def type(self, value):
        """Alias for Type.setter"""
        self.Type = value


# RibbonControlSize enumeration
RibbonControlSizeLarge = 1
RibbonControlSizeRegular = 0

class Ruler2:

    def __init__(self, ruler2=None):
        self.com_object= ruler2

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Levels(self):
        return self.com_object.Levels

    @property
    def levels(self):
        """Alias for Levels"""
        return self.Levels

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    @property
    def TabStops(self):
        return self.com_object.TabStops

    @property
    def tabstops(self):
        """Alias for TabStops"""
        return self.TabStops

    @property
    def tab_stops(self):
        """Alias for TabStops"""
        return self.TabStops


class RulerLevel2:

    def __init__(self, rulerlevel2=None):
        self.com_object= rulerlevel2

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def FirstMargin(self):
        return self.com_object.FirstMargin

    @FirstMargin.setter
    def FirstMargin(self, value):
        self.com_object.FirstMargin = value

    @property
    def firstmargin(self):
        """Alias for FirstMargin"""
        return self.FirstMargin

    @firstmargin.setter
    def firstmargin(self, value):
        """Alias for FirstMargin.setter"""
        self.FirstMargin = value

    @property
    def first_margin(self):
        """Alias for FirstMargin"""
        return self.FirstMargin

    @first_margin.setter
    def first_margin(self, value):
        """Alias for FirstMargin.setter"""
        self.FirstMargin = value

    @property
    def LeftMargin(self):
        return self.com_object.LeftMargin

    @LeftMargin.setter
    def LeftMargin(self, value):
        self.com_object.LeftMargin = value

    @property
    def leftmargin(self):
        """Alias for LeftMargin"""
        return self.LeftMargin

    @leftmargin.setter
    def leftmargin(self, value):
        """Alias for LeftMargin.setter"""
        self.LeftMargin = value

    @property
    def left_margin(self):
        """Alias for LeftMargin"""
        return self.LeftMargin

    @left_margin.setter
    def left_margin(self, value):
        """Alias for LeftMargin.setter"""
        self.LeftMargin = value

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent


class RulerLevels2:

    def __init__(self, rulerlevels2=None):
        self.com_object= rulerlevels2

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        return RulerLevel2(self.com_object.Item(*arguments))

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)


class ScopeFolder:

    def __init__(self, scopefolder=None):
        self.com_object= scopefolder

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Name(self):
        return self.com_object.Name

    @property
    def name(self):
        """Alias for Name"""
        return self.Name

    @property
    def Path(self):
        return self.com_object.Path

    @property
    def path(self):
        """Alias for Path"""
        return self.Path

    @property
    def ScopeFolders(self):
        return self.com_object.ScopeFolders

    @property
    def scopefolders(self):
        """Alias for ScopeFolders"""
        return self.ScopeFolders

    @property
    def scope_folders(self):
        """Alias for ScopeFolders"""
        return self.ScopeFolders

    def AddToSearchFolders(self):
        return self.com_object.AddToSearchFolders()

    def addtosearchfolders(self):
        """Alias for AddToSearchFolders"""
        return self.AddToSearchFolders()

    def add_to_search_folders(self):
        """Alias for AddToSearchFolders"""
        return self.AddToSearchFolders()


class ScopeFolders:

    def __init__(self, scopefolders=None):
        self.com_object= scopefolders

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        if hasattr(self.com_object, "GetItem"):
            return self.com_object.GetItem(*arguments)
        else:
            return self.com_object.Item(*arguments)

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)


class SearchFolders:

    def __init__(self, searchfolders=None):
        self.com_object= searchfolders

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        if hasattr(self.com_object, "GetItem"):
            return self.com_object.GetItem(*arguments)
        else:
            return self.com_object.Item(*arguments)

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)

    def Add(self, ScopeFolder=None):
        arguments = com_arguments([unwrap(a) for a in [ScopeFolder]])
        return self.com_object.Add(*arguments)

    def add(self, ScopeFolder=None):
        """Alias for Add"""
        arguments = [ScopeFolder]
        return self.Add(*arguments)

    def Remove(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        return self.com_object.Remove(*arguments)

    def remove(self, Index=None):
        """Alias for Remove"""
        arguments = [Index]
        return self.Remove(*arguments)


class SearchScope:

    def __init__(self, searchscope=None):
        self.com_object= searchscope

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def ScopeFolder(self):
        return self.com_object.ScopeFolder

    @property
    def scopefolder(self):
        """Alias for ScopeFolder"""
        return self.ScopeFolder

    @property
    def scope_folder(self):
        """Alias for ScopeFolder"""
        return self.ScopeFolder

    @property
    def Type(self):
        return self.com_object.Type

    @property
    def type(self):
        """Alias for Type"""
        return self.Type


class SearchScopes:

    def __init__(self, searchscopes=None):
        self.com_object= searchscopes

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        if hasattr(self.com_object, "GetItem"):
            return self.com_object.GetItem(*arguments)
        else:
            return self.com_object.Item(*arguments)

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)


class SensitivityLabel:

    def __init__(self, sensitivitylabel=None):
        self.com_object= sensitivitylabel

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    def CreateLabelInfo(self):
        return self.com_object.CreateLabelInfo()

    def createlabelinfo(self):
        """Alias for CreateLabelInfo"""
        return self.CreateLabelInfo()

    def create_label_info(self):
        """Alias for CreateLabelInfo"""
        return self.CreateLabelInfo()

    def GetLabel(self):
        return self.com_object.GetLabel()

    def getlabel(self):
        """Alias for GetLabel"""
        return self.GetLabel()

    def get_label(self):
        """Alias for GetLabel"""
        return self.GetLabel()

    def SetLabel(self, LabelInfo=None, Context=None):
        arguments = com_arguments([unwrap(a) for a in [LabelInfo, Context]])
        return self.com_object.SetLabel(*arguments)

    def setlabel(self, LabelInfo=None, Context=None):
        """Alias for SetLabel"""
        arguments = [LabelInfo, Context]
        return self.SetLabel(*arguments)

    def set_label(self, LabelInfo=None, Context=None):
        """Alias for SetLabel"""
        arguments = [LabelInfo, Context]
        return self.SetLabel(*arguments)


class SensitivityLabelInitInfo:

    def __init__(self, sensitivitylabelinitinfo=None):
        self.com_object= sensitivitylabelinitinfo

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def SensitivityLabelsPolicyXml(self):
        return self.com_object.SensitivityLabelsPolicyXml

    @property
    def sensitivitylabelspolicyxml(self):
        """Alias for SensitivityLabelsPolicyXml"""
        return self.SensitivityLabelsPolicyXml

    @property
    def sensitivity_labels_policy_xml(self):
        """Alias for SensitivityLabelsPolicyXml"""
        return self.SensitivityLabelsPolicyXml

    @property
    def UserId(self):
        return self.com_object.UserId

    @property
    def userid(self):
        """Alias for UserId"""
        return self.UserId

    @property
    def user_id(self):
        """Alias for UserId"""
        return self.UserId


class SensitivityLabelPolicy:

    def __init__(self, sensitivitylabelpolicy=None):
        self.com_object= sensitivitylabelpolicy

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    def BeginInitialize(self):
        return self.com_object.BeginInitialize()

    def begininitialize(self):
        """Alias for BeginInitialize"""
        return self.BeginInitialize()

    def begin_initialize(self):
        """Alias for BeginInitialize"""
        return self.BeginInitialize()

    def CompleteInitialize(self, SensitivityLabelInitInfo=None):
        arguments = com_arguments([unwrap(a) for a in [SensitivityLabelInitInfo]])
        return self.com_object.CompleteInitialize(*arguments)

    def completeinitialize(self, SensitivityLabelInitInfo=None):
        """Alias for CompleteInitialize"""
        arguments = [SensitivityLabelInitInfo]
        return self.CompleteInitialize(*arguments)

    def complete_initialize(self, SensitivityLabelInitInfo=None):
        """Alias for CompleteInitialize"""
        arguments = [SensitivityLabelInitInfo]
        return self.CompleteInitialize(*arguments)

    def CreateSensitivityLabelInitInfo(self):
        return self.com_object.CreateSensitivityLabelInitInfo()

    def createsensitivitylabelinitinfo(self):
        """Alias for CreateSensitivityLabelInitInfo"""
        return self.CreateSensitivityLabelInitInfo()

    def create_sensitivity_label_init_info(self):
        """Alias for CreateSensitivityLabelInitInfo"""
        return self.CreateSensitivityLabelInitInfo()


class ServerPolicy:

    def __init__(self, serverpolicy=None):
        self.com_object= serverpolicy

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def BlockPreview(self):
        return self.com_object.BlockPreview

    @property
    def blockpreview(self):
        """Alias for BlockPreview"""
        return self.BlockPreview

    @property
    def block_preview(self):
        """Alias for BlockPreview"""
        return self.BlockPreview

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Description(self):
        return self.com_object.Description

    @property
    def description(self):
        """Alias for Description"""
        return self.Description

    @property
    def Id(self):
        return self.com_object.Id

    @property
    def id(self):
        """Alias for Id"""
        return self.Id

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        if hasattr(self.com_object, "GetItem"):
            return self.com_object.GetItem(*arguments)
        else:
            return self.com_object.Item(*arguments)

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)

    @property
    def Name(self):
        return self.com_object.Name

    @property
    def name(self):
        """Alias for Name"""
        return self.Name

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    @property
    def Statement(self):
        return self.com_object.Statement

    @property
    def statement(self):
        """Alias for Statement"""
        return self.Statement


class SharedWorkspace:

    def __init__(self, sharedworkspace=None):
        self.com_object= sharedworkspace

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Connected(self):
        return self.com_object.Connected

    @property
    def connected(self):
        """Alias for Connected"""
        return self.Connected

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Files(self):
        return self.com_object.Files

    @property
    def files(self):
        """Alias for Files"""
        return self.Files

    @property
    def Folders(self):
        return self.com_object.Folders

    @property
    def folders(self):
        """Alias for Folders"""
        return self.Folders

    @property
    def LastRefreshed(self):
        return self.com_object.LastRefreshed

    @property
    def lastrefreshed(self):
        """Alias for LastRefreshed"""
        return self.LastRefreshed

    @property
    def last_refreshed(self):
        """Alias for LastRefreshed"""
        return self.LastRefreshed

    @property
    def Links(self):
        return self.com_object.Links

    @property
    def links(self):
        """Alias for Links"""
        return self.Links

    @property
    def Members(self):
        return self.com_object.Members

    @property
    def members(self):
        """Alias for Members"""
        return self.Members

    @property
    def Name(self):
        return self.com_object.Name

    @Name.setter
    def Name(self, value):
        self.com_object.Name = value

    @property
    def name(self):
        """Alias for Name"""
        return self.Name

    @name.setter
    def name(self, value):
        """Alias for Name.setter"""
        self.Name = value

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    @property
    def SourceURL(self):
        return self.com_object.SourceURL

    @property
    def sourceurl(self):
        """Alias for SourceURL"""
        return self.SourceURL

    @property
    def source_u_r_l(self):
        """Alias for SourceURL"""
        return self.SourceURL

    @property
    def Tasks(self):
        return self.com_object.Tasks

    @property
    def tasks(self):
        """Alias for Tasks"""
        return self.Tasks

    @property
    def URL(self):
        return self.com_object.URL

    @property
    def url(self):
        """Alias for URL"""
        return self.URL

    @property
    def u_r_l(self):
        """Alias for URL"""
        return self.URL

    def CreateNew(self, URL=None, Name=None):
        arguments = com_arguments([unwrap(a) for a in [URL, Name]])
        return self.com_object.CreateNew(*arguments)

    def createnew(self, URL=None, Name=None):
        """Alias for CreateNew"""
        arguments = [URL, Name]
        return self.CreateNew(*arguments)

    def create_new(self, URL=None, Name=None):
        """Alias for CreateNew"""
        arguments = [URL, Name]
        return self.CreateNew(*arguments)

    def Delete(self):
        return self.com_object.Delete()

    def delete(self):
        """Alias for Delete"""
        return self.Delete()

    def Disconnect(self):
        return self.com_object.Disconnect()

    def disconnect(self):
        """Alias for Disconnect"""
        return self.Disconnect()

    def Refresh(self):
        return self.com_object.Refresh()

    def refresh(self):
        """Alias for Refresh"""
        return self.Refresh()

    def RemoveDocument(self):
        return self.com_object.RemoveDocument()

    def removedocument(self):
        """Alias for RemoveDocument"""
        return self.RemoveDocument()

    def remove_document(self):
        """Alias for RemoveDocument"""
        return self.RemoveDocument()


class SharedWorkspaceFile:

    def __init__(self, sharedworkspacefile=None):
        self.com_object= sharedworkspacefile

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def CreatedBy(self):
        return self.com_object.CreatedBy

    @property
    def createdby(self):
        """Alias for CreatedBy"""
        return self.CreatedBy

    @property
    def created_by(self):
        """Alias for CreatedBy"""
        return self.CreatedBy

    @property
    def CreatedDate(self):
        return self.com_object.CreatedDate

    @property
    def createddate(self):
        """Alias for CreatedDate"""
        return self.CreatedDate

    @property
    def created_date(self):
        """Alias for CreatedDate"""
        return self.CreatedDate

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def ModifiedBy(self):
        return self.com_object.ModifiedBy

    @property
    def modifiedby(self):
        """Alias for ModifiedBy"""
        return self.ModifiedBy

    @property
    def modified_by(self):
        """Alias for ModifiedBy"""
        return self.ModifiedBy

    @property
    def ModifiedDate(self):
        return self.com_object.ModifiedDate

    @property
    def modifieddate(self):
        """Alias for ModifiedDate"""
        return self.ModifiedDate

    @property
    def modified_date(self):
        """Alias for ModifiedDate"""
        return self.ModifiedDate

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    @property
    def URL(self):
        return self.com_object.URL

    @property
    def url(self):
        """Alias for URL"""
        return self.URL

    @property
    def u_r_l(self):
        """Alias for URL"""
        return self.URL

    def Delete(self):
        return self.com_object.Delete()

    def delete(self):
        """Alias for Delete"""
        return self.Delete()


class SharedWorkspaceFiles:

    def __init__(self, sharedworkspacefiles=None):
        self.com_object= sharedworkspacefiles

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        if hasattr(self.com_object, "GetItem"):
            return self.com_object.GetItem(*arguments)
        else:
            return self.com_object.Item(*arguments)

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)

    @property
    def ItemCountExceeded(self):
        return self.com_object.ItemCountExceeded

    @property
    def itemcountexceeded(self):
        """Alias for ItemCountExceeded"""
        return self.ItemCountExceeded

    @property
    def item_count_exceeded(self):
        """Alias for ItemCountExceeded"""
        return self.ItemCountExceeded

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    def Add(self, FileName=None, ParentFolder=None, OverwriteIfFileAlreadyExists=None, KeepInSync=None):
        arguments = com_arguments([unwrap(a) for a in [FileName, ParentFolder, OverwriteIfFileAlreadyExists, KeepInSync]])
        return self.com_object.Add(*arguments)

    def add(self, FileName=None, ParentFolder=None, OverwriteIfFileAlreadyExists=None, KeepInSync=None):
        """Alias for Add"""
        arguments = [FileName, ParentFolder, OverwriteIfFileAlreadyExists, KeepInSync]
        return self.Add(*arguments)


class SharedWorkspaceFolder:

    def __init__(self, sharedworkspacefolder=None):
        self.com_object= sharedworkspacefolder

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def FolderName(self):
        return self.com_object.FolderName

    @property
    def foldername(self):
        """Alias for FolderName"""
        return self.FolderName

    @property
    def folder_name(self):
        """Alias for FolderName"""
        return self.FolderName

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    def Delete(self, DeleteEvenIfFolderContainsFiles=None):
        arguments = com_arguments([unwrap(a) for a in [DeleteEvenIfFolderContainsFiles]])
        return self.com_object.Delete(*arguments)

    def delete(self, DeleteEvenIfFolderContainsFiles=None):
        """Alias for Delete"""
        arguments = [DeleteEvenIfFolderContainsFiles]
        return self.Delete(*arguments)


class SharedWorkspaceFolders:

    def __init__(self, sharedworkspacefolders=None):
        self.com_object= sharedworkspacefolders

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        if hasattr(self.com_object, "GetItem"):
            return self.com_object.GetItem(*arguments)
        else:
            return self.com_object.Item(*arguments)

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)

    @property
    def ItemCountExceeded(self):
        return self.com_object.ItemCountExceeded

    @property
    def itemcountexceeded(self):
        """Alias for ItemCountExceeded"""
        return self.ItemCountExceeded

    @property
    def item_count_exceeded(self):
        """Alias for ItemCountExceeded"""
        return self.ItemCountExceeded

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    def Add(self, FolderName=None, ParentFolder=None):
        arguments = com_arguments([unwrap(a) for a in [FolderName, ParentFolder]])
        return self.com_object.Add(*arguments)

    def add(self, FolderName=None, ParentFolder=None):
        """Alias for Add"""
        arguments = [FolderName, ParentFolder]
        return self.Add(*arguments)


class SharedWorkspaceLink:

    def __init__(self, sharedworkspacelink=None):
        self.com_object= sharedworkspacelink

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def CreatedBy(self):
        return self.com_object.CreatedBy

    @property
    def createdby(self):
        """Alias for CreatedBy"""
        return self.CreatedBy

    @property
    def created_by(self):
        """Alias for CreatedBy"""
        return self.CreatedBy

    @property
    def CreatedDate(self):
        return self.com_object.CreatedDate

    @property
    def createddate(self):
        """Alias for CreatedDate"""
        return self.CreatedDate

    @property
    def created_date(self):
        """Alias for CreatedDate"""
        return self.CreatedDate

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Description(self):
        return self.com_object.Description

    @Description.setter
    def Description(self, value):
        self.com_object.Description = value

    @property
    def description(self):
        """Alias for Description"""
        return self.Description

    @description.setter
    def description(self, value):
        """Alias for Description.setter"""
        self.Description = value

    @property
    def ModifiedBy(self):
        return self.com_object.ModifiedBy

    @property
    def modifiedby(self):
        """Alias for ModifiedBy"""
        return self.ModifiedBy

    @property
    def modified_by(self):
        """Alias for ModifiedBy"""
        return self.ModifiedBy

    @property
    def ModifiedDate(self):
        return self.com_object.ModifiedDate

    @property
    def modifieddate(self):
        """Alias for ModifiedDate"""
        return self.ModifiedDate

    @property
    def modified_date(self):
        """Alias for ModifiedDate"""
        return self.ModifiedDate

    @property
    def Notes(self):
        return self.com_object.Notes

    @Notes.setter
    def Notes(self, value):
        self.com_object.Notes = value

    @property
    def notes(self):
        """Alias for Notes"""
        return self.Notes

    @notes.setter
    def notes(self, value):
        """Alias for Notes.setter"""
        self.Notes = value

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    @property
    def URL(self):
        return self.com_object.URL

    @URL.setter
    def URL(self, value):
        self.com_object.URL = value

    @property
    def url(self):
        """Alias for URL"""
        return self.URL

    @url.setter
    def url(self, value):
        """Alias for URL.setter"""
        self.URL = value

    @property
    def u_r_l(self):
        """Alias for URL"""
        return self.URL

    @u_r_l.setter
    def u_r_l(self, value):
        """Alias for URL.setter"""
        self.URL = value

    def Delete(self):
        return self.com_object.Delete()

    def delete(self):
        """Alias for Delete"""
        return self.Delete()

    def Save(self, bstrQueryName=None):
        arguments = com_arguments([unwrap(a) for a in [bstrQueryName]])
        return self.com_object.Save(*arguments)

    def save(self, bstrQueryName=None):
        """Alias for Save"""
        arguments = [bstrQueryName]
        return self.Save(*arguments)


class SharedWorkspaceLinks:

    def __init__(self, sharedworkspacelinks=None):
        self.com_object= sharedworkspacelinks

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        if hasattr(self.com_object, "GetItem"):
            return self.com_object.GetItem(*arguments)
        else:
            return self.com_object.Item(*arguments)

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)

    @property
    def ItemCountExceeded(self):
        return self.com_object.ItemCountExceeded

    @property
    def itemcountexceeded(self):
        """Alias for ItemCountExceeded"""
        return self.ItemCountExceeded

    @property
    def item_count_exceeded(self):
        """Alias for ItemCountExceeded"""
        return self.ItemCountExceeded

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    def Add(self, URL=None, Description=None, Notes=None):
        arguments = com_arguments([unwrap(a) for a in [URL, Description, Notes]])
        return SharedWorkspaceLink(self.com_object.Add(*arguments))

    def add(self, URL=None, Description=None, Notes=None):
        """Alias for Add"""
        arguments = [URL, Description, Notes]
        return self.Add(*arguments)


class SharedWorkspaceMember:

    def __init__(self, sharedworkspacemember=None):
        self.com_object= sharedworkspacemember

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def DomainName(self):
        return self.com_object.DomainName

    @property
    def domainname(self):
        """Alias for DomainName"""
        return self.DomainName

    @property
    def domain_name(self):
        """Alias for DomainName"""
        return self.DomainName

    @property
    def Email(self):
        return self.com_object.Email

    @property
    def email(self):
        """Alias for Email"""
        return self.Email

    @property
    def Name(self):
        return self.com_object.Name

    @property
    def name(self):
        """Alias for Name"""
        return self.Name

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    def Delete(self):
        return self.com_object.Delete()

    def delete(self):
        """Alias for Delete"""
        return self.Delete()


class SharedWorkspaceMembers:

    def __init__(self, sharedworkspacemembers=None):
        self.com_object= sharedworkspacemembers

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        if hasattr(self.com_object, "GetItem"):
            return self.com_object.GetItem(*arguments)
        else:
            return self.com_object.Item(*arguments)

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)

    @property
    def ItemCountExceeded(self):
        return self.com_object.ItemCountExceeded

    @property
    def itemcountexceeded(self):
        """Alias for ItemCountExceeded"""
        return self.ItemCountExceeded

    @property
    def item_count_exceeded(self):
        """Alias for ItemCountExceeded"""
        return self.ItemCountExceeded

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    def Add(self, Email=None, DomainName=None, DisplayName=None, Role=None):
        arguments = com_arguments([unwrap(a) for a in [Email, DomainName, DisplayName, Role]])
        return self.com_object.Add(*arguments)

    def add(self, Email=None, DomainName=None, DisplayName=None, Role=None):
        """Alias for Add"""
        arguments = [Email, DomainName, DisplayName, Role]
        return self.Add(*arguments)


class SharedWorkspaceTask:

    def __init__(self, sharedworkspacetask=None):
        self.com_object= sharedworkspacetask

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def AssignedTo(self):
        return self.com_object.AssignedTo

    @AssignedTo.setter
    def AssignedTo(self, value):
        self.com_object.AssignedTo = value

    @property
    def assignedto(self):
        """Alias for AssignedTo"""
        return self.AssignedTo

    @assignedto.setter
    def assignedto(self, value):
        """Alias for AssignedTo.setter"""
        self.AssignedTo = value

    @property
    def assigned_to(self):
        """Alias for AssignedTo"""
        return self.AssignedTo

    @assigned_to.setter
    def assigned_to(self, value):
        """Alias for AssignedTo.setter"""
        self.AssignedTo = value

    @property
    def CreatedBy(self):
        return self.com_object.CreatedBy

    @property
    def createdby(self):
        """Alias for CreatedBy"""
        return self.CreatedBy

    @property
    def created_by(self):
        """Alias for CreatedBy"""
        return self.CreatedBy

    @property
    def CreatedDate(self):
        return self.com_object.CreatedDate

    @property
    def createddate(self):
        """Alias for CreatedDate"""
        return self.CreatedDate

    @property
    def created_date(self):
        """Alias for CreatedDate"""
        return self.CreatedDate

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Description(self):
        return self.com_object.Description

    @Description.setter
    def Description(self, value):
        self.com_object.Description = value

    @property
    def description(self):
        """Alias for Description"""
        return self.Description

    @description.setter
    def description(self, value):
        """Alias for Description.setter"""
        self.Description = value

    @property
    def DueDate(self):
        return self.com_object.DueDate

    @DueDate.setter
    def DueDate(self, value):
        self.com_object.DueDate = value

    @property
    def duedate(self):
        """Alias for DueDate"""
        return self.DueDate

    @duedate.setter
    def duedate(self, value):
        """Alias for DueDate.setter"""
        self.DueDate = value

    @property
    def due_date(self):
        """Alias for DueDate"""
        return self.DueDate

    @due_date.setter
    def due_date(self, value):
        """Alias for DueDate.setter"""
        self.DueDate = value

    @property
    def ModifiedBy(self):
        return self.com_object.ModifiedBy

    @property
    def modifiedby(self):
        """Alias for ModifiedBy"""
        return self.ModifiedBy

    @property
    def modified_by(self):
        """Alias for ModifiedBy"""
        return self.ModifiedBy

    @property
    def ModifiedDate(self):
        return self.com_object.ModifiedDate

    @property
    def modifieddate(self):
        """Alias for ModifiedDate"""
        return self.ModifiedDate

    @property
    def modified_date(self):
        """Alias for ModifiedDate"""
        return self.ModifiedDate

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    @property
    def Priority(self):
        return self.com_object.Priority

    @Priority.setter
    def Priority(self, value):
        self.com_object.Priority = value

    @property
    def priority(self):
        """Alias for Priority"""
        return self.Priority

    @priority.setter
    def priority(self, value):
        """Alias for Priority.setter"""
        self.Priority = value

    @property
    def Status(self):
        return self.com_object.Status

    @Status.setter
    def Status(self, value):
        self.com_object.Status = value

    @property
    def status(self):
        """Alias for Status"""
        return self.Status

    @status.setter
    def status(self, value):
        """Alias for Status.setter"""
        self.Status = value

    @property
    def Title(self):
        return self.com_object.Title

    @Title.setter
    def Title(self, value):
        self.com_object.Title = value

    @property
    def title(self):
        """Alias for Title"""
        return self.Title

    @title.setter
    def title(self, value):
        """Alias for Title.setter"""
        self.Title = value

    def Delete(self):
        return self.com_object.Delete()

    def delete(self):
        """Alias for Delete"""
        return self.Delete()

    def Save(self, bstrQueryName=None):
        arguments = com_arguments([unwrap(a) for a in [bstrQueryName]])
        return self.com_object.Save(*arguments)

    def save(self, bstrQueryName=None):
        """Alias for Save"""
        arguments = [bstrQueryName]
        return self.Save(*arguments)


class SharedWorkspaceTasks:

    def __init__(self, sharedworkspacetasks=None):
        self.com_object= sharedworkspacetasks

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        if hasattr(self.com_object, "GetItem"):
            return self.com_object.GetItem(*arguments)
        else:
            return self.com_object.Item(*arguments)

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)

    @property
    def ItemCountExceeded(self):
        return self.com_object.ItemCountExceeded

    @property
    def itemcountexceeded(self):
        """Alias for ItemCountExceeded"""
        return self.ItemCountExceeded

    @property
    def item_count_exceeded(self):
        """Alias for ItemCountExceeded"""
        return self.ItemCountExceeded

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    def Add(self, Title=None, Status=None, Priority=None, Assignee=None, Description=None, DueDate=None):
        arguments = com_arguments([unwrap(a) for a in [Title, Status, Priority, Assignee, Description, DueDate]])
        return self.com_object.Add(*arguments)

    def add(self, Title=None, Status=None, Priority=None, Assignee=None, Description=None, DueDate=None):
        """Alias for Add"""
        arguments = [Title, Status, Priority, Assignee, Description, DueDate]
        return self.Add(*arguments)


class Signature:

    def __init__(self, signature=None):
        self.com_object= signature

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def CanSetup(self):
        return self.com_object.CanSetup

    @property
    def cansetup(self):
        """Alias for CanSetup"""
        return self.CanSetup

    @property
    def can_setup(self):
        """Alias for CanSetup"""
        return self.CanSetup

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Details(self):
        return self.com_object.Details

    @property
    def details(self):
        """Alias for Details"""
        return self.Details

    @property
    def IsSignatureLine(self):
        return self.com_object.IsSignatureLine

    @property
    def issignatureline(self):
        """Alias for IsSignatureLine"""
        return self.IsSignatureLine

    @property
    def is_signature_line(self):
        """Alias for IsSignatureLine"""
        return self.IsSignatureLine

    @property
    def IsSigned(self):
        return self.com_object.IsSigned

    @property
    def issigned(self):
        """Alias for IsSigned"""
        return self.IsSigned

    @property
    def is_signed(self):
        """Alias for IsSigned"""
        return self.IsSigned

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    @property
    def Setup(self):
        return self.com_object.Setup

    @property
    def setup(self):
        """Alias for Setup"""
        return self.Setup

    @property
    def SignatureLineShape(self):
        return self.com_object.SignatureLineShape

    @property
    def signaturelineshape(self):
        """Alias for SignatureLineShape"""
        return self.SignatureLineShape

    @property
    def signature_line_shape(self):
        """Alias for SignatureLineShape"""
        return self.SignatureLineShape

    @property
    def SortHint(self):
        return self.com_object.SortHint

    @property
    def sorthint(self):
        """Alias for SortHint"""
        return self.SortHint

    @property
    def sort_hint(self):
        """Alias for SortHint"""
        return self.SortHint

    def Delete(self):
        return self.com_object.Delete()

    def delete(self):
        """Alias for Delete"""
        return self.Delete()

    def ShowDetails(self):
        return self.com_object.ShowDetails()

    def showdetails(self):
        """Alias for ShowDetails"""
        return self.ShowDetails()

    def show_details(self):
        """Alias for ShowDetails"""
        return self.ShowDetails()

    def Sign(self, varSigImg=None, varDelSuggSigner=None, varDelSuggSignerLine2=None, varDelSuggSignerEmail=None):
        arguments = com_arguments([unwrap(a) for a in [varSigImg, varDelSuggSigner, varDelSuggSignerLine2, varDelSuggSignerEmail]])
        return self.com_object.Sign(*arguments)

    def sign(self, varSigImg=None, varDelSuggSigner=None, varDelSuggSignerLine2=None, varDelSuggSignerEmail=None):
        """Alias for Sign"""
        arguments = [varSigImg, varDelSuggSigner, varDelSuggSignerLine2, varDelSuggSignerEmail]
        return self.Sign(*arguments)


# SignatureDetail enumeration
sigdetApplicationName = 1
sigdetApplicationVersion = 2
sigdetColorDepth = 8
sigdetDelSuggSigner = 16
sigdetDelSuggSignerEmail = 20
sigdetDelSuggSignerEmailSet = 21
sigdetDelSuggSignerLine2 = 18
sigdetDelSuggSignerLine2Set = 19
sigdetDelSuggSignerSet = 17
sigdetDocPreviewImg = 10
sigdetHashAlgorithm = 14
sigdetHorizResolution = 6
sigdetIPCurrentView = 12
sigdetIPFormHash = 11
sigdetLocalSigningTime = 0
sigdetNumberOfMonitors = 5
sigdetOfficeVersion = 3
sigdetShouldShowViewWarning = 15
sigdetSignatureType = 13
sigdetSignedData = 9
sigdetVertResolution = 7
sigdetWindowsVersion = 4

class SignatureInfo:

    def __init__(self, signatureinfo=None):
        self.com_object= signatureinfo

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def CertificateVerificationResults(self):
        return self.com_object.CertificateVerificationResults

    @property
    def certificateverificationresults(self):
        """Alias for CertificateVerificationResults"""
        return self.CertificateVerificationResults

    @property
    def certificate_verification_results(self):
        """Alias for CertificateVerificationResults"""
        return self.CertificateVerificationResults

    @property
    def ContentVerificationResults(self):
        return self.com_object.ContentVerificationResults

    @property
    def contentverificationresults(self):
        """Alias for ContentVerificationResults"""
        return self.ContentVerificationResults

    @property
    def content_verification_results(self):
        """Alias for ContentVerificationResults"""
        return self.ContentVerificationResults

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def IsCertificateExpired(self):
        return self.com_object.IsCertificateExpired

    @property
    def iscertificateexpired(self):
        """Alias for IsCertificateExpired"""
        return self.IsCertificateExpired

    @property
    def is_certificate_expired(self):
        """Alias for IsCertificateExpired"""
        return self.IsCertificateExpired

    @property
    def IsCertificateRevoked(self):
        return self.com_object.IsCertificateRevoked

    @property
    def iscertificaterevoked(self):
        """Alias for IsCertificateRevoked"""
        return self.IsCertificateRevoked

    @property
    def is_certificate_revoked(self):
        """Alias for IsCertificateRevoked"""
        return self.IsCertificateRevoked

    @property
    def IsCertificateUntrusted(self):
        return self.com_object.IsCertificateUntrusted

    @property
    def iscertificateuntrusted(self):
        """Alias for IsCertificateUntrusted"""
        return self.IsCertificateUntrusted

    @property
    def is_certificate_untrusted(self):
        """Alias for IsCertificateUntrusted"""
        return self.IsCertificateUntrusted

    @property
    def IsValid(self):
        return self.com_object.IsValid

    @property
    def isvalid(self):
        """Alias for IsValid"""
        return self.IsValid

    @property
    def is_valid(self):
        """Alias for IsValid"""
        return self.IsValid

    @property
    def ReadOnly(self):
        return self.com_object.ReadOnly

    @property
    def readonly(self):
        """Alias for ReadOnly"""
        return self.ReadOnly

    @property
    def read_only(self):
        """Alias for ReadOnly"""
        return self.ReadOnly

    @property
    def SignatureComment(self):
        return self.com_object.SignatureComment

    @SignatureComment.setter
    def SignatureComment(self, value):
        self.com_object.SignatureComment = value

    @property
    def signaturecomment(self):
        """Alias for SignatureComment"""
        return self.SignatureComment

    @signaturecomment.setter
    def signaturecomment(self, value):
        """Alias for SignatureComment.setter"""
        self.SignatureComment = value

    @property
    def signature_comment(self):
        """Alias for SignatureComment"""
        return self.SignatureComment

    @signature_comment.setter
    def signature_comment(self, value):
        """Alias for SignatureComment.setter"""
        self.SignatureComment = value

    @property
    def SignatureImage(self):
        return self.com_object.SignatureImage

    @SignatureImage.setter
    def SignatureImage(self, value):
        self.com_object.SignatureImage = value

    @property
    def signatureimage(self):
        """Alias for SignatureImage"""
        return self.SignatureImage

    @signatureimage.setter
    def signatureimage(self, value):
        """Alias for SignatureImage.setter"""
        self.SignatureImage = value

    @property
    def signature_image(self):
        """Alias for SignatureImage"""
        return self.SignatureImage

    @signature_image.setter
    def signature_image(self, value):
        """Alias for SignatureImage.setter"""
        self.SignatureImage = value

    @property
    def SignatureProvider(self):
        return self.com_object.SignatureProvider

    @property
    def signatureprovider(self):
        """Alias for SignatureProvider"""
        return self.SignatureProvider

    @property
    def signature_provider(self):
        """Alias for SignatureProvider"""
        return self.SignatureProvider

    @property
    def SignatureText(self):
        return self.com_object.SignatureText

    @SignatureText.setter
    def SignatureText(self, value):
        self.com_object.SignatureText = value

    @property
    def signaturetext(self):
        """Alias for SignatureText"""
        return self.SignatureText

    @signaturetext.setter
    def signaturetext(self, value):
        """Alias for SignatureText.setter"""
        self.SignatureText = value

    @property
    def signature_text(self):
        """Alias for SignatureText"""
        return self.SignatureText

    @signature_text.setter
    def signature_text(self, value):
        """Alias for SignatureText.setter"""
        self.SignatureText = value

    def GetCertificateDetail(self, certdet=None):
        arguments = com_arguments([unwrap(a) for a in [certdet]])
        return self.com_object.GetCertificateDetail(*arguments)

    def getcertificatedetail(self, certdet=None):
        """Alias for GetCertificateDetail"""
        arguments = [certdet]
        return self.GetCertificateDetail(*arguments)

    def get_certificate_detail(self, certdet=None):
        """Alias for GetCertificateDetail"""
        arguments = [certdet]
        return self.GetCertificateDetail(*arguments)

    def GetSignatureDetail(self, sigdet=None):
        arguments = com_arguments([unwrap(a) for a in [sigdet]])
        return self.com_object.GetSignatureDetail(*arguments)

    def getsignaturedetail(self, sigdet=None):
        """Alias for GetSignatureDetail"""
        arguments = [sigdet]
        return self.GetSignatureDetail(*arguments)

    def get_signature_detail(self, sigdet=None):
        """Alias for GetSignatureDetail"""
        arguments = [sigdet]
        return self.GetSignatureDetail(*arguments)

    def SelectCertificateDetailByThumbprint(self, bstrThumbprint=None):
        arguments = com_arguments([unwrap(a) for a in [bstrThumbprint]])
        return self.com_object.SelectCertificateDetailByThumbprint(*arguments)

    def selectcertificatedetailbythumbprint(self, bstrThumbprint=None):
        """Alias for SelectCertificateDetailByThumbprint"""
        arguments = [bstrThumbprint]
        return self.SelectCertificateDetailByThumbprint(*arguments)

    def select_certificate_detail_by_thumbprint(self, bstrThumbprint=None):
        """Alias for SelectCertificateDetailByThumbprint"""
        arguments = [bstrThumbprint]
        return self.SelectCertificateDetailByThumbprint(*arguments)

    def SelectSignatureCertificate(self, ParentWindow=None):
        arguments = com_arguments([unwrap(a) for a in [ParentWindow]])
        return self.com_object.SelectSignatureCertificate(*arguments)

    def selectsignaturecertificate(self, ParentWindow=None):
        """Alias for SelectSignatureCertificate"""
        arguments = [ParentWindow]
        return self.SelectSignatureCertificate(*arguments)

    def select_signature_certificate(self, ParentWindow=None):
        """Alias for SelectSignatureCertificate"""
        arguments = [ParentWindow]
        return self.SelectSignatureCertificate(*arguments)

    def ShowSignatureCertificate(self, ParentWindow=None):
        arguments = com_arguments([unwrap(a) for a in [ParentWindow]])
        return self.com_object.ShowSignatureCertificate(*arguments)

    def showsignaturecertificate(self, ParentWindow=None):
        """Alias for ShowSignatureCertificate"""
        arguments = [ParentWindow]
        return self.ShowSignatureCertificate(*arguments)

    def show_signature_certificate(self, ParentWindow=None):
        """Alias for ShowSignatureCertificate"""
        arguments = [ParentWindow]
        return self.ShowSignatureCertificate(*arguments)


# SignatureLineImage enumeration
siglnimgSignedInvalid = 3
siglnimgSignedValid = 2
siglnimgSoftwareRequired = 0
siglnimgUnsigned = 1

class SignatureProvider:

    def __init__(self, signatureprovider=None):
        self.com_object= signatureprovider

    def GenerateSignatureLineImage(self, siglnimg=None, psigsetup=None, psiginfo=None):
        arguments = com_arguments([unwrap(a) for a in [siglnimg, psigsetup, psiginfo]])
        return self.com_object.GenerateSignatureLineImage(*arguments)

    def generatesignaturelineimage(self, siglnimg=None, psigsetup=None, psiginfo=None):
        """Alias for GenerateSignatureLineImage"""
        arguments = [siglnimg, psigsetup, psiginfo]
        return self.GenerateSignatureLineImage(*arguments)

    def generate_signature_line_image(self, siglnimg=None, psigsetup=None, psiginfo=None):
        """Alias for GenerateSignatureLineImage"""
        arguments = [siglnimg, psigsetup, psiginfo]
        return self.GenerateSignatureLineImage(*arguments)

    def GetProviderDetail(self, sigprovdet=None):
        arguments = com_arguments([unwrap(a) for a in [sigprovdet]])
        return self.com_object.GetProviderDetail(*arguments)

    def getproviderdetail(self, sigprovdet=None):
        """Alias for GetProviderDetail"""
        arguments = [sigprovdet]
        return self.GetProviderDetail(*arguments)

    def get_provider_detail(self, sigprovdet=None):
        """Alias for GetProviderDetail"""
        arguments = [sigprovdet]
        return self.GetProviderDetail(*arguments)

    def HashStream(self, QueryContinue=None, Stream=None):
        arguments = com_arguments([unwrap(a) for a in [QueryContinue, Stream]])
        return self.com_object.HashStream(*arguments)

    def hashstream(self, QueryContinue=None, Stream=None):
        """Alias for HashStream"""
        arguments = [QueryContinue, Stream]
        return self.HashStream(*arguments)

    def hash_stream(self, QueryContinue=None, Stream=None):
        """Alias for HashStream"""
        arguments = [QueryContinue, Stream]
        return self.HashStream(*arguments)

    def NotifySignatureAdded(self, ParentWindow=None, psigsetup=None, psiginfo=None):
        arguments = com_arguments([unwrap(a) for a in [ParentWindow, psigsetup, psiginfo]])
        return self.com_object.NotifySignatureAdded(*arguments)

    def notifysignatureadded(self, ParentWindow=None, psigsetup=None, psiginfo=None):
        """Alias for NotifySignatureAdded"""
        arguments = [ParentWindow, psigsetup, psiginfo]
        return self.NotifySignatureAdded(*arguments)

    def notify_signature_added(self, ParentWindow=None, psigsetup=None, psiginfo=None):
        """Alias for NotifySignatureAdded"""
        arguments = [ParentWindow, psigsetup, psiginfo]
        return self.NotifySignatureAdded(*arguments)

    def ShowSignatureDetails(self, ParentWindow=None, psigsetup=None, psiginfo=None, XmlDsigStream=None, pcontverres=None, pcertverres=None):
        arguments = com_arguments([unwrap(a) for a in [ParentWindow, psigsetup, psiginfo, XmlDsigStream, pcontverres, pcertverres]])
        return self.com_object.ShowSignatureDetails(*arguments)

    def showsignaturedetails(self, ParentWindow=None, psigsetup=None, psiginfo=None, XmlDsigStream=None, pcontverres=None, pcertverres=None):
        """Alias for ShowSignatureDetails"""
        arguments = [ParentWindow, psigsetup, psiginfo, XmlDsigStream, pcontverres, pcertverres]
        return self.ShowSignatureDetails(*arguments)

    def show_signature_details(self, ParentWindow=None, psigsetup=None, psiginfo=None, XmlDsigStream=None, pcontverres=None, pcertverres=None):
        """Alias for ShowSignatureDetails"""
        arguments = [ParentWindow, psigsetup, psiginfo, XmlDsigStream, pcontverres, pcertverres]
        return self.ShowSignatureDetails(*arguments)

    def ShowSignatureSetup(self, ParentWindow=None, psigsetup=None):
        arguments = com_arguments([unwrap(a) for a in [ParentWindow, psigsetup]])
        return self.com_object.ShowSignatureSetup(*arguments)

    def showsignaturesetup(self, ParentWindow=None, psigsetup=None):
        """Alias for ShowSignatureSetup"""
        arguments = [ParentWindow, psigsetup]
        return self.ShowSignatureSetup(*arguments)

    def show_signature_setup(self, ParentWindow=None, psigsetup=None):
        """Alias for ShowSignatureSetup"""
        arguments = [ParentWindow, psigsetup]
        return self.ShowSignatureSetup(*arguments)

    def ShowSigningCeremony(self, ParentWindow=None, psigsetup=None, psiginfo=None):
        arguments = com_arguments([unwrap(a) for a in [ParentWindow, psigsetup, psiginfo]])
        return self.com_object.ShowSigningCeremony(*arguments)

    def showsigningceremony(self, ParentWindow=None, psigsetup=None, psiginfo=None):
        """Alias for ShowSigningCeremony"""
        arguments = [ParentWindow, psigsetup, psiginfo]
        return self.ShowSigningCeremony(*arguments)

    def show_signing_ceremony(self, ParentWindow=None, psigsetup=None, psiginfo=None):
        """Alias for ShowSigningCeremony"""
        arguments = [ParentWindow, psigsetup, psiginfo]
        return self.ShowSigningCeremony(*arguments)

    def SignXmlDsig(self, QueryContinue=None, psigsetup=None, psiginfo=None, XmlDsigStream=None):
        arguments = com_arguments([unwrap(a) for a in [QueryContinue, psigsetup, psiginfo, XmlDsigStream]])
        return self.com_object.SignXmlDsig(*arguments)

    def signxmldsig(self, QueryContinue=None, psigsetup=None, psiginfo=None, XmlDsigStream=None):
        """Alias for SignXmlDsig"""
        arguments = [QueryContinue, psigsetup, psiginfo, XmlDsigStream]
        return self.SignXmlDsig(*arguments)

    def sign_xml_dsig(self, QueryContinue=None, psigsetup=None, psiginfo=None, XmlDsigStream=None):
        """Alias for SignXmlDsig"""
        arguments = [QueryContinue, psigsetup, psiginfo, XmlDsigStream]
        return self.SignXmlDsig(*arguments)

    def VerifyXmlDsig(self, QueryContinue=None, psigsetup=None, psiginfo=None, XmlDsigStream=None, pcontverres=None, pcertverres=None):
        arguments = com_arguments([unwrap(a) for a in [QueryContinue, psigsetup, psiginfo, XmlDsigStream, pcontverres, pcertverres]])
        return self.com_object.VerifyXmlDsig(*arguments)

    def verifyxmldsig(self, QueryContinue=None, psigsetup=None, psiginfo=None, XmlDsigStream=None, pcontverres=None, pcertverres=None):
        """Alias for VerifyXmlDsig"""
        arguments = [QueryContinue, psigsetup, psiginfo, XmlDsigStream, pcontverres, pcertverres]
        return self.VerifyXmlDsig(*arguments)

    def verify_xml_dsig(self, QueryContinue=None, psigsetup=None, psiginfo=None, XmlDsigStream=None, pcontverres=None, pcertverres=None):
        """Alias for VerifyXmlDsig"""
        arguments = [QueryContinue, psigsetup, psiginfo, XmlDsigStream, pcontverres, pcertverres]
        return self.VerifyXmlDsig(*arguments)


# SignatureProviderDetail enumeration
sigprovdetHashAlgorithm = 1
sigprovdetUIOnly = 2
sigprovdetUrl = 0

class SignatureSet:

    def __init__(self, signatureset=None):
        self.com_object= signatureset

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def CanAddSignatureLine(self):
        return self.com_object.CanAddSignatureLine

    @property
    def canaddsignatureline(self):
        """Alias for CanAddSignatureLine"""
        return self.CanAddSignatureLine

    @property
    def can_add_signature_line(self):
        """Alias for CanAddSignatureLine"""
        return self.CanAddSignatureLine

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    def Item(self, iSig=None):
        arguments = com_arguments([unwrap(a) for a in [iSig]])
        if hasattr(self.com_object, "GetItem"):
            return self.com_object.GetItem(*arguments)
        else:
            return self.com_object.Item(*arguments)

    def item(self, iSig=None):
        """Alias for Item"""
        arguments = [iSig]
        return self.Item(*arguments)

    def __call__(self, iSig=None):
        return self.Item(iSig)

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    @property
    def ShowSignaturesPane(self):
        return self.com_object.ShowSignaturesPane

    @ShowSignaturesPane.setter
    def ShowSignaturesPane(self, value):
        self.com_object.ShowSignaturesPane = value

    @property
    def showsignaturespane(self):
        """Alias for ShowSignaturesPane"""
        return self.ShowSignaturesPane

    @showsignaturespane.setter
    def showsignaturespane(self, value):
        """Alias for ShowSignaturesPane.setter"""
        self.ShowSignaturesPane = value

    @property
    def show_signatures_pane(self):
        """Alias for ShowSignaturesPane"""
        return self.ShowSignaturesPane

    @show_signatures_pane.setter
    def show_signatures_pane(self, value):
        """Alias for ShowSignaturesPane.setter"""
        self.ShowSignaturesPane = value

    @property
    def Subset(self):
        return self.com_object.Subset

    @Subset.setter
    def Subset(self, value):
        self.com_object.Subset = value

    @property
    def subset(self):
        """Alias for Subset"""
        return self.Subset

    @subset.setter
    def subset(self, value):
        """Alias for Subset.setter"""
        self.Subset = value

    def AddNonVisibleSignature(self, varSigProv=None):
        arguments = com_arguments([unwrap(a) for a in [varSigProv]])
        return Signature(self.com_object.AddNonVisibleSignature(*arguments))

    def addnonvisiblesignature(self, varSigProv=None):
        """Alias for AddNonVisibleSignature"""
        arguments = [varSigProv]
        return self.AddNonVisibleSignature(*arguments)

    def add_non_visible_signature(self, varSigProv=None):
        """Alias for AddNonVisibleSignature"""
        arguments = [varSigProv]
        return self.AddNonVisibleSignature(*arguments)

    def AddSignatureLine(self, varSigProv=None):
        arguments = com_arguments([unwrap(a) for a in [varSigProv]])
        return Signature(self.com_object.AddSignatureLine(*arguments))

    def addsignatureline(self, varSigProv=None):
        """Alias for AddSignatureLine"""
        arguments = [varSigProv]
        return self.AddSignatureLine(*arguments)

    def add_signature_line(self, varSigProv=None):
        """Alias for AddSignatureLine"""
        arguments = [varSigProv]
        return self.AddSignatureLine(*arguments)


class SignatureSetup:

    def __init__(self, signaturesetup=None):
        self.com_object= signaturesetup

    @property
    def AdditionalXml(self):
        return self.com_object.AdditionalXml

    @AdditionalXml.setter
    def AdditionalXml(self, value):
        self.com_object.AdditionalXml = value

    @property
    def additionalxml(self):
        """Alias for AdditionalXml"""
        return self.AdditionalXml

    @additionalxml.setter
    def additionalxml(self, value):
        """Alias for AdditionalXml.setter"""
        self.AdditionalXml = value

    @property
    def additional_xml(self):
        """Alias for AdditionalXml"""
        return self.AdditionalXml

    @additional_xml.setter
    def additional_xml(self, value):
        """Alias for AdditionalXml.setter"""
        self.AdditionalXml = value

    @property
    def AllowComments(self):
        return self.com_object.AllowComments

    @AllowComments.setter
    def AllowComments(self, value):
        self.com_object.AllowComments = value

    @property
    def allowcomments(self):
        """Alias for AllowComments"""
        return self.AllowComments

    @allowcomments.setter
    def allowcomments(self, value):
        """Alias for AllowComments.setter"""
        self.AllowComments = value

    @property
    def allow_comments(self):
        """Alias for AllowComments"""
        return self.AllowComments

    @allow_comments.setter
    def allow_comments(self, value):
        """Alias for AllowComments.setter"""
        self.AllowComments = value

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Id(self):
        return self.com_object.Id

    @property
    def id(self):
        """Alias for Id"""
        return self.Id

    @property
    def ReadOnly(self):
        return self.com_object.ReadOnly

    @property
    def readonly(self):
        """Alias for ReadOnly"""
        return self.ReadOnly

    @property
    def read_only(self):
        """Alias for ReadOnly"""
        return self.ReadOnly

    @property
    def ShowSignDate(self):
        return self.com_object.ShowSignDate

    @ShowSignDate.setter
    def ShowSignDate(self, value):
        self.com_object.ShowSignDate = value

    @property
    def showsigndate(self):
        """Alias for ShowSignDate"""
        return self.ShowSignDate

    @showsigndate.setter
    def showsigndate(self, value):
        """Alias for ShowSignDate.setter"""
        self.ShowSignDate = value

    @property
    def show_sign_date(self):
        """Alias for ShowSignDate"""
        return self.ShowSignDate

    @show_sign_date.setter
    def show_sign_date(self, value):
        """Alias for ShowSignDate.setter"""
        self.ShowSignDate = value

    @property
    def SignatureProvider(self):
        return self.com_object.SignatureProvider

    @property
    def signatureprovider(self):
        """Alias for SignatureProvider"""
        return self.SignatureProvider

    @property
    def signature_provider(self):
        """Alias for SignatureProvider"""
        return self.SignatureProvider

    @property
    def SigningInstructions(self):
        return self.com_object.SigningInstructions

    @SigningInstructions.setter
    def SigningInstructions(self, value):
        self.com_object.SigningInstructions = value

    @property
    def signinginstructions(self):
        """Alias for SigningInstructions"""
        return self.SigningInstructions

    @signinginstructions.setter
    def signinginstructions(self, value):
        """Alias for SigningInstructions.setter"""
        self.SigningInstructions = value

    @property
    def signing_instructions(self):
        """Alias for SigningInstructions"""
        return self.SigningInstructions

    @signing_instructions.setter
    def signing_instructions(self, value):
        """Alias for SigningInstructions.setter"""
        self.SigningInstructions = value

    @property
    def SuggestedSigner(self):
        return self.com_object.SuggestedSigner

    @SuggestedSigner.setter
    def SuggestedSigner(self, value):
        self.com_object.SuggestedSigner = value

    @property
    def suggestedsigner(self):
        """Alias for SuggestedSigner"""
        return self.SuggestedSigner

    @suggestedsigner.setter
    def suggestedsigner(self, value):
        """Alias for SuggestedSigner.setter"""
        self.SuggestedSigner = value

    @property
    def suggested_signer(self):
        """Alias for SuggestedSigner"""
        return self.SuggestedSigner

    @suggested_signer.setter
    def suggested_signer(self, value):
        """Alias for SuggestedSigner.setter"""
        self.SuggestedSigner = value

    @property
    def SuggestedSignerEmail(self):
        return self.com_object.SuggestedSignerEmail

    @SuggestedSignerEmail.setter
    def SuggestedSignerEmail(self, value):
        self.com_object.SuggestedSignerEmail = value

    @property
    def suggestedsigneremail(self):
        """Alias for SuggestedSignerEmail"""
        return self.SuggestedSignerEmail

    @suggestedsigneremail.setter
    def suggestedsigneremail(self, value):
        """Alias for SuggestedSignerEmail.setter"""
        self.SuggestedSignerEmail = value

    @property
    def suggested_signer_email(self):
        """Alias for SuggestedSignerEmail"""
        return self.SuggestedSignerEmail

    @suggested_signer_email.setter
    def suggested_signer_email(self, value):
        """Alias for SuggestedSignerEmail.setter"""
        self.SuggestedSignerEmail = value

    @property
    def SuggestedSignerLine2(self):
        return self.com_object.SuggestedSignerLine2

    @SuggestedSignerLine2.setter
    def SuggestedSignerLine2(self, value):
        self.com_object.SuggestedSignerLine2 = value

    @property
    def suggestedsignerline2(self):
        """Alias for SuggestedSignerLine2"""
        return self.SuggestedSignerLine2

    @suggestedsignerline2.setter
    def suggestedsignerline2(self, value):
        """Alias for SuggestedSignerLine2.setter"""
        self.SuggestedSignerLine2 = value

    @property
    def suggested_signer_line2(self):
        """Alias for SuggestedSignerLine2"""
        return self.SuggestedSignerLine2

    @suggested_signer_line2.setter
    def suggested_signer_line2(self, value):
        """Alias for SuggestedSignerLine2.setter"""
        self.SuggestedSignerLine2 = value


# SignatureType enumeration
sigtypeMax = 3
sigtypeNonVisible = 1
sigtypeSignatureLine = 2
sigtypeUnknown = 0

class SmartArt:

    def __init__(self, smartart=None):
        self.com_object= smartart

    @property
    def AllNodes(self):
        return self.com_object.AllNodes

    @property
    def allnodes(self):
        """Alias for AllNodes"""
        return self.AllNodes

    @property
    def all_nodes(self):
        """Alias for AllNodes"""
        return self.AllNodes

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Color(self):
        return self.com_object.Color

    @Color.setter
    def Color(self, value):
        self.com_object.Color = value

    @property
    def color(self):
        """Alias for Color"""
        return self.Color

    @color.setter
    def color(self, value):
        """Alias for Color.setter"""
        self.Color = value

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Layout(self):
        return self.com_object.Layout

    @Layout.setter
    def Layout(self, value):
        self.com_object.Layout = value

    @property
    def layout(self):
        """Alias for Layout"""
        return self.Layout

    @layout.setter
    def layout(self, value):
        """Alias for Layout.setter"""
        self.Layout = value

    @property
    def Nodes(self):
        return self.com_object.Nodes

    @property
    def nodes(self):
        """Alias for Nodes"""
        return self.Nodes

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    @property
    def QuickStyle(self):
        return self.com_object.QuickStyle

    @QuickStyle.setter
    def QuickStyle(self, value):
        self.com_object.QuickStyle = value

    @property
    def quickstyle(self):
        """Alias for QuickStyle"""
        return self.QuickStyle

    @quickstyle.setter
    def quickstyle(self, value):
        """Alias for QuickStyle.setter"""
        self.QuickStyle = value

    @property
    def quick_style(self):
        """Alias for QuickStyle"""
        return self.QuickStyle

    @quick_style.setter
    def quick_style(self, value):
        """Alias for QuickStyle.setter"""
        self.QuickStyle = value

    @property
    def Reverse(self):
        return self.com_object.Reverse

    @Reverse.setter
    def Reverse(self, value):
        self.com_object.Reverse = value

    @property
    def reverse(self):
        """Alias for Reverse"""
        return self.Reverse

    @reverse.setter
    def reverse(self, value):
        """Alias for Reverse.setter"""
        self.Reverse = value

    def Reset(self):
        return self.com_object.Reset()

    def reset(self):
        """Alias for Reset"""
        return self.Reset()


class SmartArtColor:

    def __init__(self, smartartcolor=None):
        self.com_object= smartartcolor

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Category(self):
        return self.com_object.Category

    @property
    def category(self):
        """Alias for Category"""
        return self.Category

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Description(self):
        return self.com_object.Description

    @property
    def description(self):
        """Alias for Description"""
        return self.Description

    @property
    def Id(self):
        return self.com_object.Id

    @property
    def id(self):
        """Alias for Id"""
        return self.Id

    @property
    def Name(self):
        return self.com_object.Name

    @property
    def name(self):
        """Alias for Name"""
        return self.Name

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent


class SmartArtColors:

    def __init__(self, smartartcolors=None):
        self.com_object= smartartcolors

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        return SmartArtColor(self.com_object.Item(*arguments))

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)


class SmartArtLayout:

    def __init__(self, smartartlayout=None):
        self.com_object= smartartlayout

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Category(self):
        return self.com_object.Category

    @property
    def category(self):
        """Alias for Category"""
        return self.Category

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Description(self):
        return self.com_object.Description

    @property
    def description(self):
        """Alias for Description"""
        return self.Description

    @property
    def Id(self):
        return self.com_object.Id

    @property
    def id(self):
        """Alias for Id"""
        return self.Id

    @property
    def Name(self):
        return self.com_object.Name

    @property
    def name(self):
        """Alias for Name"""
        return self.Name

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent


class SmartArtLayouts:

    def __init__(self, smartartlayouts=None):
        self.com_object= smartartlayouts

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        return SmartArtLayout(self.com_object.Item(*arguments))

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)


class SmartArtNode:

    def __init__(self, smartartnode=None):
        self.com_object= smartartnode

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Hidden(self):
        return self.com_object.Hidden

    @property
    def hidden(self):
        """Alias for Hidden"""
        return self.Hidden

    @property
    def Level(self):
        return self.com_object.Level

    @property
    def level(self):
        """Alias for Level"""
        return self.Level

    @property
    def Nodes(self):
        return self.com_object.Nodes

    @property
    def nodes(self):
        """Alias for Nodes"""
        return self.Nodes

    @property
    def OrgChartLayout(self):
        return self.com_object.OrgChartLayout

    @OrgChartLayout.setter
    def OrgChartLayout(self, value):
        self.com_object.OrgChartLayout = value

    @property
    def orgchartlayout(self):
        """Alias for OrgChartLayout"""
        return self.OrgChartLayout

    @orgchartlayout.setter
    def orgchartlayout(self, value):
        """Alias for OrgChartLayout.setter"""
        self.OrgChartLayout = value

    @property
    def org_chart_layout(self):
        """Alias for OrgChartLayout"""
        return self.OrgChartLayout

    @org_chart_layout.setter
    def org_chart_layout(self, value):
        """Alias for OrgChartLayout.setter"""
        self.OrgChartLayout = value

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    @property
    def ParentNode(self):
        return self.com_object.ParentNode

    @property
    def parentnode(self):
        """Alias for ParentNode"""
        return self.ParentNode

    @property
    def parent_node(self):
        """Alias for ParentNode"""
        return self.ParentNode

    @property
    def Shapes(self):
        return SmartArtNode(self.com_object.Shapes)

    @property
    def shapes(self):
        """Alias for Shapes"""
        return self.Shapes

    @property
    def TextFrame2(self):
        return SmartArtNode(self.com_object.TextFrame2)

    @property
    def textframe2(self):
        """Alias for TextFrame2"""
        return self.TextFrame2

    @property
    def text_frame2(self):
        """Alias for TextFrame2"""
        return self.TextFrame2

    @property
    def Type(self):
        return self.com_object.Type

    @property
    def type(self):
        """Alias for Type"""
        return self.Type

    def AddNode(self, Position=None, Type=None):
        arguments = com_arguments([unwrap(a) for a in [Position, Type]])
        return SmartArtNode(self.com_object.AddNode(*arguments))

    def addnode(self, Position=None, Type=None):
        """Alias for AddNode"""
        arguments = [Position, Type]
        return self.AddNode(*arguments)

    def add_node(self, Position=None, Type=None):
        """Alias for AddNode"""
        arguments = [Position, Type]
        return self.AddNode(*arguments)

    def Delete(self):
        return self.com_object.Delete()

    def delete(self):
        """Alias for Delete"""
        return self.Delete()

    def Demote(self):
        return self.com_object.Demote()

    def demote(self):
        """Alias for Demote"""
        return self.Demote()

    def Larger(self):
        return self.com_object.Larger()

    def larger(self):
        """Alias for Larger"""
        return self.Larger()

    def Promote(self):
        return self.com_object.Promote()

    def promote(self):
        """Alias for Promote"""
        return self.Promote()

    def ReorderDown(self):
        return self.com_object.ReorderDown()

    def reorderdown(self):
        """Alias for ReorderDown"""
        return self.ReorderDown()

    def reorder_down(self):
        """Alias for ReorderDown"""
        return self.ReorderDown()

    def ReorderUp(self):
        return self.com_object.ReorderUp()

    def reorderup(self):
        """Alias for ReorderUp"""
        return self.ReorderUp()

    def reorder_up(self):
        """Alias for ReorderUp"""
        return self.ReorderUp()

    def Smaller(self):
        return self.com_object.Smaller()

    def smaller(self):
        """Alias for Smaller"""
        return self.Smaller()


class SmartArtNodes:

    def __init__(self, smartartnodes=None):
        self.com_object= smartartnodes

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    def Add(self):
        return SmartArtNode(self.com_object.Add())

    def add(self):
        """Alias for Add"""
        return self.Add()

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        return SmartArtNode(self.com_object.Item(*arguments))

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)


class SmartArtQuickStyle:

    def __init__(self, smartartquickstyle=None):
        self.com_object= smartartquickstyle

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Category(self):
        return self.com_object.Category

    @property
    def category(self):
        """Alias for Category"""
        return self.Category

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Description(self):
        return self.com_object.Description

    @property
    def description(self):
        """Alias for Description"""
        return self.Description

    @property
    def Id(self):
        return self.com_object.Id

    @property
    def id(self):
        """Alias for Id"""
        return self.Id

    @property
    def Name(self):
        return self.com_object.Name

    @property
    def name(self):
        """Alias for Name"""
        return self.Name

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent


class SmartArtQuickStyles:

    def __init__(self, smartartquickstyles=None):
        self.com_object= smartartquickstyles

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        return SmartArtQuickStyle(self.com_object.Item(*arguments))

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)


class SmartDocument:

    def __init__(self, smartdocument=None):
        self.com_object= smartdocument

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def SolutionID(self):
        return self.com_object.SolutionID

    @SolutionID.setter
    def SolutionID(self, value):
        self.com_object.SolutionID = value

    @property
    def solutionid(self):
        """Alias for SolutionID"""
        return self.SolutionID

    @solutionid.setter
    def solutionid(self, value):
        """Alias for SolutionID.setter"""
        self.SolutionID = value

    @property
    def solution_i_d(self):
        """Alias for SolutionID"""
        return self.SolutionID

    @solution_i_d.setter
    def solution_i_d(self, value):
        """Alias for SolutionID.setter"""
        self.SolutionID = value

    @property
    def SolutionURL(self):
        return self.com_object.SolutionURL

    @SolutionURL.setter
    def SolutionURL(self, value):
        self.com_object.SolutionURL = value

    @property
    def solutionurl(self):
        """Alias for SolutionURL"""
        return self.SolutionURL

    @solutionurl.setter
    def solutionurl(self, value):
        """Alias for SolutionURL.setter"""
        self.SolutionURL = value

    @property
    def solution_u_r_l(self):
        """Alias for SolutionURL"""
        return self.SolutionURL

    @solution_u_r_l.setter
    def solution_u_r_l(self, value):
        """Alias for SolutionURL.setter"""
        self.SolutionURL = value

    def PickSolution(self, ConsiderAllSchemas=None):
        arguments = com_arguments([unwrap(a) for a in [ConsiderAllSchemas]])
        return self.com_object.PickSolution(*arguments)

    def picksolution(self, ConsiderAllSchemas=None):
        """Alias for PickSolution"""
        arguments = [ConsiderAllSchemas]
        return self.PickSolution(*arguments)

    def pick_solution(self, ConsiderAllSchemas=None):
        """Alias for PickSolution"""
        arguments = [ConsiderAllSchemas]
        return self.PickSolution(*arguments)

    def RefreshPane(self):
        return self.com_object.RefreshPane()

    def refreshpane(self):
        """Alias for RefreshPane"""
        return self.RefreshPane()

    def refresh_pane(self):
        """Alias for RefreshPane"""
        return self.RefreshPane()


class SoftEdgeFormat:

    def __init__(self, softedgeformat=None):
        self.com_object= softedgeformat

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Radius(self):
        return self.com_object.Radius

    @Radius.setter
    def Radius(self, value):
        self.com_object.Radius = value

    @property
    def radius(self):
        """Alias for Radius"""
        return self.Radius

    @radius.setter
    def radius(self, value):
        """Alias for Radius.setter"""
        self.Radius = value

    @property
    def Type(self):
        return self.com_object.Type

    @Type.setter
    def Type(self, value):
        self.com_object.Type = value

    @property
    def type(self):
        """Alias for Type"""
        return self.Type

    @type.setter
    def type(self, value):
        """Alias for Type.setter"""
        self.Type = value


class Sync:

    def __init__(self, sync=None):
        self.com_object= sync

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def ErrorType(self):
        return self.com_object.ErrorType

    @property
    def errortype(self):
        """Alias for ErrorType"""
        return self.ErrorType

    @property
    def error_type(self):
        """Alias for ErrorType"""
        return self.ErrorType

    @property
    def LastSyncTime(self):
        return self.com_object.LastSyncTime

    @property
    def lastsynctime(self):
        """Alias for LastSyncTime"""
        return self.LastSyncTime

    @property
    def last_sync_time(self):
        """Alias for LastSyncTime"""
        return self.LastSyncTime

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    @property
    def Status(self):
        return self.com_object.Status

    @property
    def status(self):
        """Alias for Status"""
        return self.Status

    @property
    def WorkspaceLastChangedBy(self):
        return self.com_object.WorkspaceLastChangedBy

    @property
    def workspacelastchangedby(self):
        """Alias for WorkspaceLastChangedBy"""
        return self.WorkspaceLastChangedBy

    @property
    def workspace_last_changed_by(self):
        """Alias for WorkspaceLastChangedBy"""
        return self.WorkspaceLastChangedBy

    def GetUpdate(self):
        return self.com_object.GetUpdate()

    def getupdate(self):
        """Alias for GetUpdate"""
        return self.GetUpdate()

    def get_update(self):
        """Alias for GetUpdate"""
        return self.GetUpdate()

    def OpenVersion(self, SyncVersionType=None):
        arguments = com_arguments([unwrap(a) for a in [SyncVersionType]])
        return self.com_object.OpenVersion(*arguments)

    def openversion(self, SyncVersionType=None):
        """Alias for OpenVersion"""
        arguments = [SyncVersionType]
        return self.OpenVersion(*arguments)

    def open_version(self, SyncVersionType=None):
        """Alias for OpenVersion"""
        arguments = [SyncVersionType]
        return self.OpenVersion(*arguments)

    def PutUpdate(self):
        return self.com_object.PutUpdate()

    def putupdate(self):
        """Alias for PutUpdate"""
        return self.PutUpdate()

    def put_update(self):
        """Alias for PutUpdate"""
        return self.PutUpdate()

    def ResolveConflict(self, SyncConflictResolution=None):
        arguments = com_arguments([unwrap(a) for a in [SyncConflictResolution]])
        return self.com_object.ResolveConflict(*arguments)

    def resolveconflict(self, SyncConflictResolution=None):
        """Alias for ResolveConflict"""
        arguments = [SyncConflictResolution]
        return self.ResolveConflict(*arguments)

    def resolve_conflict(self, SyncConflictResolution=None):
        """Alias for ResolveConflict"""
        arguments = [SyncConflictResolution]
        return self.ResolveConflict(*arguments)

    def Unsuspend(self):
        return self.com_object.Unsuspend()

    def unsuspend(self):
        """Alias for Unsuspend"""
        return self.Unsuspend()


class TabStop2:

    def __init__(self, tabstop2=None):
        self.com_object= tabstop2

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    @property
    def Position(self):
        return self.com_object.Position

    @Position.setter
    def Position(self, value):
        self.com_object.Position = value

    @property
    def position(self):
        """Alias for Position"""
        return self.Position

    @position.setter
    def position(self, value):
        """Alias for Position.setter"""
        self.Position = value

    @property
    def Type(self):
        return self.com_object.Type

    @Type.setter
    def Type(self, value):
        self.com_object.Type = value

    @property
    def type(self):
        """Alias for Type"""
        return self.Type

    @type.setter
    def type(self, value):
        """Alias for Type.setter"""
        self.Type = value

    def Clear(self):
        return self.com_object.Clear()

    def clear(self):
        """Alias for Clear"""
        return self.Clear()


class TabStops2:

    def __init__(self, tabstops2=None):
        self.com_object= tabstops2

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def DefaultSpacing(self):
        return self.com_object.DefaultSpacing

    @DefaultSpacing.setter
    def DefaultSpacing(self, value):
        self.com_object.DefaultSpacing = value

    @property
    def defaultspacing(self):
        """Alias for DefaultSpacing"""
        return self.DefaultSpacing

    @defaultspacing.setter
    def defaultspacing(self, value):
        """Alias for DefaultSpacing.setter"""
        self.DefaultSpacing = value

    @property
    def default_spacing(self):
        """Alias for DefaultSpacing"""
        return self.DefaultSpacing

    @default_spacing.setter
    def default_spacing(self, value):
        """Alias for DefaultSpacing.setter"""
        self.DefaultSpacing = value

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    def Add(self, Type=None, Position=None):
        arguments = com_arguments([unwrap(a) for a in [Type, Position]])
        return TabStop2(self.com_object.Add(*arguments))

    def add(self, Type=None, Position=None):
        """Alias for Add"""
        arguments = [Type, Position]
        return self.Add(*arguments)

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        return TabStop2(self.com_object.Item(*arguments))

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)


class TextColumn2:

    def __init__(self, textcolumn2=None):
        self.com_object= textcolumn2

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @Count.setter
    def Count(self, value):
        self.com_object.Count = value

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @count.setter
    def count(self, value):
        """Alias for Count.setter"""
        self.Count = value

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Number(self):
        return self.com_object.Number

    @Number.setter
    def Number(self, value):
        self.com_object.Number = value

    @property
    def number(self):
        """Alias for Number"""
        return self.Number

    @number.setter
    def number(self, value):
        """Alias for Number.setter"""
        self.Number = value

    @property
    def Spacing(self):
        return self.com_object.Spacing

    @Spacing.setter
    def Spacing(self, value):
        self.com_object.Spacing = value

    @property
    def spacing(self):
        """Alias for Spacing"""
        return self.Spacing

    @spacing.setter
    def spacing(self, value):
        """Alias for Spacing.setter"""
        self.Spacing = value

    @property
    def TextDirection(self):
        return self.com_object.TextDirection

    @TextDirection.setter
    def TextDirection(self, value):
        self.com_object.TextDirection = value

    @property
    def textdirection(self):
        """Alias for TextDirection"""
        return self.TextDirection

    @textdirection.setter
    def textdirection(self, value):
        """Alias for TextDirection.setter"""
        self.TextDirection = value

    @property
    def text_direction(self):
        """Alias for TextDirection"""
        return self.TextDirection

    @text_direction.setter
    def text_direction(self, value):
        """Alias for TextDirection.setter"""
        self.TextDirection = value


class TextFrame2:

    def __init__(self, textframe2=None):
        self.com_object= textframe2

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def AutoSize(self):
        return self.com_object.AutoSize

    @AutoSize.setter
    def AutoSize(self, value):
        self.com_object.AutoSize = value

    @property
    def autosize(self):
        """Alias for AutoSize"""
        return self.AutoSize

    @autosize.setter
    def autosize(self, value):
        """Alias for AutoSize.setter"""
        self.AutoSize = value

    @property
    def auto_size(self):
        """Alias for AutoSize"""
        return self.AutoSize

    @auto_size.setter
    def auto_size(self, value):
        """Alias for AutoSize.setter"""
        self.AutoSize = value

    @property
    def Column(self):
        return self.com_object.Column

    @property
    def column(self):
        """Alias for Column"""
        return self.Column

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def HasText(self):
        return self.com_object.HasText

    @property
    def hastext(self):
        """Alias for HasText"""
        return self.HasText

    @property
    def has_text(self):
        """Alias for HasText"""
        return self.HasText

    @property
    def HorizontalAnchor(self):
        return self.com_object.HorizontalAnchor

    @HorizontalAnchor.setter
    def HorizontalAnchor(self, value):
        self.com_object.HorizontalAnchor = value

    @property
    def horizontalanchor(self):
        """Alias for HorizontalAnchor"""
        return self.HorizontalAnchor

    @horizontalanchor.setter
    def horizontalanchor(self, value):
        """Alias for HorizontalAnchor.setter"""
        self.HorizontalAnchor = value

    @property
    def horizontal_anchor(self):
        """Alias for HorizontalAnchor"""
        return self.HorizontalAnchor

    @horizontal_anchor.setter
    def horizontal_anchor(self, value):
        """Alias for HorizontalAnchor.setter"""
        self.HorizontalAnchor = value

    @property
    def MarginBottom(self):
        return self.com_object.MarginBottom

    @MarginBottom.setter
    def MarginBottom(self, value):
        self.com_object.MarginBottom = value

    @property
    def marginbottom(self):
        """Alias for MarginBottom"""
        return self.MarginBottom

    @marginbottom.setter
    def marginbottom(self, value):
        """Alias for MarginBottom.setter"""
        self.MarginBottom = value

    @property
    def margin_bottom(self):
        """Alias for MarginBottom"""
        return self.MarginBottom

    @margin_bottom.setter
    def margin_bottom(self, value):
        """Alias for MarginBottom.setter"""
        self.MarginBottom = value

    @property
    def MarginLeft(self):
        return self.com_object.MarginLeft

    @MarginLeft.setter
    def MarginLeft(self, value):
        self.com_object.MarginLeft = value

    @property
    def marginleft(self):
        """Alias for MarginLeft"""
        return self.MarginLeft

    @marginleft.setter
    def marginleft(self, value):
        """Alias for MarginLeft.setter"""
        self.MarginLeft = value

    @property
    def margin_left(self):
        """Alias for MarginLeft"""
        return self.MarginLeft

    @margin_left.setter
    def margin_left(self, value):
        """Alias for MarginLeft.setter"""
        self.MarginLeft = value

    @property
    def MarginRight(self):
        return self.com_object.MarginRight

    @MarginRight.setter
    def MarginRight(self, value):
        self.com_object.MarginRight = value

    @property
    def marginright(self):
        """Alias for MarginRight"""
        return self.MarginRight

    @marginright.setter
    def marginright(self, value):
        """Alias for MarginRight.setter"""
        self.MarginRight = value

    @property
    def margin_right(self):
        """Alias for MarginRight"""
        return self.MarginRight

    @margin_right.setter
    def margin_right(self, value):
        """Alias for MarginRight.setter"""
        self.MarginRight = value

    @property
    def MarginTop(self):
        return self.com_object.MarginTop

    @MarginTop.setter
    def MarginTop(self, value):
        self.com_object.MarginTop = value

    @property
    def margintop(self):
        """Alias for MarginTop"""
        return self.MarginTop

    @margintop.setter
    def margintop(self, value):
        """Alias for MarginTop.setter"""
        self.MarginTop = value

    @property
    def margin_top(self):
        """Alias for MarginTop"""
        return self.MarginTop

    @margin_top.setter
    def margin_top(self, value):
        """Alias for MarginTop.setter"""
        self.MarginTop = value

    @property
    def NoTextRotation(self):
        return self.com_object.NoTextRotation

    @NoTextRotation.setter
    def NoTextRotation(self, value):
        self.com_object.NoTextRotation = value

    @property
    def notextrotation(self):
        """Alias for NoTextRotation"""
        return self.NoTextRotation

    @notextrotation.setter
    def notextrotation(self, value):
        """Alias for NoTextRotation.setter"""
        self.NoTextRotation = value

    @property
    def no_text_rotation(self):
        """Alias for NoTextRotation"""
        return self.NoTextRotation

    @no_text_rotation.setter
    def no_text_rotation(self, value):
        """Alias for NoTextRotation.setter"""
        self.NoTextRotation = value

    @property
    def Orientation(self):
        return self.com_object.Orientation

    @Orientation.setter
    def Orientation(self, value):
        self.com_object.Orientation = value

    @property
    def orientation(self):
        """Alias for Orientation"""
        return self.Orientation

    @orientation.setter
    def orientation(self, value):
        """Alias for Orientation.setter"""
        self.Orientation = value

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    @property
    def PathFormat(self):
        return self.com_object.PathFormat

    @PathFormat.setter
    def PathFormat(self, value):
        self.com_object.PathFormat = value

    @property
    def pathformat(self):
        """Alias for PathFormat"""
        return self.PathFormat

    @pathformat.setter
    def pathformat(self, value):
        """Alias for PathFormat.setter"""
        self.PathFormat = value

    @property
    def path_format(self):
        """Alias for PathFormat"""
        return self.PathFormat

    @path_format.setter
    def path_format(self, value):
        """Alias for PathFormat.setter"""
        self.PathFormat = value

    @property
    def Ruler(self):
        return Ruler2(self.com_object.Ruler)

    @property
    def ruler(self):
        """Alias for Ruler"""
        return self.Ruler

    @property
    def TextRange(self):
        return self.com_object.TextRange

    @property
    def textrange(self):
        """Alias for TextRange"""
        return self.TextRange

    @property
    def text_range(self):
        """Alias for TextRange"""
        return self.TextRange

    @property
    def ThreeD(self):
        return self.com_object.ThreeD

    @property
    def threed(self):
        """Alias for ThreeD"""
        return self.ThreeD

    @property
    def three_d(self):
        """Alias for ThreeD"""
        return self.ThreeD

    @property
    def VerticalAnchor(self):
        return self.com_object.VerticalAnchor

    @VerticalAnchor.setter
    def VerticalAnchor(self, value):
        self.com_object.VerticalAnchor = value

    @property
    def verticalanchor(self):
        """Alias for VerticalAnchor"""
        return self.VerticalAnchor

    @verticalanchor.setter
    def verticalanchor(self, value):
        """Alias for VerticalAnchor.setter"""
        self.VerticalAnchor = value

    @property
    def vertical_anchor(self):
        """Alias for VerticalAnchor"""
        return self.VerticalAnchor

    @vertical_anchor.setter
    def vertical_anchor(self, value):
        """Alias for VerticalAnchor.setter"""
        self.VerticalAnchor = value

    @property
    def WarpFormat(self):
        return self.com_object.WarpFormat

    @WarpFormat.setter
    def WarpFormat(self, value):
        self.com_object.WarpFormat = value

    @property
    def warpformat(self):
        """Alias for WarpFormat"""
        return self.WarpFormat

    @warpformat.setter
    def warpformat(self, value):
        """Alias for WarpFormat.setter"""
        self.WarpFormat = value

    @property
    def warp_format(self):
        """Alias for WarpFormat"""
        return self.WarpFormat

    @warp_format.setter
    def warp_format(self, value):
        """Alias for WarpFormat.setter"""
        self.WarpFormat = value

    @property
    def WordArtFormat(self):
        return self.com_object.WordArtFormat

    @WordArtFormat.setter
    def WordArtFormat(self, value):
        self.com_object.WordArtFormat = value

    @property
    def wordartformat(self):
        """Alias for WordArtFormat"""
        return self.WordArtFormat

    @wordartformat.setter
    def wordartformat(self, value):
        """Alias for WordArtFormat.setter"""
        self.WordArtFormat = value

    @property
    def word_art_format(self):
        """Alias for WordArtFormat"""
        return self.WordArtFormat

    @word_art_format.setter
    def word_art_format(self, value):
        """Alias for WordArtFormat.setter"""
        self.WordArtFormat = value

    @property
    def WordWrap(self):
        return self.com_object.WordWrap

    @WordWrap.setter
    def WordWrap(self, value):
        self.com_object.WordWrap = value

    @property
    def wordwrap(self):
        """Alias for WordWrap"""
        return self.WordWrap

    @wordwrap.setter
    def wordwrap(self, value):
        """Alias for WordWrap.setter"""
        self.WordWrap = value

    @property
    def word_wrap(self):
        """Alias for WordWrap"""
        return self.WordWrap

    @word_wrap.setter
    def word_wrap(self, value):
        """Alias for WordWrap.setter"""
        self.WordWrap = value

    def DeleteText(self):
        return self.com_object.DeleteText()

    def deletetext(self):
        """Alias for DeleteText"""
        return self.DeleteText()

    def delete_text(self):
        """Alias for DeleteText"""
        return self.DeleteText()


class TextRange2:

    def __init__(self, textrange2=None):
        self.com_object= textrange2

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def BoundHeight(self):
        return self.com_object.BoundHeight

    @property
    def boundheight(self):
        """Alias for BoundHeight"""
        return self.BoundHeight

    @property
    def bound_height(self):
        """Alias for BoundHeight"""
        return self.BoundHeight

    @property
    def BoundLeft(self):
        return self.com_object.BoundLeft

    @property
    def boundleft(self):
        """Alias for BoundLeft"""
        return self.BoundLeft

    @property
    def bound_left(self):
        """Alias for BoundLeft"""
        return self.BoundLeft

    @property
    def BoundTop(self):
        return self.com_object.BoundTop

    @property
    def boundtop(self):
        """Alias for BoundTop"""
        return self.BoundTop

    @property
    def bound_top(self):
        """Alias for BoundTop"""
        return self.BoundTop

    @property
    def BoundWidth(self):
        return self.com_object.BoundWidth

    @property
    def boundwidth(self):
        """Alias for BoundWidth"""
        return self.BoundWidth

    @property
    def bound_width(self):
        """Alias for BoundWidth"""
        return self.BoundWidth

    def Characters(self, Start=None, Length=None):
        arguments = com_arguments([unwrap(a) for a in [Start, Length]])
        if hasattr(self.com_object, "GetCharacters"):
            return self.com_object.GetCharacters(*arguments)
        else:
            return self.com_object.Characters(*arguments)

    def characters(self, Start=None, Length=None):
        """Alias for Characters"""
        arguments = [Start, Length]
        return self.Characters(*arguments)

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Font(self):
        return self.com_object.Font

    @property
    def font(self):
        """Alias for Font"""
        return self.Font

    @property
    def LanguageID(self):
        return self.com_object.LanguageID

    @LanguageID.setter
    def LanguageID(self, value):
        self.com_object.LanguageID = value

    @property
    def languageid(self):
        """Alias for LanguageID"""
        return self.LanguageID

    @languageid.setter
    def languageid(self, value):
        """Alias for LanguageID.setter"""
        self.LanguageID = value

    @property
    def language_i_d(self):
        """Alias for LanguageID"""
        return self.LanguageID

    @language_i_d.setter
    def language_i_d(self, value):
        """Alias for LanguageID.setter"""
        self.LanguageID = value

    @property
    def Length(self):
        return self.com_object.Length

    @property
    def length(self):
        """Alias for Length"""
        return self.Length

    def Lines(self, Start=None, Length=None):
        arguments = com_arguments([unwrap(a) for a in [Start, Length]])
        if hasattr(self.com_object, "GetLines"):
            return TextRange2(self.com_object.GetLines(*arguments))
        else:
            return TextRange2(self.com_object.Lines(*arguments))

    def lines(self, Start=None, Length=None):
        """Alias for Lines"""
        arguments = [Start, Length]
        return self.Lines(*arguments)

    def MathZones(self, Start=None, Length=None):
        arguments = com_arguments([unwrap(a) for a in [Start, Length]])
        if hasattr(self.com_object, "GetMathZones"):
            return self.com_object.GetMathZones(*arguments)
        else:
            return self.com_object.MathZones(*arguments)

    def mathzones(self, Start=None, Length=None):
        """Alias for MathZones"""
        arguments = [Start, Length]
        return self.MathZones(*arguments)

    def math_zones(self, Start=None, Length=None):
        """Alias for MathZones"""
        arguments = [Start, Length]
        return self.MathZones(*arguments)

    @property
    def ParagraphFormat(self):
        return self.com_object.ParagraphFormat

    @property
    def paragraphformat(self):
        """Alias for ParagraphFormat"""
        return self.ParagraphFormat

    @property
    def paragraph_format(self):
        """Alias for ParagraphFormat"""
        return self.ParagraphFormat

    def Paragraphs(self, Start=None, Length=None):
        arguments = com_arguments([unwrap(a) for a in [Start, Length]])
        if hasattr(self.com_object, "GetParagraphs"):
            return self.com_object.GetParagraphs(*arguments)
        else:
            return self.com_object.Paragraphs(*arguments)

    def paragraphs(self, Start=None, Length=None):
        """Alias for Paragraphs"""
        arguments = [Start, Length]
        return self.Paragraphs(*arguments)

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    def Runs(self, Start=None, Length=None):
        arguments = com_arguments([unwrap(a) for a in [Start, Length]])
        if hasattr(self.com_object, "GetRuns"):
            return self.com_object.GetRuns(*arguments)
        else:
            return self.com_object.Runs(*arguments)

    def runs(self, Start=None, Length=None):
        """Alias for Runs"""
        arguments = [Start, Length]
        return self.Runs(*arguments)

    def Sentences(self, Start=None, Length=None):
        arguments = com_arguments([unwrap(a) for a in [Start, Length]])
        if hasattr(self.com_object, "GetSentences"):
            return TextRange2(self.com_object.GetSentences(*arguments))
        else:
            return TextRange2(self.com_object.Sentences(*arguments))

    def sentences(self, Start=None, Length=None):
        """Alias for Sentences"""
        arguments = [Start, Length]
        return self.Sentences(*arguments)

    @property
    def Start(self):
        return self.com_object.Start

    @property
    def start(self):
        """Alias for Start"""
        return self.Start

    @property
    def Text(self):
        return self.com_object.Text

    @Text.setter
    def Text(self, value):
        self.com_object.Text = value

    @property
    def text(self):
        """Alias for Text"""
        return self.Text

    @text.setter
    def text(self, value):
        """Alias for Text.setter"""
        self.Text = value

    def Words(self, Start=None, Length=None):
        arguments = com_arguments([unwrap(a) for a in [Start, Length]])
        if hasattr(self.com_object, "GetWords"):
            return self.com_object.GetWords(*arguments)
        else:
            return self.com_object.Words(*arguments)

    def words(self, Start=None, Length=None):
        """Alias for Words"""
        arguments = [Start, Length]
        return self.Words(*arguments)

    def AddPeriods(self):
        return self.com_object.AddPeriods()

    def addperiods(self):
        """Alias for AddPeriods"""
        return self.AddPeriods()

    def add_periods(self):
        """Alias for AddPeriods"""
        return self.AddPeriods()

    def ChangeCase(self, Type=None):
        arguments = com_arguments([unwrap(a) for a in [Type]])
        return self.com_object.ChangeCase(*arguments)

    def changecase(self, Type=None):
        """Alias for ChangeCase"""
        arguments = [Type]
        return self.ChangeCase(*arguments)

    def change_case(self, Type=None):
        """Alias for ChangeCase"""
        arguments = [Type]
        return self.ChangeCase(*arguments)

    def Copy(self):
        return self.com_object.Copy()

    def copy(self):
        """Alias for Copy"""
        return self.Copy()

    def Cut(self):
        return self.com_object.Cut()

    def cut(self):
        """Alias for Cut"""
        return self.Cut()

    def Delete(self):
        return self.com_object.Delete()

    def delete(self):
        """Alias for Delete"""
        return self.Delete()

    def Find(self, FindWhat=None, After=None, MatchCase=None, WholeWords=None):
        arguments = com_arguments([unwrap(a) for a in [FindWhat, After, MatchCase, WholeWords]])
        return TextRange2(self.com_object.Find(*arguments))

    def find(self, FindWhat=None, After=None, MatchCase=None, WholeWords=None):
        """Alias for Find"""
        arguments = [FindWhat, After, MatchCase, WholeWords]
        return self.Find(*arguments)

    def InsertAfter(self, NewText=None):
        arguments = com_arguments([unwrap(a) for a in [NewText]])
        return TextRange2(self.com_object.InsertAfter(*arguments))

    def insertafter(self, NewText=None):
        """Alias for InsertAfter"""
        arguments = [NewText]
        return self.InsertAfter(*arguments)

    def insert_after(self, NewText=None):
        """Alias for InsertAfter"""
        arguments = [NewText]
        return self.InsertAfter(*arguments)

    def InsertBefore(self, NewText=None):
        arguments = com_arguments([unwrap(a) for a in [NewText]])
        return TextRange2(self.com_object.InsertBefore(*arguments))

    def insertbefore(self, NewText=None):
        """Alias for InsertBefore"""
        arguments = [NewText]
        return self.InsertBefore(*arguments)

    def insert_before(self, NewText=None):
        """Alias for InsertBefore"""
        arguments = [NewText]
        return self.InsertBefore(*arguments)

    def InsertChartField(self, ChartFieldType=None, Formula=None, Position=None):
        arguments = com_arguments([unwrap(a) for a in [ChartFieldType, Formula, Position]])
        return TextRange2(self.com_object.InsertChartField(*arguments))

    def insertchartfield(self, ChartFieldType=None, Formula=None, Position=None):
        """Alias for InsertChartField"""
        arguments = [ChartFieldType, Formula, Position]
        return self.InsertChartField(*arguments)

    def insert_chart_field(self, ChartFieldType=None, Formula=None, Position=None):
        """Alias for InsertChartField"""
        arguments = [ChartFieldType, Formula, Position]
        return self.InsertChartField(*arguments)

    def InsertSymbol(self, FontName=None, CharNumber=None, Unicode=None):
        arguments = com_arguments([unwrap(a) for a in [FontName, CharNumber, Unicode]])
        return TextRange2(self.com_object.InsertSymbol(*arguments))

    def insertsymbol(self, FontName=None, CharNumber=None, Unicode=None):
        """Alias for InsertSymbol"""
        arguments = [FontName, CharNumber, Unicode]
        return self.InsertSymbol(*arguments)

    def insert_symbol(self, FontName=None, CharNumber=None, Unicode=None):
        """Alias for InsertSymbol"""
        arguments = [FontName, CharNumber, Unicode]
        return self.InsertSymbol(*arguments)

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        return TextRange2(self.com_object.Item(*arguments))

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)

    def LtrRun(self):
        return self.com_object.LtrRun()

    def ltrrun(self):
        """Alias for LtrRun"""
        return self.LtrRun()

    def ltr_run(self):
        """Alias for LtrRun"""
        return self.LtrRun()

    def Paste(self):
        return TextRange2(self.com_object.Paste())

    def paste(self):
        """Alias for Paste"""
        return self.Paste()

    def PasteSpecial(self, Format=None):
        arguments = com_arguments([unwrap(a) for a in [Format]])
        return TextRange2(self.com_object.PasteSpecial(*arguments))

    def pastespecial(self, Format=None):
        """Alias for PasteSpecial"""
        arguments = [Format]
        return self.PasteSpecial(*arguments)

    def paste_special(self, Format=None):
        """Alias for PasteSpecial"""
        arguments = [Format]
        return self.PasteSpecial(*arguments)

    def RemovePeriods(self):
        return self.com_object.RemovePeriods()

    def removeperiods(self):
        """Alias for RemovePeriods"""
        return self.RemovePeriods()

    def remove_periods(self):
        """Alias for RemovePeriods"""
        return self.RemovePeriods()

    def Replace(self, FindWhat=None, ReplaceWhat=None, After=None, MatchCase=None, WholeWords=None):
        arguments = com_arguments([unwrap(a) for a in [FindWhat, ReplaceWhat, After, MatchCase, WholeWords]])
        return TextRange2(self.com_object.Replace(*arguments))

    def replace(self, FindWhat=None, ReplaceWhat=None, After=None, MatchCase=None, WholeWords=None):
        """Alias for Replace"""
        arguments = [FindWhat, ReplaceWhat, After, MatchCase, WholeWords]
        return self.Replace(*arguments)

    def RotatedBounds(self, X1=None, Y1=None, X2=None, Y2=None, X3=None, Y3=None, x4=None, y4=None):
        arguments = com_arguments([unwrap(a) for a in [X1, Y1, X2, Y2, X3, Y3, x4, y4]])
        return self.com_object.RotatedBounds(*arguments)

    def rotatedbounds(self, X1=None, Y1=None, X2=None, Y2=None, X3=None, Y3=None, x4=None, y4=None):
        """Alias for RotatedBounds"""
        arguments = [X1, Y1, X2, Y2, X3, Y3, x4, y4]
        return self.RotatedBounds(*arguments)

    def rotated_bounds(self, X1=None, Y1=None, X2=None, Y2=None, X3=None, Y3=None, x4=None, y4=None):
        """Alias for RotatedBounds"""
        arguments = [X1, Y1, X2, Y2, X3, Y3, x4, y4]
        return self.RotatedBounds(*arguments)

    def RtlRun(self):
        return self.com_object.RtlRun()

    def rtlrun(self):
        """Alias for RtlRun"""
        return self.RtlRun()

    def rtl_run(self):
        """Alias for RtlRun"""
        return self.RtlRun()

    def Select(self):
        return self.com_object.Select()

    def select(self):
        """Alias for Select"""
        return self.Select()

    def TrimText(self):
        return TextRange2(self.com_object.TrimText())

    def trimtext(self):
        """Alias for TrimText"""
        return self.TrimText()

    def trim_text(self):
        """Alias for TrimText"""
        return self.TrimText()


class ThemeColor:

    def __init__(self, themecolor=None):
        self.com_object= themecolor

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    @property
    def RGB(self):
        return self.com_object.RGB

    @RGB.setter
    def RGB(self, value):
        self.com_object.RGB = value

    @property
    def rgb(self):
        """Alias for RGB"""
        return self.RGB

    @rgb.setter
    def rgb(self, value):
        """Alias for RGB.setter"""
        self.RGB = value

    @property
    def r_g_b(self):
        """Alias for RGB"""
        return self.RGB

    @r_g_b.setter
    def r_g_b(self, value):
        """Alias for RGB.setter"""
        self.RGB = value

    @property
    def ThemeColorSchemeIndex(self):
        return self.com_object.ThemeColorSchemeIndex

    @property
    def themecolorschemeindex(self):
        """Alias for ThemeColorSchemeIndex"""
        return self.ThemeColorSchemeIndex

    @property
    def theme_color_scheme_index(self):
        """Alias for ThemeColorSchemeIndex"""
        return self.ThemeColorSchemeIndex


class ThemeColorScheme:

    def __init__(self, themecolorscheme=None):
        self.com_object= themecolorscheme

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    def Colors(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        return ThemeColor(self.com_object.Colors(*arguments))

    def colors(self, Index=None):
        """Alias for Colors"""
        arguments = [Index]
        return self.Colors(*arguments)

    def GetCustomColor(self, Name=None):
        arguments = com_arguments([unwrap(a) for a in [Name]])
        return MsoThemeColorSchemeIndex(self.com_object.GetCustomColor(*arguments))

    def getcustomcolor(self, Name=None):
        """Alias for GetCustomColor"""
        arguments = [Name]
        return self.GetCustomColor(*arguments)

    def get_custom_color(self, Name=None):
        """Alias for GetCustomColor"""
        arguments = [Name]
        return self.GetCustomColor(*arguments)

    def Load(self, FileName=None):
        arguments = com_arguments([unwrap(a) for a in [FileName]])
        return self.com_object.Load(*arguments)

    def load(self, FileName=None):
        """Alias for Load"""
        arguments = [FileName]
        return self.Load(*arguments)

    def Save(self, FileName=None):
        arguments = com_arguments([unwrap(a) for a in [FileName]])
        return self.com_object.Save(*arguments)

    def save(self, FileName=None):
        """Alias for Save"""
        arguments = [FileName]
        return self.Save(*arguments)


class ThemeEffectScheme:

    def __init__(self, themeeffectscheme=None):
        self.com_object= themeeffectscheme

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    def Load(self, FileName=None):
        arguments = com_arguments([unwrap(a) for a in [FileName]])
        return self.com_object.Load(*arguments)

    def load(self, FileName=None):
        """Alias for Load"""
        arguments = [FileName]
        return self.Load(*arguments)


class ThemeFont:

    def __init__(self, themefont=None):
        self.com_object= themefont

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Name(self):
        return self.com_object.Name

    @Name.setter
    def Name(self, value):
        self.com_object.Name = value

    @property
    def name(self):
        """Alias for Name"""
        return self.Name

    @name.setter
    def name(self, value):
        """Alias for Name.setter"""
        self.Name = value

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent


class ThemeFonts:

    def __init__(self, themefonts=None):
        self.com_object= themefonts

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        return ThemeFont(self.com_object.Item(*arguments))

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)


class ThemeFontScheme:

    def __init__(self, themefontscheme=None):
        self.com_object= themefontscheme

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def MajorFont(self):
        return self.com_object.MajorFont

    @property
    def majorfont(self):
        """Alias for MajorFont"""
        return self.MajorFont

    @property
    def major_font(self):
        """Alias for MajorFont"""
        return self.MajorFont

    @property
    def MinorFont(self):
        return self.com_object.MinorFont

    @property
    def minorfont(self):
        """Alias for MinorFont"""
        return self.MinorFont

    @property
    def minor_font(self):
        """Alias for MinorFont"""
        return self.MinorFont

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    def Load(self, FileName=None):
        arguments = com_arguments([unwrap(a) for a in [FileName]])
        return self.com_object.Load(*arguments)

    def load(self, FileName=None):
        """Alias for Load"""
        arguments = [FileName]
        return self.Load(*arguments)

    def Save(self, FileName=None):
        arguments = com_arguments([unwrap(a) for a in [FileName]])
        return self.com_object.Save(*arguments)

    def save(self, FileName=None):
        """Alias for Save"""
        arguments = [FileName]
        return self.Save(*arguments)


class UserPermission:

    def __init__(self, userpermission=None):
        self.com_object= userpermission

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def ExpirationDate(self):
        return self.com_object.ExpirationDate

    @ExpirationDate.setter
    def ExpirationDate(self, value):
        self.com_object.ExpirationDate = value

    @property
    def expirationdate(self):
        """Alias for ExpirationDate"""
        return self.ExpirationDate

    @expirationdate.setter
    def expirationdate(self, value):
        """Alias for ExpirationDate.setter"""
        self.ExpirationDate = value

    @property
    def expiration_date(self):
        """Alias for ExpirationDate"""
        return self.ExpirationDate

    @expiration_date.setter
    def expiration_date(self, value):
        """Alias for ExpirationDate.setter"""
        self.ExpirationDate = value

    @property
    def Parent(self):
        return self.com_object.Parent

    @property
    def parent(self):
        """Alias for Parent"""
        return self.Parent

    @property
    def Permission(self):
        return self.com_object.Permission

    @Permission.setter
    def Permission(self, value):
        self.com_object.Permission = value

    @property
    def permission(self):
        """Alias for Permission"""
        return self.Permission

    @permission.setter
    def permission(self, value):
        """Alias for Permission.setter"""
        self.Permission = value

    @property
    def UserId(self):
        return self.com_object.UserId

    @property
    def userid(self):
        """Alias for UserId"""
        return self.UserId

    @property
    def user_id(self):
        """Alias for UserId"""
        return self.UserId

    def Remove(self):
        return self.com_object.Remove()

    def remove(self):
        """Alias for Remove"""
        return self.Remove()


class WebPageFont:

    def __init__(self, webpagefont=None):
        self.com_object= webpagefont

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def FixedWidthFont(self):
        return self.com_object.FixedWidthFont

    @FixedWidthFont.setter
    def FixedWidthFont(self, value):
        self.com_object.FixedWidthFont = value

    @property
    def fixedwidthfont(self):
        """Alias for FixedWidthFont"""
        return self.FixedWidthFont

    @fixedwidthfont.setter
    def fixedwidthfont(self, value):
        """Alias for FixedWidthFont.setter"""
        self.FixedWidthFont = value

    @property
    def fixed_width_font(self):
        """Alias for FixedWidthFont"""
        return self.FixedWidthFont

    @fixed_width_font.setter
    def fixed_width_font(self, value):
        """Alias for FixedWidthFont.setter"""
        self.FixedWidthFont = value

    @property
    def FixedWidthFontSize(self):
        return self.com_object.FixedWidthFontSize

    @FixedWidthFontSize.setter
    def FixedWidthFontSize(self, value):
        self.com_object.FixedWidthFontSize = value

    @property
    def fixedwidthfontsize(self):
        """Alias for FixedWidthFontSize"""
        return self.FixedWidthFontSize

    @fixedwidthfontsize.setter
    def fixedwidthfontsize(self, value):
        """Alias for FixedWidthFontSize.setter"""
        self.FixedWidthFontSize = value

    @property
    def fixed_width_font_size(self):
        """Alias for FixedWidthFontSize"""
        return self.FixedWidthFontSize

    @fixed_width_font_size.setter
    def fixed_width_font_size(self, value):
        """Alias for FixedWidthFontSize.setter"""
        self.FixedWidthFontSize = value

    @property
    def ProportionalFont(self):
        return self.com_object.ProportionalFont

    @ProportionalFont.setter
    def ProportionalFont(self, value):
        self.com_object.ProportionalFont = value

    @property
    def proportionalfont(self):
        """Alias for ProportionalFont"""
        return self.ProportionalFont

    @proportionalfont.setter
    def proportionalfont(self, value):
        """Alias for ProportionalFont.setter"""
        self.ProportionalFont = value

    @property
    def proportional_font(self):
        """Alias for ProportionalFont"""
        return self.ProportionalFont

    @proportional_font.setter
    def proportional_font(self, value):
        """Alias for ProportionalFont.setter"""
        self.ProportionalFont = value

    @property
    def ProportionalFontSize(self):
        return self.com_object.ProportionalFontSize

    @ProportionalFontSize.setter
    def ProportionalFontSize(self, value):
        self.com_object.ProportionalFontSize = value

    @property
    def proportionalfontsize(self):
        """Alias for ProportionalFontSize"""
        return self.ProportionalFontSize

    @proportionalfontsize.setter
    def proportionalfontsize(self, value):
        """Alias for ProportionalFontSize.setter"""
        self.ProportionalFontSize = value

    @property
    def proportional_font_size(self):
        """Alias for ProportionalFontSize"""
        return self.ProportionalFontSize

    @proportional_font_size.setter
    def proportional_font_size(self, value):
        """Alias for ProportionalFontSize.setter"""
        self.ProportionalFontSize = value


class WebPageFonts:

    def __init__(self, webpagefonts=None):
        self.com_object= webpagefonts

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        if hasattr(self.com_object, "GetItem"):
            return self.com_object.GetItem(*arguments)
        else:
            return self.com_object.Item(*arguments)

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)


class WorkflowTask:

    def __init__(self, workflowtask=None):
        self.com_object= workflowtask

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def AssignedTo(self):
        return self.com_object.AssignedTo

    @property
    def assignedto(self):
        """Alias for AssignedTo"""
        return self.AssignedTo

    @property
    def assigned_to(self):
        """Alias for AssignedTo"""
        return self.AssignedTo

    @property
    def CreatedBy(self):
        return self.com_object.CreatedBy

    @property
    def createdby(self):
        """Alias for CreatedBy"""
        return self.CreatedBy

    @property
    def created_by(self):
        """Alias for CreatedBy"""
        return self.CreatedBy

    @property
    def CreatedDate(self):
        return self.com_object.CreatedDate

    @property
    def createddate(self):
        """Alias for CreatedDate"""
        return self.CreatedDate

    @property
    def created_date(self):
        """Alias for CreatedDate"""
        return self.CreatedDate

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Description(self):
        return self.com_object.Description

    @property
    def description(self):
        """Alias for Description"""
        return self.Description

    @property
    def DueDate(self):
        return self.com_object.DueDate

    @property
    def duedate(self):
        """Alias for DueDate"""
        return self.DueDate

    @property
    def due_date(self):
        """Alias for DueDate"""
        return self.DueDate

    @property
    def Id(self):
        return self.com_object.Id

    @property
    def id(self):
        """Alias for Id"""
        return self.Id

    @property
    def ListID(self):
        return self.com_object.ListID

    @property
    def listid(self):
        """Alias for ListID"""
        return self.ListID

    @property
    def list_i_d(self):
        """Alias for ListID"""
        return self.ListID

    @property
    def Name(self):
        return self.com_object.Name

    @property
    def name(self):
        """Alias for Name"""
        return self.Name

    @property
    def WorkflowID(self):
        return self.com_object.WorkflowID

    @property
    def workflowid(self):
        """Alias for WorkflowID"""
        return self.WorkflowID

    @property
    def workflow_i_d(self):
        """Alias for WorkflowID"""
        return self.WorkflowID

    def Show(self):
        return self.com_object.Show()

    def show(self):
        """Alias for Show"""
        return self.Show()


class WorkflowTasks:

    def __init__(self, workflowtasks=None):
        self.com_object= workflowtasks

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        if hasattr(self.com_object, "GetItem"):
            return self.com_object.GetItem(*arguments)
        else:
            return self.com_object.Item(*arguments)

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)


class WorkflowTemplate:

    def __init__(self, workflowtemplate=None):
        self.com_object= workflowtemplate

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    @property
    def Description(self):
        return self.com_object.Description

    @property
    def description(self):
        """Alias for Description"""
        return self.Description

    @property
    def DocumentLibraryName(self):
        return self.com_object.DocumentLibraryName

    @property
    def documentlibraryname(self):
        """Alias for DocumentLibraryName"""
        return self.DocumentLibraryName

    @property
    def document_library_name(self):
        """Alias for DocumentLibraryName"""
        return self.DocumentLibraryName

    @property
    def DocumentLibraryURL(self):
        return self.com_object.DocumentLibraryURL

    @property
    def documentlibraryurl(self):
        """Alias for DocumentLibraryURL"""
        return self.DocumentLibraryURL

    @property
    def document_library_u_r_l(self):
        """Alias for DocumentLibraryURL"""
        return self.DocumentLibraryURL

    @property
    def Id(self):
        return self.com_object.Id

    @property
    def id(self):
        """Alias for Id"""
        return self.Id

    @property
    def Name(self):
        return self.com_object.Name

    @property
    def name(self):
        """Alias for Name"""
        return self.Name

    def Show(self):
        return self.com_object.Show()

    def show(self):
        """Alias for Show"""
        return self.Show()


class WorkflowTemplates:

    def __init__(self, workflowtemplates=None):
        self.com_object= workflowtemplates

    @property
    def Application(self):
        return self.com_object.Application

    @property
    def application(self):
        """Alias for Application"""
        return self.Application

    @property
    def Count(self):
        return self.com_object.Count

    @property
    def count(self):
        """Alias for Count"""
        return self.Count

    @property
    def Creator(self):
        return self.com_object.Creator

    @property
    def creator(self):
        """Alias for Creator"""
        return self.Creator

    def Item(self, Index=None):
        arguments = com_arguments([unwrap(a) for a in [Index]])
        if hasattr(self.com_object, "GetItem"):
            return self.com_object.GetItem(*arguments)
        else:
            return self.com_object.Item(*arguments)

    def item(self, Index=None):
        """Alias for Item"""
        arguments = [Index]
        return self.Item(*arguments)

    def __call__(self, Index=None):
        return self.Item(Index)


# XlDataLabelPosition enumeration
xlLabelPositionAbove = 0
xlLabelPositionBelow = 1
xlLabelPositionBestFit = 5
xlLabelPositionCenter = -4108
xlLabelPositionCustom = 7
xlLabelPositionInsideBase = 4
xlLabelPositionInsideEnd = 3
xlLabelPositionLeft = -4131
xlLabelPositionMixed = 6
xlLabelPositionOutsideEnd = 2
xlLabelPositionRight = -4152

# XlDisplayUnit enumeration
xlDisplayUnitCustom = -4114
xlDisplayUnitNone = -4142
xlHundredMillions = -8
xlHundreds = -2
xlHundredThousands = -5
xlMillionMillions = -10
xlMillions = -6
xlTenMillions = -7
xlTenThousands = -4
xlThousandMillions = -9
xlThousands = -3

# XlPivotFieldOrientation enumeration
xlColumnField = 2
xlDataField = 4
xlHidden = 0
xlPageField = 3
xlRowField = 1

# XlSizeRepresents enumeration
xlSizeIsArea = 1
xlSizeIsWidth = 2

# XlTimeUnit enumeration
xlDays = 0
xlMonths = 1
xlYears = 2
