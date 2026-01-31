from pandas import DataFrame
from typing import Any, Optional
from .office_objects import (
                            Excel as _Excel,
                            Office as _Office,
                           OfficeExtension as _OfficeExtension, 
                           OfficeCore as _OfficeCore
                            )
__all__ = [
    "workbook",
    "worksheets",
    "context",
    "excel",
    "Excel", #Excel class representing Excel type for users intellisense and event_args typing
    "Office",
    "OfficeExtension",
    "OfficeCore",
    "messaging",
    "Serializer",
    "OfficeJsObject",
    "OfficeJsArray",
    "OfficeJsDict",
    "objects",
    "getEventArgsRange",
    "messages",
    "eventManager",
    "tools"
]

class Excel(_Excel): ...
class Office(_Office): ...
class OfficeExtension(_OfficeExtension): ...
class OfficeCore(_OfficeCore): ...

__version__: str

# Main proxy instances - the primary API
excel: Excel
context: Excel.RequestContext

# Convenience properties
workbook: Excel.Workbook
worksheets: Excel.WorksheetCollection

# ObjectKeeper functions
class Objects:
    def saveObject(key: str, value: Any) -> None: ...
    def getObject(key: str) -> Optional[Any]: ...
    def clearObject(key: str) -> None: ...
    def clearAllObjects() -> None: ...


class EventManager:
    def setEnableEvents( enable: bool) -> None:...
    def getEnableEvents() -> bool:...
    # Event helper
    def getEventArgsRange(event_args: Any) -> Excel.Range: ...


class Tools:
    def RangeToDf(range: Excel.Range) -> DataFrame: ...
    def DfToRange(df: DataFrame, range: Excel.Range) -> Excel.Range: ...
    def Union(*ranges: Excel.Range|Excel.RangeAreas) -> Excel.Range|Excel.RangeAreas: ...
    def Intersect(*ranges:Excel.Range|Excel.RangeAreas)->Excel.Range|Excel.RangeAreas: ...


# Message box functions

class Messages:
    def showMessageBox(message: str, title: str = "XPyCode", type:str="Info") -> None: ...
    def showMessageBoxError(message: str, title: str = "XPyCode") -> None: ...
    def showMessageBoxInfo(message: str, title: str = "XPyCode") -> None: ...
    def showMessageBoxWarning(message: str, title: str = "XPyCode") -> None: ...


