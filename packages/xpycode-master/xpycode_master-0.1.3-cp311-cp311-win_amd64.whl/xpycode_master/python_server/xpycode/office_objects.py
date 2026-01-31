
class Blob:
    pass

class HTMLElement:
    pass

class Office:
    
    class ActiveView:
        Read = 0
        Edit = 1
    
    class AsyncResultStatus:
        Succeeded = 0
        Failed = 1
    
    class BindingType:
        Text = 0
        Matrix = 1
        Table = 2
    
    class CoercionType:
        Text = 0
        Matrix = 1
        Table = 2
        Html = 3
        Ooxml = 4
        SlideRange = 5
        Image = 6
        XmlSvg = 7
    
    class CustomXMLNodeType:
        Attribute = 0
        CData = 1
        NodeComment = 2
        Element = 3
        NodeDocument = 4
        ProcessingInstruction = 5
        Text = 6
    
    class DevicePermissionType:
        camera = 0
        geolocation = 1
        microphone = 2
    
    class DocumentMode:
        ReadOnly = 0
        ReadWrite = 1
    
    class EventType:
        ActiveViewChanged = 0
        AppointmentTimeChanged = 1
        AttachmentsChanged = 2
        BindingDataChanged = 3
        BindingSelectionChanged = 4
        DialogEventReceived = 5
        DialogMessageReceived = 6
        DialogParentMessageReceived = 7
        DocumentSelectionChanged = 8
        EnhancedLocationsChanged = 9
        InfobarClicked = 10
        InitializationContextChanged = 11
        ItemChanged = 12
        DragAndDropEvent = 13
        NodeDeleted = 14
        NodeInserted = 15
        NodeReplaced = 16
        OfficeThemeChanged = 17
        RecipientsChanged = 18
        RecurrenceChanged = 19
        ResourceSelectionChanged = 20
        SelectedItemsChanged = 21
        SensitivityLabelChanged = 22
        SettingsChanged = 23
        SpamReporting = 24
        TaskSelectionChanged = 25
        ViewSelectionChanged = 26
    
    class FileType:
        Text = 0
        Compressed = 1
        Pdf = 2
    
    class FilterType:
        All = 0
        OnlyVisible = 1
    
    class GoToType:
        Binding = 0
        NamedItem = 1
        Slide = 2
        Index = 3
    
    class HostType:
        Word = 0
        Excel = 1
        PowerPoint = 2
        Outlook = 3
        OneNote = 4
        Project = 5
        Access = 6
    
    class Index:
        First = 0
        Last = 1
        Next = 2
        Previous = 3
    
    class InitializationReason:
        Inserted = 0
        DocumentOpened = 1
    
    class PlatformType:
        PC = 0
        OfficeOnline = 1
        Mac = 2
        iOS = 3
        Android = 4
        Universal = 5
    
    class ProjectProjectFields:
        CurrencyDigits = 0
        CurrencySymbol = 1
        CurrencySymbolPosition = 2
        DurationUnits = 3
        GUID = 4
        Finish = 5
        Start = 6
        ReadOnly = 7
        VERSION = 8
        WorkUnits = 9
        ProjectServerUrl = 10
        WSSUrl = 11
        WSSList = 12
    
    class ProjectResourceFields:
        Accrual = 0
        ActualCost = 1
        ActualOvertimeCost = 2
        ActualOvertimeWork = 3
        ActualOvertimeWorkProtected = 4
        ActualWork = 5
        ActualWorkProtected = 6
        BaseCalendar = 7
        Baseline10BudgetCost = 8
        Baseline10BudgetWork = 9
        Baseline10Cost = 10
        Baseline10Work = 11
        Baseline1BudgetCost = 12
        Baseline1BudgetWork = 13
        Baseline1Cost = 14
        Baseline1Work = 15
        Baseline2BudgetCost = 16
        Baseline2BudgetWork = 17
        Baseline2Cost = 18
        Baseline2Work = 19
        Baseline3BudgetCost = 20
        Baseline3BudgetWork = 21
        Baseline3Cost = 22
        Baseline3Work = 23
        Baseline4BudgetCost = 24
        Baseline4BudgetWork = 25
        Baseline4Cost = 26
        Baseline4Work = 27
        Baseline5BudgetCost = 28
        Baseline5BudgetWork = 29
        Baseline5Cost = 30
        Baseline5Work = 31
        Baseline6BudgetCost = 32
        Baseline6BudgetWork = 33
        Baseline6Cost = 34
        Baseline6Work = 35
        Baseline7BudgetCost = 36
        Baseline7BudgetWork = 37
        Baseline7Cost = 38
        Baseline7Work = 39
        Baseline8BudgetCost = 40
        Baseline8BudgetWork = 41
        Baseline8Cost = 42
        Baseline8Work = 43
        Baseline9BudgetCost = 44
        Baseline9BudgetWork = 45
        Baseline9Cost = 46
        Baseline9Work = 47
        BaselineBudgetCost = 48
        BaselineBudgetWork = 49
        BaselineCost = 50
        BaselineWork = 51
        BudgetCost = 52
        BudgetWork = 53
        ResourceCalendarGUID = 54
        Code = 55
        Cost1 = 56
        Cost10 = 57
        Cost2 = 58
        Cost3 = 59
        Cost4 = 60
        Cost5 = 61
        Cost6 = 62
        Cost7 = 63
        Cost8 = 64
        Cost9 = 65
        ResourceCreationDate = 66
        Date1 = 67
        Date10 = 68
        Date2 = 69
        Date3 = 70
        Date4 = 71
        Date5 = 72
        Date6 = 73
        Date7 = 74
        Date8 = 75
        Date9 = 76
        Duration1 = 77
        Duration10 = 78
        Duration2 = 79
        Duration3 = 80
        Duration4 = 81
        Duration5 = 82
        Duration6 = 83
        Duration7 = 84
        Duration8 = 85
        Duration9 = 86
        Email = 87
        End = 88
        Finish1 = 89
        Finish10 = 90
        Finish2 = 91
        Finish3 = 92
        Finish4 = 93
        Finish5 = 94
        Finish6 = 95
        Finish7 = 96
        Finish8 = 97
        Finish9 = 98
        Flag10 = 99
        Flag1 = 100
        Flag11 = 101
        Flag12 = 102
        Flag13 = 103
        Flag14 = 104
        Flag15 = 105
        Flag16 = 106
        Flag17 = 107
        Flag18 = 108
        Flag19 = 109
        Flag2 = 110
        Flag20 = 111
        Flag3 = 112
        Flag4 = 113
        Flag5 = 114
        Flag6 = 115
        Flag7 = 116
        Flag8 = 117
        Flag9 = 118
        Group = 119
        Units = 120
        Name = 121
        Notes = 122
        Number1 = 123
        Number10 = 124
        Number11 = 125
        Number12 = 126
        Number13 = 127
        Number14 = 128
        Number15 = 129
        Number16 = 130
        Number17 = 131
        Number18 = 132
        Number19 = 133
        Number2 = 134
        Number20 = 135
        Number3 = 136
        Number4 = 137
        Number5 = 138
        Number6 = 139
        Number7 = 140
        Number8 = 141
        Number9 = 142
        OvertimeCost = 143
        OvertimeRate = 144
        OvertimeWork = 145
        PercentWorkComplete = 146
        CostPerUse = 147
        Generic = 148
        OverAllocated = 149
        RegularWork = 150
        RemainingCost = 151
        RemainingOvertimeCost = 152
        RemainingOvertimeWork = 153
        RemainingWork = 154
        ResourceGUID = 155
        Cost = 156
        Work = 157
        Start = 158
        Start1 = 159
        Start10 = 160
        Start2 = 161
        Start3 = 162
        Start4 = 163
        Start5 = 164
        Start6 = 165
        Start7 = 166
        Start8 = 167
        Start9 = 168
        StandardRate = 169
        Text1 = 170
        Text10 = 171
        Text11 = 172
        Text12 = 173
        Text13 = 174
        Text14 = 175
        Text15 = 176
        Text16 = 177
        Text17 = 178
        Text18 = 179
        Text19 = 180
        Text2 = 181
        Text20 = 182
        Text21 = 183
        Text22 = 184
        Text23 = 185
        Text24 = 186
        Text25 = 187
        Text26 = 188
        Text27 = 189
        Text28 = 190
        Text29 = 191
        Text3 = 192
        Text30 = 193
        Text4 = 194
        Text5 = 195
        Text6 = 196
        Text7 = 197
        Text8 = 198
        Text9 = 199
    
    class ProjectTaskFields:
        ActualCost = 0
        ActualDuration = 1
        ActualFinish = 2
        ActualOvertimeCost = 3
        ActualOvertimeWork = 4
        ActualStart = 5
        ActualWork = 6
        Text1 = 7
        Text10 = 8
        Finish10 = 9
        Start10 = 10
        Text11 = 11
        Text12 = 12
        Text13 = 13
        Text14 = 14
        Text15 = 15
        Text16 = 16
        Text17 = 17
        Text18 = 18
        Text19 = 19
        Finish1 = 20
        Start1 = 21
        Text2 = 22
        Text20 = 23
        Text21 = 24
        Text22 = 25
        Text23 = 26
        Text24 = 27
        Text25 = 28
        Text26 = 29
        Text27 = 30
        Text28 = 31
        Text29 = 32
        Finish2 = 33
        Start2 = 34
        Text3 = 35
        Text30 = 36
        Finish3 = 37
        Start3 = 38
        Text4 = 39
        Finish4 = 40
        Start4 = 41
        Text5 = 42
        Finish5 = 43
        Start5 = 44
        Text6 = 45
        Finish6 = 46
        Start6 = 47
        Text7 = 48
        Finish7 = 49
        Start7 = 50
        Text8 = 51
        Finish8 = 52
        Start8 = 53
        Text9 = 54
        Finish9 = 55
        Start9 = 56
        Baseline10BudgetCost = 57
        Baseline10BudgetWork = 58
        Baseline10Cost = 59
        Baseline10Duration = 60
        Baseline10Finish = 61
        Baseline10FixedCost = 62
        Baseline10FixedCostAccrual = 63
        Baseline10Start = 64
        Baseline10Work = 65
        Baseline1BudgetCost = 66
        Baseline1BudgetWork = 67
        Baseline1Cost = 68
        Baseline1Duration = 69
        Baseline1Finish = 70
        Baseline1FixedCost = 71
        Baseline1FixedCostAccrual = 72
        Baseline1Start = 73
        Baseline1Work = 74
        Baseline2BudgetCost = 75
        Baseline2BudgetWork = 76
        Baseline2Cost = 77
        Baseline2Duration = 78
        Baseline2Finish = 79
        Baseline2FixedCost = 80
        Baseline2FixedCostAccrual = 81
        Baseline2Start = 82
        Baseline2Work = 83
        Baseline3BudgetCost = 84
        Baseline3BudgetWork = 85
        Baseline3Cost = 86
        Baseline3Duration = 87
        Baseline3Finish = 88
        Baseline3FixedCost = 89
        Baseline3FixedCostAccrual = 90
        Baseline3Start = 91
        Baseline3Work = 92
        Baseline4BudgetCost = 93
        Baseline4BudgetWork = 94
        Baseline4Cost = 95
        Baseline4Duration = 96
        Baseline4Finish = 97
        Baseline4FixedCost = 98
        Baseline4FixedCostAccrual = 99
        Baseline4Start = 100
        Baseline4Work = 101
        Baseline5BudgetCost = 102
        Baseline5BudgetWork = 103
        Baseline5Cost = 104
        Baseline5Duration = 105
        Baseline5Finish = 106
        Baseline5FixedCost = 107
        Baseline5FixedCostAccrual = 108
        Baseline5Start = 109
        Baseline5Work = 110
        Baseline6BudgetCost = 111
        Baseline6BudgetWork = 112
        Baseline6Cost = 113
        Baseline6Duration = 114
        Baseline6Finish = 115
        Baseline6FixedCost = 116
        Baseline6FixedCostAccrual = 117
        Baseline6Start = 118
        Baseline6Work = 119
        Baseline7BudgetCost = 120
        Baseline7BudgetWork = 121
        Baseline7Cost = 122
        Baseline7Duration = 123
        Baseline7Finish = 124
        Baseline7FixedCost = 125
        Baseline7FixedCostAccrual = 126
        Baseline7Start = 127
        Baseline7Work = 128
        Baseline8BudgetCost = 129
        Baseline8BudgetWork = 130
        Baseline8Cost = 131
        Baseline8Duration = 132
        Baseline8Finish = 133
        Baseline8FixedCost = 134
        Baseline8FixedCostAccrual = 135
        Baseline8Start = 136
        Baseline8Work = 137
        Baseline9BudgetCost = 138
        Baseline9BudgetWork = 139
        Baseline9Cost = 140
        Baseline9Duration = 141
        Baseline9Finish = 142
        Baseline9FixedCost = 143
        Baseline9FixedCostAccrual = 144
        Baseline9Start = 145
        Baseline9Work = 146
        BaselineBudgetCost = 147
        BaselineBudgetWork = 148
        BaselineCost = 149
        BaselineDuration = 150
        BaselineFinish = 151
        BaselineFixedCost = 152
        BaselineFixedCostAccrual = 153
        BaselineStart = 154
        BaselineWork = 155
        BudgetCost = 156
        BudgetFixedCost = 157
        BudgetFixedWork = 158
        BudgetWork = 159
        TaskCalendarGUID = 160
        ConstraintDate = 161
        ConstraintType = 162
        Cost1 = 163
        Cost10 = 164
        Cost2 = 165
        Cost3 = 166
        Cost4 = 167
        Cost5 = 168
        Cost6 = 169
        Cost7 = 170
        Cost8 = 171
        Cost9 = 172
        Date1 = 173
        Date10 = 174
        Date2 = 175
        Date3 = 176
        Date4 = 177
        Date5 = 178
        Date6 = 179
        Date7 = 180
        Date8 = 181
        Date9 = 182
        Deadline = 183
        Duration1 = 184
        Duration10 = 185
        Duration2 = 186
        Duration3 = 187
        Duration4 = 188
        Duration5 = 189
        Duration6 = 190
        Duration7 = 191
        Duration8 = 192
        Duration9 = 193
        Duration = 194
        EarnedValueMethod = 195
        FinishSlack = 196
        FixedCost = 197
        FixedCostAccrual = 198
        Flag10 = 199
        Flag1 = 200
        Flag11 = 201
        Flag12 = 202
        Flag13 = 203
        Flag14 = 204
        Flag15 = 205
        Flag16 = 206
        Flag17 = 207
        Flag18 = 208
        Flag19 = 209
        Flag2 = 210
        Flag20 = 211
        Flag3 = 212
        Flag4 = 213
        Flag5 = 214
        Flag6 = 215
        Flag7 = 216
        Flag8 = 217
        Flag9 = 218
        FreeSlack = 219
        HasRollupSubTasks = 220
        ID = 221
        Name = 222
        Notes = 223
        Number1 = 224
        Number10 = 225
        Number11 = 226
        Number12 = 227
        Number13 = 228
        Number14 = 229
        Number15 = 230
        Number16 = 231
        Number17 = 232
        Number18 = 233
        Number19 = 234
        Number2 = 235
        Number20 = 236
        Number3 = 237
        Number4 = 238
        Number5 = 239
        Number6 = 240
        Number7 = 241
        Number8 = 242
        Number9 = 243
        ScheduledDuration = 244
        ScheduledFinish = 245
        ScheduledStart = 246
        OutlineLevel = 247
        OvertimeCost = 248
        OvertimeWork = 249
        PercentComplete = 250
        PercentWorkComplete = 251
        Predecessors = 252
        PreleveledFinish = 253
        PreleveledStart = 254
        Priority = 255
        Active = 256
        Critical = 257
        Milestone = 258
        Overallocated = 259
        IsRollup = 260
        Summary = 261
        RegularWork = 262
        RemainingCost = 263
        RemainingDuration = 264
        RemainingOvertimeCost = 265
        RemainingWork = 266
        ResourceNames = 267
        Cost = 268
        Finish = 269
        Start = 270
        Work = 271
        StartSlack = 272
        Status = 273
        Successors = 274
        StatusManager = 275
        TotalSlack = 276
        TaskGUID = 277
        Type = 278
        WBS = 279
        WBSPREDECESSORS = 280
        WBSSUCCESSORS = 281
        WSSID = 282
    
    class ProjectViewTypes:
        Gantt = 0
        NetworkDiagram = 1
        TaskDiagram = 2
        TaskForm = 3
        TaskSheet = 4
        ResourceForm = 5
        ResourceSheet = 6
        ResourceGraph = 7
        TeamPlanner = 8
        TaskDetails = 9
        TaskNameForm = 10
        ResourceNames = 11
        Calendar = 12
        TaskUsage = 13
        ResourceUsage = 14
        Timeline = 15
    
    class SelectionMode:
        Default = 0
        Selected = 1
        None_ = 2
    
    class StartupBehavior:
        none = 'None'
        load = 'Load'
    
    class Table:
        All = 0
        Data = 1
        Headers = 2
    
    class ThemeId:
        Black = 0
        Colorful = 1
        DarkGray = 2
        White = 3
    
    class ValueFormat:
        Unformatted = 0
        Formatted = 1
    
    class VisibilityMode:
        hidden = 'Hidden'
        taskpane = 'Taskpane'
    
    class IPromiseConstructor:
        pass
    
    class Actions:
        pass
    
    class AddBindingFromNamedItemOptions:
        pass
    
    class AddBindingFromPromptOptions:
        pass
    
    class AddBindingFromSelectionOptions:
        pass
    
    class Addin:
        pass
    
    class AsyncContextOptions:
        pass
    
    class AsyncResult:
        pass
    
    class Auth:
        pass
    
    class AuthOptions:
        pass
    
    class AuthContext:
        pass
    
    class BeforeDocumentCloseNotification:
        pass
    
    class Binding:
        pass
    
    class Bindings:
        pass
    
    class BindingDataChangedEventArgs:
        pass
    
    class BindingSelectionChangedEventArgs:
        pass
    
    class Context:
        pass
    
    class ContextInformation:
        pass
    
    class ContextMenu:
        pass
    
    class ContextMenuControl:
        pass
    
    class ContextMenuUpdaterData:
        pass
    
    class Control:
        pass
    
    class CustomXmlNode:
        pass
    
    class CustomXmlPart:
        pass
    
    class CustomXmlParts:
        pass
    
    class CustomXmlPrefixMappings:
        pass
    
    class DevicePermission:
        pass
    
    class Dialog:
        pass
    
    class DialogMessageOptions:
        pass
    
    class DialogOptions:
        pass
    
    class DialogParentMessageReceivedEventArgs:
        pass
    
    class Document:
        pass
    
    class DocumentSelectionChangedEventArgs:
        pass
    
    class Error:
        pass
    
    class ExtensionLifeCycle:
        pass
    
    class File:
        pass
    
    class FileProperties:
        pass
    
    class GetBindingDataOptions:
        pass
    
    class GetFileOptions:
        pass
    
    class GetSelectedDataOptions:
        pass
    
    class GoToByIdOptions:
        pass
    
    class Group:
        pass
    
    class MatrixBinding:
        pass
    
    class NodeDeletedEventArgs:
        pass
    
    class NodeInsertedEventArgs:
        pass
    
    class NodeReplacedEventArgs:
        pass
    
    class OfficeTheme:
        pass
    
    class RangeCoordinates:
        pass
    
    class RangeFormatConfiguration:
        pass
    
    class RemoveHandlerOptions:
        pass
    
    class RequirementSetSupport:
        pass
    
    class Ribbon:
        pass
    
    class RibbonUpdaterData:
        pass
    
    class SaveSettingsOptions:
        pass
    
    class SetBindingDataOptions:
        pass
    
    class SetSelectedDataOptions:
        pass
    
    class Settings:
        pass
    
    class SettingsChangedEventArgs:
        pass
    
    class Slice:
        pass
    
    class Tab:
        pass
    
    class TableBinding:
        pass
    
    class TableData:
        pass
    
    class TaskPane:
        pass
    
    class TextBinding:
        pass
    
    class UI:
        pass
    
    class Urls:
        pass
    
    class VisibilityModeChangedMessage:
        pass
    
    class CoercionTypeOptions:
        pass
    
    class Appointment:
        pass
    
    class AppointmentCompose:
        pass
    
    class AppointmentForm:
        pass
    
    class AppointmentRead:
        pass
    
    class AppointmentTimeChangedEventArgs:
        pass
    
    class AttachmentContent:
        pass
    
    class AttachmentDetailsCompose:
        pass
    
    class AttachmentDetails:
        pass
    
    class AttachmentsChangedEventArgs:
        pass
    
    class Body:
        pass
    
    class Categories:
        pass
    
    class CategoryDetails:
        pass
    
    class Contact:
        pass
    
    class CustomProperties:
        pass
    
    class DelayDeliveryTime:
        pass
    
    class Diagnostics:
        pass
    
    class DragAndDropEventArgs:
        pass
    
    class DragoverEventData:
        pass
    
    class DropEventData:
        pass
    
    class DroppedItems:
        pass
    
    class DroppedItemDetails:
        pass
    
    class EmailAddressDetails:
        pass
    
    class EmailUser:
        pass
    
    class EnhancedLocation:
        pass
    
    class EnhancedLocationsChangedEventArgs:
        pass
    
    class Entities:
        pass
    
    class From:
        pass
    
    class InfobarClickedEventArgs:
        pass
    
    class InfobarDetails:
        pass
    
    class InitializationContextChangedEventArgs:
        pass
    
    class InternetHeaders:
        pass
    
    class Item:
        pass
    
    class ItemCompose:
        pass
    
    class ItemRead:
        pass
    
    class LoadedMessageCompose:
        pass
    
    class LoadedMessageRead:
        pass
    
    class LocalClientTime:
        pass
    
    class Location:
        pass
    
    class LocationDetails:
        pass
    
    class LocationIdentifier:
        pass
    
    class Mailbox:
        pass
    
    class MailboxEvent:
        pass
    
    class MasterCategories:
        pass
    
    class MeetingSuggestion:
        pass
    
    class Message:
        pass
    
    class MessageCompose:
        pass
    
    class MessageRead:
        pass
    
    class NotificationMessageAction:
        pass
    
    class NotificationMessageDetails:
        pass
    
    class NotificationMessages:
        pass
    
    class OfficeThemeChangedEventArgs:
        pass
    
    class Organizer:
        pass
    
    class PhoneNumber:
        pass
    
    class Recipients:
        pass
    
    class RecipientsChangedEventArgs:
        pass
    
    class RecipientsChangedFields:
        pass
    
    class Recurrence:
        pass
    
    class RecurrenceChangedEventArgs:
        pass
    
    class RecurrenceProperties:
        pass
    
    class RecurrenceTimeZone:
        pass
    
    class ReplyFormAttachment:
        pass
    
    class ReplyFormData:
        pass
    
    class RoamingSettings:
        pass
    
    class SelectedItemDetails:
        pass
    
    class Sensitivity:
        pass
    
    class SensitivityLabel:
        pass
    
    class SensitivityLabelChangedEventArgs:
        pass
    
    class SensitivityLabelDetails:
        pass
    
    class SensitivityLabelsCatalog:
        pass
    
    class SeriesTime:
        pass
    
    class SessionData:
        pass
    
    class SharedProperties:
        pass
    
    class SmartAlertsEventCompletedOptions:
        pass
    
    class SpamReportingEventArgs:
        pass
    
    class SpamReportingEventCompletedOptions:
        pass
    
    class Subject:
        pass
    
    class TaskSuggestion:
        pass
    
    class Time:
        pass
    
    class UserProfile:
        pass
    
    class AddinCommands:
        
        class Event:
            pass
        
        class EventCompletedOptions:
            pass
        
        class Source:
            pass
    
    class MailboxEnums:
        
        class ActionType:
            ShowTaskPane = 'showTaskPane'
        
        class AppointmentSensitivityType:
            Normal = 'normal'
            Personal = 'personal'
            Private = 'private'
            Confidential = 'confidential'
        
        class AttachmentContentFormat:
            Base64 = 'base64'
            Url = 'url'
            Eml = 'eml'
            ICalendar = 'iCalendar'
        
        class AttachmentStatus:
            Added = 'added'
            Removed = 'removed'
        
        class AttachmentType:
            Base64 = 'base64'
            Cloud = 'cloud'
            File = 'file'
            Item = 'item'
        
        class BodyMode:
            FullBody = 0
            HostConfig = 1
        
        class CategoryColor:
            None_ = 0
            Preset0 = 1
            Preset1 = 2
            Preset2 = 3
            Preset3 = 4
            Preset4 = 5
            Preset5 = 6
            Preset6 = 7
            Preset7 = 8
            Preset8 = 9
            Preset9 = 10
            Preset10 = 11
            Preset11 = 12
            Preset12 = 13
            Preset13 = 14
            Preset14 = 15
            Preset15 = 16
            Preset16 = 17
            Preset17 = 18
            Preset18 = 19
            Preset19 = 20
            Preset20 = 21
            Preset21 = 22
            Preset22 = 23
            Preset23 = 24
            Preset24 = 25
        
        class ComposeType:
            Reply = 'reply'
            NewMail = 'newMail'
            Forward = 'forward'
        
        class Days:
            Mon = 'mon'
            Tue = 'tue'
            Wed = 'wed'
            Thu = 'thu'
            Fri = 'fri'
            Sat = 'sat'
            Sun = 'sun'
            Weekday = 'weekday'
            WeekendDay = 'weekendDay'
            Day = 'day'
        
        class DelegatePermissions:
            Read = 1
            Write = 2
            DeleteOwn = 4
            DeleteAll = 8
            EditOwn = 16
            EditAll = 32
        
        class EntityType:
            MeetingSuggestion = 'meetingSuggestion'
            TaskSuggestion = 'taskSuggestion'
            Address = 'address'
            EmailAddress = 'emailAddress'
            Url = 'url'
            PhoneNumber = 'phoneNumber'
            Contact = 'contact'
        
        class InfobarActionType:
            Dismiss = 1
        
        class InfobarType:
            Informational = 0
            ProgressIndicator = 1
            Error = 2
            Insight = 3
        
        class ItemNotificationMessageType:
            ProgressIndicator = 'progressIndicator'
            InformationalMessage = 'informationalMessage'
            ErrorMessage = 'errorMessage'
            InsightMessage = 'insightMessage'
        
        class ItemType:
            Message = 'message'
            Appointment = 'appointment'
        
        class LocationType:
            Custom = 'custom'
            Room = 'room'
        
        class Month:
            Jan = 'jan'
            Feb = 'feb'
            Mar = 'mar'
            Apr = 'apr'
            May = 'may'
            Jun = 'jun'
            Jul = 'jul'
            Aug = 'aug'
            Sep = 'sep'
            Oct = 'oct'
            Nov = 'nov'
            Dec = 'dec'
        
        class MoveSpamItemTo:
            CustomFolder = 'customFolder'
            DeletedItemsFolder = 'deletedItemsFolder'
            JunkFolder = 'junkFolder'
            NoMove = 'noMove'
        
        class OpenLocation:
            AccountDocument = 0
            Camera = 1
            Local = 2
            OnedriveForBusiness = 3
            Other = 4
            PhotoLibrary = 5
            SharePoint = 6
        
        class OWAView:
            OneColumnNarrow = 'OneColumnNarrow'
            OneColumn = 'OneColumn'
            TwoColumns = 'TwoColumns'
            ThreeColumns = 'ThreeColumns'
        
        class RecipientType:
            DistributionList = 'distributionList'
            User = 'user'
            ExternalUser = 'externalUser'
            Other = 'other'
        
        class RecurrenceTimeZone:
            AfghanistanStandardTime = 'Afghanistan Standard Time'
            AlaskanStandardTime = 'Alaskan Standard Time'
            AleutianStandardTime = 'Aleutian Standard Time'
            AltaiStandardTime = 'Altai Standard Time'
            ArabStandardTime = 'Arab Standard Time'
            ArabianStandardTime = 'Arabian Standard Time'
            ArabicStandardTime = 'Arabic Standard Time'
            ArgentinaStandardTime = 'Argentina Standard Time'
            AstrakhanStandardTime = 'Astrakhan Standard Time'
            AtlanticStandardTime = 'Atlantic Standard Time'
            AUSCentralStandardTime = 'AUS Central Standard Time'
            AusCentralW_StandardTime = 'Aus Central W. Standard Time'
            AUSEasternStandardTime = 'AUS Eastern Standard Time'
            AzerbaijanStandardTime = 'Azerbaijan Standard Time'
            AzoresStandardTime = 'Azores Standard Time'
            BahiaStandardTime = 'Bahia Standard Time'
            BangladeshStandardTime = 'Bangladesh Standard Time'
            BelarusStandardTime = 'Belarus Standard Time'
            BougainvilleStandardTime = 'Bougainville Standard Time'
            CanadaCentralStandardTime = 'Canada Central Standard Time'
            CapeVerdeStandardTime = 'Cape Verde Standard Time'
            CaucasusStandardTime = 'Caucasus Standard Time'
            CenAustraliaStandardTime = 'Cen. Australia Standard Time'
            CentralAmericaStandardTime = 'Central America Standard Time'
            CentralAsiaStandardTime = 'Central Asia Standard Time'
            CentralBrazilianStandardTime = 'Central Brazilian Standard Time'
            CentralEuropeStandardTime = 'Central Europe Standard Time'
            CentralEuropeanStandardTime = 'Central European Standard Time'
            CentralPacificStandardTime = 'Central Pacific Standard Time'
            CentralStandardTime = 'Central Standard Time'
            CentralStandardTime_Mexico = 'Central Standard Time (Mexico)'
            ChathamIslandsStandardTime = 'Chatham Islands Standard Time'
            ChinaStandardTime = 'China Standard Time'
            CubaStandardTime = 'Cuba Standard Time'
            DatelineStandardTime = 'Dateline Standard Time'
            E_AfricaStandardTime = 'E. Africa Standard Time'
            E_AustraliaStandardTime = 'E. Australia Standard Time'
            E_EuropeStandardTime = 'E. Europe Standard Time'
            E_SouthAmericaStandardTime = 'E. South America Standard Time'
            EasterIslandStandardTime = 'Easter Island Standard Time'
            EasternStandardTime = 'Eastern Standard Time'
            EasternStandardTime_Mexico = 'Eastern Standard Time (Mexico)'
            EgyptStandardTime = 'Egypt Standard Time'
            EkaterinburgStandardTime = 'Ekaterinburg Standard Time'
            FijiStandardTime = 'Fiji Standard Time'
            FLEStandardTime = 'FLE Standard Time'
            GeorgianStandardTime = 'Georgian Standard Time'
            GMTStandardTime = 'GMT Standard Time'
            GreenlandStandardTime = 'Greenland Standard Time'
            GreenwichStandardTime = 'Greenwich Standard Time'
            GTBStandardTime = 'GTB Standard Time'
            HaitiStandardTime = 'Haiti Standard Time'
            HawaiianStandardTime = 'Hawaiian Standard Time'
            IndiaStandardTime = 'India Standard Time'
            IranStandardTime = 'Iran Standard Time'
            IsraelStandardTime = 'Israel Standard Time'
            JordanStandardTime = 'Jordan Standard Time'
            KaliningradStandardTime = 'Kaliningrad Standard Time'
            KamchatkaStandardTime = 'Kamchatka Standard Time'
            KoreaStandardTime = 'Korea Standard Time'
            LibyaStandardTime = 'Libya Standard Time'
            LineIslandsStandardTime = 'Line Islands Standard Time'
            LordHoweStandardTime = 'Lord Howe Standard Time'
            MagadanStandardTime = 'Magadan Standard Time'
            MagallanesStandardTime = 'Magallanes Standard Time'
            MarquesasStandardTime = 'Marquesas Standard Time'
            MauritiusStandardTime = 'Mauritius Standard Time'
            MidAtlanticStandardTime = 'Mid-Atlantic Standard Time'
            MiddleEastStandardTime = 'Middle East Standard Time'
            MontevideoStandardTime = 'Montevideo Standard Time'
            MoroccoStandardTime = 'Morocco Standard Time'
            MountainStandardTime = 'Mountain Standard Time'
            MountainStandardTime_Mexico = 'Mountain Standard Time (Mexico)'
            MyanmarStandardTime = 'Myanmar Standard Time'
            N_CentralAsiaStandardTime = 'N. Central Asia Standard Time'
            NamibiaStandardTime = 'Namibia Standard Time'
            NepalStandardTime = 'Nepal Standard Time'
            NewZealandStandardTime = 'New Zealand Standard Time'
            NewfoundlandStandardTime = 'Newfoundland Standard Time'
            NorfolkStandardTime = 'Norfolk Standard Time'
            NorthAsiaEastStandardTime = 'North Asia East Standard Time'
            NorthAsiaStandardTime = 'North Asia Standard Time'
            NorthKoreaStandardTime = 'North Korea Standard Time'
            OmskStandardTime = 'Omsk Standard Time'
            PacificSAStandardTime = 'Pacific SA Standard Time'
            PacificStandardTime = 'Pacific Standard Time'
            PacificStandardTimeMexico = 'Pacific Standard Time (Mexico)'
            PakistanStandardTime = 'Pakistan Standard Time'
            ParaguayStandardTime = 'Paraguay Standard Time'
            RomanceStandardTime = 'Romance Standard Time'
            RussiaTimeZone10 = 'Russia Time Zone 10'
            RussiaTimeZone11 = 'Russia Time Zone 11'
            RussiaTimeZone3 = 'Russia Time Zone 3'
            RussianStandardTime = 'Russian Standard Time'
            SAEasternStandardTime = 'SA Eastern Standard Time'
            SAPacificStandardTime = 'SA Pacific Standard Time'
            SAWesternStandardTime = 'SA Western Standard Time'
            SaintPierreStandardTime = 'Saint Pierre Standard Time'
            SakhalinStandardTime = 'Sakhalin Standard Time'
            SamoaStandardTime = 'Samoa Standard Time'
            SaratovStandardTime = 'Saratov Standard Time'
            SEAsiaStandardTime = 'SE Asia Standard Time'
            SingaporeStandardTime = 'Singapore Standard Time'
            SouthAfricaStandardTime = 'South Africa Standard Time'
            SriLankaStandardTime = 'Sri Lanka Standard Time'
            SudanStandardTime = 'Sudan Standard Time'
            SyriaStandardTime = 'Syria Standard Time'
            TaipeiStandardTime = 'Taipei Standard Time'
            TasmaniaStandardTime = 'Tasmania Standard Time'
            TocantinsStandardTime = 'Tocantins Standard Time'
            TokyoStandardTime = 'Tokyo Standard Time'
            TomskStandardTime = 'Tomsk Standard Time'
            TongaStandardTime = 'Tonga Standard Time'
            TransbaikalStandardTime = 'Transbaikal Standard Time'
            TurkeyStandardTime = 'Turkey Standard Time'
            TurksAndCaicosStandardTime = 'Turks And Caicos Standard Time'
            UlaanbaatarStandardTime = 'Ulaanbaatar Standard Time'
            USEasternStandardTime = 'US Eastern Standard Time'
            USMountainStandardTime = 'US Mountain Standard Time'
            UTC = 'UTC'
            UTCPLUS12 = 'UTC+12'
            UTCPLUS13 = 'UTC+13'
            UTCMINUS02 = 'UTC-02'
            UTCMINUS08 = 'UTC-08'
            UTCMINUS09 = 'UTC-09'
            UTCMINUS11 = 'UTC-11'
            VenezuelaStandardTime = 'Venezuela Standard Time'
            VladivostokStandardTime = 'Vladivostok Standard Time'
            W_AustraliaStandardTime = 'W. Australia Standard Time'
            W_CentralAfricaStandardTime = 'W. Central Africa Standard Time'
            W_EuropeStandardTime = 'W. Europe Standard Time'
            W_MongoliaStandardTime = 'W. Mongolia Standard Time'
            WestAsiaStandardTime = 'West Asia Standard Time'
            WestBankStandardTime = 'West Bank Standard Time'
            WestPacificStandardTime = 'West Pacific Standard Time'
            YakutskStandardTime = 'Yakutsk Standard Time'
        
        class RecurrenceType:
            Daily = 'daily'
            Weekday = 'weekday'
            Weekly = 'weekly'
            Monthly = 'monthly'
            Yearly = 'yearly'
        
        class ResponseType:
            None_ = 'none'
            Organizer = 'organizer'
            Tentative = 'tentative'
            Accepted = 'accepted'
            Declined = 'declined'
        
        class RestVersion:
            v1_0 = 'v1.0'
            v2_0 = 'v2.0'
            Beta = 'beta'
        
        class SaveLocation:
            AccountDocument = 0
            Box = 1
            Dropbox = 2
            GoogleDrive = 3
            Local = 4
            OnedriveForBusiness = 5
            Other = 6
            PhotoLibrary = 7
            SharePoint = 8
        
        class SendModeOverride:
            PromptUser = 'promptUser'
        
        class SourceProperty:
            Body = 'body'
            Subject = 'subject'
        
        class WeekNumber:
            First = 'first'
            Second = 'second'
            Third = 'third'
            Fourth = 'fourth'
            Last = 'last'

class OfficeExtension:
    
    class ClientObject:
        pass
    
    class LoadOption:
        pass
    
    class UpdateOptions:
        pass
    
    class RunOptions:
        pass
    
    class RequestContextDebugInfo:
        pass
    
    class ClientRequestContext:
        pass
    
    class EmbeddedOptions:
        pass
    
    class EmbeddedSession:
        pass
    
    class ClientResult:
        pass
    
    class DebugInfo:
        pass
    
    class Error:
        pass
    
    class ErrorCodes:
        pass
    
    class TrackedObjects:
        pass
    
    class EventHandlers:
        pass
    
    class EventHandlerResult:
        pass
    
    class EventInfo:
        pass
    
    class RequestUrlAndHeaderInfo:
        pass

class OfficeCore:
    
    class RequestContext:
        pass

class Excel:
    
    class BlockedErrorCellValueSubType:
        unknown = 'Unknown'
        dataTypeRestrictedDomain = 'DataTypeRestrictedDomain'
        dataTypePrivacySetting = 'DataTypePrivacySetting'
        dataTypeUnsupportedApp = 'DataTypeUnsupportedApp'
        externalLinksGeneric = 'ExternalLinksGeneric'
        richDataLinkDisabled = 'RichDataLinkDisabled'
        signInError = 'SignInError'
        noLicense = 'NoLicense'
    
    class BusyErrorCellValueSubType:
        unknown = 'Unknown'
        externalLinksGeneric = 'ExternalLinksGeneric'
        loadingImage = 'LoadingImage'
    
    class CalcErrorCellValueSubType:
        unknown = 'Unknown'
        arrayOfArrays = 'ArrayOfArrays'
        arrayOfRanges = 'ArrayOfRanges'
        emptyArray = 'EmptyArray'
        unsupportedLifting = 'UnsupportedLifting'
        dataTableReferencedPendingFormula = 'DataTableReferencedPendingFormula'
        tooManyCells = 'TooManyCells'
        lambdaInCell = 'LambdaInCell'
        tooDeeplyNested = 'TooDeeplyNested'
        textOverflow = 'TextOverflow'
    
    class EntityCardLayoutType:
        entity = 'Entity'
    
    class FunctionCellValueType:
        javaScriptReference = 'JavaScriptReference'
    
    class EntityCompactLayoutIcons:
        generic = 'Generic'
        accessibility = 'Accessibility'
        airplane = 'Airplane'
        airplaneTakeOff = 'AirplaneTakeOff'
        album = 'Album'
        alert = 'Alert'
        alertUrgent = 'AlertUrgent'
        animal = 'Animal'
        animalCat = 'AnimalCat'
        animalDog = 'AnimalDog'
        animalRabbit = 'AnimalRabbit'
        animalTurtle = 'AnimalTurtle'
        appFolder = 'AppFolder'
        appGeneric = 'AppGeneric'
        apple = 'Apple'
        approvalsApp = 'ApprovalsApp'
        archive = 'Archive'
        archiveMultiple = 'ArchiveMultiple'
        arrowTrendingLines = 'ArrowTrendingLines'
        art = 'Art'
        atom = 'Atom'
        attach = 'Attach'
        automobile = 'Automobile'
        autosum = 'Autosum'
        backpack = 'Backpack'
        badge = 'Badge'
        balloon = 'Balloon'
        bank = 'Bank'
        barcodeScanner = 'BarcodeScanner'
        basketball = 'Basketball'
        battery0 = 'Battery0'
        battery10 = 'Battery10'
        beach = 'Beach'
        beaker = 'Beaker'
        bed = 'Bed'
        binFull = 'BinFull'
        bird = 'Bird'
        bluetooth = 'Bluetooth'
        board = 'Board'
        boardGames = 'BoardGames'
        book = 'Book'
        bookmark = 'Bookmark'
        bookmarkMultiple = 'BookmarkMultiple'
        bot = 'Bot'
        bowlChopsticks = 'BowlChopsticks'
        box = 'Box'
        boxMultiple = 'BoxMultiple'
        brainCircuit = 'BrainCircuit'
        branch = 'Branch'
        branchFork = 'BranchFork'
        branchRequest = 'BranchRequest'
        bridge = 'Bridge'
        briefcase = 'Briefcase'
        briefcaseMedical = 'BriefcaseMedical'
        broadActivityFeed = 'BroadActivityFeed'
        broom = 'Broom'
        bug = 'Bug'
        building = 'Building'
        buildingBank = 'BuildingBank'
        buildingFactory = 'BuildingFactory'
        buildingGovernment = 'BuildingGovernment'
        buildingHome = 'BuildingHome'
        buildingLighthouse = 'BuildingLighthouse'
        buildingMultiple = 'BuildingMultiple'
        buildingRetail = 'BuildingRetail'
        buildingRetailMore = 'BuildingRetailMore'
        buildingRetailToolbox = 'BuildingRetailToolbox'
        buildingShop = 'BuildingShop'
        buildingSkyscraper = 'BuildingSkyscraper'
        calculator = 'Calculator'
        calendarLtr = 'CalendarLtr'
        calendarRtl = 'CalendarRtl'
        call = 'Call'
        calligraphyPen = 'CalligraphyPen'
        camera = 'Camera'
        cameraDome = 'CameraDome'
        car = 'Car'
        cart = 'Cart'
        cat = 'Cat'
        certificate = 'Certificate'
        chartMultiple = 'ChartMultiple'
        chat = 'Chat'
        chatMultiple = 'ChatMultiple'
        chatVideo = 'ChatVideo'
        check = 'Check'
        checkboxChecked = 'CheckboxChecked'
        checkboxUnchecked = 'CheckboxUnchecked'
        checkmark = 'Checkmark'
        chess = 'Chess'
        city = 'City'
        class_ = 'Class'
        classification = 'Classification'
        clipboard = 'Clipboard'
        clipboardDataBar = 'ClipboardDataBar'
        clipboardPulse = 'ClipboardPulse'
        clipboardTask = 'ClipboardTask'
        clock = 'Clock'
        clockAlarm = 'ClockAlarm'
        cloud = 'Cloud'
        cloudWords = 'CloudWords'
        code = 'Code'
        collections = 'Collections'
        comment = 'Comment'
        commentMultiple = 'CommentMultiple'
        communication = 'Communication'
        compassNorthwest = 'CompassNorthwest'
        conferenceRoom = 'ConferenceRoom'
        connector = 'Connector'
        constellation = 'Constellation'
        contactCard = 'ContactCard'
        cookies = 'Cookies'
        couch = 'Couch'
        creditCardPerson = 'CreditCardPerson'
        creditCardToolbox = 'CreditCardToolbox'
        cube = 'Cube'
        cubeMultiple = 'CubeMultiple'
        cubeTree = 'CubeTree'
        currencyDollarEuro = 'CurrencyDollarEuro'
        currencyDollarRupee = 'CurrencyDollarRupee'
        dataArea = 'DataArea'
        database = 'Database'
        databaseMultiple = 'DatabaseMultiple'
        dataFunnel = 'DataFunnel'
        dataHistogram = 'DataHistogram'
        dataLine = 'DataLine'
        dataPie = 'DataPie'
        dataScatter = 'DataScatter'
        dataSunburst = 'DataSunburst'
        dataTreemap = 'DataTreemap'
        dataWaterfall = 'DataWaterfall'
        dataWhisker = 'DataWhisker'
        dentist = 'Dentist'
        designIdeas = 'DesignIdeas'
        desktop = 'Desktop'
        desktopMac = 'DesktopMac'
        developerBoard = 'DeveloperBoard'
        deviceMeetingRoom = 'DeviceMeetingRoom'
        diagram = 'Diagram'
        dialpad = 'Dialpad'
        diamond = 'Diamond'
        dinosaur = 'Dinosaur'
        directions = 'Directions'
        disaster = 'Disaster'
        diversity = 'Diversity'
        dNA = 'DNA'
        doctor = 'Doctor'
        document = 'Document'
        documentData = 'DocumentData'
        documentLandscape = 'DocumentLandscape'
        documentMultiple = 'DocumentMultiple'
        documentPdf = 'DocumentPdf'
        documentQueue = 'DocumentQueue'
        documentText = 'DocumentText'
        dog = 'Dog'
        door = 'Door'
        doorTag = 'DoorTag'
        drafts = 'Drafts'
        drama = 'Drama'
        drinkBeer = 'DrinkBeer'
        drinkCoffee = 'DrinkCoffee'
        drinkMargarita = 'DrinkMargarita'
        drinkToGo = 'DrinkToGo'
        drinkWine = 'DrinkWine'
        driveTrain = 'DriveTrain'
        drop = 'Drop'
        dualScreen = 'DualScreen'
        dumbbell = 'Dumbbell'
        earth = 'Earth'
        emoji = 'Emoji'
        emojiAngry = 'EmojiAngry'
        emojiHand = 'EmojiHand'
        emojiLaugh = 'EmojiLaugh'
        emojiMeh = 'EmojiMeh'
        emojiMultiple = 'EmojiMultiple'
        emojiSad = 'EmojiSad'
        emojiSadSlight = 'EmojiSadSlight'
        emojiSmileSlight = 'EmojiSmileSlight'
        emojiSparkle = 'EmojiSparkle'
        emojiSurprise = 'EmojiSurprise'
        engine = 'Engine'
        eraser = 'Eraser'
        eye = 'Eye'
        eyedropper = 'Eyedropper'
        fax = 'Fax'
        fingerprint = 'Fingerprint'
        firstAid = 'FirstAid'
        flag = 'Flag'
        flash = 'Flash'
        flashlight = 'Flashlight'
        flow = 'Flow'
        flowchart = 'Flowchart'
        folder = 'Folder'
        folderOpen = 'FolderOpen'
        folderOpenVertical = 'FolderOpenVertical'
        folderPerson = 'FolderPerson'
        folderZip = 'FolderZip'
        food = 'Food'
        foodApple = 'FoodApple'
        foodCake = 'FoodCake'
        foodEgg = 'FoodEgg'
        foodGrains = 'FoodGrains'
        foodPizza = 'FoodPizza'
        foodToast = 'FoodToast'
        galaxy = 'Galaxy'
        games = 'Games'
        ganttChart = 'GanttChart'
        gas = 'Gas'
        gasPump = 'GasPump'
        gauge = 'Gauge'
        gavel = 'Gavel'
        gift = 'Gift'
        giftCard = 'GiftCard'
        glasses = 'Glasses'
        globe = 'Globe'
        globeSurface = 'GlobeSurface'
        grid = 'Grid'
        gridDots = 'GridDots'
        gridKanban = 'GridKanban'
        guardian = 'Guardian'
        guest = 'Guest'
        guitar = 'Guitar'
        handLeft = 'HandLeft'
        handRight = 'HandRight'
        handshake = 'Handshake'
        hardDrive = 'HardDrive'
        hatGraduation = 'HatGraduation'
        headphones = 'Headphones'
        headphonesSoundWave = 'HeadphonesSoundWave'
        headset = 'Headset'
        headsetVr = 'HeadsetVr'
        heart = 'Heart'
        heartBroken = 'HeartBroken'
        heartCircle = 'HeartCircle'
        heartHuman = 'HeartHuman'
        heartPulse = 'HeartPulse'
        history = 'History'
        home = 'Home'
        homeMore = 'HomeMore'
        homePerson = 'HomePerson'
        icons = 'Icons'
        image = 'Image'
        imageGlobe = 'ImageGlobe'
        imageMultiple = 'ImageMultiple'
        iot = 'Iot'
        joystick = 'Joystick'
        justice = 'Justice'
        key = 'Key'
        keyboard = 'Keyboard'
        keyboardLayoutSplit = 'KeyboardLayoutSplit'
        keyMultiple = 'KeyMultiple'
        languages = 'Languages'
        laptop = 'Laptop'
        lasso = 'Lasso'
        launcherSettings = 'LauncherSettings'
        layer = 'Layer'
        leaf = 'Leaf'
        leafOne = 'LeafOne'
        leafThree = 'LeafThree'
        leafTwo = 'LeafTwo'
        library = 'Library'
        lightbulb = 'Lightbulb'
        lightbulbFilament = 'LightbulbFilament'
        likert = 'Likert'
        link = 'Link'
        localLanguage = 'LocalLanguage'
        location = 'Location'
        lockClosed = 'LockClosed'
        lockMultiple = 'LockMultiple'
        lockOpen = 'LockOpen'
        lottery = 'Lottery'
        luggage = 'Luggage'
        mail = 'Mail'
        mailInbox = 'MailInbox'
        mailMultiple = 'MailMultiple'
        map = 'Map'
        mapPin = 'MapPin'
        markdown = 'Markdown'
        mathFormula = 'MathFormula'
        mathSymbols = 'MathSymbols'
        max = 'Max'
        megaphone = 'Megaphone'
        megaphoneLoud = 'MegaphoneLoud'
        mention = 'Mention'
        mic = 'Mic'
        microscope = 'Microscope'
        midi = 'Midi'
        molecule = 'Molecule'
        money = 'Money'
        moneyHand = 'MoneyHand'
        mountain = 'Mountain'
        movieCamera = 'MovieCamera'
        moviesAndTv = 'MoviesAndTv'
        musicNote = 'MusicNote'
        musicNote1 = 'MusicNote1'
        musicNote2 = 'MusicNote2'
        myLocation = 'MyLocation'
        nByN = 'NByN'
        nByOne = 'NByOne'
        news = 'News'
        notablePeople = 'NotablePeople'
        note = 'Note'
        notebook = 'Notebook'
        notepad = 'Notepad'
        notepadPerson = 'NotepadPerson'
        oneByN = 'OneByN'
        oneByOne = 'OneByOne'
        options = 'Options'
        organization = 'Organization'
        organizationHorizontal = 'OrganizationHorizontal'
        oval = 'Oval'
        paintBrush = 'PaintBrush'
        paintBucket = 'PaintBucket'
        partlySunnyWeather = 'PartlySunnyWeather'
        password = 'Password'
        patch = 'Patch'
        patient = 'Patient'
        payment = 'Payment'
        pen = 'Pen'
        pentagon = 'Pentagon'
        people = 'People'
        peopleAudience = 'PeopleAudience'
        peopleCall = 'PeopleCall'
        peopleCommunity = 'PeopleCommunity'
        peopleMoney = 'PeopleMoney'
        peopleQueue = 'PeopleQueue'
        peopleTeam = 'PeopleTeam'
        peopleToolbox = 'PeopleToolbox'
        person = 'Person'
        personBoard = 'PersonBoard'
        personCall = 'PersonCall'
        personChat = 'PersonChat'
        personFeedback = 'PersonFeedback'
        personSupport = 'PersonSupport'
        personVoice = 'PersonVoice'
        phone = 'Phone'
        phoneDesktop = 'PhoneDesktop'
        phoneLaptop = 'PhoneLaptop'
        phoneShake = 'PhoneShake'
        phoneTablet = 'PhoneTablet'
        phoneVibrate = 'PhoneVibrate'
        photoFilter = 'PhotoFilter'
        pi = 'Pi'
        pictureInPicture = 'PictureInPicture'
        pilates = 'Pilates'
        pill = 'Pill'
        pin = 'Pin'
        pipeline = 'Pipeline'
        planet = 'Planet'
        playingCards = 'PlayingCards'
        plugConnected = 'PlugConnected'
        plugDisconnected = 'PlugDisconnected'
        pointScan = 'PointScan'
        poll = 'Poll'
        power = 'Power'
        predictions = 'Predictions'
        premium = 'Premium'
        presenter = 'Presenter'
        previewLink = 'PreviewLink'
        print = 'Print'
        production = 'Production'
        prohibited = 'Prohibited'
        projectionScreen = 'ProjectionScreen'
        protocolHandler = 'ProtocolHandler'
        pulse = 'Pulse'
        pulseSquare = 'PulseSquare'
        puzzlePiece = 'PuzzlePiece'
        qrCode = 'QrCode'
        radar = 'Radar'
        ram = 'Ram'
        readingList = 'ReadingList'
        realEstate = 'RealEstate'
        receipt = 'Receipt'
        reward = 'Reward'
        rhombus = 'Rhombus'
        ribbon = 'Ribbon'
        ribbonStar = 'RibbonStar'
        roadCone = 'RoadCone'
        rocket = 'Rocket'
        router = 'Router'
        rss = 'Rss'
        ruler = 'Ruler'
        run = 'Run'
        running = 'Running'
        satellite = 'Satellite'
        save = 'Save'
        savings = 'Savings'
        scales = 'Scales'
        scan = 'Scan'
        scratchpad = 'Scratchpad'
        screenPerson = 'ScreenPerson'
        screenshot = 'Screenshot'
        search = 'Search'
        serialPort = 'SerialPort'
        server = 'Server'
        serverMultiple = 'ServerMultiple'
        serviceBell = 'ServiceBell'
        settings = 'Settings'
        shapes = 'Shapes'
        shield = 'Shield'
        shieldTask = 'ShieldTask'
        shoppingBag = 'ShoppingBag'
        signature = 'Signature'
        sim = 'Sim'
        sleep = 'Sleep'
        smartwatch = 'Smartwatch'
        soundSource = 'SoundSource'
        soundWaveCircle = 'SoundWaveCircle'
        sparkle = 'Sparkle'
        speaker0 = 'Speaker0'
        speaker2 = 'Speaker2'
        sport = 'Sport'
        sportAmericanFootball = 'SportAmericanFootball'
        sportBaseball = 'SportBaseball'
        sportBasketball = 'SportBasketball'
        sportHockey = 'SportHockey'
        sportSoccer = 'SportSoccer'
        squareMultiple = 'SquareMultiple'
        squareShadow = 'SquareShadow'
        squaresNested = 'SquaresNested'
        stack = 'Stack'
        stackStar = 'StackStar'
        star = 'Star'
        starFilled = 'StarFilled'
        starHalf = 'StarHalf'
        starLineHorizontal3 = 'StarLineHorizontal3'
        starOneQuarter = 'StarOneQuarter'
        starThreeQuarter = 'StarThreeQuarter'
        status = 'Status'
        steps = 'Steps'
        stethoscope = 'Stethoscope'
        sticker = 'Sticker'
        storage = 'Storage'
        stream = 'Stream'
        streamInput = 'StreamInput'
        streamInputOutput = 'StreamInputOutput'
        streamOutput = 'StreamOutput'
        styleGuide = 'StyleGuide'
        subGrid = 'SubGrid'
        subtitles = 'Subtitles'
        surfaceEarbuds = 'SurfaceEarbuds'
        surfaceHub = 'SurfaceHub'
        symbols = 'Symbols'
        syringe = 'Syringe'
        system = 'System'
        tabDesktop = 'TabDesktop'
        tabInprivateAccount = 'TabInprivateAccount'
        table = 'Table'
        tableImage = 'TableImage'
        tableMultiple = 'TableMultiple'
        tablet = 'Tablet'
        tabs = 'Tabs'
        tag = 'Tag'
        tagCircle = 'TagCircle'
        tagMultiple = 'TagMultiple'
        target = 'Target'
        targetArrow = 'TargetArrow'
        teddy = 'Teddy'
        temperature = 'Temperature'
        tent = 'Tent'
        tetrisApp = 'TetrisApp'
        textbox = 'Textbox'
        textQuote = 'TextQuote'
        thinking = 'Thinking'
        thumbDislike = 'ThumbDislike'
        thumbLike = 'ThumbLike'
        ticketDiagonal = 'TicketDiagonal'
        ticketHorizontal = 'TicketHorizontal'
        timeAndWeather = 'TimeAndWeather'
        timeline = 'Timeline'
        timer = 'Timer'
        toolbox = 'Toolbox'
        topSpeed = 'TopSpeed'
        translate = 'Translate'
        transmission = 'Transmission'
        treeDeciduous = 'TreeDeciduous'
        treeEvergreen = 'TreeEvergreen'
        trophy = 'Trophy'
        tv = 'Tv'
        tvUsb = 'TvUsb'
        umbrella = 'Umbrella'
        usbPlug = 'UsbPlug'
        usbStick = 'UsbStick'
        vault = 'Vault'
        vehicleBicycle = 'VehicleBicycle'
        vehicleBus = 'VehicleBus'
        vehicleCab = 'VehicleCab'
        vehicleCar = 'VehicleCar'
        vehicleCarCollision = 'VehicleCarCollision'
        vehicleCarProfileLtr = 'VehicleCarProfileLtr'
        vehicleCarProfileRtl = 'VehicleCarProfileRtl'
        vehicleShip = 'VehicleShip'
        vehicleSubway = 'VehicleSubway'
        vehicleTruck = 'VehicleTruck'
        vehicleTruckBag = 'VehicleTruckBag'
        vehicleTruckCube = 'VehicleTruckCube'
        vehicleTruckProfile = 'VehicleTruckProfile'
        video = 'Video'
        video360 = 'Video360'
        videoChat = 'VideoChat'
        videoClip = 'VideoClip'
        videoClipMultiple = 'VideoClipMultiple'
        videoPerson = 'VideoPerson'
        videoRecording = 'VideoRecording'
        videoSecurity = 'VideoSecurity'
        viewDesktop = 'ViewDesktop'
        viewDesktopMobile = 'ViewDesktopMobile'
        violin = 'Violin'
        virtualNetwork = 'VirtualNetwork'
        voicemail = 'Voicemail'
        vote = 'Vote'
        walkieTalkie = 'WalkieTalkie'
        wallet = 'Wallet'
        walletCreditCard = 'WalletCreditCard'
        wallpaper = 'Wallpaper'
        wand = 'Wand'
        warning = 'Warning'
        weatherBlowingSnow = 'WeatherBlowingSnow'
        weatherCloudy = 'WeatherCloudy'
        weatherDrizzle = 'WeatherDrizzle'
        weatherDuststorm = 'WeatherDuststorm'
        weatherFog = 'WeatherFog'
        weatherHailDay = 'WeatherHailDay'
        weatherHailNight = 'WeatherHailNight'
        weatherHaze = 'WeatherHaze'
        weatherMoon = 'WeatherMoon'
        weatherPartlyCloudyDay = 'WeatherPartlyCloudyDay'
        weatherPartlyCloudyNight = 'WeatherPartlyCloudyNight'
        weatherRain = 'WeatherRain'
        weatherRainShowersDay = 'WeatherRainShowersDay'
        weatherRainShowersNight = 'WeatherRainShowersNight'
        weatherRainSnow = 'WeatherRainSnow'
        weatherSnow = 'WeatherSnow'
        weatherSnowflake = 'WeatherSnowflake'
        weatherSnowShowerDay = 'WeatherSnowShowerDay'
        weatherSnowShowerNight = 'WeatherSnowShowerNight'
        weatherSqualls = 'WeatherSqualls'
        weatherSunnyHigh = 'WeatherSunnyHigh'
        weatherSunnyLow = 'WeatherSunnyLow'
        weatherThunderstorm = 'WeatherThunderstorm'
        webAsset = 'WebAsset'
        whiteboard = 'Whiteboard'
        wifi1 = 'Wifi1'
        wifi2 = 'Wifi2'
        window = 'Window'
        windowMultiple = 'WindowMultiple'
        windowWrench = 'WindowWrench'
        wrench = 'Wrench'
        wrenchScrewdriver = 'WrenchScrewdriver'
        xray = 'Xray'
        yoga = 'Yoga'
    
    class ReferenceValueType:
        array = 'Array'
        entity = 'Entity'
        root = 'Root'
        double = 'Double'
        string = 'String'
        boolean = 'Boolean'
    
    class CellValueType:
        array = 'Array'
        boolean = 'Boolean'
        double = 'Double'
        entity = 'Entity'
        empty = 'Empty'
        error = 'Error'
        formattedNumber = 'FormattedNumber'
        function = 'Function'
        linkedEntity = 'LinkedEntity'
        reference = 'Reference'
        string = 'String'
        notAvailable = 'NotAvailable'
        webImage = 'WebImage'
    
    class ConnectErrorCellValueSubType:
        unknown = 'Unknown'
        serviceError = 'ServiceError'
        externalLinks = 'ExternalLinks'
        externalLinksNonCloudLocation = 'ExternalLinksNonCloudLocation'
        dataTypeNoConnection = 'DataTypeNoConnection'
        dataTypeServiceError = 'DataTypeServiceError'
        missingContent = 'MissingContent'
        requestThrottle = 'RequestThrottle'
        externalLinksFailedToRefresh = 'ExternalLinksFailedToRefresh'
        externalLinksAccessFailed = 'ExternalLinksAccessFailed'
        externalLinksServerError = 'ExternalLinksServerError'
        externalLinksInvalidRequest = 'ExternalLinksInvalidRequest'
        externalLinksUnAuthenticated = 'ExternalLinksUnAuthenticated'
        externalLinksThrottledByHost = 'ExternalLinksThrottledByHost'
        externalLinksFileTooLarge = 'ExternalLinksFileTooLarge'
        outdatedLinkedEntity = 'OutdatedLinkedEntity'
        genericServerError = 'GenericServerError'
    
    class ErrorCellValueType:
        blocked = 'Blocked'
        busy = 'Busy'
        calc = 'Calc'
        connect = 'Connect'
        div0 = 'Div0'
        external = 'External'
        field = 'Field'
        gettingData = 'GettingData'
        notAvailable = 'NotAvailable'
        name = 'Name'
        null = 'Null'
        num = 'Num'
        placeholder = 'Placeholder'
        ref = 'Ref'
        spill = 'Spill'
        value = 'Value'
    
    class ExternalErrorCellValueSubType:
        unknown = 'Unknown'
    
    class FieldErrorCellValueSubType:
        unknown = 'Unknown'
        webImageMissingFilePart = 'WebImageMissingFilePart'
        dataProviderError = 'DataProviderError'
        richValueRelMissingFilePart = 'RichValueRelMissingFilePart'
    
    class NumErrorCellValueSubType:
        unknown = 'Unknown'
        arrayTooLarge = 'ArrayTooLarge'
    
    class RefErrorCellValueSubType:
        unknown = 'Unknown'
        externalLinksStructuredRef = 'ExternalLinksStructuredRef'
        externalLinksCalculatedRef = 'ExternalLinksCalculatedRef'
    
    class SpillErrorCellValueSubType:
        unknown = 'Unknown'
        collision = 'Collision'
        indeterminateSize = 'IndeterminateSize'
        worksheetEdge = 'WorksheetEdge'
        outOfMemoryWhileCalc = 'OutOfMemoryWhileCalc'
        table = 'Table'
        mergedCell = 'MergedCell'
    
    class ValueErrorCellValueSubType:
        unknown = 'Unknown'
        vlookupColumnIndexLessThanOne = 'VlookupColumnIndexLessThanOne'
        vlookupResultNotFound = 'VlookupResultNotFound'
        hlookupRowIndexLessThanOne = 'HlookupRowIndexLessThanOne'
        hlookupResultNotFound = 'HlookupResultNotFound'
        coerceStringToNumberInvalid = 'CoerceStringToNumberInvalid'
        coerceStringToBoolInvalid = 'CoerceStringToBoolInvalid'
        coerceStringToInvalidType = 'CoerceStringToInvalidType'
        subArrayStartRowMissingEndRowNot = 'SubArrayStartRowMissingEndRowNot'
        subArrayStartColumnMissingEndColumnNot = 'SubArrayStartColumnMissingEndColumnNot'
        invalidImageUrl = 'InvalidImageUrl'
        stockHistoryNonTradingDays = 'StockHistoryNonTradingDays'
        stockHistoryNotAStock = 'StockHistoryNotAStock'
        stockHistoryInvalidDate = 'StockHistoryInvalidDate'
        stockHistoryEndBeforeStart = 'StockHistoryEndBeforeStart'
        stockHistoryStartInFuture = 'StockHistoryStartInFuture'
        stockHistoryInvalidEnum = 'StockHistoryInvalidEnum'
        stockHistoryOnlyDateRequested = 'StockHistoryOnlyDateRequested'
        stockHistoryNotFound = 'StockHistoryNotFound'
        lambdaWrongParamCount = 'LambdaWrongParamCount'
    
    class LoadToType:
        connectionOnly = 'ConnectionOnly'
        table = 'Table'
        pivotTable = 'PivotTable'
        pivotChart = 'PivotChart'
    
    class QueryError:
        unknown = 'Unknown'
        none = 'None'
        failedLoadToWorksheet = 'FailedLoadToWorksheet'
        failedLoadToDataModel = 'FailedLoadToDataModel'
        failedDownload = 'FailedDownload'
        failedToCompleteDownload = 'FailedToCompleteDownload'
    
    class WorkbookLinksRefreshMode:
        manual = 'Manual'
        automatic = 'Automatic'
    
    class DataSourceType:
        unknown = 'Unknown'
        localRange = 'LocalRange'
        localTable = 'LocalTable'
    
    class DateFilterCondition:
        unknown = 'Unknown'
        equals = 'Equals'
        before = 'Before'
        beforeOrEqualTo = 'BeforeOrEqualTo'
        after = 'After'
        afterOrEqualTo = 'AfterOrEqualTo'
        between = 'Between'
        tomorrow = 'Tomorrow'
        today = 'Today'
        yesterday = 'Yesterday'
        nextWeek = 'NextWeek'
        thisWeek = 'ThisWeek'
        lastWeek = 'LastWeek'
        nextMonth = 'NextMonth'
        thisMonth = 'ThisMonth'
        lastMonth = 'LastMonth'
        nextQuarter = 'NextQuarter'
        thisQuarter = 'ThisQuarter'
        lastQuarter = 'LastQuarter'
        nextYear = 'NextYear'
        thisYear = 'ThisYear'
        lastYear = 'LastYear'
        yearToDate = 'YearToDate'
        allDatesInPeriodQuarter1 = 'AllDatesInPeriodQuarter1'
        allDatesInPeriodQuarter2 = 'AllDatesInPeriodQuarter2'
        allDatesInPeriodQuarter3 = 'AllDatesInPeriodQuarter3'
        allDatesInPeriodQuarter4 = 'AllDatesInPeriodQuarter4'
        allDatesInPeriodJanuary = 'AllDatesInPeriodJanuary'
        allDatesInPeriodFebruary = 'AllDatesInPeriodFebruary'
        allDatesInPeriodMarch = 'AllDatesInPeriodMarch'
        allDatesInPeriodApril = 'AllDatesInPeriodApril'
        allDatesInPeriodMay = 'AllDatesInPeriodMay'
        allDatesInPeriodJune = 'AllDatesInPeriodJune'
        allDatesInPeriodJuly = 'AllDatesInPeriodJuly'
        allDatesInPeriodAugust = 'AllDatesInPeriodAugust'
        allDatesInPeriodSeptember = 'AllDatesInPeriodSeptember'
        allDatesInPeriodOctober = 'AllDatesInPeriodOctober'
        allDatesInPeriodNovember = 'AllDatesInPeriodNovember'
        allDatesInPeriodDecember = 'AllDatesInPeriodDecember'
    
    class LabelFilterCondition:
        unknown = 'Unknown'
        equals = 'Equals'
        beginsWith = 'BeginsWith'
        endsWith = 'EndsWith'
        contains = 'Contains'
        greaterThan = 'GreaterThan'
        greaterThanOrEqualTo = 'GreaterThanOrEqualTo'
        lessThan = 'LessThan'
        lessThanOrEqualTo = 'LessThanOrEqualTo'
        between = 'Between'
    
    class PivotFilterType:
        unknown = 'Unknown'
        value = 'Value'
        manual = 'Manual'
        label = 'Label'
        date = 'Date'
    
    class TopBottomSelectionType:
        items = 'Items'
        percent = 'Percent'
        sum = 'Sum'
    
    class ValueFilterCondition:
        unknown = 'Unknown'
        equals = 'Equals'
        greaterThan = 'GreaterThan'
        greaterThanOrEqualTo = 'GreaterThanOrEqualTo'
        lessThan = 'LessThan'
        lessThanOrEqualTo = 'LessThanOrEqualTo'
        between = 'Between'
        topN = 'TopN'
        bottomN = 'BottomN'
    
    class ChartSeriesDimension:
        categories = 'Categories'
        values = 'Values'
        xvalues = 'XValues'
        yvalues = 'YValues'
        bubbleSizes = 'BubbleSizes'
    
    class CellControlType:
        unknown = 'Unknown'
        empty = 'Empty'
        mixed = 'Mixed'
        checkbox = 'Checkbox'
    
    class PivotFilterTopBottomCriterion:
        invalid = 'Invalid'
        topItems = 'TopItems'
        topPercent = 'TopPercent'
        topSum = 'TopSum'
        bottomItems = 'BottomItems'
        bottomPercent = 'BottomPercent'
        bottomSum = 'BottomSum'
    
    class SortBy:
        ascending = 'Ascending'
        descending = 'Descending'
    
    class AggregationFunction:
        unknown = 'Unknown'
        automatic = 'Automatic'
        sum = 'Sum'
        count = 'Count'
        average = 'Average'
        max = 'Max'
        min = 'Min'
        product = 'Product'
        countNumbers = 'CountNumbers'
        standardDeviation = 'StandardDeviation'
        standardDeviationP = 'StandardDeviationP'
        variance = 'Variance'
        varianceP = 'VarianceP'
    
    class ShowAsCalculation:
        unknown = 'Unknown'
        none = 'None'
        percentOfGrandTotal = 'PercentOfGrandTotal'
        percentOfRowTotal = 'PercentOfRowTotal'
        percentOfColumnTotal = 'PercentOfColumnTotal'
        percentOfParentRowTotal = 'PercentOfParentRowTotal'
        percentOfParentColumnTotal = 'PercentOfParentColumnTotal'
        percentOfParentTotal = 'PercentOfParentTotal'
        percentOf = 'PercentOf'
        runningTotal = 'RunningTotal'
        percentRunningTotal = 'PercentRunningTotal'
        differenceFrom = 'DifferenceFrom'
        percentDifferenceFrom = 'PercentDifferenceFrom'
        rankAscending = 'RankAscending'
        rankDecending = 'RankDecending'
        index = 'Index'
    
    class PivotAxis:
        unknown = 'Unknown'
        row = 'Row'
        column = 'Column'
        data = 'Data'
        filter = 'Filter'
    
    class PictureColorType:
        mixed = 'Mixed'
        automatic = 'Automatic'
        grayScale = 'GrayScale'
        blackAndWhite = 'BlackAndWhite'
        watermark = 'Watermark'
    
    class LinkedEntityDataDomainRefreshMode:
        unknown = 'Unknown'
        manual = 'Manual'
        onLoad = 'OnLoad'
        periodic = 'Periodic'
    
    class ChartAxisType:
        invalid = 'Invalid'
        category = 'Category'
        value = 'Value'
        series = 'Series'
    
    class ChartAxisGroup:
        primary = 'Primary'
        secondary = 'Secondary'
    
    class ChartAxisScaleType:
        linear = 'Linear'
        logarithmic = 'Logarithmic'
    
    class ChartAxisPosition:
        automatic = 'Automatic'
        maximum = 'Maximum'
        minimum = 'Minimum'
        custom = 'Custom'
    
    class ChartAxisTickMark:
        none = 'None'
        cross = 'Cross'
        inside = 'Inside'
        outside = 'Outside'
    
    class CalculationState:
        done = 'Done'
        calculating = 'Calculating'
        pending = 'Pending'
    
    class ChartAxisTickLabelPosition:
        nextToAxis = 'NextToAxis'
        high = 'High'
        low = 'Low'
        none = 'None'
    
    class ChartAxisDisplayUnit:
        none = 'None'
        hundreds = 'Hundreds'
        thousands = 'Thousands'
        tenThousands = 'TenThousands'
        hundredThousands = 'HundredThousands'
        millions = 'Millions'
        tenMillions = 'TenMillions'
        hundredMillions = 'HundredMillions'
        billions = 'Billions'
        trillions = 'Trillions'
        custom = 'Custom'
    
    class ChartAxisTimeUnit:
        days = 'Days'
        months = 'Months'
        years = 'Years'
    
    class ChartBoxQuartileCalculation:
        inclusive = 'Inclusive'
        exclusive = 'Exclusive'
    
    class ChartAxisCategoryType:
        automatic = 'Automatic'
        textAxis = 'TextAxis'
        dateAxis = 'DateAxis'
    
    class ChartBinType:
        category = 'Category'
        auto = 'Auto'
        binWidth = 'BinWidth'
        binCount = 'BinCount'
    
    class ChartLineStyle:
        none = 'None'
        continuous = 'Continuous'
        dash = 'Dash'
        dashDot = 'DashDot'
        dashDotDot = 'DashDotDot'
        dot = 'Dot'
        grey25 = 'Grey25'
        grey50 = 'Grey50'
        grey75 = 'Grey75'
        automatic = 'Automatic'
        roundDot = 'RoundDot'
    
    class ChartDataLabelPosition:
        invalid = 'Invalid'
        none = 'None'
        center = 'Center'
        insideEnd = 'InsideEnd'
        insideBase = 'InsideBase'
        outsideEnd = 'OutsideEnd'
        left = 'Left'
        right = 'Right'
        top = 'Top'
        bottom = 'Bottom'
        bestFit = 'BestFit'
        callout = 'Callout'
    
    class ChartErrorBarsInclude:
        both = 'Both'
        minusValues = 'MinusValues'
        plusValues = 'PlusValues'
    
    class ChartErrorBarsType:
        fixedValue = 'FixedValue'
        percent = 'Percent'
        stDev = 'StDev'
        stError = 'StError'
        custom = 'Custom'
    
    class ChartMapAreaLevel:
        automatic = 'Automatic'
        dataOnly = 'DataOnly'
        city = 'City'
        county = 'County'
        state = 'State'
        country = 'Country'
        continent = 'Continent'
        world = 'World'
    
    class ChartGradientStyle:
        twoPhaseColor = 'TwoPhaseColor'
        threePhaseColor = 'ThreePhaseColor'
    
    class ChartGradientStyleType:
        extremeValue = 'ExtremeValue'
        number = 'Number'
        percent = 'Percent'
    
    class ChartTitlePosition:
        automatic = 'Automatic'
        top = 'Top'
        bottom = 'Bottom'
        left = 'Left'
        right = 'Right'
    
    class ChartLegendPosition:
        invalid = 'Invalid'
        top = 'Top'
        bottom = 'Bottom'
        left = 'Left'
        right = 'Right'
        corner = 'Corner'
        custom = 'Custom'
    
    class ChartMarkerStyle:
        invalid = 'Invalid'
        automatic = 'Automatic'
        none = 'None'
        square = 'Square'
        diamond = 'Diamond'
        triangle = 'Triangle'
        x = 'X'
        star = 'Star'
        dot = 'Dot'
        dash = 'Dash'
        circle = 'Circle'
        plus = 'Plus'
        picture = 'Picture'
    
    class ChartPlotAreaPosition:
        automatic = 'Automatic'
        custom = 'Custom'
    
    class ChartMapLabelStrategy:
        none = 'None'
        bestFit = 'BestFit'
        showAll = 'ShowAll'
    
    class ChartMapProjectionType:
        automatic = 'Automatic'
        mercator = 'Mercator'
        miller = 'Miller'
        robinson = 'Robinson'
        albers = 'Albers'
    
    class ChartParentLabelStrategy:
        none = 'None'
        banner = 'Banner'
        overlapping = 'Overlapping'
    
    class ChartSeriesBy:
        auto = 'Auto'
        columns = 'Columns'
        rows = 'Rows'
    
    class ChartDataSourceType:
        localRange = 'LocalRange'
        externalRange = 'ExternalRange'
        list = 'List'
        unknown = 'Unknown'
    
    class ChartTextHorizontalAlignment:
        center = 'Center'
        left = 'Left'
        right = 'Right'
        justify = 'Justify'
        distributed = 'Distributed'
    
    class ChartTextVerticalAlignment:
        center = 'Center'
        bottom = 'Bottom'
        top = 'Top'
        justify = 'Justify'
        distributed = 'Distributed'
    
    class ChartTickLabelAlignment:
        center = 'Center'
        left = 'Left'
        right = 'Right'
    
    class ChartType:
        invalid = 'Invalid'
        columnClustered = 'ColumnClustered'
        columnStacked = 'ColumnStacked'
        columnStacked100 = 'ColumnStacked100'
        _3DColumnClustered = '3DColumnClustered'
        _3DColumnStacked = '3DColumnStacked'
        _3DColumnStacked100 = '3DColumnStacked100'
        barClustered = 'BarClustered'
        barStacked = 'BarStacked'
        barStacked100 = 'BarStacked100'
        _3DBarClustered = '3DBarClustered'
        _3DBarStacked = '3DBarStacked'
        _3DBarStacked100 = '3DBarStacked100'
        lineStacked = 'LineStacked'
        lineStacked100 = 'LineStacked100'
        lineMarkers = 'LineMarkers'
        lineMarkersStacked = 'LineMarkersStacked'
        lineMarkersStacked100 = 'LineMarkersStacked100'
        pieOfPie = 'PieOfPie'
        pieExploded = 'PieExploded'
        _3DPieExploded = '3DPieExploded'
        barOfPie = 'BarOfPie'
        xyscatterSmooth = 'XYScatterSmooth'
        xyscatterSmoothNoMarkers = 'XYScatterSmoothNoMarkers'
        xyscatterLines = 'XYScatterLines'
        xyscatterLinesNoMarkers = 'XYScatterLinesNoMarkers'
        areaStacked = 'AreaStacked'
        areaStacked100 = 'AreaStacked100'
        _3DAreaStacked = '3DAreaStacked'
        _3DAreaStacked100 = '3DAreaStacked100'
        doughnutExploded = 'DoughnutExploded'
        radarMarkers = 'RadarMarkers'
        radarFilled = 'RadarFilled'
        surface = 'Surface'
        surfaceWireframe = 'SurfaceWireframe'
        surfaceTopView = 'SurfaceTopView'
        surfaceTopViewWireframe = 'SurfaceTopViewWireframe'
        bubble = 'Bubble'
        bubble3DEffect = 'Bubble3DEffect'
        stockHLC = 'StockHLC'
        stockOHLC = 'StockOHLC'
        stockVHLC = 'StockVHLC'
        stockVOHLC = 'StockVOHLC'
        cylinderColClustered = 'CylinderColClustered'
        cylinderColStacked = 'CylinderColStacked'
        cylinderColStacked100 = 'CylinderColStacked100'
        cylinderBarClustered = 'CylinderBarClustered'
        cylinderBarStacked = 'CylinderBarStacked'
        cylinderBarStacked100 = 'CylinderBarStacked100'
        cylinderCol = 'CylinderCol'
        coneColClustered = 'ConeColClustered'
        coneColStacked = 'ConeColStacked'
        coneColStacked100 = 'ConeColStacked100'
        coneBarClustered = 'ConeBarClustered'
        coneBarStacked = 'ConeBarStacked'
        coneBarStacked100 = 'ConeBarStacked100'
        coneCol = 'ConeCol'
        pyramidColClustered = 'PyramidColClustered'
        pyramidColStacked = 'PyramidColStacked'
        pyramidColStacked100 = 'PyramidColStacked100'
        pyramidBarClustered = 'PyramidBarClustered'
        pyramidBarStacked = 'PyramidBarStacked'
        pyramidBarStacked100 = 'PyramidBarStacked100'
        pyramidCol = 'PyramidCol'
        _3DColumn = '3DColumn'
        line = 'Line'
        _3DLine = '3DLine'
        _3DPie = '3DPie'
        pie = 'Pie'
        xyscatter = 'XYScatter'
        _3DArea = '3DArea'
        area = 'Area'
        doughnut = 'Doughnut'
        radar = 'Radar'
        histogram = 'Histogram'
        boxwhisker = 'Boxwhisker'
        pareto = 'Pareto'
        regionMap = 'RegionMap'
        treemap = 'Treemap'
        waterfall = 'Waterfall'
        sunburst = 'Sunburst'
        funnel = 'Funnel'
    
    class ChartUnderlineStyle:
        none = 'None'
        single = 'Single'
    
    class ChartDisplayBlanksAs:
        notPlotted = 'NotPlotted'
        zero = 'Zero'
        interplotted = 'Interplotted'
    
    class ChartPlotBy:
        rows = 'Rows'
        columns = 'Columns'
    
    class ChartSplitType:
        splitByPosition = 'SplitByPosition'
        splitByValue = 'SplitByValue'
        splitByPercentValue = 'SplitByPercentValue'
        splitByCustomSplit = 'SplitByCustomSplit'
    
    class ChartColorScheme:
        colorfulPalette1 = 'ColorfulPalette1'
        colorfulPalette2 = 'ColorfulPalette2'
        colorfulPalette3 = 'ColorfulPalette3'
        colorfulPalette4 = 'ColorfulPalette4'
        monochromaticPalette1 = 'MonochromaticPalette1'
        monochromaticPalette2 = 'MonochromaticPalette2'
        monochromaticPalette3 = 'MonochromaticPalette3'
        monochromaticPalette4 = 'MonochromaticPalette4'
        monochromaticPalette5 = 'MonochromaticPalette5'
        monochromaticPalette6 = 'MonochromaticPalette6'
        monochromaticPalette7 = 'MonochromaticPalette7'
        monochromaticPalette8 = 'MonochromaticPalette8'
        monochromaticPalette9 = 'MonochromaticPalette9'
        monochromaticPalette10 = 'MonochromaticPalette10'
        monochromaticPalette11 = 'MonochromaticPalette11'
        monochromaticPalette12 = 'MonochromaticPalette12'
        monochromaticPalette13 = 'MonochromaticPalette13'
    
    class ChartTrendlineType:
        linear = 'Linear'
        exponential = 'Exponential'
        logarithmic = 'Logarithmic'
        movingAverage = 'MovingAverage'
        polynomial = 'Polynomial'
        power = 'Power'
    
    class ShapeZOrder:
        bringToFront = 'BringToFront'
        bringForward = 'BringForward'
        sendToBack = 'SendToBack'
        sendBackward = 'SendBackward'
    
    class ShapeType:
        unsupported = 'Unsupported'
        image = 'Image'
        geometricShape = 'GeometricShape'
        group = 'Group'
        line = 'Line'
    
    class ShapeScaleType:
        currentSize = 'CurrentSize'
        originalSize = 'OriginalSize'
    
    class ShapeScaleFrom:
        scaleFromTopLeft = 'ScaleFromTopLeft'
        scaleFromMiddle = 'ScaleFromMiddle'
        scaleFromBottomRight = 'ScaleFromBottomRight'
    
    class ShapeFillType:
        noFill = 'NoFill'
        solid = 'Solid'
        gradient = 'Gradient'
        pattern = 'Pattern'
        pictureAndTexture = 'PictureAndTexture'
        mixed = 'Mixed'
    
    class ShapeFontUnderlineStyle:
        none = 'None'
        single = 'Single'
        double = 'Double'
        heavy = 'Heavy'
        dotted = 'Dotted'
        dottedHeavy = 'DottedHeavy'
        dash = 'Dash'
        dashHeavy = 'DashHeavy'
        dashLong = 'DashLong'
        dashLongHeavy = 'DashLongHeavy'
        dotDash = 'DotDash'
        dotDashHeavy = 'DotDashHeavy'
        dotDotDash = 'DotDotDash'
        dotDotDashHeavy = 'DotDotDashHeavy'
        wavy = 'Wavy'
        wavyHeavy = 'WavyHeavy'
        wavyDouble = 'WavyDouble'
    
    class PictureFormat:
        unknown = 'UNKNOWN'
        bmp = 'BMP'
        jpeg = 'JPEG'
        gif = 'GIF'
        png = 'PNG'
        svg = 'SVG'
    
    class ShapeLineStyle:
        single = 'Single'
        thickBetweenThin = 'ThickBetweenThin'
        thickThin = 'ThickThin'
        thinThick = 'ThinThick'
        thinThin = 'ThinThin'
    
    class ShapeLineDashStyle:
        dash = 'Dash'
        dashDot = 'DashDot'
        dashDotDot = 'DashDotDot'
        longDash = 'LongDash'
        longDashDot = 'LongDashDot'
        roundDot = 'RoundDot'
        solid = 'Solid'
        squareDot = 'SquareDot'
        longDashDotDot = 'LongDashDotDot'
        systemDash = 'SystemDash'
        systemDot = 'SystemDot'
        systemDashDot = 'SystemDashDot'
    
    class ArrowheadLength:
        short = 'Short'
        medium = 'Medium'
        long = 'Long'
    
    class ArrowheadStyle:
        none = 'None'
        triangle = 'Triangle'
        stealth = 'Stealth'
        diamond = 'Diamond'
        oval = 'Oval'
        open = 'Open'
    
    class ArrowheadWidth:
        narrow = 'Narrow'
        medium = 'Medium'
        wide = 'Wide'
    
    class BindingType:
        range = 'Range'
        table = 'Table'
        text = 'Text'
    
    class BorderIndex:
        edgeTop = 'EdgeTop'
        edgeBottom = 'EdgeBottom'
        edgeLeft = 'EdgeLeft'
        edgeRight = 'EdgeRight'
        insideVertical = 'InsideVertical'
        insideHorizontal = 'InsideHorizontal'
        diagonalDown = 'DiagonalDown'
        diagonalUp = 'DiagonalUp'
    
    class BorderLineStyle:
        none = 'None'
        continuous = 'Continuous'
        dash = 'Dash'
        dashDot = 'DashDot'
        dashDotDot = 'DashDotDot'
        dot = 'Dot'
        double = 'Double'
        slantDashDot = 'SlantDashDot'
    
    class BorderWeight:
        hairline = 'Hairline'
        thin = 'Thin'
        medium = 'Medium'
        thick = 'Thick'
    
    class CalculationMode:
        automatic = 'Automatic'
        automaticExceptTables = 'AutomaticExceptTables'
        manual = 'Manual'
    
    class CalculationType:
        recalculate = 'Recalculate'
        full = 'Full'
        fullRebuild = 'FullRebuild'
    
    class ClearApplyTo:
        all = 'All'
        formats = 'Formats'
        contents = 'Contents'
        hyperlinks = 'Hyperlinks'
        removeHyperlinks = 'RemoveHyperlinks'
        resetContents = 'ResetContents'
    
    class ConditionalDataBarAxisFormat:
        automatic = 'Automatic'
        none = 'None'
        cellMidPoint = 'CellMidPoint'
    
    class ConditionalDataBarDirection:
        context = 'Context'
        leftToRight = 'LeftToRight'
        rightToLeft = 'RightToLeft'
    
    class ConditionalFormatDirection:
        top = 'Top'
        bottom = 'Bottom'
    
    class ConditionalFormatType:
        custom = 'Custom'
        dataBar = 'DataBar'
        colorScale = 'ColorScale'
        iconSet = 'IconSet'
        topBottom = 'TopBottom'
        presetCriteria = 'PresetCriteria'
        containsText = 'ContainsText'
        cellValue = 'CellValue'
    
    class ConditionalFormatRuleType:
        invalid = 'Invalid'
        automatic = 'Automatic'
        lowestValue = 'LowestValue'
        highestValue = 'HighestValue'
        number = 'Number'
        percent = 'Percent'
        formula = 'Formula'
        percentile = 'Percentile'
    
    class ConditionalFormatIconRuleType:
        invalid = 'Invalid'
        number = 'Number'
        percent = 'Percent'
        formula = 'Formula'
        percentile = 'Percentile'
    
    class ConditionalFormatColorCriterionType:
        invalid = 'Invalid'
        lowestValue = 'LowestValue'
        highestValue = 'HighestValue'
        number = 'Number'
        percent = 'Percent'
        formula = 'Formula'
        percentile = 'Percentile'
    
    class ConditionalTopBottomCriterionType:
        invalid = 'Invalid'
        topItems = 'TopItems'
        topPercent = 'TopPercent'
        bottomItems = 'BottomItems'
        bottomPercent = 'BottomPercent'
    
    class ConditionalFormatPresetCriterion:
        invalid = 'Invalid'
        blanks = 'Blanks'
        nonBlanks = 'NonBlanks'
        errors = 'Errors'
        nonErrors = 'NonErrors'
        yesterday = 'Yesterday'
        today = 'Today'
        tomorrow = 'Tomorrow'
        lastSevenDays = 'LastSevenDays'
        lastWeek = 'LastWeek'
        thisWeek = 'ThisWeek'
        nextWeek = 'NextWeek'
        lastMonth = 'LastMonth'
        thisMonth = 'ThisMonth'
        nextMonth = 'NextMonth'
        aboveAverage = 'AboveAverage'
        belowAverage = 'BelowAverage'
        equalOrAboveAverage = 'EqualOrAboveAverage'
        equalOrBelowAverage = 'EqualOrBelowAverage'
        oneStdDevAboveAverage = 'OneStdDevAboveAverage'
        oneStdDevBelowAverage = 'OneStdDevBelowAverage'
        twoStdDevAboveAverage = 'TwoStdDevAboveAverage'
        twoStdDevBelowAverage = 'TwoStdDevBelowAverage'
        threeStdDevAboveAverage = 'ThreeStdDevAboveAverage'
        threeStdDevBelowAverage = 'ThreeStdDevBelowAverage'
        uniqueValues = 'UniqueValues'
        duplicateValues = 'DuplicateValues'
    
    class ConditionalTextOperator:
        invalid = 'Invalid'
        contains = 'Contains'
        notContains = 'NotContains'
        beginsWith = 'BeginsWith'
        endsWith = 'EndsWith'
    
    class ConditionalCellValueOperator:
        invalid = 'Invalid'
        between = 'Between'
        notBetween = 'NotBetween'
        equalTo = 'EqualTo'
        notEqualTo = 'NotEqualTo'
        greaterThan = 'GreaterThan'
        lessThan = 'LessThan'
        greaterThanOrEqual = 'GreaterThanOrEqual'
        lessThanOrEqual = 'LessThanOrEqual'
    
    class ConditionalIconCriterionOperator:
        invalid = 'Invalid'
        greaterThan = 'GreaterThan'
        greaterThanOrEqual = 'GreaterThanOrEqual'
    
    class ConditionalRangeBorderIndex:
        edgeTop = 'EdgeTop'
        edgeBottom = 'EdgeBottom'
        edgeLeft = 'EdgeLeft'
        edgeRight = 'EdgeRight'
    
    class ConditionalRangeBorderLineStyle:
        none = 'None'
        continuous = 'Continuous'
        dash = 'Dash'
        dashDot = 'DashDot'
        dashDotDot = 'DashDotDot'
        dot = 'Dot'
    
    class ConditionalRangeFontUnderlineStyle:
        none = 'None'
        single = 'Single'
        double = 'Double'
    
    class DataValidationType:
        none = 'None'
        wholeNumber = 'WholeNumber'
        decimal = 'Decimal'
        list = 'List'
        date = 'Date'
        time = 'Time'
        textLength = 'TextLength'
        custom = 'Custom'
        inconsistent = 'Inconsistent'
        mixedCriteria = 'MixedCriteria'
    
    class DataValidationOperator:
        between = 'Between'
        notBetween = 'NotBetween'
        equalTo = 'EqualTo'
        notEqualTo = 'NotEqualTo'
        greaterThan = 'GreaterThan'
        lessThan = 'LessThan'
        greaterThanOrEqualTo = 'GreaterThanOrEqualTo'
        lessThanOrEqualTo = 'LessThanOrEqualTo'
    
    class DataValidationAlertStyle:
        stop = 'Stop'
        warning = 'Warning'
        information = 'Information'
    
    class DeleteShiftDirection:
        up = 'Up'
        left = 'Left'
    
    class DynamicFilterCriteria:
        unknown = 'Unknown'
        aboveAverage = 'AboveAverage'
        allDatesInPeriodApril = 'AllDatesInPeriodApril'
        allDatesInPeriodAugust = 'AllDatesInPeriodAugust'
        allDatesInPeriodDecember = 'AllDatesInPeriodDecember'
        allDatesInPeriodFebruray = 'AllDatesInPeriodFebruray'
        allDatesInPeriodJanuary = 'AllDatesInPeriodJanuary'
        allDatesInPeriodJuly = 'AllDatesInPeriodJuly'
        allDatesInPeriodJune = 'AllDatesInPeriodJune'
        allDatesInPeriodMarch = 'AllDatesInPeriodMarch'
        allDatesInPeriodMay = 'AllDatesInPeriodMay'
        allDatesInPeriodNovember = 'AllDatesInPeriodNovember'
        allDatesInPeriodOctober = 'AllDatesInPeriodOctober'
        allDatesInPeriodQuarter1 = 'AllDatesInPeriodQuarter1'
        allDatesInPeriodQuarter2 = 'AllDatesInPeriodQuarter2'
        allDatesInPeriodQuarter3 = 'AllDatesInPeriodQuarter3'
        allDatesInPeriodQuarter4 = 'AllDatesInPeriodQuarter4'
        allDatesInPeriodSeptember = 'AllDatesInPeriodSeptember'
        belowAverage = 'BelowAverage'
        lastMonth = 'LastMonth'
        lastQuarter = 'LastQuarter'
        lastWeek = 'LastWeek'
        lastYear = 'LastYear'
        nextMonth = 'NextMonth'
        nextQuarter = 'NextQuarter'
        nextWeek = 'NextWeek'
        nextYear = 'NextYear'
        thisMonth = 'ThisMonth'
        thisQuarter = 'ThisQuarter'
        thisWeek = 'ThisWeek'
        thisYear = 'ThisYear'
        today = 'Today'
        tomorrow = 'Tomorrow'
        yearToDate = 'YearToDate'
        yesterday = 'Yesterday'
    
    class FilterDatetimeSpecificity:
        year = 'Year'
        month = 'Month'
        day = 'Day'
        hour = 'Hour'
        minute = 'Minute'
        second = 'Second'
    
    class FilterOn:
        bottomItems = 'BottomItems'
        bottomPercent = 'BottomPercent'
        cellColor = 'CellColor'
        dynamic = 'Dynamic'
        fontColor = 'FontColor'
        values = 'Values'
        topItems = 'TopItems'
        topPercent = 'TopPercent'
        icon = 'Icon'
        custom = 'Custom'
    
    class FilterOperator:
        and_ = 'And'
        or_ = 'Or'
    
    class HorizontalAlignment:
        general = 'General'
        left = 'Left'
        center = 'Center'
        right = 'Right'
        fill = 'Fill'
        justify = 'Justify'
        centerAcrossSelection = 'CenterAcrossSelection'
        distributed = 'Distributed'
    
    class IconSet:
        invalid = 'Invalid'
        threeArrows = 'ThreeArrows'
        threeArrowsGray = 'ThreeArrowsGray'
        threeFlags = 'ThreeFlags'
        threeTrafficLights1 = 'ThreeTrafficLights1'
        threeTrafficLights2 = 'ThreeTrafficLights2'
        threeSigns = 'ThreeSigns'
        threeSymbols = 'ThreeSymbols'
        threeSymbols2 = 'ThreeSymbols2'
        fourArrows = 'FourArrows'
        fourArrowsGray = 'FourArrowsGray'
        fourRedToBlack = 'FourRedToBlack'
        fourRating = 'FourRating'
        fourTrafficLights = 'FourTrafficLights'
        fiveArrows = 'FiveArrows'
        fiveArrowsGray = 'FiveArrowsGray'
        fiveRating = 'FiveRating'
        fiveQuarters = 'FiveQuarters'
        threeStars = 'ThreeStars'
        threeTriangles = 'ThreeTriangles'
        fiveBoxes = 'FiveBoxes'
    
    class ImageFittingMode:
        fit = 'Fit'
        fitAndCenter = 'FitAndCenter'
        fill = 'Fill'
    
    class InsertShiftDirection:
        down = 'Down'
        right = 'Right'
    
    class NamedItemScope:
        worksheet = 'Worksheet'
        workbook = 'Workbook'
    
    class NamedItemType:
        string = 'String'
        integer = 'Integer'
        double = 'Double'
        boolean = 'Boolean'
        range = 'Range'
        error = 'Error'
        array = 'Array'
    
    class RangeUnderlineStyle:
        none = 'None'
        single = 'Single'
        double = 'Double'
        singleAccountant = 'SingleAccountant'
        doubleAccountant = 'DoubleAccountant'
    
    class SheetVisibility:
        visible = 'Visible'
        hidden = 'Hidden'
        veryHidden = 'VeryHidden'
    
    class EventTriggerSource:
        unknown = 'Unknown'
        thisLocalAddin = 'ThisLocalAddin'
    
    class RangeValueType:
        unknown = 'Unknown'
        empty = 'Empty'
        string = 'String'
        integer = 'Integer'
        double = 'Double'
        boolean = 'Boolean'
        error = 'Error'
        richValue = 'RichValue'
    
    class KeyboardDirection:
        left = 'Left'
        right = 'Right'
        up = 'Up'
        down = 'Down'
    
    class SearchDirection:
        forward = 'Forward'
        backwards = 'Backwards'
    
    class SortOrientation:
        rows = 'Rows'
        columns = 'Columns'
    
    class SortOn:
        value = 'Value'
        cellColor = 'CellColor'
        fontColor = 'FontColor'
        icon = 'Icon'
    
    class SortDataOption:
        normal = 'Normal'
        textAsNumber = 'TextAsNumber'
    
    class SortMethod:
        pinYin = 'PinYin'
        strokeCount = 'StrokeCount'
    
    class VerticalAlignment:
        top = 'Top'
        center = 'Center'
        bottom = 'Bottom'
        justify = 'Justify'
        distributed = 'Distributed'
    
    class DocumentPropertyType:
        number = 'Number'
        boolean = 'Boolean'
        date = 'Date'
        string = 'String'
        float = 'Float'
    
    class EventSource:
        local = 'Local'
        remote = 'Remote'
    
    class DataChangeType:
        unknown = 'Unknown'
        rangeEdited = 'RangeEdited'
        rowInserted = 'RowInserted'
        rowDeleted = 'RowDeleted'
        columnInserted = 'ColumnInserted'
        columnDeleted = 'ColumnDeleted'
        cellInserted = 'CellInserted'
        cellDeleted = 'CellDeleted'
    
    class RowHiddenChangeType:
        unhidden = 'Unhidden'
        hidden = 'Hidden'
    
    class CommentChangeType:
        commentEdited = 'CommentEdited'
        commentResolved = 'CommentResolved'
        commentReopened = 'CommentReopened'
        replyAdded = 'ReplyAdded'
        replyDeleted = 'ReplyDeleted'
        replyEdited = 'ReplyEdited'
    
    class EventType:
        worksheetChanged = 'WorksheetChanged'
        worksheetSelectionChanged = 'WorksheetSelectionChanged'
        worksheetAdded = 'WorksheetAdded'
        worksheetActivated = 'WorksheetActivated'
        worksheetDeactivated = 'WorksheetDeactivated'
        tableChanged = 'TableChanged'
        tableSelectionChanged = 'TableSelectionChanged'
        worksheetDeleted = 'WorksheetDeleted'
        chartAdded = 'ChartAdded'
        chartActivated = 'ChartActivated'
        chartDeactivated = 'ChartDeactivated'
        chartDeleted = 'ChartDeleted'
        worksheetCalculated = 'WorksheetCalculated'
        visualSelectionChanged = 'VisualSelectionChanged'
        tableAdded = 'TableAdded'
        tableDeleted = 'TableDeleted'
        tableFiltered = 'TableFiltered'
        worksheetFiltered = 'WorksheetFiltered'
        shapeActivated = 'ShapeActivated'
        shapeDeactivated = 'ShapeDeactivated'
        visualChange = 'VisualChange'
        workbookAutoSaveSettingChanged = 'WorkbookAutoSaveSettingChanged'
        worksheetFormatChanged = 'WorksheetFormatChanged'
        ribbonCommandExecuted = 'RibbonCommandExecuted'
        worksheetRowSorted = 'WorksheetRowSorted'
        worksheetColumnSorted = 'WorksheetColumnSorted'
        worksheetSingleClicked = 'WorksheetSingleClicked'
        worksheetRowHiddenChanged = 'WorksheetRowHiddenChanged'
        commentAdded = 'CommentAdded'
        commentDeleted = 'CommentDeleted'
        commentChanged = 'CommentChanged'
        worksheetFormulaChanged = 'WorksheetFormulaChanged'
        workbookActivated = 'WorkbookActivated'
        linkedWorkbookWorkbookLinksChanged = 'LinkedWorkbookWorkbookLinksChanged'
        linkedWorkbookRefreshCompleted = 'LinkedWorkbookRefreshCompleted'
        worksheetProtectionChanged = 'WorksheetProtectionChanged'
        worksheetNameChanged = 'WorksheetNameChanged'
        worksheetVisibilityChanged = 'WorksheetVisibilityChanged'
        worksheetMoved = 'WorksheetMoved'
        linkedEntityDataDomainLinkedEntityDataDomainAdded = 'LinkedEntityDataDomainLinkedEntityDataDomainAdded'
        linkedEntityDataDomainRefreshCompleted = 'LinkedEntityDataDomainRefreshCompleted'
        linkedEntityDataDomainRefreshModeChanged = 'LinkedEntityDataDomainRefreshModeChanged'
    
    class DocumentPropertyItem:
        title = 'Title'
        subject = 'Subject'
        author = 'Author'
        keywords = 'Keywords'
        comments = 'Comments'
        template = 'Template'
        lastAuth = 'LastAuth'
        revision = 'Revision'
        appName = 'AppName'
        lastPrint = 'LastPrint'
        creation = 'Creation'
        lastSave = 'LastSave'
        category = 'Category'
        format = 'Format'
        manager = 'Manager'
        company = 'Company'
    
    class SubtotalLocationType:
        atTop = 'AtTop'
        atBottom = 'AtBottom'
        off = 'Off'
    
    class PivotLayoutType:
        compact = 'Compact'
        tabular = 'Tabular'
        outline = 'Outline'
    
    class ProtectionSelectionMode:
        normal = 'Normal'
        unlocked = 'Unlocked'
        none = 'None'
    
    class PageOrientation:
        portrait = 'Portrait'
        landscape = 'Landscape'
    
    class PaperType:
        letter = 'Letter'
        letterSmall = 'LetterSmall'
        tabloid = 'Tabloid'
        ledger = 'Ledger'
        legal = 'Legal'
        statement = 'Statement'
        executive = 'Executive'
        a3 = 'A3'
        a4 = 'A4'
        a4Small = 'A4Small'
        a5 = 'A5'
        b4 = 'B4'
        b5 = 'B5'
        folio = 'Folio'
        quatro = 'Quatro'
        paper10x14 = 'Paper10x14'
        paper11x17 = 'Paper11x17'
        note = 'Note'
        envelope9 = 'Envelope9'
        envelope10 = 'Envelope10'
        envelope11 = 'Envelope11'
        envelope12 = 'Envelope12'
        envelope14 = 'Envelope14'
        csheet = 'Csheet'
        dsheet = 'Dsheet'
        esheet = 'Esheet'
        envelopeDL = 'EnvelopeDL'
        envelopeC5 = 'EnvelopeC5'
        envelopeC3 = 'EnvelopeC3'
        envelopeC4 = 'EnvelopeC4'
        envelopeC6 = 'EnvelopeC6'
        envelopeC65 = 'EnvelopeC65'
        envelopeB4 = 'EnvelopeB4'
        envelopeB5 = 'EnvelopeB5'
        envelopeB6 = 'EnvelopeB6'
        envelopeItaly = 'EnvelopeItaly'
        envelopeMonarch = 'EnvelopeMonarch'
        envelopePersonal = 'EnvelopePersonal'
        fanfoldUS = 'FanfoldUS'
        fanfoldStdGerman = 'FanfoldStdGerman'
        fanfoldLegalGerman = 'FanfoldLegalGerman'
    
    class ReadingOrder:
        context = 'Context'
        leftToRight = 'LeftToRight'
        rightToLeft = 'RightToLeft'
    
    class BuiltInStyle:
        normal = 'Normal'
        comma = 'Comma'
        currency = 'Currency'
        percent = 'Percent'
        wholeComma = 'WholeComma'
        wholeDollar = 'WholeDollar'
        hlink = 'Hlink'
        hlinkTrav = 'HlinkTrav'
        note = 'Note'
        warningText = 'WarningText'
        emphasis1 = 'Emphasis1'
        emphasis2 = 'Emphasis2'
        emphasis3 = 'Emphasis3'
        sheetTitle = 'SheetTitle'
        heading1 = 'Heading1'
        heading2 = 'Heading2'
        heading3 = 'Heading3'
        heading4 = 'Heading4'
        input = 'Input'
        output = 'Output'
        calculation = 'Calculation'
        checkCell = 'CheckCell'
        linkedCell = 'LinkedCell'
        total = 'Total'
        good = 'Good'
        bad = 'Bad'
        neutral = 'Neutral'
        accent1 = 'Accent1'
        accent1_20 = 'Accent1_20'
        accent1_40 = 'Accent1_40'
        accent1_60 = 'Accent1_60'
        accent2 = 'Accent2'
        accent2_20 = 'Accent2_20'
        accent2_40 = 'Accent2_40'
        accent2_60 = 'Accent2_60'
        accent3 = 'Accent3'
        accent3_20 = 'Accent3_20'
        accent3_40 = 'Accent3_40'
        accent3_60 = 'Accent3_60'
        accent4 = 'Accent4'
        accent4_20 = 'Accent4_20'
        accent4_40 = 'Accent4_40'
        accent4_60 = 'Accent4_60'
        accent5 = 'Accent5'
        accent5_20 = 'Accent5_20'
        accent5_40 = 'Accent5_40'
        accent5_60 = 'Accent5_60'
        accent6 = 'Accent6'
        accent6_20 = 'Accent6_20'
        accent6_40 = 'Accent6_40'
        accent6_60 = 'Accent6_60'
        explanatoryText = 'ExplanatoryText'
    
    class PrintErrorType:
        asDisplayed = 'AsDisplayed'
        blank = 'Blank'
        dash = 'Dash'
        notAvailable = 'NotAvailable'
    
    class WorksheetPositionType:
        none = 'None'
        before = 'Before'
        after = 'After'
        beginning = 'Beginning'
        end = 'End'
    
    class PrintComments:
        noComments = 'NoComments'
        endSheet = 'EndSheet'
        inPlace = 'InPlace'
    
    class PrintOrder:
        downThenOver = 'DownThenOver'
        overThenDown = 'OverThenDown'
    
    class PrintMarginUnit:
        points = 'Points'
        inches = 'Inches'
        centimeters = 'Centimeters'
    
    class HeaderFooterState:
        default = 'Default'
        firstAndDefault = 'FirstAndDefault'
        oddAndEven = 'OddAndEven'
        firstOddAndEven = 'FirstOddAndEven'
    
    class AutoFillType:
        fillDefault = 'FillDefault'
        fillCopy = 'FillCopy'
        fillSeries = 'FillSeries'
        fillFormats = 'FillFormats'
        fillValues = 'FillValues'
        fillDays = 'FillDays'
        fillWeekdays = 'FillWeekdays'
        fillMonths = 'FillMonths'
        fillYears = 'FillYears'
        linearTrend = 'LinearTrend'
        growthTrend = 'GrowthTrend'
        flashFill = 'FlashFill'
    
    class GroupOption:
        byRows = 'ByRows'
        byColumns = 'ByColumns'
    
    class RangeCopyType:
        all = 'All'
        formulas = 'Formulas'
        values = 'Values'
        formats = 'Formats'
        link = 'Link'
    
    class LinkedDataTypeState:
        none = 'None'
        validLinkedData = 'ValidLinkedData'
        disambiguationNeeded = 'DisambiguationNeeded'
        brokenLinkedData = 'BrokenLinkedData'
        fetchingData = 'FetchingData'
    
    class GeometricShapeType:
        lineInverse = 'LineInverse'
        triangle = 'Triangle'
        rightTriangle = 'RightTriangle'
        rectangle = 'Rectangle'
        diamond = 'Diamond'
        parallelogram = 'Parallelogram'
        trapezoid = 'Trapezoid'
        nonIsoscelesTrapezoid = 'NonIsoscelesTrapezoid'
        pentagon = 'Pentagon'
        hexagon = 'Hexagon'
        heptagon = 'Heptagon'
        octagon = 'Octagon'
        decagon = 'Decagon'
        dodecagon = 'Dodecagon'
        star4 = 'Star4'
        star5 = 'Star5'
        star6 = 'Star6'
        star7 = 'Star7'
        star8 = 'Star8'
        star10 = 'Star10'
        star12 = 'Star12'
        star16 = 'Star16'
        star24 = 'Star24'
        star32 = 'Star32'
        roundRectangle = 'RoundRectangle'
        round1Rectangle = 'Round1Rectangle'
        round2SameRectangle = 'Round2SameRectangle'
        round2DiagonalRectangle = 'Round2DiagonalRectangle'
        snipRoundRectangle = 'SnipRoundRectangle'
        snip1Rectangle = 'Snip1Rectangle'
        snip2SameRectangle = 'Snip2SameRectangle'
        snip2DiagonalRectangle = 'Snip2DiagonalRectangle'
        plaque = 'Plaque'
        ellipse = 'Ellipse'
        teardrop = 'Teardrop'
        homePlate = 'HomePlate'
        chevron = 'Chevron'
        pieWedge = 'PieWedge'
        pie = 'Pie'
        blockArc = 'BlockArc'
        donut = 'Donut'
        noSmoking = 'NoSmoking'
        rightArrow = 'RightArrow'
        leftArrow = 'LeftArrow'
        upArrow = 'UpArrow'
        downArrow = 'DownArrow'
        stripedRightArrow = 'StripedRightArrow'
        notchedRightArrow = 'NotchedRightArrow'
        bentUpArrow = 'BentUpArrow'
        leftRightArrow = 'LeftRightArrow'
        upDownArrow = 'UpDownArrow'
        leftUpArrow = 'LeftUpArrow'
        leftRightUpArrow = 'LeftRightUpArrow'
        quadArrow = 'QuadArrow'
        leftArrowCallout = 'LeftArrowCallout'
        rightArrowCallout = 'RightArrowCallout'
        upArrowCallout = 'UpArrowCallout'
        downArrowCallout = 'DownArrowCallout'
        leftRightArrowCallout = 'LeftRightArrowCallout'
        upDownArrowCallout = 'UpDownArrowCallout'
        quadArrowCallout = 'QuadArrowCallout'
        bentArrow = 'BentArrow'
        uturnArrow = 'UturnArrow'
        circularArrow = 'CircularArrow'
        leftCircularArrow = 'LeftCircularArrow'
        leftRightCircularArrow = 'LeftRightCircularArrow'
        curvedRightArrow = 'CurvedRightArrow'
        curvedLeftArrow = 'CurvedLeftArrow'
        curvedUpArrow = 'CurvedUpArrow'
        curvedDownArrow = 'CurvedDownArrow'
        swooshArrow = 'SwooshArrow'
        cube = 'Cube'
        can = 'Can'
        lightningBolt = 'LightningBolt'
        heart = 'Heart'
        sun = 'Sun'
        moon = 'Moon'
        smileyFace = 'SmileyFace'
        irregularSeal1 = 'IrregularSeal1'
        irregularSeal2 = 'IrregularSeal2'
        foldedCorner = 'FoldedCorner'
        bevel = 'Bevel'
        frame = 'Frame'
        halfFrame = 'HalfFrame'
        corner = 'Corner'
        diagonalStripe = 'DiagonalStripe'
        chord = 'Chord'
        arc = 'Arc'
        leftBracket = 'LeftBracket'
        rightBracket = 'RightBracket'
        leftBrace = 'LeftBrace'
        rightBrace = 'RightBrace'
        bracketPair = 'BracketPair'
        bracePair = 'BracePair'
        callout1 = 'Callout1'
        callout2 = 'Callout2'
        callout3 = 'Callout3'
        accentCallout1 = 'AccentCallout1'
        accentCallout2 = 'AccentCallout2'
        accentCallout3 = 'AccentCallout3'
        borderCallout1 = 'BorderCallout1'
        borderCallout2 = 'BorderCallout2'
        borderCallout3 = 'BorderCallout3'
        accentBorderCallout1 = 'AccentBorderCallout1'
        accentBorderCallout2 = 'AccentBorderCallout2'
        accentBorderCallout3 = 'AccentBorderCallout3'
        wedgeRectCallout = 'WedgeRectCallout'
        wedgeRRectCallout = 'WedgeRRectCallout'
        wedgeEllipseCallout = 'WedgeEllipseCallout'
        cloudCallout = 'CloudCallout'
        cloud = 'Cloud'
        ribbon = 'Ribbon'
        ribbon2 = 'Ribbon2'
        ellipseRibbon = 'EllipseRibbon'
        ellipseRibbon2 = 'EllipseRibbon2'
        leftRightRibbon = 'LeftRightRibbon'
        verticalScroll = 'VerticalScroll'
        horizontalScroll = 'HorizontalScroll'
        wave = 'Wave'
        doubleWave = 'DoubleWave'
        plus = 'Plus'
        flowChartProcess = 'FlowChartProcess'
        flowChartDecision = 'FlowChartDecision'
        flowChartInputOutput = 'FlowChartInputOutput'
        flowChartPredefinedProcess = 'FlowChartPredefinedProcess'
        flowChartInternalStorage = 'FlowChartInternalStorage'
        flowChartDocument = 'FlowChartDocument'
        flowChartMultidocument = 'FlowChartMultidocument'
        flowChartTerminator = 'FlowChartTerminator'
        flowChartPreparation = 'FlowChartPreparation'
        flowChartManualInput = 'FlowChartManualInput'
        flowChartManualOperation = 'FlowChartManualOperation'
        flowChartConnector = 'FlowChartConnector'
        flowChartPunchedCard = 'FlowChartPunchedCard'
        flowChartPunchedTape = 'FlowChartPunchedTape'
        flowChartSummingJunction = 'FlowChartSummingJunction'
        flowChartOr = 'FlowChartOr'
        flowChartCollate = 'FlowChartCollate'
        flowChartSort = 'FlowChartSort'
        flowChartExtract = 'FlowChartExtract'
        flowChartMerge = 'FlowChartMerge'
        flowChartOfflineStorage = 'FlowChartOfflineStorage'
        flowChartOnlineStorage = 'FlowChartOnlineStorage'
        flowChartMagneticTape = 'FlowChartMagneticTape'
        flowChartMagneticDisk = 'FlowChartMagneticDisk'
        flowChartMagneticDrum = 'FlowChartMagneticDrum'
        flowChartDisplay = 'FlowChartDisplay'
        flowChartDelay = 'FlowChartDelay'
        flowChartAlternateProcess = 'FlowChartAlternateProcess'
        flowChartOffpageConnector = 'FlowChartOffpageConnector'
        actionButtonBlank = 'ActionButtonBlank'
        actionButtonHome = 'ActionButtonHome'
        actionButtonHelp = 'ActionButtonHelp'
        actionButtonInformation = 'ActionButtonInformation'
        actionButtonForwardNext = 'ActionButtonForwardNext'
        actionButtonBackPrevious = 'ActionButtonBackPrevious'
        actionButtonEnd = 'ActionButtonEnd'
        actionButtonBeginning = 'ActionButtonBeginning'
        actionButtonReturn = 'ActionButtonReturn'
        actionButtonDocument = 'ActionButtonDocument'
        actionButtonSound = 'ActionButtonSound'
        actionButtonMovie = 'ActionButtonMovie'
        gear6 = 'Gear6'
        gear9 = 'Gear9'
        funnel = 'Funnel'
        mathPlus = 'MathPlus'
        mathMinus = 'MathMinus'
        mathMultiply = 'MathMultiply'
        mathDivide = 'MathDivide'
        mathEqual = 'MathEqual'
        mathNotEqual = 'MathNotEqual'
        cornerTabs = 'CornerTabs'
        squareTabs = 'SquareTabs'
        plaqueTabs = 'PlaqueTabs'
        chartX = 'ChartX'
        chartStar = 'ChartStar'
        chartPlus = 'ChartPlus'
    
    class ConnectorType:
        straight = 'Straight'
        elbow = 'Elbow'
        curve = 'Curve'
    
    class ContentType:
        plain = 'Plain'
        mention = 'Mention'
    
    class SpecialCellType:
        conditionalFormats = 'ConditionalFormats'
        dataValidations = 'DataValidations'
        blanks = 'Blanks'
        constants = 'Constants'
        formulas = 'Formulas'
        sameConditionalFormat = 'SameConditionalFormat'
        sameDataValidation = 'SameDataValidation'
        visible = 'Visible'
    
    class SpecialCellValueType:
        all = 'All'
        errors = 'Errors'
        errorsLogical = 'ErrorsLogical'
        errorsNumbers = 'ErrorsNumbers'
        errorsText = 'ErrorsText'
        errorsLogicalNumber = 'ErrorsLogicalNumber'
        errorsLogicalText = 'ErrorsLogicalText'
        errorsNumberText = 'ErrorsNumberText'
        logical = 'Logical'
        logicalNumbers = 'LogicalNumbers'
        logicalText = 'LogicalText'
        logicalNumbersText = 'LogicalNumbersText'
        numbers = 'Numbers'
        numbersText = 'NumbersText'
        text = 'Text'
    
    class Placement:
        twoCell = 'TwoCell'
        oneCell = 'OneCell'
        absolute = 'Absolute'
    
    class FillPattern:
        none = 'None'
        solid = 'Solid'
        gray50 = 'Gray50'
        gray75 = 'Gray75'
        gray25 = 'Gray25'
        horizontal = 'Horizontal'
        vertical = 'Vertical'
        down = 'Down'
        up = 'Up'
        checker = 'Checker'
        semiGray75 = 'SemiGray75'
        lightHorizontal = 'LightHorizontal'
        lightVertical = 'LightVertical'
        lightDown = 'LightDown'
        lightUp = 'LightUp'
        grid = 'Grid'
        crissCross = 'CrissCross'
        gray16 = 'Gray16'
        gray8 = 'Gray8'
        linearGradient = 'LinearGradient'
        rectangularGradient = 'RectangularGradient'
    
    class ShapeTextHorizontalAlignment:
        left = 'Left'
        center = 'Center'
        right = 'Right'
        justify = 'Justify'
        justifyLow = 'JustifyLow'
        distributed = 'Distributed'
        thaiDistributed = 'ThaiDistributed'
    
    class ShapeTextVerticalAlignment:
        top = 'Top'
        middle = 'Middle'
        bottom = 'Bottom'
        justified = 'Justified'
        distributed = 'Distributed'
    
    class ShapeTextVerticalOverflow:
        overflow = 'Overflow'
        ellipsis = 'Ellipsis'
        clip = 'Clip'
    
    class ShapeTextHorizontalOverflow:
        overflow = 'Overflow'
        clip = 'Clip'
    
    class ShapeTextReadingOrder:
        leftToRight = 'LeftToRight'
        rightToLeft = 'RightToLeft'
    
    class ShapeTextOrientation:
        horizontal = 'Horizontal'
        vertical = 'Vertical'
        vertical270 = 'Vertical270'
        wordArtVertical = 'WordArtVertical'
        eastAsianVertical = 'EastAsianVertical'
        mongolianVertical = 'MongolianVertical'
        wordArtVerticalRTL = 'WordArtVerticalRTL'
    
    class ShapeAutoSize:
        autoSizeNone = 'AutoSizeNone'
        autoSizeTextToFitShape = 'AutoSizeTextToFitShape'
        autoSizeShapeToFitText = 'AutoSizeShapeToFitText'
        autoSizeMixed = 'AutoSizeMixed'
    
    class CloseBehavior:
        save = 'Save'
        skipSave = 'SkipSave'
    
    class SaveBehavior:
        save = 'Save'
        prompt = 'Prompt'
    
    class SlicerSortType:
        dataSourceOrder = 'DataSourceOrder'
        ascending = 'Ascending'
        descending = 'Descending'
    
    class RibbonTab:
        others = 'Others'
        home = 'Home'
        insert = 'Insert'
        draw = 'Draw'
        pageLayout = 'PageLayout'
        formulas = 'Formulas'
        data = 'Data'
        review = 'Review'
        view = 'View'
        developer = 'Developer'
        addIns = 'AddIns'
        help = 'Help'
    
    class NumberFormatCategory:
        general = 'General'
        number = 'Number'
        currency = 'Currency'
        accounting = 'Accounting'
        date = 'Date'
        time = 'Time'
        percentage = 'Percentage'
        fraction = 'Fraction'
        scientific = 'Scientific'
        text = 'Text'
        special = 'Special'
        custom = 'Custom'
    
    class WindowState:
        maximized = 'maximized'
        minimized = 'minimized'
        normal = 'normal'
    
    class WindowView:
        normalView = 'normalView'
        pageBreakPreview = 'pageBreakPreview'
        pageLayoutView = 'pageLayoutView'
    
    class WindowType:
        chartAsWindow = 'chartAsWindow'
        chartInPlace = 'chartInPlace'
        clipboard = 'clipboard'
        workbook = 'workbook'
    
    class ScrollWorkbookTabPosition:
        first = 'First'
        last = 'Last'
    
    class ErrorCodes:
        accessDenied = 'AccessDenied'
        apiNotFound = 'ApiNotFound'
        conflict = 'Conflict'
        emptyChartSeries = 'EmptyChartSeries'
        filteredRangeConflict = 'FilteredRangeConflict'
        formulaLengthExceedsLimit = 'FormulaLengthExceedsLimit'
        generalException = 'GeneralException'
        inactiveWorkbook = 'InactiveWorkbook'
        insertDeleteConflict = 'InsertDeleteConflict'
        invalidArgument = 'InvalidArgument'
        invalidBinding = 'InvalidBinding'
        invalidOperation = 'InvalidOperation'
        invalidReference = 'InvalidReference'
        invalidSelection = 'InvalidSelection'
        itemAlreadyExists = 'ItemAlreadyExists'
        itemNotFound = 'ItemNotFound'
        mergedRangeConflict = 'MergedRangeConflict'
        nonBlankCellOffSheet = 'NonBlankCellOffSheet'
        notImplemented = 'NotImplemented'
        openWorkbookLinksBlocked = 'OpenWorkbookLinksBlocked'
        operationCellsExceedLimit = 'OperationCellsExceedLimit'
        pivotTableRangeConflict = 'PivotTableRangeConflict'
        powerQueryRefreshResourceChallenge = 'PowerQueryRefreshResourceChallenge'
        rangeExceedsLimit = 'RangeExceedsLimit'
        rangeImageExceedsLimit = 'RangeImageExceedsLimit'
        refreshWorkbookLinksBlocked = 'RefreshWorkbookLinksBlocked'
        requestAborted = 'RequestAborted'
        responsePayloadSizeLimitExceeded = 'ResponsePayloadSizeLimitExceeded'
        unsupportedFeature = 'UnsupportedFeature'
        unsupportedFillType = 'UnsupportedFillType'
        unsupportedOperation = 'UnsupportedOperation'
        unsupportedSheet = 'UnsupportedSheet'
        invalidOperationInCellEditMode = 'InvalidOperationInCellEditMode'
    
    class UnknownCellControl:
        pass
    
    class EmptyCellControl:
        pass
    
    class MixedCellControl:
        pass
    
    class CheckboxCellControl:
        pass
    
    class ArrayCellValue:
        pass
    
    class BasicCompactLayout:
        pass
    
    class BasicCardLayout:
        pass
    
    class BasicViewLayouts:
        pass
    
    class BlockedErrorCellValue:
        pass
    
    class BooleanCellValue:
        pass
    
    class BusyErrorCellValue:
        pass
    
    class CalcErrorCellValue:
        pass
    
    class CardLayoutPropertyReference:
        pass
    
    class CardLayoutSectionStandardProperties:
        pass
    
    class CardLayoutListSection:
        pass
    
    class CardLayoutTableSection:
        pass
    
    class CardLayoutTwoColumnSection:
        pass
    
    class CardLayoutStandardProperties:
        pass
    
    class EntityCompactLayout:
        pass
    
    class JavaScriptCustomFunctionReferenceCellValue:
        pass
    
    class ReferenceCellValue:
        pass
    
    class RootReferenceCellValue:
        pass
    
    class CellValueExtraProperties:
        pass
    
    class CellValueAttributionAttributes:
        pass
    
    class PlaceholderErrorCellValue:
        pass
    
    class CellValueProviderAttributes:
        pass
    
    class CellValuePropertyMetadata:
        pass
    
    class CellValuePropertyMetadataExclusions:
        pass
    
    class ConnectErrorCellValue:
        pass
    
    class Div0ErrorCellValue:
        pass
    
    class DoubleCellValue:
        pass
    
    class EmptyCellValue:
        pass
    
    class EntityPropertyExtraProperties:
        pass
    
    class EntityCellValue:
        pass
    
    class EntityViewLayouts:
        pass
    
    class EntityCardLayout:
        pass
    
    class ExternalErrorCellValue:
        pass
    
    class FieldErrorCellValue:
        pass
    
    class FormattedNumberCellValue:
        pass
    
    class GettingDataErrorCellValue:
        pass
    
    class LinkedEntityLoadServiceRequest:
        pass
    
    class LinkedEntityLoadServiceResult:
        pass
    
    class LinkedEntityId:
        pass
    
    class LinkedEntityIdCulture:
        pass
    
    class LinkedEntityCellValue:
        pass
    
    class NotAvailableErrorCellValue:
        pass
    
    class NameErrorCellValue:
        pass
    
    class NullErrorCellValue:
        pass
    
    class NumErrorCellValue:
        pass
    
    class RefErrorCellValue:
        pass
    
    class SpillErrorCellValue:
        pass
    
    class StringCellValue:
        pass
    
    class ValueErrorCellValue:
        pass
    
    class ValueTypeNotAvailableCellValue:
        pass
    
    class WebImageCellValue:
        pass
    
    class CellPropertiesLoadOptions:
        pass
    
    class RowPropertiesLoadOptions:
        pass
    
    class ColumnPropertiesLoadOptions:
        pass
    
    class CellPropertiesFormatLoadOptions:
        pass
    
    class SettableCellProperties:
        pass
    
    class CellProperties:
        pass
    
    class SettableRowProperties:
        pass
    
    class RowProperties:
        pass
    
    class SettableColumnProperties:
        pass
    
    class ColumnProperties:
        pass
    
    class CellPropertiesFormat:
        pass
    
    class ThreeArrowsSet:
        pass
    
    class ThreeArrowsGraySet:
        pass
    
    class ThreeFlagsSet:
        pass
    
    class ThreeTrafficLights1Set:
        pass
    
    class ThreeTrafficLights2Set:
        pass
    
    class ThreeSignsSet:
        pass
    
    class ThreeSymbolsSet:
        pass
    
    class ThreeSymbols2Set:
        pass
    
    class FourArrowsSet:
        pass
    
    class FourArrowsGraySet:
        pass
    
    class FourRedToBlackSet:
        pass
    
    class FourRatingSet:
        pass
    
    class FourTrafficLightsSet:
        pass
    
    class FiveArrowsSet:
        pass
    
    class FiveArrowsGraySet:
        pass
    
    class FiveRatingSet:
        pass
    
    class FiveQuartersSet:
        pass
    
    class ThreeStarsSet:
        pass
    
    class ThreeTrianglesSet:
        pass
    
    class FiveBoxesSet:
        pass
    
    class IconCollections:
        pass
    
    class Session:
        pass
    
    class RequestContext:
        pass
    
    class RunOptions:
        pass
    
    class AllowEditRange:
        pass
    
    class AllowEditRangeCollection:
        pass
    
    class AllowEditRangeOptions:
        pass
    
    class WorksheetMovedEventArgs:
        pass
    
    class WorksheetNameChangedEventArgs:
        pass
    
    class WorksheetVisibilityChangedEventArgs:
        pass
    
    class Query:
        pass
    
    class QueryCollection:
        pass
    
    class LinkedWorkbook:
        pass
    
    class LinkedWorkbookCollection:
        pass
    
    class PivotDateFilter:
        pass
    
    class PivotFilters:
        pass
    
    class PivotLabelFilter:
        pass
    
    class PivotManualFilter:
        pass
    
    class PivotValueFilter:
        pass
    
    class BindingSelectionChangedEventArgs:
        pass
    
    class BindingDataChangedEventArgs:
        pass
    
    class SelectionChangedEventArgs:
        pass
    
    class SettingsChangedEventArgs:
        pass
    
    class WorkbookActivatedEventArgs:
        pass
    
    class WorkbookAutoSaveSettingChangedEventArgs:
        pass
    
    class ChangeDirectionState:
        pass
    
    class ChangedEventDetail:
        pass
    
    class WorksheetChangedEventArgs:
        pass
    
    class WorksheetFormatChangedEventArgs:
        pass
    
    class WorksheetRowHiddenChangedEventArgs:
        pass
    
    class TableChangedEventArgs:
        pass
    
    class WorksheetFormulaChangedEventArgs:
        pass
    
    class FormulaChangedEventDetail:
        pass
    
    class WorksheetProtectionChangedEventArgs:
        pass
    
    class WorksheetActivatedEventArgs:
        pass
    
    class WorksheetDeactivatedEventArgs:
        pass
    
    class WorksheetRowSortedEventArgs:
        pass
    
    class WorksheetColumnSortedEventArgs:
        pass
    
    class WorksheetSelectionChangedEventArgs:
        pass
    
    class WorksheetSingleClickedEventArgs:
        pass
    
    class TableSelectionChangedEventArgs:
        pass
    
    class WorksheetAddedEventArgs:
        pass
    
    class WorksheetDeletedEventArgs:
        pass
    
    class ChartAddedEventArgs:
        pass
    
    class ChartActivatedEventArgs:
        pass
    
    class ChartDeactivatedEventArgs:
        pass
    
    class ChartDeletedEventArgs:
        pass
    
    class WorksheetCalculatedEventArgs:
        pass
    
    class TableAddedEventArgs:
        pass
    
    class TableDeletedEventArgs:
        pass
    
    class CommentAddedEventArgs:
        pass
    
    class CommentDeletedEventArgs:
        pass
    
    class CommentChangedEventArgs:
        pass
    
    class CommentDetail:
        pass
    
    class ShapeActivatedEventArgs:
        pass
    
    class ShapeDeactivatedEventArgs:
        pass
    
    class Runtime:
        pass
    
    class Application:
        pass
    
    class IterativeCalculation:
        pass
    
    class Workbook:
        pass
    
    class WorkbookProtection:
        pass
    
    class WorkbookCreated:
        pass
    
    class Worksheet:
        pass
    
    class CheckSpellingOptions:
        pass
    
    class WorksheetCollection:
        pass
    
    class WorksheetProtection:
        pass
    
    class WorksheetProtectionOptions:
        pass
    
    class WorksheetFreezePanes:
        pass
    
    class InsertWorksheetOptions:
        pass
    
    class Range:
        pass
    
    class RangeReference:
        pass
    
    class RangeHyperlink:
        pass
    
    class RangeAreas:
        pass
    
    class WorkbookRangeAreas:
        pass
    
    class SearchCriteria:
        pass
    
    class WorksheetSearchCriteria:
        pass
    
    class ReplaceCriteria:
        pass
    
    class CellPropertiesFillLoadOptions:
        pass
    
    class CellPropertiesFontLoadOptions:
        pass
    
    class CellPropertiesBorderLoadOptions:
        pass
    
    class RangeTextRun:
        pass
    
    class CellPropertiesProtection:
        pass
    
    class CellPropertiesFill:
        pass
    
    class CellPropertiesFont:
        pass
    
    class CellBorderCollection:
        pass
    
    class CellBorder:
        pass
    
    class RangeView:
        pass
    
    class RangeViewCollection:
        pass
    
    class SettingCollection:
        pass
    
    class Setting:
        pass
    
    class NamedItemCollection:
        pass
    
    class NamedItem:
        pass
    
    class NamedItemArrayValues:
        pass
    
    class Binding:
        pass
    
    class BindingCollection:
        pass
    
    class TableCollection:
        pass
    
    class TableScopedCollection:
        pass
    
    class Table:
        pass
    
    class TableColumnCollection:
        pass
    
    class TableColumn:
        pass
    
    class TableRowCollection:
        pass
    
    class TableRow:
        pass
    
    class DataValidation:
        pass
    
    class DataValidationRule:
        pass
    
    class RemoveDuplicatesResult:
        pass
    
    class BasicDataValidation:
        pass
    
    class DateTimeDataValidation:
        pass
    
    class ListDataValidation:
        pass
    
    class CustomDataValidation:
        pass
    
    class DataValidationErrorAlert:
        pass
    
    class DataValidationPrompt:
        pass
    
    class RangeFormat:
        pass
    
    class FormatProtection:
        pass
    
    class RangeFill:
        pass
    
    class RangeBorder:
        pass
    
    class RangeBorderCollection:
        pass
    
    class RangeFont:
        pass
    
    class ChartCollection:
        pass
    
    class Chart:
        pass
    
    class ChartPivotOptions:
        pass
    
    class ChartAreaFormat:
        pass
    
    class ChartSeriesCollection:
        pass
    
    class ChartSeries:
        pass
    
    class ChartSeriesFormat:
        pass
    
    class ChartPointsCollection:
        pass
    
    class ChartPoint:
        pass
    
    class ChartPointFormat:
        pass
    
    class ChartAxes:
        pass
    
    class ChartAxis:
        pass
    
    class ChartAxisFormat:
        pass
    
    class ChartAxisTitle:
        pass
    
    class ChartAxisTitleFormat:
        pass
    
    class ChartDataLabels:
        pass
    
    class ChartDataLabel:
        pass
    
    class ChartDataLabelFormat:
        pass
    
    class ChartDataLabelAnchor:
        pass
    
    class ChartDataTable:
        pass
    
    class ChartDataTableFormat:
        pass
    
    class ChartErrorBars:
        pass
    
    class ChartErrorBarsFormat:
        pass
    
    class ChartGridlines:
        pass
    
    class ChartGridlinesFormat:
        pass
    
    class ChartLegend:
        pass
    
    class ChartLegendEntry:
        pass
    
    class ChartLegendEntryCollection:
        pass
    
    class ChartLegendFormat:
        pass
    
    class ChartMapOptions:
        pass
    
    class ChartTitle:
        pass
    
    class ChartFormatString:
        pass
    
    class ChartTitleFormat:
        pass
    
    class ChartFill:
        pass
    
    class ChartBorder:
        pass
    
    class ChartBinOptions:
        pass
    
    class ChartBoxwhiskerOptions:
        pass
    
    class ChartLineFormat:
        pass
    
    class ChartFont:
        pass
    
    class ChartTrendline:
        pass
    
    class ChartTrendlineCollection:
        pass
    
    class ChartTrendlineFormat:
        pass
    
    class ChartTrendlineLabel:
        pass
    
    class ChartTrendlineLabelFormat:
        pass
    
    class ChartPlotArea:
        pass
    
    class ChartPlotAreaFormat:
        pass
    
    class ChartLeaderLines:
        pass
    
    class ChartLeaderLinesFormat:
        pass
    
    class RangeSort:
        pass
    
    class TableSort:
        pass
    
    class SortField:
        pass
    
    class Filter:
        pass
    
    class FilterCriteria:
        pass
    
    class FilterDatetime:
        pass
    
    class AutoFilter:
        pass
    
    class CultureInfo:
        pass
    
    class NumberFormatInfo:
        pass
    
    class DatetimeFormatInfo:
        pass
    
    class Icon:
        pass
    
    class CustomXmlPartScopedCollection:
        pass
    
    class CustomXmlPartCollection:
        pass
    
    class CustomXmlPart:
        pass
    
    class PivotTableScopedCollection:
        pass
    
    class PivotTableCollection:
        pass
    
    class PivotTable:
        pass
    
    class PivotLayout:
        pass
    
    class PivotHierarchyCollection:
        pass
    
    class PivotHierarchy:
        pass
    
    class RowColumnPivotHierarchyCollection:
        pass
    
    class RowColumnPivotHierarchy:
        pass
    
    class FilterPivotHierarchyCollection:
        pass
    
    class FilterPivotHierarchy:
        pass
    
    class DataPivotHierarchyCollection:
        pass
    
    class DataPivotHierarchy:
        pass
    
    class ShowAsRule:
        pass
    
    class PivotFieldCollection:
        pass
    
    class PivotField:
        pass
    
    class PivotItemCollection:
        pass
    
    class PivotItem:
        pass
    
    class Subtotals:
        pass
    
    class WorksheetCustomProperty:
        pass
    
    class WorksheetCustomPropertyCollection:
        pass
    
    class DocumentProperties:
        pass
    
    class CustomProperty:
        pass
    
    class CustomPropertyCollection:
        pass
    
    class ConditionalFormatCollection:
        pass
    
    class ConditionalFormat:
        pass
    
    class DataBarConditionalFormat:
        pass
    
    class ConditionalDataBarPositiveFormat:
        pass
    
    class ConditionalDataBarNegativeFormat:
        pass
    
    class ConditionalDataBarRule:
        pass
    
    class CustomConditionalFormat:
        pass
    
    class ConditionalFormatRule:
        pass
    
    class IconSetConditionalFormat:
        pass
    
    class ConditionalIconCriterion:
        pass
    
    class ColorScaleConditionalFormat:
        pass
    
    class ConditionalColorScaleCriteria:
        pass
    
    class ConditionalColorScaleCriterion:
        pass
    
    class TopBottomConditionalFormat:
        pass
    
    class ConditionalTopBottomRule:
        pass
    
    class PresetCriteriaConditionalFormat:
        pass
    
    class ConditionalPresetCriteriaRule:
        pass
    
    class TextConditionalFormat:
        pass
    
    class ConditionalTextComparisonRule:
        pass
    
    class CellValueConditionalFormat:
        pass
    
    class ConditionalCellValueRule:
        pass
    
    class ConditionalRangeFormat:
        pass
    
    class ConditionalRangeFont:
        pass
    
    class ConditionalRangeFill:
        pass
    
    class ConditionalRangeBorder:
        pass
    
    class ConditionalRangeBorderCollection:
        pass
    
    class CustomFunctionManager:
        pass
    
    class CustomFunctionVisibilityOptions:
        pass
    
    class Style:
        pass
    
    class StyleCollection:
        pass
    
    class TableStyleCollection:
        pass
    
    class TableStyle:
        pass
    
    class PivotTableStyleCollection:
        pass
    
    class PivotTableStyle:
        pass
    
    class SlicerStyleCollection:
        pass
    
    class SlicerStyle:
        pass
    
    class TimelineStyleCollection:
        pass
    
    class TimelineStyle:
        pass
    
    class PageLayout:
        pass
    
    class PageLayoutZoomOptions:
        pass
    
    class PageLayoutMarginOptions:
        pass
    
    class HeaderFooter:
        pass
    
    class HeaderFooterGroup:
        pass
    
    class HeaderFooterPicture:
        pass
    
    class PageBreak:
        pass
    
    class PageBreakCollection:
        pass
    
    class DataConnectionCollection:
        pass
    
    class RangeCollection:
        pass
    
    class RangeAreasCollection:
        pass
    
    class CommentMention:
        pass
    
    class CommentRichContent:
        pass
    
    class CommentCollection:
        pass
    
    class Comment:
        pass
    
    class CommentReplyCollection:
        pass
    
    class CommentReply:
        pass
    
    class ShapeCollection:
        pass
    
    class Shape:
        pass
    
    class GeometricShape:
        pass
    
    class Image:
        pass
    
    class ShapeGroup:
        pass
    
    class GroupShapeCollection:
        pass
    
    class Line:
        pass
    
    class ShapeFill:
        pass
    
    class ShapeLineFormat:
        pass
    
    class TextFrame:
        pass
    
    class TextRange:
        pass
    
    class ShapeFont:
        pass
    
    class Slicer:
        pass
    
    class SlicerCollection:
        pass
    
    class SlicerItem:
        pass
    
    class SlicerItemCollection:
        pass
    
    class LinkedEntityDataDomain:
        pass
    
    class LinkedEntityDataDomainAddedEventArgs:
        pass
    
    class LinkedEntityDataDomainCollection:
        pass
    
    class LinkedEntityDataDomainCreateOptions:
        pass
    
    class LinkedEntityDataDomainRefreshCompletedEventArgs:
        pass
    
    class LinkedEntityDataDomainRefreshModeChangedEventArgs:
        pass
    
    class NamedSheetView:
        pass
    
    class NamedSheetViewCollection:
        pass
    
    class NoteCollection:
        pass
    
    class Note:
        pass
    
    class Window:
        pass
    
    class WindowCollection:
        pass
    
    class Pane:
        pass
    
    class PaneCollection:
        pass
    
    class FunctionResult:
        pass
    
    class Functions:
        pass
    
    class Interfaces:
        
        class CollectionLoadOptions:
            pass
        
        class AllowEditRangeUpdateData:
            pass
        
        class AllowEditRangeCollectionUpdateData:
            pass
        
        class QueryCollectionUpdateData:
            pass
        
        class LinkedWorkbookCollectionUpdateData:
            pass
        
        class RuntimeUpdateData:
            pass
        
        class ApplicationUpdateData:
            pass
        
        class IterativeCalculationUpdateData:
            pass
        
        class WorkbookUpdateData:
            pass
        
        class WorksheetUpdateData:
            pass
        
        class WorksheetCollectionUpdateData:
            pass
        
        class RangeUpdateData:
            pass
        
        class RangeAreasUpdateData:
            pass
        
        class RangeViewUpdateData:
            pass
        
        class RangeViewCollectionUpdateData:
            pass
        
        class SettingCollectionUpdateData:
            pass
        
        class SettingUpdateData:
            pass
        
        class NamedItemCollectionUpdateData:
            pass
        
        class NamedItemUpdateData:
            pass
        
        class BindingCollectionUpdateData:
            pass
        
        class TableCollectionUpdateData:
            pass
        
        class TableScopedCollectionUpdateData:
            pass
        
        class TableUpdateData:
            pass
        
        class TableColumnCollectionUpdateData:
            pass
        
        class TableColumnUpdateData:
            pass
        
        class TableRowCollectionUpdateData:
            pass
        
        class TableRowUpdateData:
            pass
        
        class DataValidationUpdateData:
            pass
        
        class RangeFormatUpdateData:
            pass
        
        class FormatProtectionUpdateData:
            pass
        
        class RangeFillUpdateData:
            pass
        
        class RangeBorderUpdateData:
            pass
        
        class RangeBorderCollectionUpdateData:
            pass
        
        class RangeFontUpdateData:
            pass
        
        class ChartCollectionUpdateData:
            pass
        
        class ChartUpdateData:
            pass
        
        class ChartPivotOptionsUpdateData:
            pass
        
        class ChartAreaFormatUpdateData:
            pass
        
        class ChartSeriesCollectionUpdateData:
            pass
        
        class ChartSeriesUpdateData:
            pass
        
        class ChartSeriesFormatUpdateData:
            pass
        
        class ChartPointsCollectionUpdateData:
            pass
        
        class ChartPointUpdateData:
            pass
        
        class ChartPointFormatUpdateData:
            pass
        
        class ChartAxesUpdateData:
            pass
        
        class ChartAxisUpdateData:
            pass
        
        class ChartAxisFormatUpdateData:
            pass
        
        class ChartAxisTitleUpdateData:
            pass
        
        class ChartAxisTitleFormatUpdateData:
            pass
        
        class ChartDataLabelsUpdateData:
            pass
        
        class ChartDataLabelUpdateData:
            pass
        
        class ChartDataLabelFormatUpdateData:
            pass
        
        class ChartDataLabelAnchorUpdateData:
            pass
        
        class ChartDataTableUpdateData:
            pass
        
        class ChartDataTableFormatUpdateData:
            pass
        
        class ChartErrorBarsUpdateData:
            pass
        
        class ChartErrorBarsFormatUpdateData:
            pass
        
        class ChartGridlinesUpdateData:
            pass
        
        class ChartGridlinesFormatUpdateData:
            pass
        
        class ChartLegendUpdateData:
            pass
        
        class ChartLegendEntryUpdateData:
            pass
        
        class ChartLegendEntryCollectionUpdateData:
            pass
        
        class ChartLegendFormatUpdateData:
            pass
        
        class ChartMapOptionsUpdateData:
            pass
        
        class ChartTitleUpdateData:
            pass
        
        class ChartFormatStringUpdateData:
            pass
        
        class ChartTitleFormatUpdateData:
            pass
        
        class ChartBorderUpdateData:
            pass
        
        class ChartBinOptionsUpdateData:
            pass
        
        class ChartBoxwhiskerOptionsUpdateData:
            pass
        
        class ChartLineFormatUpdateData:
            pass
        
        class ChartFontUpdateData:
            pass
        
        class ChartTrendlineUpdateData:
            pass
        
        class ChartTrendlineCollectionUpdateData:
            pass
        
        class ChartTrendlineFormatUpdateData:
            pass
        
        class ChartTrendlineLabelUpdateData:
            pass
        
        class ChartTrendlineLabelFormatUpdateData:
            pass
        
        class ChartPlotAreaUpdateData:
            pass
        
        class ChartPlotAreaFormatUpdateData:
            pass
        
        class ChartLeaderLinesUpdateData:
            pass
        
        class ChartLeaderLinesFormatUpdateData:
            pass
        
        class CustomXmlPartScopedCollectionUpdateData:
            pass
        
        class CustomXmlPartCollectionUpdateData:
            pass
        
        class PivotTableScopedCollectionUpdateData:
            pass
        
        class PivotTableCollectionUpdateData:
            pass
        
        class PivotTableUpdateData:
            pass
        
        class PivotLayoutUpdateData:
            pass
        
        class PivotHierarchyCollectionUpdateData:
            pass
        
        class PivotHierarchyUpdateData:
            pass
        
        class RowColumnPivotHierarchyCollectionUpdateData:
            pass
        
        class RowColumnPivotHierarchyUpdateData:
            pass
        
        class FilterPivotHierarchyCollectionUpdateData:
            pass
        
        class FilterPivotHierarchyUpdateData:
            pass
        
        class DataPivotHierarchyCollectionUpdateData:
            pass
        
        class DataPivotHierarchyUpdateData:
            pass
        
        class PivotFieldCollectionUpdateData:
            pass
        
        class PivotFieldUpdateData:
            pass
        
        class PivotItemCollectionUpdateData:
            pass
        
        class PivotItemUpdateData:
            pass
        
        class WorksheetCustomPropertyUpdateData:
            pass
        
        class WorksheetCustomPropertyCollectionUpdateData:
            pass
        
        class DocumentPropertiesUpdateData:
            pass
        
        class CustomPropertyUpdateData:
            pass
        
        class CustomPropertyCollectionUpdateData:
            pass
        
        class ConditionalFormatCollectionUpdateData:
            pass
        
        class ConditionalFormatUpdateData:
            pass
        
        class DataBarConditionalFormatUpdateData:
            pass
        
        class ConditionalDataBarPositiveFormatUpdateData:
            pass
        
        class ConditionalDataBarNegativeFormatUpdateData:
            pass
        
        class CustomConditionalFormatUpdateData:
            pass
        
        class ConditionalFormatRuleUpdateData:
            pass
        
        class IconSetConditionalFormatUpdateData:
            pass
        
        class ColorScaleConditionalFormatUpdateData:
            pass
        
        class TopBottomConditionalFormatUpdateData:
            pass
        
        class PresetCriteriaConditionalFormatUpdateData:
            pass
        
        class TextConditionalFormatUpdateData:
            pass
        
        class CellValueConditionalFormatUpdateData:
            pass
        
        class ConditionalRangeFormatUpdateData:
            pass
        
        class ConditionalRangeFontUpdateData:
            pass
        
        class ConditionalRangeFillUpdateData:
            pass
        
        class ConditionalRangeBorderUpdateData:
            pass
        
        class ConditionalRangeBorderCollectionUpdateData:
            pass
        
        class StyleUpdateData:
            pass
        
        class StyleCollectionUpdateData:
            pass
        
        class TableStyleCollectionUpdateData:
            pass
        
        class TableStyleUpdateData:
            pass
        
        class PivotTableStyleCollectionUpdateData:
            pass
        
        class PivotTableStyleUpdateData:
            pass
        
        class SlicerStyleCollectionUpdateData:
            pass
        
        class SlicerStyleUpdateData:
            pass
        
        class TimelineStyleCollectionUpdateData:
            pass
        
        class TimelineStyleUpdateData:
            pass
        
        class PageLayoutUpdateData:
            pass
        
        class HeaderFooterUpdateData:
            pass
        
        class HeaderFooterGroupUpdateData:
            pass
        
        class HeaderFooterPictureUpdateData:
            pass
        
        class PageBreakCollectionUpdateData:
            pass
        
        class RangeCollectionUpdateData:
            pass
        
        class RangeAreasCollectionUpdateData:
            pass
        
        class CommentCollectionUpdateData:
            pass
        
        class CommentUpdateData:
            pass
        
        class CommentReplyCollectionUpdateData:
            pass
        
        class CommentReplyUpdateData:
            pass
        
        class ShapeCollectionUpdateData:
            pass
        
        class ShapeUpdateData:
            pass
        
        class ImageUpdateData:
            pass
        
        class GroupShapeCollectionUpdateData:
            pass
        
        class LineUpdateData:
            pass
        
        class ShapeFillUpdateData:
            pass
        
        class ShapeLineFormatUpdateData:
            pass
        
        class TextFrameUpdateData:
            pass
        
        class TextRangeUpdateData:
            pass
        
        class ShapeFontUpdateData:
            pass
        
        class SlicerUpdateData:
            pass
        
        class SlicerCollectionUpdateData:
            pass
        
        class SlicerItemUpdateData:
            pass
        
        class SlicerItemCollectionUpdateData:
            pass
        
        class LinkedEntityDataDomainUpdateData:
            pass
        
        class LinkedEntityDataDomainCollectionUpdateData:
            pass
        
        class NamedSheetViewUpdateData:
            pass
        
        class NamedSheetViewCollectionUpdateData:
            pass
        
        class NoteCollectionUpdateData:
            pass
        
        class NoteUpdateData:
            pass
        
        class WindowUpdateData:
            pass
        
        class WindowCollectionUpdateData:
            pass
        
        class PaneCollectionUpdateData:
            pass
        
        class AllowEditRangeData:
            pass
        
        class AllowEditRangeCollectionData:
            pass
        
        class QueryData:
            pass
        
        class QueryCollectionData:
            pass
        
        class LinkedWorkbookData:
            pass
        
        class LinkedWorkbookCollectionData:
            pass
        
        class RuntimeData:
            pass
        
        class ApplicationData:
            pass
        
        class IterativeCalculationData:
            pass
        
        class WorkbookData:
            pass
        
        class WorkbookProtectionData:
            pass
        
        class WorkbookCreatedData:
            pass
        
        class WorksheetData:
            pass
        
        class WorksheetCollectionData:
            pass
        
        class WorksheetProtectionData:
            pass
        
        class RangeData:
            pass
        
        class RangeAreasData:
            pass
        
        class WorkbookRangeAreasData:
            pass
        
        class RangeViewData:
            pass
        
        class RangeViewCollectionData:
            pass
        
        class SettingCollectionData:
            pass
        
        class SettingData:
            pass
        
        class NamedItemCollectionData:
            pass
        
        class NamedItemData:
            pass
        
        class NamedItemArrayValuesData:
            pass
        
        class BindingData:
            pass
        
        class BindingCollectionData:
            pass
        
        class TableCollectionData:
            pass
        
        class TableScopedCollectionData:
            pass
        
        class TableData:
            pass
        
        class TableColumnCollectionData:
            pass
        
        class TableColumnData:
            pass
        
        class TableRowCollectionData:
            pass
        
        class TableRowData:
            pass
        
        class DataValidationData:
            pass
        
        class RemoveDuplicatesResultData:
            pass
        
        class RangeFormatData:
            pass
        
        class FormatProtectionData:
            pass
        
        class RangeFillData:
            pass
        
        class RangeBorderData:
            pass
        
        class RangeBorderCollectionData:
            pass
        
        class RangeFontData:
            pass
        
        class ChartCollectionData:
            pass
        
        class ChartData:
            pass
        
        class ChartPivotOptionsData:
            pass
        
        class ChartAreaFormatData:
            pass
        
        class ChartSeriesCollectionData:
            pass
        
        class ChartSeriesData:
            pass
        
        class ChartSeriesFormatData:
            pass
        
        class ChartPointsCollectionData:
            pass
        
        class ChartPointData:
            pass
        
        class ChartPointFormatData:
            pass
        
        class ChartAxesData:
            pass
        
        class ChartAxisData:
            pass
        
        class ChartAxisFormatData:
            pass
        
        class ChartAxisTitleData:
            pass
        
        class ChartAxisTitleFormatData:
            pass
        
        class ChartDataLabelsData:
            pass
        
        class ChartDataLabelData:
            pass
        
        class ChartDataLabelFormatData:
            pass
        
        class ChartDataLabelAnchorData:
            pass
        
        class ChartDataTableData:
            pass
        
        class ChartDataTableFormatData:
            pass
        
        class ChartErrorBarsData:
            pass
        
        class ChartErrorBarsFormatData:
            pass
        
        class ChartGridlinesData:
            pass
        
        class ChartGridlinesFormatData:
            pass
        
        class ChartLegendData:
            pass
        
        class ChartLegendEntryData:
            pass
        
        class ChartLegendEntryCollectionData:
            pass
        
        class ChartLegendFormatData:
            pass
        
        class ChartMapOptionsData:
            pass
        
        class ChartTitleData:
            pass
        
        class ChartFormatStringData:
            pass
        
        class ChartTitleFormatData:
            pass
        
        class ChartBorderData:
            pass
        
        class ChartBinOptionsData:
            pass
        
        class ChartBoxwhiskerOptionsData:
            pass
        
        class ChartLineFormatData:
            pass
        
        class ChartFontData:
            pass
        
        class ChartTrendlineData:
            pass
        
        class ChartTrendlineCollectionData:
            pass
        
        class ChartTrendlineFormatData:
            pass
        
        class ChartTrendlineLabelData:
            pass
        
        class ChartTrendlineLabelFormatData:
            pass
        
        class ChartPlotAreaData:
            pass
        
        class ChartPlotAreaFormatData:
            pass
        
        class ChartLeaderLinesData:
            pass
        
        class ChartLeaderLinesFormatData:
            pass
        
        class TableSortData:
            pass
        
        class FilterData:
            pass
        
        class AutoFilterData:
            pass
        
        class CultureInfoData:
            pass
        
        class NumberFormatInfoData:
            pass
        
        class DatetimeFormatInfoData:
            pass
        
        class CustomXmlPartScopedCollectionData:
            pass
        
        class CustomXmlPartCollectionData:
            pass
        
        class CustomXmlPartData:
            pass
        
        class PivotTableScopedCollectionData:
            pass
        
        class PivotTableCollectionData:
            pass
        
        class PivotTableData:
            pass
        
        class PivotLayoutData:
            pass
        
        class PivotHierarchyCollectionData:
            pass
        
        class PivotHierarchyData:
            pass
        
        class RowColumnPivotHierarchyCollectionData:
            pass
        
        class RowColumnPivotHierarchyData:
            pass
        
        class FilterPivotHierarchyCollectionData:
            pass
        
        class FilterPivotHierarchyData:
            pass
        
        class DataPivotHierarchyCollectionData:
            pass
        
        class DataPivotHierarchyData:
            pass
        
        class PivotFieldCollectionData:
            pass
        
        class PivotFieldData:
            pass
        
        class PivotItemCollectionData:
            pass
        
        class PivotItemData:
            pass
        
        class WorksheetCustomPropertyData:
            pass
        
        class WorksheetCustomPropertyCollectionData:
            pass
        
        class DocumentPropertiesData:
            pass
        
        class CustomPropertyData:
            pass
        
        class CustomPropertyCollectionData:
            pass
        
        class ConditionalFormatCollectionData:
            pass
        
        class ConditionalFormatData:
            pass
        
        class DataBarConditionalFormatData:
            pass
        
        class ConditionalDataBarPositiveFormatData:
            pass
        
        class ConditionalDataBarNegativeFormatData:
            pass
        
        class CustomConditionalFormatData:
            pass
        
        class ConditionalFormatRuleData:
            pass
        
        class IconSetConditionalFormatData:
            pass
        
        class ColorScaleConditionalFormatData:
            pass
        
        class TopBottomConditionalFormatData:
            pass
        
        class PresetCriteriaConditionalFormatData:
            pass
        
        class TextConditionalFormatData:
            pass
        
        class CellValueConditionalFormatData:
            pass
        
        class ConditionalRangeFormatData:
            pass
        
        class ConditionalRangeFontData:
            pass
        
        class ConditionalRangeFillData:
            pass
        
        class ConditionalRangeBorderData:
            pass
        
        class ConditionalRangeBorderCollectionData:
            pass
        
        class CustomFunctionManagerData:
            pass
        
        class StyleData:
            pass
        
        class StyleCollectionData:
            pass
        
        class TableStyleCollectionData:
            pass
        
        class TableStyleData:
            pass
        
        class PivotTableStyleCollectionData:
            pass
        
        class PivotTableStyleData:
            pass
        
        class SlicerStyleCollectionData:
            pass
        
        class SlicerStyleData:
            pass
        
        class TimelineStyleCollectionData:
            pass
        
        class TimelineStyleData:
            pass
        
        class PageLayoutData:
            pass
        
        class HeaderFooterData:
            pass
        
        class HeaderFooterGroupData:
            pass
        
        class HeaderFooterPictureData:
            pass
        
        class PageBreakData:
            pass
        
        class PageBreakCollectionData:
            pass
        
        class RangeCollectionData:
            pass
        
        class RangeAreasCollectionData:
            pass
        
        class CommentCollectionData:
            pass
        
        class CommentData:
            pass
        
        class CommentReplyCollectionData:
            pass
        
        class CommentReplyData:
            pass
        
        class ShapeCollectionData:
            pass
        
        class ShapeData:
            pass
        
        class GeometricShapeData:
            pass
        
        class ImageData:
            pass
        
        class ShapeGroupData:
            pass
        
        class GroupShapeCollectionData:
            pass
        
        class LineData:
            pass
        
        class ShapeFillData:
            pass
        
        class ShapeLineFormatData:
            pass
        
        class TextFrameData:
            pass
        
        class TextRangeData:
            pass
        
        class ShapeFontData:
            pass
        
        class SlicerData:
            pass
        
        class SlicerCollectionData:
            pass
        
        class SlicerItemData:
            pass
        
        class SlicerItemCollectionData:
            pass
        
        class LinkedEntityDataDomainData:
            pass
        
        class LinkedEntityDataDomainCollectionData:
            pass
        
        class NamedSheetViewData:
            pass
        
        class NamedSheetViewCollectionData:
            pass
        
        class NoteCollectionData:
            pass
        
        class NoteData:
            pass
        
        class WindowData:
            pass
        
        class WindowCollectionData:
            pass
        
        class PaneData:
            pass
        
        class PaneCollectionData:
            pass
        
        class FunctionResultData:
            pass
        
        class AllowEditRangeLoadOptions:
            pass
        
        class AllowEditRangeCollectionLoadOptions:
            pass
        
        class QueryLoadOptions:
            pass
        
        class QueryCollectionLoadOptions:
            pass
        
        class LinkedWorkbookLoadOptions:
            pass
        
        class LinkedWorkbookCollectionLoadOptions:
            pass
        
        class RuntimeLoadOptions:
            pass
        
        class ApplicationLoadOptions:
            pass
        
        class IterativeCalculationLoadOptions:
            pass
        
        class WorkbookLoadOptions:
            pass
        
        class WorkbookProtectionLoadOptions:
            pass
        
        class WorksheetLoadOptions:
            pass
        
        class WorksheetCollectionLoadOptions:
            pass
        
        class WorksheetProtectionLoadOptions:
            pass
        
        class RangeLoadOptions:
            pass
        
        class RangeAreasLoadOptions:
            pass
        
        class WorkbookRangeAreasLoadOptions:
            pass
        
        class RangeViewLoadOptions:
            pass
        
        class RangeViewCollectionLoadOptions:
            pass
        
        class SettingCollectionLoadOptions:
            pass
        
        class SettingLoadOptions:
            pass
        
        class NamedItemCollectionLoadOptions:
            pass
        
        class NamedItemLoadOptions:
            pass
        
        class NamedItemArrayValuesLoadOptions:
            pass
        
        class BindingLoadOptions:
            pass
        
        class BindingCollectionLoadOptions:
            pass
        
        class TableCollectionLoadOptions:
            pass
        
        class TableScopedCollectionLoadOptions:
            pass
        
        class TableLoadOptions:
            pass
        
        class TableColumnCollectionLoadOptions:
            pass
        
        class TableColumnLoadOptions:
            pass
        
        class TableRowCollectionLoadOptions:
            pass
        
        class TableRowLoadOptions:
            pass
        
        class DataValidationLoadOptions:
            pass
        
        class RemoveDuplicatesResultLoadOptions:
            pass
        
        class RangeFormatLoadOptions:
            pass
        
        class FormatProtectionLoadOptions:
            pass
        
        class RangeFillLoadOptions:
            pass
        
        class RangeBorderLoadOptions:
            pass
        
        class RangeBorderCollectionLoadOptions:
            pass
        
        class RangeFontLoadOptions:
            pass
        
        class ChartCollectionLoadOptions:
            pass
        
        class ChartLoadOptions:
            pass
        
        class ChartPivotOptionsLoadOptions:
            pass
        
        class ChartAreaFormatLoadOptions:
            pass
        
        class ChartSeriesCollectionLoadOptions:
            pass
        
        class ChartSeriesLoadOptions:
            pass
        
        class ChartSeriesFormatLoadOptions:
            pass
        
        class ChartPointsCollectionLoadOptions:
            pass
        
        class ChartPointLoadOptions:
            pass
        
        class ChartPointFormatLoadOptions:
            pass
        
        class ChartAxesLoadOptions:
            pass
        
        class ChartAxisLoadOptions:
            pass
        
        class ChartAxisFormatLoadOptions:
            pass
        
        class ChartAxisTitleLoadOptions:
            pass
        
        class ChartAxisTitleFormatLoadOptions:
            pass
        
        class ChartDataLabelsLoadOptions:
            pass
        
        class ChartDataLabelLoadOptions:
            pass
        
        class ChartDataLabelFormatLoadOptions:
            pass
        
        class ChartDataLabelAnchorLoadOptions:
            pass
        
        class ChartDataTableLoadOptions:
            pass
        
        class ChartDataTableFormatLoadOptions:
            pass
        
        class ChartErrorBarsLoadOptions:
            pass
        
        class ChartErrorBarsFormatLoadOptions:
            pass
        
        class ChartGridlinesLoadOptions:
            pass
        
        class ChartGridlinesFormatLoadOptions:
            pass
        
        class ChartLegendLoadOptions:
            pass
        
        class ChartLegendEntryLoadOptions:
            pass
        
        class ChartLegendEntryCollectionLoadOptions:
            pass
        
        class ChartLegendFormatLoadOptions:
            pass
        
        class ChartMapOptionsLoadOptions:
            pass
        
        class ChartTitleLoadOptions:
            pass
        
        class ChartFormatStringLoadOptions:
            pass
        
        class ChartTitleFormatLoadOptions:
            pass
        
        class ChartBorderLoadOptions:
            pass
        
        class ChartBinOptionsLoadOptions:
            pass
        
        class ChartBoxwhiskerOptionsLoadOptions:
            pass
        
        class ChartLineFormatLoadOptions:
            pass
        
        class ChartFontLoadOptions:
            pass
        
        class ChartTrendlineLoadOptions:
            pass
        
        class ChartTrendlineCollectionLoadOptions:
            pass
        
        class ChartTrendlineFormatLoadOptions:
            pass
        
        class ChartTrendlineLabelLoadOptions:
            pass
        
        class ChartTrendlineLabelFormatLoadOptions:
            pass
        
        class ChartPlotAreaLoadOptions:
            pass
        
        class ChartPlotAreaFormatLoadOptions:
            pass
        
        class ChartLeaderLinesLoadOptions:
            pass
        
        class ChartLeaderLinesFormatLoadOptions:
            pass
        
        class TableSortLoadOptions:
            pass
        
        class FilterLoadOptions:
            pass
        
        class AutoFilterLoadOptions:
            pass
        
        class CultureInfoLoadOptions:
            pass
        
        class NumberFormatInfoLoadOptions:
            pass
        
        class DatetimeFormatInfoLoadOptions:
            pass
        
        class CustomXmlPartScopedCollectionLoadOptions:
            pass
        
        class CustomXmlPartCollectionLoadOptions:
            pass
        
        class CustomXmlPartLoadOptions:
            pass
        
        class PivotTableScopedCollectionLoadOptions:
            pass
        
        class PivotTableCollectionLoadOptions:
            pass
        
        class PivotTableLoadOptions:
            pass
        
        class PivotLayoutLoadOptions:
            pass
        
        class PivotHierarchyCollectionLoadOptions:
            pass
        
        class PivotHierarchyLoadOptions:
            pass
        
        class RowColumnPivotHierarchyCollectionLoadOptions:
            pass
        
        class RowColumnPivotHierarchyLoadOptions:
            pass
        
        class FilterPivotHierarchyCollectionLoadOptions:
            pass
        
        class FilterPivotHierarchyLoadOptions:
            pass
        
        class DataPivotHierarchyCollectionLoadOptions:
            pass
        
        class DataPivotHierarchyLoadOptions:
            pass
        
        class PivotFieldCollectionLoadOptions:
            pass
        
        class PivotFieldLoadOptions:
            pass
        
        class PivotItemCollectionLoadOptions:
            pass
        
        class PivotItemLoadOptions:
            pass
        
        class WorksheetCustomPropertyLoadOptions:
            pass
        
        class WorksheetCustomPropertyCollectionLoadOptions:
            pass
        
        class DocumentPropertiesLoadOptions:
            pass
        
        class CustomPropertyLoadOptions:
            pass
        
        class CustomPropertyCollectionLoadOptions:
            pass
        
        class ConditionalFormatCollectionLoadOptions:
            pass
        
        class ConditionalFormatLoadOptions:
            pass
        
        class DataBarConditionalFormatLoadOptions:
            pass
        
        class ConditionalDataBarPositiveFormatLoadOptions:
            pass
        
        class ConditionalDataBarNegativeFormatLoadOptions:
            pass
        
        class CustomConditionalFormatLoadOptions:
            pass
        
        class ConditionalFormatRuleLoadOptions:
            pass
        
        class IconSetConditionalFormatLoadOptions:
            pass
        
        class ColorScaleConditionalFormatLoadOptions:
            pass
        
        class TopBottomConditionalFormatLoadOptions:
            pass
        
        class PresetCriteriaConditionalFormatLoadOptions:
            pass
        
        class TextConditionalFormatLoadOptions:
            pass
        
        class CellValueConditionalFormatLoadOptions:
            pass
        
        class ConditionalRangeFormatLoadOptions:
            pass
        
        class ConditionalRangeFontLoadOptions:
            pass
        
        class ConditionalRangeFillLoadOptions:
            pass
        
        class ConditionalRangeBorderLoadOptions:
            pass
        
        class ConditionalRangeBorderCollectionLoadOptions:
            pass
        
        class StyleLoadOptions:
            pass
        
        class StyleCollectionLoadOptions:
            pass
        
        class TableStyleCollectionLoadOptions:
            pass
        
        class TableStyleLoadOptions:
            pass
        
        class PivotTableStyleCollectionLoadOptions:
            pass
        
        class PivotTableStyleLoadOptions:
            pass
        
        class SlicerStyleCollectionLoadOptions:
            pass
        
        class SlicerStyleLoadOptions:
            pass
        
        class TimelineStyleCollectionLoadOptions:
            pass
        
        class TimelineStyleLoadOptions:
            pass
        
        class PageLayoutLoadOptions:
            pass
        
        class HeaderFooterLoadOptions:
            pass
        
        class HeaderFooterGroupLoadOptions:
            pass
        
        class HeaderFooterPictureLoadOptions:
            pass
        
        class PageBreakLoadOptions:
            pass
        
        class PageBreakCollectionLoadOptions:
            pass
        
        class RangeCollectionLoadOptions:
            pass
        
        class RangeAreasCollectionLoadOptions:
            pass
        
        class CommentCollectionLoadOptions:
            pass
        
        class CommentLoadOptions:
            pass
        
        class CommentReplyCollectionLoadOptions:
            pass
        
        class CommentReplyLoadOptions:
            pass
        
        class ShapeCollectionLoadOptions:
            pass
        
        class ShapeLoadOptions:
            pass
        
        class GeometricShapeLoadOptions:
            pass
        
        class ImageLoadOptions:
            pass
        
        class ShapeGroupLoadOptions:
            pass
        
        class GroupShapeCollectionLoadOptions:
            pass
        
        class LineLoadOptions:
            pass
        
        class ShapeFillLoadOptions:
            pass
        
        class ShapeLineFormatLoadOptions:
            pass
        
        class TextFrameLoadOptions:
            pass
        
        class TextRangeLoadOptions:
            pass
        
        class ShapeFontLoadOptions:
            pass
        
        class SlicerLoadOptions:
            pass
        
        class SlicerCollectionLoadOptions:
            pass
        
        class SlicerItemLoadOptions:
            pass
        
        class SlicerItemCollectionLoadOptions:
            pass
        
        class LinkedEntityDataDomainLoadOptions:
            pass
        
        class LinkedEntityDataDomainCollectionLoadOptions:
            pass
        
        class NamedSheetViewLoadOptions:
            pass
        
        class NamedSheetViewCollectionLoadOptions:
            pass
        
        class NoteCollectionLoadOptions:
            pass
        
        class NoteLoadOptions:
            pass
        
        class WindowLoadOptions:
            pass
        
        class WindowCollectionLoadOptions:
            pass
        
        class PaneLoadOptions:
            pass
        
        class PaneCollectionLoadOptions:
            pass
        
        class FunctionResultLoadOptions:
            pass

class Word:
    
    class CritiqueColorScheme:
        red = 'Red'
        green = 'Green'
        blue = 'Blue'
        lavender = 'Lavender'
        berry = 'Berry'
    
    class AnnotationState:
        created = 'Created'
        accepted = 'Accepted'
        rejected = 'Rejected'
    
    class XmlNodeType:
        element = 'Element'
        attribute = 'Attribute'
    
    class XmlValidationStatus:
        ok = 'Ok'
        custom = 'Custom'
    
    class XmlNodeLevel:
        inline = 'Inline'
        paragraph = 'Paragraph'
        row = 'Row'
        cell = 'Cell'
    
    class ApplyQuickStyleSet:
        sessionStart = 'SessionStart'
        template = 'Template'
    
    class ScreenSize:
        size544x376 = 'Size544x376'
        size640x480 = 'Size640x480'
        size720x512 = 'Size720x512'
        size800x600 = 'Size800x600'
        size1024x768 = 'Size1024x768'
        size1152x882 = 'Size1152x882'
        size1152x900 = 'Size1152x900'
        size1280x1024 = 'Size1280x1024'
        size1600x1200 = 'Size1600x1200'
        size1800x1440 = 'Size1800x1440'
        size1920x1200 = 'Size1920x1200'
    
    class TargetBrowser:
        v3 = 'V3'
        v4 = 'V4'
        ie4 = 'Ie4'
        ie5 = 'Ie5'
        ie6 = 'Ie6'
    
    class CalendarType:
        western = 'Western'
        arabic = 'Arabic'
        hebrew = 'Hebrew'
        taiwan = 'Taiwan'
        japan = 'Japan'
        thai = 'Thai'
        korean = 'Korean'
        sakaEra = 'SakaEra'
        translitEnglish = 'TranslitEnglish'
        translitFrench = 'TranslitFrench'
        umalqura = 'Umalqura'
    
    class ContentControlDateStorageFormat:
        text = 'Text'
        date = 'Date'
        dateTime = 'DateTime'
    
    class ChangeTrackingMode:
        off = 'Off'
        trackAll = 'TrackAll'
        trackMineOnly = 'TrackMineOnly'
    
    class ChangeTrackingVersion:
        original = 'Original'
        current = 'Current'
    
    class ChangeTrackingState:
        unknown = 'Unknown'
        normal = 'Normal'
        added = 'Added'
        deleted = 'Deleted'
    
    class TrackedChangeType:
        none = 'None'
        added = 'Added'
        deleted = 'Deleted'
        formatted = 'Formatted'
    
    class NoteItemType:
        footnote = 'Footnote'
        endnote = 'Endnote'
    
    class EventType:
        contentControlDeleted = 'ContentControlDeleted'
        contentControlSelectionChanged = 'ContentControlSelectionChanged'
        contentControlDataChanged = 'ContentControlDataChanged'
        contentControlAdded = 'ContentControlAdded'
        contentControlEntered = 'ContentControlEntered'
        contentControlExited = 'ContentControlExited'
        paragraphAdded = 'ParagraphAdded'
        paragraphChanged = 'ParagraphChanged'
        paragraphDeleted = 'ParagraphDeleted'
        annotationClicked = 'AnnotationClicked'
        annotationHovered = 'AnnotationHovered'
        annotationInserted = 'AnnotationInserted'
        annotationRemoved = 'AnnotationRemoved'
        annotationPopupAction = 'AnnotationPopupAction'
    
    class EventSource:
        local = 'Local'
        remote = 'Remote'
    
    class ContentControlType:
        unknown = 'Unknown'
        richTextInline = 'RichTextInline'
        richTextParagraphs = 'RichTextParagraphs'
        richTextTableCell = 'RichTextTableCell'
        richTextTableRow = 'RichTextTableRow'
        richTextTable = 'RichTextTable'
        plainTextInline = 'PlainTextInline'
        plainTextParagraph = 'PlainTextParagraph'
        picture = 'Picture'
        buildingBlockGallery = 'BuildingBlockGallery'
        checkBox = 'CheckBox'
        comboBox = 'ComboBox'
        dropDownList = 'DropDownList'
        datePicker = 'DatePicker'
        repeatingSection = 'RepeatingSection'
        richText = 'RichText'
        plainText = 'PlainText'
        group = 'Group'
    
    class ContentControlAppearance:
        boundingBox = 'BoundingBox'
        tags = 'Tags'
        hidden = 'Hidden'
    
    class ContentControlLevel:
        inline = 'Inline'
        paragraph = 'Paragraph'
        row = 'Row'
        cell = 'Cell'
    
    class UnderlineType:
        mixed = 'Mixed'
        none = 'None'
        hidden = 'Hidden'
        dotLine = 'DotLine'
        single = 'Single'
        word = 'Word'
        double = 'Double'
        thick = 'Thick'
        dotted = 'Dotted'
        dottedHeavy = 'DottedHeavy'
        dashLine = 'DashLine'
        dashLineHeavy = 'DashLineHeavy'
        dashLineLong = 'DashLineLong'
        dashLineLongHeavy = 'DashLineLongHeavy'
        dotDashLine = 'DotDashLine'
        dotDashLineHeavy = 'DotDashLineHeavy'
        twoDotDashLine = 'TwoDotDashLine'
        twoDotDashLineHeavy = 'TwoDotDashLineHeavy'
        wave = 'Wave'
        waveHeavy = 'WaveHeavy'
        waveDouble = 'WaveDouble'
    
    class BreakType:
        page = 'Page'
        next = 'Next'
        sectionNext = 'SectionNext'
        sectionContinuous = 'SectionContinuous'
        sectionEven = 'SectionEven'
        sectionOdd = 'SectionOdd'
        line = 'Line'
    
    class InsertLocation:
        before = 'Before'
        after = 'After'
        start = 'Start'
        end = 'End'
        replace = 'Replace'
    
    class Alignment:
        mixed = 'Mixed'
        unknown = 'Unknown'
        left = 'Left'
        centered = 'Centered'
        right = 'Right'
        justified = 'Justified'
    
    class HeaderFooterType:
        primary = 'Primary'
        firstPage = 'FirstPage'
        evenPages = 'EvenPages'
    
    class BodyType:
        unknown = 'Unknown'
        mainDoc = 'MainDoc'
        section = 'Section'
        header = 'Header'
        footer = 'Footer'
        tableCell = 'TableCell'
        footnote = 'Footnote'
        endnote = 'Endnote'
        noteItem = 'NoteItem'
    
    class SelectionMode:
        select = 'Select'
        start = 'Start'
        end = 'End'
    
    class ImageFormat:
        unsupported = 'Unsupported'
        undefined = 'Undefined'
        bmp = 'Bmp'
        jpeg = 'Jpeg'
        gif = 'Gif'
        tiff = 'Tiff'
        png = 'Png'
        icon = 'Icon'
        exif = 'Exif'
        wmf = 'Wmf'
        emf = 'Emf'
        pict = 'Pict'
        pdf = 'Pdf'
        svg = 'Svg'
    
    class RangeLocation:
        whole = 'Whole'
        start = 'Start'
        end = 'End'
        before = 'Before'
        after = 'After'
        content = 'Content'
    
    class LocationRelation:
        unrelated = 'Unrelated'
        equal = 'Equal'
        containsStart = 'ContainsStart'
        containsEnd = 'ContainsEnd'
        contains = 'Contains'
        insideStart = 'InsideStart'
        insideEnd = 'InsideEnd'
        inside = 'Inside'
        adjacentBefore = 'AdjacentBefore'
        overlapsBefore = 'OverlapsBefore'
        before = 'Before'
        adjacentAfter = 'AdjacentAfter'
        overlapsAfter = 'OverlapsAfter'
        after = 'After'
    
    class BorderLocation:
        top = 'Top'
        left = 'Left'
        bottom = 'Bottom'
        right = 'Right'
        insideHorizontal = 'InsideHorizontal'
        insideVertical = 'InsideVertical'
        inside = 'Inside'
        outside = 'Outside'
        all = 'All'
    
    class CellPaddingLocation:
        top = 'Top'
        left = 'Left'
        bottom = 'Bottom'
        right = 'Right'
    
    class BorderWidth:
        none = 'None'
        pt025 = 'Pt025'
        pt050 = 'Pt050'
        pt075 = 'Pt075'
        pt100 = 'Pt100'
        pt150 = 'Pt150'
        pt225 = 'Pt225'
        pt300 = 'Pt300'
        pt450 = 'Pt450'
        pt600 = 'Pt600'
        mixed = 'Mixed'
    
    class BorderType:
        mixed = 'Mixed'
        none = 'None'
        single = 'Single'
        double = 'Double'
        dotted = 'Dotted'
        dashed = 'Dashed'
        dotDashed = 'DotDashed'
        dot2Dashed = 'Dot2Dashed'
        triple = 'Triple'
        thinThickSmall = 'ThinThickSmall'
        thickThinSmall = 'ThickThinSmall'
        thinThickThinSmall = 'ThinThickThinSmall'
        thinThickMed = 'ThinThickMed'
        thickThinMed = 'ThickThinMed'
        thinThickThinMed = 'ThinThickThinMed'
        thinThickLarge = 'ThinThickLarge'
        thickThinLarge = 'ThickThinLarge'
        thinThickThinLarge = 'ThinThickThinLarge'
        wave = 'Wave'
        doubleWave = 'DoubleWave'
        dashedSmall = 'DashedSmall'
        dashDotStroked = 'DashDotStroked'
        threeDEmboss = 'ThreeDEmboss'
        threeDEngrave = 'ThreeDEngrave'
    
    class VerticalAlignment:
        mixed = 'Mixed'
        top = 'Top'
        center = 'Center'
        bottom = 'Bottom'
    
    class ListLevelType:
        bullet = 'Bullet'
        number = 'Number'
        picture = 'Picture'
    
    class ListBullet:
        custom = 'Custom'
        solid = 'Solid'
        hollow = 'Hollow'
        square = 'Square'
        diamonds = 'Diamonds'
        arrow = 'Arrow'
        checkmark = 'Checkmark'
    
    class ListNumbering:
        none = 'None'
        arabic = 'Arabic'
        upperRoman = 'UpperRoman'
        lowerRoman = 'LowerRoman'
        upperLetter = 'UpperLetter'
        lowerLetter = 'LowerLetter'
    
    class BuiltInStyleName:
        other = 'Other'
        normal = 'Normal'
        heading1 = 'Heading1'
        heading2 = 'Heading2'
        heading3 = 'Heading3'
        heading4 = 'Heading4'
        heading5 = 'Heading5'
        heading6 = 'Heading6'
        heading7 = 'Heading7'
        heading8 = 'Heading8'
        heading9 = 'Heading9'
        toc1 = 'Toc1'
        toc2 = 'Toc2'
        toc3 = 'Toc3'
        toc4 = 'Toc4'
        toc5 = 'Toc5'
        toc6 = 'Toc6'
        toc7 = 'Toc7'
        toc8 = 'Toc8'
        toc9 = 'Toc9'
        footnoteText = 'FootnoteText'
        header = 'Header'
        footer = 'Footer'
        caption = 'Caption'
        footnoteReference = 'FootnoteReference'
        endnoteReference = 'EndnoteReference'
        endnoteText = 'EndnoteText'
        title = 'Title'
        subtitle = 'Subtitle'
        hyperlink = 'Hyperlink'
        strong = 'Strong'
        emphasis = 'Emphasis'
        noSpacing = 'NoSpacing'
        listParagraph = 'ListParagraph'
        quote = 'Quote'
        intenseQuote = 'IntenseQuote'
        subtleEmphasis = 'SubtleEmphasis'
        intenseEmphasis = 'IntenseEmphasis'
        subtleReference = 'SubtleReference'
        intenseReference = 'IntenseReference'
        bookTitle = 'BookTitle'
        bibliography = 'Bibliography'
        tocHeading = 'TocHeading'
        tableGrid = 'TableGrid'
        plainTable1 = 'PlainTable1'
        plainTable2 = 'PlainTable2'
        plainTable3 = 'PlainTable3'
        plainTable4 = 'PlainTable4'
        plainTable5 = 'PlainTable5'
        tableGridLight = 'TableGridLight'
        gridTable1Light = 'GridTable1Light'
        gridTable1Light_Accent1 = 'GridTable1Light_Accent1'
        gridTable1Light_Accent2 = 'GridTable1Light_Accent2'
        gridTable1Light_Accent3 = 'GridTable1Light_Accent3'
        gridTable1Light_Accent4 = 'GridTable1Light_Accent4'
        gridTable1Light_Accent5 = 'GridTable1Light_Accent5'
        gridTable1Light_Accent6 = 'GridTable1Light_Accent6'
        gridTable2 = 'GridTable2'
        gridTable2_Accent1 = 'GridTable2_Accent1'
        gridTable2_Accent2 = 'GridTable2_Accent2'
        gridTable2_Accent3 = 'GridTable2_Accent3'
        gridTable2_Accent4 = 'GridTable2_Accent4'
        gridTable2_Accent5 = 'GridTable2_Accent5'
        gridTable2_Accent6 = 'GridTable2_Accent6'
        gridTable3 = 'GridTable3'
        gridTable3_Accent1 = 'GridTable3_Accent1'
        gridTable3_Accent2 = 'GridTable3_Accent2'
        gridTable3_Accent3 = 'GridTable3_Accent3'
        gridTable3_Accent4 = 'GridTable3_Accent4'
        gridTable3_Accent5 = 'GridTable3_Accent5'
        gridTable3_Accent6 = 'GridTable3_Accent6'
        gridTable4 = 'GridTable4'
        gridTable4_Accent1 = 'GridTable4_Accent1'
        gridTable4_Accent2 = 'GridTable4_Accent2'
        gridTable4_Accent3 = 'GridTable4_Accent3'
        gridTable4_Accent4 = 'GridTable4_Accent4'
        gridTable4_Accent5 = 'GridTable4_Accent5'
        gridTable4_Accent6 = 'GridTable4_Accent6'
        gridTable5Dark = 'GridTable5Dark'
        gridTable5Dark_Accent1 = 'GridTable5Dark_Accent1'
        gridTable5Dark_Accent2 = 'GridTable5Dark_Accent2'
        gridTable5Dark_Accent3 = 'GridTable5Dark_Accent3'
        gridTable5Dark_Accent4 = 'GridTable5Dark_Accent4'
        gridTable5Dark_Accent5 = 'GridTable5Dark_Accent5'
        gridTable5Dark_Accent6 = 'GridTable5Dark_Accent6'
        gridTable6Colorful = 'GridTable6Colorful'
        gridTable6Colorful_Accent1 = 'GridTable6Colorful_Accent1'
        gridTable6Colorful_Accent2 = 'GridTable6Colorful_Accent2'
        gridTable6Colorful_Accent3 = 'GridTable6Colorful_Accent3'
        gridTable6Colorful_Accent4 = 'GridTable6Colorful_Accent4'
        gridTable6Colorful_Accent5 = 'GridTable6Colorful_Accent5'
        gridTable6Colorful_Accent6 = 'GridTable6Colorful_Accent6'
        gridTable7Colorful = 'GridTable7Colorful'
        gridTable7Colorful_Accent1 = 'GridTable7Colorful_Accent1'
        gridTable7Colorful_Accent2 = 'GridTable7Colorful_Accent2'
        gridTable7Colorful_Accent3 = 'GridTable7Colorful_Accent3'
        gridTable7Colorful_Accent4 = 'GridTable7Colorful_Accent4'
        gridTable7Colorful_Accent5 = 'GridTable7Colorful_Accent5'
        gridTable7Colorful_Accent6 = 'GridTable7Colorful_Accent6'
        listTable1Light = 'ListTable1Light'
        listTable1Light_Accent1 = 'ListTable1Light_Accent1'
        listTable1Light_Accent2 = 'ListTable1Light_Accent2'
        listTable1Light_Accent3 = 'ListTable1Light_Accent3'
        listTable1Light_Accent4 = 'ListTable1Light_Accent4'
        listTable1Light_Accent5 = 'ListTable1Light_Accent5'
        listTable1Light_Accent6 = 'ListTable1Light_Accent6'
        listTable2 = 'ListTable2'
        listTable2_Accent1 = 'ListTable2_Accent1'
        listTable2_Accent2 = 'ListTable2_Accent2'
        listTable2_Accent3 = 'ListTable2_Accent3'
        listTable2_Accent4 = 'ListTable2_Accent4'
        listTable2_Accent5 = 'ListTable2_Accent5'
        listTable2_Accent6 = 'ListTable2_Accent6'
        listTable3 = 'ListTable3'
        listTable3_Accent1 = 'ListTable3_Accent1'
        listTable3_Accent2 = 'ListTable3_Accent2'
        listTable3_Accent3 = 'ListTable3_Accent3'
        listTable3_Accent4 = 'ListTable3_Accent4'
        listTable3_Accent5 = 'ListTable3_Accent5'
        listTable3_Accent6 = 'ListTable3_Accent6'
        listTable4 = 'ListTable4'
        listTable4_Accent1 = 'ListTable4_Accent1'
        listTable4_Accent2 = 'ListTable4_Accent2'
        listTable4_Accent3 = 'ListTable4_Accent3'
        listTable4_Accent4 = 'ListTable4_Accent4'
        listTable4_Accent5 = 'ListTable4_Accent5'
        listTable4_Accent6 = 'ListTable4_Accent6'
        listTable5Dark = 'ListTable5Dark'
        listTable5Dark_Accent1 = 'ListTable5Dark_Accent1'
        listTable5Dark_Accent2 = 'ListTable5Dark_Accent2'
        listTable5Dark_Accent3 = 'ListTable5Dark_Accent3'
        listTable5Dark_Accent4 = 'ListTable5Dark_Accent4'
        listTable5Dark_Accent5 = 'ListTable5Dark_Accent5'
        listTable5Dark_Accent6 = 'ListTable5Dark_Accent6'
        listTable6Colorful = 'ListTable6Colorful'
        listTable6Colorful_Accent1 = 'ListTable6Colorful_Accent1'
        listTable6Colorful_Accent2 = 'ListTable6Colorful_Accent2'
        listTable6Colorful_Accent3 = 'ListTable6Colorful_Accent3'
        listTable6Colorful_Accent4 = 'ListTable6Colorful_Accent4'
        listTable6Colorful_Accent5 = 'ListTable6Colorful_Accent5'
        listTable6Colorful_Accent6 = 'ListTable6Colorful_Accent6'
        listTable7Colorful = 'ListTable7Colorful'
        listTable7Colorful_Accent1 = 'ListTable7Colorful_Accent1'
        listTable7Colorful_Accent2 = 'ListTable7Colorful_Accent2'
        listTable7Colorful_Accent3 = 'ListTable7Colorful_Accent3'
        listTable7Colorful_Accent4 = 'ListTable7Colorful_Accent4'
        listTable7Colorful_Accent5 = 'ListTable7Colorful_Accent5'
        listTable7Colorful_Accent6 = 'ListTable7Colorful_Accent6'
    
    class DocumentPropertyType:
        string = 'String'
        number = 'Number'
        date = 'Date'
        boolean = 'Boolean'
    
    class PrintOutItem:
        documentContent = 'DocumentContent'
        properties = 'Properties'
        comments = 'Comments'
        markup = 'Markup'
        styles = 'Styles'
        autoTextEntries = 'AutoTextEntries'
        keyAssignments = 'KeyAssignments'
        envelope = 'Envelope'
        documentWithMarkup = 'DocumentWithMarkup'
    
    class PrintOutPages:
        all = 'All'
        oddOnly = 'OddOnly'
        evenOnly = 'EvenOnly'
    
    class PrintOutRange:
        allDocument = 'AllDocument'
        selection = 'Selection'
        currentPage = 'CurrentPage'
        fromTo = 'FromTo'
        rangeOfPages = 'RangeOfPages'
    
    class ExportFormat:
        pdf = 'Pdf'
        xps = 'Xps'
    
    class ExportItem:
        documentContent = 'DocumentContent'
        documentWithMarkup = 'DocumentWithMarkup'
    
    class ExportOptimizeFor:
        print = 'Print'
        onScreen = 'OnScreen'
    
    class ExportRange:
        allDocument = 'AllDocument'
        selection = 'Selection'
        currentPage = 'CurrentPage'
        fromTo = 'FromTo'
    
    class ExportCreateBookmarks:
        none = 'None'
        headings = 'Headings'
        wordBookmarks = 'WordBookmarks'
    
    class UseFormattingFrom:
        current = 'Current'
        selected = 'Selected'
        prompt = 'Prompt'
    
    class AutoMacro:
        startWord = 'StartWord'
        new = 'New'
        open = 'Open'
        close = 'Close'
        exit = 'Exit'
        sync = 'Sync'
    
    class StatisticType:
        words = 'Words'
        lines = 'Lines'
        pages = 'Pages'
        characters = 'Characters'
        paragraphs = 'Paragraphs'
        charactersWithSpaces = 'CharactersWithSpaces'
        farEastCharacters = 'FarEastCharacters'
    
    class RemoveDocInfoType:
        comments = 'Comments'
        revisions = 'Revisions'
        versions = 'Versions'
        removePersonalInformation = 'RemovePersonalInformation'
        emailHeader = 'EmailHeader'
        routingSlip = 'RoutingSlip'
        sendForReview = 'SendForReview'
        documentProperties = 'DocumentProperties'
        template = 'Template'
        documentWorkspace = 'DocumentWorkspace'
        inkAnnotations = 'InkAnnotations'
        documentServerProperties = 'DocumentServerProperties'
        documentManagementPolicy = 'DocumentManagementPolicy'
        contentType = 'ContentType'
        taskpaneWebExtensions = 'TaskpaneWebExtensions'
        atMentions = 'AtMentions'
        documentTasks = 'DocumentTasks'
        documentIntelligence = 'DocumentIntelligence'
        commentReactions = 'CommentReactions'
        all = 'All'
    
    class CheckInVersionType:
        minor = 'Minor'
        major = 'Major'
        overwrite = 'Overwrite'
    
    class MergeTarget:
        selected = 'Selected'
        current = 'Current'
        new = 'New'
    
    class DocumentType:
        document = 'Document'
        template = 'Template'
        frameset = 'Frameset'
    
    class DocumentKind:
        notSpecified = 'NotSpecified'
        letter = 'Letter'
        email = 'Email'
    
    class FileSaveFormat:
        document = 'Document'
        template = 'Template'
        text = 'Text'
        textLineBreaks = 'TextLineBreaks'
        dosText = 'DosText'
        dosTextLineBreaks = 'DosTextLineBreaks'
        rtf = 'Rtf'
        unicodeText = 'UnicodeText'
        html = 'Html'
        webArchive = 'WebArchive'
        filteredHtml = 'FilteredHtml'
        xml = 'Xml'
        xmlDocument = 'XmlDocument'
        xmlDocumentMacroEnabled = 'XmlDocumentMacroEnabled'
        xmlTemplate = 'XmlTemplate'
        xmlTemplateMacroEnabled = 'XmlTemplateMacroEnabled'
        documentDefault = 'DocumentDefault'
        pdf = 'Pdf'
        xps = 'Xps'
        flatXml = 'FlatXml'
        flatXmlMacroEnabled = 'FlatXmlMacroEnabled'
        flatXmlTemplate = 'FlatXmlTemplate'
        flatXmlTemplateMacroEnabled = 'FlatXmlTemplateMacroEnabled'
        openDocumentText = 'OpenDocumentText'
        strictOpenXmlDocument = 'StrictOpenXmlDocument'
    
    class ProtectionType:
        noProtection = 'NoProtection'
        allowOnlyRevisions = 'AllowOnlyRevisions'
        allowOnlyComments = 'AllowOnlyComments'
        allowOnlyFormFields = 'AllowOnlyFormFields'
        allowOnlyReading = 'AllowOnlyReading'
    
    class LineEndingType:
        crlf = 'Crlf'
        crOnly = 'CrOnly'
        lfOnly = 'LfOnly'
        lfcr = 'Lfcr'
        lsps = 'Lsps'
    
    class DocumentEncoding:
        thai = 'Thai'
        japaneseShiftJis = 'JapaneseShiftJis'
        simplifiedChineseGbk = 'SimplifiedChineseGbk'
        korean = 'Korean'
        traditionalChineseBig5 = 'TraditionalChineseBig5'
        unicodeLittleEndian = 'UnicodeLittleEndian'
        unicodeBigEndian = 'UnicodeBigEndian'
        centralEuropean = 'CentralEuropean'
        cyrillic = 'Cyrillic'
        western = 'Western'
        greek = 'Greek'
        turkish = 'Turkish'
        hebrew = 'Hebrew'
        arabic = 'Arabic'
        baltic = 'Baltic'
        vietnamese = 'Vietnamese'
        autoDetect = 'AutoDetect'
        japaneseAutoDetect = 'JapaneseAutoDetect'
        simplifiedChineseAutoDetect = 'SimplifiedChineseAutoDetect'
        koreanAutoDetect = 'KoreanAutoDetect'
        traditionalChineseAutoDetect = 'TraditionalChineseAutoDetect'
        cyrillicAutoDetect = 'CyrillicAutoDetect'
        greekAutoDetect = 'GreekAutoDetect'
        arabicAutoDetect = 'ArabicAutoDetect'
        iso88591Latin1 = 'Iso88591Latin1'
        iso88592CentralEurope = 'Iso88592CentralEurope'
        iso88593Latin3 = 'Iso88593Latin3'
        iso88594Baltic = 'Iso88594Baltic'
        iso88595Cyrillic = 'Iso88595Cyrillic'
        iso88596Arabic = 'Iso88596Arabic'
        iso88597Greek = 'Iso88597Greek'
        iso88598Hebrew = 'Iso88598Hebrew'
        iso88599Turkish = 'Iso88599Turkish'
        iso885915Latin9 = 'Iso885915Latin9'
        iso88598HebrewLogical = 'Iso88598HebrewLogical'
        iso2022JpNoHalfwidthKatakana = 'Iso2022JpNoHalfwidthKatakana'
        iso2022JpJisX02021984 = 'Iso2022JpJisX02021984'
        iso2022JpJisX02011989 = 'Iso2022JpJisX02011989'
        iso2022Kr = 'Iso2022Kr'
        iso2022CnTraditionalChinese = 'Iso2022CnTraditionalChinese'
        iso2022CnSimplifiedChinese = 'Iso2022CnSimplifiedChinese'
        macRoman = 'MacRoman'
        macJapanese = 'MacJapanese'
        macTraditionalChineseBig5 = 'MacTraditionalChineseBig5'
        macKorean = 'MacKorean'
        macArabic = 'MacArabic'
        macHebrew = 'MacHebrew'
        macGreek1 = 'MacGreek1'
        macCyrillic = 'MacCyrillic'
        macSimplifiedChineseGb2312 = 'MacSimplifiedChineseGb2312'
        macRomania = 'MacRomania'
        macUkraine = 'MacUkraine'
        macLatin2 = 'MacLatin2'
        macIcelandic = 'MacIcelandic'
        macTurkish = 'MacTurkish'
        macCroatia = 'MacCroatia'
        ebcdicUsCanada = 'EbcdicUsCanada'
        ebcdicInternational = 'EbcdicInternational'
        ebcdicMultilingualRoeceLatin2 = 'EbcdicMultilingualRoeceLatin2'
        ebcdicGreekModern = 'EbcdicGreekModern'
        ebcdicTurkishLatin5 = 'EbcdicTurkishLatin5'
        ebcdicGermany = 'EbcdicGermany'
        ebcdicDenmarkNorway = 'EbcdicDenmarkNorway'
        ebcdicFinlandSweden = 'EbcdicFinlandSweden'
        ebcdicItaly = 'EbcdicItaly'
        ebcdicLatinAmericaSpain = 'EbcdicLatinAmericaSpain'
        ebcdicUnitedKingdom = 'EbcdicUnitedKingdom'
        ebcdicJapaneseKatakanaExtended = 'EbcdicJapaneseKatakanaExtended'
        ebcdicFrance = 'EbcdicFrance'
        ebcdicArabic = 'EbcdicArabic'
        ebcdicGreek = 'EbcdicGreek'
        ebcdicHebrew = 'EbcdicHebrew'
        ebcdicKoreanExtended = 'EbcdicKoreanExtended'
        ebcdicThai = 'EbcdicThai'
        ebcdicIcelandic = 'EbcdicIcelandic'
        ebcdicTurkish = 'EbcdicTurkish'
        ebcdicRussian = 'EbcdicRussian'
        ebcdicSerbianBulgarian = 'EbcdicSerbianBulgarian'
        ebcdicJapaneseKatakanaExtendedAndJapanese = 'EbcdicJapaneseKatakanaExtendedAndJapanese'
        ebcdicUsCanadaAndJapanese = 'EbcdicUsCanadaAndJapanese'
        ebcdicKoreanExtendedAndKorean = 'EbcdicKoreanExtendedAndKorean'
        ebcdicSimplifiedChineseExtendedAndSimplifiedChinese = 'EbcdicSimplifiedChineseExtendedAndSimplifiedChinese'
        ebcdicUsCanadaAndTraditionalChinese = 'EbcdicUsCanadaAndTraditionalChinese'
        ebcdicJapaneseLatinExtendedAndJapanese = 'EbcdicJapaneseLatinExtendedAndJapanese'
        oemUnitedStates = 'OemUnitedStates'
        oemGreek437G = 'OemGreek437G'
        oemBaltic = 'OemBaltic'
        oemMultilingualLatinI = 'OemMultilingualLatinI'
        oemMultilingualLatinIi = 'OemMultilingualLatinIi'
        oemCyrillic = 'OemCyrillic'
        oemTurkish = 'OemTurkish'
        oemPortuguese = 'OemPortuguese'
        oemIcelandic = 'OemIcelandic'
        oemHebrew = 'OemHebrew'
        oemCanadianFrench = 'OemCanadianFrench'
        oemArabic = 'OemArabic'
        oemNordic = 'OemNordic'
        oemCyrillicIi = 'OemCyrillicIi'
        oemModernGreek = 'OemModernGreek'
        eucJapanese = 'EucJapanese'
        eucChineseSimplifiedChinese = 'EucChineseSimplifiedChinese'
        eucKorean = 'EucKorean'
        eucTaiwaneseTraditionalChinese = 'EucTaiwaneseTraditionalChinese'
        isciiDevanagari = 'IsciiDevanagari'
        isciiBengali = 'IsciiBengali'
        isciiTamil = 'IsciiTamil'
        isciiTelugu = 'IsciiTelugu'
        isciiAssamese = 'IsciiAssamese'
        isciiOriya = 'IsciiOriya'
        isciiKannada = 'IsciiKannada'
        isciiMalayalam = 'IsciiMalayalam'
        isciiGujarati = 'IsciiGujarati'
        isciiPunjabi = 'IsciiPunjabi'
        arabicAsmo = 'ArabicAsmo'
        arabicTransparentAsmo = 'ArabicTransparentAsmo'
        koreanJohab = 'KoreanJohab'
        taiwanCns = 'TaiwanCns'
        taiwanTca = 'TaiwanTca'
        taiwanEten = 'TaiwanEten'
        taiwanIbm5550 = 'TaiwanIbm5550'
        taiwanTeleText = 'TaiwanTeleText'
        taiwanWang = 'TaiwanWang'
        ia5Irv = 'Ia5Irv'
        ia5German = 'Ia5German'
        ia5Swedish = 'Ia5Swedish'
        ia5Norwegian = 'Ia5Norwegian'
        usaAscii = 'UsaAscii'
        t61 = 'T61'
        iso6937NonSpacingAccent = 'Iso6937NonSpacingAccent'
        koi8R = 'Koi8R'
        extAlphaLowercase = 'ExtAlphaLowercase'
        koi8U = 'Koi8U'
        europa3 = 'Europa3'
        hzGbSimplifiedChinese = 'HzGbSimplifiedChinese'
        simplifiedChineseGb18030 = 'SimplifiedChineseGb18030'
        utf7 = 'Utf7'
        utf8 = 'Utf8'
    
    class CompatibilityMode:
        word2003 = 'Word2003'
        word2007 = 'Word2007'
        word2010 = 'Word2010'
        word2013 = 'Word2013'
        current = 'Current'
    
    class StyleType:
        character = 'Character'
        list = 'List'
        paragraph = 'Paragraph'
        table = 'Table'
    
    class OutlineLevel:
        outlineLevel1 = 'OutlineLevel1'
        outlineLevel2 = 'OutlineLevel2'
        outlineLevel3 = 'OutlineLevel3'
        outlineLevel4 = 'OutlineLevel4'
        outlineLevel5 = 'OutlineLevel5'
        outlineLevel6 = 'OutlineLevel6'
        outlineLevel7 = 'OutlineLevel7'
        outlineLevel8 = 'OutlineLevel8'
        outlineLevel9 = 'OutlineLevel9'
        outlineLevelBodyText = 'OutlineLevelBodyText'
    
    class CloseBehavior:
        save = 'Save'
        skipSave = 'SkipSave'
    
    class SaveBehavior:
        save = 'Save'
        prompt = 'Prompt'
    
    class FieldType:
        addin = 'Addin'
        addressBlock = 'AddressBlock'
        advance = 'Advance'
        ask = 'Ask'
        author = 'Author'
        autoText = 'AutoText'
        autoTextList = 'AutoTextList'
        barCode = 'BarCode'
        bibliography = 'Bibliography'
        bidiOutline = 'BidiOutline'
        citation = 'Citation'
        comments = 'Comments'
        compare = 'Compare'
        createDate = 'CreateDate'
        data = 'Data'
        database = 'Database'
        date = 'Date'
        displayBarcode = 'DisplayBarcode'
        docProperty = 'DocProperty'
        docVariable = 'DocVariable'
        editTime = 'EditTime'
        embedded = 'Embedded'
        eq = 'EQ'
        expression = 'Expression'
        fileName = 'FileName'
        fileSize = 'FileSize'
        fillIn = 'FillIn'
        formCheckbox = 'FormCheckbox'
        formDropdown = 'FormDropdown'
        formText = 'FormText'
        gotoButton = 'GotoButton'
        greetingLine = 'GreetingLine'
        hyperlink = 'Hyperlink'
        if_ = 'If'
        import_ = 'Import'
        include = 'Include'
        includePicture = 'IncludePicture'
        includeText = 'IncludeText'
        index = 'Index'
        info = 'Info'
        keywords = 'Keywords'
        lastSavedBy = 'LastSavedBy'
        link = 'Link'
        listNum = 'ListNum'
        macroButton = 'MacroButton'
        mergeBarcode = 'MergeBarcode'
        mergeField = 'MergeField'
        mergeRec = 'MergeRec'
        mergeSeq = 'MergeSeq'
        next = 'Next'
        nextIf = 'NextIf'
        noteRef = 'NoteRef'
        numChars = 'NumChars'
        numPages = 'NumPages'
        numWords = 'NumWords'
        ocx = 'OCX'
        page = 'Page'
        pageRef = 'PageRef'
        print = 'Print'
        printDate = 'PrintDate'
        private = 'Private'
        quote = 'Quote'
        rd = 'RD'
        ref = 'Ref'
        revNum = 'RevNum'
        saveDate = 'SaveDate'
        section = 'Section'
        sectionPages = 'SectionPages'
        seq = 'Seq'
        set = 'Set'
        shape = 'Shape'
        skipIf = 'SkipIf'
        styleRef = 'StyleRef'
        subject = 'Subject'
        subscriber = 'Subscriber'
        symbol = 'Symbol'
        ta = 'TA'
        tc = 'TC'
        template = 'Template'
        time = 'Time'
        title = 'Title'
        toa = 'TOA'
        toc = 'TOC'
        userAddress = 'UserAddress'
        userInitials = 'UserInitials'
        userName = 'UserName'
        xe = 'XE'
        empty = 'Empty'
        others = 'Others'
        undefined = 'Undefined'
    
    class FieldKind:
        none = 'None'
        hot = 'Hot'
        warm = 'Warm'
        cold = 'Cold'
    
    class TrailingCharacter:
        trailingTab = 'TrailingTab'
        trailingSpace = 'TrailingSpace'
        trailingNone = 'TrailingNone'
    
    class ListBuiltInNumberStyle:
        none = 'None'
        arabic = 'Arabic'
        upperRoman = 'UpperRoman'
        lowerRoman = 'LowerRoman'
        upperLetter = 'UpperLetter'
        lowerLetter = 'LowerLetter'
        ordinal = 'Ordinal'
        cardinalText = 'CardinalText'
        ordinalText = 'OrdinalText'
        kanji = 'Kanji'
        kanjiDigit = 'KanjiDigit'
        aiueoHalfWidth = 'AiueoHalfWidth'
        irohaHalfWidth = 'IrohaHalfWidth'
        arabicFullWidth = 'ArabicFullWidth'
        kanjiTraditional = 'KanjiTraditional'
        kanjiTraditional2 = 'KanjiTraditional2'
        numberInCircle = 'NumberInCircle'
        aiueo = 'Aiueo'
        iroha = 'Iroha'
        arabicLZ = 'ArabicLZ'
        bullet = 'Bullet'
        ganada = 'Ganada'
        chosung = 'Chosung'
        gbnum1 = 'GBNum1'
        gbnum2 = 'GBNum2'
        gbnum3 = 'GBNum3'
        gbnum4 = 'GBNum4'
        zodiac1 = 'Zodiac1'
        zodiac2 = 'Zodiac2'
        zodiac3 = 'Zodiac3'
        tradChinNum1 = 'TradChinNum1'
        tradChinNum2 = 'TradChinNum2'
        tradChinNum3 = 'TradChinNum3'
        tradChinNum4 = 'TradChinNum4'
        simpChinNum1 = 'SimpChinNum1'
        simpChinNum2 = 'SimpChinNum2'
        simpChinNum3 = 'SimpChinNum3'
        simpChinNum4 = 'SimpChinNum4'
        hanjaRead = 'HanjaRead'
        hanjaReadDigit = 'HanjaReadDigit'
        hangul = 'Hangul'
        hanja = 'Hanja'
        hebrew1 = 'Hebrew1'
        arabic1 = 'Arabic1'
        hebrew2 = 'Hebrew2'
        arabic2 = 'Arabic2'
        hindiLetter1 = 'HindiLetter1'
        hindiLetter2 = 'HindiLetter2'
        hindiArabic = 'HindiArabic'
        hindiCardinalText = 'HindiCardinalText'
        thaiLetter = 'ThaiLetter'
        thaiArabic = 'ThaiArabic'
        thaiCardinalText = 'ThaiCardinalText'
        vietCardinalText = 'VietCardinalText'
        lowercaseRussian = 'LowercaseRussian'
        uppercaseRussian = 'UppercaseRussian'
        lowercaseGreek = 'LowercaseGreek'
        uppercaseGreek = 'UppercaseGreek'
        arabicLZ2 = 'ArabicLZ2'
        arabicLZ3 = 'ArabicLZ3'
        arabicLZ4 = 'ArabicLZ4'
        lowercaseTurkish = 'LowercaseTurkish'
        uppercaseTurkish = 'UppercaseTurkish'
        lowercaseBulgarian = 'LowercaseBulgarian'
        uppercaseBulgarian = 'UppercaseBulgarian'
        pictureBullet = 'PictureBullet'
        legal = 'Legal'
        legalLZ = 'LegalLZ'
    
    class ShadingTextureType:
        darkDiagonalDown = 'DarkDiagonalDown'
        darkDiagonalUp = 'DarkDiagonalUp'
        darkGrid = 'DarkGrid'
        darkHorizontal = 'DarkHorizontal'
        darkTrellis = 'DarkTrellis'
        darkVertical = 'DarkVertical'
        lightDiagonalDown = 'LightDiagonalDown'
        lightDiagonalUp = 'LightDiagonalUp'
        lightGrid = 'LightGrid'
        lightHorizontal = 'LightHorizontal'
        lightTrellis = 'LightTrellis'
        lightVertical = 'LightVertical'
        none = 'None'
        percent10 = 'Percent10'
        percent12Pt5 = 'Percent12Pt5'
        percent15 = 'Percent15'
        percent20 = 'Percent20'
        percent25 = 'Percent25'
        percent30 = 'Percent30'
        percent35 = 'Percent35'
        percent37Pt5 = 'Percent37Pt5'
        percent40 = 'Percent40'
        percent45 = 'Percent45'
        percent5 = 'Percent5'
        percent50 = 'Percent50'
        percent55 = 'Percent55'
        percent60 = 'Percent60'
        percent62Pt5 = 'Percent62Pt5'
        percent65 = 'Percent65'
        percent70 = 'Percent70'
        percent75 = 'Percent75'
        percent80 = 'Percent80'
        percent85 = 'Percent85'
        percent87Pt5 = 'Percent87Pt5'
        percent90 = 'Percent90'
        percent95 = 'Percent95'
        solid = 'Solid'
    
    class CompareTarget:
        compareTargetCurrent = 'CompareTargetCurrent'
        compareTargetSelected = 'CompareTargetSelected'
        compareTargetNew = 'CompareTargetNew'
    
    class ImportedStylesConflictBehavior:
        ignore = 'Ignore'
        overwrite = 'Overwrite'
        createNew = 'CreateNew'
    
    class ShapeType:
        unsupported = 'Unsupported'
        textBox = 'TextBox'
        geometricShape = 'GeometricShape'
        group = 'Group'
        picture = 'Picture'
        canvas = 'Canvas'
    
    class RelativeHorizontalPosition:
        margin = 'Margin'
        page = 'Page'
        column = 'Column'
        character = 'Character'
        leftMargin = 'LeftMargin'
        rightMargin = 'RightMargin'
        insideMargin = 'InsideMargin'
        outsideMargin = 'OutsideMargin'
    
    class RelativeVerticalPosition:
        margin = 'Margin'
        page = 'Page'
        paragraph = 'Paragraph'
        line = 'Line'
        topMargin = 'TopMargin'
        bottomMargin = 'BottomMargin'
        insideMargin = 'InsideMargin'
        outsideMargin = 'OutsideMargin'
    
    class RelativeSize:
        margin = 'Margin'
        page = 'Page'
        topMargin = 'TopMargin'
        bottomMargin = 'BottomMargin'
        insideMargin = 'InsideMargin'
        outsideMargin = 'OutsideMargin'
    
    class GeometricShapeType:
        lineInverse = 'LineInverse'
        triangle = 'Triangle'
        rightTriangle = 'RightTriangle'
        rectangle = 'Rectangle'
        diamond = 'Diamond'
        parallelogram = 'Parallelogram'
        trapezoid = 'Trapezoid'
        nonIsoscelesTrapezoid = 'NonIsoscelesTrapezoid'
        pentagon = 'Pentagon'
        hexagon = 'Hexagon'
        heptagon = 'Heptagon'
        octagon = 'Octagon'
        decagon = 'Decagon'
        dodecagon = 'Dodecagon'
        star4 = 'Star4'
        star5 = 'Star5'
        star6 = 'Star6'
        star7 = 'Star7'
        star8 = 'Star8'
        star10 = 'Star10'
        star12 = 'Star12'
        star16 = 'Star16'
        star24 = 'Star24'
        star32 = 'Star32'
        roundRectangle = 'RoundRectangle'
        round1Rectangle = 'Round1Rectangle'
        round2SameRectangle = 'Round2SameRectangle'
        round2DiagonalRectangle = 'Round2DiagonalRectangle'
        snipRoundRectangle = 'SnipRoundRectangle'
        snip1Rectangle = 'Snip1Rectangle'
        snip2SameRectangle = 'Snip2SameRectangle'
        snip2DiagonalRectangle = 'Snip2DiagonalRectangle'
        plaque = 'Plaque'
        ellipse = 'Ellipse'
        teardrop = 'Teardrop'
        homePlate = 'HomePlate'
        chevron = 'Chevron'
        pieWedge = 'PieWedge'
        pie = 'Pie'
        blockArc = 'BlockArc'
        donut = 'Donut'
        noSmoking = 'NoSmoking'
        rightArrow = 'RightArrow'
        leftArrow = 'LeftArrow'
        upArrow = 'UpArrow'
        downArrow = 'DownArrow'
        stripedRightArrow = 'StripedRightArrow'
        notchedRightArrow = 'NotchedRightArrow'
        bentUpArrow = 'BentUpArrow'
        leftRightArrow = 'LeftRightArrow'
        upDownArrow = 'UpDownArrow'
        leftUpArrow = 'LeftUpArrow'
        leftRightUpArrow = 'LeftRightUpArrow'
        quadArrow = 'QuadArrow'
        leftArrowCallout = 'LeftArrowCallout'
        rightArrowCallout = 'RightArrowCallout'
        upArrowCallout = 'UpArrowCallout'
        downArrowCallout = 'DownArrowCallout'
        leftRightArrowCallout = 'LeftRightArrowCallout'
        upDownArrowCallout = 'UpDownArrowCallout'
        quadArrowCallout = 'QuadArrowCallout'
        bentArrow = 'BentArrow'
        uturnArrow = 'UturnArrow'
        circularArrow = 'CircularArrow'
        leftCircularArrow = 'LeftCircularArrow'
        leftRightCircularArrow = 'LeftRightCircularArrow'
        curvedRightArrow = 'CurvedRightArrow'
        curvedLeftArrow = 'CurvedLeftArrow'
        curvedUpArrow = 'CurvedUpArrow'
        curvedDownArrow = 'CurvedDownArrow'
        swooshArrow = 'SwooshArrow'
        cube = 'Cube'
        can = 'Can'
        lightningBolt = 'LightningBolt'
        heart = 'Heart'
        sun = 'Sun'
        moon = 'Moon'
        smileyFace = 'SmileyFace'
        irregularSeal1 = 'IrregularSeal1'
        irregularSeal2 = 'IrregularSeal2'
        foldedCorner = 'FoldedCorner'
        bevel = 'Bevel'
        frame = 'Frame'
        halfFrame = 'HalfFrame'
        corner = 'Corner'
        diagonalStripe = 'DiagonalStripe'
        chord = 'Chord'
        arc = 'Arc'
        leftBracket = 'LeftBracket'
        rightBracket = 'RightBracket'
        leftBrace = 'LeftBrace'
        rightBrace = 'RightBrace'
        bracketPair = 'BracketPair'
        bracePair = 'BracePair'
        callout1 = 'Callout1'
        callout2 = 'Callout2'
        callout3 = 'Callout3'
        accentCallout1 = 'AccentCallout1'
        accentCallout2 = 'AccentCallout2'
        accentCallout3 = 'AccentCallout3'
        borderCallout1 = 'BorderCallout1'
        borderCallout2 = 'BorderCallout2'
        borderCallout3 = 'BorderCallout3'
        accentBorderCallout1 = 'AccentBorderCallout1'
        accentBorderCallout2 = 'AccentBorderCallout2'
        accentBorderCallout3 = 'AccentBorderCallout3'
        wedgeRectCallout = 'WedgeRectCallout'
        wedgeRRectCallout = 'WedgeRRectCallout'
        wedgeEllipseCallout = 'WedgeEllipseCallout'
        cloudCallout = 'CloudCallout'
        cloud = 'Cloud'
        ribbon = 'Ribbon'
        ribbon2 = 'Ribbon2'
        ellipseRibbon = 'EllipseRibbon'
        ellipseRibbon2 = 'EllipseRibbon2'
        leftRightRibbon = 'LeftRightRibbon'
        verticalScroll = 'VerticalScroll'
        horizontalScroll = 'HorizontalScroll'
        wave = 'Wave'
        doubleWave = 'DoubleWave'
        plus = 'Plus'
        flowChartProcess = 'FlowChartProcess'
        flowChartDecision = 'FlowChartDecision'
        flowChartInputOutput = 'FlowChartInputOutput'
        flowChartPredefinedProcess = 'FlowChartPredefinedProcess'
        flowChartInternalStorage = 'FlowChartInternalStorage'
        flowChartDocument = 'FlowChartDocument'
        flowChartMultidocument = 'FlowChartMultidocument'
        flowChartTerminator = 'FlowChartTerminator'
        flowChartPreparation = 'FlowChartPreparation'
        flowChartManualInput = 'FlowChartManualInput'
        flowChartManualOperation = 'FlowChartManualOperation'
        flowChartConnector = 'FlowChartConnector'
        flowChartPunchedCard = 'FlowChartPunchedCard'
        flowChartPunchedTape = 'FlowChartPunchedTape'
        flowChartSummingJunction = 'FlowChartSummingJunction'
        flowChartOr = 'FlowChartOr'
        flowChartCollate = 'FlowChartCollate'
        flowChartSort = 'FlowChartSort'
        flowChartExtract = 'FlowChartExtract'
        flowChartMerge = 'FlowChartMerge'
        flowChartOfflineStorage = 'FlowChartOfflineStorage'
        flowChartOnlineStorage = 'FlowChartOnlineStorage'
        flowChartMagneticTape = 'FlowChartMagneticTape'
        flowChartMagneticDisk = 'FlowChartMagneticDisk'
        flowChartMagneticDrum = 'FlowChartMagneticDrum'
        flowChartDisplay = 'FlowChartDisplay'
        flowChartDelay = 'FlowChartDelay'
        flowChartAlternateProcess = 'FlowChartAlternateProcess'
        flowChartOffpageConnector = 'FlowChartOffpageConnector'
        actionButtonBlank = 'ActionButtonBlank'
        actionButtonHome = 'ActionButtonHome'
        actionButtonHelp = 'ActionButtonHelp'
        actionButtonInformation = 'ActionButtonInformation'
        actionButtonForwardNext = 'ActionButtonForwardNext'
        actionButtonBackPrevious = 'ActionButtonBackPrevious'
        actionButtonEnd = 'ActionButtonEnd'
        actionButtonBeginning = 'ActionButtonBeginning'
        actionButtonReturn = 'ActionButtonReturn'
        actionButtonDocument = 'ActionButtonDocument'
        actionButtonSound = 'ActionButtonSound'
        actionButtonMovie = 'ActionButtonMovie'
        gear6 = 'Gear6'
        gear9 = 'Gear9'
        funnel = 'Funnel'
        mathPlus = 'MathPlus'
        mathMinus = 'MathMinus'
        mathMultiply = 'MathMultiply'
        mathDivide = 'MathDivide'
        mathEqual = 'MathEqual'
        mathNotEqual = 'MathNotEqual'
        cornerTabs = 'CornerTabs'
        squareTabs = 'SquareTabs'
        plaqueTabs = 'PlaqueTabs'
        chartX = 'ChartX'
        chartStar = 'ChartStar'
        chartPlus = 'ChartPlus'
    
    class ShapeFillType:
        noFill = 'NoFill'
        solid = 'Solid'
        gradient = 'Gradient'
        pattern = 'Pattern'
        picture = 'Picture'
        texture = 'Texture'
        mixed = 'Mixed'
    
    class ShapeTextVerticalAlignment:
        top = 'Top'
        middle = 'Middle'
        bottom = 'Bottom'
    
    class ShapeTextOrientation:
        none = 'None'
        horizontal = 'Horizontal'
        eastAsianVertical = 'EastAsianVertical'
        vertical270 = 'Vertical270'
        vertical = 'Vertical'
        eastAsianHorizontalRotated = 'EastAsianHorizontalRotated'
        mixed = 'Mixed'
    
    class ShapeAutoSize:
        none = 'None'
        textToFitShape = 'TextToFitShape'
        shapeToFitText = 'ShapeToFitText'
        mixed = 'Mixed'
    
    class ShapeTextWrapType:
        inline = 'Inline'
        square = 'Square'
        tight = 'Tight'
        through = 'Through'
        topBottom = 'TopBottom'
        behind = 'Behind'
        front = 'Front'
    
    class ShapeTextWrapSide:
        none = 'None'
        both = 'Both'
        left = 'Left'
        right = 'Right'
        largest = 'Largest'
    
    class ShapeScaleType:
        currentSize = 'CurrentSize'
        originalSize = 'OriginalSize'
    
    class ShapeScaleFrom:
        scaleFromTopLeft = 'ScaleFromTopLeft'
        scaleFromMiddle = 'ScaleFromMiddle'
        scaleFromBottomRight = 'ScaleFromBottomRight'
    
    class FrameSizeRule:
        auto = 'Auto'
        atLeast = 'AtLeast'
        exact = 'Exact'
    
    class BorderLineStyle:
        none = 'None'
        single = 'Single'
        dot = 'Dot'
        dashSmallGap = 'DashSmallGap'
        dashLargeGap = 'DashLargeGap'
        dashDot = 'DashDot'
        dashDotDot = 'DashDotDot'
        double = 'Double'
        triple = 'Triple'
        thinThickSmallGap = 'ThinThickSmallGap'
        thickThinSmallGap = 'ThickThinSmallGap'
        thinThickThinSmallGap = 'ThinThickThinSmallGap'
        thinThickMedGap = 'ThinThickMedGap'
        thickThinMedGap = 'ThickThinMedGap'
        thinThickThinMedGap = 'ThinThickThinMedGap'
        thinThickLargeGap = 'ThinThickLargeGap'
        thickThinLargeGap = 'ThickThinLargeGap'
        thinThickThinLargeGap = 'ThinThickThinLargeGap'
        singleWavy = 'SingleWavy'
        doubleWavy = 'DoubleWavy'
        dashDotStroked = 'DashDotStroked'
        emboss3D = 'Emboss3D'
        engrave3D = 'Engrave3D'
        outset = 'Outset'
        inset = 'Inset'
    
    class LineWidth:
        pt025 = 'Pt025'
        pt050 = 'Pt050'
        pt075 = 'Pt075'
        pt100 = 'Pt100'
        pt150 = 'Pt150'
        pt225 = 'Pt225'
        pt300 = 'Pt300'
        pt450 = 'Pt450'
        pt600 = 'Pt600'
    
    class PageBorderArt:
        apples = 'Apples'
        mapleMuffins = 'MapleMuffins'
        cakeSlice = 'CakeSlice'
        candyCorn = 'CandyCorn'
        iceCreamCones = 'IceCreamCones'
        champagneBottle = 'ChampagneBottle'
        partyGlass = 'PartyGlass'
        christmasTree = 'ChristmasTree'
        trees = 'Trees'
        palmsColor = 'PalmsColor'
        balloons3Colors = 'Balloons3Colors'
        balloonsHotAir = 'BalloonsHotAir'
        partyFavor = 'PartyFavor'
        confettiStreamers = 'ConfettiStreamers'
        hearts = 'Hearts'
        heartBalloon = 'HeartBalloon'
        stars3D = 'Stars3D'
        starsShadowed = 'StarsShadowed'
        stars = 'Stars'
        sun = 'Sun'
        earth2 = 'Earth2'
        earth1 = 'Earth1'
        peopleHats = 'PeopleHats'
        sombrero = 'Sombrero'
        pencils = 'Pencils'
        packages = 'Packages'
        clocks = 'Clocks'
        firecrackers = 'Firecrackers'
        rings = 'Rings'
        mapPins = 'MapPins'
        confetti = 'Confetti'
        creaturesButterfly = 'CreaturesButterfly'
        creaturesLadyBug = 'CreaturesLadyBug'
        creaturesFish = 'CreaturesFish'
        birdsFlight = 'BirdsFlight'
        scaredCat = 'ScaredCat'
        bats = 'Bats'
        flowersRoses = 'FlowersRoses'
        flowersRedRose = 'FlowersRedRose'
        poinsettias = 'Poinsettias'
        holly = 'Holly'
        flowersTiny = 'FlowersTiny'
        flowersPansy = 'FlowersPansy'
        flowersModern2 = 'FlowersModern2'
        flowersModern1 = 'FlowersModern1'
        whiteFlowers = 'WhiteFlowers'
        vine = 'Vine'
        flowersDaisies = 'FlowersDaisies'
        flowersBlockPrint = 'FlowersBlockPrint'
        decoArchColor = 'DecoArchColor'
        fans = 'Fans'
        film = 'Film'
        lightning1 = 'Lightning1'
        compass = 'Compass'
        doubleD = 'DoubleD'
        classicalWave = 'ClassicalWave'
        shadowedSquares = 'ShadowedSquares'
        twistedLines1 = 'TwistedLines1'
        waveline = 'Waveline'
        quadrants = 'Quadrants'
        checkedBarColor = 'CheckedBarColor'
        swirligig = 'Swirligig'
        pushPinNote1 = 'PushPinNote1'
        pushPinNote2 = 'PushPinNote2'
        pumpkin1 = 'Pumpkin1'
        eggsBlack = 'EggsBlack'
        cup = 'Cup'
        heartGray = 'HeartGray'
        gingerbreadMan = 'GingerbreadMan'
        babyPacifier = 'BabyPacifier'
        babyRattle = 'BabyRattle'
        cabins = 'Cabins'
        houseFunky = 'HouseFunky'
        starsBlack = 'StarsBlack'
        snowflakes = 'Snowflakes'
        snowflakeFancy = 'SnowflakeFancy'
        skyrocket = 'Skyrocket'
        seattle = 'Seattle'
        musicNotes = 'MusicNotes'
        palmsBlack = 'PalmsBlack'
        mapleLeaf = 'MapleLeaf'
        paperClips = 'PaperClips'
        shorebirdTracks = 'ShorebirdTracks'
        people = 'People'
        peopleWaving = 'PeopleWaving'
        eclipsingSquares2 = 'EclipsingSquares2'
        hypnotic = 'Hypnotic'
        diamondsGray = 'DiamondsGray'
        decoArch = 'DecoArch'
        decoBlocks = 'DecoBlocks'
        circlesLines = 'CirclesLines'
        papyrus = 'Papyrus'
        woodwork = 'Woodwork'
        weavingBraid = 'WeavingBraid'
        weavingRibbon = 'WeavingRibbon'
        weavingAngles = 'WeavingAngles'
        archedScallops = 'ArchedScallops'
        safari = 'Safari'
        celticKnotwork = 'CelticKnotwork'
        crazyMaze = 'CrazyMaze'
        eclipsingSquares1 = 'EclipsingSquares1'
        birds = 'Birds'
        flowersTeacup = 'FlowersTeacup'
        northwest = 'Northwest'
        southwest = 'Southwest'
        tribal6 = 'Tribal6'
        tribal4 = 'Tribal4'
        tribal3 = 'Tribal3'
        tribal2 = 'Tribal2'
        tribal5 = 'Tribal5'
        xillusions = 'XIllusions'
        zanyTriangles = 'ZanyTriangles'
        pyramids = 'Pyramids'
        pyramidsAbove = 'PyramidsAbove'
        confettiGrays = 'ConfettiGrays'
        confettiOutline = 'ConfettiOutline'
        confettiWhite = 'ConfettiWhite'
        mosaic = 'Mosaic'
        lightning2 = 'Lightning2'
        heebieJeebies = 'HeebieJeebies'
        lightBulb = 'LightBulb'
        gradient = 'Gradient'
        triangleParty = 'TriangleParty'
        twistedLines2 = 'TwistedLines2'
        moons = 'Moons'
        ovals = 'Ovals'
        doubleDiamonds = 'DoubleDiamonds'
        chainLink = 'ChainLink'
        triangles = 'Triangles'
        tribal1 = 'Tribal1'
        marqueeToothed = 'MarqueeToothed'
        sharksTeeth = 'SharksTeeth'
        sawtooth = 'Sawtooth'
        sawtoothGray = 'SawtoothGray'
        postageStamp = 'PostageStamp'
        weavingStrips = 'WeavingStrips'
        zigZag = 'ZigZag'
        crossStitch = 'CrossStitch'
        gems = 'Gems'
        circlesRectangles = 'CirclesRectangles'
        cornerTriangles = 'CornerTriangles'
        creaturesInsects = 'CreaturesInsects'
        zigZagStitch = 'ZigZagStitch'
        checkered = 'Checkered'
        checkedBarBlack = 'CheckedBarBlack'
        marquee = 'Marquee'
        basicWhiteDots = 'BasicWhiteDots'
        basicWideMidline = 'BasicWideMidline'
        basicWideOutline = 'BasicWideOutline'
        basicWideInline = 'BasicWideInline'
        basicThinLines = 'BasicThinLines'
        basicWhiteDashes = 'BasicWhiteDashes'
        basicWhiteSquares = 'BasicWhiteSquares'
        basicBlackSquares = 'BasicBlackSquares'
        basicBlackDashes = 'BasicBlackDashes'
        basicBlackDots = 'BasicBlackDots'
        starsTop = 'StarsTop'
        certificateBanner = 'CertificateBanner'
        handmade1 = 'Handmade1'
        handmade2 = 'Handmade2'
        tornPaper = 'TornPaper'
        tornPaperBlack = 'TornPaperBlack'
        couponCutoutDashes = 'CouponCutoutDashes'
        couponCutoutDots = 'CouponCutoutDots'
    
    class PreferredWidthType:
        auto = 'Auto'
        percent = 'Percent'
        points = 'Points'
    
    class RulerStyle:
        none = 'None'
        proportional = 'Proportional'
        firstColumn = 'FirstColumn'
        sameWidth = 'SameWidth'
    
    class FarEastLineBreakLanguageId:
        traditionalChinese = 'TraditionalChinese'
        japanese = 'Japanese'
        korean = 'Korean'
        simplifiedChinese = 'SimplifiedChinese'
    
    class FarEastLineBreakLevel:
        normal = 'Normal'
        strict = 'Strict'
        custom = 'Custom'
    
    class JustificationMode:
        expand = 'Expand'
        compress = 'Compress'
        compressKana = 'CompressKana'
    
    class TemplateType:
        normal = 'Normal'
        global_ = 'Global'
        attached = 'Attached'
    
    class LanguageId:
        afrikaans = 'Afrikaans'
        albanian = 'Albanian'
        amharic = 'Amharic'
        arabic = 'Arabic'
        arabicAlgeria = 'ArabicAlgeria'
        arabicBahrain = 'ArabicBahrain'
        arabicEgypt = 'ArabicEgypt'
        arabicIraq = 'ArabicIraq'
        arabicJordan = 'ArabicJordan'
        arabicKuwait = 'ArabicKuwait'
        arabicLebanon = 'ArabicLebanon'
        arabicLibya = 'ArabicLibya'
        arabicMorocco = 'ArabicMorocco'
        arabicOman = 'ArabicOman'
        arabicQatar = 'ArabicQatar'
        arabicSyria = 'ArabicSyria'
        arabicTunisia = 'ArabicTunisia'
        arabicUAE = 'ArabicUAE'
        arabicYemen = 'ArabicYemen'
        armenian = 'Armenian'
        assamese = 'Assamese'
        azeriCyrillic = 'AzeriCyrillic'
        azeriLatin = 'AzeriLatin'
        basque = 'Basque'
        belgianDutch = 'BelgianDutch'
        belgianFrench = 'BelgianFrench'
        bengali = 'Bengali'
        bulgarian = 'Bulgarian'
        burmese = 'Burmese'
        belarusian = 'Belarusian'
        catalan = 'Catalan'
        cherokee = 'Cherokee'
        chineseHongKongSAR = 'ChineseHongKongSAR'
        chineseMacaoSAR = 'ChineseMacaoSAR'
        chineseSingapore = 'ChineseSingapore'
        croatian = 'Croatian'
        czech = 'Czech'
        danish = 'Danish'
        divehi = 'Divehi'
        dutch = 'Dutch'
        edo = 'Edo'
        englishAUS = 'EnglishAUS'
        englishBelize = 'EnglishBelize'
        englishCanadian = 'EnglishCanadian'
        englishCaribbean = 'EnglishCaribbean'
        englishIndonesia = 'EnglishIndonesia'
        englishIreland = 'EnglishIreland'
        englishJamaica = 'EnglishJamaica'
        englishNewZealand = 'EnglishNewZealand'
        englishPhilippines = 'EnglishPhilippines'
        englishSouthAfrica = 'EnglishSouthAfrica'
        englishTrinidadTobago = 'EnglishTrinidadTobago'
        englishUK = 'EnglishUK'
        englishUS = 'EnglishUS'
        englishZimbabwe = 'EnglishZimbabwe'
        estonian = 'Estonian'
        faeroese = 'Faeroese'
        filipino = 'Filipino'
        finnish = 'Finnish'
        french = 'French'
        frenchCameroon = 'FrenchCameroon'
        frenchCanadian = 'FrenchCanadian'
        frenchCongoDRC = 'FrenchCongoDRC'
        frenchCotedIvoire = 'FrenchCotedIvoire'
        frenchHaiti = 'FrenchHaiti'
        frenchLuxembourg = 'FrenchLuxembourg'
        frenchMali = 'FrenchMali'
        frenchMonaco = 'FrenchMonaco'
        frenchMorocco = 'FrenchMorocco'
        frenchReunion = 'FrenchReunion'
        frenchSenegal = 'FrenchSenegal'
        frenchWestIndies = 'FrenchWestIndies'
        frisianNetherlands = 'FrisianNetherlands'
        fulfulde = 'Fulfulde'
        gaelicIreland = 'GaelicIreland'
        gaelicScotland = 'GaelicScotland'
        galician = 'Galician'
        georgian = 'Georgian'
        german = 'German'
        germanAustria = 'GermanAustria'
        germanLiechtenstein = 'GermanLiechtenstein'
        germanLuxembourg = 'GermanLuxembourg'
        greek = 'Greek'
        guarani = 'Guarani'
        gujarati = 'Gujarati'
        hausa = 'Hausa'
        hawaiian = 'Hawaiian'
        hebrew = 'Hebrew'
        hindi = 'Hindi'
        hungarian = 'Hungarian'
        ibibio = 'Ibibio'
        icelandic = 'Icelandic'
        igbo = 'Igbo'
        indonesian = 'Indonesian'
        inuktitut = 'Inuktitut'
        italian = 'Italian'
        japanese = 'Japanese'
        kannada = 'Kannada'
        kanuri = 'Kanuri'
        kashmiri = 'Kashmiri'
        kazakh = 'Kazakh'
        khmer = 'Khmer'
        kirghiz = 'Kirghiz'
        konkani = 'Konkani'
        korean = 'Korean'
        kyrgyz = 'Kyrgyz'
        languageNone = 'LanguageNone'
        lao = 'Lao'
        latin = 'Latin'
        latvian = 'Latvian'
        lithuanian = 'Lithuanian'
        macedonianFYROM = 'MacedonianFYROM'
        malayalam = 'Malayalam'
        malayBruneiDarussalam = 'MalayBruneiDarussalam'
        malaysian = 'Malaysian'
        maltese = 'Maltese'
        manipuri = 'Manipuri'
        marathi = 'Marathi'
        mexicanSpanish = 'MexicanSpanish'
        mongolian = 'Mongolian'
        nepali = 'Nepali'
        noProofing = 'NoProofing'
        norwegianBokmol = 'NorwegianBokmol'
        norwegianNynorsk = 'NorwegianNynorsk'
        oriya = 'Oriya'
        oromo = 'Oromo'
        pashto = 'Pashto'
        persian = 'Persian'
        polish = 'Polish'
        portuguese = 'Portuguese'
        portugueseBrazil = 'PortugueseBrazil'
        punjabi = 'Punjabi'
        rhaetoRomanic = 'RhaetoRomanic'
        romanian = 'Romanian'
        romanianMoldova = 'RomanianMoldova'
        russian = 'Russian'
        russianMoldova = 'RussianMoldova'
        samiLappish = 'SamiLappish'
        sanskrit = 'Sanskrit'
        serbianCyrillic = 'SerbianCyrillic'
        serbianLatin = 'SerbianLatin'
        sesotho = 'Sesotho'
        simplifiedChinese = 'SimplifiedChinese'
        sindhi = 'Sindhi'
        sindhiPakistan = 'SindhiPakistan'
        sinhalese = 'Sinhalese'
        slovak = 'Slovak'
        slovenian = 'Slovenian'
        somali = 'Somali'
        sorbian = 'Sorbian'
        spanish = 'Spanish'
        spanishArgentina = 'SpanishArgentina'
        spanishBolivia = 'SpanishBolivia'
        spanishChile = 'SpanishChile'
        spanishColombia = 'SpanishColombia'
        spanishCostaRica = 'SpanishCostaRica'
        spanishDominicanRepublic = 'SpanishDominicanRepublic'
        spanishEcuador = 'SpanishEcuador'
        spanishElSalvador = 'SpanishElSalvador'
        spanishGuatemala = 'SpanishGuatemala'
        spanishHonduras = 'SpanishHonduras'
        spanishModernSort = 'SpanishModernSort'
        spanishNicaragua = 'SpanishNicaragua'
        spanishPanama = 'SpanishPanama'
        spanishParaguay = 'SpanishParaguay'
        spanishPeru = 'SpanishPeru'
        spanishPuertoRico = 'SpanishPuertoRico'
        spanishUruguay = 'SpanishUruguay'
        spanishVenezuela = 'SpanishVenezuela'
        sutu = 'Sutu'
        swahili = 'Swahili'
        swedish = 'Swedish'
        swedishFinland = 'SwedishFinland'
        swissFrench = 'SwissFrench'
        swissGerman = 'SwissGerman'
        swissItalian = 'SwissItalian'
        syriac = 'Syriac'
        tajik = 'Tajik'
        tamazight = 'Tamazight'
        tamazightLatin = 'TamazightLatin'
        tamil = 'Tamil'
        tatar = 'Tatar'
        telugu = 'Telugu'
        thai = 'Thai'
        tibetan = 'Tibetan'
        tigrignaEritrea = 'TigrignaEritrea'
        tigrignaEthiopic = 'TigrignaEthiopic'
        traditionalChinese = 'TraditionalChinese'
        tsonga = 'Tsonga'
        tswana = 'Tswana'
        turkish = 'Turkish'
        turkmen = 'Turkmen'
        ukrainian = 'Ukrainian'
        urdu = 'Urdu'
        uzbekCyrillic = 'UzbekCyrillic'
        uzbekLatin = 'UzbekLatin'
        venda = 'Venda'
        vietnamese = 'Vietnamese'
        welsh = 'Welsh'
        xhosa = 'Xhosa'
        yi = 'Yi'
        yiddish = 'Yiddish'
        yoruba = 'Yoruba'
        zulu = 'Zulu'
    
    class DocPartInsertType:
        content = 'Content'
        paragraph = 'Paragraph'
        page = 'Page'
    
    class BuildingBlockType:
        quickParts = 'QuickParts'
        coverPage = 'CoverPage'
        equations = 'Equations'
        footers = 'Footers'
        headers = 'Headers'
        pageNumber = 'PageNumber'
        tables = 'Tables'
        watermarks = 'Watermarks'
        autoText = 'AutoText'
        textBox = 'TextBox'
        pageNumberTop = 'PageNumberTop'
        pageNumberBottom = 'PageNumberBottom'
        pageNumberPage = 'PageNumberPage'
        tableOfContents = 'TableOfContents'
        customQuickParts = 'CustomQuickParts'
        customCoverPage = 'CustomCoverPage'
        customEquations = 'CustomEquations'
        customFooters = 'CustomFooters'
        customHeaders = 'CustomHeaders'
        customPageNumber = 'CustomPageNumber'
        customTables = 'CustomTables'
        customWatermarks = 'CustomWatermarks'
        customAutoText = 'CustomAutoText'
        customTextBox = 'CustomTextBox'
        customPageNumberTop = 'CustomPageNumberTop'
        customPageNumberBottom = 'CustomPageNumberBottom'
        customPageNumberPage = 'CustomPageNumberPage'
        customTableOfContents = 'CustomTableOfContents'
        custom1 = 'Custom1'
        custom2 = 'Custom2'
        custom3 = 'Custom3'
        custom4 = 'Custom4'
        custom5 = 'Custom5'
        bibliography = 'Bibliography'
        customBibliography = 'CustomBibliography'
    
    class CustomXmlNodeType:
        element = 'element'
        attribute = 'attribute'
        text = 'text'
        cData = 'cData'
        processingInstruction = 'processingInstruction'
        comment = 'comment'
        document = 'document'
    
    class LinkType:
        ole = 'Ole'
        picture = 'Picture'
        text = 'Text'
        reference = 'Reference'
        include = 'Include'
        import_ = 'Import'
        dde = 'Dde'
        ddeAuto = 'DdeAuto'
        chart = 'Chart'
    
    class OleVerb:
        primary = 'Primary'
        show = 'Show'
        open = 'Open'
        hide = 'Hide'
        uiActivate = 'UiActivate'
        inPlaceActivate = 'InPlaceActivate'
        discardUndoState = 'DiscardUndoState'
    
    class ArrowheadLength:
        mixed = 'Mixed'
        short = 'Short'
        medium = 'Medium'
        long = 'Long'
    
    class ArrowheadStyle:
        mixed = 'Mixed'
        none = 'None'
        triangle = 'Triangle'
        open = 'Open'
        stealth = 'Stealth'
        diamond = 'Diamond'
        oval = 'Oval'
    
    class ArrowheadWidth:
        mixed = 'Mixed'
        narrow = 'Narrow'
        medium = 'Medium'
        wide = 'Wide'
    
    class BevelType:
        mixed = 'mixed'
        none = 'none'
        relaxedInset = 'relaxedInset'
        circle = 'circle'
        slope = 'slope'
        cross = 'cross'
        angle = 'angle'
        softRound = 'softRound'
        convex = 'convex'
        coolSlant = 'coolSlant'
        divot = 'divot'
        riblet = 'riblet'
        hardEdge = 'hardEdge'
        artDeco = 'artDeco'
    
    class ColorIndex:
        auto = 'Auto'
        black = 'Black'
        blue = 'Blue'
        turquoise = 'Turquoise'
        brightGreen = 'BrightGreen'
        pink = 'Pink'
        red = 'Red'
        yellow = 'Yellow'
        white = 'White'
        darkBlue = 'DarkBlue'
        teal = 'Teal'
        green = 'Green'
        violet = 'Violet'
        darkRed = 'DarkRed'
        darkYellow = 'DarkYellow'
        gray50 = 'Gray50'
        gray25 = 'Gray25'
        classicRed = 'ClassicRed'
        classicBlue = 'ClassicBlue'
        byAuthor = 'ByAuthor'
    
    class ColorType:
        rgb = 'rgb'
        scheme = 'scheme'
    
    class Continue:
        disabled = 'Disabled'
        list = 'List'
        reset = 'Reset'
    
    class DefaultListBehavior:
        word97 = 'Word97'
        word2000 = 'Word2000'
        word2002 = 'Word2002'
    
    class EmphasisMark:
        none = 'None'
        overSolidCircle = 'OverSolidCircle'
        overComma = 'OverComma'
        overWhiteCircle = 'OverWhiteCircle'
        underSolidCircle = 'UnderSolidCircle'
    
    class ExtrusionColorType:
        mixed = 'mixed'
        automatic = 'automatic'
        custom = 'custom'
    
    class FillType:
        mixed = 'Mixed'
        solid = 'Solid'
        patterned = 'Patterned'
        gradient = 'Gradient'
        textured = 'Textured'
        background = 'Background'
        picture = 'Picture'
    
    class GradientColorType:
        mixed = 'Mixed'
        oneColor = 'OneColor'
        twoColors = 'TwoColors'
        presetColors = 'PresetColors'
        multiColor = 'MultiColor'
    
    class GradientStyle:
        mixed = 'Mixed'
        horizontal = 'Horizontal'
        vertical = 'Vertical'
        diagonalUp = 'DiagonalUp'
        diagonalDown = 'DiagonalDown'
        fromCorner = 'FromCorner'
        fromTitle = 'FromTitle'
        fromCenter = 'FromCenter'
    
    class Ligature:
        none = 'None'
        standard = 'Standard'
        contextual = 'Contextual'
        standardContextual = 'StandardContextual'
        historical = 'Historical'
        standardHistorical = 'StandardHistorical'
        contextualHistorical = 'ContextualHistorical'
        standardContextualHistorical = 'StandardContextualHistorical'
        discretional = 'Discretional'
        standardDiscretional = 'StandardDiscretional'
        contextualDiscretional = 'ContextualDiscretional'
        standardContextualDiscretional = 'StandardContextualDiscretional'
        historicalDiscretional = 'HistoricalDiscretional'
        standardHistoricalDiscretional = 'StandardHistoricalDiscretional'
        contextualHistoricalDiscretional = 'ContextualHistoricalDiscretional'
        all = 'All'
    
    class LightRigType:
        mixed = 'Mixed'
        legacyFlat1 = 'LegacyFlat1'
        legacyFlat2 = 'LegacyFlat2'
        legacyFlat3 = 'LegacyFlat3'
        legacyFlat4 = 'LegacyFlat4'
        legacyNormal1 = 'LegacyNormal1'
        legacyNormal2 = 'LegacyNormal2'
        legacyNormal3 = 'LegacyNormal3'
        legacyNormal4 = 'LegacyNormal4'
        legacyHarsh1 = 'LegacyHarsh1'
        legacyHarsh2 = 'LegacyHarsh2'
        legacyHarsh3 = 'LegacyHarsh3'
        legacyHarsh4 = 'LegacyHarsh4'
        threePoint = 'ThreePoint'
        balanced = 'Balanced'
        soft = 'Soft'
        harsh = 'Harsh'
        flood = 'Flood'
        contrasting = 'Contrasting'
        morning = 'Morning'
        sunrise = 'Sunrise'
        sunset = 'Sunset'
        chilly = 'Chilly'
        freezing = 'Freezing'
        flat = 'Flat'
        twoPoint = 'TwoPoint'
        glow = 'Glow'
        brightRoom = 'BrightRoom'
    
    class LineDashStyle:
        mixed = 'Mixed'
        solid = 'Solid'
        squareDot = 'SquareDot'
        roundDot = 'RoundDot'
        dash = 'Dash'
        dashDot = 'DashDot'
        dashDotDot = 'DashDotDot'
        longDash = 'LongDash'
        longDashDot = 'LongDashDot'
        longDashDotDot = 'LongDashDotDot'
        sysDash = 'SysDash'
        sysDot = 'SysDot'
        sysDashDot = 'SysDashDot'
    
    class LineFormatStyle:
        mixed = 'Mixed'
        single = 'Single'
        thinThin = 'ThinThin'
        thinThick = 'ThinThick'
        thickThin = 'ThickThin'
        thickBetweenThin = 'ThickBetweenThin'
    
    class ListApplyTo:
        wholeList = 'WholeList'
        thisPointForward = 'ThisPointForward'
        selection = 'Selection'
    
    class ListType:
        listNoNumbering = 'ListNoNumbering'
        listListNumOnly = 'ListListNumOnly'
        listBullet = 'ListBullet'
        listSimpleNumbering = 'ListSimpleNumbering'
        listOutlineNumbering = 'ListOutlineNumbering'
        listMixedNumbering = 'ListMixedNumbering'
        listPictureBullet = 'ListPictureBullet'
    
    class NumberForm:
        default = 'Default'
        lining = 'Lining'
        oldStyle = 'OldStyle'
    
    class NumberSpacing:
        default = 'Default'
        proportional = 'Proportional'
        tabular = 'Tabular'
    
    class NumberType:
        paragraph = 'Paragraph'
        listNum = 'ListNum'
        allNumbers = 'AllNumbers'
    
    class PatternType:
        mixed = 'Mixed'
        percent5 = 'Percent5'
        percent10 = 'Percent10'
        percent20 = 'Percent20'
        percent25 = 'Percent25'
        percent30 = 'Percent30'
        percent40 = 'Percent40'
        percent50 = 'Percent50'
        percent60 = 'Percent60'
        percent70 = 'Percent70'
        percent75 = 'Percent75'
        percent80 = 'Percent80'
        percent90 = 'Percent90'
        darkHorizontal = 'DarkHorizontal'
        darkVertical = 'DarkVertical'
        darkDownwardDiagonal = 'DarkDownwardDiagonal'
        darkUpwardDiagonal = 'DarkUpwardDiagonal'
        smallCheckerBoard = 'SmallCheckerBoard'
        trellis = 'Trellis'
        lightHorizontal = 'LightHorizontal'
        lightVertical = 'LightVertical'
        lightDownwardDiagonal = 'LightDownwardDiagonal'
        lightUpwardDiagonal = 'LightUpwardDiagonal'
        smallGrid = 'SmallGrid'
        dottedDiamond = 'DottedDiamond'
        wideDownwardDiagonal = 'WideDownwardDiagonal'
        wideUpwardDiagonal = 'WideUpwardDiagonal'
        dashedUpwardDiagonal = 'DashedUpwardDiagonal'
        dashedDownwardDiagonal = 'DashedDownwardDiagonal'
        narrowVertical = 'NarrowVertical'
        narrowHorizontal = 'NarrowHorizontal'
        dashedVertical = 'DashedVertical'
        dashedHorizontal = 'DashedHorizontal'
        largeConfetti = 'LargeConfetti'
        largeGrid = 'LargeGrid'
        horizontalBrick = 'HorizontalBrick'
        largeCheckerBoard = 'LargeCheckerBoard'
        smallConfetti = 'SmallConfetti'
        zigZag = 'ZigZag'
        solidDiamond = 'SolidDiamond'
        diagonalBrick = 'DiagonalBrick'
        outlinedDiamond = 'OutlinedDiamond'
        plaid = 'Plaid'
        sphere = 'Sphere'
        weave = 'Weave'
        dottedGrid = 'DottedGrid'
        divot = 'Divot'
        shingle = 'Shingle'
        wave = 'Wave'
        horizontal = 'Horizontal'
        vertical = 'Vertical'
        cross = 'Cross'
        downwardDiagonal = 'DownwardDiagonal'
        upwardDiagonal = 'UpwardDiagonal'
        diagonalCross = 'DiagonalCross'
    
    class PresetCamera:
        mixed = 'Mixed'
        legacyObliqueTopLeft = 'LegacyObliqueTopLeft'
        legacyObliqueTop = 'LegacyObliqueTop'
        legacyObliqueTopRight = 'LegacyObliqueTopRight'
        legacyObliqueLeft = 'LegacyObliqueLeft'
        legacyObliqueFront = 'LegacyObliqueFront'
        legacyObliqueRight = 'LegacyObliqueRight'
        legacyObliqueBottomLeft = 'LegacyObliqueBottomLeft'
        legacyObliqueBottom = 'LegacyObliqueBottom'
        legacyObliqueBottomRight = 'LegacyObliqueBottomRight'
        legacyPerspectiveTopLeft = 'LegacyPerspectiveTopLeft'
        legacyPerspectiveTop = 'LegacyPerspectiveTop'
        legacyPerspectiveTopRight = 'LegacyPerspectiveTopRight'
        legacyPerspectiveLeft = 'LegacyPerspectiveLeft'
        legacyPerspectiveFront = 'LegacyPerspectiveFront'
        legacyPerspectiveRight = 'LegacyPerspectiveRight'
        legacyPerspectiveBottomLeft = 'LegacyPerspectiveBottomLeft'
        legacyPerspectiveBottom = 'LegacyPerspectiveBottom'
        legacyPerspectiveBottomRight = 'LegacyPerspectiveBottomRight'
        orthographicFront = 'OrthographicFront'
        isometricTopUp = 'IsometricTopUp'
        isometricTopDown = 'IsometricTopDown'
        isometricBottomUp = 'IsometricBottomUp'
        isometricBottomDown = 'IsometricBottomDown'
        isometricLeftUp = 'IsometricLeftUp'
        isometricLeftDown = 'IsometricLeftDown'
        isometricRightUp = 'IsometricRightUp'
        isometricRightDown = 'IsometricRightDown'
        isometricOffAxis1Left = 'IsometricOffAxis1Left'
        isometricOffAxis1Right = 'IsometricOffAxis1Right'
        isometricOffAxis1Top = 'IsometricOffAxis1Top'
        isometricOffAxis2Left = 'IsometricOffAxis2Left'
        isometricOffAxis2Right = 'IsometricOffAxis2Right'
        isometricOffAxis2Top = 'IsometricOffAxis2Top'
        isometricOffAxis3Left = 'IsometricOffAxis3Left'
        isometricOffAxis3Right = 'IsometricOffAxis3Right'
        isometricOffAxis3Bottom = 'IsometricOffAxis3Bottom'
        isometricOffAxis4Left = 'IsometricOffAxis4Left'
        isometricOffAxis4Right = 'IsometricOffAxis4Right'
        isometricOffAxis4Bottom = 'IsometricOffAxis4Bottom'
        obliqueTopLeft = 'ObliqueTopLeft'
        obliqueTop = 'ObliqueTop'
        obliqueTopRight = 'ObliqueTopRight'
        obliqueLeft = 'ObliqueLeft'
        obliqueRight = 'ObliqueRight'
        obliqueBottomLeft = 'ObliqueBottomLeft'
        obliqueBottom = 'ObliqueBottom'
        obliqueBottomRight = 'ObliqueBottomRight'
        perspectiveFront = 'PerspectiveFront'
        perspectiveLeft = 'PerspectiveLeft'
        perspectiveRight = 'PerspectiveRight'
        perspectiveAbove = 'PerspectiveAbove'
        perspectiveBelow = 'PerspectiveBelow'
        perspectiveAboveLeftFacing = 'PerspectiveAboveLeftFacing'
        perspectiveAboveRightFacing = 'PerspectiveAboveRightFacing'
        perspectiveContrastingLeftFacing = 'PerspectiveContrastingLeftFacing'
        perspectiveContrastingRightFacing = 'PerspectiveContrastingRightFacing'
        perspectiveHeroicLeftFacing = 'PerspectiveHeroicLeftFacing'
        perspectiveHeroicRightFacing = 'PerspectiveHeroicRightFacing'
        perspectiveHeroicExtremeLeftFacing = 'PerspectiveHeroicExtremeLeftFacing'
        perspectiveHeroicExtremeRightFacing = 'PerspectiveHeroicExtremeRightFacing'
        perspectiveRelaxed = 'PerspectiveRelaxed'
        perspectiveRelaxedModerately = 'PerspectiveRelaxedModerately'
    
    class PresetExtrusionDirection:
        mixed = 'Mixed'
        bottomRight = 'BottomRight'
        bottom = 'Bottom'
        bottomLeft = 'BottomLeft'
        right = 'Right'
        none = 'None'
        left = 'Left'
        topRight = 'TopRight'
        top = 'Top'
        topLeft = 'TopLeft'
    
    class PresetGradientType:
        mixed = 'Mixed'
        earlySunset = 'EarlySunset'
        lateSunset = 'LateSunset'
        nightfall = 'Nightfall'
        daybreak = 'Daybreak'
        horizon = 'Horizon'
        desert = 'Desert'
        ocean = 'Ocean'
        calmWater = 'CalmWater'
        fire = 'Fire'
        fog = 'Fog'
        moss = 'Moss'
        peacock = 'Peacock'
        wheat = 'Wheat'
        parchment = 'Parchment'
        mahogany = 'Mahogany'
        rainbow = 'Rainbow'
        rainbowII = 'RainbowII'
        gold = 'Gold'
        goldII = 'GoldII'
        brass = 'Brass'
        chrome = 'Chrome'
        chromeII = 'ChromeII'
        silver = 'Silver'
        sapphire = 'Sapphire'
    
    class PresetLightingDirection:
        mixed = 'Mixed'
        topLeft = 'TopLeft'
        top = 'Top'
        topRight = 'TopRight'
        left = 'Left'
        none = 'None'
        right = 'Right'
        bottomLeft = 'BottomLeft'
        bottom = 'Bottom'
        bottomRight = 'BottomRight'
    
    class PresetLightingSoftness:
        mixed = 'Mixed'
        dim = 'Dim'
        normal = 'Normal'
        bright = 'Bright'
    
    class PresetMaterial:
        mixed = 'Mixed'
        matte = 'Matte'
        plastic = 'Plastic'
        metal = 'Metal'
        wireFrame = 'WireFrame'
        matte2 = 'Matte2'
        plastic2 = 'Plastic2'
        metal2 = 'Metal2'
        warmMatte = 'WarmMatte'
        translucentPowder = 'TranslucentPowder'
        powder = 'Powder'
        darkEdge = 'DarkEdge'
        softEdge = 'SoftEdge'
        clear = 'Clear'
        flat = 'Flat'
        softMetal = 'SoftMetal'
    
    class PresetTexture:
        mixed = 'Mixed'
        papyrus = 'Papyrus'
        canvas = 'Canvas'
        denim = 'Denim'
        wovenMat = 'WovenMat'
        waterDroplets = 'WaterDroplets'
        paperBag = 'PaperBag'
        fishFossil = 'FishFossil'
        sand = 'Sand'
        greenMarble = 'GreenMarble'
        whiteMarble = 'WhiteMarble'
        brownMarble = 'BrownMarble'
        granite = 'Granite'
        newsprint = 'Newsprint'
        recycledPaper = 'RecycledPaper'
        parchment = 'Parchment'
        stationery = 'Stationery'
        blueTissuePaper = 'BlueTissuePaper'
        pinkTissuePaper = 'PinkTissuePaper'
        purpleMesh = 'PurpleMesh'
        bouquet = 'Bouquet'
        cork = 'Cork'
        walnut = 'Walnut'
        oak = 'Oak'
        mediumWood = 'MediumWood'
    
    class PresetThreeDimensionalFormat:
        mixed = 'Mixed'
        format1 = 'Format1'
        format2 = 'Format2'
        format3 = 'Format3'
        format4 = 'Format4'
        format5 = 'Format5'
        format6 = 'Format6'
        format7 = 'Format7'
        format8 = 'Format8'
        format9 = 'Format9'
        format10 = 'Format10'
        format11 = 'Format11'
        format12 = 'Format12'
        format13 = 'Format13'
        format14 = 'Format14'
        format15 = 'Format15'
        format16 = 'Format16'
        format17 = 'Format17'
        format18 = 'Format18'
        format19 = 'Format19'
        format20 = 'Format20'
    
    class ReflectionType:
        mixed = 'Mixed'
        none = 'None'
        type1 = 'Type1'
        type2 = 'Type2'
        type3 = 'Type3'
        type4 = 'Type4'
        type5 = 'Type5'
        type6 = 'Type6'
        type7 = 'Type7'
        type8 = 'Type8'
        type9 = 'Type9'
    
    class ShadowStyle:
        mixed = 'Mixed'
        outerShadow = 'OuterShadow'
        innerShadow = 'InnerShadow'
    
    class ShadowType:
        mixed = 'Mixed'
        type1 = 'Type1'
        type2 = 'Type2'
        type3 = 'Type3'
        type4 = 'Type4'
        type5 = 'Type5'
        type6 = 'Type6'
        type7 = 'Type7'
        type8 = 'Type8'
        type9 = 'Type9'
        type10 = 'Type10'
        type11 = 'Type11'
        type12 = 'Type12'
        type13 = 'Type13'
        type14 = 'Type14'
        type15 = 'Type15'
        type16 = 'Type16'
        type17 = 'Type17'
        type18 = 'Type18'
        type19 = 'Type19'
        type20 = 'Type20'
        type21 = 'Type21'
        type22 = 'Type22'
        type23 = 'Type23'
        type24 = 'Type24'
        type25 = 'Type25'
        type26 = 'Type26'
        type27 = 'Type27'
        type28 = 'Type28'
        type29 = 'Type29'
        type30 = 'Type30'
        type31 = 'Type31'
        type32 = 'Type32'
        type33 = 'Type33'
        type34 = 'Type34'
        type35 = 'Type35'
        type36 = 'Type36'
        type37 = 'Type37'
        type38 = 'Type38'
        type39 = 'Type39'
        type40 = 'Type40'
        type41 = 'Type41'
        type42 = 'Type42'
        type43 = 'Type43'
    
    class StylisticSet:
        default = 'Default'
        set01 = 'Set01'
        set02 = 'Set02'
        set03 = 'Set03'
        set04 = 'Set04'
        set05 = 'Set05'
        set06 = 'Set06'
        set07 = 'Set07'
        set08 = 'Set08'
        set09 = 'Set09'
        set10 = 'Set10'
        set11 = 'Set11'
        set12 = 'Set12'
        set13 = 'Set13'
        set14 = 'Set14'
        set15 = 'Set15'
        set16 = 'Set16'
        set17 = 'Set17'
        set18 = 'Set18'
        set19 = 'Set19'
        set20 = 'Set20'
    
    class TextureAlignment:
        mixed = 'Mixed'
        topLeft = 'TopLeft'
        top = 'Top'
        topRight = 'TopRight'
        left = 'Left'
        center = 'Center'
        right = 'Right'
        bottomLeft = 'BottomLeft'
        bottom = 'Bottom'
        bottomRight = 'BottomRight'
    
    class TextureType:
        mixed = 'Mixed'
        preset = 'Preset'
        userDefined = 'UserDefined'
    
    class ThemeColorIndex:
        notThemeColor = 'NotThemeColor'
        mainDark1 = 'MainDark1'
        mainLight1 = 'MainLight1'
        mainDark2 = 'MainDark2'
        mainLight2 = 'MainLight2'
        accent1 = 'Accent1'
        accent2 = 'Accent2'
        accent3 = 'Accent3'
        accent4 = 'Accent4'
        accent5 = 'Accent5'
        accent6 = 'Accent6'
        hyperlink = 'Hyperlink'
        hyperlinkFollowed = 'HyperlinkFollowed'
        background1 = 'Background1'
        text1 = 'Text1'
        background2 = 'Background2'
        text2 = 'Text2'
    
    class HyperlinkType:
        range = 'Range'
        shape = 'Shape'
        inlineShape = 'InlineShape'
    
    class CharacterCase:
        next = 'Next'
        lower = 'Lower'
        upper = 'Upper'
        titleWord = 'TitleWord'
        titleSentence = 'TitleSentence'
        toggle = 'Toggle'
        halfWidth = 'HalfWidth'
        fullWidth = 'FullWidth'
        katakana = 'Katakana'
        hiragana = 'Hiragana'
    
    class CharacterWidth:
        half = 'Half'
        full = 'Full'
    
    class SeekView:
        mainDocument = 'MainDocument'
        primaryHeader = 'PrimaryHeader'
        firstPageHeader = 'FirstPageHeader'
        evenPagesHeader = 'EvenPagesHeader'
        primaryFooter = 'PrimaryFooter'
        firstPageFooter = 'FirstPageFooter'
        evenPagesFooter = 'EvenPagesFooter'
        footnotes = 'Footnotes'
        endnotes = 'Endnotes'
        currentPageHeader = 'CurrentPageHeader'
        currentPageFooter = 'CurrentPageFooter'
    
    class ShowSourceDocuments:
        none = 'None'
        original = 'Original'
        revised = 'Revised'
        both = 'Both'
    
    class SpecialPane:
        none = 'None'
        primaryHeader = 'PrimaryHeader'
        firstPageHeader = 'FirstPageHeader'
        evenPagesHeader = 'EvenPagesHeader'
        primaryFooter = 'PrimaryFooter'
        firstPageFooter = 'FirstPageFooter'
        evenPagesFooter = 'EvenPagesFooter'
        footnotes = 'Footnotes'
        endnotes = 'Endnotes'
        footnoteContinuationNotice = 'FootnoteContinuationNotice'
        footnoteContinuationSeparator = 'FootnoteContinuationSeparator'
        footnoteSeparator = 'FootnoteSeparator'
        endnoteContinuationNotice = 'EndnoteContinuationNotice'
        endnoteContinuationSeparator = 'EndnoteContinuationSeparator'
        endnoteSeparator = 'EndnoteSeparator'
        comments = 'Comments'
        currentPageHeader = 'CurrentPageHeader'
        currentPageFooter = 'CurrentPageFooter'
        revisions = 'Revisions'
        revisionsHoriz = 'RevisionsHoriz'
        revisionsVert = 'RevisionsVert'
    
    class SaveConfiguration:
        doNotSaveChanges = 'DoNotSaveChanges'
        saveChanges = 'SaveChanges'
        promptToSaveChanges = 'PromptToSaveChanges'
    
    class PageColor:
        none = 'None'
        sepia = 'Sepia'
        inverse = 'Inverse'
    
    class PageMovementType:
        vertical = 'Vertical'
        sideToSide = 'SideToSide'
    
    class ReadingLayoutMargin:
        automatic = 'Automatic'
        suppress = 'Suppress'
        full = 'Full'
    
    class RevisionsBalloonMargin:
        left = 'Left'
        right = 'Right'
    
    class RevisionsBalloonWidthType:
        percent = 'Percent'
        points = 'Points'
    
    class RevisionsMarkup:
        none = 'None'
        simple = 'Simple'
        all = 'All'
    
    class RevisionsMode:
        balloon = 'Balloon'
        inline = 'Inline'
        mixed = 'Mixed'
    
    class RevisionsView:
        final = 'Final'
        original = 'Original'
    
    class RevisionType:
        none = 'None'
        insert = 'Insert'
        delete = 'Delete'
        property = 'Property'
        paragraphNumber = 'ParagraphNumber'
        displayField = 'DisplayField'
        reconcile = 'Reconcile'
        conflict = 'Conflict'
        style = 'Style'
        replace = 'Replace'
        paragraphProperty = 'ParagraphProperty'
        tableProperty = 'TableProperty'
        sectionProperty = 'SectionProperty'
        styleDefinition = 'StyleDefinition'
        movedFrom = 'MovedFrom'
        movedTo = 'MovedTo'
        cellInsertion = 'CellInsertion'
        cellDeletion = 'CellDeletion'
        cellMerge = 'CellMerge'
        cellSplit = 'CellSplit'
        conflictInsert = 'ConflictInsert'
        conflictDelete = 'ConflictDelete'
    
    class ColumnWidth:
        narrow = 'Narrow'
        default = 'Default'
        wide = 'Wide'
    
    class FieldShading:
        never = 'Never'
        always = 'Always'
        whenSelected = 'WhenSelected'
    
    class HorizontalInVerticalType:
        none = 'None'
        fitInLine = 'FitInLine'
        resizeLine = 'ResizeLine'
    
    class ImeMode:
        noControl = 'NoControl'
        on = 'On'
        off = 'Off'
        hiragana = 'Hiragana'
        katakana = 'Katakana'
        katakanaHalf = 'KatakanaHalf'
        alphaFull = 'AlphaFull'
        alpha = 'Alpha'
        hangulFull = 'HangulFull'
        hangul = 'Hangul'
    
    class Kana:
        katakana = 'Katakana'
        hiragana = 'Hiragana'
    
    class TwoLinesInOneType:
        none = 'None'
        noBrackets = 'NoBrackets'
        parentheses = 'Parentheses'
        squareBrackets = 'SquareBrackets'
        angleBrackets = 'AngleBrackets'
        curlyBrackets = 'CurlyBrackets'
    
    class ViewType:
        normal = 'Normal'
        outline = 'Outline'
        print = 'Print'
        printPreview = 'PrintPreview'
        master = 'Master'
        web = 'Web'
        reading = 'Reading'
        conflict = 'Conflict'
    
    class WindowState:
        normal = 'Normal'
        maximize = 'Maximize'
        minimize = 'Minimize'
    
    class WindowType:
        document = 'Document'
        template = 'Template'
    
    class FlowDirection:
        leftToRight = 'LeftToRight'
        rightToLeft = 'RightToLeft'
    
    class GutterPosition:
        left = 'Left'
        right = 'Right'
        top = 'Top'
    
    class GutterStyle:
        bidirectional = 'Bidirectional'
        latin = 'Latin'
    
    class LayoutMode:
        default = 'Default'
        grid = 'Grid'
        lineGrid = 'LineGrid'
        genko = 'Genko'
    
    class NumberingRule:
        restartContinuous = 'RestartContinuous'
        restartSection = 'RestartSection'
        restartPage = 'RestartPage'
    
    class PageOrientation:
        portrait = 'Portrait'
        landscape = 'Landscape'
    
    class PageSetupVerticalAlignment:
        top = 'Top'
        center = 'Center'
        justify = 'Justify'
        bottom = 'Bottom'
    
    class PaperSize:
        size10x14 = 'Size10x14'
        size11x17 = 'Size11x17'
        letter = 'Letter'
        letterSmall = 'LetterSmall'
        legal = 'Legal'
        executive = 'Executive'
        a3 = 'A3'
        a4 = 'A4'
        a4Small = 'A4Small'
        a5 = 'A5'
        b4 = 'B4'
        b5 = 'B5'
        csheet = 'CSheet'
        dsheet = 'DSheet'
        esheet = 'ESheet'
        fanfoldLegalGerman = 'FanfoldLegalGerman'
        fanfoldStdGerman = 'FanfoldStdGerman'
        fanfoldUS = 'FanfoldUS'
        folio = 'Folio'
        ledger = 'Ledger'
        note = 'Note'
        quarto = 'Quarto'
        statement = 'Statement'
        tabloid = 'Tabloid'
        envelope9 = 'Envelope9'
        envelope10 = 'Envelope10'
        envelope11 = 'Envelope11'
        envelope12 = 'Envelope12'
        envelope14 = 'Envelope14'
        envelopeB4 = 'EnvelopeB4'
        envelopeB5 = 'EnvelopeB5'
        envelopeB6 = 'EnvelopeB6'
        envelopeC3 = 'EnvelopeC3'
        envelopeC4 = 'EnvelopeC4'
        envelopeC5 = 'EnvelopeC5'
        envelopeC6 = 'EnvelopeC6'
        envelopeC65 = 'EnvelopeC65'
        envelopeDL = 'EnvelopeDL'
        envelopeItaly = 'EnvelopeItaly'
        envelopeMonarch = 'EnvelopeMonarch'
        envelopePersonal = 'EnvelopePersonal'
        custom = 'Custom'
    
    class SectionDirection:
        rightToLeft = 'RightToLeft'
        leftToRight = 'LeftToRight'
    
    class SectionStart:
        continuous = 'Continuous'
        newColumn = 'NewColumn'
        newPage = 'NewPage'
        evenPage = 'EvenPage'
        oddPage = 'OddPage'
    
    class AutoFitBehavior:
        fixedSize = 'FixedSize'
        content = 'Content'
        window = 'Window'
    
    class CalendarTypeBidirectional:
        gregorian = 'Gregorian'
        bidirectional = 'Bidirectional'
    
    class CaptionPosition:
        above = 'Above'
        below = 'Below'
    
    class CollapseDirection:
        start = 'Start'
        end = 'End'
    
    class DateLanguage:
        bidirectional = 'Bidirectional'
        latin = 'Latin'
    
    class FontBias:
        standard = 'Standard'
        farEast = 'FarEast'
        noSpecified = 'NoSpecified'
    
    class GoToDirection:
        first = 'First'
        last = 'Last'
        next = 'Next'
        previous = 'Previous'
    
    class GoToItem:
        bookmark = 'Bookmark'
        comment = 'Comment'
        endnote = 'Endnote'
        field = 'Field'
        footnote = 'Footnote'
        graphic = 'Graphic'
        heading = 'Heading'
        line = 'Line'
        page = 'Page'
        section = 'Section'
        table = 'Table'
        embeddedObject = 'EmbeddedObject'
        equation = 'Equation'
        percent = 'Percent'
        spellingError = 'SpellingError'
        grammaticalError = 'GrammaticalError'
        proofreadingError = 'ProofreadingError'
    
    class MovementType:
        move = 'Move'
        extend = 'Extend'
    
    class OperationUnit:
        character = 'Character'
        word = 'Word'
        sentence = 'Sentence'
        paragraph = 'Paragraph'
        line = 'Line'
        story = 'Story'
        screen = 'Screen'
        section = 'Section'
        column = 'Column'
        row = 'Row'
        window = 'Window'
        cell = 'Cell'
        characterFormat = 'CharacterFormat'
        paragraphFormat = 'ParagraphFormat'
        table = 'Table'
        item = 'Item'
    
    class PasteFormatType:
        pasteDefault = 'PasteDefault'
        singleCellText = 'SingleCellText'
        singleCellTable = 'SingleCellTable'
        listContinueNumbering = 'ListContinueNumbering'
        listRestartNumbering = 'ListRestartNumbering'
        tableAppendTable = 'TableAppendTable'
        tableInsertAsRows = 'TableInsertAsRows'
        tableOriginalFormatting = 'TableOriginalFormatting'
        chartPicture = 'ChartPicture'
        chart = 'Chart'
        chartLinked = 'ChartLinked'
        formatOriginalFormatting = 'FormatOriginalFormatting'
        formatSurroundingFormattingWithEmphasis = 'FormatSurroundingFormattingWithEmphasis'
        formatPlainText = 'FormatPlainText'
        tableOverwriteCells = 'TableOverwriteCells'
        listCombineWithExistingList = 'ListCombineWithExistingList'
        listDontMerge = 'ListDontMerge'
        useDestinationStylesRecovery = 'UseDestinationStylesRecovery'
    
    class ReferenceType:
        numberedItem = 'NumberedItem'
        heading = 'Heading'
        bookmark = 'Bookmark'
        footnote = 'Footnote'
        endnote = 'Endnote'
    
    class SelectionType:
        noSelection = 'NoSelection'
        insertionPoint = 'InsertionPoint'
        normal = 'Normal'
        frame = 'Frame'
        column = 'Column'
        row = 'Row'
        block = 'Block'
        inlineShape = 'InlineShape'
        selectionShape = 'SelectionShape'
    
    class SortFieldType:
        alphanumeric = 'Alphanumeric'
        numeric = 'Numeric'
        date = 'Date'
        syllable = 'Syllable'
        japanJis = 'JapanJis'
        stroke = 'Stroke'
        koreaKs = 'KoreaKs'
    
    class SortOrder:
        ascending = 'Ascending'
        descending = 'Descending'
    
    class TableCellInsertionLocation:
        shiftRight = 'ShiftRight'
        shiftDown = 'ShiftDown'
        shiftRowDown = 'ShiftRowDown'
        shiftColumnRight = 'ShiftColumnRight'
    
    class TextOrientation:
        horizontal = 'Horizontal'
        upward = 'Upward'
        downward = 'Downward'
        verticalFarEast = 'VerticalFarEast'
        horizontalRotatedFarEast = 'HorizontalRotatedFarEast'
        vertical = 'Vertical'
    
    class StoryType:
        mainText = 'MainText'
        footnotes = 'Footnotes'
        endnotes = 'Endnotes'
        comments = 'Comments'
        textFrame = 'TextFrame'
        evenPagesHeader = 'EvenPagesHeader'
        primaryHeader = 'PrimaryHeader'
        evenPagesFooter = 'EvenPagesFooter'
        primaryFooter = 'PrimaryFooter'
        firstPageHeader = 'FirstPageHeader'
        firstPageFooter = 'FirstPageFooter'
        footnoteSeparator = 'FootnoteSeparator'
        footnoteContinuationSeparator = 'FootnoteContinuationSeparator'
        footnoteContinuationNotice = 'FootnoteContinuationNotice'
        endnoteSeparator = 'EndnoteSeparator'
        endnoteContinuationSeparator = 'EndnoteContinuationSeparator'
        endnoteContinuationNotice = 'EndnoteContinuationNotice'
    
    class HeadingSeparator:
        none = 'None'
        blankLine = 'BlankLine'
        letter = 'Letter'
        letterLow = 'LetterLow'
        letterFull = 'LetterFull'
    
    class DropPosition:
        none = 'None'
        normal = 'Normal'
        margin = 'Margin'
    
    class TabAlignment:
        left = 'Left'
        center = 'Center'
        right = 'Right'
        decimal = 'Decimal'
        bar = 'Bar'
        list = 'List'
    
    class IndexFilter:
        none = 'None'
        aiueo = 'Aiueo'
        akasatana = 'Akasatana'
        chosung = 'Chosung'
        low = 'Low'
        medium = 'Medium'
        full = 'Full'
    
    class IndexFormat:
        template = 'Template'
        classic = 'Classic'
        fancy = 'Fancy'
        modern = 'Modern'
        bulleted = 'Bulleted'
        formal = 'Formal'
        simple = 'Simple'
    
    class IndexSortBy:
        stroke = 'Stroke'
        syllable = 'Syllable'
    
    class IndexType:
        indent = 'Indent'
        runin = 'Runin'
    
    class TabLeader:
        spaces = 'Spaces'
        dots = 'Dots'
        dashes = 'Dashes'
        lines = 'Lines'
        heavy = 'Heavy'
        middleDot = 'MiddleDot'
    
    class ConditionCode:
        firstRow = 'FirstRow'
        lastRow = 'LastRow'
        oddRowBanding = 'OddRowBanding'
        evenRowBanding = 'EvenRowBanding'
        firstColumn = 'FirstColumn'
        lastColumn = 'LastColumn'
        oddColumnBanding = 'OddColumnBanding'
        evenColumnBanding = 'EvenColumnBanding'
        topRightCell = 'TopRightCell'
        topLeftCell = 'TopLeftCell'
        bottomRightCell = 'BottomRightCell'
        bottomLeftCell = 'BottomLeftCell'
    
    class DeleteCells:
        shiftLeft = 'ShiftLeft'
        shiftUp = 'ShiftUp'
        entireRow = 'EntireRow'
        entireColumn = 'EntireColumn'
    
    class RowHeightRule:
        auto = 'Auto'
        atLeast = 'AtLeast'
        exactly = 'Exactly'
    
    class TableDirection:
        rightToLeft = 'RightToLeft'
        leftToRight = 'LeftToRight'
    
    class TableFieldSeparator:
        paragraph = 'Paragraph'
        tab = 'Tab'
        comma = 'Comma'
        defaultListSeparator = 'DefaultListSeparator'
    
    class TableFormatType:
        none = 'None'
        simple1 = 'Simple1'
        simple2 = 'Simple2'
        simple3 = 'Simple3'
        classic1 = 'Classic1'
        classic2 = 'Classic2'
        classic3 = 'Classic3'
        classic4 = 'Classic4'
        colorful1 = 'Colorful1'
        colorful2 = 'Colorful2'
        colorful3 = 'Colorful3'
        columns1 = 'Columns1'
        columns2 = 'Columns2'
        columns3 = 'Columns3'
        columns4 = 'Columns4'
        columns5 = 'Columns5'
        grid1 = 'Grid1'
        grid2 = 'Grid2'
        grid3 = 'Grid3'
        grid4 = 'Grid4'
        grid5 = 'Grid5'
        grid6 = 'Grid6'
        grid7 = 'Grid7'
        grid8 = 'Grid8'
        list1 = 'List1'
        list2 = 'List2'
        list3 = 'List3'
        list4 = 'List4'
        list5 = 'List5'
        list6 = 'List6'
        list7 = 'List7'
        list8 = 'List8'
        threeDEffects1 = 'ThreeDEffects1'
        threeDEffects2 = 'ThreeDEffects2'
        threeDEffects3 = 'ThreeDEffects3'
        contemporary = 'Contemporary'
        elegant = 'Elegant'
        professional = 'Professional'
        subtle1 = 'Subtle1'
        subtle2 = 'Subtle2'
        web1 = 'Web1'
        web2 = 'Web2'
        web3 = 'Web3'
    
    class ListTemplateGalleryType:
        bullets = 'Bullets'
        number = 'Number'
        outlineNumbered = 'OutlineNumbered'
    
    class CoauthoringLockType:
        none = 'None'
        reservation = 'Reservation'
        ephemeral = 'Ephemeral'
        changed = 'Changed'
    
    class EditorType:
        current = 'Current'
        editors = 'Editors'
        everyone = 'Everyone'
        owners = 'Owners'
    
    class ErrorCodes:
        accessDenied = 'AccessDenied'
        generalException = 'GeneralException'
        invalidArgument = 'InvalidArgument'
        itemNotFound = 'ItemNotFound'
        notAllowed = 'NotAllowed'
        notImplemented = 'NotImplemented'
        searchDialogIsOpen = 'SearchDialogIsOpen'
        searchStringInvalidOrTooLong = 'SearchStringInvalidOrTooLong'
    
    class EditorCollection:
        pass
    
    class Editor:
        pass
    
    class ConflictCollection:
        pass
    
    class Conflict:
        pass
    
    class CritiquePopupOptions:
        pass
    
    class Critique:
        pass
    
    class CritiqueAnnotation:
        pass
    
    class AnnotationSet:
        pass
    
    class Annotation:
        pass
    
    class AnnotationInsertedEventArgs:
        pass
    
    class AnnotationClickedEventArgs:
        pass
    
    class AnnotationRemovedEventArgs:
        pass
    
    class AnnotationHoveredEventArgs:
        pass
    
    class AnnotationPopupActionEventArgs:
        pass
    
    class AnnotationCollection:
        pass
    
    class Application:
        pass
    
    class Body:
        pass
    
    class Border:
        pass
    
    class BorderUniversal:
        pass
    
    class BorderCollection:
        pass
    
    class BorderUniversalCollection:
        pass
    
    class Break:
        pass
    
    class BreakCollection:
        pass
    
    class BuildingBlock:
        pass
    
    class BuildingBlockCollection:
        pass
    
    class BuildingBlockEntryCollection:
        pass
    
    class BuildingBlockCategory:
        pass
    
    class BuildingBlockCategoryCollection:
        pass
    
    class BuildingBlockTypeItem:
        pass
    
    class BuildingBlockTypeItemCollection:
        pass
    
    class CheckboxContentControl:
        pass
    
    class CoauthoringLock:
        pass
    
    class CoauthoringLockCollection:
        pass
    
    class CoauthoringLockAddOptions:
        pass
    
    class Coauthor:
        pass
    
    class CoauthorCollection:
        pass
    
    class Coauthoring:
        pass
    
    class CoauthoringUpdate:
        pass
    
    class CoauthoringUpdateCollection:
        pass
    
    class Comment:
        pass
    
    class CommentCollection:
        pass
    
    class CommentContentRange:
        pass
    
    class CommentReply:
        pass
    
    class CommentReplyCollection:
        pass
    
    class ConditionalStyle:
        pass
    
    class XmlMapping:
        pass
    
    class XmlSetMappingOptions:
        pass
    
    class CustomXmlPrefixMappingCollection:
        pass
    
    class CustomXmlPrefixMapping:
        pass
    
    class CustomXmlSchema:
        pass
    
    class CustomXmlSchemaCollection:
        pass
    
    class CustomXmlAddSchemaOptions:
        pass
    
    class CustomXmlNodeCollection:
        pass
    
    class CustomXmlAppendChildNodeOptions:
        pass
    
    class CustomXmlInsertNodeBeforeOptions:
        pass
    
    class CustomXmlInsertSubtreeBeforeOptions:
        pass
    
    class CustomXmlReplaceChildNodeOptions:
        pass
    
    class CustomXmlNode:
        pass
    
    class ContentControl:
        pass
    
    class ContentControlCollection:
        pass
    
    class ContentControlListItem:
        pass
    
    class ContentControlListItemCollection:
        pass
    
    class ContentControlOptions:
        pass
    
    class CustomProperty:
        pass
    
    class CustomPropertyCollection:
        pass
    
    class CustomXmlAddNodeOptions:
        pass
    
    class CustomXmlPart:
        pass
    
    class CustomXmlPartCollection:
        pass
    
    class CustomXmlPartScopedCollection:
        pass
    
    class Document:
        pass
    
    class DocumentCreated:
        pass
    
    class DocumentProperties:
        pass
    
    class DropDownListContentControl:
        pass
    
    class ComboBoxContentControl:
        pass
    
    class Field:
        pass
    
    class FieldCollection:
        pass
    
    class Font:
        pass
    
    class HeadingStyle:
        pass
    
    class HeadingStyleCollection:
        pass
    
    class Hyperlink:
        pass
    
    class HyperlinkCollection:
        pass
    
    class HyperlinkAddOptions:
        pass
    
    class InlinePicture:
        pass
    
    class InlinePictureCollection:
        pass
    
    class LinkFormat:
        pass
    
    class List:
        pass
    
    class ListCollection:
        pass
    
    class ListItem:
        pass
    
    class ListLevel:
        pass
    
    class ListLevelCollection:
        pass
    
    class ListTemplate:
        pass
    
    class NoteItem:
        pass
    
    class NoteItemCollection:
        pass
    
    class OleFormat:
        pass
    
    class Page:
        pass
    
    class PageCollection:
        pass
    
    class Pane:
        pass
    
    class PaneCollection:
        pass
    
    class WindowCloseOptions:
        pass
    
    class WindowScrollOptions:
        pass
    
    class WindowPageScrollOptions:
        pass
    
    class Window:
        pass
    
    class WindowCollection:
        pass
    
    class Paragraph:
        pass
    
    class ParagraphCollection:
        pass
    
    class ParagraphFormat:
        pass
    
    class Range:
        pass
    
    class RangeCollection:
        pass
    
    class InsertShapeOptions:
        pass
    
    class InsertFileOptions:
        pass
    
    class SearchOptions:
        pass
    
    class GetTextOptions:
        pass
    
    class DocumentCompareOptions:
        pass
    
    class Section:
        pass
    
    class SectionCollection:
        pass
    
    class Setting:
        pass
    
    class SettingCollection:
        pass
    
    class StyleCollection:
        pass
    
    class Style:
        pass
    
    class Shading:
        pass
    
    class ShadingUniversal:
        pass
    
    class Table:
        pass
    
    class TableStyle:
        pass
    
    class TabStop:
        pass
    
    class TabStopCollection:
        pass
    
    class TabStopAddOptions:
        pass
    
    class TableCollection:
        pass
    
    class TableColumn:
        pass
    
    class TableColumnCollection:
        pass
    
    class TableOfAuthorities:
        pass
    
    class TableOfAuthoritiesCollection:
        pass
    
    class TableOfAuthoritiesAddOptions:
        pass
    
    class TableOfAuthoritiesMarkCitationOptions:
        pass
    
    class TableOfAuthoritiesCategory:
        pass
    
    class TableOfAuthoritiesCategoryCollection:
        pass
    
    class TableOfContents:
        pass
    
    class TableOfContentsCollection:
        pass
    
    class TableOfContentsAddOptions:
        pass
    
    class TableOfContentsMarkEntryOptions:
        pass
    
    class TableOfFigures:
        pass
    
    class TableOfFiguresCollection:
        pass
    
    class TableOfFiguresAddOptions:
        pass
    
    class TableRow:
        pass
    
    class TableRowCollection:
        pass
    
    class TableCell:
        pass
    
    class TableCellCollection:
        pass
    
    class TableBorder:
        pass
    
    class Template:
        pass
    
    class TemplateCollection:
        pass
    
    class TrackedChange:
        pass
    
    class TrackedChangeCollection:
        pass
    
    class View:
        pass
    
    class Shape:
        pass
    
    class ShapeGroup:
        pass
    
    class Canvas:
        pass
    
    class ShapeCollection:
        pass
    
    class ShapeFill:
        pass
    
    class TextFrame:
        pass
    
    class ShapeTextWrap:
        pass
    
    class Reviewer:
        pass
    
    class ReviewerCollection:
        pass
    
    class RevisionsFilter:
        pass
    
    class RepeatingSectionItem:
        pass
    
    class RepeatingSectionItemCollection:
        pass
    
    class Revision:
        pass
    
    class RevisionCollection:
        pass
    
    class DatePickerContentControl:
        pass
    
    class PictureContentControl:
        pass
    
    class GroupContentControl:
        pass
    
    class ContentControlPlaceholderOptions:
        pass
    
    class BuildingBlockGalleryContentControl:
        pass
    
    class RepeatingSectionContentControl:
        pass
    
    class ReadabilityStatistic:
        pass
    
    class ReadabilityStatisticCollection:
        pass
    
    class WebSettings:
        pass
    
    class XmlNodeCollection:
        pass
    
    class XmlNodeSetValidationErrorOptions:
        pass
    
    class XmlNode:
        pass
    
    class SelectNodesOptions:
        pass
    
    class SelectSingleNodeOptions:
        pass
    
    class HtmlDivision:
        pass
    
    class HtmlDivisionCollection:
        pass
    
    class Frame:
        pass
    
    class FrameCollection:
        pass
    
    class DocumentLibraryVersion:
        pass
    
    class DocumentLibraryVersionCollection:
        pass
    
    class ContentControlAddedEventArgs:
        pass
    
    class ContentControlDataChangedEventArgs:
        pass
    
    class ContentControlDeletedEventArgs:
        pass
    
    class ContentControlEnteredEventArgs:
        pass
    
    class ContentControlExitedEventArgs:
        pass
    
    class DropCap:
        pass
    
    class ContentControlSelectionChangedEventArgs:
        pass
    
    class ParagraphAddedEventArgs:
        pass
    
    class ParagraphChangedEventArgs:
        pass
    
    class ParagraphDeletedEventArgs:
        pass
    
    class ListFormat:
        pass
    
    class ListFormatCountNumberedItemsOptions:
        pass
    
    class ListTemplateApplyOptions:
        pass
    
    class FillFormat:
        pass
    
    class GlowFormat:
        pass
    
    class LineFormat:
        pass
    
    class ReflectionFormat:
        pass
    
    class ColorFormat:
        pass
    
    class ShadowFormat:
        pass
    
    class ThreeDimensionalFormat:
        pass
    
    class Bibliography:
        pass
    
    class SourceCollection:
        pass
    
    class Source:
        pass
    
    class PageSetup:
        pass
    
    class LineNumbering:
        pass
    
    class TextColumnCollection:
        pass
    
    class TextColumnAddOptions:
        pass
    
    class TextColumn:
        pass
    
    class SelectionDeleteOptions:
        pass
    
    class SelectionInsertDateTimeOptions:
        pass
    
    class SelectionInsertFormulaOptions:
        pass
    
    class SelectionInsertSymbolOptions:
        pass
    
    class SelectionMoveLeftRightOptions:
        pass
    
    class SelectionMoveOptions:
        pass
    
    class SelectionMoveStartEndOptions:
        pass
    
    class SelectionMoveUpDownOptions:
        pass
    
    class SelectionNextOptions:
        pass
    
    class SelectionPreviousOptions:
        pass
    
    class Selection:
        pass
    
    class RangeScopedCollection:
        pass
    
    class Bookmark:
        pass
    
    class BookmarkCollection:
        pass
    
    class Index:
        pass
    
    class IndexCollection:
        pass
    
    class IndexAddOptions:
        pass
    
    class IndexMarkAllEntriesOptions:
        pass
    
    class TableAutoFormatOptions:
        pass
    
    class TableCellCollectionSplitOptions:
        pass
    
    class TableCellFormulaOptions:
        pass
    
    class TableConvertToTextOptions:
        pass
    
    class TableSortOptions:
        pass
    
    class FontNameCollection:
        pass
    
    class ListTemplateCollection:
        pass
    
    class ListTemplateGallery:
        pass
    
    class ListTemplateGalleryCollection:
        pass
    
    class RequestContext:
        pass
    
    class Interfaces:
        
        class CollectionLoadOptions:
            pass
        
        class EditorUpdateData:
            pass
        
        class ConflictCollectionUpdateData:
            pass
        
        class ConflictUpdateData:
            pass
        
        class AnnotationCollectionUpdateData:
            pass
        
        class ApplicationUpdateData:
            pass
        
        class BodyUpdateData:
            pass
        
        class BorderUpdateData:
            pass
        
        class BorderUniversalUpdateData:
            pass
        
        class BorderCollectionUpdateData:
            pass
        
        class BorderUniversalCollectionUpdateData:
            pass
        
        class BreakUpdateData:
            pass
        
        class BreakCollectionUpdateData:
            pass
        
        class BuildingBlockUpdateData:
            pass
        
        class CheckboxContentControlUpdateData:
            pass
        
        class CoauthoringLockUpdateData:
            pass
        
        class CoauthoringLockCollectionUpdateData:
            pass
        
        class CoauthorCollectionUpdateData:
            pass
        
        class CoauthoringUpdateUpdateData:
            pass
        
        class CoauthoringUpdateCollectionUpdateData:
            pass
        
        class CommentUpdateData:
            pass
        
        class CommentCollectionUpdateData:
            pass
        
        class CommentContentRangeUpdateData:
            pass
        
        class CommentReplyUpdateData:
            pass
        
        class CommentReplyCollectionUpdateData:
            pass
        
        class ConditionalStyleUpdateData:
            pass
        
        class XmlMappingUpdateData:
            pass
        
        class CustomXmlPrefixMappingCollectionUpdateData:
            pass
        
        class CustomXmlSchemaCollectionUpdateData:
            pass
        
        class CustomXmlNodeCollectionUpdateData:
            pass
        
        class CustomXmlNodeUpdateData:
            pass
        
        class ContentControlUpdateData:
            pass
        
        class ContentControlCollectionUpdateData:
            pass
        
        class ContentControlListItemUpdateData:
            pass
        
        class ContentControlListItemCollectionUpdateData:
            pass
        
        class CustomPropertyUpdateData:
            pass
        
        class CustomPropertyCollectionUpdateData:
            pass
        
        class CustomXmlPartUpdateData:
            pass
        
        class CustomXmlPartCollectionUpdateData:
            pass
        
        class CustomXmlPartScopedCollectionUpdateData:
            pass
        
        class DocumentUpdateData:
            pass
        
        class DocumentCreatedUpdateData:
            pass
        
        class DocumentPropertiesUpdateData:
            pass
        
        class FieldUpdateData:
            pass
        
        class FieldCollectionUpdateData:
            pass
        
        class FontUpdateData:
            pass
        
        class HeadingStyleUpdateData:
            pass
        
        class HeadingStyleCollectionUpdateData:
            pass
        
        class HyperlinkUpdateData:
            pass
        
        class HyperlinkCollectionUpdateData:
            pass
        
        class InlinePictureUpdateData:
            pass
        
        class InlinePictureCollectionUpdateData:
            pass
        
        class LinkFormatUpdateData:
            pass
        
        class ListCollectionUpdateData:
            pass
        
        class ListItemUpdateData:
            pass
        
        class ListLevelUpdateData:
            pass
        
        class ListLevelCollectionUpdateData:
            pass
        
        class ListTemplateUpdateData:
            pass
        
        class NoteItemUpdateData:
            pass
        
        class NoteItemCollectionUpdateData:
            pass
        
        class OleFormatUpdateData:
            pass
        
        class PageCollectionUpdateData:
            pass
        
        class PaneCollectionUpdateData:
            pass
        
        class WindowUpdateData:
            pass
        
        class WindowCollectionUpdateData:
            pass
        
        class ParagraphUpdateData:
            pass
        
        class ParagraphCollectionUpdateData:
            pass
        
        class ParagraphFormatUpdateData:
            pass
        
        class RangeUpdateData:
            pass
        
        class RangeCollectionUpdateData:
            pass
        
        class SearchOptionsUpdateData:
            pass
        
        class SectionUpdateData:
            pass
        
        class SectionCollectionUpdateData:
            pass
        
        class SettingUpdateData:
            pass
        
        class SettingCollectionUpdateData:
            pass
        
        class StyleCollectionUpdateData:
            pass
        
        class StyleUpdateData:
            pass
        
        class ShadingUpdateData:
            pass
        
        class ShadingUniversalUpdateData:
            pass
        
        class TableUpdateData:
            pass
        
        class TableStyleUpdateData:
            pass
        
        class TabStopCollectionUpdateData:
            pass
        
        class TableCollectionUpdateData:
            pass
        
        class TableColumnUpdateData:
            pass
        
        class TableColumnCollectionUpdateData:
            pass
        
        class TableOfAuthoritiesUpdateData:
            pass
        
        class TableOfAuthoritiesCollectionUpdateData:
            pass
        
        class TableOfAuthoritiesCategoryCollectionUpdateData:
            pass
        
        class TableOfContentsUpdateData:
            pass
        
        class TableOfContentsCollectionUpdateData:
            pass
        
        class TableOfFiguresUpdateData:
            pass
        
        class TableOfFiguresCollectionUpdateData:
            pass
        
        class TableRowUpdateData:
            pass
        
        class TableRowCollectionUpdateData:
            pass
        
        class TableCellUpdateData:
            pass
        
        class TableCellCollectionUpdateData:
            pass
        
        class TableBorderUpdateData:
            pass
        
        class TemplateUpdateData:
            pass
        
        class TemplateCollectionUpdateData:
            pass
        
        class TrackedChangeCollectionUpdateData:
            pass
        
        class ViewUpdateData:
            pass
        
        class ShapeUpdateData:
            pass
        
        class ShapeGroupUpdateData:
            pass
        
        class CanvasUpdateData:
            pass
        
        class ShapeCollectionUpdateData:
            pass
        
        class ShapeFillUpdateData:
            pass
        
        class TextFrameUpdateData:
            pass
        
        class ShapeTextWrapUpdateData:
            pass
        
        class ReviewerUpdateData:
            pass
        
        class ReviewerCollectionUpdateData:
            pass
        
        class RevisionsFilterUpdateData:
            pass
        
        class RepeatingSectionItemUpdateData:
            pass
        
        class RevisionUpdateData:
            pass
        
        class RevisionCollectionUpdateData:
            pass
        
        class DatePickerContentControlUpdateData:
            pass
        
        class PictureContentControlUpdateData:
            pass
        
        class GroupContentControlUpdateData:
            pass
        
        class BuildingBlockGalleryContentControlUpdateData:
            pass
        
        class RepeatingSectionContentControlUpdateData:
            pass
        
        class ReadabilityStatisticCollectionUpdateData:
            pass
        
        class WebSettingsUpdateData:
            pass
        
        class XmlNodeCollectionUpdateData:
            pass
        
        class XmlNodeUpdateData:
            pass
        
        class HtmlDivisionUpdateData:
            pass
        
        class HtmlDivisionCollectionUpdateData:
            pass
        
        class FrameUpdateData:
            pass
        
        class FrameCollectionUpdateData:
            pass
        
        class DocumentLibraryVersionCollectionUpdateData:
            pass
        
        class ListFormatUpdateData:
            pass
        
        class FillFormatUpdateData:
            pass
        
        class GlowFormatUpdateData:
            pass
        
        class LineFormatUpdateData:
            pass
        
        class ReflectionFormatUpdateData:
            pass
        
        class ColorFormatUpdateData:
            pass
        
        class ShadowFormatUpdateData:
            pass
        
        class ThreeDimensionalFormatUpdateData:
            pass
        
        class BibliographyUpdateData:
            pass
        
        class SourceCollectionUpdateData:
            pass
        
        class PageSetupUpdateData:
            pass
        
        class LineNumberingUpdateData:
            pass
        
        class TextColumnCollectionUpdateData:
            pass
        
        class TextColumnUpdateData:
            pass
        
        class SelectionUpdateData:
            pass
        
        class RangeScopedCollectionUpdateData:
            pass
        
        class BookmarkUpdateData:
            pass
        
        class BookmarkCollectionUpdateData:
            pass
        
        class IndexUpdateData:
            pass
        
        class IndexCollectionUpdateData:
            pass
        
        class ListTemplateCollectionUpdateData:
            pass
        
        class ListTemplateGalleryCollectionUpdateData:
            pass
        
        class EditorData:
            pass
        
        class ConflictCollectionData:
            pass
        
        class ConflictData:
            pass
        
        class CritiqueAnnotationData:
            pass
        
        class AnnotationData:
            pass
        
        class AnnotationCollectionData:
            pass
        
        class ApplicationData:
            pass
        
        class BodyData:
            pass
        
        class BorderData:
            pass
        
        class BorderUniversalData:
            pass
        
        class BorderCollectionData:
            pass
        
        class BorderUniversalCollectionData:
            pass
        
        class BreakData:
            pass
        
        class BreakCollectionData:
            pass
        
        class BuildingBlockData:
            pass
        
        class BuildingBlockCategoryData:
            pass
        
        class BuildingBlockTypeItemData:
            pass
        
        class CheckboxContentControlData:
            pass
        
        class CoauthoringLockData:
            pass
        
        class CoauthoringLockCollectionData:
            pass
        
        class CoauthorData:
            pass
        
        class CoauthorCollectionData:
            pass
        
        class CoauthoringData:
            pass
        
        class CoauthoringUpdateData:
            pass
        
        class CoauthoringUpdateCollectionData:
            pass
        
        class CommentData:
            pass
        
        class CommentCollectionData:
            pass
        
        class CommentContentRangeData:
            pass
        
        class CommentReplyData:
            pass
        
        class CommentReplyCollectionData:
            pass
        
        class ConditionalStyleData:
            pass
        
        class XmlMappingData:
            pass
        
        class CustomXmlPrefixMappingCollectionData:
            pass
        
        class CustomXmlPrefixMappingData:
            pass
        
        class CustomXmlSchemaData:
            pass
        
        class CustomXmlSchemaCollectionData:
            pass
        
        class CustomXmlNodeCollectionData:
            pass
        
        class CustomXmlNodeData:
            pass
        
        class ContentControlData:
            pass
        
        class ContentControlCollectionData:
            pass
        
        class ContentControlListItemData:
            pass
        
        class ContentControlListItemCollectionData:
            pass
        
        class CustomPropertyData:
            pass
        
        class CustomPropertyCollectionData:
            pass
        
        class CustomXmlPartData:
            pass
        
        class CustomXmlPartCollectionData:
            pass
        
        class CustomXmlPartScopedCollectionData:
            pass
        
        class DocumentData:
            pass
        
        class DocumentCreatedData:
            pass
        
        class DocumentPropertiesData:
            pass
        
        class DropDownListContentControlData:
            pass
        
        class ComboBoxContentControlData:
            pass
        
        class FieldData:
            pass
        
        class FieldCollectionData:
            pass
        
        class FontData:
            pass
        
        class HeadingStyleData:
            pass
        
        class HeadingStyleCollectionData:
            pass
        
        class HyperlinkData:
            pass
        
        class HyperlinkCollectionData:
            pass
        
        class InlinePictureData:
            pass
        
        class InlinePictureCollectionData:
            pass
        
        class LinkFormatData:
            pass
        
        class ListData:
            pass
        
        class ListCollectionData:
            pass
        
        class ListItemData:
            pass
        
        class ListLevelData:
            pass
        
        class ListLevelCollectionData:
            pass
        
        class ListTemplateData:
            pass
        
        class NoteItemData:
            pass
        
        class NoteItemCollectionData:
            pass
        
        class OleFormatData:
            pass
        
        class PageData:
            pass
        
        class PageCollectionData:
            pass
        
        class PaneData:
            pass
        
        class PaneCollectionData:
            pass
        
        class WindowData:
            pass
        
        class WindowCollectionData:
            pass
        
        class ParagraphData:
            pass
        
        class ParagraphCollectionData:
            pass
        
        class ParagraphFormatData:
            pass
        
        class RangeData:
            pass
        
        class RangeCollectionData:
            pass
        
        class SearchOptionsData:
            pass
        
        class SectionData:
            pass
        
        class SectionCollectionData:
            pass
        
        class SettingData:
            pass
        
        class SettingCollectionData:
            pass
        
        class StyleCollectionData:
            pass
        
        class StyleData:
            pass
        
        class ShadingData:
            pass
        
        class ShadingUniversalData:
            pass
        
        class TableData:
            pass
        
        class TableStyleData:
            pass
        
        class TabStopData:
            pass
        
        class TabStopCollectionData:
            pass
        
        class TableCollectionData:
            pass
        
        class TableColumnData:
            pass
        
        class TableColumnCollectionData:
            pass
        
        class TableOfAuthoritiesData:
            pass
        
        class TableOfAuthoritiesCollectionData:
            pass
        
        class TableOfAuthoritiesCategoryData:
            pass
        
        class TableOfAuthoritiesCategoryCollectionData:
            pass
        
        class TableOfContentsData:
            pass
        
        class TableOfContentsCollectionData:
            pass
        
        class TableOfFiguresData:
            pass
        
        class TableOfFiguresCollectionData:
            pass
        
        class TableRowData:
            pass
        
        class TableRowCollectionData:
            pass
        
        class TableCellData:
            pass
        
        class TableCellCollectionData:
            pass
        
        class TableBorderData:
            pass
        
        class TemplateData:
            pass
        
        class TemplateCollectionData:
            pass
        
        class TrackedChangeData:
            pass
        
        class TrackedChangeCollectionData:
            pass
        
        class ViewData:
            pass
        
        class ShapeData:
            pass
        
        class ShapeGroupData:
            pass
        
        class CanvasData:
            pass
        
        class ShapeCollectionData:
            pass
        
        class ShapeFillData:
            pass
        
        class TextFrameData:
            pass
        
        class ShapeTextWrapData:
            pass
        
        class ReviewerData:
            pass
        
        class ReviewerCollectionData:
            pass
        
        class RevisionsFilterData:
            pass
        
        class RepeatingSectionItemData:
            pass
        
        class RevisionData:
            pass
        
        class RevisionCollectionData:
            pass
        
        class DatePickerContentControlData:
            pass
        
        class PictureContentControlData:
            pass
        
        class GroupContentControlData:
            pass
        
        class BuildingBlockGalleryContentControlData:
            pass
        
        class RepeatingSectionContentControlData:
            pass
        
        class ReadabilityStatisticData:
            pass
        
        class ReadabilityStatisticCollectionData:
            pass
        
        class WebSettingsData:
            pass
        
        class XmlNodeCollectionData:
            pass
        
        class XmlNodeData:
            pass
        
        class HtmlDivisionData:
            pass
        
        class HtmlDivisionCollectionData:
            pass
        
        class FrameData:
            pass
        
        class FrameCollectionData:
            pass
        
        class DocumentLibraryVersionData:
            pass
        
        class DocumentLibraryVersionCollectionData:
            pass
        
        class DropCapData:
            pass
        
        class ListFormatData:
            pass
        
        class FillFormatData:
            pass
        
        class GlowFormatData:
            pass
        
        class LineFormatData:
            pass
        
        class ReflectionFormatData:
            pass
        
        class ColorFormatData:
            pass
        
        class ShadowFormatData:
            pass
        
        class ThreeDimensionalFormatData:
            pass
        
        class BibliographyData:
            pass
        
        class SourceCollectionData:
            pass
        
        class SourceData:
            pass
        
        class PageSetupData:
            pass
        
        class LineNumberingData:
            pass
        
        class TextColumnCollectionData:
            pass
        
        class TextColumnData:
            pass
        
        class SelectionData:
            pass
        
        class RangeScopedCollectionData:
            pass
        
        class BookmarkData:
            pass
        
        class BookmarkCollectionData:
            pass
        
        class IndexData:
            pass
        
        class IndexCollectionData:
            pass
        
        class ListTemplateCollectionData:
            pass
        
        class ListTemplateGalleryData:
            pass
        
        class ListTemplateGalleryCollectionData:
            pass
        
        class EditorLoadOptions:
            pass
        
        class ConflictCollectionLoadOptions:
            pass
        
        class ConflictLoadOptions:
            pass
        
        class CritiqueAnnotationLoadOptions:
            pass
        
        class AnnotationLoadOptions:
            pass
        
        class AnnotationCollectionLoadOptions:
            pass
        
        class ApplicationLoadOptions:
            pass
        
        class BodyLoadOptions:
            pass
        
        class BorderLoadOptions:
            pass
        
        class BorderUniversalLoadOptions:
            pass
        
        class BorderCollectionLoadOptions:
            pass
        
        class BorderUniversalCollectionLoadOptions:
            pass
        
        class BreakLoadOptions:
            pass
        
        class BreakCollectionLoadOptions:
            pass
        
        class BuildingBlockLoadOptions:
            pass
        
        class BuildingBlockCategoryLoadOptions:
            pass
        
        class BuildingBlockTypeItemLoadOptions:
            pass
        
        class CheckboxContentControlLoadOptions:
            pass
        
        class CoauthoringLockLoadOptions:
            pass
        
        class CoauthoringLockCollectionLoadOptions:
            pass
        
        class CoauthorLoadOptions:
            pass
        
        class CoauthorCollectionLoadOptions:
            pass
        
        class CoauthoringLoadOptions:
            pass
        
        class CoauthoringUpdateLoadOptions:
            pass
        
        class CoauthoringUpdateCollectionLoadOptions:
            pass
        
        class CommentLoadOptions:
            pass
        
        class CommentCollectionLoadOptions:
            pass
        
        class CommentContentRangeLoadOptions:
            pass
        
        class CommentReplyLoadOptions:
            pass
        
        class CommentReplyCollectionLoadOptions:
            pass
        
        class ConditionalStyleLoadOptions:
            pass
        
        class XmlMappingLoadOptions:
            pass
        
        class CustomXmlPrefixMappingCollectionLoadOptions:
            pass
        
        class CustomXmlPrefixMappingLoadOptions:
            pass
        
        class CustomXmlSchemaLoadOptions:
            pass
        
        class CustomXmlSchemaCollectionLoadOptions:
            pass
        
        class CustomXmlNodeCollectionLoadOptions:
            pass
        
        class CustomXmlNodeLoadOptions:
            pass
        
        class ContentControlLoadOptions:
            pass
        
        class ContentControlCollectionLoadOptions:
            pass
        
        class ContentControlListItemLoadOptions:
            pass
        
        class ContentControlListItemCollectionLoadOptions:
            pass
        
        class CustomPropertyLoadOptions:
            pass
        
        class CustomPropertyCollectionLoadOptions:
            pass
        
        class CustomXmlPartLoadOptions:
            pass
        
        class CustomXmlPartCollectionLoadOptions:
            pass
        
        class CustomXmlPartScopedCollectionLoadOptions:
            pass
        
        class DocumentLoadOptions:
            pass
        
        class DocumentCreatedLoadOptions:
            pass
        
        class DocumentPropertiesLoadOptions:
            pass
        
        class FieldLoadOptions:
            pass
        
        class FieldCollectionLoadOptions:
            pass
        
        class FontLoadOptions:
            pass
        
        class HeadingStyleLoadOptions:
            pass
        
        class HeadingStyleCollectionLoadOptions:
            pass
        
        class HyperlinkLoadOptions:
            pass
        
        class HyperlinkCollectionLoadOptions:
            pass
        
        class InlinePictureLoadOptions:
            pass
        
        class InlinePictureCollectionLoadOptions:
            pass
        
        class LinkFormatLoadOptions:
            pass
        
        class ListLoadOptions:
            pass
        
        class ListCollectionLoadOptions:
            pass
        
        class ListItemLoadOptions:
            pass
        
        class ListLevelLoadOptions:
            pass
        
        class ListLevelCollectionLoadOptions:
            pass
        
        class ListTemplateLoadOptions:
            pass
        
        class NoteItemLoadOptions:
            pass
        
        class NoteItemCollectionLoadOptions:
            pass
        
        class OleFormatLoadOptions:
            pass
        
        class PageLoadOptions:
            pass
        
        class PageCollectionLoadOptions:
            pass
        
        class PaneLoadOptions:
            pass
        
        class PaneCollectionLoadOptions:
            pass
        
        class WindowLoadOptions:
            pass
        
        class WindowCollectionLoadOptions:
            pass
        
        class ParagraphLoadOptions:
            pass
        
        class ParagraphCollectionLoadOptions:
            pass
        
        class ParagraphFormatLoadOptions:
            pass
        
        class RangeLoadOptions:
            pass
        
        class RangeCollectionLoadOptions:
            pass
        
        class SearchOptionsLoadOptions:
            pass
        
        class SectionLoadOptions:
            pass
        
        class SectionCollectionLoadOptions:
            pass
        
        class SettingLoadOptions:
            pass
        
        class SettingCollectionLoadOptions:
            pass
        
        class StyleCollectionLoadOptions:
            pass
        
        class StyleLoadOptions:
            pass
        
        class ShadingLoadOptions:
            pass
        
        class ShadingUniversalLoadOptions:
            pass
        
        class TableLoadOptions:
            pass
        
        class TableStyleLoadOptions:
            pass
        
        class TabStopLoadOptions:
            pass
        
        class TabStopCollectionLoadOptions:
            pass
        
        class TableCollectionLoadOptions:
            pass
        
        class TableColumnLoadOptions:
            pass
        
        class TableColumnCollectionLoadOptions:
            pass
        
        class TableOfAuthoritiesLoadOptions:
            pass
        
        class TableOfAuthoritiesCollectionLoadOptions:
            pass
        
        class TableOfAuthoritiesCategoryLoadOptions:
            pass
        
        class TableOfAuthoritiesCategoryCollectionLoadOptions:
            pass
        
        class TableOfContentsLoadOptions:
            pass
        
        class TableOfContentsCollectionLoadOptions:
            pass
        
        class TableOfFiguresLoadOptions:
            pass
        
        class TableOfFiguresCollectionLoadOptions:
            pass
        
        class TableRowLoadOptions:
            pass
        
        class TableRowCollectionLoadOptions:
            pass
        
        class TableCellLoadOptions:
            pass
        
        class TableCellCollectionLoadOptions:
            pass
        
        class TableBorderLoadOptions:
            pass
        
        class TemplateLoadOptions:
            pass
        
        class TemplateCollectionLoadOptions:
            pass
        
        class TrackedChangeLoadOptions:
            pass
        
        class TrackedChangeCollectionLoadOptions:
            pass
        
        class ViewLoadOptions:
            pass
        
        class ShapeLoadOptions:
            pass
        
        class ShapeGroupLoadOptions:
            pass
        
        class CanvasLoadOptions:
            pass
        
        class ShapeCollectionLoadOptions:
            pass
        
        class ShapeFillLoadOptions:
            pass
        
        class TextFrameLoadOptions:
            pass
        
        class ShapeTextWrapLoadOptions:
            pass
        
        class ReviewerLoadOptions:
            pass
        
        class ReviewerCollectionLoadOptions:
            pass
        
        class RevisionsFilterLoadOptions:
            pass
        
        class RepeatingSectionItemLoadOptions:
            pass
        
        class RevisionLoadOptions:
            pass
        
        class RevisionCollectionLoadOptions:
            pass
        
        class DatePickerContentControlLoadOptions:
            pass
        
        class PictureContentControlLoadOptions:
            pass
        
        class GroupContentControlLoadOptions:
            pass
        
        class BuildingBlockGalleryContentControlLoadOptions:
            pass
        
        class RepeatingSectionContentControlLoadOptions:
            pass
        
        class ReadabilityStatisticLoadOptions:
            pass
        
        class ReadabilityStatisticCollectionLoadOptions:
            pass
        
        class WebSettingsLoadOptions:
            pass
        
        class XmlNodeCollectionLoadOptions:
            pass
        
        class XmlNodeLoadOptions:
            pass
        
        class HtmlDivisionLoadOptions:
            pass
        
        class HtmlDivisionCollectionLoadOptions:
            pass
        
        class FrameLoadOptions:
            pass
        
        class FrameCollectionLoadOptions:
            pass
        
        class DocumentLibraryVersionLoadOptions:
            pass
        
        class DocumentLibraryVersionCollectionLoadOptions:
            pass
        
        class DropCapLoadOptions:
            pass
        
        class ListFormatLoadOptions:
            pass
        
        class FillFormatLoadOptions:
            pass
        
        class GlowFormatLoadOptions:
            pass
        
        class LineFormatLoadOptions:
            pass
        
        class ReflectionFormatLoadOptions:
            pass
        
        class ColorFormatLoadOptions:
            pass
        
        class ShadowFormatLoadOptions:
            pass
        
        class ThreeDimensionalFormatLoadOptions:
            pass
        
        class BibliographyLoadOptions:
            pass
        
        class SourceCollectionLoadOptions:
            pass
        
        class SourceLoadOptions:
            pass
        
        class PageSetupLoadOptions:
            pass
        
        class LineNumberingLoadOptions:
            pass
        
        class TextColumnCollectionLoadOptions:
            pass
        
        class TextColumnLoadOptions:
            pass
        
        class SelectionLoadOptions:
            pass
        
        class RangeScopedCollectionLoadOptions:
            pass
        
        class BookmarkLoadOptions:
            pass
        
        class BookmarkCollectionLoadOptions:
            pass
        
        class IndexLoadOptions:
            pass
        
        class IndexCollectionLoadOptions:
            pass
        
        class ListTemplateCollectionLoadOptions:
            pass

class OneNote:
    
    class InsertLocation:
        before = 'Before'
        after = 'After'
    
    class PageContentType:
        outline = 'Outline'
        image = 'Image'
        ink = 'Ink'
        other = 'Other'
    
    class ParagraphType:
        richText = 'RichText'
        image = 'Image'
        table = 'Table'
        ink = 'Ink'
        other = 'Other'
    
    class NoteTagType:
        unknown = 'Unknown'
        toDo = 'ToDo'
        important = 'Important'
        question = 'Question'
        contact = 'Contact'
        address = 'Address'
        phoneNumber = 'PhoneNumber'
        website = 'Website'
        idea = 'Idea'
        critical = 'Critical'
        toDoPriority1 = 'ToDoPriority1'
        toDoPriority2 = 'ToDoPriority2'
    
    class NoteTagStatus:
        unknown = 'Unknown'
        normal = 'Normal'
        completed = 'Completed'
        disabled = 'Disabled'
        outlookTask = 'OutlookTask'
        taskNotSyncedYet = 'TaskNotSyncedYet'
        taskRemoved = 'TaskRemoved'
    
    class ListType:
        none = 'None'
        number = 'Number'
        bullet = 'Bullet'
    
    class NumberType:
        none = 'None'
        arabic = 'Arabic'
        ucroman = 'UCRoman'
        lcroman = 'LCRoman'
        ucletter = 'UCLetter'
        lcletter = 'LCLetter'
        ordinal = 'Ordinal'
        cardtext = 'Cardtext'
        ordtext = 'Ordtext'
        hex = 'Hex'
        chiManSty = 'ChiManSty'
        dbNum1 = 'DbNum1'
        dbNum2 = 'DbNum2'
        aiueo = 'Aiueo'
        iroha = 'Iroha'
        dbChar = 'DbChar'
        sbChar = 'SbChar'
        dbNum3 = 'DbNum3'
        dbNum4 = 'DbNum4'
        circlenum = 'Circlenum'
        darabic = 'DArabic'
        daiueo = 'DAiueo'
        diroha = 'DIroha'
        arabicLZ = 'ArabicLZ'
        bullet = 'Bullet'
        ganada = 'Ganada'
        chosung = 'Chosung'
        gb1 = 'GB1'
        gb2 = 'GB2'
        gb3 = 'GB3'
        gb4 = 'GB4'
        zodiac1 = 'Zodiac1'
        zodiac2 = 'Zodiac2'
        zodiac3 = 'Zodiac3'
        tpeDbNum1 = 'TpeDbNum1'
        tpeDbNum2 = 'TpeDbNum2'
        tpeDbNum3 = 'TpeDbNum3'
        tpeDbNum4 = 'TpeDbNum4'
        chnDbNum1 = 'ChnDbNum1'
        chnDbNum2 = 'ChnDbNum2'
        chnDbNum3 = 'ChnDbNum3'
        chnDbNum4 = 'ChnDbNum4'
        korDbNum1 = 'KorDbNum1'
        korDbNum2 = 'KorDbNum2'
        korDbNum3 = 'KorDbNum3'
        korDbNum4 = 'KorDbNum4'
        hebrew1 = 'Hebrew1'
        arabic1 = 'Arabic1'
        hebrew2 = 'Hebrew2'
        arabic2 = 'Arabic2'
        hindi1 = 'Hindi1'
        hindi2 = 'Hindi2'
        hindi3 = 'Hindi3'
        thai1 = 'Thai1'
        thai2 = 'Thai2'
        numInDash = 'NumInDash'
        lcrus = 'LCRus'
        ucrus = 'UCRus'
        lcgreek = 'LCGreek'
        ucgreek = 'UCGreek'
        lim = 'Lim'
        custom = 'Custom'
    
    class EventType:
        alterationSelected = 'AlterationSelected'
        inkSelectedForCorrection = 'InkSelectedForCorrection'
        restrictionsCalculated = 'RestrictionsCalculated'
        reset = 'Reset'
    
    class ParagraphStyle:
        noStyle = 0
        normal = 1
        title = 2
        dateTime = 3
        heading1 = 4
        heading2 = 5
        heading3 = 6
        heading4 = 7
        heading5 = 8
        heading6 = 9
        quote = 10
        citation = 11
        code = 12
    
    class ErrorCodes:
        accessDenied = 'AccessDenied'
        generalException = 'GeneralException'
        invalidArgument = 'InvalidArgument'
        invalidOperation = 'InvalidOperation'
        invalidState = 'InvalidState'
        itemNotFound = 'ItemNotFound'
        notImplemented = 'NotImplemented'
        notSupported = 'NotSupported'
        operationAborted = 'OperationAborted'
    
    class Application:
        pass
    
    class InkAnalysis:
        pass
    
    class InkAnalysisParagraph:
        pass
    
    class InkAnalysisParagraphCollection:
        pass
    
    class InkAnalysisLine:
        pass
    
    class InkAnalysisLineCollection:
        pass
    
    class InkAnalysisWord:
        pass
    
    class InkAnalysisWordCollection:
        pass
    
    class FloatingInk:
        pass
    
    class InkStroke:
        pass
    
    class InkStrokeCollection:
        pass
    
    class Point:
        pass
    
    class PointCollection:
        pass
    
    class InkWord:
        pass
    
    class InkWordCollection:
        pass
    
    class Notebook:
        pass
    
    class NotebookCollection:
        pass
    
    class SectionGroup:
        pass
    
    class SectionGroupCollection:
        pass
    
    class Section:
        pass
    
    class SectionCollection:
        pass
    
    class Page:
        pass
    
    class PageCollection:
        pass
    
    class PageContent:
        pass
    
    class PageContentCollection:
        pass
    
    class Outline:
        pass
    
    class Paragraph:
        pass
    
    class ParagraphCollection:
        pass
    
    class NoteTag:
        pass
    
    class RichText:
        pass
    
    class Image:
        pass
    
    class Table:
        pass
    
    class TableRow:
        pass
    
    class TableRowCollection:
        pass
    
    class TableCell:
        pass
    
    class TableCellCollection:
        pass
    
    class ImageOcrData:
        pass
    
    class InkStrokePointer:
        pass
    
    class ParagraphInfo:
        pass
    
    class RequestContext:
        pass
    
    class Interfaces:
        
        class CollectionLoadOptions:
            pass
        
        class ApplicationUpdateData:
            pass
        
        class InkAnalysisUpdateData:
            pass
        
        class InkAnalysisParagraphUpdateData:
            pass
        
        class InkAnalysisParagraphCollectionUpdateData:
            pass
        
        class InkAnalysisLineUpdateData:
            pass
        
        class InkAnalysisLineCollectionUpdateData:
            pass
        
        class InkAnalysisWordUpdateData:
            pass
        
        class InkAnalysisWordCollectionUpdateData:
            pass
        
        class InkStrokeCollectionUpdateData:
            pass
        
        class PointCollectionUpdateData:
            pass
        
        class InkWordCollectionUpdateData:
            pass
        
        class NotebookCollectionUpdateData:
            pass
        
        class SectionGroupCollectionUpdateData:
            pass
        
        class SectionCollectionUpdateData:
            pass
        
        class PageUpdateData:
            pass
        
        class PageCollectionUpdateData:
            pass
        
        class PageContentUpdateData:
            pass
        
        class PageContentCollectionUpdateData:
            pass
        
        class ParagraphUpdateData:
            pass
        
        class ParagraphCollectionUpdateData:
            pass
        
        class ImageUpdateData:
            pass
        
        class TableUpdateData:
            pass
        
        class TableRowCollectionUpdateData:
            pass
        
        class TableCellUpdateData:
            pass
        
        class TableCellCollectionUpdateData:
            pass
        
        class ApplicationData:
            pass
        
        class InkAnalysisData:
            pass
        
        class InkAnalysisParagraphData:
            pass
        
        class InkAnalysisParagraphCollectionData:
            pass
        
        class InkAnalysisLineData:
            pass
        
        class InkAnalysisLineCollectionData:
            pass
        
        class InkAnalysisWordData:
            pass
        
        class InkAnalysisWordCollectionData:
            pass
        
        class FloatingInkData:
            pass
        
        class InkStrokeData:
            pass
        
        class InkStrokeCollectionData:
            pass
        
        class PointData:
            pass
        
        class PointCollectionData:
            pass
        
        class InkWordData:
            pass
        
        class InkWordCollectionData:
            pass
        
        class NotebookData:
            pass
        
        class NotebookCollectionData:
            pass
        
        class SectionGroupData:
            pass
        
        class SectionGroupCollectionData:
            pass
        
        class SectionData:
            pass
        
        class SectionCollectionData:
            pass
        
        class PageData:
            pass
        
        class PageCollectionData:
            pass
        
        class PageContentData:
            pass
        
        class PageContentCollectionData:
            pass
        
        class OutlineData:
            pass
        
        class ParagraphData:
            pass
        
        class ParagraphCollectionData:
            pass
        
        class NoteTagData:
            pass
        
        class RichTextData:
            pass
        
        class ImageData:
            pass
        
        class TableData:
            pass
        
        class TableRowData:
            pass
        
        class TableRowCollectionData:
            pass
        
        class TableCellData:
            pass
        
        class TableCellCollectionData:
            pass
        
        class ApplicationLoadOptions:
            pass
        
        class InkAnalysisLoadOptions:
            pass
        
        class InkAnalysisParagraphLoadOptions:
            pass
        
        class InkAnalysisParagraphCollectionLoadOptions:
            pass
        
        class InkAnalysisLineLoadOptions:
            pass
        
        class InkAnalysisLineCollectionLoadOptions:
            pass
        
        class InkAnalysisWordLoadOptions:
            pass
        
        class InkAnalysisWordCollectionLoadOptions:
            pass
        
        class FloatingInkLoadOptions:
            pass
        
        class InkStrokeLoadOptions:
            pass
        
        class InkStrokeCollectionLoadOptions:
            pass
        
        class PointLoadOptions:
            pass
        
        class PointCollectionLoadOptions:
            pass
        
        class InkWordLoadOptions:
            pass
        
        class InkWordCollectionLoadOptions:
            pass
        
        class NotebookLoadOptions:
            pass
        
        class NotebookCollectionLoadOptions:
            pass
        
        class SectionGroupLoadOptions:
            pass
        
        class SectionGroupCollectionLoadOptions:
            pass
        
        class SectionLoadOptions:
            pass
        
        class SectionCollectionLoadOptions:
            pass
        
        class PageLoadOptions:
            pass
        
        class PageCollectionLoadOptions:
            pass
        
        class PageContentLoadOptions:
            pass
        
        class PageContentCollectionLoadOptions:
            pass
        
        class OutlineLoadOptions:
            pass
        
        class ParagraphLoadOptions:
            pass
        
        class ParagraphCollectionLoadOptions:
            pass
        
        class NoteTagLoadOptions:
            pass
        
        class RichTextLoadOptions:
            pass
        
        class ImageLoadOptions:
            pass
        
        class TableLoadOptions:
            pass
        
        class TableRowLoadOptions:
            pass
        
        class TableRowCollectionLoadOptions:
            pass
        
        class TableCellLoadOptions:
            pass
        
        class TableCellCollectionLoadOptions:
            pass

class Visio:
    
    class OverlayHorizontalAlignment:
        left = 'Left'
        center = 'Center'
        right = 'Right'
    
    class OverlayVerticalAlignment:
        top = 'Top'
        middle = 'Middle'
        bottom = 'Bottom'
    
    class OverlayType:
        text = 'Text'
        image = 'Image'
        html = 'Html'
    
    class ToolBarType:
        commandBar = 'CommandBar'
        pageNavigationBar = 'PageNavigationBar'
        statusBar = 'StatusBar'
    
    class DataVisualizerDiagramResultType:
        success = 'Success'
        unexpected = 'Unexpected'
        validationError = 'ValidationError'
        conflictError = 'ConflictError'
    
    class DataVisualizerDiagramOperationType:
        unknown = 'Unknown'
        create = 'Create'
        updateMappings = 'UpdateMappings'
        updateData = 'UpdateData'
        update = 'Update'
        delete = 'Delete'
    
    class DataVisualizerDiagramType:
        unknown = 'Unknown'
        basicFlowchart = 'BasicFlowchart'
        crossFunctionalFlowchart_Horizontal = 'CrossFunctionalFlowchart_Horizontal'
        crossFunctionalFlowchart_Vertical = 'CrossFunctionalFlowchart_Vertical'
        audit = 'Audit'
        orgChart = 'OrgChart'
        network = 'Network'
    
    class ColumnType:
        unknown = 'Unknown'
        string = 'String'
        number = 'Number'
        date = 'Date'
        currency = 'Currency'
    
    class DataSourceType:
        unknown = 'Unknown'
        excel = 'Excel'
    
    class CrossFunctionalFlowchartOrientation:
        horizontal = 'Horizontal'
        vertical = 'Vertical'
    
    class LayoutVariant:
        unknown = 'Unknown'
        pageDefault = 'PageDefault'
        flowchart_TopToBottom = 'Flowchart_TopToBottom'
        flowchart_BottomToTop = 'Flowchart_BottomToTop'
        flowchart_LeftToRight = 'Flowchart_LeftToRight'
        flowchart_RightToLeft = 'Flowchart_RightToLeft'
        wideTree_DownThenRight = 'WideTree_DownThenRight'
        wideTree_DownThenLeft = 'WideTree_DownThenLeft'
        wideTree_RightThenDown = 'WideTree_RightThenDown'
        wideTree_LeftThenDown = 'WideTree_LeftThenDown'
    
    class DataValidationErrorType:
        none = 'None'
        columnNotMapped = 'ColumnNotMapped'
        uniqueIdColumnError = 'UniqueIdColumnError'
        swimlaneColumnError = 'SwimlaneColumnError'
        delimiterError = 'DelimiterError'
        connectorColumnError = 'ConnectorColumnError'
        connectorColumnMappedElsewhere = 'ConnectorColumnMappedElsewhere'
        connectorLabelColumnMappedElsewhere = 'ConnectorLabelColumnMappedElsewhere'
        connectorColumnAndConnectorLabelMappedElsewhere = 'ConnectorColumnAndConnectorLabelMappedElsewhere'
    
    class ConnectorDirection:
        fromTarget = 'FromTarget'
        toTarget = 'ToTarget'
    
    class TaskPaneType:
        none = 'None'
        dataVisualizerProcessMappings = 'DataVisualizerProcessMappings'
        dataVisualizerOrgChartMappings = 'DataVisualizerOrgChartMappings'
    
    class MessageType:
        none = 0
        dataVisualizerDiagramOperationCompletedEvent = 1
    
    class EventType:
        dataVisualizerDiagramOperationCompleted = 'DataVisualizerDiagramOperationCompleted'
    
    class ErrorCodes:
        accessDenied = 'AccessDenied'
        generalException = 'GeneralException'
        invalidArgument = 'InvalidArgument'
        itemNotFound = 'ItemNotFound'
        notImplemented = 'NotImplemented'
        unsupportedOperation = 'UnsupportedOperation'
    
    class ShapeMouseEnterEventArgs:
        pass
    
    class ShapeMouseLeaveEventArgs:
        pass
    
    class PageLoadCompleteEventArgs:
        pass
    
    class DataRefreshCompleteEventArgs:
        pass
    
    class SelectionChangedEventArgs:
        pass
    
    class DocumentLoadCompleteEventArgs:
        pass
    
    class PageRenderCompleteEventArgs:
        pass
    
    class DocumentErrorEventArgs:
        pass
    
    class TaskPaneStateChangedEventArgs:
        pass
    
    class Application:
        pass
    
    class Document:
        pass
    
    class DocumentView:
        pass
    
    class Page:
        pass
    
    class PageView:
        pass
    
    class PageCollection:
        pass
    
    class ShapeCollection:
        pass
    
    class Shape:
        pass
    
    class ShapeView:
        pass
    
    class Position:
        pass
    
    class BoundingBox:
        pass
    
    class Highlight:
        pass
    
    class ShapeDataItemCollection:
        pass
    
    class ShapeDataItem:
        pass
    
    class HyperlinkCollection:
        pass
    
    class Hyperlink:
        pass
    
    class CommentCollection:
        pass
    
    class Comment:
        pass
    
    class Selection:
        pass
    
    class RequestContext:
        pass
    
    class Interfaces:
        
        class CollectionLoadOptions:
            pass
        
        class ApplicationUpdateData:
            pass
        
        class DocumentUpdateData:
            pass
        
        class DocumentViewUpdateData:
            pass
        
        class PageUpdateData:
            pass
        
        class PageViewUpdateData:
            pass
        
        class PageCollectionUpdateData:
            pass
        
        class ShapeCollectionUpdateData:
            pass
        
        class ShapeUpdateData:
            pass
        
        class ShapeViewUpdateData:
            pass
        
        class ShapeDataItemCollectionUpdateData:
            pass
        
        class HyperlinkCollectionUpdateData:
            pass
        
        class CommentCollectionUpdateData:
            pass
        
        class CommentUpdateData:
            pass
        
        class ApplicationData:
            pass
        
        class DocumentData:
            pass
        
        class DocumentViewData:
            pass
        
        class PageData:
            pass
        
        class PageViewData:
            pass
        
        class PageCollectionData:
            pass
        
        class ShapeCollectionData:
            pass
        
        class ShapeData:
            pass
        
        class ShapeViewData:
            pass
        
        class ShapeDataItemCollectionData:
            pass
        
        class ShapeDataItemData:
            pass
        
        class HyperlinkCollectionData:
            pass
        
        class HyperlinkData:
            pass
        
        class CommentCollectionData:
            pass
        
        class CommentData:
            pass
        
        class SelectionData:
            pass
        
        class ApplicationLoadOptions:
            pass
        
        class DocumentLoadOptions:
            pass
        
        class DocumentViewLoadOptions:
            pass
        
        class PageLoadOptions:
            pass
        
        class PageViewLoadOptions:
            pass
        
        class PageCollectionLoadOptions:
            pass
        
        class ShapeCollectionLoadOptions:
            pass
        
        class ShapeLoadOptions:
            pass
        
        class ShapeViewLoadOptions:
            pass
        
        class ShapeDataItemCollectionLoadOptions:
            pass
        
        class ShapeDataItemLoadOptions:
            pass
        
        class HyperlinkCollectionLoadOptions:
            pass
        
        class HyperlinkLoadOptions:
            pass
        
        class CommentCollectionLoadOptions:
            pass
        
        class CommentLoadOptions:
            pass

class PowerPoint:
    
    class BindingType:
        shape = 'Shape'
    
    class ParagraphHorizontalAlignment:
        left = 'Left'
        center = 'Center'
        right = 'Right'
        justify = 'Justify'
        justifyLow = 'JustifyLow'
        distributed = 'Distributed'
        thaiDistributed = 'ThaiDistributed'
    
    class ShapeFontUnderlineStyle:
        none = 'None'
        single = 'Single'
        double = 'Double'
        heavy = 'Heavy'
        dotted = 'Dotted'
        dottedHeavy = 'DottedHeavy'
        dash = 'Dash'
        dashHeavy = 'DashHeavy'
        dashLong = 'DashLong'
        dashLongHeavy = 'DashLongHeavy'
        dotDash = 'DotDash'
        dotDashHeavy = 'DotDashHeavy'
        dotDotDash = 'DotDotDash'
        dotDotDashHeavy = 'DotDotDashHeavy'
        wavy = 'Wavy'
        wavyHeavy = 'WavyHeavy'
        wavyDouble = 'WavyDouble'
    
    class ShapeAutoSize:
        autoSizeNone = 'AutoSizeNone'
        autoSizeTextToFitShape = 'AutoSizeTextToFitShape'
        autoSizeShapeToFitText = 'AutoSizeShapeToFitText'
        autoSizeMixed = 'AutoSizeMixed'
    
    class TextVerticalAlignment:
        top = 'Top'
        middle = 'Middle'
        bottom = 'Bottom'
        topCentered = 'TopCentered'
        middleCentered = 'MiddleCentered'
        bottomCentered = 'BottomCentered'
    
    class PlaceholderType:
        unsupported = 'Unsupported'
        date = 'Date'
        slideNumber = 'SlideNumber'
        footer = 'Footer'
        header = 'Header'
        title = 'Title'
        body = 'Body'
        centerTitle = 'CenterTitle'
        subtitle = 'Subtitle'
        verticalTitle = 'VerticalTitle'
        verticalBody = 'VerticalBody'
        content = 'Content'
        chart = 'Chart'
        table = 'Table'
        onlinePicture = 'OnlinePicture'
        smartArt = 'SmartArt'
        media = 'Media'
        verticalContent = 'VerticalContent'
        picture = 'Picture'
        cameo = 'Cameo'
    
    class ShapeType:
        unsupported = 'Unsupported'
        image = 'Image'
        geometricShape = 'GeometricShape'
        group = 'Group'
        line = 'Line'
        table = 'Table'
        callout = 'Callout'
        chart = 'Chart'
        contentApp = 'ContentApp'
        diagram = 'Diagram'
        freeform = 'Freeform'
        graphic = 'Graphic'
        ink = 'Ink'
        media = 'Media'
        model3D = 'Model3D'
        ole = 'Ole'
        placeholder = 'Placeholder'
        smartArt = 'SmartArt'
        textBox = 'TextBox'
    
    class ConnectorType:
        straight = 'Straight'
        elbow = 'Elbow'
        curve = 'Curve'
    
    class GeometricShapeType:
        lineInverse = 'LineInverse'
        triangle = 'Triangle'
        rightTriangle = 'RightTriangle'
        rectangle = 'Rectangle'
        diamond = 'Diamond'
        parallelogram = 'Parallelogram'
        trapezoid = 'Trapezoid'
        nonIsoscelesTrapezoid = 'NonIsoscelesTrapezoid'
        pentagon = 'Pentagon'
        hexagon = 'Hexagon'
        heptagon = 'Heptagon'
        octagon = 'Octagon'
        decagon = 'Decagon'
        dodecagon = 'Dodecagon'
        star4 = 'Star4'
        star5 = 'Star5'
        star6 = 'Star6'
        star7 = 'Star7'
        star8 = 'Star8'
        star10 = 'Star10'
        star12 = 'Star12'
        star16 = 'Star16'
        star24 = 'Star24'
        star32 = 'Star32'
        roundRectangle = 'RoundRectangle'
        round1Rectangle = 'Round1Rectangle'
        round2SameRectangle = 'Round2SameRectangle'
        round2DiagonalRectangle = 'Round2DiagonalRectangle'
        snipRoundRectangle = 'SnipRoundRectangle'
        snip1Rectangle = 'Snip1Rectangle'
        snip2SameRectangle = 'Snip2SameRectangle'
        snip2DiagonalRectangle = 'Snip2DiagonalRectangle'
        plaque = 'Plaque'
        ellipse = 'Ellipse'
        teardrop = 'Teardrop'
        homePlate = 'HomePlate'
        chevron = 'Chevron'
        pieWedge = 'PieWedge'
        pie = 'Pie'
        blockArc = 'BlockArc'
        donut = 'Donut'
        noSmoking = 'NoSmoking'
        rightArrow = 'RightArrow'
        leftArrow = 'LeftArrow'
        upArrow = 'UpArrow'
        downArrow = 'DownArrow'
        stripedRightArrow = 'StripedRightArrow'
        notchedRightArrow = 'NotchedRightArrow'
        bentUpArrow = 'BentUpArrow'
        leftRightArrow = 'LeftRightArrow'
        upDownArrow = 'UpDownArrow'
        leftUpArrow = 'LeftUpArrow'
        leftRightUpArrow = 'LeftRightUpArrow'
        quadArrow = 'QuadArrow'
        leftArrowCallout = 'LeftArrowCallout'
        rightArrowCallout = 'RightArrowCallout'
        upArrowCallout = 'UpArrowCallout'
        downArrowCallout = 'DownArrowCallout'
        leftRightArrowCallout = 'LeftRightArrowCallout'
        upDownArrowCallout = 'UpDownArrowCallout'
        quadArrowCallout = 'QuadArrowCallout'
        bentArrow = 'BentArrow'
        uturnArrow = 'UturnArrow'
        circularArrow = 'CircularArrow'
        leftCircularArrow = 'LeftCircularArrow'
        leftRightCircularArrow = 'LeftRightCircularArrow'
        curvedRightArrow = 'CurvedRightArrow'
        curvedLeftArrow = 'CurvedLeftArrow'
        curvedUpArrow = 'CurvedUpArrow'
        curvedDownArrow = 'CurvedDownArrow'
        swooshArrow = 'SwooshArrow'
        cube = 'Cube'
        can = 'Can'
        lightningBolt = 'LightningBolt'
        heart = 'Heart'
        sun = 'Sun'
        moon = 'Moon'
        smileyFace = 'SmileyFace'
        irregularSeal1 = 'IrregularSeal1'
        irregularSeal2 = 'IrregularSeal2'
        foldedCorner = 'FoldedCorner'
        bevel = 'Bevel'
        frame = 'Frame'
        halfFrame = 'HalfFrame'
        corner = 'Corner'
        diagonalStripe = 'DiagonalStripe'
        chord = 'Chord'
        arc = 'Arc'
        leftBracket = 'LeftBracket'
        rightBracket = 'RightBracket'
        leftBrace = 'LeftBrace'
        rightBrace = 'RightBrace'
        bracketPair = 'BracketPair'
        bracePair = 'BracePair'
        callout1 = 'Callout1'
        callout2 = 'Callout2'
        callout3 = 'Callout3'
        accentCallout1 = 'AccentCallout1'
        accentCallout2 = 'AccentCallout2'
        accentCallout3 = 'AccentCallout3'
        borderCallout1 = 'BorderCallout1'
        borderCallout2 = 'BorderCallout2'
        borderCallout3 = 'BorderCallout3'
        accentBorderCallout1 = 'AccentBorderCallout1'
        accentBorderCallout2 = 'AccentBorderCallout2'
        accentBorderCallout3 = 'AccentBorderCallout3'
        wedgeRectCallout = 'WedgeRectCallout'
        wedgeRRectCallout = 'WedgeRRectCallout'
        wedgeEllipseCallout = 'WedgeEllipseCallout'
        cloudCallout = 'CloudCallout'
        cloud = 'Cloud'
        ribbon = 'Ribbon'
        ribbon2 = 'Ribbon2'
        ellipseRibbon = 'EllipseRibbon'
        ellipseRibbon2 = 'EllipseRibbon2'
        leftRightRibbon = 'LeftRightRibbon'
        verticalScroll = 'VerticalScroll'
        horizontalScroll = 'HorizontalScroll'
        wave = 'Wave'
        doubleWave = 'DoubleWave'
        plus = 'Plus'
        flowChartProcess = 'FlowChartProcess'
        flowChartDecision = 'FlowChartDecision'
        flowChartInputOutput = 'FlowChartInputOutput'
        flowChartPredefinedProcess = 'FlowChartPredefinedProcess'
        flowChartInternalStorage = 'FlowChartInternalStorage'
        flowChartDocument = 'FlowChartDocument'
        flowChartMultidocument = 'FlowChartMultidocument'
        flowChartTerminator = 'FlowChartTerminator'
        flowChartPreparation = 'FlowChartPreparation'
        flowChartManualInput = 'FlowChartManualInput'
        flowChartManualOperation = 'FlowChartManualOperation'
        flowChartConnector = 'FlowChartConnector'
        flowChartPunchedCard = 'FlowChartPunchedCard'
        flowChartPunchedTape = 'FlowChartPunchedTape'
        flowChartSummingJunction = 'FlowChartSummingJunction'
        flowChartOr = 'FlowChartOr'
        flowChartCollate = 'FlowChartCollate'
        flowChartSort = 'FlowChartSort'
        flowChartExtract = 'FlowChartExtract'
        flowChartMerge = 'FlowChartMerge'
        flowChartOfflineStorage = 'FlowChartOfflineStorage'
        flowChartOnlineStorage = 'FlowChartOnlineStorage'
        flowChartMagneticTape = 'FlowChartMagneticTape'
        flowChartMagneticDisk = 'FlowChartMagneticDisk'
        flowChartMagneticDrum = 'FlowChartMagneticDrum'
        flowChartDisplay = 'FlowChartDisplay'
        flowChartDelay = 'FlowChartDelay'
        flowChartAlternateProcess = 'FlowChartAlternateProcess'
        flowChartOffpageConnector = 'FlowChartOffpageConnector'
        actionButtonBlank = 'ActionButtonBlank'
        actionButtonHome = 'ActionButtonHome'
        actionButtonHelp = 'ActionButtonHelp'
        actionButtonInformation = 'ActionButtonInformation'
        actionButtonForwardNext = 'ActionButtonForwardNext'
        actionButtonBackPrevious = 'ActionButtonBackPrevious'
        actionButtonEnd = 'ActionButtonEnd'
        actionButtonBeginning = 'ActionButtonBeginning'
        actionButtonReturn = 'ActionButtonReturn'
        actionButtonDocument = 'ActionButtonDocument'
        actionButtonSound = 'ActionButtonSound'
        actionButtonMovie = 'ActionButtonMovie'
        gear6 = 'Gear6'
        gear9 = 'Gear9'
        funnel = 'Funnel'
        mathPlus = 'MathPlus'
        mathMinus = 'MathMinus'
        mathMultiply = 'MathMultiply'
        mathDivide = 'MathDivide'
        mathEqual = 'MathEqual'
        mathNotEqual = 'MathNotEqual'
        cornerTabs = 'CornerTabs'
        squareTabs = 'SquareTabs'
        plaqueTabs = 'PlaqueTabs'
        chartX = 'ChartX'
        chartStar = 'ChartStar'
        chartPlus = 'ChartPlus'
    
    class ShapeLineDashStyle:
        dash = 'Dash'
        dashDot = 'DashDot'
        dashDotDot = 'DashDotDot'
        longDash = 'LongDash'
        longDashDot = 'LongDashDot'
        roundDot = 'RoundDot'
        solid = 'Solid'
        squareDot = 'SquareDot'
        longDashDotDot = 'LongDashDotDot'
        systemDash = 'SystemDash'
        systemDot = 'SystemDot'
        systemDashDot = 'SystemDashDot'
    
    class ShapeFillType:
        noFill = 'NoFill'
        solid = 'Solid'
        gradient = 'Gradient'
        pattern = 'Pattern'
        pictureAndTexture = 'PictureAndTexture'
        slideBackground = 'SlideBackground'
    
    class TableStyle:
        noStyleNoGrid = 'NoStyleNoGrid'
        themedStyle1Accent1 = 'ThemedStyle1Accent1'
        themedStyle1Accent2 = 'ThemedStyle1Accent2'
        themedStyle1Accent3 = 'ThemedStyle1Accent3'
        themedStyle1Accent4 = 'ThemedStyle1Accent4'
        themedStyle1Accent5 = 'ThemedStyle1Accent5'
        themedStyle1Accent6 = 'ThemedStyle1Accent6'
        noStyleTableGrid = 'NoStyleTableGrid'
        themedStyle2Accent1 = 'ThemedStyle2Accent1'
        themedStyle2Accent2 = 'ThemedStyle2Accent2'
        themedStyle2Accent3 = 'ThemedStyle2Accent3'
        themedStyle2Accent4 = 'ThemedStyle2Accent4'
        themedStyle2Accent5 = 'ThemedStyle2Accent5'
        themedStyle2Accent6 = 'ThemedStyle2Accent6'
        lightStyle1 = 'LightStyle1'
        lightStyle1Accent1 = 'LightStyle1Accent1'
        lightStyle1Accent2 = 'LightStyle1Accent2'
        lightStyle1Accent3 = 'LightStyle1Accent3'
        lightStyle1Accent4 = 'LightStyle1Accent4'
        lightStyle1Accent5 = 'LightStyle1Accent5'
        lightStyle1Accent6 = 'LightStyle1Accent6'
        lightStyle2 = 'LightStyle2'
        lightStyle2Accent1 = 'LightStyle2Accent1'
        lightStyle2Accent2 = 'LightStyle2Accent2'
        lightStyle2Accent3 = 'LightStyle2Accent3'
        lightStyle2Accent4 = 'LightStyle2Accent4'
        lightStyle2Accent5 = 'LightStyle2Accent5'
        lightStyle2Accent6 = 'LightStyle2Accent6'
        lightStyle3 = 'LightStyle3'
        lightStyle3Accent1 = 'LightStyle3Accent1'
        lightStyle3Accent2 = 'LightStyle3Accent2'
        lightStyle3Accent3 = 'LightStyle3Accent3'
        lightStyle3Accent4 = 'LightStyle3Accent4'
        lightStyle3Accent5 = 'LightStyle3Accent5'
        lightStyle3Accent6 = 'LightStyle3Accent6'
        mediumStyle1 = 'MediumStyle1'
        mediumStyle1Accent1 = 'MediumStyle1Accent1'
        mediumStyle1Accent2 = 'MediumStyle1Accent2'
        mediumStyle1Accent3 = 'MediumStyle1Accent3'
        mediumStyle1Accent4 = 'MediumStyle1Accent4'
        mediumStyle1Accent5 = 'MediumStyle1Accent5'
        mediumStyle1Accent6 = 'MediumStyle1Accent6'
        mediumStyle2 = 'MediumStyle2'
        mediumStyle2Accent1 = 'MediumStyle2Accent1'
        mediumStyle2Accent2 = 'MediumStyle2Accent2'
        mediumStyle2Accent3 = 'MediumStyle2Accent3'
        mediumStyle2Accent4 = 'MediumStyle2Accent4'
        mediumStyle2Accent5 = 'MediumStyle2Accent5'
        mediumStyle2Accent6 = 'MediumStyle2Accent6'
        mediumStyle3 = 'MediumStyle3'
        mediumStyle3Accent1 = 'MediumStyle3Accent1'
        mediumStyle3Accent2 = 'MediumStyle3Accent2'
        mediumStyle3Accent3 = 'MediumStyle3Accent3'
        mediumStyle3Accent4 = 'MediumStyle3Accent4'
        mediumStyle3Accent5 = 'MediumStyle3Accent5'
        mediumStyle3Accent6 = 'MediumStyle3Accent6'
        mediumStyle4 = 'MediumStyle4'
        mediumStyle4Accent1 = 'MediumStyle4Accent1'
        mediumStyle4Accent2 = 'MediumStyle4Accent2'
        mediumStyle4Accent3 = 'MediumStyle4Accent3'
        mediumStyle4Accent4 = 'MediumStyle4Accent4'
        mediumStyle4Accent5 = 'MediumStyle4Accent5'
        mediumStyle4Accent6 = 'MediumStyle4Accent6'
        darkStyle1 = 'DarkStyle1'
        darkStyle1Accent1 = 'DarkStyle1Accent1'
        darkStyle1Accent2 = 'DarkStyle1Accent2'
        darkStyle1Accent3 = 'DarkStyle1Accent3'
        darkStyle1Accent4 = 'DarkStyle1Accent4'
        darkStyle1Accent5 = 'DarkStyle1Accent5'
        darkStyle1Accent6 = 'DarkStyle1Accent6'
        darkStyle2 = 'DarkStyle2'
        darkStyle2Accent1 = 'DarkStyle2Accent1'
        darkStyle2Accent2 = 'DarkStyle2Accent2'
        darkStyle2Accent3 = 'DarkStyle2Accent3'
    
    class SlideLayoutType:
        blank = 'Blank'
        chart = 'Chart'
        chartAndText = 'ChartAndText'
        clipArtAndText = 'ClipArtAndText'
        clipArtAndVerticalText = 'ClipArtAndVerticalText'
        comparison = 'Comparison'
        contentWithCaption = 'ContentWithCaption'
        custom = 'Custom'
        fourObjects = 'FourObjects'
        largeObject = 'LargeObject'
        mediaClipAndText = 'MediaClipAndText'
        mixed = 'Mixed'
        object = 'Object'
        objectAndText = 'ObjectAndText'
        objectAndTwoObjects = 'ObjectAndTwoObjects'
        objectOverText = 'ObjectOverText'
        organizationChart = 'OrganizationChart'
        pictureWithCaption = 'PictureWithCaption'
        sectionHeader = 'SectionHeader'
        table = 'Table'
        text = 'Text'
        textAndChart = 'TextAndChart'
        textAndClipArt = 'TextAndClipArt'
        textAndMediaClip = 'TextAndMediaClip'
        textAndObject = 'TextAndObject'
        textAndTwoObjects = 'TextAndTwoObjects'
        textOverObject = 'TextOverObject'
        title = 'Title'
        titleOnly = 'TitleOnly'
        twoColumnText = 'TwoColumnText'
        twoObjects = 'TwoObjects'
        twoObjectsAndObject = 'TwoObjectsAndObject'
        twoObjectsAndText = 'TwoObjectsAndText'
        twoObjectsOverText = 'TwoObjectsOverText'
        verticalText = 'VerticalText'
        verticalTitleAndText = 'VerticalTitleAndText'
        verticalTitleAndTextOverChart = 'VerticalTitleAndTextOverChart'
    
    class ShapeLineStyle:
        single = 'Single'
        thickBetweenThin = 'ThickBetweenThin'
        thickThin = 'ThickThin'
        thinThick = 'ThinThick'
        thinThin = 'ThinThin'
    
    class ShapeZOrder:
        bringForward = 'BringForward'
        bringToFront = 'BringToFront'
        sendBackward = 'SendBackward'
        sendToBack = 'SendToBack'
    
    class DocumentPropertyType:
        boolean = 'Boolean'
        date = 'Date'
        number = 'Number'
        string = 'String'
    
    class InsertSlideFormatting:
        keepSourceFormatting = 'KeepSourceFormatting'
        useDestinationTheme = 'UseDestinationTheme'
    
    class ErrorCodes:
        generalException = 'GeneralException'
    
    class Application:
        pass
    
    class Presentation:
        pass
    
    class AddSlideOptions:
        pass
    
    class CustomXmlPart:
        pass
    
    class CustomXmlPartScopedCollection:
        pass
    
    class CustomXmlPartCollection:
        pass
    
    class BulletFormat:
        pass
    
    class ParagraphFormat:
        pass
    
    class ShapeFont:
        pass
    
    class TextFrame:
        pass
    
    class TextRange:
        pass
    
    class Hyperlink:
        pass
    
    class PlaceholderFormat:
        pass
    
    class HyperlinkCollection:
        pass
    
    class ShapeAddOptions:
        pass
    
    class Border:
        pass
    
    class Borders:
        pass
    
    class Margins:
        pass
    
    class ShapeFill:
        pass
    
    class FontProperties:
        pass
    
    class TextRun:
        pass
    
    class TableCell:
        pass
    
    class TableCellCollection:
        pass
    
    class TableColumn:
        pass
    
    class TableColumnCollection:
        pass
    
    class TableClearOptions:
        pass
    
    class TableRow:
        pass
    
    class TableRowCollection:
        pass
    
    class TableStyleSettings:
        pass
    
    class Table:
        pass
    
    class FillProperties:
        pass
    
    class BorderProperties:
        pass
    
    class TableCellBorders:
        pass
    
    class TableCellMargins:
        pass
    
    class TableCellProperties:
        pass
    
    class TableColumnProperties:
        pass
    
    class TableMergedAreaProperties:
        pass
    
    class TableRowProperties:
        pass
    
    class TableAddOptions:
        pass
    
    class ShapeCollection:
        pass
    
    class SlideGetImageOptions:
        pass
    
    class SlideLayout:
        pass
    
    class SlideLayoutCollection:
        pass
    
    class SlideMaster:
        pass
    
    class Tag:
        pass
    
    class TagCollection:
        pass
    
    class Slide:
        pass
    
    class ShapeScopedCollection:
        pass
    
    class ShapeGroup:
        pass
    
    class ShapeLineFormat:
        pass
    
    class Shape:
        pass
    
    class Binding:
        pass
    
    class BindingCollection:
        pass
    
    class CustomProperty:
        pass
    
    class CustomPropertyCollection:
        pass
    
    class DocumentProperties:
        pass
    
    class InsertSlideOptions:
        pass
    
    class SlideCollection:
        pass
    
    class SlideScopedCollection:
        pass
    
    class SlideMasterCollection:
        pass
    
    class RequestContext:
        pass
    
    class Interfaces:
        
        class CollectionLoadOptions:
            pass
        
        class CustomXmlPartScopedCollectionUpdateData:
            pass
        
        class CustomXmlPartCollectionUpdateData:
            pass
        
        class BulletFormatUpdateData:
            pass
        
        class ParagraphFormatUpdateData:
            pass
        
        class ShapeFontUpdateData:
            pass
        
        class TextFrameUpdateData:
            pass
        
        class TextRangeUpdateData:
            pass
        
        class HyperlinkUpdateData:
            pass
        
        class HyperlinkCollectionUpdateData:
            pass
        
        class BorderUpdateData:
            pass
        
        class MarginsUpdateData:
            pass
        
        class ShapeFillUpdateData:
            pass
        
        class TableCellUpdateData:
            pass
        
        class TableCellCollectionUpdateData:
            pass
        
        class TableColumnUpdateData:
            pass
        
        class TableColumnCollectionUpdateData:
            pass
        
        class TableRowUpdateData:
            pass
        
        class TableRowCollectionUpdateData:
            pass
        
        class TableStyleSettingsUpdateData:
            pass
        
        class ShapeCollectionUpdateData:
            pass
        
        class SlideLayoutCollectionUpdateData:
            pass
        
        class TagUpdateData:
            pass
        
        class TagCollectionUpdateData:
            pass
        
        class ShapeScopedCollectionUpdateData:
            pass
        
        class ShapeLineFormatUpdateData:
            pass
        
        class ShapeUpdateData:
            pass
        
        class BindingCollectionUpdateData:
            pass
        
        class CustomPropertyUpdateData:
            pass
        
        class CustomPropertyCollectionUpdateData:
            pass
        
        class DocumentPropertiesUpdateData:
            pass
        
        class SlideCollectionUpdateData:
            pass
        
        class SlideScopedCollectionUpdateData:
            pass
        
        class SlideMasterCollectionUpdateData:
            pass
        
        class PresentationData:
            pass
        
        class CustomXmlPartData:
            pass
        
        class CustomXmlPartScopedCollectionData:
            pass
        
        class CustomXmlPartCollectionData:
            pass
        
        class BulletFormatData:
            pass
        
        class ParagraphFormatData:
            pass
        
        class ShapeFontData:
            pass
        
        class TextFrameData:
            pass
        
        class TextRangeData:
            pass
        
        class HyperlinkData:
            pass
        
        class PlaceholderFormatData:
            pass
        
        class HyperlinkCollectionData:
            pass
        
        class BorderData:
            pass
        
        class BordersData:
            pass
        
        class MarginsData:
            pass
        
        class ShapeFillData:
            pass
        
        class TableCellData:
            pass
        
        class TableCellCollectionData:
            pass
        
        class TableColumnData:
            pass
        
        class TableColumnCollectionData:
            pass
        
        class TableRowData:
            pass
        
        class TableRowCollectionData:
            pass
        
        class TableStyleSettingsData:
            pass
        
        class TableData:
            pass
        
        class ShapeCollectionData:
            pass
        
        class SlideLayoutData:
            pass
        
        class SlideLayoutCollectionData:
            pass
        
        class SlideMasterData:
            pass
        
        class TagData:
            pass
        
        class TagCollectionData:
            pass
        
        class SlideData:
            pass
        
        class ShapeScopedCollectionData:
            pass
        
        class ShapeGroupData:
            pass
        
        class ShapeLineFormatData:
            pass
        
        class ShapeData:
            pass
        
        class BindingData:
            pass
        
        class BindingCollectionData:
            pass
        
        class CustomPropertyData:
            pass
        
        class CustomPropertyCollectionData:
            pass
        
        class DocumentPropertiesData:
            pass
        
        class SlideCollectionData:
            pass
        
        class SlideScopedCollectionData:
            pass
        
        class SlideMasterCollectionData:
            pass
        
        class PresentationLoadOptions:
            pass
        
        class CustomXmlPartLoadOptions:
            pass
        
        class CustomXmlPartScopedCollectionLoadOptions:
            pass
        
        class CustomXmlPartCollectionLoadOptions:
            pass
        
        class BulletFormatLoadOptions:
            pass
        
        class ParagraphFormatLoadOptions:
            pass
        
        class ShapeFontLoadOptions:
            pass
        
        class TextFrameLoadOptions:
            pass
        
        class TextRangeLoadOptions:
            pass
        
        class HyperlinkLoadOptions:
            pass
        
        class PlaceholderFormatLoadOptions:
            pass
        
        class HyperlinkCollectionLoadOptions:
            pass
        
        class BorderLoadOptions:
            pass
        
        class BordersLoadOptions:
            pass
        
        class MarginsLoadOptions:
            pass
        
        class ShapeFillLoadOptions:
            pass
        
        class TableCellLoadOptions:
            pass
        
        class TableCellCollectionLoadOptions:
            pass
        
        class TableColumnLoadOptions:
            pass
        
        class TableColumnCollectionLoadOptions:
            pass
        
        class TableRowLoadOptions:
            pass
        
        class TableRowCollectionLoadOptions:
            pass
        
        class TableStyleSettingsLoadOptions:
            pass
        
        class TableLoadOptions:
            pass
        
        class ShapeCollectionLoadOptions:
            pass
        
        class SlideLayoutLoadOptions:
            pass
        
        class SlideLayoutCollectionLoadOptions:
            pass
        
        class SlideMasterLoadOptions:
            pass
        
        class TagLoadOptions:
            pass
        
        class TagCollectionLoadOptions:
            pass
        
        class SlideLoadOptions:
            pass
        
        class ShapeScopedCollectionLoadOptions:
            pass
        
        class ShapeGroupLoadOptions:
            pass
        
        class ShapeLineFormatLoadOptions:
            pass
        
        class ShapeLoadOptions:
            pass
        
        class BindingLoadOptions:
            pass
        
        class BindingCollectionLoadOptions:
            pass
        
        class CustomPropertyLoadOptions:
            pass
        
        class CustomPropertyCollectionLoadOptions:
            pass
        
        class DocumentPropertiesLoadOptions:
            pass
        
        class SlideCollectionLoadOptions:
            pass
        
        class SlideScopedCollectionLoadOptions:
            pass
        
        class SlideMasterCollectionLoadOptions:
            pass
