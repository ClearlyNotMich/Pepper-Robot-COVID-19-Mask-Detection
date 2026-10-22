/* Page binding: offline until an explicit form submission. */
(function (root, factory) {
    "use strict";
    if (typeof module === "object" && module.exports) module.exports = factory;
    else root.tabletController = factory(root.document, root.TabletMQTT, root.Paho && root.Paho.MQTT, root.FileReader);
}(typeof window !== "undefined" ? window : this, function (document, mqtt, paho, FileReaderType) {
    "use strict";
    function get(id) { return document.getElementById(id); }
    var buttons = Array.prototype.slice.call(document.querySelectorAll("[data-command]"));
    var client = null;
    var loadingConfig = false;
    var messages = {
        disconnected: "Offline preview. No broker connection.",
        connecting: "Connecting…",
        subscribing: "Connected; subscribing to the command topic…",
        ready: "Connected. Commands can now be sent.",
        failed: "Connection or subscription failed. Check your settings before reconnecting."
    };
    function isBusy() { return client && ["connecting", "subscribing", "ready"].indexOf(client.state) !== -1; }
    function showState(state) {
        var busy = ["connecting", "subscribing", "ready"].indexOf(state) !== -1;
        get("connection-status").textContent = messages[state];
        get("connection-settings").disabled = busy;
        get("connect-button").disabled = busy || loadingConfig;
        get("disconnect-button").disabled = !busy;
        buttons.forEach(function (button) { button.disabled = state !== "ready"; });
    }
    function readConfig() {
        return {
            host: get("broker-host").value,
            port: Number(get("broker-port").value),
            path: get("broker-path").value,
            useSSL: get("broker-tls").checked,
            topic: get("command-topic").value
        };
    }
    function disconnect() {
        if (client) client.disconnect();
        client = null;
        get("broker-username").value = "";
        get("broker-password").value = "";
        get("command-status").textContent = "";
        get("last-message").textContent = "";
        showState("disconnected");
    }
    get("connection-form").addEventListener("submit", function (event) {
        event.preventDefault();
        if (loadingConfig || isBusy()) return;
        get("command-status").textContent = "";
        get("last-message").textContent = "";
        try {
            client = new mqtt.Client(readConfig(), paho, showState, function (payload) {
                // Broker text is untrusted; never insert it as HTML.
                get("last-message").textContent = payload;
            });
            var credentials = {username: get("broker-username").value, password: get("broker-password").value};
            get("broker-username").value = "";
            get("broker-password").value = "";
            client.connect(credentials);
        } catch (_) {
            showState("disconnected");
            get("connection-status").textContent = "Could not connect. Check the hostname, port, path, topic and credentials.";
        }
    });
    get("disconnect-button").addEventListener("click", disconnect);
    buttons.forEach(function (button) {
        button.addEventListener("click", function () {
            var command = button.getAttribute("data-command");
            var sent = client && client.publish(command);
            var label = command === "stop" ? "Shut down robot" : command;
            get("command-status").textContent = sent ? "Command sent: " + label + ". Robot execution is not confirmed." : "No command sent. Connect first.";
        });
    });
    get("config-file").addEventListener("change", function () {
        var file = get("config-file").files[0];
        if (!file || isBusy()) return;
        if (file.size > 8192) {
            get("connection-status").textContent = "Choose a configuration file smaller than 8 KB.";
            return;
        }
        loadingConfig = true;
        get("connect-button").disabled = true;
        var reader = new FileReaderType();
        function finished() { loadingConfig = false; get("connect-button").disabled = !!isBusy(); get("config-file").value = ""; }
        reader.onload = function () {
            try {
                var config = mqtt.validateConfig(JSON.parse(reader.result));
                get("broker-host").value = config.host;
                get("broker-port").value = config.port;
                get("broker-path").value = config.path;
                get("broker-tls").checked = config.useSSL;
                get("command-topic").value = config.topic;
                get("connection-status").textContent = "Settings loaded locally. Enter credentials if needed, then Connect.";
            } catch (_) {
                get("connection-status").textContent = "Invalid configuration. Use config.example.json; do not include credentials.";
            }
            finished();
        };
        reader.onerror = function () { get("connection-status").textContent = "Could not read the configuration file."; finished(); };
        reader.readAsText(file);
    });
    showState("disconnected");
    return {disconnect: disconnect};
}));
if (typeof window !== "undefined") window.addEventListener("pagehide", function () { if (window.tabletController) window.tabletController.disconnect(); });
