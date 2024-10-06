from at_controller.core.arguments import get_args
from at_controller.core.controller import ATController
from at_queue.core.session import ConnectionParameters
import asyncio

async def main():    
    connection_parameters = ConnectionParameters(**get_args())
    
    controller = ATController(connection_parameters=connection_parameters)
    
    await controller.initialize()
    await controller.register()
    await controller.start()
    
    
if __name__ == '__main__':
    asyncio.run(main())
    