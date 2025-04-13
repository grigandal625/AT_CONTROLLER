import asyncio
import logging
import os

from at_queue.core.session import ConnectionParameters

from at_controller.core.arguments import get_args
from at_controller.core.controller import ATController

logging.basicConfig(level=logging.INFO)


async def main():
    connection_parameters = ConnectionParameters(**get_args())

    try:
        if not os.path.exists("/var/run/at_controller/"):
            os.makedirs("/var/run/at_controller/")

        with open("/var/run/at_controller/pidfile.pid", "w") as f:
            f.write(str(os.getpid()))
    except PermissionError:
        pass

    controller = ATController(connection_parameters=connection_parameters)

    await controller.initialize()
    await controller.register()
    await controller.start()


if __name__ == "__main__":
    asyncio.run(main())
