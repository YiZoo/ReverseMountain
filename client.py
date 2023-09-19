import asyncio
import json
import websockets

params = "test_params"


async def climb(params):
    async with websockets.connect("ws://localhost:8000/spider/") as websocket:
        await websocket.send(json.dumps({'group': 'test', 'params': params}))
        response = json.loads(await websocket.recv())
        return response["data"]


if __name__ == '__main__':
    print(asyncio.run(climb(params)))
