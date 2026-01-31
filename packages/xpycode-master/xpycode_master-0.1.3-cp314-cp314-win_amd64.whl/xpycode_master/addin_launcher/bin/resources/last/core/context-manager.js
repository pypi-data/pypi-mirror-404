// XPyCode Context Manager
// Manages Excel object references and serialization between JavaScript and Python

import { TEMPORARY_PARENT_ID } from './constants.js';
import { isPlainObject, getExcelClassName, trackObject, untrackObject, transferToAnotherContext } from './utils.js';
import { getSetting } from '../settings/index.js'; 
/**
 * Context Manager class
 * Handles tracking of Excel objects and serialization/deserialization of data between JS and Python
 */
export class ContextManager {
    constructor() {
        this.liveInstances = new Map(); // id -> { instance, resolve, todelete, parent }
        this.nextId = 200; // to have 200 reserved ids
    }

    async getUnion(...items) {
        if (items.length === 0) return null;
        if (items.length === 1) return items[0];

        const context = items[0].context;

        // Load address + worksheet identity
        for (const it of items) {
            it.load(["address", "worksheet/name"]);
        }
        await context.sync();

        const firstSheet = items[0].worksheet;
        const firstSheetName = items[0].worksheet.name;

        // Ensure same worksheet
        for (const it of items) {
            if (it.worksheet.name !== firstSheetName) {
                throw new Error(
                    `Cannot union across worksheets. Expected "${firstSheetName}", got "${it.worksheet.name}".`
                );
            }
        }

        // ---- Deduplicate addresses (simple "no doublons" pass) ----
        // Notes:
        // - We normalize to uppercase and remove $ to treat "A1" and "$A$1" as the same.
        // - We don't attempt full geometric containment elimination (complex with multi-areas),
        //   but we do remove exact duplicates.
        const normalize = (addr) => addr.replace(/\$/g, "").trim().toUpperCase();

        const seen = new Set();
        const uniqueAddresses = [];

        for (const it of items) {
            // RangeAreas.address can be something like "Sheet1!A1:A3,Sheet1!C1:C3"
            // Worksheet.getRanges accepts addresses without sheet prefix, so strip "SheetName!".
            const parts = it.address.split(",").map(s => s.trim());

            for (let part of parts) {
                // Remove worksheet prefix if present (e.g., "Sheet1!A1:A3")
                const bang = part.indexOf("!");
                if (bang !== -1) part = part.slice(bang + 1);

                const key = normalize(part);
                if (!seen.has(key)) {
                    seen.add(key);
                    uniqueAddresses.push(part);
                }
            }
        }

        if (uniqueAddresses.length === 0) return null;

        // If only one area, return a Range (not RangeAreas)
        if (uniqueAddresses.length === 1) {
            return firstSheet.getRange(uniqueAddresses[0]);
        }

        return firstSheet.getRanges(uniqueAddresses.join(","));
    }



    _getIntersection(...ranges) {
        if (ranges.length === 0) {
            return null;
        }
        if (ranges.length === 1) {
            return ranges[0];
        }
        if (ranges.length === 2) {
            let r1 = ranges[0];
            let r2 = ranges[1];

            if (r1._className === 'RangeAreas') {
                const rt = r1;
                r1 = r2;
                r2 = rt;
            }
            if (r2._className === 'RangeAreas') {
                try {
                    res = r2.getIntersection(r1);
                } catch (e) {
                    return null;
                }
                if (res.areas.getCount() === 0) {
                    return null;
                }
                else if (res.areas.getCount() === 1) {
                    return res.areas.getItemAt(0);
                }
                else { return res; }
            }
            try {
                return r1.getIntersection(r2);
            }
            catch (e) {
                return null;
            }
        }
        let r1 = ranges[0];
        let r2 = this.getIntersection(...ranges.slice(1));
        if (!r2) {
            return null;

        }
        return this.getIntersection(r1, r2);
    }

    async getIntersection(...ranges) {
        let res = this._getIntersection(...ranges);
        if (res) {
            try {
                res.load('address');
                await res.context.sync();
                if (!res.address) { return null; }
                return res;
            } catch (e) {
                return null;
            }
            return res;
        }
        return null;
    }




    _getObjectFromRegistry(id, context) {
        if (id === 0) { return context; }
        if (id === 1) { return Excel; }
        if (id === 2) { return getSetting; }
        if (id === 3) { return this.getUnion; }
        if (id === 4) { return this.getIntersection.bind(this); }

        const rec = this.liveInstances.get(id);
        if (!rec) throw new Error(`Unknown object id ${id}`);
        if (rec.resolve) {
            return rec.resolve(context);
        }
        return rec.instance;
    }

    _getParentObjectFromRegistry(id, context) {
        if (id === 0) { return null; }
        if (id === 1) { return null; }
        if (id === 2) { return null; }
        if (id === 3) { return null; }
        if (id === 4) { return null; }

        const rec = this.liveInstances.get(id);
        if (!rec) throw new Error(`Unknown object id ${id}`);
        if (rec.parent === TEMPORARY_PARENT_ID) return null;
        const parent = this._getObjectFromRegistry(rec.parent, context);
        return parent;
    }

    _getParentContextFromRegistry(id, context) {
        if (id === 0) { return null; }
        if (id === 1) { return null; }
        if (id === 2) { return null; }
        if (id === 3) { return null; }
        if (id === 4) { return null; }

        const rec = this.liveInstances.get(id);
        if (!rec) throw new Error(`Unknown object id ${id}`);
        if (rec.parent === TEMPORARY_PARENT_ID) return null;
        const parent = this._getObjectFromRegistry(rec.parent, context);
        if (!(parent?.context)) {
            return this._getParentContextFromRegistry(rec.parent, context);
        }
        return parent.context
        return parent;
    }




    registerInstance(obj, parentId, childName, tryTrack = true) {
        const id = this.nextId++;

        try {
            if (tryTrack) {
                trackObject(obj);
            }
            this.liveInstances.set(id, { instance: obj, resolve: null, todelete: false, parent: parentId });
        } catch (e) {
            // If parentId indicates a temporary/event object, register directly without lazy resolution
            // This allows "temporary" or "event" objects to be tracked without a full object model path
            if (parentId === TEMPORARY_PARENT_ID) {
                this.liveInstances.set(id, { instance: obj, resolve: null, todelete: false, parent: parentId });
            } else {
                this.liveInstances.set(id, {
                    instance: null,
                    resolve: (context) => {
                        let sobj = this._getObjectFromRegistry(parentId, context);
                        if (!sobj) throw new Error(`Parent object id ${parentId} not found for lazy child ${childName}`);
                        try { sobj.load(childName); } catch (e) { }
                        let res = sobj[childName];
                        try { res = res.bind(sobj); } catch (_) { }
                        //context?.sync().then(() => null);
                        return res;
                    },
                    todelete: false, parent: parentId
                });
            }
        }

        return id;
    }

    unregisterInstance(id, only_todelete = false) {
        if (id === 0) return;
        const rec = this.liveInstances.get(id);
        if (!rec) return;
		
        if (only_todelete && !rec.todelete) {
            return;
        }

        rec.todelete = true;
        for (const [cid, crec] of this.liveInstances.entries()) {
            if (crec.parent === id) {
                return;
            }
        }
        try {
            untrackObject(rec.instance);
        } catch (e) {
        }
        this.liveInstances.delete(id);
        this.unregisterInstance(rec.parent, true);
    }

    ensureContext() {
        this.liveInstances.set(0, { instance: {}, resolver: null, todelete: false, parent: -1 });
        this.liveInstances.set(1, { instance: Excel, resolver: null, todelete: false, parent: -1 });
    }

    toWire(value, callerId, nameForChild) {

        if (value === null || value === undefined) return { type: 'Null', value: null, isSpec: false };
        if (typeof value === 'boolean') return { type: 'Bool', value: value, isSpec: false };
        if (typeof value === 'number') {
            if (Number.isInteger(value)) return { type: 'Int', value: value, isSpec: false };
            return { type: 'Float', value: value, isSpec: false };
        }
        if (typeof value === 'string') return { type: 'String', value: value, isSpec: false };
        if (value instanceof Date) return { type: 'Date', value: value.toISOString(), isSpec: false };
        if (value instanceof Uint8Array) {
            const b64 = btoa(String.fromCharCode(...value));
            return { type: 'Bytes', value: b64, isSpec: false };
        }
        if (value instanceof ArrayBuffer) {
            const view = new Uint8Array(value);
            const b64 = btoa(String.fromCharCode(...view));
            return { type: 'Bytes', value: b64, isSpec: false };
        }
        if (Array.isArray(value)) {
            const ida = this.registerInstance(value, callerId, nameForChild, false);
            return { type: 'Array', value: value.map(v => this.toWire(v, callerId, nameForChild)), isSpec: false, id: ida };
        }
        if (value && typeof value === 'object' && isPlainObject(value)) {
            const ido = this.registerInstance(value, callerId, nameForChild, false);
            return { type: 'Dict', value: Object.fromEntries(Object.entries(value).map(([k, v]) => [k, this.toWire(v, callerId, nameForChild)])), isSpec: false, id: ido };
        }
        if (value && typeof value === 'object' && !isPlainObject(value)) {
            const id = this.registerInstance(value, callerId, nameForChild);
            const typeName = getExcelClassName(value);
            return { type: typeName, value: id, isSpec: true };
        }
        if (typeof value === 'function') {
            const id = this.registerInstance(value, callerId, nameForChild);
            return { type: 'Function', value: id, isSpec: true };
        }

        return { type: 'String', value: String(value), isSpec: false };
    }

    fromWire(obj, context) {
        if (!obj || typeof obj !== 'object') return obj;
        const { type, value, isSpec } = obj;

        switch (type) {
            case 'Null': return null;
            case 'Bool': return !!value;
            case 'Int': return Number(value);
            case 'Float': return Number(value);
            case 'String': return String(value);
            case 'Date': return new Date(value);
            case 'Bytes': {
                const str = atob(value || '');
                const arr = new Uint8Array(str.length);
                for (let i = 0; i < str.length; i++) arr[i] = str.charCodeAt(i);
                return arr;
            }
            case 'Array': return (value || []).map(v => this.fromWire(v, context));
            case 'Dict': {
                const out = {};
                for (const [k, v] of Object.entries(value || {})) out[k] = this.fromWire(v, context);
                return out;
            }
            case 'Python_Function': {
                // Return a JavaScript function that invokes the Python callable
                const callableId = value;
                const ctxMgr = this;
                
                // Note: Messaging instance is accessed via window._xpycode_messaging
                // This is set during initialization in taskpane.js
                // TODO: Pass messaging instance via dependency injection when refactoring
                return async function(...args) {
                    // Get the global messaging instance (set when Messaging is initialized)
                    const messaging = window._xpycode_messaging;
                    if (!messaging) {
                        throw new Error('Messaging not available for Python_Function call. Ensure window._xpycode_messaging is set during initialization.');
                    }
                    
                    // Send request encapsulated in Excel.run
                    return Excel.run(async (excelContext) => {
                        // Bundle arguments serialized with toWire
                        const serializedArgs = args.map(arg => ctxMgr.toWire(arg, 0, null));
                        
                        const request = {
                            type: 'python_function_call',
                            callable_id: callableId,
                            args: serializedArgs
                        };
                        
                        // Send request through messaging and wait for response
                        const response = await messaging.sendRequest(request);
                        
                        if (response.ok) {
                            return ctxMgr.fromWire(response.result, excelContext);
                        } else {
                            const errorMsg = response?.error?.message || 'Remote error';
                            throw new Error(errorMsg);
                        }
                    });
                };
            }
            default: {
                if (isSpec) {
                    return this._getObjectFromRegistry(value, context);
                } else {
                    return String(value);
                }
            }
        }
    }

    _buildReturn(value, callerId, nameForChild = null) {
        const prim = this.toWire(value, callerId, nameForChild);
        return prim;
    }

    async processMessage(msg) {
        const { requestId, method, name, args = [], value, caller } = msg;

        return Excel.run(async (context) => {
            this.liveInstances.get(0).instance = context;

            const targetObj = this._getObjectFromRegistry(caller, context);
            if (!targetObj) {
                return { ok: false, error: { message: `Unknown caller id ${caller}` } };
            }

            try {
                if (method === 'GET') {
                    let ret;
                    if (name in targetObj) {
                        try {
                            targetObj.load(name);
                            await targetObj.context.sync();
                        } catch (e) {
                            // ignore load errors
                        }
                        ret = targetObj[name];
                        // Bind functions to the target object to preserve 'this' context
                        // when called via CALL method
                        if (typeof ret === 'function') {
                            //ret = ret.bind(targetObj);
                        }
                        else {
                            //await context.sync();
                        }

                    } else {
                        throw new Error(`Attribute ${name} not found on OfficeJs object`);
                    }
                    const result = this._buildReturn(ret, caller, name);
                    //await ret?.context?.sync();
                    return { ok: true, result };
                }

                if (method === 'GETITEM') {
                    let ret;
                    const numIndex = Number(name);
                    if (!Number.isNaN(numIndex) && Number.isInteger(numIndex)) {
                        if (Array.isArray(targetObj)) {
                            ret = targetObj[numIndex];
                            //await context.sync();
                        } else {
                            throw new Error(`Object is not an array`);
                        }
                    } else {
                        throw new Error(`Invalid index ${name} for GETITEM on OfficeJs object`);
                    }
                    const result = this._buildReturn(ret, caller, name);
                    //await ret?.context?.sync();
                    return { ok: true, result };
                }

                if (method === 'SET') {
                    if (!(name in targetObj)) throw new Error(`Attribute ${name} not found on OfficeJs object`);
                    const des = this.fromWire(value, context);
                    /*
                    try {
                        targetObj.load(name);
                        await targetObj.context.sync();
                    } catch (e) {
                        // ignore load errors
                    }
                    */
                    targetObj[name] = des;
                    await targetObj?.context?.sync();
                    return { ok: true, result: { type: 'Null', value: null } };
                }

                if (method === 'CALL') {
                    if (typeof targetObj !== 'function') throw new Error('Caller is not Function');

                    //const parent = this._getParentObjectFromRegistry(caller, context);
                    //const callingContext = parent?.context ?? context;

                    const callingContext = this._getParentContextFromRegistry(caller, context) || context;
					
                    let placed = [];
                    const named = {};
                    for (const a of args) {
                        const val = this.fromWire(a.value, callingContext);
                        if (a.arg_type === 'PLACED') placed.push(val);
                        else if (a.arg_type === 'NAMED') named[a.name] = val;
                    }

                    if (Object.keys(named).length) { placed.push(named); }
                    placed = await transferToAnotherContext(callingContext, placed);	
                    const ret = await Promise.resolve(targetObj(...placed));
                    const result = this._buildReturn(ret, TEMPORARY_PARENT_ID, name);
                    //await context.sync();
                    //await callingContext.sync();
                    //await ret?.context?.sync();
                    return { ok: true, result };
                }

                if (method === 'DEL') {
                    this.unregisterInstance(caller);
                    //await context.sync();
                    //await targetObj?.context?.sync();
                    return { ok: true, result: { type: 'Null', value: null } };
                }

                return { ok: false, error: { message: `Unknown method ${method}` } };
            } catch (e) {
                const errorMsg = e.stack || e.message || String(e);
                window.logToServer('ERROR', `Error processing message ${method} ${name} from caller ${caller}: ${errorMsg}`);
                return { ok: false, error: { message: e.message || String(e) } };
            }
        });
    }
}
