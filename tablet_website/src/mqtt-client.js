/* Small adapter for the bundled Paho MQTT client. No connection on import. */
(function (root, factory) {
    "use strict";
    if (typeof module === "object" && module.exports) module.exports = factory();
    else root.TabletMQTT = factory();
}(typeof window !== "undefined" ? window : this, function () {
    "use strict";
    var commands = ["stop", "surveillance_mode", "entrance_mode"];
    function validateConfig(input) {
        var allowed = ["host", "port", "path", "useSSL", "topic"];
        if (!input || typeof input !== "object" || Array.isArray(input) ||
            Object.keys(input).some(function (key) { return allowed.indexOf(key) === -1; })) {
            throw new Error("Configuration accepts only host, port, path, useSSL and topic. Enter credentials in the form.");
        }
        var host = typeof input.host === "string" ? input.host.trim() : "";
        var port = Number(input.port);
        var path = typeof input.path === "string" ? input.path : "/mqtt";
        var topic = typeof input.topic === "string" ? input.topic.trim() : "";
        if (!host || /[\s/\\?#]/.test(host) || host.indexOf("://") !== -1) throw new Error("Enter a broker hostname without a URL or path.");
        if (!isFinite(port) || Math.floor(port) !== port || port < 1 || port > 65535) throw new Error("Enter a port from 1 to 65535.");
        if (path.charAt(0) !== "/" || /[\s?#]/.test(path)) throw new Error("Enter a WebSocket path beginning with /.");
        if (typeof input.useSSL !== "boolean") throw new Error("useSSL must be true or false.");
        if (!topic || /[+#\u0000]/.test(topic)) throw new Error("Enter a command topic without MQTT wildcards.");
        return {host: host, port: port, path: path, useSSL: input.useSSL, topic: topic};
    }
    function Client(config, paho, onState, onMessage) {
        this.config = validateConfig(config);
        this.paho = paho;
        this.onState = onState || function () {};
        this.onMessage = onMessage || function () {};
        this.client = null;
        this.state = "disconnected";
        this.generation = 0;
    }
    Client.prototype.setState = function (state) { this.state = state; this.onState(state); };
    Client.prototype.connect = function (credentials) {
        credentials = credentials || {};
        if (this.client) throw new Error("Disconnect before connecting again.");
        var username = credentials.username || "";
        var password = credentials.password || "";
        if (password && !username) throw new Error("A password requires a username.");
        if (!this.paho || !this.paho.Client || !this.paho.Message) throw new Error("The bundled MQTT library is unavailable.");
        var self = this;
        var generation = ++this.generation;
        var config = this.config;
        // A unique client ID prevents one tablet page from disconnecting another.
        var id = "pepper-" + Math.random().toString(36).slice(2, 13);
        var client = new this.paho.Client(config.host, config.port, config.path, id);
        this.client = client;
        function active() { return self.client === client && self.generation === generation; }
        function close() { try { client.disconnect(); } catch (_) { /* Already closed or connecting. */ } }
        function fail() {
            if (!active()) return;
            self.client = null;
            ++self.generation;
            close();
            self.setState("failed");
        }
        client.onConnectionLost = function () {
            if (!active()) return;
            self.client = null;
            ++self.generation;
            self.setState("disconnected");
        };
        client.onMessageArrived = function (message) {
            if (active() && self.state === "ready" && message.destinationName === config.topic)
                self.onMessage(message.payloadString);
        };
        this.setState("connecting");
        var options = {
            useSSL: config.useSSL, timeout: 10, mqttVersion: 4, cleanSession: true,
            onFailure: fail,
            onSuccess: function () {
                if (!active()) { close(); return; }
                self.setState("subscribing");
                try {
                    client.subscribe(config.topic, {
                        qos: 0,
                        onSuccess: function () { if (active()) self.setState("ready"); },
                        onFailure: fail
                    });
                } catch (_) { fail(); }
            }
        };
        if (username) options.userName = username;
        if (password) options.password = password;
        try { client.connect(options); } catch (_) { fail(); }
    };
    Client.prototype.publish = function (command) {
        if (commands.indexOf(command) === -1) throw new Error("Unsupported tablet command.");
        if (this.state !== "ready" || !this.client) return false;
        try {
            var message = new this.paho.Message(command);
            message.destinationName = this.config.topic;
            message.qos = 0;
            message.retained = false;
            this.client.send(message);
            return true;
        } catch (_) {
            this.disconnect();
            this.setState("failed");
            return false;
        }
    };
    Client.prototype.disconnect = function () {
        var client = this.client;
        this.client = null;
        ++this.generation;
        if (client) { try { client.disconnect(); } catch (_) { /* Pending callback will close it. */ } }
        this.setState("disconnected");
    };
    return {Client: Client, validateConfig: validateConfig};
}));
