import uasyncio as asyncio
from app import SimonApp, LedButtonPins

LED_BUTTON_RED = LedButtonPins(4, 2)
LED_BUTTON_GREEN = LedButtonPins(17, 16)
LED_BUTTON_BLUE = LedButtonPins(18, 5)


def set_global_exception():
    def handle_exception(_, context):
        import sys
        sys.print_exception(context["exception"])
        sys.exit()

    loop = asyncio.get_event_loop()
    loop.set_exception_handler(handle_exception)


async def main():
    set_global_exception()
    app = SimonApp(LED_BUTTON_RED, LED_BUTTON_GREEN, LED_BUTTON_BLUE)
    await app.run()


try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()  # Clear retained state
