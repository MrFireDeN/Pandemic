const socket = io();

const joinBtn = document.getElementById("join-btn");
const readyBtn = document.getElementById("ready-btn");

const form = document.getElementById("form");
const status = document.getElementById("status");
const statusText = document.getElementById("status-text");

let code = "";
let name = "";
let role = 1;

// ---------------
// GLOBAL LISTENERS
// ---------------

// Когда игрок успешно добавлен
socket.on("player_joined", (data) => {
    // Только если это ТЕКУЩИЙ ИГРОК
    if (data.name === name) {
        form.style.display = "none";
        status.style.display = "block";
        statusText.textContent = `Вы подключены к комнате ${code} как ${name}`;
    }
});

socket.on("error", (data) => {
    alert(data.message || "Ошибка подключения");
});

socket.on("game_started", () => {
    window.location.href = `/player/${code}/${name}`;
});

joinBtn.addEventListener("click", () => {
    code = document.getElementById("room").value.trim().toUpperCase();
    name = document.getElementById("name").value.trim();
    role = parseInt(document.getElementById("role").value);

    if (!code || !name) {
        alert("Введите код комнаты и имя!");
        return;
    }

    socket.emit("player_join", {
        code,
        name,
        role
    });
});

readyBtn.addEventListener("click", () => {
    window.location.href = `/player/${code}/${name}`;
});
