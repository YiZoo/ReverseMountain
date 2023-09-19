ReverseMountain是一个简易的RPC服务，提供给爬虫工程师小伙伴们，希望大家能早点下班。
工作原理是在服务端开启一个websocket服务，并在浏览器端注入一段自执行JS代码，hook加密函数并开启一个连接服务端的websocket长链接。每当有爬虫程序需要获取加密参数时，只需连接服务，发送需加密的参数即可，开袋即食！

Usage
<hr>

步骤1：开启websocket服务
    

```shell
python main.py
```


步骤2：浏览器注入JS脚本

```js
(function () {
    window._rparse = encrypt_function;
    var ws = new WebSocket("ws://localhost:8000/worker/");
    ws.onopen = (event) => {
        console.log("connected");
        ws.send(JSON.stringify({"group": "group_name", "msg": "worker init"}))
    };
    ws.onmessage = (event) => {
        let response = JSON.parse(event.data);
        response.data = window._rparse(response['params']);
        ws.send(JSON.stringify(response))
    };
    ws.onclose = (event) => {
        console.log("closed")
    };
})();
```

步骤3：爬虫程序调用API

```python
import json
import websockets


async def climb(params):
    async with websockets.connect("ws://localhost:8000/spider/") as websocket:
        await websocket.send(json.dumps({'group': 'test', 'params': params}))
        response = await websocket.recv()
        return response
```
扣代码，补环境累了的话，不妨试试RPC吧。
