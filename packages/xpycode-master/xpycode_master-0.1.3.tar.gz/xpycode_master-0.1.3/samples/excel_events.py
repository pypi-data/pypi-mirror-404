import xpycode

def on_startlivebinding_onselectionchanged(event_args: xpycode.Excel.BindingSelectionChangedEventArgs):
    """
    Handler for Binding[StartLiveBinding].onSelectionChanged event.
    
    Args:
        event_args: Event arguments
    """
    from streaming_updates import start_live_streaming,stop_live_streaming
    r=event_args.binding.getRange()
    is_live=xpycode.Objects.getObject("streaming_active")
    if is_live:
        stop_live_streaming()
    else:
        start_live_streaming()


def on_championship_rankings_onchanged(event_args: xpycode.Excel.WorksheetChangedEventArgs):
    """
    Handler for Worksheet[Championship Rankings].onChanged event.
    
    Args:
        event_args: Event arguments
    """

    rchanged=xpycode.EventManager.getEventArgsRange(event_args)
    rname=rchanged.worksheet.getRange("csName")
    r=xpycode.Tools.Intersect(rchanged,rname)
    if r is None:
        return
    enable_events=xpycode.EventManager.getEnableEvents()
    xpycode.EventManager.setEnableEvents(False)
    import show_rankings
    show_rankings.show_rankings(r.values[0][0])
    xpycode.setEnableEvents(enable_events)




def on_championship_rankings_onselectionchanged(event_args: xpycode.Excel.WorksheetSelectionChangedEventArgs):
    """
    Handler for Worksheet[Championship Rankings].onSelectionChanged event.
    
    Args:
        event_args: Event arguments
    """
    

    rchanged=xpycode.EventManager.getEventArgsRange(event_args)
    rname=rchanged.worksheet.getRange("rAllNames")
    r=xpycode.Tools.Intersect(rchanged,rname)
    if r is None:
        return

    enable_events=xpycode.EventManager.getEnableEvents()
    xpycode.EventManager.setEnableEvents(False)
    import show_match_details
    r=r.getCell(0,0)
    team_name=r.values[0][0]
    if team_name!='':
        championship_name=r.worksheet.getRange("csName").values[0][0]
        if championship_name!='':
            show_match_details.show_match_details(team_name,championship_name)
    xpycode.setEnableEvents(enable_events)


def on_match_day_view_onchanged(event_args: xpycode.Excel.WorksheetChangedEventArgs):
    """
    Handler for Worksheet[Match Day View].onChanged event.
    
    Args:
        event_args: Event arguments
    """
    rchanged=xpycode.EventManager.getEventArgsRange(event_args)
    rname=rchanged.worksheet.getRange("csDayName")
    rnum=rchanged.worksheet.getRange("csDayNum")
    r=xpycode.Tools.Intersect(rchanged,xpycode.Tools.Union(rname,rnum))
    if r is None:
        return

    enable_events=xpycode.EventManager.getEnableEvents()
    xpycode.EventManager.setEnableEvents(False)
    import show_matches_by_day
    championship_name=rname.values[0][0]
    day_num=rnum.values[0][0]
    show_matches_by_day.show_matches_by_day(day_num,championship_name)
    xpycode.setEnableEvents(enable_events)


