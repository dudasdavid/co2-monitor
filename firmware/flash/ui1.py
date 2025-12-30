import lvgl as lv
from math import ceil

# ---- Global variables ----
import shared_variables as var

SCREEN_H = 272
SCREEN_W = 480
STATUS_BAR_H = 24
PAGE_W_PADDING = 28

# ---- Swipe handling ----
SWIPE_THRESHOLD = 40   # pixels
LOCK_THRESHOLD  = 12  # when horizontal movement is clearly starting

# ---- LVGL helper functions ----
def show_screen(idx):
    """Load screen by index (wrap around)."""
    #global current_idx
    if not var.screens:
        return
    var.current_idx = idx % len(var.screens)
    lv.scr_load(var.screens[var.current_idx])


def next_screen():
    show_screen(var.current_idx + 1)


def prev_screen():
    show_screen(var.current_idx - 1)

def swipe_event_cb(obj, event):
    #global touch_start_x, touch_start_y

    if event == lv.EVENT.PRESSED:
        # Remember where the touch started
        indev = lv.indev_get_act()
        if not indev:
            return
        p = lv.point_t()
        indev.get_point(p)
        var.touch_start_x = p.x
        var.touch_start_y = p.y

    elif event == lv.EVENT.RELEASED:
        # Compare start and end to detect swipe direction
        indev = lv.indev_get_act()
        if not indev:
            return
        p = lv.point_t()
        indev.get_point(p)
        dx = p.x - var.touch_start_x
        dy = p.y - var.touch_start_y

        if abs(dx) > abs(dy) and abs(dx) > SWIPE_THRESHOLD:
            if dx < 0:
                # Swipe left go to next screen
                next_screen()
            else:
                # Swipe right go to previous screen
                prev_screen()

def swipe_event_table_on_page_cb(page):
    """
    Returns an event callback that knows which page to scroll.
    """
    def swipe_event_table_cb(obj, event):
        #global var.touch_start_x, var.touch_start_y, var.last_y

        indev = lv.indev_get_act()
        if not indev:
            return

        p = lv.point_t()
        indev.get_point(p)

        if event == lv.EVENT.PRESSED:
            # remember starting point
            var.touch_start_x = p.x
            var.touch_start_y = p.y
            var.last_y = p.y

        elif event == lv.EVENT.PRESSING:
            # handle vertical scrolling while finger moves
            dy = p.y - var.last_y
            var.last_y = p.y

            # scroll the page vertically
            # NOTE: sign might feel inverted, swap if it feels wrong
            if dy != 0:
                page.scroll_ver(int(dy*2.0))

        elif event == lv.EVENT.RELEASED:
            dx = p.x - var.touch_start_x
            dy = p.y - var.touch_start_y

            # Only treat as horizontal swipe if clearly more horizontal than vertical
            if abs(dx) > abs(dy) and abs(dx) > SWIPE_THRESHOLD:
                if dx < 0:
                    # swipe left -> next screen
                    next_screen()
                else:
                    # swipe right -> previous screen
                    prev_screen()
            # Otherwise: it was mostly vertical we already scrolled the page
            
    return swipe_event_table_cb

def create_sensor_table():
    scr = lv.obj()

    # This will be the scrollable area
    page = lv.page(scr)
    page.set_size(SCREEN_W, SCREEN_H-STATUS_BAR_H)                 # visible "window" size
    page.align(scr, lv.ALIGN.IN_TOP_MID, 0, STATUS_BAR_H)

    # Optional: control scrollbar behaviour
    page.set_scrollbar_mode(lv.SCROLLBAR_MODE.AUTO)
    # or:
    # page.set_scrollbar_mode(lv.SCROLLBAR_MODE.DRAG)  # only when dragging

    table = lv.table(page)
    table.set_size(SCREEN_W-PAGE_W_PADDING, 500)
    table.align(page, lv.ALIGN.IN_TOP_MID, 0, 0)

    #page.glue_obj(table)
    #table.parent_page = page

    # 2 columns and 15 rows
    table.set_col_cnt(2)
    table.set_row_cnt(13)

    table.set_col_width(0, 250)
    table.set_col_width(1, 180)

    '''
    # Static labels in first row
    table.set_cell_value(0, 0, "Sensor")
    table.set_cell_value(0, 1, "Value")
    
    rows = table.get_row_cnt()
    cols = table.get_col_cnt()

    # Make row 0 a header row
    for c in range(cols):
        table.set_cell_type(0, c, 2)   # 1 = CELL1, 2 = CELL2
    '''
    # Static labels in first column
    table.set_cell_value(0, 0, "Temperature AHT21 [°C]")
    table.set_cell_value(1, 0, "Temperature SCD41 [°C]")
    table.set_cell_value(2, 0, "Temperature ENS160 [°C]")
    table.set_cell_value(3, 0, "Temperature BMP280 [°C]")
    table.set_cell_value(4, 0, "Humidity AHT21 [%]")
    table.set_cell_value(5, 0, "Humidity SCD41 [%]")
    table.set_cell_value(6, 0, "Humidity ENS160 [%]")
    table.set_cell_value(7, 0, "CO2 [ppm]")
    table.set_cell_value(8, 0, "eCO2 ENS160 [ppm]")
    table.set_cell_value(9, 0, "TVOC [ppb]")
    table.set_cell_value(10, 0, "AQI")
    table.set_cell_value(11, 0, "Pressure [hPa]")
    table.set_cell_value(12, 0, "Lux")


    # --- LVGL task: pull Python vars & update table ---
    def table_update_cb(task):
        # Read your Python variables here
        table.set_cell_value(0, 1, "{:.1f}".format(var.sensor_data.temp_aht21))
        table.set_cell_value(1, 1, "{:.1f}".format(var.sensor_data.temp_scd41))
        table.set_cell_value(2, 1, "{:.1f}".format(var.sensor_data.temp_ens160))
        table.set_cell_value(3, 1, "{:.1f}".format(var.sensor_data.temp_bmp280))
        table.set_cell_value(4, 1, "{:.1f}".format(var.sensor_data.humidity_aht21))
        table.set_cell_value(5, 1, "{:.1f}".format(var.sensor_data.humidity_scd41))
        table.set_cell_value(6, 1, "{:.1f}".format(var.sensor_data.humidity_ens160))
        table.set_cell_value(7, 1, "{}".format(int(var.sensor_data.co2_scd41)))
        table.set_cell_value(8, 1, "{}".format(int(var.sensor_data.eco2_ens160)))
        table.set_cell_value(9, 1, "{}".format(int(var.sensor_data.tvoc_ens160)))
        table.set_cell_value(10, 1, "{}".format(int(var.sensor_data.aqi_ens160)))
        table.set_cell_value(11, 1, "{}".format(int(var.sensor_data.pressure_bmp280)))
        table.set_cell_value(12, 1, "{:.2f}".format(var.sensor_data.lux_veml7700))



    # --- Update table in every 500ms ---
    lv.task_create(table_update_cb, 500, lv.TASK_PRIO.LOW, None)

    # --- Enable swipe on the full screen and table ---
    scr.set_event_cb(swipe_event_cb)
    table.set_event_cb(swipe_event_table_on_page_cb(page))

    # --- Screen style ---
    style_scr = lv.style_t()
    style_scr.init()
    style_scr.set_bg_color(lv.STATE.DEFAULT, lv.color_hex(0x000000))   # black bg
    style_scr.set_text_color(lv.STATE.DEFAULT, lv.color_hex(0xffffff)) # white text
    scr.add_style(scr.PART.MAIN, style_scr)

    # --- Page style ---
    page_style = lv.style_t()
    page_style.init()
    page_style.set_bg_color(lv.STATE.DEFAULT, lv.color_hex(0x000000))
    page_style.set_bg_opa(lv.STATE.DEFAULT, lv.OPA.COVER)
    page_style.set_border_width(lv.STATE.DEFAULT, 0)

    page.add_style(page.PART.BG, page_style)

    # --- Remove thick border around table ---
    table_bg = lv.style_t()
    table_bg.init()
    table_bg.set_border_width(lv.STATE.DEFAULT, 0)  # kill the fat border
    table_bg.set_pad_all(lv.STATE.DEFAULT, 0)
    table_bg.set_bg_color(lv.STATE.DEFAULT, lv.color_hex(0x000000))
    table_bg.set_bg_opa(lv.STATE.DEFAULT, lv.OPA.COVER)
    table.add_style(table.PART.BG, table_bg)

    # --- Table style ---
    table_style = lv.style_t()
    table_style.init()
    # Background of table
    table_style.set_bg_color(lv.STATE.DEFAULT, lv.color_hex(0x101010))
    table_style.set_bg_opa(lv.STATE.DEFAULT, lv.OPA.COVER)
    # Text
    table_style.set_text_color(lv.STATE.DEFAULT, lv.color_hex(0xffffff))
    # Cell borders
    table_style.set_border_color(lv.STATE.DEFAULT, lv.color_hex(0x404040))
    table_style.set_border_width(lv.STATE.DEFAULT, 1)
    # Row/column dividers
    table_style.set_pad_top(lv.STATE.DEFAULT, 2)
    table_style.set_pad_bottom(lv.STATE.DEFAULT, 2)
    table_style.set_pad_left(lv.STATE.DEFAULT, 5)
    table_style.set_pad_right(lv.STATE.DEFAULT, 5)
    # Apply to your table
    table.add_style(table.PART.CELL1, table_style)   # normal cells
    '''
    # --- Header style ---
    header_style = lv.style_t()
    header_style.init()
    header_style.set_bg_color(lv.STATE.DEFAULT, lv.color_hex(0x303030))
    header_style.set_bg_opa(lv.STATE.DEFAULT, lv.OPA.COVER)
    header_style.set_text_color(lv.STATE.DEFAULT, lv.color_hex(0xffffff))
    
    header_style.set_border_width(lv.STATE.DEFAULT, 1)
    header_style.set_border_color(lv.STATE.DEFAULT, lv.color_hex(0x505050))
    header_style.set_border_side(lv.STATE.DEFAULT, lv.BORDER_SIDE.BOTTOM)  # only bottom line

    # SAME padding as body!
    header_style.set_pad_left(lv.STATE.DEFAULT, 2)
    header_style.set_pad_right(lv.STATE.DEFAULT, 2)
    header_style.set_pad_top(lv.STATE.DEFAULT, 6)
    header_style.set_pad_bottom(lv.STATE.DEFAULT, 6)

    table.add_style(table.PART.CELL2, header_style) 
    '''
    # --- Apply fonts style ---
    font_style = lv.style_t()
    font_style.init()
    font_style.set_text_font(lv.STATE.DEFAULT, lv.font_montserrat_14)
    table.add_style(table.PART.CELL1, font_style)  # normal cells
    #table.add_style(table.PART.CELL2, font_style)  # header cells

    # --- Add screen to screens ---
    var.screens.append(scr)
    var.screen_names.append("Sensors")
    return scr

def create_system_table():
    scr = lv.obj()
    
    # This will be the scrollable area
    page = lv.page(scr)
    page.set_size(SCREEN_W, SCREEN_H-STATUS_BAR_H)                 # visible "window" size
    page.align(scr, lv.ALIGN.IN_TOP_MID, 0, STATUS_BAR_H)

    # Optional: control scrollbar behaviour
    page.set_scrollbar_mode(lv.SCROLLBAR_MODE.AUTO)
    # or:
    # page.set_scrollbar_mode(lv.SCROLLBAR_MODE.DRAG)  # only when dragging

    table = lv.table(page)
    table.set_size(SCREEN_W-PAGE_W_PADDING, 500)
    table.align(page, lv.ALIGN.IN_TOP_MID, 0, 0)

    #page.glue_obj(table)
    #table.parent_page = page

    # 2 columns and 15 rows
    table.set_col_cnt(2)
    table.set_row_cnt(18)

    table.set_col_width(0, 180)
    table.set_col_width(1, 250)

    '''
    # Static labels in first row
    table.set_cell_value(0, 0, "System")
    table.set_cell_value(0, 1, "Value")

    rows = table.get_row_cnt()
    cols = table.get_col_cnt()

    # Make row 0 a header row
    for c in range(cols):
        table.set_cell_type(0, c, 2)   # 1 = CELL1, 2 = CELL2
    '''
    # Static labels in first column
    table.set_cell_value(0, 0, "WIFI status")
    table.set_cell_value(1, 0, "NTP time")
    table.set_cell_value(2, 0, "RTC time")
    table.set_cell_value(3, 0, "SD card status")
    table.set_cell_value(4, 0, "/flash storage")
    table.set_cell_value(5, 0, "/sd storage")
    table.set_cell_value(6, 0, "LVGL heap")
    table.set_cell_value(7, 0, "Lux")
    table.set_cell_value(8, 0, "Backlight")
    table.set_cell_value(9, 0, "i2c SCD41")
    table.set_cell_value(10, 0, "i2c AHT21")
    table.set_cell_value(11, 0, "i2c ENS160")
    table.set_cell_value(12, 0, "i2c BMP280")
    table.set_cell_value(13, 0, "i2c VEML7700")
    table.set_cell_value(14, 0, "i2c DS3231")
    table.set_cell_value(15, 0, "Unknown devices")
    table.set_cell_value(16, 0, "USB voltage")
    table.set_cell_value(17, 0, "Battery voltage")
    table.set_cell_value(18, 0, "Battery %") 

    # --- LVGL task: pull Python vars & update table ---
    def table_update_cb(task):
        # Read your Python variables here
        table.set_cell_value(0, 1, var.system_data.status_wifi)
        dt = var.system_data.time_ntp
        if dt is not None and type(dt) == tuple:
            table.set_cell_value(1, 1, "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(dt[0],dt[1],dt[2],dt[4],dt[5],dt[6]))
        else:
            table.set_cell_value(1, 1, "None")
        dt = var.system_data.time_rtc
        if dt is not None and type(dt) == tuple:
            table.set_cell_value(2, 1, "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(dt[0],dt[1],dt[2],dt[4],dt[5],dt[6]))
        else:
            table.set_cell_value(2, 1, "None")
        table.set_cell_value(3, 1, var.system_data.status_sd)
        table.set_cell_value(4, 1, "{}kB / {}kB".format(int(var.system_data.used_space_flash), int(var.system_data.total_space_flash)))
        table.set_cell_value(5, 1, "{}MB / {}MB".format(int(var.system_data.used_space_sd), int(var.system_data.total_space_sd)))
        table.set_cell_value(6, 1, "{}kB / {}kB".format(int(var.system_data.used_heap), int(var.system_data.total_heap)))
        table.set_cell_value(7, 1, "{:.2f}".format(var.sensor_data.lux_veml7700)) # This comes from sensor data!
        table.set_cell_value(8, 1, "{} / 1000".format(int(var.system_data.bl_duty_percent)))
        table.set_cell_value(9, 1, "SCD41 {} at 0x62".format(var.system_data.i2c_status_scd41))
        table.set_cell_value(10, 1, "AHT21 {} at 0x38".format(var.system_data.i2c_status_aht21))
        table.set_cell_value(11, 1, "ENS160 {} at 0x53".format(var.system_data.i2c_status_ens160))
        table.set_cell_value(12, 1, "BMP280 {} at 0x76".format(var.system_data.i2c_status_bmp280))
        table.set_cell_value(13, 1, "VEML7700 {} at 0x11".format(var.system_data.i2c_status_veml7700))
        table.set_cell_value(14, 1, "DS3231 {} at at 0x53".format(var.system_data.i2c_status_ds3231))
        table.set_cell_value(15, 1, "Uknown devices at {}".format(str(var.system_data.i2c_status_unknown)))
        table.set_cell_value(16, 1, "{:.2f}".format(var.system_data.usb_volt))
        table.set_cell_value(17, 1, "{:.2f}".format(var.system_data.bat_volt))
        table.set_cell_value(18, 1, "{}".format(int(var.system_data.bat_percentage)))


    # --- Update table in every 1000ms ---
    lv.task_create(table_update_cb, 1000, lv.TASK_PRIO.LOW, None)

    # --- Enable swipe on the full screen and table ---
    scr.set_event_cb(swipe_event_cb)
    table.set_event_cb(swipe_event_table_on_page_cb(page))

    # --- Screen style ---
    style_scr = lv.style_t()
    style_scr.init()
    style_scr.set_bg_color(lv.STATE.DEFAULT, lv.color_hex(0x000000))   # black bg
    style_scr.set_text_color(lv.STATE.DEFAULT, lv.color_hex(0xffffff)) # white text
    scr.add_style(scr.PART.MAIN, style_scr)

    # --- Page style ---
    page_style = lv.style_t()
    page_style.init()
    page_style.set_bg_color(lv.STATE.DEFAULT, lv.color_hex(0x000000))
    page_style.set_bg_opa(lv.STATE.DEFAULT, lv.OPA.COVER)
    page_style.set_border_width(lv.STATE.DEFAULT, 0)

    page.add_style(page.PART.BG, page_style)

    # --- Remove thick border around table ---
    table_bg = lv.style_t()
    table_bg.init()
    table_bg.set_border_width(lv.STATE.DEFAULT, 0)  # kill the fat border
    table_bg.set_pad_all(lv.STATE.DEFAULT, 0)
    table_bg.set_bg_color(lv.STATE.DEFAULT, lv.color_hex(0x000000))
    table_bg.set_bg_opa(lv.STATE.DEFAULT, lv.OPA.COVER)
    table.add_style(table.PART.BG, table_bg)

    # --- Table style ---
    table_style = lv.style_t()
    table_style.init()
    # Background of table
    table_style.set_bg_color(lv.STATE.DEFAULT, lv.color_hex(0x101010))
    table_style.set_bg_opa(lv.STATE.DEFAULT, lv.OPA.COVER)
    # Text
    table_style.set_text_color(lv.STATE.DEFAULT, lv.color_hex(0xffffff))
    # Cell borders
    table_style.set_border_color(lv.STATE.DEFAULT, lv.color_hex(0x404040))
    table_style.set_border_width(lv.STATE.DEFAULT, 1)
    # Row/column dividers
    table_style.set_pad_top(lv.STATE.DEFAULT, 2)
    table_style.set_pad_bottom(lv.STATE.DEFAULT, 2)
    table_style.set_pad_left(lv.STATE.DEFAULT, 5)
    table_style.set_pad_right(lv.STATE.DEFAULT, 5)
    # Apply to your table
    table.add_style(table.PART.CELL1, table_style)   # normal cells

    '''
    # --- Header style ---
    header_style = lv.style_t()
    header_style.init()
    header_style.set_bg_color(lv.STATE.DEFAULT, lv.color_hex(0x303030))
    header_style.set_bg_opa(lv.STATE.DEFAULT, lv.OPA.COVER)
    header_style.set_text_color(lv.STATE.DEFAULT, lv.color_hex(0xffffff))
    
    header_style.set_border_width(lv.STATE.DEFAULT, 1)
    header_style.set_border_color(lv.STATE.DEFAULT, lv.color_hex(0x505050))
    header_style.set_border_side(lv.STATE.DEFAULT, lv.BORDER_SIDE.BOTTOM)  # only bottom line

    # SAME padding as body!
    header_style.set_pad_left(lv.STATE.DEFAULT, 2)
    header_style.set_pad_right(lv.STATE.DEFAULT, 2)
    header_style.set_pad_top(lv.STATE.DEFAULT, 6)
    header_style.set_pad_bottom(lv.STATE.DEFAULT, 6)

    table.add_style(table.PART.CELL2, header_style) 
    '''
    # --- Apply fonts style ---
    font_style = lv.style_t()
    font_style.init()
    font_style.set_text_font(lv.STATE.DEFAULT, lv.font_montserrat_14)
    table.add_style(table.PART.CELL1, font_style)  # normal cells
    #table.add_style(table.PART.CELL2, font_style)  # header cells

    # --- Add screen to screens ---
    var.screens.append(scr)
    var.screen_names.append("System")
    return scr


    
def create_console_log():
    
    scr = lv.obj()
    
    BTN_BAR_H = 40
    
    # Root container
    root = lv.cont(scr, None)
    root.set_size(SCREEN_W, SCREEN_H-STATUS_BAR_H)
    root.align(scr, lv.ALIGN.IN_TOP_MID, 0, STATUS_BAR_H)
    root.set_fit(lv.FIT.NONE)
    root.set_layout(lv.LAYOUT.COLUMN_MID)   # vertical stacking
    
    # 1) Create the scrollable page
    page = lv.page(root)
    page.set_size(SCREEN_W, SCREEN_H-STATUS_BAR_H-BTN_BAR_H)
    #page.align(scr, lv.ALIGN.IN_TOP_MID, 0, 0)
    page.set_scrollbar_mode(lv.SCROLLBAR_MODE.AUTO)
    #page.set_fit2(lv.FIT.FLOOD, lv.FIT.PARENT)
    #page.set_scrl_fit2(lv.FIT.FLOOD, lv.FIT.TIGHT)   # horizontal fill, vertical = content height
    scrl = page.get_child(None)
    scrl.set_width(SCREEN_W)

    # 2) Create the label inside the page
    log_label = lv.label(page)
    log_label.set_long_mode(lv.label.LONG.BREAK)  # multi-line wrap
    log_label.set_width(page.get_width_fit() - 10)      # <-- key: match usable page width
    log_label.set_text("")  # empty initially
    log_label.set_recolor(True)

    # --- Apply fonts style ---
    font_style = lv.style_t()
    font_style.init()
    font_style.set_text_font(lv.STATE.DEFAULT, lv.font_montserrat_10)
    log_label.add_style(lv.label.PART.MAIN, font_style)

    # --- Apply indentation within the label ---
    style_label_indent = lv.style_t()
    style_label_indent.init()

    style_label_indent.set_pad_left(lv.STATE.DEFAULT, 4)   # ← adjust: 2–6 px usually perfect
    style_label_indent.set_pad_right(lv.STATE.DEFAULT, 2)
    style_label_indent.set_pad_top(lv.STATE.DEFAULT, 2)
    style_label_indent.set_pad_bottom(lv.STATE.DEFAULT, 2)
    
    log_label.add_style(lv.label.PART.MAIN, style_label_indent)

    # --- Bottom button bar ---
    bar = lv.cont(root, None)
    bar.set_size(SCREEN_W, BTN_BAR_H)
    bar.set_fit(lv.FIT.NONE)
    bar.set_layout(lv.LAYOUT.ROW_MID)       # 4 buttons in a row
    
    btn_w = SCREEN_W // 5
    
    style_nopad = lv.style_t()
    style_nopad.init()
    style_nopad.set_pad_all(lv.STATE.DEFAULT, 0)
    style_nopad.set_pad_inner(lv.STATE.DEFAULT, 0)
    
    root.add_style(lv.cont.PART.MAIN, style_nopad)
    page.add_style(lv.page.PART.BG, style_nopad)
    page.add_style(lv.page.PART.SCROLLABLE, style_nopad)
    bar.add_style(lv.cont.PART.MAIN, style_nopad)
    
    def make_btn(txt, cb):
        b = lv.btn(bar, None)
        b.set_size(btn_w, BTN_BAR_H)
        b.set_checkable(True)
        b.add_style(lv.btn.PART.MAIN, style_nopad)
        b.set_event_cb(cb)

        l = lv.label(b, None)
        l.set_text(txt)
        return b

    # Example callbacks
    def btn1_cb(obj, event):
        if event == lv.EVENT.CLICKED:
            if obj.get_state() & lv.STATE.CHECKED: 
                print("Pause is ON")
                var.logger_paused = True
            else:
                print("Pause is OFF")
                var.logger_paused = False

    def btn2_cb(obj, event):
        nonlocal log_label
        if event == lv.EVENT.CLICKED:
            if obj.get_state() & lv.STATE.CHECKED:
                
                log_label.delete()
                log_label = lv.label(page)
                log_label.set_long_mode(lv.label.LONG.BREAK)  # multi-line wrap
                log_label.set_width(page.get_width_fit() - 10)      # <-- key: match usable page width
                log_label.set_text("")  # empty initially
                log_label.set_recolor(True)
                log_label.add_style(lv.label.PART.MAIN, font_style)
                log_label.add_style(lv.label.PART.MAIN, style_label_indent)
                
                btn3.clear_state(lv.STATE.CHECKED)
                btn4.clear_state(lv.STATE.CHECKED)
                btn5.clear_state(lv.STATE.CHECKED)
                var.logger_current_view = var.logger_debug

    def btn3_cb(obj, event):
        nonlocal log_label
        if event == lv.EVENT.CLICKED:
            if obj.get_state() & lv.STATE.CHECKED:
                
                log_label.delete()
                log_label = lv.label(page)
                log_label.set_long_mode(lv.label.LONG.BREAK)  # multi-line wrap
                log_label.set_width(page.get_width_fit() - 10)      # <-- key: match usable page width
                log_label.set_text("")  # empty initially
                log_label.set_recolor(True)
                log_label.add_style(lv.label.PART.MAIN, font_style)
                log_label.add_style(lv.label.PART.MAIN, style_label_indent)
                
                btn2.clear_state(lv.STATE.CHECKED)
                btn4.clear_state(lv.STATE.CHECKED)
                btn5.clear_state(lv.STATE.CHECKED)
                var.logger_current_view = var.logger_info

    def btn4_cb(obj, event):
        nonlocal log_label
        if event == lv.EVENT.CLICKED:
            if obj.get_state() & lv.STATE.CHECKED:
                
                log_label.delete()
                log_label = lv.label(page)
                log_label.set_long_mode(lv.label.LONG.BREAK)  # multi-line wrap
                log_label.set_width(page.get_width_fit() - 10)      # <-- key: match usable page width
                log_label.set_text("")  # empty initially
                log_label.set_recolor(True)
                log_label.add_style(lv.label.PART.MAIN, font_style)
                log_label.add_style(lv.label.PART.MAIN, style_label_indent)
                
                btn2.clear_state(lv.STATE.CHECKED)
                btn3.clear_state(lv.STATE.CHECKED)
                btn5.clear_state(lv.STATE.CHECKED)
                var.logger_current_view = var.logger_warning
            
    def btn5_cb(obj, event):
        nonlocal log_label
        if event == lv.EVENT.CLICKED:
            if obj.get_state() & lv.STATE.CHECKED:
                
                log_label.delete()
                log_label = lv.label(page)
                log_label.set_long_mode(lv.label.LONG.BREAK)  # multi-line wrap
                log_label.set_width(page.get_width_fit() - 10)      # <-- key: match usable page width
                log_label.set_text("")  # empty initially
                log_label.set_recolor(True)
                log_label.add_style(lv.label.PART.MAIN, font_style)
                log_label.add_style(lv.label.PART.MAIN, style_label_indent)
                
                btn2.clear_state(lv.STATE.CHECKED)
                btn3.clear_state(lv.STATE.CHECKED)
                btn4.clear_state(lv.STATE.CHECKED)
                var.logger_current_view = var.logger_error

    btn1 = make_btn("Pause",   btn1_cb)
    btn2 = make_btn("Debug",   btn2_cb)
    btn3 = make_btn("Info",    btn3_cb)
    btn4 = make_btn("Warning", btn4_cb)
    btn5 = make_btn("Error",   btn5_cb)
    
    var.logger_current_view = var.logger_error
    btn5.set_state(lv.STATE.CHECKED)
    
    def page_scroll_to_bottom(page):
        scrl = page.get_child(None)  # scrollable container
        y = page.get_height_fit() - scrl.get_height()
        if y > 0: 
            y = 0
        scrl.set_y(y)
        

    def update_log_cb(timer):
        nonlocal log_label
        
        logger_label = "\n".join(var.logger_current_view)
        if logger_label != var.logger_label_prev:
                       
            log_label.set_text(logger_label)
            log_label.set_width(page.get_width_fit()-10)  # keep wrap correct
            
            # let LVGL recalc sizes/scrollbars
            lv.task_handler()
            #lv.task_handler()
            #lv.refr_now(None)
            #log_label.update_layout()
            #scrl.update_layout()
            #page.update_layout()

            # --- IMPORTANT: shrink scrollable height to exactly label height ---
            new_h = log_label.get_height()   # now valid after task_handler()
            if new_h < page.get_height_fit():
                new_h = page.get_height_fit()  # at least viewport height (avoid weirdness)
            scrl.set_height(new_h)

            # Clamp scroll position (prevents "scrolling into empty space")
            min_y = page.get_height_fit() - scrl.get_height()
            if min_y > 0:
                min_y = 0
            if scrl.get_y() < min_y:
                scrl.set_y(min_y)      
            
            logger_label_prev = logger_label
            
        if not var.logger_paused:
            page_scroll_to_bottom(page)
        
    # --- Update time in every 500ms ---
    lv.task_create(update_log_cb, 500, lv.TASK_PRIO.LOW, None)
    
    # --- Enable swipe on the full screen and table ---
    scr.set_event_cb(swipe_event_cb)
    scrl = page.get_child(None)
    scrl.set_event_cb(swipe_event_table_on_page_cb(page))

    style_checked = lv.style_t()
    style_checked.init()
    style_checked.set_bg_color(lv.STATE.CHECKED, lv.color_hex(0x4040FF))
    style_checked.set_text_color(lv.STATE.CHECKED, lv.color_hex(0xffffff))

    btn1.add_style(lv.btn.PART.MAIN, style_checked)

    # --- Add screen to screens ---
    var.screens.append(scr)
    var.screen_names.append("Log")
    return scr 

