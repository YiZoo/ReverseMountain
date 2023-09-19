import re
import json
import asyncio
import secrets
import websockets

# 非windows环境下，可以使用uvloop库来提高性能

workers = {}
spiders = {}


async def encrypt(websocket):
    try:
        params = json.loads(await asyncio.wait_for(websocket.recv(), timeout=5))
        assert 'group' in params
    except TimeoutError:
        # 超时，worker初始化失败，关闭连接，记录log
        await websocket.send(json.dumps({"code": 400, "msg": "timeout error, worker init failed!"}))
        await websocket.close()
        return
    except AssertionError:
        await websocket.send(json.dumps({'code': 400, 'msg': 'need a "group" params to init worker,add it and retry!'}))
        await websocket.close()
        return
    workers[params['group']] = websocket  # 保存每个组的worker,以便同组spider广播消息
    async for message in websocket:  # TODO 可能引发异常，未捕获
        spider_key = json.loads(message).get("spider", None)
        if spider_key:
            spider = spiders.get(spider_key)
            websockets.broadcast({spider}, message)
    workers.pop(params['group'])


async def get_secret(websocket):
    try:
        params = json.loads(await asyncio.wait_for(websocket.recv(), timeout=2))
        assert 'group' in params
    except TimeoutError:
        await websocket.send(json.dumps({"code": 400, "msg": "timeout error, did you send any message to server?"}))
        await websocket.close()
        return
    except AssertionError:
        await websocket.send(json.dumps({'code': 400, 'msg': 'need a "group" params to init worker,add it and retry!'}))
        await websocket.close()
        return
    except Exception:
        await websocket.send(json.dumps({'code': 400, 'msg': ' enter JSON format data please!'}))
        await websocket.close()
        return
    key = secrets.token_urlsafe(8)  # 每个spider生成唯一key
    spiders[key] = websocket
    worker = workers.get(params['group'], None)
    if worker:
        params.update({"spider": key})
        websockets.broadcast({worker}, json.dumps(params))
    else:
        await websocket.send(json.dumps({"code": 400, "msg": "no worker"}))
        return
    try:
        # 如果3秒内没有返回worker加密后的消息，抛出异常并告警
        response = await asyncio.wait_for(websocket.recv(), timeout=3)
        await websocket.send(response)
    except websockets.ConnectionClosedOK:
        pass
    except TimeoutError:
        await websocket.send(json.dumps({'code': 500, 'msg': 'time out ,server busy!'}))
    finally:
        spiders.pop(key)


async def handler(websocket, path):
    try:
        # 匹配路径参数，获取到worker或spider
        type = re.match("/([a-z]*)(/?)", path).group(1)
    except AttributeError:
        await websocket.send(json.dumps(
            {"code": 400,
             "msg": "need a path params,choose in [worker,spider],such as 'ws://localhost:8000/worker/'"}))
        await websocket.close()
        return
    if type == "worker":
        await encrypt(websocket)
    elif type == "spider":
        await get_secret(websocket)
    else:
        await websocket.send(json.dumps(
            {"code": 400, "msg": "path params just in  [worker,spider]"}
        ))


async def main(host='localhost', port=8000):
    async with websockets.serve(handler, host, port):
        await asyncio.Future()


if __name__ == '__main__':
    # TODO 可以封装成脚本启动，命令行中配置serve IP,PORT
    asyncio.run(main())
