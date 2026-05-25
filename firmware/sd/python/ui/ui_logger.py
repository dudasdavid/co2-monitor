import lvgl as lv
from math import ceil
from ui import ui_generic as ui

# ---- Global variables ----
if ui.SIMULATOR:
    import fake_shared_variables as var
else:
    import shared_variables as var

def create_console_log(alt=False):
    
    scr = lv.obj()
        
    BTN_BAR_H = 28
    
    # Root container
    root = lv.cont(scr, None)
    root.set_size(ui.SCREEN_W, ui.SCREEN_H-ui.STATUS_BAR_H)
    root.align(scr, lv.ALIGN.IN_TOP_MID, 0, ui.STATUS_BAR_H)
    root.set_fit(lv.FIT.NONE)
    root.set_layout(lv.LAYOUT.COLUMN_MID)   # vertical stacking
    
    # 1) Create the scrollable page
    page = lv.page(root)
    page.set_size(ui.SCREEN_W, ui.SCREEN_H-ui.STATUS_BAR_H-BTN_BAR_H)
    #page.align(scr, lv.ALIGN.IN_TOP_MID, 0, 0)
    page.set_scrollbar_mode(lv.SCROLLBAR_MODE.AUTO)
    #page.set_fit2(lv.FIT.FLOOD, lv.FIT.PARENT)
    #page.set_scrl_fit2(lv.FIT.FLOOD, lv.FIT.TIGHT)   # horizontal fill, vertical = content height
    scrl = page.get_child(None)
    scrl.set_width(ui.SCREEN_W)
    
    scrl.set_style_local_pad_left(lv.cont.PART.MAIN, lv.STATE.DEFAULT, 0)
    scrl.set_style_local_pad_right(lv.cont.PART.MAIN, lv.STATE.DEFAULT, 0)
    scrl.set_style_local_pad_top(lv.cont.PART.MAIN, lv.STATE.DEFAULT, 0)
    scrl.set_style_local_pad_bottom(lv.cont.PART.MAIN, lv.STATE.DEFAULT, 0)

    scrl.set_style_local_border_width(lv.cont.PART.MAIN, lv.STATE.DEFAULT, 0)
    scrl.set_style_local_margin_left(lv.cont.PART.MAIN, lv.STATE.DEFAULT, 0)
    scrl.set_style_local_margin_right(lv.cont.PART.MAIN, lv.STATE.DEFAULT, 0)

    scrl.set_x(0)
    scrl.set_width(ui.SCREEN_W)

    # 2) Create the label inside the page
    log_label = lv.label(page)
    log_label.set_long_mode(lv.label.LONG.BREAK)  # multi-line wrap
    #log_label.set_width(page.get_width_fit() - 10)      # <-- key: match usable page width
    log_label.set_width(ui.SCREEN_W)
    log_label.set_x(0)
    log_label.set_text("")  # empty initially
    log_label.set_recolor(True)

    # --- Apply fonts style ---
    font_style = lv.style_t()
    font_style.init()
    
    # Load font baked into firmware
    font_style.set_text_font(lv.STATE.DEFAULT, lv.font_consolas_12)
    
    # Loading external font crashes on my MCU at the moment only baking it into the firmware is the only way to make it work
    #from drivers import fs_driver
    #fs_drv = lv.fs_drv_t()
    #fs_driver.fs_register(fs_drv, 'S')
    #custom_font = lv.font_load("S:/font-PHT-en-20.bin")
    #font_style.set_text_font(lv.STATE.DEFAULT, custom_font)
    
    log_label.add_style(lv.label.PART.MAIN, font_style)

    # --- Apply indentation within the label ---
    style_label_indent = lv.style_t()
    style_label_indent.init()

    style_label_indent.set_pad_left(lv.STATE.DEFAULT, 0)   # ← adjust: 2–6 px usually perfect
    style_label_indent.set_pad_right(lv.STATE.DEFAULT, 2)
    style_label_indent.set_pad_top(lv.STATE.DEFAULT, 2)
    style_label_indent.set_pad_bottom(lv.STATE.DEFAULT, 2)
    
    log_label.add_style(lv.label.PART.MAIN, style_label_indent)

    log_label.set_style_local_pad_left(lv.label.PART.MAIN, lv.STATE.DEFAULT, 0)
    log_label.set_style_local_pad_right(lv.label.PART.MAIN, lv.STATE.DEFAULT, 0)
    log_label.set_style_local_pad_top(lv.label.PART.MAIN, lv.STATE.DEFAULT, 0)
    log_label.set_style_local_pad_bottom(lv.label.PART.MAIN, lv.STATE.DEFAULT, 0)

    log_label.set_style_local_margin_left(lv.label.PART.MAIN, lv.STATE.DEFAULT, 0)
    log_label.set_style_local_margin_right(lv.label.PART.MAIN, lv.STATE.DEFAULT, 0)

    log_label.set_style_local_border_width(lv.label.PART.MAIN, lv.STATE.DEFAULT, 0)
    log_label.set_x(0)

    # --- Bottom button bar ---
    bar = lv.cont(root, None)
    bar.set_size(ui.SCREEN_W, BTN_BAR_H)
    bar.set_fit(lv.FIT.NONE)
    bar.set_layout(lv.LAYOUT.ROW_MID)       # 4 buttons in a row
    
    btn_w = ui.SCREEN_W // 5
    
    # Padding removal style
    style_nopad = lv.style_t()
    style_nopad.init()
    style_nopad.set_pad_all(lv.STATE.DEFAULT, 0)
    style_nopad.set_pad_inner(lv.STATE.DEFAULT, 0)
    
    # Create a dark theme
    style_dark = lv.style_t()
    style_dark.init()

    # dark gray background
    style_dark.set_bg_color(lv.STATE.DEFAULT, lv.color_hex(0x202020))
    style_dark.set_bg_grad_color(lv.STATE.DEFAULT, lv.color_hex(0x202020))
    style_dark.set_bg_opa(lv.STATE.DEFAULT, lv.OPA.COVER)

    # text color
    style_dark.set_text_color(lv.STATE.DEFAULT, lv.color_hex(0xFFFFFF))

    # border
    style_dark.set_border_width(lv.STATE.DEFAULT, 1)
    style_dark.set_border_color(lv.STATE.DEFAULT, lv.color_hex(0x404040))

    # rectangular
    style_dark.set_radius(lv.STATE.DEFAULT, 0)

    # turn off focus highlight
    style_dark.set_outline_width(lv.STATE.FOCUSED, 0)
    style_dark.set_shadow_width(lv.STATE.FOCUSED, 0)

    style_dark.set_border_color(
        lv.STATE.FOCUSED,
        lv.color_hex(0x404040)
    )

    style_dark.set_bg_color(
        lv.STATE.FOCUSED,
        lv.color_hex(0x202020)
    )

    style_dark.set_bg_grad_color(
        lv.STATE.FOCUSED,
        lv.color_hex(0x202020)
    )

    # Apply no padding
    root.add_style(lv.cont.PART.MAIN, style_nopad)
    page.add_style(lv.page.PART.BG, style_nopad)
    page.add_style(lv.page.PART.SCROLLABLE, style_nopad)
    bar.add_style(lv.cont.PART.MAIN, style_nopad)
    
    # Apply dark style
    root.add_style(lv.cont.PART.MAIN, style_dark)
    page.add_style(lv.page.PART.BG, style_dark)
    page.add_style(lv.page.PART.SCROLLABLE, style_dark)
    bar.add_style(lv.cont.PART.MAIN, style_dark)
    
    style_log_text = lv.style_t()
    style_log_text.init()
    style_log_text.set_text_color(lv.STATE.DEFAULT, lv.color_hex(0xFFFFFF))
    style_log_text.set_bg_opa(lv.STATE.DEFAULT, lv.OPA.TRANSP)
    style_log_text.set_border_width(lv.STATE.DEFAULT, 0)
    style_log_text.set_pad_all(lv.STATE.DEFAULT, 0)

    log_label.add_style(lv.label.PART.MAIN, style_log_text)
    
    def reset_log_view():
        var.logger_error = []
        var.logger_label_prev = ""

        log_label.set_text("")
        log_label.set_width(page.get_width_fit())
        log_label.set_pos(0, 0)

        lv.task_handler()

        scrl.set_size(page.get_width_fit(), page.get_height_fit())
        scrl.set_pos(0, 0)

        page.scroll_ver(-10000)
        scrl.set_y(0)
    
    def make_btn(txt, cb):
        b = lv.btn(bar, None)
        b.set_size(btn_w, BTN_BAR_H)
        b.set_checkable(True)
        b.add_style(lv.btn.PART.MAIN, style_nopad)
        b.set_event_cb(cb)

        l = lv.label(b, None)
        l.set_text(txt)
        return b

    def pause_button_cb(obj, event):
        if event == lv.EVENT.CLICKED:
            if obj.get_state() & lv.STATE.CHECKED: 
                print("Pause is ON")
                var.logger_paused = True
            else:
                print("Pause is OFF")
                var.logger_paused = False

    def clear_button_cb(obj, event):
        if event == lv.EVENT.CLICKED:
            reset_log_view()
            btn2.clear_state(lv.STATE.CHECKED)

    btn1 = make_btn("Pause", pause_button_cb)
    btn2 = make_btn("Clear", clear_button_cb)
               
    def update_log_cb(timer):
        nonlocal log_label
        if lv.scr_act() != scr:
            return

        logger_label = "\n".join(var.logger_error)

        if logger_label != var.logger_label_prev:

            # remember current scroll before resizing
            old_y = scrl.get_y()

            log_label.set_text(logger_label)
            log_label.set_width(ui.SCREEN_W)
            log_label.set_pos(0, 0)

            lv.task_handler()

            new_h = log_label.get_height()
            if new_h < page.get_height_fit():
                new_h = page.get_height_fit()

            scrl.set_height(new_h)

            min_y = page.get_height_fit() - scrl.get_height()
            if min_y > 0:
                min_y = 0

            if var.logger_paused:
                # keep the visible position unchanged
                if old_y < min_y:
                    old_y = min_y
                if old_y > 0:
                    old_y = 0
                scrl.set_y(old_y)
            else:
                # live mode: follow bottom
                scrl.set_y(min_y)

            var.logger_label_prev = logger_label
        
    # --- Update time in every 1000ms ---
    lv.task_create(update_log_cb, 1000, lv.TASK_PRIO.LOW, None)
    
    # --- Enable swipe on the full screen and table ---
    scr.set_event_cb(ui.swipe_event_cb)
    scrl = page.get_child(None)
    scrl.set_event_cb(ui.swipe_event_table_on_page_cb(page))

    style_btn = lv.style_t()
    style_btn.init()
    # rectangular
    style_btn.set_radius(lv.STATE.DEFAULT, 0)
    # tighter padding
    style_btn.set_pad_top(lv.STATE.DEFAULT, 0)
    style_btn.set_pad_bottom(lv.STATE.DEFAULT, 0)
    style_btn.set_pad_left(lv.STATE.DEFAULT, 0)
    style_btn.set_pad_right(lv.STATE.DEFAULT, 0)
    # optional cleaner look
    style_btn.set_border_width(lv.STATE.DEFAULT, 1)
    # checked color
    style_btn.set_pad_inner(lv.STATE.DEFAULT, 0)
    style_btn.set_bg_color(lv.STATE.CHECKED, lv.color_hex(0x5050FF))
    style_btn.set_text_color(lv.STATE.CHECKED, lv.color_hex(0xFFFFFF))
    # Pressed color
    style_btn.set_bg_color(lv.STATE.PRESSED, lv.color_hex(0x303030))
    style_btn.set_bg_grad_color(lv.STATE.PRESSED, lv.color_hex(0x303030))
    style_btn.set_border_color(lv.STATE.PRESSED, lv.color_hex(0x505050))
    style_btn.set_text_color(lv.STATE.PRESSED, lv.color_hex(0xFFFFFF))
    # Turn off focus highlight
    style_btn.set_outline_width(lv.STATE.FOCUSED, 0)
    style_btn.set_shadow_width(lv.STATE.FOCUSED, 0)

    style_btn.set_border_color(
        lv.STATE.FOCUSED,
        lv.color_hex(0x505050)
    )

    style_btn.set_bg_color(
        lv.STATE.CHECKED | lv.STATE.FOCUSED,
        lv.color_hex(0x5050FF)
    )

    style_btn.set_bg_grad_color(
        lv.STATE.CHECKED | lv.STATE.FOCUSED,
        lv.color_hex(0x5050FF)
    )

    btn1.add_style(lv.btn.PART.MAIN, style_btn)
    btn2.add_style(lv.btn.PART.MAIN, style_btn)
    btn1.add_style(lv.btn.PART.MAIN, style_dark)
    btn2.add_style(lv.btn.PART.MAIN, style_dark)

    # --- Add screen to screens ---  
    screen_name = "Log"
    if not alt:
        var.screens.append(scr)
        var.screen_names.append(screen_name)
    else:
        var.screens_alt.append(scr)
        var.screen_names_alt.append(screen_name)
    
    return scr 
