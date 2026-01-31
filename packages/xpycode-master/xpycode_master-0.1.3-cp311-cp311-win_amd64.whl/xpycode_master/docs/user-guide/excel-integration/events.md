# Excel Events

Handle Excel events with Python code to create interactive and responsive spreadsheets.

## :material-lightning-bolt: Overview

Excel events let you run Python code automatically when:

- A cell selection changes
- A worksheet is activated
- Cell values are edited
- A calculation completes
- The workbook is opened or closed
- **All events managed by [Microsoft Office.js](https://learn.microsoft.com/en-us/javascript/api/excel)** 

This enables:

- **Validation** - Check input data as it's entered
- **Automation** - Update cells automatically
- **Monitoring** - Log user actions
- **Interactivity** - Respond to user selections

## :material-cog-outline: Event Manager

Configure event handlers through the Event Manager panel:

1. Open the **Events** tab (right dock)
2. Select the workbook from the list
3. Select the object for which you want to add an event handler
4. Select the event you want to listen to on the right
5. Either:
   - Double-click to create a new handler (generates a function with the correct signature)
   - Right-click and select **Create New Handler...** to create a new function
   - Right-click and select **Assign Handler...** to select an existing function

<!-- SCREENSHOT: event-manager.png -->
<figure markdown>
  ![Event Manager](../../assets/screenshots/ide/event-manager.png){ width="600" }
  <figcaption>Event Manager for registering event handlers</figcaption>
</figure>

## :material-format-list-bulleted: Available Events

!!! info "Office.js Events"
    All Office.js events can be managed through XPyCode's Event Manager. For a complete list of available events, see the [Excel JavaScript API Events documentation](https://learn.microsoft.com/en-us/javascript/api/excel#events).


### Unregister Handler

To stop listening to an event:

1. Open the **Events** tab (right dock)
2. Select the workbook from the list
3. Select the object with the event handler you want to remove
4. Select the event you want to stop listening to on the right
5. Right-click and select **Clear Handler**

The event handler function remains in your code but is no longer triggered by the event.

## :material-arrow-right: Next Steps

<div class="grid cards" markdown>

-   :material-cube: __Excel Objects__

    ---

    Learn to work with workbooks, sheets, and ranges.

    [:octicons-arrow-right-24: Objects Guide](objects.md)

-   :material-function: __Custom Functions__

    ---

    Publish Python functions as Excel formulas.

    [:octicons-arrow-right-24: Custom Functions](custom-functions.md)

-   :material-school: __Automation Tutorial__

    ---

    Build automated workflows with events.

    [:octicons-arrow-right-24: Automation Tutorial](../../tutorials/automation.md)

</div>

---

!!! tip "Start Simple"
    Begin with simple event handlers (logging, validation) before building complex automation. Test thoroughly to avoid infinite loops.
