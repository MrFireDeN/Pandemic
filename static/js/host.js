const { createApp } = Vue;

createApp({
    data: () => ({ players: [] }),
    mounted() {
        const code = window.__ROOM_CODE__;
        socket.emit("host_join", { code });
        socket.on("player_joined", ({ name }) => {
            if (!this.players.includes(name)) this.players.push(name);
        });
        socket.on("game_started", () => {
            // TODO: отрисовать стартовую фазу поля
        });
    },
    methods: {
        startGame() {
            const code = window.__ROOM_CODE__;
            socket.emit("start_game", { code });
        }
    }
}).mount("#host-app");
