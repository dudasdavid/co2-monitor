from micropython import const  # NOQA
import lvgl as lv
import SDL
import time

_WIDTH = const(480)
_HEIGHT = const(272)

def init_display():
  lv.init()
  SDL.init(w=_WIDTH, h=_HEIGHT)

  # Display
  disp_buf = lv.disp_buf_t()
  buf = bytearray(_WIDTH * 20 * 4)
  disp_buf.init(buf, None, len(buf) // 4)

  disp_drv = lv.disp_drv_t()
  disp_drv.init()
  disp_drv.buffer = disp_buf
  disp_drv.flush_cb = SDL.monitor_flush
  disp_drv.hor_res = _WIDTH
  disp_drv.ver_res = _HEIGHT
  disp_drv.register()

  # Mouse
  indev_drv = lv.indev_drv_t()
  indev_drv.init()
  indev_drv.type = lv.INDEV_TYPE.POINTER
  indev_drv.read_cb = SDL.mouse_read
  indev_drv.register()

def main():

  init_display()

  from ui import ui_generic
  from ui import ui_chart

  top_layer = lv.layer_top()

  ui_generic.create_status_bar(top_layer)

  # Test screen
  scr1 = ui_chart.create_co2_chart(alt = False)

  lv.scr_load(scr1)

  '''
  scr = lv.obj()
  label = lv.label(scr)
  label.set_text("LVGL 7.11 sim works")
  label.align(scr, lv.ALIGN.CENTER, 0, 0)
  lv.scr_load(scr)
  '''

  while True:
      #SDL.check()
      lv.task_handler()
      time.sleep_ms(5)


if __name__ == "__main__" or __name__ == "simulator":
  main()