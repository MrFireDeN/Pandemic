const code = "{{ code }}";
const socket = io("/game");

socket.emit("host_join", { code });

socket.on("player_joined", (data) => {
    const list = document.getElementById("player-list");
    const li = document.createElement("li");
    li.textContent = data.name;
    list.appendChild(li);
});

socket.on("player:moved", (data) => {
    const log = document.createElement("p");
    log.textContent = `Игрок ${data.player_id} переместился в ${data.new_city}`;
    document.body.appendChild(log);
});

socket.on("game_started", () => {
    alert("Игра началась!");
});