const code = "{{ code }}";
const name = "{{ name }}";
const playerId = "{{ player_id }}";
const socket = io();

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
    const log = document.getElementById("log");
    const p = document.createElement("p");
    p.textContent = `Игрок ${data.player_id} переместился в ${data.new_city}`;
    log.appendChild(p);
});