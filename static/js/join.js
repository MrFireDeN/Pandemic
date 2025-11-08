const socket = io("/game");

const joinBtn = document.getElementById("join-btn");
const readyBtn = document.getElementById("ready-btn");
const form = document.getElementById("form");
const status = document.getElementById("status");
const statusText = document.getElementById("status-text");

let code = "";
let name = "";

joinBtn.addEventListener("click", () => {
    code = document.getElementById("room").value.trim().toUpperCase();
    name = document.getElementById("name").value.trim();

    if (!code || !name) {
        alert("Введите код комнаты и имя!");
        return;
    }

    socket.emit("player_join", { code, name, role: "Researcher" }); // временно фиксированная роль

    socket.on("player_joined", (data) => {
        if (data.name === name) {
            form.style.display = "none";
            status.style.display = "block";
            statusText.textContent = `Вы подключены к комнате ${code} как ${name}`;
        }
    });

    socket.on("error", (data) => {
        alert(data.message || "Ошибка подключения");
    });
});

readyBtn.addEventListener("click", () => {
    // Переход на страницу игрока
    window.location.href = `/player/${code}/${name}`;
});