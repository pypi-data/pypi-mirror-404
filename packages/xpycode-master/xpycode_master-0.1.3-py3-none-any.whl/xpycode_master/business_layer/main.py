import asyncio

class BusinessLayer:
    def __init__(self):
        self.workbooks = {} 

    async def start(self):
        print("Starting Business Layer...")

if __name__ == "__main__":
    from ..logging_config import setup_logging_subprocess, get_logger
    setup_logging_subprocess()
    logger = get_logger(__name__)
    bl = BusinessLayer()
    asyncio.run(bl.start())
