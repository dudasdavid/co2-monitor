import lvgl as lv
from math import ceil
from ui import ui_generic as ui

# ---- Global variables ----
import shared_variables as var


def create_sensor_cards_screen(alt=False):
    scr = lv.obj()

    scr.set_style_local_bg_color(
        scr.PART.MAIN,
        lv.STATE.DEFAULT,
        lv.color_hex(0x050805)
    )

    page = lv.cont(scr)
    page.set_size(ui.SCREEN_W, ui.SCREEN_H - ui.STATUS_BAR_H)
    page.align(scr, lv.ALIGN.IN_BOTTOM_MID, 0, 0)
    page.set_layout(lv.LAYOUT.OFF)
    page.set_fit2(lv.FIT.NONE, lv.FIT.NONE)
    page.set_style_local_bg_opa(lv.cont.PART.MAIN, lv.STATE.DEFAULT, lv.OPA.TRANSP)
    page.set_style_local_border_width(lv.cont.PART.MAIN, lv.STATE.DEFAULT, 0)
    page.set_style_local_pad_all(lv.cont.PART.MAIN, lv.STATE.DEFAULT, 0)

    def make_non_interactive(obj):
        obj.set_click(False)
        obj.set_drag(False)
        
    make_non_interactive(page)

    CARD_W = ui.SCREEN_W // 3          # 160
    CARD_H = (ui.SCREEN_H - ui.STATUS_BAR_H) // 2   # 124
    ARC_SIZE = 110

    GREEN = lv.color_hex(0x00ff66)
    YELLOW = lv.color_hex(0xffcc00)
    RED = lv.color_hex(0xff3333)
    DARK_CARD = lv.color_hex(0x101510)
    DARK_ARC = lv.color_hex(0x263026)
    WHITE = lv.color_hex(0xffffff)
    MUTED = lv.color_hex(0x9aa59a)

    cards = []

    def clamp(v, lo, hi):
        if v < lo:
            return lo
        if v > hi:
            return hi
        return v

    def safe_value(v):
        if v is None:
            return None
        try:
            return float(v)
        except:
            return None

    def color_low_is_good(v, green_until, yellow_until):
        if v is None:
            return MUTED
        if v <= green_until:
            return GREEN
        elif v <= yellow_until:
            return YELLOW
        else:
            return RED

    def color_comfort_zone(v, low_red, low_yellow, high_yellow, high_red):
        if v is None:
            return MUTED
        if v < low_red:
            return RED
        elif v < low_yellow:
            return YELLOW
        elif v <= high_yellow:
            return GREEN
        elif v <= high_red:
            return YELLOW
        else:
            return RED

    def create_card(idx, name, unit, getter, vmin, vmax, color_func, decimals=0):
        row = idx // 3
        col = idx % 3

        cont = lv.cont(page)
        cont.set_size(CARD_W - 8, CARD_H - 8)
        cont.set_pos(col * CARD_W + 4, row * CARD_H + 4)
        cont.set_layout(lv.LAYOUT.OFF)
        cont.set_fit2(lv.FIT.NONE, lv.FIT.NONE)

        cont.set_style_local_bg_color(lv.cont.PART.MAIN, lv.STATE.DEFAULT, DARK_CARD)
        cont.set_style_local_bg_opa(lv.cont.PART.MAIN, lv.STATE.DEFAULT, lv.OPA.COVER)
        cont.set_style_local_radius(lv.cont.PART.MAIN, lv.STATE.DEFAULT, 10)
        cont.set_style_local_border_width(lv.cont.PART.MAIN, lv.STATE.DEFAULT, 1)
        cont.set_style_local_border_color(lv.cont.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0x203020))
        cont.set_style_local_pad_all(lv.cont.PART.MAIN, lv.STATE.DEFAULT, 0)

        # Disable focus/click highlight
        cont.set_click(False)

        cont.set_style_local_outline_width(
            lv.cont.PART.MAIN,
            lv.STATE.FOCUSED,
            0
        )

        cont.set_style_local_outline_width(
            lv.cont.PART.MAIN,
            lv.STATE.DEFAULT,
            0
        )

        cont.set_style_local_border_width(
            lv.cont.PART.MAIN,
            lv.STATE.FOCUSED,
            1
        )

        # Create arcs for measurements
        arc = lv.arc(cont)
        arc.set_size(ARC_SIZE, ARC_SIZE)
        arc.align(cont, lv.ALIGN.CENTER, 0, 0)

        arc.set_range(0, 100)
        arc.set_value(0)

        # Start from 12 o'clock instead of 3 o'clock
        arc.set_bg_angles(270, 269)
        arc.set_angles(270, 270)

        # Remove white/default background square
        arc.set_style_local_bg_opa(lv.arc.PART.BG, lv.STATE.DEFAULT, lv.OPA.TRANSP)
        arc.set_style_local_border_width(lv.arc.PART.BG, lv.STATE.DEFAULT, 0)
        arc.set_style_local_pad_all(lv.arc.PART.BG, lv.STATE.DEFAULT, 0)

        # Arc background circle
        arc.set_style_local_line_width(lv.arc.PART.BG, lv.STATE.DEFAULT, 9)
        arc.set_style_local_line_color(lv.arc.PART.BG, lv.STATE.DEFAULT, DARK_ARC)
        arc.set_style_local_line_opa(lv.arc.PART.BG, lv.STATE.DEFAULT, lv.OPA.COVER)

        # Arc filled indicator
        arc.set_style_local_line_width(lv.arc.PART.INDIC, lv.STATE.DEFAULT, 9)
        arc.set_style_local_line_color(lv.arc.PART.INDIC, lv.STATE.DEFAULT, GREEN)
        arc.set_style_local_line_opa(lv.arc.PART.INDIC, lv.STATE.DEFAULT, lv.OPA.COVER)

        # Hide knob if your LVGL build has it
        try:
            arc.set_style_local_bg_opa(lv.arc.PART.KNOB, lv.STATE.DEFAULT, lv.OPA.TRANSP)
            arc.set_style_local_border_width(lv.arc.PART.KNOB, lv.STATE.DEFAULT, 0)
        except:
            pass

        title = lv.label(cont)
        title.set_text(name)
        title.set_style_local_text_color(lv.label.PART.MAIN, lv.STATE.DEFAULT, MUTED)
        title.set_style_local_text_font(lv.label.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_10)
        title.align(cont, lv.ALIGN.CENTER, 0, -30)

        value_label = lv.label(cont)
        value_label.set_text("--")
        value_label.set_style_local_text_color(lv.label.PART.MAIN, lv.STATE.DEFAULT, WHITE)
        value_label.set_style_local_text_font(lv.label.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_16) # This should be bigger later
        value_label.align(cont, lv.ALIGN.CENTER, 0, 0)

        unit_label = lv.label(cont)
        unit_label.set_text(unit)
        unit_label.set_style_local_text_color(lv.label.PART.MAIN, lv.STATE.DEFAULT, MUTED)
        unit_label.set_style_local_text_font(lv.label.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_10)
        unit_label.align(cont, lv.ALIGN.CENTER, 0, 32)

        card = {
            "arc": arc,
            "value_label": value_label,
            "getter": getter,
            "vmin": vmin,
            "vmax": vmax,
            "color_func": color_func,
            "decimals": decimals,
            "last_txt": None,
            "last_pct": None,
            "last_color": None,
        }

        make_non_interactive(cont)
        make_non_interactive(arc)
        make_non_interactive(title)
        make_non_interactive(value_label)
        make_non_interactive(unit_label)

        cards.append(card)

    create_card(
        0, "TEMP", "°C",
        lambda: var.sensor_data.temp_aht21,
        0, 50,
        lambda v: color_comfort_zone(v, 16, 19, 26, 30),
        1
    )

    create_card(
        1, "HUM", "%",
        lambda: var.sensor_data.humidity_aht21,
        0, 100,
        lambda v: color_comfort_zone(v, 25, 35, 60, 70),
        0
    )

    create_card(
        2, "CO2", "ppm",
        lambda: var.sensor_data.co2_scd41,
        400, 2500,
        lambda v: color_low_is_good(v, 1000, 1500),
        0
    )

    create_card(
        3, "TVOC", "ppb",
        lambda: var.sensor_data.tvoc_ens160,
        0, 1000,
        lambda v: color_low_is_good(v, 250, 500),
        0
    )

    create_card(
        4, "PM2.5", "ug/m3",
        lambda: var.sensor_data.pm2_5_sps30,
        0, 100,
        lambda v: color_low_is_good(v, 15, 35),
        0
    )

    create_card(
        5, "PM10", "ug/m3",
        lambda: var.sensor_data.pm10_sps30,
        0, 150,
        lambda v: color_low_is_good(v, 45, 100),
        0
    )

    def update_cards_cb(task):
        for c in cards:
            v = safe_value(c["getter"]())

            if v is None:
                txt = "--"
                pct = 0
            else:
                if c["decimals"] == 0:
                    txt = str(int(v))
                else:
                    txt = "{:.1f}".format(v)

                pct = int((v - c["vmin"]) * 100 / (c["vmax"] - c["vmin"]))
                pct = clamp(pct, 0, 100)

            color = c["color_func"](v)

            if txt != c["last_txt"]:
                c["value_label"].set_text(txt)
                c["value_label"].align(c["value_label"].get_parent(), lv.ALIGN.CENTER, 0, 0)
                c["last_txt"] = txt

            if pct != c["last_pct"]:
                c["arc"].set_angles(270, 270 + int(pct * 360 / 100))
                c["last_pct"] = pct

            if color != c["last_color"]:
                c["arc"].set_style_local_line_color(lv.arc.PART.INDIC, lv.STATE.DEFAULT, color)
                c["value_label"].set_style_local_text_color(lv.label.PART.MAIN, lv.STATE.DEFAULT, color)
                c["last_color"] = color

    lv.task_create(update_cards_cb, 1000, lv.TASK_PRIO.LOW, None)
    update_cards_cb(None)

    scr.set_event_cb(ui.swipe_event_cb)
    page.set_event_cb(ui.swipe_event_cb)

    screen_name = "Sensors"
    if not alt:
        var.screens.append(scr)
        var.screen_names.append(screen_name)
    else:
        var.screens_alt.append(scr)
        var.screen_names_alt.append(screen_name)

    return scr