const code = "{{ code }}";
const name = "{{ name }}";
let playerId = null;
const socket = io();

console.log("Player page initialized:", { code, name });

// Загружаем состояние игры и находим player_id
async function loadGameState() {
    try {
        const response = await fetch(`/api/game/${code}/state`);
        const result = await response.json();
        
        if (result.status === "ok" && result.data) {
            const gameData = result.data;
            
            // Находим игрока по имени (с учетом возможных различий в регистре/пробелах)
            const player = gameData.players.find(p => 
                p.name && name && p.name.trim().toLowerCase() === name.trim().toLowerCase()
            );
            
            if (player) {
                playerId = player.id;
                updatePlayerInfo(player);
                console.log("Player found in game state:", player);
            } else {
                console.warn("Player not found. Available players:", gameData.players.map(p => p.name));
                console.warn("Looking for:", name);
                // Если игрок не найден, но есть игроки, попробуем найти по первому совпадению
                if (gameData.players.length > 0 && !playerId) {
                    addLogEntry("Игрок не найден в списке. Попробуйте перезагрузить страницу.", "error");
                }
            }
            
            updateGameState(gameData);
        } else {
            console.error("Error loading game state:", result.message);
            addLogEntry(`Ошибка загрузки состояния: ${result.message}`, "error");
        }
    } catch (error) {
        console.error("Error loading game state:", error);
        addLogEntry(`Ошибка: ${error.message}`, "error");
    }
}

function updatePlayerInfo(player) {
    document.getElementById("actions-left").textContent = player.actions_left || 0;
    document.getElementById("current-position").textContent = player.position || "Неизвестно";
    document.getElementById("player-role").textContent = player.role || "Неизвестно";
}

function updateGameState(gameData) {
    document.getElementById("game-phase").textContent = gameData.phase || "Неизвестно";
    if (gameData.current_player) {
        document.getElementById("current-player").textContent = gameData.current_player.name || "Неизвестно";
    }
    if (gameData.board) {
        document.getElementById("infection-indicator").textContent = gameData.board.infection_indicator || 0;
        document.getElementById("outbreak-indicator").textContent = gameData.board.outbreak_indicator || 0;
    }
}

function addLogEntry(message, type = "info") {
    const logContent = document.getElementById("log-content");
    const entry = document.createElement("div");
    entry.className = "log-entry";
    entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    logContent.insertBefore(entry, logContent.firstChild);
    
    // Ограничиваем количество записей
    while (logContent.children.length > 50) {
        logContent.removeChild(logContent.lastChild);
    }
}

// Подключаемся к игре
socket.emit("player_join", { code, name });

// Обрабатываем событие player_joined для установки playerId
socket.on("player_joined", (data) => {
    console.log("Player joined:", data);
    if (data.name === name) {
        playerId = data.id;
        updatePlayerInfo(data);
        addLogEntry(`Вы подключены как игрок #${playerId}`);
    }
});

// Загружаем начальное состояние
loadGameState();

// Периодически проверяем состояние игры, если playerId еще не установлен
let stateCheckInterval = setInterval(() => {
    if (!playerId) {
        console.log("Player ID not set, checking game state...");
        loadGameState();
    } else {
        clearInterval(stateCheckInterval);
    }
}, 2000); // Проверяем каждые 2 секунды

// Останавливаем проверку через 30 секунд
setTimeout(() => {
    clearInterval(stateCheckInterval);
    if (!playerId) {
        addLogEntry("Не удалось найти игрока. Проверьте, что вы правильно подключились к игре.", "error");
    }
}, 30000);

// Обработчики действий
document.getElementById("move-btn").addEventListener("click", async () => {
    const city = document.getElementById("target-city").value.trim();
    
    if (!city) {
        alert("Введите название города");
        return;
    }
    
    if (!playerId) {
        // Попробуем еще раз загрузить состояние игры
        await loadGameState();
        if (!playerId) {
            alert("Игрок не найден. Убедитесь, что вы правильно подключились к игре и перезагрузите страницу.");
            return;
        }
    }
    
    try {
        const response = await fetch(`/api/game/${code}/move`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ player_id: playerId, to_city: city })
        });
        
        const result = await response.json();
        if (result.status === "ok") {
            addLogEntry(`Перемещение в ${city} выполнено`);
            socket.emit("player:move", { game_code: code, player_id: playerId, to_city: city });
            loadGameState();
        } else {
            addLogEntry(`Ошибка: ${result.message}`, "error");
            alert(result.message || "Ошибка перемещения");
        }
    } catch (error) {
        addLogEntry(`Ошибка: ${error.message}`, "error");
        console.error("Error moving:", error);
    }
});

document.getElementById("cure-btn").addEventListener("click", async () => {
    const city = document.getElementById("cure-city").value.trim();
    const color = document.getElementById("cure-color").value;
    
    if (!city) {
        alert("Введите название города");
        return;
    }
    
    if (!playerId) {
        // Попробуем еще раз загрузить состояние игры
        await loadGameState();
        if (!playerId) {
            alert("Игрок не найден. Убедитесь, что вы правильно подключились к игре и перезагрузите страницу.");
            return;
        }
    }
    
    try {
        const response = await fetch(`/api/game/${code}/cure`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ player_id: playerId, city_name: city, color: color })
        });
        
        const result = await response.json();
        if (result.status === "ok") {
            addLogEntry(`Город ${city} вылечен (${color})`);
            socket.emit("player:cure", { game_code: code, player_id: playerId, city_name: city, color: color });
            loadGameState();
        } else {
            addLogEntry(`Ошибка: ${result.message}`, "error");
            alert(result.message || "Ошибка лечения");
        }
    } catch (error) {
        addLogEntry(`Ошибка: ${error.message}`, "error");
        console.error("Error curing:", error);
    }
});

document.getElementById("end-turn-btn").addEventListener("click", async () => {
    if (!playerId) {
        // Попробуем еще раз загрузить состояние игры
        await loadGameState();
        if (!playerId) {
            alert("Игрок не найден. Убедитесь, что вы правильно подключились к игре и перезагрузите страницу.");
            return;
        }
    }
    
    try {
        const response = await fetch(`/api/game/${code}/end_turn`, {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });
        
        const result = await response.json();
        if (result.status === "ok") {
            addLogEntry("Ход завершен");
            socket.emit("player:end_turn", { game_code: code });
            loadGameState();
        } else {
            addLogEntry(`Ошибка: ${result.message}`, "error");
            alert(result.message || "Ошибка завершения хода");
        }
    } catch (error) {
        addLogEntry(`Ошибка: ${error.message}`, "error");
        console.error("Error ending turn:", error);
    }
});

// Слушаем события через сокеты
socket.on("player:moved", (data) => {
    if (data.player_id == playerId) {
        document.getElementById("actions-left").textContent = data.actions_left || 0;
    }
    addLogEntry(`Игрок #${data.player_id} переместился в ${data.new_city}`);
    loadGameState();
});

socket.on("city:cured", (data) => {
    addLogEntry(`Игрок #${data.player_id} вылечил город ${data.city} (${data.color})`);
    loadGameState();
});

socket.on("turn_ended", (data) => {
    addLogEntry("Ход завершен");
    loadGameState();
});

socket.on("game_started", (data) => {
    addLogEntry("Игра началась!");
    console.log("Game started, data:", data);
    
    // Обновляем информацию об игроке из данных игры
    if (data && data.players) {
        const player = data.players.find(p => 
            p.name && name && p.name.trim().toLowerCase() === name.trim().toLowerCase()
        );
        if (player) {
            playerId = player.id;
            updatePlayerInfo(player);
            console.log("Player ID set from game_started:", playerId);
        }
    }
    
    updateGameState(data);
    loadGameState();
});

socket.on("game_state", (data) => {
    console.log("Game state received:", data);
    updateGameState(data);
    if (data.players) {
        const player = data.players.find(p => p.name === name);
        if (player) {
            playerId = player.id;
            updatePlayerInfo(player);
            console.log("Player ID set to:", playerId);
        } else {
            console.warn("Player not found in game state. Players:", data.players.map(p => p.name));
        }
    }
});

socket.on("error", (data) => {
    addLogEntry(`Ошибка: ${data.message}`, "error");
    console.error("Socket error:", data);
});