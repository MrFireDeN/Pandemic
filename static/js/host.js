const startBtn = document.getElementById("start-btn");
const roomCode = startBtn.dataset.room;

const socket = io();

const playerList = document.getElementById("player-list");

// Присоединяемся к комнате
socket.emit("host_join", { code: roomCode });

// Когда новый игрок подключается
socket.on("player_joined", (data) => {
    const li = document.createElement("li");
    li.textContent = `${data.name} — ${data.role}`;

    playerList.appendChild(li);

    if (playerList.children.length > 0) {
        startBtn.disabled = false;
    }
});

// Кнопка "Начать игру"
startBtn.addEventListener("click", () => {
    socket.emit("start_game", { code: roomCode });
});

// Подтверждение начала игры
socket.on("game_started", () => {
    window.location.href = `/board/${roomCode}`;
});

socket.on("error", (data) => {
    alert(data.message || "Ошибка соединения");
});