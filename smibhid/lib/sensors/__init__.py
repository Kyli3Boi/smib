from asyncio import create_task, sleep
from machine import I2C
from config import SENSOR_MODULES
from lib.ulogging import uLogger
from lib.sensors.SGP30 import SGP30
from lib.sensors.BME280 import BME280
from lib.sensors.SCD30 import SCD30
from lib.sensors.sensor_module import SensorModule

class Sensors:
    def __init__(self, i2c: I2C) -> None:
        self.log = uLogger("Sensors")
        self.i2c = i2c
        self.SENSOR_MODULES = SENSOR_MODULES
        self.available_modules: dict[str, SensorModule] = {}
        self.configured_modules: dict[str, SensorModule] = {}
        modules = ["SGP30", "BME280", "SCD30"]
        self.load_modules(modules)
        self._configure_modules()   

    def load_modules(self, modules: list[str]) -> None:
        """
        Load a list of sensor modules by name passed as a list of strings.
        """
        for module in modules:
            try:
                self.log.info(f"Loading {module} sensor module")
                module_class = globals().get(module)
                if module_class is None:
                    raise ValueError(f"Sensor module '{module}' not imported.")
                self.available_modules[module] = module_class(self.i2c)
                self.log.info(f"Loaded {module} sensor module")

            except RuntimeError as e:
                self.log.error(f"Failed to load {module} sensor module: {e}")

            except Exception as e:
                self.log.error(f"Failed to load {module} sensor module: {e}")
    
    def _configure_modules(self) -> None:
        self.log.info(f"Attempting to locate drivers for: {self.SENSOR_MODULES}")
        for sensor_module in self.SENSOR_MODULES:
            if sensor_module in self.available_modules:
                self.log.info(f"Found driver for {sensor_module}")
                self.configured_modules[sensor_module] = self.available_modules[sensor_module]
                self.log.info(f"Configured {sensor_module} sensor module")
                self.log.info(f"Available sensors: {self.get_sensors(sensor_module)}")
            else:
                self.log.error(f"Driver not found for {sensor_module}")

        self.log.info(f"Configured modules: {self.get_modules()}")

    def startup(self) -> None:
        self.log.info(f"Starting sensors: {self.configured_modules}")
        create_task(self._poll_sensors())

    async def _poll_sensors(self) -> None:
        """
        Asynchronously poll sensors and log readings every 60 seconds.
        """
        while True:
            readings = self.get_readings()
            for reading in readings:
                self.log.info(f"Module: {reading}: {readings[reading]}")
            await sleep(60)
    
    def get_modules(self) -> list:
        """
        Return a dictionary of configured sensor modules.
        """
        return list(self.configured_modules.keys())

    def get_sensors(self, module: str) -> list:
        """
        Return list of sensors for a specific module name.
        """
        module_object = self.configured_modules[module]
        sensors = module_object.get_sensors()
        self.log.info(f"Available sensors for {module}: {sensors}")
        return sensors

    def get_readings(self, module: str = "") -> dict:
        """
        Return readings from a specific module by passing it's name as a
        string, or all modules if none specified.
        """
        readings = {}
        if module:
            readings[module] = self.configured_modules[module].get_reading()
        else:
            for name, instance in self.configured_modules.items():
                readings[name] = instance.get_reading()
        return readings
