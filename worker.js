(function () {
    window._rparse = encrypt_function; // hook到加密函数
    var ws = new WebSocket("ws://localhost:8000/worker/");
    ws.onopen = (event) => {
        console.log("connected");
        // 初始化worker
        ws.send(JSON.stringify({"group": "test", "msg": "worker init"}))
    };
    ws.onmessage = (event) => {
        let response = JSON.parse(event.data);
        // 调用加密函数，回传response
        response.data = window._rparse(response['params']);
        ws.send(JSON.stringify(response))
    };
    ws.onclose = (event) => {
        console.log("closed")
    };
})();