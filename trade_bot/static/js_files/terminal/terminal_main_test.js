
document.addEventListener("DOMContentLoaded", function() {
    // функции 
    const formatTime = (isoString) => {
        if (!isoString) return "--:--:--";
        const date = new Date(isoString);
        if (isNaN(date.getTime())) return isoString;
        
        const pad = (num) => String(num).padStart(2, '0');
        const hours = pad(date.getHours());
        const minutes = pad(date.getMinutes());
        const seconds = pad(date.getSeconds());
        
        // Для точного времени сделки (last_trade_ts) выводим также миллисекунды
        if (isoString.includes('.')) {
            const ms = String(date.getMilliseconds()).padStart(3, '0');
            return `${hours}:${minutes}:${seconds}.${ms}`;
        }
        
        return `${hours}:${minutes}:${seconds}`;
    };

    // --------------------------------------------------------------------------------------
    // candle констранты
    const tickTimeElement = document.getElementById('log-tick-time');
    const tickTimeElementCandle = document.getElementById('log-tick-time-candle');
    const closeCell = document.getElementById('log-close');
    const CellVolBue = document.getElementById('log-vol-buy');
    const CellVolSell = document.getElementById('log-vol-sell');
    //---------------------------------------------------------------------------------------




    const statusBlock = document.getElementById("ws-status");
    
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
                //
                if (tickTimeElement) {
                    tickTimeElement.textContent = formatTime(data.last_trade_ts);
                }
                if (tickTimeElementCandle) {
                    tickTimeElementCandle.textContent = formatTime(data.time);
                }

                // 2. Обновляем значения в таблице
                const fields = {
                    'log-open': data.open,
                    'log-high': data.high,
                    'log-low': data.low,
                    'log-close': data.close,
                    'log-volume': data.volume,
                    'log-vol-buy': data.volume_buy,
                    'log-vol-sell': data.volume_sell
                };

                for (const [id, value] of Object.entries(fields)) {
                    const element = document.getElementById(id);
                    if (element && value !== undefined) {
                        if (id.includes('volume') || id.includes('vol-')) {
                            element.textContent = parseInt(value);
                        } else {
                            element.textContent = parseFloat(value).toFixed(2);
                        }
                    }
                }
                const openPrice = parseFloat(data.open);
                const closePrice = parseFloat(data.close);
                if (closeCell && !isNaN(openPrice) && !isNaN(closePrice)) {
                    if (closePrice > openPrice) {
                        closeCell.style.color = '#198754';
                        closeCell.classList.add('fw-bold');
                        closeCell.style.backgroundColor = 'transparent'; 
                    } else if (closePrice < openPrice) {
                        closeCell.style.color = '#dc3545';
                        closeCell.classList.remove('fw-bold');
                        closeCell.style.backgroundColor = 'transparent';
                    } else {
                        closeCell.style.color = '#000000';
                        closeCell.classList.remove('fw-bold');
                    }
                }
                const VolBue = parseFloat(data.volume_buy);
                const VolSell = parseFloat(data.volume_sell);
                if (CellVolBue && CellVolSell && !isNaN(VolBue) && !isNaN(VolSell)) {
                    if (VolBue > VolSell) {
                        CellVolBue.style.color = '#198754'; 
                        CellVolBue.classList.add('fw-bold');
                        CellVolBue.style.backgroundColor = 'transparent'; 

                        CellVolSell.style.color = '#000000';
                        CellVolSell.classList.remove('fw-bold');
                    } else if (VolBue < VolSell) {
                        CellVolSell.style.color = '#dc3545';
                        CellVolSell.classList.remove('fw-bold');
                        CellVolSell.style.backgroundColor = 'transparent';

                        CellVolBue.style.color = '#000000';
                        CellVolBue.classList.remove('fw-bold');
                    } else {
                        CellVolBue.style.color = '#000000';
                        CellVolBue.classList.remove('fw-bold');
                        CellVolSell.style.color = '#000000';
                        CellVolSell.classList.remove('fw-bold');
                    }
                }
                //
            }

            // Б. ОБРАБОТКА ЛЕНТЫ СДЕЛОК
            if (data.event === "TRADE") {
                const tradesContainer = document.getElementById("trades-stream-list");
                const emptyMsg = document.getElementById("trades-empty-msg");
                
                // Удаляем заглушку "Ожидание сделок..." при первом тике
                if (emptyMsg) emptyMsg.remove();

                // Форматируем входные данные
                const tradeTime = formatTime(data.time); // Время с миллисекундами
                const price = parseFloat(data.price).toFixed(2);
                const quantity = parseInt(data.quantity);
                
                // Определяем тип направления сделки
                const isBuy = data.direction === "BUY" || data.direction === "TRADE_DIRECTION_BUY";
                const badgeClass = isBuy ? "text-success fw-bold" : "text-danger";
                const borderClass = isBuy ? "border-start border-success border-3" : "border-start border-danger border-3";
                const bgClass = isBuy ? "bg-success bg-opacity-10" : "bg-opacity-10 bg-danger";
                const directionText = isBuy ? "BUY" : "SELL";

                // Создаем новую строку сделки
                const tradeRow = document.createElement("div");
                tradeRow.className = `d-flex justify-content-between px-2 py-1 mb-1 small ${borderClass} ${bgClass} font-monospace`;
                tradeRow.style.fontSize = "0.8rem";
                
                tradeRow.innerHTML = `
                    <span style="width: 25%;" class="text-muted">${tradeTime}</span>
                    <span style="width: 25%; text-align: right;" class="fw-bold text-dark">${price}</span>
                    <span style="width: 25%; text-align: right;" class="text-dark">${quantity}</span>
                    <span style="width: 25%; text-align: right;" class="${badgeClass}">${directionText}</span>
                `;

                // Вставляем новую сделку в самый верх списка (prepend)
                tradesContainer.insertBefore(tradeRow, tradesContainer.firstChild);

                // Защита от перегрузки памяти: оставляем только последние 25 сделок в DOM
                if (tradesContainer.children.length > 25) {
                    tradesContainer.removeChild(tradesContainer.lastChild);
                }
            }

            // В. ОБРАБОТКА СТАКАНА (ORDERBOOK)
            if (data.event === "ORDERBOOK") {
                // Используем ключи, полученные из нашего MarketDataFastSerializer

                //
                const asksContainer = document.getElementById('orderbook-asks-list');
                const bidsContainer = document.getElementById('orderbook-bids-list');
                const spreadElement = document.getElementById('orderbook-spread-val');

                // Проверяем наличие массивов BIDS и ASKS в пришедшем объекте
                const bids = data.bids || [];
                const asks = data.asks || [];

                // 1. РАСЧЕТ И ВЫВОД СПРЕДА
                if (asks.length > 0 && bids.length > 0) {
                    const bestAsk = parseFloat(asks[0].p);
                    const bestBid = parseFloat(bids[0].p);
                    const spread = bestAsk - bestBid;
                    
                    if (spreadElement && !isNaN(spread)) {
                        spreadElement.textContent = spread.toFixed(2);
                    }
                }

                // 2. ОТРИСОВКА АСКОВ (ПРОДАЖИ)
                if (asksContainer && asks.length > 0) {
                    // Берем топ-5 лучших заявок на продажу
                    // .reverse() нужен, чтобы самая низкая (лучшая) цена продажи оказалась прямо над спредом
                    const topAsks = asks.slice(0, 5); 
                    
                    asksContainer.innerHTML = topAsks.map(ask => {
                        const price = parseFloat(ask.p).toFixed(2);
                        const quantity = parseInt(ask.q).toLocaleString('ru-RU');
                        
                        // Первая строка (лучший аск) выделяется полужирным для ЧБ стиля
                        const isBest = ask.p === asks[0].p ? 'fw-bold bg-light' : '';
                        
                        return `
                            <div class="d-flex justify-content-between text-secondary px-1 py-05 ${isBest}">
                                <span><i class="bi bi-arrow-down-short"></i>${price}</span>
                                <span>${quantity}</span>
                            </div>`;
                    }).join('');
                }

                // 3. ОТРИСОВКА БИДОВ (ПОКУПКИ)
                if (bidsContainer && bids.length > 0) {
                    // Берем топ-5 лучших заявок на покупку (лучшая цена покупки сразу под спредом)
                    const topBids = bids.slice(0, 5);
                    
                    bidsContainer.innerHTML = topBids.map(bid => {
                        const price = parseFloat(bid.p).toFixed(2);
                        const quantity = parseInt(bid.q).toLocaleString('ru-RU');
                        
                        const isBest = bid.p === bids[0].p ? 'fw-bold bg-light border-bottom border-dark' : '';
                        
                        return `
                            <div class="d-flex justify-content-between text-dark px-1 py-05 ${isBest}">
                                <span><i class="bi bi-arrow-up-short"></i>${price}</span>
                                <span>${quantity}</span>
                            </div>`;
                    }).join('');
                }
                //

                










                //



















































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

    connect();
});