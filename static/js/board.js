const code = "{{ code }}";
const socket = io();

socket.emit("host_join", { code });

socket.on("player_joined", (data) => {
    const list = document.getElementById("player-list");
    const li = document.createElement("li");
    li.textContent = data.name;
    list.appendChild(li);
});

socket.on("player:moved", (data) => {
    const log = document.createElement("p");
    // Получаем имя игрока из данных или используем player_id
    const playerName = data.player_name || `Игрок #${data.player_id}`;
    log.textContent = `${playerName} переместился в ${data.new_city}`;
    document.body.appendChild(log);
});

socket.on("game_started", () => {
    alert("Игра началась!");
});