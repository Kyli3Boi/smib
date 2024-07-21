from lib.ulogging import uLogger
from asyncio import create_task

class UIState:
    """
    State machine for the SMIBHID user interface.
    """
    def __init__(self, hid: object, space_state) -> None:
        """
        Pass HID instance for global UI state reference.
        Pass SpaceState instance to allow space open and closed buttons to work
        in all UIs.
        """
        self.hid = hid
        self.space_state = space_state
        self.log = uLogger("UIState")

    def on_enter(self) -> None:
        """
        Default actions for entering a UI state.
        """
        self.log.info(f"Entering {self.__class__.__module__} {self.__class__.__name__} State")

    def on_exit(self) -> None:
        """
        Default actions for exiting a UI state.
        """
        self.log.info(f"Exiting {self.__class__.__module__} {self.__class__.__name__} State")

    def transition_to(self, state: 'UIState') -> None:
        """
        Move to a new UI state.
        """
        self.on_exit()
        self.hid.set_ui_state(state)
        state.on_enter()

    async def _async_close_space(self) -> None:
        """
        Default action for closing the space.
        """
        self.space_state.flash_task = create_task(self.space_state.space_closed_led.async_constant_flash(4))
        try:
            await self.space_state.slack_api.async_space_closed()
            self.space_state.flash_task.cancel()
            self.space_state.set_output_space_closed()
            create_task(self.space_state.async_update_space_state_output())
        except Exception as e:
            self.log.error(
                f"An exception was encountered trying to set SMIB space state: {e}"
            )
            self.space_state.flash_task.cancel()
            self.space_state.space_closed_led.off()
    
    async def _async_open_space(self, open_for_hours: int = 0) -> None:
        """
        Default action for opening the space.
        """
        self.space_state.flash_task = create_task(self.space_state.space_open_led.async_constant_flash(4))
        try:
            await self.space_state.slack_api.async_space_open(open_for_hours)
            self.space_state.flash_task.cancel()
            self.space_state.set_output_space_open()
            create_task(self.space_state.async_update_space_state_output())
        except Exception as e:
            self.log.error(
                f"An exception was encountered trying to set SMIB space state: {e}"
            )
            self.space_state.flash_task.cancel()
            self.space_state.space_open_led.off()
    
    async def async_on_space_closed_button(self) -> None:
        """
        Close space when space closed button pressed outside of space state UI.
        """
        await self._async_close_space()
    
    async def async_on_space_open_button(self) -> None:
        """
        Open space with no hours when when space open button pressed outside of space state UI.
        """
        await self._async_open_space()
