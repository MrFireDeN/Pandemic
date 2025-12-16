const code = "{{ code }}";
const socket = io();

function appendLog(text) {
    const logContainer = document.getElementById("log-messages");
    if (!logContainer) return;
    const item = document.createElement("div");
    item.textContent = text;
    logContainer.prepend(item);
}

socket.emit("host_join", { code });

socket.on("player_joined", (data) => {
    const list = document.getElementById("player-list");
    const li = document.createElement("li");
    li.textContent = data.role ? `${data.name} — ${data.role}` : data.name;
    list.appendChild(li);
    appendLog(`Подключился ${data.name}`);
});

socket.on("player:moved", (data) => {
    appendLog(`Игрок ${data.player_id} переместился в ${data.new_city}`);
});

socket.on("player:traded_card", (data) => {
    appendLog(`Игрок ${data.from} передал карту ${data.card_id} игроку ${data.to}`);
});

socket.on("player:built_station", (data) => {
    appendLog(`Построена станция в ${data.city}`);
});

socket.on("game_started", () => {
    appendLog("Игра началась");
});

socket.on("game:log", (data) => {
    if (data && data.text) {
        appendLog(data.text);
    }
});
