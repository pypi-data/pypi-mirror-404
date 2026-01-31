"""
XPyCode - Synchronous COM-like bridge between Python and Excel Office.js.

This module provides a synchronous proxy to Office.js objects, allowing
Python code to interact with Excel through a COM-like interface.

Classes:
- Serializer: Handles marshaling of data types between Python and JavaScript
- Messaging: Handles message passing with synchronous send/wait (no WebSocket server)
- OfficeJsObject: Dynamic proxy for Office.js objects
- OfficeJsArray: Specialized proxy for arrays
- OfficeJsDict: Specialized proxy for dictionaries

Globals:
- Excel: Root proxy object (ID 1)
- Context: Context proxy object (ID 0)
"""

import base64
import concurrent.futures
from ctypes import Union
import datetime as dt
import threading
import uuid
import pandas as pd
import numpy as np
from typing import Any, Dict


# ---------------- Serialization Registry
class Serializer:
    """Handles marshaling of data types between Python and JavaScript."""

    @staticmethod
    def to_wire(value: Any) -> Dict[str, Any]:
        """
        Serialize a Python value to wire format for transmission.

        Supports: None, bool, int, float, str, datetime, bytes, list, dict,
        and OfficeJsObject wrappers.
        """
        if value is None:
            return {"type": "Null", "value": None, "isSpec": False}
        if isinstance(value, (bool, np.bool_)):
            return {"type": "Bool", "value": bool(value), "isSpec": False}
        if isinstance(value, int):
            return {"type": "Int", "value": int(value), "isSpec": False}
        if isinstance(value, float):
            return {"type": "Float", "value": float(value), "isSpec": False}
        if isinstance(value, str):
            return {"type": "String", "value": value, "isSpec": False}
        if isinstance(value, (dt.datetime, dt.date, pd.Timestamp, np.datetime64)):
            # Always send ISO 8601 (UTC if datetime has tzinfo)
            if isinstance(value, dt.datetime) and value.tzinfo:
                value = value.astimezone(dt.timezone.utc)
            iso = value.isoformat()
            return {"type": "Date", "value": iso, "isSpec": False}
        if isinstance(value, (bytes, bytearray, memoryview)):
            b64 = base64.b64encode(bytes(value)).decode("ascii")
            return {"type": "Bytes", "value": b64, "isSpec": False}
        if isinstance(value, (list, tuple)):
            return {
                "type": "Array",
                "value": [Serializer.to_wire(v) for v in value],
                "isSpec": False,
            }
        if isinstance(value, dict):
            return {
                "type": "Dict",
                "value": {k: Serializer.to_wire(v) for k, v in value.items()},
                "isSpec": False,
            }

        try:
            if np.isna(value):
                return {"type": "Null", "value": None, "isSpec": False}
        except:
            pass
        if isinstance(value, (pd.Series, pd.DataFrame)):
            if isinstance(value, pd.Series):
                value = value.to_frame()
        
            result = [value.columns.tolist()]
            for row in value.values:
                result.append(row.tolist())
            rep= Serializer.to_wire(result)
            return rep

        if isinstance(value, OfficeJsObject):
            return {"type": value._internal_typeName, "value": value._internal_id, "isSpec": True}
        
        # Handle Python callables (functions, lambdas, methods, etc.)
        if callable(value):
            callable_id = messaging.register_callable(value)
            return {"type": "Python_Function", "value": callable_id, "isSpec": True}
        
        # Fallback: stringify
        return {"type": "String", "value": str(value), "isSpec": False}

    @staticmethod
    def from_wire(wire: Dict[str, Any]) -> Any:
        """
        Deserialize a wire format value back to Python.

        Handles: Null, Bool, Int, Float, String, Date, Bytes, Array, Dict,
        and special OfficeJs object references.
        """
        t = wire.get("type")
        v = wire.get("value")
        i = wire.get("isSpec")
        obj_id = wire.get("id")

        if t == "Null":
            return None
        if t == "Bool":
            return bool(v)
        if t in ("Int", "Float"):
            return float(v) if t == "Float" else int(v)
        if t == "String":
            return str(v)
        if t == "Date":
            # Parse ISO format
            try:
                return dt.datetime.fromisoformat(v)
            except Exception:
                return v
        if t == "Bytes":
            return base64.b64decode(v or b"")
        if t == "Array":
            ret = OfficeJsArray(obj_id)
            ret.extend([Serializer.from_wire(x) for x in (v or [])])
            return ret
        if t == "Dict":
            ret = OfficeJsDict(obj_id)
            ret.update({k: Serializer.from_wire(x) for k, x in (v or {}).items()})
            return ret
        if i:
            return OfficeJsObject(int(v), t)

        return str(v)


# ---------------- Messaging (no WebSocket server)
class Messaging:
    """
    Handles messaging for the Python-Excel bridge.

    This class does NOT start a WebSocket server. Instead, it uses a
    send handler callback pattern that allows the kernel to forward
    messages through the Business Layer.
    
    Threading Model:
    ----------------
    This class is designed to be thread-safe for use in multi-threaded environments:
    - waiters dict: Protected by _waiters_lock (threading.Lock)
    - callable_registry: Protected by _callable_lock (threading.Lock)
    - send_request_sync(): Can be called from worker threads, blocks using concurrent.futures.Future
    - on_message(): Can be called from listener thread to resolve pending futures
    """

    def __init__(self):
        # Thread-safe futures for pending requests (requestId -> Future)
        # Threading Note: This dict is accessed from both worker and listener threads
        self.waiters: Dict[str, concurrent.futures.Future] = {}
        self._waiters_lock = threading.Lock()

        self._guid = uuid.uuid4().hex
        self._send_handler = None
        self.loop = None
        self.loop_thread = None
        
        # Registry for Python callables that can be invoked from Excel
        # Maps callable_id -> callable object
        # Threading Note: This dict is accessed from multiple threads
        self._callable_registry: Dict[str, Any] = {}
        self._callable_lock = threading.Lock()
        self._next_callable_id = 1

    def set_send_handler(self, handler):
        """
        Register a callback used to send messages to the add-in.

        The handler should be a callable that takes a dict (the message payload)
        and sends it appropriately (e.g., via WebSocket through the Business Layer).
        """
        self._send_handler = handler

    def on_message(self, message: Dict[str, Any]):
        """
        Handle an incoming response message from the add-in.

        This method is called by the kernel when it receives an excel_response
        message. It resolves the pending future for the corresponding request.
        
        Threading Note: This method is typically called from the listener thread.
        The _waiters_lock ensures thread-safe access to the waiters dict.
        """
        req_id = message.get("requestId")
        if not req_id:
            return

        # Threading Note: Lock protects concurrent access to waiters dict
        with self._waiters_lock:
            fut = self.waiters.pop(req_id, None)

        # Set result on the future if it exists and is not done
        # Note: A future is "done" if it has a result, exception, or was cancelled
        if fut and not fut.done():
            if message.get("ok"):
                fut.set_result(message)
            else:
                error_msg = message.get("error", {}).get("message", "Remote error")
                fut.set_exception(RuntimeError(error_msg))

    def send_request_sync(self, req: Dict[str, Any], timeout: float = 30.0):
        """
        Send a request and wait synchronously for the response.

        This creates a thread-safe Future, calls the send handler, and blocks
        until the response is received (or timeout).
        
        Threading Note: This method can be called from worker threads. It blocks
        the calling thread using concurrent.futures.Future.result(), but releases
        the GIL so the listener thread can continue processing messages.
        """
        if not self._send_handler:
            raise RuntimeError("No send handler registered")

        rid = uuid.uuid4().hex
        env = {**req, "requestId": rid, "kind": "request"}

        # Create a thread-safe Future
        # Threading Note: concurrent.futures.Future is thread-safe
        fut = concurrent.futures.Future()
        with self._waiters_lock:
            self.waiters[rid] = fut

        try:
            # Call the send handler to transmit the message
            self._send_handler(env)

            # Wait for the response (blocking)
            # Threading Note: fut.result() blocks the worker thread but releases the GIL,
            # allowing the listener thread to call on_message() and set the result
            return fut.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            # Clean up on timeout
            with self._waiters_lock:
                self.waiters.pop(rid, None)
            raise TimeoutError("Timed out waiting for Office.js response")
        except Exception:
            # Clean up on error
            with self._waiters_lock:
                self.waiters.pop(rid, None)
            raise

    def reset(self):
        """
        Reset the messaging state (e.g., when the connection is closed).

        Cancels all pending futures and generates a new GUID.
        
        Threading Note: This method should be called from the listener thread
        during disconnect/reconnect. The locks ensure thread-safe cleanup.
        """
        # Threading Note: Lock protects concurrent access during cleanup
        with self._waiters_lock:
            for fut in list(self.waiters.values()):
                if not fut.done():
                    fut.cancel()
            self.waiters.clear()

        self._guid = uuid.uuid4().hex

        # Clear callable registry on reset
        # Threading Note: Lock protects concurrent access during cleanup
        with self._callable_lock:
            self._callable_registry.clear()
            self._next_callable_id = 1

        # Update global proxy objects with new GUID
        # Note: Context and Excel are defined at module level after this class
        try:
            Context._msg_guid = self._guid
        except NameError:
            pass
        except Exception:
            pass
        try:
            Excel._msg_guid = self._guid
        except NameError:
            pass
        except Exception:
            pass

    def register_callable(self, callable_obj: Any) -> str:
        """
        Register a Python callable and return its ID.

        Args:
            callable_obj: The callable to register (function, lambda, method, etc.)

        Returns:
            String ID that can be used to invoke the callable from Excel.
            
        Raises:
            TypeError: If callable_obj is not callable
            
        Threading Note: This method is thread-safe due to _callable_lock.
        Can be called from any thread (worker or listener).
        """
        # Validate that the object is callable
        if not callable(callable_obj):
            raise TypeError(f"Object must be callable, got {type(callable_obj).__name__}")
        
        with self._callable_lock:
            # Include GUID prefix to prevent collisions across messaging instances
            callable_id = f"pyfunc_{self._guid[:8]}_{self._next_callable_id}"
            self._next_callable_id += 1
            self._callable_registry[callable_id] = callable_obj
            return callable_id

    def get_callable(self, callable_id: str) -> Any:
        """
        Retrieve a registered callable by its ID.

        Args:
            callable_id: The ID returned by register_callable.

        Returns:
            The callable object, or None if not found.
            
        Threading Note: This method is thread-safe due to _callable_lock.
        Can be called from any thread (worker or listener).
        """
        with self._callable_lock:
            return self._callable_registry.get(callable_id)

    def unregister_callable(self, callable_id: str):
        """
        Remove a callable from the registry.

        Args:
            callable_id: The ID of the callable to remove.
            
        Threading Note: This method is thread-safe due to _callable_lock.
        Can be called from any thread (worker or listener).
        """
        with self._callable_lock:
            self._callable_registry.pop(callable_id, None)


# ---------------- Office.js Object Proxy Helpers


def _cw__getattr__(self, name: str):
    """Get attribute proxy method for OfficeJsObject."""
    if name in ["_internal_id", "_internal_typeName", "_msg_guid","_typ", "_internal_cache"]:
        return object.__getattribute__(self, name)

    if self._msg_guid != messaging._guid:
        raise RuntimeError("Excel Object used after messaging context was stopped")

    if False and name in self._internal_cache:
        return self._internal_cache[name]

    req = {"method": "GET", "name": name, "caller": self._internal_id}
    env = messaging.send_request_sync(req)
    if not env.get("ok"):
        raise AttributeError(
            env.get("error", {}).get("message", f"GET failed for {name}")
        )
    rep = Serializer.from_wire(env.get("result"))
    if False and isinstance(rep, OfficeJsObject):
        self._internal_cache[name] = rep
    return rep

def _cw__getitem__(self, index):
    """Get item proxy method for OfficeJsObject."""
    if isinstance(index, slice):
        # Slice handling: convert to "start:stop:step" format
        start = index.start if index.start is not None else ""
        stop = index.stop if index.stop is not None else ""
        step = index.step if index.step is not None else ""
        index_str = f"{start}:{stop}:{step}"
    elif isinstance(index, int):
        index_str = str(index)
    else:
        raise TypeError("Index must be an integer or a slice")

    if self._msg_guid != messaging._guid:
        raise RuntimeError("Excel Object used after messaging context was stopped")

    req = {"method": "GETITEM", "name": index_str, "caller": self._internal_id}
    env = messaging.send_request_sync(req)
    if not env.get("ok"):
        raise AttributeError(
            env.get("error", {}).get("message", f"GET ITEM failed for {index}")
        )
    return Serializer.from_wire(env.get("result"))


def _cw__setattr__(self, name: str, value):
    """Set attribute proxy method for OfficeJsObject."""
    if name in ("_internal_id", "_internal_typeName", "_msg_guid","_typ"):
        return object.__setattr__(self, name, value)

    if self._msg_guid != messaging._guid:
        raise RuntimeError("Excel Object used after messaging context was stopped")

    wire = Serializer.to_wire(value)
    req = {"method": "SET", "name": name, "value": wire, "caller": self._internal_id}
    env = messaging.send_request_sync(req)
    if not env.get("ok"):
        raise AttributeError(
            env.get("error", {}).get("message", f"SET failed for {name}")
        )


def _cw__call__(self, *args, **kwargs):
    """Call proxy method for OfficeJsObject (Function type)."""
    if self._msg_guid != messaging._guid:
        raise RuntimeError("Excel Object used after messaging context was stopped")

    if self._internal_typeName != "Function":
        raise TypeError("Only Function-typed SpecialObjects are callable")
    wire_args = [{"arg_type": "PLACED", "value": Serializer.to_wire(a)} for a in args]
    wire_args += [
        {"arg_type": "NAMED", "name": k, "value": Serializer.to_wire(v)}
        for k, v in kwargs.items()
    ]
    req = {"method": "CALL", "name": "__call__", "args": wire_args, "caller": self._internal_id}
    env = messaging.send_request_sync(req)
    if not env.get("ok"):
        raise RuntimeError(env.get("error", {}).get("message", "CALL failed"))
    return Serializer.from_wire(env.get("result"))


def _cw__del__(self):
    """Delete proxy method for OfficeJsObject."""
    # Best-effort, avoid raising during GC
    try:
        req = {"method": "DEL", "name": "__del__", "caller": self._internal_id}
        messaging.send_request_sync(req)
    except Exception:
        pass


# ---------------- Office.js Object Proxies

_internal_officejs_names=[
    '_cw__getattr__','_cw__getitem__','_cw__setattr__','_cw__call__','_cw__del__',
    '__getattr__','__getitem__','__setattr__','__call__','__del__'
    ]
class OfficeJsObject:
    """
    Dynamic proxy class for Office.js objects.

    Provides __getattr__, __setattr__, __call__, __getitem__ to proxy
    operations to the Office.js Add-in via WebSocket.
    """

    def __init__(self, object_id: int, type_name: str):
        # Avoid recursion by using object.__setattr__
        object.__setattr__(self, "_internal_id", int(object_id))
        object.__setattr__(self, "_internal_typeName", str(type_name))
        object.__setattr__(self, "_msg_guid", messaging._guid)
        object.__setattr__(self, "_typ", 'officejs_object')
        object.__setattr__(self, "_internal_cache", {})

    def __getattr__(self, name: str):
        try:
            return _cw__getattr__(self, name)
        except Exception as e:
            tb = e.__traceback__

            while tb is not None and tb.tb_frame.f_code.co_name in _internal_officejs_names:
                tb = tb.tb_next

            raise e.with_traceback(tb) from None            

    def __getitem__(self, index):
        try:
            return _cw__getitem__(self, index)
        except Exception as e:
            tb = e.__traceback__

            while tb is not None and tb.tb_frame.f_code.co_name in _internal_officejs_names:
                tb = tb.tb_next

            raise e.with_traceback(tb) from None            

    def __setattr__(self, name: str, value):
        try:
            return _cw__setattr__(self, name, value)
        except Exception as e:
            tb = e.__traceback__

            while tb is not None and tb.tb_frame.f_code.co_name in _internal_officejs_names:
                tb = tb.tb_next

            raise e.with_traceback(tb) from None            

    def __call__(self, *args, **kwargs):
        try:
            return _cw__call__(self, *args, **kwargs)
        except Exception as e:
            tb = e.__traceback__

            while tb is not None and tb.tb_frame.f_code.co_name in _internal_officejs_names:
                tb = tb.tb_next

            raise e.with_traceback(tb) from None            

    def __del__(self):
        try:
            return _cw__del__(self)
        except Exception as e:
            tb = e.__traceback__

            while tb is not None and tb.tb_frame.f_code.co_name in _internal_officejs_names:
                tb = tb.tb_next

            raise e.with_traceback(tb) from None            

    def __repr__(self):
        return f"<OfficeJsObject {self._internal_typeName} id={self._internal_id}>"


class OfficeJsArray(list):
    """Specialized proxy for arrays returned from Office.js."""

    def __init__(self, object_id: int):
        super().__init__()
        # Avoid recursion by using object.__setattr__
        object.__setattr__(self, "_internal_id", int(object_id) if object_id else 0)
        object.__setattr__(self, "_internal_typeName", "Array")
        object.__setattr__(self, "_msg_guid", messaging._guid)
        object.__setattr__(self, "_typ", 'officejs_array')
        object.__setattr__(self, "_internal_cache", {})

    def __getattr__(self, name: str):
        try:
            return _cw__getattr__(self, name)
        except Exception as e:
            tb = e.__traceback__

            while tb is not None and tb.tb_frame.f_code.co_name in _internal_officejs_names:
                tb = tb.tb_next

            raise e.with_traceback(tb) from None            

    def __setattr__(self, name: str, value):
        raise AttributeError("Cannot set attributes on OfficeJsArray")

    def __call__(self, *args, **kwargs):
        try:
            return _cw__call__(self, *args, **kwargs)
        except Exception as e:
            tb = e.__traceback__

            while tb is not None and tb.tb_frame.f_code.co_name in _internal_officejs_names:
                tb = tb.tb_next

            raise e.with_traceback(tb) from None            

    def __del__(self):
        try:
            return _cw__del__(self)
        except Exception as e:
            tb = e.__traceback__

            while tb is not None and tb.tb_frame.f_code.co_name in _internal_officejs_names:
                tb = tb.tb_next

            raise e.with_traceback(tb) from None            

    def __repr__(self):
        return f"<OfficeJsArray id={self._internal_id} len={len(self)}>"


class OfficeJsDict(dict):
    """Specialized proxy for dictionaries returned from Office.js."""

    def __init__(self, object_id: int):
        super().__init__()
        # Avoid recursion by using object.__setattr__
        object.__setattr__(self, "_internal_id", int(object_id) if object_id else 0)
        object.__setattr__(self, "_internal_typeName", "Dict")
        object.__setattr__(self, "_msg_guid", messaging._guid)
        object.__setattr__(self, "_typ", 'officejs_dict')
        object.__setattr__(self, "_internal_cache", {})

    def __getattr__(self, name: str):
        if name in self:
            return self[name]
        try:
            return _cw__getattr__(self, name)
        except Exception as e:
            tb = e.__traceback__

            while tb is not None and tb.tb_frame.f_code.co_name in _internal_officejs_names:
                tb = tb.tb_next

            raise e.with_traceback(tb) from None            

    def __setattr__(self, name: str, value):
        if name in self:
            self[name] = value
            return
        raise AttributeError("Cannot set attributes on OfficeJsDict")

    def __call__(self, *args, **kwargs):
        try:
            return _cw__call__(self, *args, **kwargs)
        except Exception as e:
            tb = e.__traceback__

            while tb is not None and tb.tb_frame.f_code.co_name in _internal_officejs_names:
                tb = tb.tb_next

            raise e.with_traceback(tb) from None            

    def __del__(self):
        try:
            return _cw__del__(self)
        except Exception as e:
            tb = e.__traceback__

            while tb is not None and tb.tb_frame.f_code.co_name in _internal_officejs_names:
                tb = tb.tb_next

            raise e.with_traceback(tb) from None            

    def __repr__(self):
        return f"<OfficeJsDict id={self._internal_id} keys={list(self.keys())}>"


# ---------------- Bootstrap
messaging = Messaging()

# Global Context and Excel handle (id 0 & 1)
# These are the internal proxies used by the xpycode module
Context = OfficeJsObject(object_id=0, type_name="RequestContext")
Excel = OfficeJsObject(object_id=1, type_name="Excel")
GetSetting=OfficeJsObject(object_id=2, type_name="Function")
Union=OfficeJsObject(object_id=3, type_name="Function")
Intersect=OfficeJsObject(object_id=4, type_name="Function")