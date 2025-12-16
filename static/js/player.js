const code = "{{ code }}";
const name = "{{ name }}";
const playerId = "{{ player_id }}";
const socket = io();

function appendLog(text) {
    const log = document.getElementById("log");
    if (!log) return;
    const p = document.createElement("p");
    p.textContent = text;
    log.prepend(p);
}

socket.emit("player_join", { code, name });

document.getElementById("move-btn").addEventListener("click", () => {
    const city = document.getElementById("target-city").value.trim();

    if (city) {
        socket.emit("player:move", { game_code: code, player_id: playerId, to_city: city });
        console.log(code, playerId, city);
    }
});

socket.on("player:moved", (data) => {
    if (data.player_id == playerId) {
        document.getElementById("actions-left").textContent = data.actions_left;
    }
    appendLog(`Игрок ${data.player_id} переместился в ${data.new_city}`);
});

socket.on("player:move:error", (data) => {
    appendLog(data.message || "Не удалось переместиться");
});

socket.on("game:log", (data) => {
    if (data && data.text) {
        appendLog(data.text);
    }
});
