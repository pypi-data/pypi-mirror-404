"""
XPyCode - Synchronous COM-like bridge between Python and Excel Office.js.

This package provides a synchronous proxy to Office.js objects, allowing
Python code to interact with Excel through a COM-like interface.

Exports:
- context: Context proxy object for Excel operations (typed as Excel.RequestContext)
- excel: Root proxy object for Excel operations (typed as Excel)
- messaging: Messaging singleton for send/receive handling
- Serializer: Handles marshaling of data types between Python and JavaScript
- OfficeJsObject: Dynamic proxy for Office.js objects
- OfficeJsArray: Specialized proxy for arrays
- OfficeJsDict: Specialized proxy for dictionaries
- saveObject: Store an object in the ObjectKeeper
- getObject: Retrieve an object from the ObjectKeeper
- clearObject: Remove an object from the ObjectKeeper
- clearAllObjects: Clear all objects from the ObjectKeeper
"""

from typing import Any, Optional, TYPE_CHECKING
from pandas import DataFrame
# Kernel instance reference (set by kernel on connect)
# Mandatory to define here to avoid circular imports
_kernel_instance = None
def get_kernel_instance():
    return _kernel_instance

from .utils import ( 
                    Intersect, saveObject, getObject, clearObject, clearAllObjects,
                    showMessageBox,showMessageBoxError,showMessageBoxInfo,
                    showMessageBoxWarning,
                    setEnableEvents,
                    RangeToDf,DfToRange,#Union,Intersect
                    )
from .com_like import (
    Context as _ContextImpl,
    Excel as _ExcelImpl,
    GetSetting,
    Union,Intersect,
    messaging,
    Serializer,
    OfficeJsObject,
    OfficeJsArray,
    OfficeJsDict,
)
from .office_objects import Excel, Office, OfficeExtension, OfficeCore
from ... import __version__

# Type-annotated instances for Intellisense/Autocompletion
# The runtime objects are OfficeJsObject proxies, but we annotate them with
# the stub types from office_objects.py to enable IDE completion.
excel: Excel = _ExcelImpl  # type: ignore[assignment]
context: Excel.RequestContext = _ContextImpl  # type: ignore[assignment]

# Kernel instance reference (set by kernel on connect)



def _get_workbook():
    return context.workbook

def _get_worksheets(nb=5):
    try:
        return context.workbook.worksheets
    except:
        # Call again as the first call may not succeed 
        if(nb==0):
            raise
        return _get_worksheets(nb-1)


_module_properties={
    'workbook':_get_workbook,
    'worksheets':_get_worksheets,
}

def __getattr__(name):
    if name in _module_properties:
        return _module_properties[name]()
    raise AttributeError(name)

if TYPE_CHECKING:
    workbook:Excel.Workbook
    worksheets:Excel.WorksheetCollection

class Messages:
    def showMessageBox( message: str, title: str = "XPyCode", type:str="Info") -> None:
        showMessageBox(message, title, type)
    def showMessageBoxError(message: str, title: str = "XPyCode") -> None:
        showMessageBoxError(message, title)
    def showMessageBoxInfo(message: str, title: str = "XPyCode") -> None:
        showMessageBoxInfo(message, title)
    def showMessageBoxWarning( message: str, title: str = "XPyCode") -> None:
        showMessageBoxWarning(message, title)

class Objects:
    def saveObject(key: str, value: Any) -> None:
        saveObject(key, value)
    def getObject( key: str) -> Optional[Any]:
        return getObject(key)
    def clearObject( key: str) -> None:
        clearObject(key)
    def clearAllObjects() -> None:
        clearAllObjects()

class EventManager:
    def setEnableEvents(enable: bool) -> None:
        setEnableEvents(enable)

    def getEnableEvents() -> bool:
        return  GetSetting('enableEditorEvents')
        
    def getEventArgsRange(event_args)->Excel.Range:
        if hasattr(event_args,'worksheetId') and hasattr(event_args,'address'):
            ws=_get_worksheets().getItem(event_args.worksheetId)
            r=ws.getRange(event_args.address)
            return r
        raise TypeError('The event_args argument must have both worksheetId and address')



class Tools:
    def RangeToDf(range: Excel.Range) -> DataFrame:
        return RangeToDf(range)
    def DfToRange(df: DataFrame, range: Excel.Range) -> Excel.Range:
        return DfToRange(df, range)
    def Union(*ranges: Excel.Range|Excel.RangeAreas) -> Excel.Range|Excel.RangeAreas:
        ranges=[r for r in ranges if r is not None]
        return Union(*ranges)
    def Intersect(*ranges:Excel.Range|Excel.RangeAreas)->Excel.Range|Excel.RangeAreas:
        ranges=[r for r in ranges if r is not None]
        return Intersect(*ranges)

__all__ = [
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
    "Objects",
    "Messages",
    "EventManager",
    "Tools",
]+list(_module_properties.keys())
