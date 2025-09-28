const { createApp } = Vue;

createApp({
    data: () => ({
        code: "",
        name: "",
        connected: false
    }),
    methods: {
        connect() {
            if (!this.code || !this.name) return;
            socket.emit("player_join", { code: this.code, name: this.name });
            socket.on("host_ready", () => { this.connected = true; });
            socket.on("action_broadcast", ({ action }) => {
                // TODO: отобразить входящий action
                console.log("broadcast action:", action);
            });
        },
        sendAction(action) {
            socket.emit("player_action", { code: this.code, action, name: this.name });
        }
    }
}).mount("#join-app");
