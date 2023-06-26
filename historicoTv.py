import asyncio
from websocket._exceptions import WebSocketConnectionClosedException
from cla_historicotv import HistoricoTV
import logging
logging.basicConfig(filename=f'loghistorico.log', level=logging.INFO,
                    format='%(asctime)s %(name)s  %(levelname)s  %(message)s  %(lineno)d ')
log = logging.getLogger("socketHistorico")


async def main(symbol):
    his = HistoricoTV()
    result = await asyncio.create_task(his.get_data_for_symbol(symbol))
    log.info(f"result: {result}")
    print("terminado todo")


if __name__ == "__main__":
    pairs = ["SP:SPX"]
    asyncio.run(main(pairs))

