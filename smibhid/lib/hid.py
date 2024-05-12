from ulogging import uLogger
import config
from button import Button
from asyncio import Event, create_task, get_event_loop, sleep
from utils import StatusLED
from slack_api import Wrapper
from lib.networking import WirelessNetwork
from constants import OPEN, CLOSED

class HID:
    
    def __init__(self, loglevel: int) -> None:
        """
        Human Interface Device for event spaces providing buttons and status LEDs for space open state.
        Create HID instance and then run startup() to start services for button monitoring and LED output.
        """
        self.log = uLogger("HID", loglevel)
        self.space_open_button_event = Event()
        self.space_closed_button_event = Event()
        self.open_button = Button(loglevel, config.SPACE_OPEN_BUTTON, "Space_open", self.space_open_button_event)
        self.closed_button = Button(loglevel, config.SPACE_CLOSED_BUTTON, "Space_closed", self.space_closed_button_event)
        self.space_open_led = StatusLED(loglevel, config.SPACE_OPEN_LED)
        self.space_closed_led = StatusLED(loglevel, config.SPACE_CLOSED_LED)
        self.space_open_led = StatusLED(loglevel, config.SPACE_OPEN_LED)
        self.space_closed_led = StatusLED(loglevel, config.SPACE_CLOSED_LED)
        self.space_open_led.off()
        self.space_closed_led.off()
        self.wifi = WirelessNetwork(log_level=loglevel)
        self.wifi = WirelessNetwork(log_level=loglevel)
        self.wifi.configure_wifi()
        self.slack_api = Wrapper(loglevel, self.wifi)
        self.loop_running = False
        self.space_state = None
        
        self.space_state_poll_frequency = config.space_state_poll_frequency_s
        if self.space_state_poll_frequency != 0 and self.space_state_poll_frequency < 5:
            self.space_state_poll_frequency = 5

    def startup(self) -> None:
        """
        Initialise all aysnc services for the HID.
        """
        self.log.info("Starting HID")
        self.log.info("Starting HID")
        self.log.info(f"Starting {self.open_button.get_name()} button watcher")
        create_task(self.open_button.wait_for_press())
        self.log.info(f"Starting {self.closed_button.get_name()} button watcher")
        create_task(self.closed_button.wait_for_press())
        self.log.info(f"Starting {self.open_button.get_name()} button pressed event catcher")
        create_task(self.async_space_opened_watcher())
        self.log.info(f"Starting {self.closed_button.get_name()} button pressed event catcher")
        create_task(self.async_space_closed_watcher())
        self.log.info("Starting network monitor")
        create_task(self.wifi.network_monitor())
        if self.space_state_poll_frequency != 0:
            self.log.info(f"Starting space state poller with frequency of {self.space_state_poll_frequency} seconds")
            create_task(self.async_space_state_watcher())
        else:
            self.log.info("Space state poller disabled by config")

        self.log.info("Entering main loop")        
        self.log.info("Entering main loop")        
        self.loop_running = True
        loop = get_event_loop()
        loop.run_forever()

    def set_output_space_open(self) -> None:
        """Set LED's display etc to show the space as open"""
        self.space_open_led.on()
        self.space_closed_led.off()
        self.log.info("Space state is open.")
    
    def set_output_space_closed(self) -> None:
        """Set LED's display etc to show the space as closed"""
        self.space_open_led.off()
        self.space_closed_led.on()
        self.log.info("Space state is closed.")

    def set_output_space_none(self) -> None:
        """Set LED's display etc to show the space as none"""
        self.space_open_led.off()
        self.space_closed_led.off()
        self.log.info("Space state is none.")
    
    async def async_update_space_state_output(self) -> None:
        """Checks space state from server and sets SMIDHID output to reflect current space state, including errors if space state not available."""
        try:
            space_state = await self.slack_api.async_get_space_state()
            self.log.info(f"Space state is: {space_state}")
            if space_state != self.space_state:
                self.space_state = space_state
                if space_state is OPEN:
                    self.set_output_space_open()
                elif space_state is CLOSED:
                    self.set_output_space_closed()
                elif space_state is None:
                    self.set_output_space_none()
                else:
                    raise ValueError("Space state is not an expected value")
        except Exception as e:
            self.log.error(f"Error encountered polling updating space state: {e}")
            raise
    
    async def async_space_opened_watcher(self) -> None:
        """
        Coroutine to be added to the async loop for watching for the space open button press event and taking appropriate actions.
        """
        while True:
            await self.space_open_button_event.wait()
            self.space_open_button_event.clear()
            flash_task = create_task(self.space_open_led.async_constant_flash(4))
            try:
                await self.slack_api.async_space_open()
                flash_task.cancel()
                self.set_output_space_open()
                await self.async_update_space_state_output()
            except Exception as e:
                self.log.error(f"An exception was encountered trying to set SMIB space state: {e}")
                flash_task.cancel()
                self.space_open_led.off()

    async def async_space_closed_watcher(self) -> None:
        """
        Coroutine to be added to the async loop for watching for the space close button press event and taking appropriate actions.
        """
        while True:
            await self.space_closed_button_event.wait()
            self.space_closed_button_event.clear()
            flash_task = create_task(self.space_closed_led.async_constant_flash(4))
            try:
                await self.slack_api.async_space_closed()
                flash_task.cancel()
                self.set_output_space_closed()
                await self.async_update_space_state_output()
            except Exception as e:
                self.log.error(f"An exception was encountered trying to set SMIB space state: {e}")
                flash_task.cancel()
                self.space_closed_led.off()

    async def async_space_state_watcher(self) -> None:
        """
        Coroutine to frequently poll the space state from the slack server and update SMIBHID output if the state has changed.
        """
        while True:
            self.log.info("Polling space state")
            try:
                await self.async_update_space_state_output()
            except Exception as e:
                self.log.error(f"State poller encountered an error updating space state: {e}")
            finally:
                await sleep(self.space_state_poll_frequency)
