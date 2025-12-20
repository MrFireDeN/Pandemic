const createBtn = document.getElementById("create-host");
const roomInfo = document.getElementById("room-info");
const codeEl = document.getElementById("room-code");
const hostLink = document.getElementById("host-link");

createBtn.addEventListener("click", async () => {
    try {
        const res = await fetch("/api/host/create", { method: "POST" });
        const data = await res.json();

        if (data.status === "ok") {
            codeEl.textContent = data.code;
            hostLink.href = `/host/${data.code}`;
            roomInfo.style.display = "block";
        } else {
            alert("Ошибка при создании комнаты");
        }
    } catch (err) {
        alert("Ошибка соединения с сервером");
    }
});