'''
Battleships server
'''


import json
import asyncio
import ssl
import traceback
import websockets
import database
import log
import wst
import config
from user import auth
from user.user import User
from game import game


database.tables_create()
log.startup()


users = set()


async def handler(websocket, _):
    # ws connection handler
    user = User(websocket)
    users.add(user)
    await wst.send(user.ws, {'type': 'state', 'data': -2})  # sends state=-2(connected) to the client
    try:
        async for message in websocket:
            try:
                rc = json.loads(message)
                user_state = user.get_state()
                # state 0-pre login 1-login 2-in game
                if user_state == 2:
                    await game.action[rc['type']](user, rc)
                elif user_state == 1 and rc["type"] == "join":
                    await game.join(user, rc['data'], rc.get('code'))
                elif user_state == 0:
                    if rc["type"] == "authorization":
                        await auth.authorization(users, user, rc)
            except Exception:
                log.exception(traceback.format_exc())

    except Exception:
        # only ws connection close errors
        pass
    finally:
        await game.finish(user)
        users.remove(user)


async def server():
    async with websockets.serve(handler, config.IP, config.PORT, ssl=ssl_context):
        await asyncio.Future()

if __name__ == '__main__':
    ssl_context = None
    if config.SSL_KEY:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(config.SSL_CHAIN, config.SSL_KEY)
    asyncio.run(server())
