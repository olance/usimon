import uasyncio as asyncio
from machine import Pin

from primitives import launch
from primitives.pushbutton import Pushbutton
from ucollections import namedtuple
from uos import urandom
from urandom import choice, seed


class SimonApp:
    def __init__(self, *led_btn_pin_ids, speed: int = 0.8):
        """
        Initialize the Simon App with a list of led button pins to be used by the game.

        :param LedButtonPins led_btn_pin_ids: a list of LedButtonPins tuples
        """
        self.__speed = speed
        self.__leds = [LedButton(led_btn_pins) for led_btn_pins in led_btn_pin_ids]
        self.__sequence = []

    async def start_over(self):
        await self.boot_sequence()

        self.__reset_leds()
        self.__sequence = []

    async def run(self):
        await self.start_over()

        while True:
            seed(int.from_bytes(urandom(2), 'big'))
            await self.advance_sequence()
            await self.show_sequence()
            await self.playtime()
            await asyncio.sleep(0.5)

    def __reset_leds(self):
        for led in self.__leds:
            led.led_off()

    async def boot_sequence(self):
        self.__reset_leds()

        for _ in range(2):
            for led in self.__leds:
                led.led_on()
                await asyncio.sleep(0.3)
                led.led_off()

        await asyncio.sleep(0.3)

        for _ in range(4):
            for led in self.__leds:
                led.toggle_led()
            await asyncio.sleep(0.5)

    async def advance_sequence(self):
        self.__sequence.append(choice(self.__leds))

    async def show_sequence(self):
        self.__reset_leds()

        for led in self.__sequence:
            led.led_on()
            await asyncio.sleep(self.__speed / 2)
            led.led_off()
            await asyncio.sleep(self.__speed)

    async def playtime(self):
        expected_sequence = iter(self.__sequence)
        next_led = next(expected_sequence)
        next_move = asyncio.Event()
        lost = False

        def check_led(pressed_led):
            nonlocal next_led, lost

            # Don't process event when processing a previous one
            if next_move.is_set():
                return

            lost = pressed_led is not next_led

            try:
                next_led = next(expected_sequence)
            except StopIteration:
                next_led = None

            next_move.set()

        for led in self.__leds:
            led.on_released(check_led)

        # Stop looping once player has lost or sequence is exhausted
        while not lost and next_led is not None:
            await next_move.wait()
            next_move.clear()

        for led in self.__leds:
            led.on_released(None)

        if lost:
            await self.start_over()


LedButtonPins = namedtuple('LedButtonPins', ['led_pin_id', 'button_pin_id'])


class LedButton:
    def __init__(self, led_btn_pins: LedButtonPins):
        self.__led_pin = Pin(led_btn_pins.led_pin_id, Pin.OUT, value=0)
        self.__btn_pin = Pin(led_btn_pins.button_pin_id, Pin.IN, Pin.PULL_UP)

        self.__btn = Pushbutton(self.__btn_pin)
        self.__btn.press_func(self.__handle_pressed)
        self.__btn.release_func(self.__handle_released)
        self.__on_pressed_cb = None
        self.__on_released_cb = None

    def toggle_led(self):
        self.__led_pin.value(not self.__led_pin.value())

    def led_on(self):
        self.__led_pin.value(1)

    def led_off(self):
        self.__led_pin.value(0)

    def __handle_pressed(self):
        self.led_on()

        if self.__on_pressed_cb:
            launch(self.__on_pressed_cb, (self,))

    def on_pressed(self, cb):
        self.__on_pressed_cb = cb

    def __handle_released(self):
        self.led_off()

        if self.__on_released_cb:
            launch(self.__on_released_cb, (self,))

    def on_released(self, cb):
        self.__on_released_cb = cb
