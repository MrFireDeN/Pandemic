const { createApp } = Vue;

createApp({
    data: () => ({ hostCode: null }),
    methods: {
        async createHost() {
            const res = await fetch("/api/host/create", { method: "POST" });
            const data = await res.json();
            this.hostCode = data.code;
        }
    }
}).mount("#index-app");
