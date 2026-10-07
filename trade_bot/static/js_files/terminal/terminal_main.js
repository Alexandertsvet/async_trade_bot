
document.addEventListener("DOMContentLoaded", function() {
    const statusBlock = document.getElementById("ws-status-");
    
    let socket = null;
    let reconnectDelay = 1000;       
    const maxReconnectDelay = 16000; 
    let reconnectTimer = null;
    
    let dataWatchdogTimer = null; 
    const DATA_TIMEOUT = 4000;       

    // ВАЖНО: Маршрут из команды указывает на /ws/trades/ticker_name/
    // Если вы используете фиксированный широковещательный маршрут /ws/terminal/, проверьте routing.py!
    const wsProtocol = window.location.protocol === "https:" ? "wss://" : "ws://";
    const wsUrl = wsProtocol + window.location.host + "/ws/trades/gazp/"; // Адаптировано под ваш роутинг

    function resetDataWatchdog() {
        if (dataWatchdogTimer) clearTimeout(dataWatchdogTimer);

        if (socket && socket.readyState === WebSocket.OPEN) {
            statusBlock.className = "border border-dark border-2 p-2 text-center small mb-3 bg-white text-dark fw-bold text-uppercase";
            statusBlock.innerHTML = "🟢 WS_CONNECTED // СТРИМ ДАННЫХ АКТИВЕН";
        }

        dataWatchdogTimer = setTimeout(function() {
            if (socket && socket.readyState === WebSocket.OPEN) {
                statusBlock.className = "border border-dark border-2 p-2 text-center small mb-3 bg-light text-muted fw-bold text-uppercase";
                statusBlock.innerHTML = "⚠️ ОЖИДАНИЕ КОТИРОВОК // ДАННЫЕ ИЗ T-INVEST НЕ ПОСТУПАЮТ";
            }
        }, DATA_TIMEOUT);
    }

    function connect() {
        if (reconnectTimer) {
            clearTimeout(reconnectTimer);
            reconnectTimer = null;
        }

        console.log("STREAM_CONNECTING // УСТАНОВКА СВЯЗИ С URL:", wsUrl);
        statusBlock.className = "border border-dark border-2 p-2 text-center small mb-3 bg-light text-dark fw-bold text-uppercase";
        statusBlock.innerHTML = "🔄 ПОДКЛЮЧЕНИЕ К WS://СЕРВЕРУ...";

        socket = new WebSocket(wsUrl);

        socket.onopen = function(e) {
            console.log("STREAM_CONNECTED // СЕТЕВОЙ МОСТ С ASGI СТАБИЛЕН");
            resetDataWatchdog();
            reconnectDelay = 1000; 
        };

        socket.onmessage = function(event) {
            const data = JSON.parse(event.data);
            resetDataWatchdog(); 

            if (data.event === "SYSTEM_INFO") {
                console.log("СИСТЕМА:", data.message);
            }

            // А. ОБРАБОТКА СВЕЧЕЙ (1M)
            if (data.event === "CANDLE") {
                document.getElementById("candle-price").innerText = parseFloat(data.close).toFixed(2);
                document.getElementById("candle-volume").innerText = data.volume;
            }

            // Б. ОБРАБОТКА ЛЕНТЫ СДЕЛОК
            if (data.event === "TRADE") {
                const directionBlock = document.getElementById("trade-direction");
                document.getElementById("trade-price").innerText = parseFloat(data.price).toFixed(2);
                
                if (data.direction === "BUY" || data.direction === "TRADE_DIRECTION_BUY") {
                    directionBlock.className = "small fw-bold text-uppercase py-1 px-2 border border-dark bg-white text-dark";
                    directionBlock.innerText = "🟢 ПОКУПКА // BUY";
                } else {
                    directionBlock.className = "small fw-bold text-uppercase py-1 px-2 border border-dark bg-light text-muted";
                    directionBlock.innerText = "🔴 ПРОДАЖА // SELL";
                }
            }

            // В. ОБРАБОТКА СТАКАНА (ORDERBOOK)
            if (data.event === "ORDERBOOK") {
                // Используем ключи, полученные из нашего MarketDataFastSerializer
                if (data.best_ask !== undefined && data.best_bid !== undefined) {
                    document.getElementById("book-ask").innerText = parseFloat(data.best_ask).toFixed(2);
                    document.getElementById("book-bid").innerText = parseFloat(data.best_bid).toFixed(2);
                    
                    // Если в payload передаются объемы лучших цен:
                    document.getElementById("book-ask-q").innerText = data.best_ask_quantity || (data.asks[0] ? data.asks[0].q : 0);
                    document.getElementById("book-bid-q").innerText = data.best_bid_quantity || (data.bids[0] ? data.bids[0].q : 0);
                }
            }
        };

        socket.onclose = function(e) {
            console.log(`STREAM_DISCONNECTED // СОЕДИНЕНИЕ ЗАКРЫТО. РЕКОННЕКТ ЧЕРЕЗ ${reconnectDelay}мс`, e.reason);
            if (dataWatchdogTimer) clearTimeout(dataWatchdogTimer);
            
            statusBlock.className = "border border-dark border-2 p-2 text-center small mb-3 bg-danger text-white fw-bold text-uppercase";
            statusBlock.innerHTML = `🚨 ОШИБКА СВЯЗИ // ПОПЫТКА РЕКОННЕКТА ЧЕРЕЗ ${reconnectDelay / 1000} СЕК...`;
            
            // Экспоненциальный шаг задержки
            reconnectTimer = setTimeout(connect, reconnectDelay);
            reconnectDelay = Math.min(reconnectDelay * 2, maxReconnectDelay);
        };

        socket.onerror = function(err) {
            console.error("STREAM_SOCKET_ERROR // СБОЙ В РАБОТЕ ВЕБСОКЕТА:", err);
            socket.close();
        };
    }

    // Запуск первичного подключения
    connect();
});
