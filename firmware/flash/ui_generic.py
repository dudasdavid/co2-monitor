import lvgl as lv

# ---- Global variables ----
import shared_variables as var

SCREEN_H = 272
SCREEN_W = 480
STATUS_BAR_H = 24
PAGE_W_PADDING = 0

# ---- Swipe handling ----
SWIPE_THRESHOLD = 60   # pixels
LOCK_THRESHOLD  = 12  # when horizontal movement is clearly starting

charging_blink = 0

screen_label = None

# ---- LVGL helper functions ----
def show_screen(idx):
    """Load screen by index (wrap around)."""
    #global current_idx
    if not var.screens:
        return
    var.current_idx = idx % len(var.screens)
    lv.scr_load(var.screens[var.current_idx])
    
    global screen_label
    s = var.screen_names[var.current_idx]
    #print("screen name:", s)
    screen_label.set_text(s)


def next_screen():
    var.haptic_events.put_nowait(var.EVENT_FB_SWIPE_LEFT)
    show_screen(var.current_idx + 1)
    
def prev_screen():
    var.haptic_events.put_nowait(var.EVENT_FB_SWIPE_RIGHT)
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
                page.scroll_ver(int(dy*3.0))

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

def create_screen(bg_color, text):
    scr = lv.obj()

    # Background color
    scr.set_style_local_bg_color(
        scr.PART.MAIN,
        lv.STATE.DEFAULT,
        lv.color_hex(bg_color)
    )

    # Simple label in the middle
    label = lv.label(scr)
    label.set_text(text)
    label.align(None, lv.ALIGN.CENTER, 0, 0)

    # Enable swipe on the full screen
    scr.set_event_cb(swipe_event_cb)

    var.screens.append(scr)
    var.screen_names.append(text)
    return scr

def _battery_symbol_from_pct(pct):
    # LVGL has several battery glyphs in the built-in font
    if pct <= 5:
        return lv.SYMBOL.BATTERY_EMPTY
    elif pct <= 25:
        return lv.SYMBOL.BATTERY_1
    elif pct <= 50:
        return lv.SYMBOL.BATTERY_2
    elif pct <= 75:
        return lv.SYMBOL.BATTERY_3
    else:
        return lv.SYMBOL.BATTERY_FULL


def create_battery_widget(parent, right_pad=6, top_pad=2):
    """
    Returns a dict of LVGL objects you can update:
      w['cont'], w['icon'], w['bolt'], w['pct_lbl']
    """

    w = {}

    # Container on the right
    cont = lv.cont(parent)
    #cont.set_fit(lv.FIT.NONE)
    #cont.set_layout(lv.LAYOUT.OFF)
    cont.set_height(parent.get_height())
    cont.set_width(40)  # tweak if you want it tighter/wider
    cont.align(parent, lv.ALIGN.IN_RIGHT_MID, -right_pad, 0)
    cont.set_fit2(lv.FIT.TIGHT, lv.FIT.TIGHT)     # container hugs its children
    cont.set_layout(lv.LAYOUT.ROW_MID)            # children placed left→right, vertically centered
    cont.set_style_local_pad_inner(lv.obj.PART.MAIN, lv.STATE.DEFAULT, 3)

    # Make it visually "flat"
    cont.set_style_local_bg_opa(lv.obj.PART.MAIN, lv.STATE.DEFAULT, lv.OPA.TRANSP)
    cont.set_style_local_border_width(lv.obj.PART.MAIN, lv.STATE.DEFAULT, 0)
    cont.set_style_local_outline_width(lv.obj.PART.MAIN, lv.STATE.DEFAULT, 0)
    cont.set_style_local_shadow_width(lv.obj.PART.MAIN, lv.STATE.DEFAULT, 0)

    # Percent label (fixed width-ish so it doesn't “jump”)
    #pct_lbl = lv.label(cont)
    #pct_lbl.set_text("100%")
    #pct_lbl.align(cont, lv.ALIGN.IN_LEFT_MID, 4, 0)
    #pct_lbl.set_style_local_text_color(lv.obj.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xCCCCCC))
    #pct_lbl.set_style_local_text_opa(lv.label.PART.MAIN, lv.STATE.DEFAULT, lv.OPA.TRANSP)

    # --- Icon container (so we can overlay stuff) ---
    icon_cont = lv.cont(cont)
    icon_cont.set_size(40, STATUS_BAR_H)
    icon_cont.set_layout(lv.LAYOUT.OFF)

    # remove visuals
    icon_cont.set_style_local_bg_opa(lv.obj.PART.MAIN, lv.STATE.DEFAULT, lv.OPA.TRANSP)
    icon_cont.set_style_local_border_width(lv.obj.PART.MAIN, lv.STATE.DEFAULT, 0)

    # Battery icon
    icon = lv.label(icon_cont)
    icon.set_text(lv.SYMBOL.BATTERY_FULL)
    icon.set_style_local_text_color(lv.obj.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xCCCCCC))
    icon.align(icon_cont, lv.ALIGN.CENTER, 0, -3)

    # Charging bolt shadow overlay (hidden by default)
    bolt_shadow = lv.label(icon_cont)
    bolt_shadow.set_text(lv.SYMBOL.CHARGE)
    bolt_shadow.set_style_local_text_opa(lv.label.PART.MAIN, lv.STATE.DEFAULT, lv.OPA.TRANSP)
    bolt_shadow.align(icon, lv.ALIGN.CENTER, 0, 0)
    bolt_shadow.set_style_local_text_color(lv.obj.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0x101010))

    # Charging bolt overlay (hidden by default)
    bolt = lv.label(icon_cont)
    bolt.set_text(lv.SYMBOL.CHARGE)
    bolt.set_style_local_text_opa(lv.label.PART.MAIN, lv.STATE.DEFAULT, lv.OPA.TRANSP)
    bolt.align(icon, lv.ALIGN.CENTER, 1, 2)
    bolt.set_style_local_text_color(lv.obj.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xC3A100))

    # --- Apply fonts style ---
    font_style = lv.style_t()
    font_style.init()
    font_style.set_text_font(lv.STATE.DEFAULT, lv.font_montserrat_16)
    icon.add_style(lv.label.PART.MAIN, font_style)

    font_style = lv.style_t()
    font_style.init()
    font_style.set_text_font(lv.STATE.DEFAULT, lv.font_montserrat_16)
    bolt_shadow.add_style(lv.label.PART.MAIN, font_style)
    
    font_style = lv.style_t()
    font_style.init()
    font_style.set_text_font(lv.STATE.DEFAULT, lv.font_montserrat_12)
    bolt.add_style(lv.label.PART.MAIN, font_style)

    w["icon"] = icon
    w["bolt_shadow"] = bolt_shadow
    w["bolt"] = bolt
    #w["pct_lbl"] = pct_lbl
    return w


def set_battery_widget(w, pct, charging=False):
    global charging_blink
    """
    pct: 0..100
    charging: True/False
    """
    if pct < 0: pct = 0
    if pct > 100: pct = 100

    w["icon"].set_text(_battery_symbol_from_pct(pct))

    # Fixed-width formatting to reduce visual jitter
    #w["pct_lbl"].set_text("{:>3d}%".format(pct))

    # Show/hide bolt (keep its space by using opacity)
    if charging and charging_blink % 2 == 0:
        w["bolt"].set_style_local_text_opa(
            lv.label.PART.MAIN,
            lv.STATE.DEFAULT,
            lv.OPA.COVER
        )
        
        w["bolt_shadow"].set_style_local_text_opa(
            lv.label.PART.MAIN,
            lv.STATE.DEFAULT,
            lv.OPA.COVER
        )

    else:
        w["bolt"].set_style_local_text_opa(
            lv.label.PART.MAIN,
            lv.STATE.DEFAULT,
            lv.OPA.TRANSP
        )
        
        w["bolt_shadow"].set_style_local_text_opa(
            lv.label.PART.MAIN,
            lv.STATE.DEFAULT,
            lv.OPA.TRANSP
        )
        
    charging_blink +=1


def create_status_bar(top_layer):
    #global btn_left, btn_right
    global screen_label

    status = lv.cont(top_layer, None)
    status.set_fit(lv.FIT.NONE)
    status.set_layout(lv.LAYOUT.OFF)
    status.set_width(SCREEN_W)
    status.set_height(STATUS_BAR_H)
    status.align(None, lv.ALIGN.IN_TOP_MID, 0, 0)

    status.set_style_local_border_width(lv.btn.PART.MAIN, lv.STATE.DEFAULT, 0)
    status.set_style_local_outline_width(lv.btn.PART.MAIN, lv.STATE.DEFAULT, 0)
    status.set_style_local_shadow_width(lv.btn.PART.MAIN, lv.STATE.DEFAULT, 0)
    status.set_style_local_radius(lv.btn.PART.MAIN, lv.STATE.DEFAULT, 0)

    #wifi_icon = lv.label(status, None)
    #wifi_icon.set_text(SYMBOL_WIFI)

    #sd_icon = lv.label(status, None)
    #sd_icon.set_text(SYMBOL_SD)
    
    status.set_style_local_bg_color(lv.STATE.DEFAULT, 0, lv.color_hex(0x101010))

    screen_label = lv.label(status)
    screen_label.set_text("SYSTEM")
    screen_label.align(status, lv.ALIGN.CENTER, 0, 0)
    
    screen_label.set_style_local_text_color(lv.obj.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xCCCCCC))
    
    time_row = lv.cont(status)
    time_row.set_fit2(lv.FIT.TIGHT, lv.FIT.TIGHT)     # container hugs its children
    time_row.set_layout(lv.LAYOUT.ROW_MID)            # children placed left→right, vertically centered
    # remove spacing between hour : minute
    time_row.set_style_local_pad_inner(lv.obj.PART.MAIN, lv.STATE.DEFAULT, 0)
    # remove any visual borders of the container
    time_row.set_style_local_bg_opa(lv.obj.PART.MAIN, lv.STATE.DEFAULT, lv.OPA.TRANSP)
    time_row.set_style_local_border_width(lv.obj.PART.MAIN, lv.STATE.DEFAULT, 0)
    time_row.set_style_local_pad_all(lv.obj.PART.MAIN, lv.STATE.DEFAULT, 0)
    time_row.set_style_local_pad_inner(lv.obj.PART.MAIN, lv.STATE.DEFAULT, 0)
    # put the whole group where you want
    time_row.align(status, lv.ALIGN.IN_LEFT_MID, 5, 0)   # change pos as needed

    hour_lbl  = lv.label(time_row)
    colon_lbl = lv.label(time_row)
    min_lbl   = lv.label(time_row)
    
    hour_lbl.set_style_local_text_color(lv.obj.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xCCCCCC))
    colon_lbl.set_style_local_text_color(lv.obj.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xCCCCCC))
    min_lbl.set_style_local_text_color(lv.obj.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xCCCCCC))

    hour_lbl.set_text("12")
    colon_lbl.set_text(":")
    min_lbl.set_text("34")
      
    previous_minute = ""
    previous_label = ""
    sec = 0
    
    batt = create_battery_widget(status)
    
    set_battery_widget(batt, 69, charging=False)
    
    '''
    def remove_button_style(btn):
        btn.set_style_local_border_width(lv.btn.PART.MAIN, lv.STATE.DEFAULT, 0)
        btn.set_style_local_outline_width(lv.btn.PART.MAIN, lv.STATE.DEFAULT, 0)
        btn.set_style_local_shadow_width(lv.btn.PART.MAIN, lv.STATE.DEFAULT, 0)
        btn.set_style_local_radius(lv.btn.PART.MAIN, lv.STATE.DEFAULT, 0)
        #btn.set_style_local_bg_opa(lv.btn.PART.MAIN, lv.STATE.DEFAULT, lv.OPA.TRANSP)

    # Left button
    var.btn_left = lv.btn(status)
    var.btn_left.set_size(40, STATUS_BAR_H)
    var.btn_left.align(status, lv.ALIGN.IN_LEFT_MID, 0, 0)
    var.btn_left.set_event_cb(nav_btn_event_cb)

    lbl_l = lv.label(var.btn_left)
    lbl_l.set_text(lv.SYMBOL.LEFT)
    lbl_l.align(var.btn_left, lv.ALIGN.CENTER, 0, 0)

    # Right button
    var.btn_right = lv.btn(status)
    var.btn_right.set_size(40, STATUS_BAR_H)
    var.btn_right.align(None, lv.ALIGN.IN_RIGHT_MID, 0, 0)
    var.btn_right.set_event_cb(nav_btn_event_cb)

    lbl_r = lv.label(var.btn_right)
    lbl_r.set_text(lv.SYMBOL.RIGHT)
    lbl_r.align(var.btn_right, lv.ALIGN.CENTER, 0, 0)
    
    # Remove outlines
    remove_button_style(var.btn_left)
    remove_button_style(var.btn_right)
    '''
    
    style_hidden = lv.style_t()
    style_hidden.init()
    style_hidden.set_text_opa(lv.STATE.DEFAULT, lv.OPA.TRANSP)

    style_visible = lv.style_t()
    style_visible.init()
    style_visible.set_text_opa(lv.STATE.DEFAULT, lv.OPA.COVER)
    
    '''
    def update_screen_label_cb(timer):
        nonlocal previous_label
            
        label = var.screen_names[var.current_idx]
        
        if label != previous_label:
            s = label
            screen_label.set_text(s)
            previous_label = label
            
        else:
            return
    '''
    def update_time_labels_cb(timer):
        nonlocal sec, previous_minute, batt
        # read actual time from your var
        rtc = var.system_data.time_rtc

        if rtc is not None and type(rtc) == tuple:
            hour = rtc[4]
            minute = rtc[5]
        else:
            hour = 12
            minute = 34
        
        sec += 1
        
        #set_hidden removes the label from ui rendering :(
        #colon_lbl.set_hidden(sec % 2 == 0)
        if sec % 2 == 0:
            # invisible but still takes space
            colon_lbl.set_style_local_text_opa(lv.label.PART.MAIN, lv.STATE.DEFAULT, lv.OPA.TRANSP)
        else:
            # visible
            colon_lbl.set_style_local_text_opa(lv.label.PART.MAIN, lv.STATE.DEFAULT, lv.OPA.COVER)
            
        set_battery_widget(batt, int(var.system_data.bat_percentage), var.system_data.charging)
            
        if minute != previous_minute:
            # format HH:MM with leading zeros
            #s = "{:02}  {:02}".format(hour, minute)
            s = "{:02}".format(hour)
            hour_lbl.set_text(s)

            s = "{:02}".format(minute)
            min_lbl.set_text(s)
            
            previous_minute = minute
            
        else:
            return
        
    # --- Update screen label in every 50ms ---
    #lv.task_create(update_screen_label_cb, 50, lv.TASK_PRIO.LOW, None)
    # --- Update time labels in every 1000ms ---
    lv.task_create(update_time_labels_cb, 1000, lv.TASK_PRIO.LOW, None)
