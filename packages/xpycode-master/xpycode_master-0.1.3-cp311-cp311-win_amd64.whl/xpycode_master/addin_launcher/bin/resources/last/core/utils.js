// XPyCode Utility Functions
// Common utility functions used across the add-in

/**
 * Generate a unique ID
 * @returns {string} A unique identifier
 */
export const genId = () => Math.random().toString(36).slice(2) + Date.now().toString(36);

/**
 * Check if an object is a plain JavaScript object (not an Excel object or other special type)
 * @param {*} obj - The value to check
 * @returns {boolean} True if the object is a plain object
 */
export function isPlainObject(obj) {
    if (typeof obj !== 'object' || obj === null) return false;
    const proto = Object.getPrototypeOf(obj);
    return proto === Object.prototype || proto === null;
}

/**
 * Get the Excel class name of an object
 * @param {*} obj - The object to get the class name for
 * @returns {string} The class name
 */
export function getExcelClassName(obj) {
    if (!obj || typeof obj !== 'object') return typeof obj;
    try {
        return obj._className;
    } catch (_) { }
    return obj?.constructor?.name ?? 'Unknown Object';
}

/**
 * Track an Excel object for memory management
 * @param {*} obj - The Excel object to track
 */
export function trackObject(obj) {
    if (typeof obj.track === 'function') {
        obj.track();
    } else {
        obj.context.trackedObjects.add(obj);
    }
}

/**
 * Untrack an Excel object
 * @param {*} obj - The Excel object to untrack
 */
export function untrackObject(obj) {
    if (typeof obj.untrack === 'function') {
        obj.untrack();
    } else {
        obj.context.trackedObjects.remove(obj);
    }
}

/**
 * Try to load properties on an Excel object
 * @param {*} target - The Excel object
 * @param {string} props - Properties to load
 */
export async function tryLoad(target, props) {
    try { target.load(props); await target.context.sync(); } 
    catch (e) { 
		}
}

/**
 * Transfer an Excel object to another context
 * @param {*} ctx - The target context
 * @param {*} obj - The object to transfer
 * @returns {*} The transferred object
 */
export async function transferToAnotherContext(ctx, obj) {
    if (Array.isArray(obj)) {
        let repliedArray = [];
        for (let v of obj) {
            repliedArray.push(await transferToAnotherContext(ctx, v));
        }
        return repliedArray;
    }
	
	if (obj && typeof obj === 'object' && isPlainObject(obj)) {
        let repliedObject = {};
        for (let [k, v] of Object.entries(obj)) {
            repliedObject[k] = await transferToAnotherContext(ctx, v);
        }
        return repliedObject;
    }

    try {
        switch (obj._className) {
            case 'Worksheet':
                await tryLoad(obj, 'id,name');
                if (obj.id) return ctx.workbook.worksheets.getItem(obj.id);
                return ctx.workbook.worksheets.getItem(obj.name);

            case 'Range': {
                await tryLoad(obj, 'address, worksheet/id, worksheet/name');
                const ws = obj.worksheet.id
                    ? ctx.workbook.worksheets.getItem(obj.worksheet.id)
                    : ctx.workbook.worksheets.getItem(obj.worksheet.name);
                let addr = obj.address; // to ensure address is loaded
                return ws.getRange(addr);
            }

            case 'Table':
                await tryLoad(obj, 'id,name');
                if (obj.id) return ctx.workbook.tables.getItem(obj.id);
                return ctx.workbook.tables.getItem(obj.name);

            case 'Chart': {
                await tryLoad(obj, 'id, worksheet/id, worksheet/name');
                const ws = obj.worksheet && obj.worksheet.id
                    ? ctx.workbook.worksheets.getItem(obj.worksheet.id)
                    : obj.worksheet && obj.worksheet.name
                    ? ctx.workbook.worksheets.getItem(obj.worksheet.name)
                    : null;
                if (!ws) throw new Error('Chart worksheet not found');
                return ws.charts.getItem(obj.id);
            }

            case 'RangeAreas': 
                await tryLoad(obj, 'address, worksheet/id, worksheet/name');
                {
                    const ws = obj.worksheet.id
                        ? ctx.workbook.worksheets.getItem(obj.worksheet.id)
                        : ctx.workbook.worksheets.getItem(obj.worksheet.name);
                    return ws.getRanges(obj.address);
                }
            case 'PivotTable':
                await tryLoad(obj, 'name');
                return ctx.workbook.pivotTables.getItem(obj.name);
            case 'Slicer':
                await tryLoad(obj, 'name');
                return ctx.workbook.slicers.getItem(obj.name);
            case 'PivotHierarchy':
                await tryLoad(obj, 'name');
                return ctx.workbook.pivotHierarchies.getItem(obj.name);
            case 'PivotField':
                await tryLoad(obj, 'name');
                return ctx.workbook.pivotFields.getItem(obj.name);
            case 'ConditionalFormat':
                await tryLoad(obj, 'id');
                return ctx.workbook.conditionalFormats.getItem(obj.id);
            case 'FormatCondition':
                await tryLoad(obj, 'id');
                return ctx.workbook.conditionalFormats.getItem(obj.id);
            case 'TableColumn':
                await tryLoad(obj, 'id,table/id,table/name');
                {
                    const table = obj.table.id
                        ? ctx.workbook.tables.getItem(obj.table.id)
                        : ctx.workbook.tables.getItem(obj.table.name);
                    return table.columns.getItem(obj.id);
                }
            case 'TableRow':
                await tryLoad(obj, 'index,table/id,table/name');
                {
                    const table = obj.table.id
                        ? ctx.workbook.tables.getItem(obj.table.id)
                        : ctx.workbook.tables.getItem(obj.table.name);
                    return table.rows.getItemAt(obj.index);
                }
            case 'TableSort':
                await tryLoad(obj, 'table/id,table/name');
                {
                    const table = obj.table.id
                        ? ctx.workbook.tables.getItem(obj.table.id)
                        : ctx.workbook.tables.getItem(obj.table.name);
                    return table.sort;
                }
            case 'ChartArea':
                await tryLoad(obj, 'chart/id,chart/worksheet/id,chart/worksheet/name');
                {
                    const ws = obj.chart.worksheet.id
                        ? ctx.workbook.worksheets.getItem(obj.chart.worksheet.id)
                        : ctx.workbook.worksheets.getItem(obj.chart.worksheet.name);
                    const chart = ws.charts.getItem(obj.chart.id);
                    return chart.area;
                }
            case 'ChartTitle':
                await tryLoad(obj, 'chart/id,chart/worksheet/id,chart/worksheet/name');
                {
                    const ws = obj.chart.worksheet.id
                        ? ctx.workbook.worksheets.getItem(obj.chart.worksheet.id)
                        : ctx.workbook.worksheets.getItem(obj.chart.worksheet.name);
                    const chart = ws.charts.getItem(obj.chart.id);
                    return chart.title;
                }


            case 'NamedItem':
                await tryLoad(obj, 'name');
                return ctx.workbook.names.getItem(obj.name).getRange();

            default:
                throw new Error(`Unsupported ref kind: ${obj._className}`);
        }
    } catch (e) {
        window.logToServer('DEBUG', `Error transferring object to another context: ${e.message || String(e)}`);
        return obj;
    }
}
