/**
 * XPyCode Office Tools - Helper functions for ID-based object tracking
 * This file provides utilities for Excel object resolution and tree generation
 */

import { getPlatformInfo } from './index.js'; 

/**
	* Retrieves an Excel object or collection based on its type and ID.
	* 
	* @param {Excel.RequestContext} context - The Excel RequestContext.
	* @param {string} typeName - The type of object to retrieve.
	* @param {string} id - The ID of the object, or the composite ID for collections ("typeName|parentId").
	* @returns {Promise<OfficeExtension.ClientObject | null>} The found object or null if not found.
	*/
export async function getObjectByType(context, typeName, id) {
	// Helper to extract parent ID from composite key (e.g., "ChartCollection|Sheet1" -> "Sheet1")
	// If the ID is not composite (legacy calls), we assume it is the parent ID itself.
	const getParentId = (fullId) => {
		if (fullId.includes('|')) {
			return fullId.split('|')[1];
		}
		return fullId;
	};

	switch (typeName) {
		// --- 1. The Root Object ---
		case 'Workbook':
			return context.workbook;

		// --- 2. Global Objects (Direct Access) ---
		case 'Worksheet':
			return context.workbook.worksheets.getItem(id);

		case 'Binding':
			return context.workbook.bindings.getItem(id);

		case 'Table':
			return context.workbook.tables.getItem(id);

		// --- 3. Sheet-Scoped Objects (Deep Search) ---
		case 'Chart':
		case 'Shape':
			return await findObjectOnAnySheet(context, typeName, id);

		// --- 4. Collections (Composite ID Resolution) ---
		case 'WorksheetCollection':
			return context.workbook.worksheets;

		case 'BindingCollection':
			return context.workbook.bindings;

		case 'SettingCollection':
			return context.workbook.settings;

		case 'CommentCollection':
			return context.workbook.comments;

		case 'LinkedEntityDataDomainCollection':
			if (context.workbook.linkedEntityDataDomains) {
				return context.workbook.linkedEntityDataDomains;
			}
			window.logToServer('WARNING', "LinkedEntityDataDomains not supported on this version.");
			return null;

		case 'TableCollection':
			{
				const parentId = getParentId(id);
				if (parentId === '-1') {
					return context.workbook.tables;
				} else {
					const sheet = context.workbook.worksheets.getItem(parentId);
					return sheet.tables;
				}
			}

		case 'ChartCollection':
			{
				const parentId = getParentId(id);
				if (parentId === '-1') {
					window.logToServer('WARNING', "ChartCollection cannot be retrieved from Workbook parent directly.");
					return null;
				} else {
					const sheet = context.workbook.worksheets.getItem(parentId);
					return sheet.charts;
				}
			}

		case 'ShapeCollection':
			{
				const parentId = getParentId(id);
				if (parentId === '-1') {
					window.logToServer('WARNING', "ShapeCollection cannot be retrieved from Workbook parent directly.");
					return null;
				} else {
					const sheet = context.workbook.worksheets.getItem(parentId);
					return sheet.shapes;
				}
			}

		default:
			throw new Error(`Type ${typeName} is not supported.`);
	}
}

/**
	* Retrieves the ID of an Excel object or the composite ID for a collection.
	* 
	* @param {Excel.RequestContext} context - The Excel RequestContext.
	* @param {OfficeExtension.ClientObject} object - The Excel object or collection.
	* @param {string} typeName - The type of the object.
	* @returns {Promise<string>} The ID of the object, or 'typeName|parentId' for collections.
	*/
export async function getIdByType(context, object, typeName) {
	switch (typeName) {
		case 'Workbook':
			return '-1';

		case 'Worksheet':
		case 'Binding':
		case 'Table':
		case 'Chart':
		case 'Shape':
			object.load("id");
			await context.sync();
			return object.id;

		// --- Global Collections ---
		case 'WorksheetCollection':
			return 'WorksheetCollection|-1';
			
		case 'BindingCollection':
			return 'BindingCollection|-1';

		case 'SettingCollection':
			return 'SettingCollection|-1';

		case 'CommentCollection':
			return 'CommentCollection|-1';

		case 'LinkedEntityDataDomainCollection':
			return 'LinkedEntityDataDomainCollection|-1';

		// --- Ambiguous/Sheet-Scoped Collections ---
		case 'TableCollection':
			// Default to Workbook scope if we can't determine otherwise easily
			return 'TableCollection|-1';

		case 'ChartCollection':
			object.load("items");
			await context.sync();
			if (object.items.length > 0) {
				const first = object.items[0];
				const sheet = first.worksheet;
				sheet.load("id");
				await context.sync();
				return `ChartCollection|${sheet.id}`;
			} else {
				throw new Error("Cannot determine parent ID for an empty ChartCollection.");
			}

		case 'ShapeCollection':
			object.load("items");
			await context.sync();
			if (object.items.length > 0) {
				const first = object.items[0];
				const sheet = first.worksheet;
				sheet.load("id");
				await context.sync();
				return `ShapeCollection|${sheet.id}`;
			} else {
				throw new Error("Cannot determine parent ID for an empty ShapeCollection.");
			}

		default:
			throw new Error(`Type ${typeName} is not supported.`);
	}
}

/**
	* Generates a dictionary tree of all supported existing objects in the workbook.
	* Structure: { type, id, name, children: [] }
	* Collections use their property name (e.g., 'tables', 'worksheets') as the name.
	* IDs for collections are 'TypeName|ParentID'.
	* 
	* @param {Excel.RequestContext} context 
	* @returns {Promise<Object>} The root Workbook node with its full hierarchy.
	*/
export async function getWorkbookTree(context) {
	const platformInfo = getPlatformInfo();
	const wb = context.workbook;
	wb.load("name");
	await context.sync();

	// Initialize Root
	const root = {
		type: 'Workbook',
		id: '-1',
		name: wb.name,
		children: []
	};

	// 1. Prepare Global Collections
	const worksheets = wb.worksheets;
	const bindings = wb.bindings;

	worksheets.load("items/name, items/id");
	bindings.load("items/id, items/type");

	// Check for capability
	let hasLinkedData = false;
	if (!platformInfo.isOnline) {
		hasLinkedData = !!wb.linkedEntityDataDomains;
	}
	await context.sync();

	// 2. Add Level 1 Nodes (Collections & Globals)
		
	// WorksheetCollection -> 'worksheets'
	const wsCollectionNode = {
		type: 'WorksheetCollection',
		id: 'WorksheetCollection|-1',
		name: 'worksheets',
		children: []
	};
	root.children.push(wsCollectionNode);

	// BindingCollection -> 'bindings'
	const bindingCollectionNode = {
		type: 'BindingCollection',
		id: 'BindingCollection|-1',
		name: 'bindings',
		children: []
	};
	root.children.push(bindingCollectionNode);

	// SettingCollection -> 'settings'
	root.children.push({ type: 'SettingCollection', id: 'SettingCollection|-1', name: 'settings', children: [] });

	// CommentCollection -> 'comments'
	root.children.push({ type: 'CommentCollection', id: 'CommentCollection|-1', name: 'comments', children: [] });

	// LinkedEntityDataDomainCollection -> 'linkedEntityDataDomains'
	if (hasLinkedData) {
		root.children.push({ type: 'LinkedEntityDataDomainCollection', id: 'LinkedEntityDataDomainCollection|-1', name: 'linkedEntityDataDomains', children: [] });
	}

	// Bindings (Children of BindingCollection)
	bindings.items.forEach(b => {
		bindingCollectionNode.children.push({
			type: 'Binding',
			id: b.id,
			name: b.id,
			children: []
		});
	});

	// 3. Load Sheet Contents (Batch Operation)
	worksheets.items.forEach(ws => {
		ws.tables.load("items/id, items/name");
		ws.charts.load("items/id, items/name");
		ws.shapes.load("items/id, items/name");
	});

	await context.sync();

	// 4. Build Sheet Hierarchies
	worksheets.items.forEach(ws => {
		const wsNode = {
			type: 'Worksheet',
			id: ws.id,
			name: ws.name,
			children: []
		};

		// TableCollection -> 'tables'
		const tableCollNode = {
			type: 'TableCollection',
			id: `TableCollection|${ws.id}`,
			name: 'tables',
			children: []
		};
		ws.tables.items.forEach(t => {
			tableCollNode.children.push({
				type: 'Table',
				id: t.id,
				name: t.name,
				children: []
			});
		});
		wsNode.children.push(tableCollNode);

		// ChartCollection -> 'charts'
		const chartCollNode = {
			type: 'ChartCollection',
			id: `ChartCollection|${ws.id}`,
			name: 'charts',
			children: []
		};
		ws.charts.items.forEach(c => {
			chartCollNode.children.push({
				type: 'Chart',
				id: c.id,
				name: c.name,
				children: []
			});
		});
		wsNode.children.push(chartCollNode);

		// ShapeCollection -> 'shapes'
		const shapeCollNode = {
			type: 'ShapeCollection',
			id: `ShapeCollection|${ws.id}`,
			name: 'shapes',
			children: []
		};
		ws.shapes.items.forEach(s => {
			if(!(chartCollNode.children.find(el=>el.id==s.id))) {
				shapeCollNode.children.push({
					type: 'Shape',
					id: s.id,
					name: s.name,
					children: []
				});
			}
		});
		wsNode.children.push(shapeCollNode);

		// Add populated Sheet node to SheetCollection
		wsCollectionNode.children.push(wsNode);
	});

	return root;
}

/**
	* Returns the full dictionary of supported events for all types.
	* @returns {Object} Dictionary where keys are type names and values are lists of event metadata.
	*/
export function getEventsDictionary() {
	return {
		'Workbook': [
			{ eventName: 'onActivated', eventArgsType: 'Excel.WorkbookActivatedEventArgs', eventType: 'WorkbookActivated' },
			{ eventName: 'onAutoSaveSettingChanged', eventArgsType: 'Excel.WorkbookAutoSaveSettingChangedEventArgs', eventType: 'WorkbookAutoSaveSettingChanged' },
			{ eventName: 'onSelectionChanged', eventArgsType: 'Excel.SelectionChangedEventArgs', eventType: 'WorkbookSelectionChanged' }
		],
		'Worksheet': [
			{ eventName: 'onActivated', eventArgsType: 'Excel.WorksheetActivatedEventArgs', eventType: 'WorksheetActivated' },
			{ eventName: 'onDeactivated', eventArgsType: 'Excel.WorksheetDeactivatedEventArgs', eventType: 'WorksheetDeactivated' },
			{ eventName: 'onCalculated', eventArgsType: 'Excel.WorksheetCalculatedEventArgs', eventType: 'WorksheetCalculated' },
			{ eventName: 'onChanged', eventArgsType: 'Excel.WorksheetChangedEventArgs', eventType: 'WorksheetChanged' },
			{ eventName: 'onColumnSorted', eventArgsType: 'Excel.WorksheetColumnSortedEventArgs', eventType: 'WorksheetColumnSorted' },
			{ eventName: 'onFormatChanged', eventArgsType: 'Excel.WorksheetFormatChangedEventArgs', eventType: 'WorksheetFormatChanged' },
			{ eventName: 'onFormulaChanged', eventArgsType: 'Excel.WorksheetFormulaChangedEventArgs', eventType: 'WorksheetFormulaChanged' },
			{ eventName: 'onRowHiddenChanged', eventArgsType: 'Excel.WorksheetRowHiddenChangedEventArgs', eventType: 'WorksheetRowHiddenChanged' },
			{ eventName: 'onRowSorted', eventArgsType: 'Excel.WorksheetRowSortedEventArgs', eventType: 'WorksheetRowSorted' },
			{ eventName: 'onSelectionChanged', eventArgsType: 'Excel.WorksheetSelectionChangedEventArgs', eventType: 'WorksheetSelectionChanged' },
			{ eventName: 'onSingleClicked', eventArgsType: 'Excel.WorksheetSingleClickedEventArgs', eventType: 'WorksheetSingleClicked' },
			{ eventName: 'onProtectionChanged', eventArgsType: 'Excel.WorksheetProtectionChangedEventArgs', eventType: 'WorksheetProtectionChanged' }
		],
		'WorksheetCollection': [
			{ eventName: 'onActivated', eventArgsType: 'Excel.WorksheetActivatedEventArgs', eventType: 'WorksheetActivated' },
			{ eventName: 'onAdded', eventArgsType: 'Excel.WorksheetAddedEventArgs', eventType: 'WorksheetAdded' },
			{ eventName: 'onCalculated', eventArgsType: 'Excel.WorksheetCalculatedEventArgs', eventType: 'WorksheetCalculated' },
			{ eventName: 'onChanged', eventArgsType: 'Excel.WorksheetChangedEventArgs', eventType: 'WorksheetChanged' },
			{ eventName: 'onColumnSorted', eventArgsType: 'Excel.WorksheetColumnSortedEventArgs', eventType: 'WorksheetColumnSorted' },
			{ eventName: 'onDeactivated', eventArgsType: 'Excel.WorksheetDeactivatedEventArgs', eventType: 'WorksheetDeactivated' },
			{ eventName: 'onDeleted', eventArgsType: 'Excel.WorksheetDeletedEventArgs', eventType: 'WorksheetDeleted' },
			{ eventName: 'onFormatChanged', eventArgsType: 'Excel.WorksheetFormatChangedEventArgs', eventType: 'WorksheetFormatChanged' },
			{ eventName: 'onFormulaChanged', eventArgsType: 'Excel.WorksheetFormulaChangedEventArgs', eventType: 'WorksheetFormulaChanged' },
			{ eventName: 'onMoved', eventArgsType: 'Excel.WorksheetMovedEventArgs', eventType: 'WorksheetMoved' },
			{ eventName: 'onRowHiddenChanged', eventArgsType: 'Excel.WorksheetRowHiddenChangedEventArgs', eventType: 'WorksheetRowHiddenChanged' },
			{ eventName: 'onRowSorted', eventArgsType: 'Excel.WorksheetRowSortedEventArgs', eventType: 'WorksheetRowSorted' },
			{ eventName: 'onSelectionChanged', eventArgsType: 'Excel.WorksheetSelectionChangedEventArgs', eventType: 'WorksheetSelectionChanged' },
			{ eventName: 'onSingleClicked', eventArgsType: 'Excel.WorksheetSingleClickedEventArgs', eventType: 'WorksheetSingleClicked' },
			{ eventName: 'onNameChanged', eventArgsType: 'Excel.WorksheetNameChangedEventArgs', eventType: 'WorksheetNameChanged' },
			{ eventName: 'onProtectionChanged', eventArgsType: 'Excel.WorksheetProtectionChangedEventArgs', eventType: 'WorksheetProtectionChanged' }
		],
		'Table': [
			{ eventName: 'onChanged', eventArgsType: 'Excel.TableChangedEventArgs', eventType: 'TableChanged' },
			{ eventName: 'onSelectionChanged', eventArgsType: 'Excel.TableSelectionChangedEventArgs', eventType: 'TableSelectionChanged' }
		],
		'TableCollection': [
			{ eventName: 'onAdded', eventArgsType: 'Excel.TableAddedEventArgs', eventType: 'TableAdded' },
			{ eventName: 'onChanged', eventArgsType: 'Excel.TableChangedEventArgs', eventType: 'TableChanged' },
			{ eventName: 'onDeleted', eventArgsType: 'Excel.TableDeletedEventArgs', eventType: 'TableDeleted' }
		],
		'Chart': [
			{ eventName: 'onActivated', eventArgsType: 'Excel.ChartActivatedEventArgs', eventType: 'ChartActivated' },
			{ eventName: 'onDeactivated', eventArgsType: 'Excel.ChartDeactivatedEventArgs', eventType: 'ChartDeactivated' }
		],
		'ChartCollection': [
			{ eventName: 'onActivated', eventArgsType: 'Excel.ChartActivatedEventArgs', eventType: 'ChartActivated' },
			{ eventName: 'onAdded', eventArgsType: 'Excel.ChartAddedEventArgs', eventType: 'ChartAdded' },
			{ eventName: 'onDeactivated', eventArgsType: 'Excel.ChartDeactivatedEventArgs', eventType: 'ChartDeactivated' },
			{ eventName: 'onDeleted', eventArgsType: 'Excel.ChartDeletedEventArgs', eventType: 'ChartDeleted' }
		],
		'Shape': [
			{ eventName: 'onActivated', eventArgsType: 'Excel.ShapeActivatedEventArgs', eventType: 'ShapeActivated' },
			{ eventName: 'onDeactivated', eventArgsType: 'Excel.ShapeDeactivatedEventArgs', eventType: 'ShapeDeactivated' }
		],
		'ShapeCollection': [],
		'CommentCollection': [
			{ eventName: 'onChanged', eventArgsType: 'Excel.CommentChangedEventArgs', eventType: 'CommentChanged' },
			{ eventName: 'onAdded', eventArgsType: 'Excel.CommentAddedEventArgs', eventType: 'CommentAdded' },
			{ eventName: 'onDeleted', eventArgsType: 'Excel.CommentDeletedEventArgs', eventType: 'CommentDeleted' }
		],
		'Binding': [
			{ eventName: 'onDataChanged', eventArgsType: 'Excel.BindingDataChangedEventArgs', eventType: 'BindingDataChanged' },
			{ eventName: 'onSelectionChanged', eventArgsType: 'Excel.BindingSelectionChangedEventArgs', eventType: 'BindingSelectionChanged' }
		],
		'BindingCollection': [], // BindingCollection does not expose events in standard API; children Bindings do.
		'SettingCollection': [
			{ eventName: 'onSettingsChanged', eventArgsType: 'Excel.SettingsChangedEventArgs', eventType: 'SettingsChanged' }
		]
	};
}

/**
	* Returns a list of events available for a specific Excel object type.
	* 
	* @param {string} typeName - The type of object (e.g., 'Worksheet', 'Table').
	* @returns {Array<{eventName: string, eventArgsType: string, eventType: string}>} List of event metadata.
	*/
export function getEventsByType(typeName) {
	const allEvents = getEventsDictionary();
	return allEvents[typeName] || [];
}

// --- Internal Helpers ---

export async function findObjectOnAnySheet(context, type, id) {
	const sheets = context.workbook.worksheets;
	sheets.load("items");
	await context.sync();

	const potentialItems = sheets.items.map(sheet => {
		let item;
		if (type === 'Chart') {
			item = sheet.charts.getItemOrNullObject(id);
		} else {
			item = sheet.shapes.getItemOrNullObject(id);
		}
		return { item: item };
	});

	potentialItems.forEach(entry => entry.item.load("isNullObject"));
	await context.sync();

	const foundEntry = potentialItems.find(entry => !entry.item.isNullObject);

	return foundEntry ? foundEntry.item : null;
}


