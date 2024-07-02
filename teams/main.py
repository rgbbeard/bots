from thread_maid import ThreadMaid
from time import sleep
import keyboard
from random import randint
from gui_class import *

debug = True
can_run = not debug
w = None
t = None
button_status_text = None
sw = 0
keyboard_thread = ThreadMaid()
mouse_thread = ThreadMaid()
status_thread = ThreadMaid()
gui_thread = ThreadMaid()


def randpos():
	global sw

	mx = randint(30, sw-30)
	my = mx+5

	return mx, my


def change_status():
	global can_run

	can_run = not can_run


def keyboard_fn():
	global can_run

	while True:
		try:
			if keyboard.is_pressed("f9"):
				change_status()
			elif keyboard.is_pressed("esc") or keyboard.is_pressed("escape"):
				exit(0)
		except Exception as e:
			print(e)


def mouse_fn():
	global can_run, t

	while True:
		if can_run:
			mx, my = randpos()

			t.event_generate('<Motion>', warp=True, x=mx, y=my)
			sleep(2)


def status_fn():
	global can_run, w, t, button_status_text

	while True:
		if button_status_text is not None:
			if can_run:
				button_status_text.set("Attivo")
			else:
				button_status_text.set("Fermo")


def gui_fn():
	global w, t, sw, button_status_text

	if w is None:
		w = Window(window_name="TeamSaver", window_size="100x100")
		t = w.get_root()
		sw = t.winfo_screenwidth()
		button_status_text = tkinter.StringVar()

	button_status = tkinter.Button(
		t,
		textvariable=button_status_text,
		command=partial(change_status),
		width=100,
		height=100
	)
	button_status.pack(side="left")
	w.display()
	exit(0)


keyboard_thread.setup(target=keyboard_fn).run()
mouse_thread.setup(target=mouse_fn).run()
status_thread.setup(target=status_fn).run()
gui_thread.setup(target=gui_fn).run()