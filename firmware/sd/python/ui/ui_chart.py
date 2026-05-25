import lvgl as lv
from math import ceil
from ui import ui_generic as ui

# ---- Global variables ----
if ui.SIMULATOR:
    import fake_shared_variables as var
else:
    import shared_variables as var

def calc_nice_axis(y_min, y_max_raw, steps, base=100, min_y_max=1100):
    """
    Calculate a 'nice' y_max and labels for a chart axis.

    y_min:      minimum value (e.g. 300)
    y_max_raw:  maximum of your data series
    steps:      number of intervals between min and max (grids)
                -> labels count = steps + 2 (including min & max)
    base:       granularity of 'niceness' (100 => multiples of 100)
    min_y_max:  minimal allowed y_max (for your CO2 case: 1100)

    Returns: y_max
    """
    # Ensure we have at least some span
    if y_max_raw <= y_min:
        y_max_raw = y_min + base * (steps + 1)

    # Enforce minimum y_max (like your 1100 rule)
    if y_max_raw < min_y_max:
        y_max_raw = min_y_max

    # Raw span & step
    span_raw = y_max_raw - y_min
    step_raw = span_raw / (steps + 1)

    # Round the step up to the next 'nice' multiple of base (100)
    step = int(ceil(step_raw / base)) * base

    # Recompute y_max so that all ticks are aligned to this step
    y_max = y_min + step * (steps + 1)

    # Generate label values
    #labels = [y_min + i * step for i in range(steps + 2)]

    return y_max

def create_co2_chart(alt=False):
    scr = lv.obj()
    
    chart = lv.chart(scr)
    chart.set_size(ui.SCREEN_W, ui.SCREEN_H - ui.STATUS_BAR_H)
    chart.align(scr, lv.ALIGN.IN_TOP_MID, 0, ui.STATUS_BAR_H)

    co2_last_label = lv.label(scr)
    co2_last_label.set_text("")       # starts empty
    co2_last_label.set_auto_realign(True)

    # Line chart
    chart.set_type(lv.chart.TYPE.LINE)

    # X-axis: up to 24h of data
    chart.set_point_count(1)  # start with 1, will update dynamically

    y_grids = 3

    # Add grid lines
    chart.set_div_line_count(y_grids, 5)
    
    # Give space for X and Y tick texts (labels)
    #chart.set_style_local_pad_bottom(lv.obj.PART.MAIN, lv.STATE.DEFAULT, 20)
    #chart.set_style_local_pad_top(lv.obj.PART.MAIN, lv.STATE.DEFAULT, 20)
    #chart.set_style_local_pad_left(lv.obj.PART.MAIN, lv.STATE.DEFAULT, 50)

    # Y-axis range (CO2 ppm). You can change to dynamic later.
    chart.set_y_range(lv.chart.AXIS.PRIMARY_Y, 0, 3000)

    # Add series for CO2 (green)
    ser = chart.add_series(lv.color_hex(0x00FF00))
    
    # Set padding around chart labels
    #chart.set_x_tick_texts("-24h\n-20h\n-16h\n-12h\n-8h\n-4h\n0h", 7, 0)
    chart.set_style_local_pad_bottom(0,0,0)
    chart.set_style_local_pad_top(0,0,0)
    chart.set_style_local_pad_right(0,0,0)
    chart.set_style_local_pad_left(0,0,0)
    #chart.set_x_tick_length(0, 0)
    
    # Add X axis labels
    x_axis_label_1 = lv.label(scr)
    x_axis_label_1.set_text("-20h")
    x_axis_label_1.set_pos(82, 255)
    x_axis_label_2 = lv.label(scr)
    x_axis_label_2.set_text("-12h")
    x_axis_label_2.set_pos(242, 255)
    x_axis_label_3 = lv.label(scr)
    x_axis_label_3.set_text("-4h")
    x_axis_label_3.set_pos(402, 255)
    x_axis_label_1.set_style_local_text_color(lv.obj.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xC0C0C0))
    x_axis_label_1.set_style_local_bg_opa(lv.obj.PART.MAIN, lv.STATE.DEFAULT, lv.OPA.TRANSP)
    x_axis_label_2.set_style_local_text_color(lv.obj.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xC0C0C0))
    x_axis_label_2.set_style_local_bg_opa(lv.obj.PART.MAIN, lv.STATE.DEFAULT, lv.OPA.TRANSP)
    x_axis_label_3.set_style_local_text_color(lv.obj.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xC0C0C0))
    x_axis_label_3.set_style_local_bg_opa(lv.obj.PART.MAIN, lv.STATE.DEFAULT, lv.OPA.TRANSP)
    
    # Add Y axis labels
    y_axis_label_1 = lv.label(scr)
    y_axis_label_1.set_text("1000")
    y_axis_label_1.set_pos(4, 26)
    y_axis_label_2 = lv.label(scr)
    y_axis_label_2.set_text("900")
    y_axis_label_2.set_pos(4, 87)
    y_axis_label_3 = lv.label(scr)
    y_axis_label_3.set_text("800")
    y_axis_label_3.set_pos(4, 149)
    y_axis_label_4 = lv.label(scr)
    y_axis_label_4.set_text("700")
    y_axis_label_4.set_pos(4, 210)
    y_axis_label_1.set_style_local_text_color(lv.obj.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xC0C0C0))
    y_axis_label_1.set_style_local_bg_opa(lv.obj.PART.MAIN, lv.STATE.DEFAULT, lv.OPA.TRANSP)
    y_axis_label_2.set_style_local_text_color(lv.obj.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xC0C0C0))
    y_axis_label_2.set_style_local_bg_opa(lv.obj.PART.MAIN, lv.STATE.DEFAULT, lv.OPA.TRANSP)
    y_axis_label_3.set_style_local_text_color(lv.obj.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xC0C0C0))
    y_axis_label_3.set_style_local_bg_opa(lv.obj.PART.MAIN, lv.STATE.DEFAULT, lv.OPA.TRANSP)
    y_axis_label_4.set_style_local_text_color(lv.obj.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xC0C0C0))
    y_axis_label_4.set_style_local_bg_opa(lv.obj.PART.MAIN, lv.STATE.DEFAULT, lv.OPA.TRANSP)
    
    def place_last_value_label(chart, ser, value, index, y_min, y_max):
        # 1—Get outer coords
        a = lv.area_t()
        chart.get_coords(a)

        # 2—Get paddings
        pad_left   = chart.get_style_pad_left(0)
        pad_right  = chart.get_style_pad_right(0)
        pad_top    = chart.get_style_pad_top(0)
        pad_bottom = chart.get_style_pad_bottom(0)

        # 3—Inner chart area
        inner_x1 = a.x1 + pad_left
        inner_y1 = a.y1 + pad_top
        inner_x2 = a.x2 - pad_right
        inner_y2 = a.y2 - pad_bottom

        inner_w = inner_x2 - inner_x1
        inner_h = inner_y2 - inner_y1

        # Avoid division by zero
        if index < 1:
            px = inner_x1
        else:
            px = inner_x1 + int((index * inner_w) / (chart.get_point_count() - 1))

        # Clamp empty range
        yrange = (y_max - y_min) if (y_max != y_min) else 1

        py = inner_y2 - int((value - y_min) * inner_h / yrange)

        co2_last_label.set_text(str(value))

        # offset: above & slightly left
        co2_last_label.set_pos(px - 35, py - 8)

    def update_co2_chart_cb(task):
        if lv.scr_act() != scr:
            return

        data = var.scd41_co2_history
        n = len(data)

        if n == 0:
            # Nothing to show
            chart.set_point_count(1)
            chart.set_point_id(ser, 0, 0)
            return

        # --- SPECIAL CASE: only 1 item -> draw a flat line ---
        if n == 1:
            data = data*2
            n = 2

        # Safety clamp: never above max expected
        if n > var.CO2_HISTORY_MAX:
            data = data[-var.CO2_HISTORY_MAX:]
            n = len(data)

        # Make LVGL series length follow your list length
        chart.set_point_count(n)

        # Optional: dynamic Y range based on actual data
        y_min = 300 #min(data)
        y_max = max(data)

        # Avoid max < min
        if y_max < y_min:
            y_min = y_max

        # Avoid zero-height range
        if y_min == y_max:
            y_min -= 50
            y_max += 50
            if y_min < 0:
                y_min = 0
                
        y_max = calc_nice_axis(300, y_max, y_grids)
                
        # Or comment this out to stick to fixed 0…3000 range above
        chart.set_y_range(lv.chart.AXIS.PRIMARY_Y, y_min, y_max)

        # Copy list → chart
        for i, val in enumerate(data):
            chart.set_point_id(ser, val, i)

        # Choose labels
        steps = y_grids
        step = (y_max - y_min) // (steps + 1)

        labels = []
        for i in range(steps + 2):
            labels.append(str(y_min + i * step))

        labels.reverse()
        '''
        label_text = "\n".join(labels)

        chart.set_y_tick_texts(label_text, len(labels), lv.chart.AXIS.PRIMARY_Y)
        chart.set_y_tick_length(0, 0)
        '''
        
        y_axis_label_1.set_text(labels[0])
        y_axis_label_2.set_text(labels[1])
        y_axis_label_3.set_text(labels[2])
        y_axis_label_4.set_text(labels[3])

        last_val = data[-1]
        last_index = n - 1
        place_last_value_label(chart, ser, last_val, last_index, y_min, y_max + 70)

        # Redraw
        chart.refresh()

    # --- Update chart in every 1000ms ---
    lv.task_create(update_co2_chart_cb, 3000, lv.TASK_PRIO.LOW, None)

    # --- Enable swipe on the full screen and table ---
    scr.set_event_cb(ui.swipe_event_cb)
    chart.set_event_cb(ui.swipe_event_cb)

    chart.set_style_local_border_width(lv.btn.PART.MAIN, lv.STATE.DEFAULT, 0)
    chart.set_style_local_outline_width(lv.btn.PART.MAIN, lv.STATE.DEFAULT, 0)
    chart.set_style_local_shadow_width(lv.btn.PART.MAIN, lv.STATE.DEFAULT, 0)
    chart.set_style_local_radius(lv.btn.PART.MAIN, lv.STATE.DEFAULT, 0)
    
    chart.set_style_local_bg_color(lv.obj.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0x000000))
    chart.set_style_local_bg_opa(lv.obj.PART.MAIN, lv.STATE.DEFAULT, lv.OPA.COVER)

    chart.set_style_local_line_color(lv.chart.PART.BG, lv.STATE.DEFAULT, lv.color_hex(0x606060))
    chart.set_style_local_line_color(lv.chart.PART.SERIES_BG, lv.STATE.DEFAULT, lv.color_hex(0x606060))
    chart.set_style_local_line_width(lv.chart.PART.BG, lv.STATE.DEFAULT, 1)
    chart.set_style_local_text_color(lv.chart.PART.BG, lv.STATE.DEFAULT, lv.color_hex(0x606060))
    co2_last_label.set_style_local_text_color(lv.obj.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0x00FF00))
    co2_last_label.set_style_local_bg_opa(lv.obj.PART.MAIN, lv.STATE.DEFAULT, lv.OPA.TRANSP)
    
    # Add a faded area effect
    #chart.set_style_local_bg_opa(lv.chart.PART.SERIES, lv.STATE.DEFAULT, lv.OPA._50)               # Max. opa.
    #chart.set_style_local_bg_grad_dir(lv.chart.PART.SERIES, lv.STATE.DEFAULT, lv.GRAD_DIR.VER)
    #chart.set_style_local_bg_main_stop(lv.chart.PART.SERIES, lv.STATE.DEFAULT, 255)                # Max opa on the top
    #chart.set_style_local_bg_grad_stop(lv.chart.PART.SERIES, lv.STATE.DEFAULT, 50)
    
    # Change dot size and line width
    style_series = lv.style_t()
    style_series.init()

    # 0 size = no visible dots
    style_series.set_size(lv.STATE.DEFAULT, 1)
    # keep a nice line thickness
    style_series.set_line_width(lv.STATE.DEFAULT, 2)

    chart.add_style(lv.chart.PART.SERIES, style_series)
    
    # --- Add screen to screens --- 
    screen_name = "CO2 Chart"
    if not alt:
        var.screens.append(scr)
        var.screen_names.append(screen_name)
    else:
        var.screens_alt.append(scr)
        var.screen_names_alt.append(screen_name)
    
    return scr
