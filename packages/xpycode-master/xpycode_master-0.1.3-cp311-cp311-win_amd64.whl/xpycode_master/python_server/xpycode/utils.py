from math import e
from typing import Any, Optional, TYPE_CHECKING

import pandas
from . import get_kernel_instance
from ...logging_config import get_logger
from .office_objects import Excel

logger = get_logger(__name__)

def saveObject(key: str, value: Any) -> None:
    """
    Store an object in the ObjectKeeper.
    
    Args:
        key: String key for the object
        value: Object to store
        
    Raises:
        RuntimeError: If kernel instance is not available
    """
    _kernel_instance = get_kernel_instance()
    if _kernel_instance is None:
        logger.error("Attempted to save object but kernel instance is not available")
        raise RuntimeError("ObjectKeeper not available: kernel not connected")
    _kernel_instance.save_object(key, value)


def getObject(key: str) -> Optional[Any]:
    """
    Retrieve an object from the ObjectKeeper.
    
    Args:
        key: String key for the object
        
    Returns:
        The stored object or None if not found
        
    Raises:
        RuntimeError: If kernel instance is not available
    """
    _kernel_instance = get_kernel_instance()
    if _kernel_instance is None:
        raise RuntimeError("ObjectKeeper not available: kernel not connected")
    return _kernel_instance.get_object(key)


def clearObject(key: str) -> None:
    """
    Remove an object from the ObjectKeeper.
    
    Args:
        key: String key for the object to remove
        
    Raises:
        RuntimeError: If kernel instance is not available
    """
    _kernel_instance = get_kernel_instance()
    if _kernel_instance is None:
        raise RuntimeError("ObjectKeeper not available: kernel not connected")
    _kernel_instance.clear_object(key)


def clearAllObjects() -> None:
    """
    Clear all objects from the ObjectKeeper.
    
    Raises:
        RuntimeError: If kernel instance is not available
    """
    _kernel_instance = get_kernel_instance()
    if _kernel_instance is None:
        raise RuntimeError("ObjectKeeper not available: kernel not connected")
    _kernel_instance.clear_all_objects()

def setEnableEvents(enable: bool) -> None:
    """
    Enable or disable event handling in the Excel add-in.
    ⚠️ only affects event handlers from XPyCode Editor
    
    Args:
        enable: True to enable events, False to disable
    """
    _kernel_instance = get_kernel_instance()
    if _kernel_instance is None:
        raise RuntimeError("Cannot set event handling: kernel not connected")
    _kernel_instance.set_enable_events(enable)

def showMessageBox(message: str, title: str = "XPyCode", type:str="Info") -> None:
    """
    Show a message box in the Excel add-in UI.
    
    Args:
        message: The message to display
        title: The title of the message box (default: "XPyCode")
        type: The type of message box ("Info", "Warning", "Error")
        
    Raises:
        RuntimeError: If kernel instance is not available
    """
    _kernel_instance = get_kernel_instance()
    if _kernel_instance is None:
        raise RuntimeError("Cannot show message box: kernel not connected")
    _kernel_instance.show_message_box(message, title,type)

def showMessageBoxInfo(message: str, title: str = "XPyCode") -> None:
    """
    Show an info message box in the Excel add-in UI.
    Args:
            message: The message to display
            title: The title of the message box (default: "XPyCode")
        
        Raises:
            RuntimeError: If kernel instance is not available
    """
    showMessageBox(message, title, type="Info")
                   
def showMessageBoxWarning(message: str, title: str = "XPyCode") -> None:
    """
    Show a warning message box in the Excel add-in UI.
    Args:
            message: The message to display
            title: The title of the message box (default: "XPyCode")
        
        Raises:
            RuntimeError: If kernel instance is not available
    """
    showMessageBox(message, title, type="Warning")

def showMessageBoxError(message: str, title: str = "XPyCode") -> None:
    """
    Show an error message box in the Excel add-in UI.
    Args:
            message: The message to display
            title: The title of the message box (default: "XPyCode")
        
        Raises:
            RuntimeError: If kernel instance is not available
    """
    showMessageBox(message, title, type="Error")


def DfToRange(df:pandas.DataFrame, start_cell:Excel.Range)->Excel.Range:
    """
    Helper function to write a pandas DataFrame to an Excel Range.
    
    Args:
        df: The pandas DataFrame to write
        start_cell: The top-left cell address where the DataFrame will be written (default: 'A1')
        
    Returns:
        The Excel Range where the DataFrame was written
    """
    dfs=df.shape
    r=start_cell.getResizedRange(dfs[0],dfs[1]-1)
    r.values=df
    return df

def RangeToDf(r:Excel.Range)->pandas.DataFrame:
    """
    Helper function to read an Excel Range into a pandas DataFrame.
    
    Args:
        r: The Excel Range to read
        
    Returns:
        A pandas DataFrame containing the data from the Excel Range
    """
    vals=r.values
    df=pandas.DataFrame(vals[1:],columns=vals[0])
    return df

def Union(*ranges:Excel.Range)->Excel.Range|Excel.RangeAreas:
    """
    Helper function to create a union of multiple Excel Ranges.
    
    Args:
        *ranges: Multiple Excel Range objects to union
        
    Returns:
        A single Excel Range representing the union of the input ranges
    """

    ranges=[r for r in ranges if r is not None]

    if not ranges:
        return None
    ws=ranges[0].worksheet
    if any(r.worksheet.name!=ws.name for r in ranges):
        raise ValueError("All ranges must be on the same worksheet to create a union")
    addr=",".join(r.address for r in ranges)
    return ws.getRanges(addr)

def Intersect(*ranges:Excel.Range)->Excel.Range|Excel.RangeAreas:
    """
    Helper function to create an intersection of multiple Excel Ranges.
    
    Args:
        *ranges: Multiple Excel Range objects to intersect
        
    Returns:
        A single Excel Range representing the intersection of the input ranges
    """
    ranges=[r for r in ranges if r is not None]
    if not ranges:
        return None
    ws=ranges[0].worksheet
    if any(r.worksheet.name!=ws.name for r in ranges):
        raise ValueError("All ranges must be on the same worksheet to create an intersection")
    

    if len(ranges)==1:
        return ranges[0]
    r1=ranges[0]
    r2=Intersect(*ranges[1:])
    if r2 is None:
        return None

    if r1._className=='RangeAreas':
        to_union=[]
        for area in r1.areas.items:
            inter=Intersect(area,r2)
            if inter is not None:
                to_union.append(inter)
        if to_union:
            return Union(*to_union)
        else:
            return None
    elif r2._className=='RangeAreas':
        to_union=[]
        for area in r2.areas.items:
            inter=Intersect(r1,area)
            if inter is not None:
                to_union.append(inter)
        if to_union:
            return Union(*to_union)
        else:
            return None



    r1Top    = r1.rowIndex;
    r1Left   = r1.columnIndex;
    r1Bottom = r1Top + r1.rowCount - 1;
    r1Right  = r1Left + r1.columnCount - 1;

    r2Top    = r2.rowIndex;
    r2Left   = r2.columnIndex;
    r2Bottom = r2Top + r2.rowCount - 1;
    r2Right  = r2Left + r2.columnCount - 1;

    top    = max(r1Top, r2Top);
    left   = max(r1Left, r2Left);
    bottom = min(r1Bottom, r2Bottom);
    right  = min(r1Right, r2Right);

    if top > bottom or left > right: 
        return None

    intersect = ws.getRangeByIndexes(
        top,
        left,
        bottom - top + 1,
        right - left + 1
      )

    return intersect