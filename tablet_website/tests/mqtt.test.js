"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const mqtt = require("../src/mqtt-client.js");
const initPage = require("../src/javascript.js");
const config = {host: "broker.example.invalid", port: 443, path: "/mqtt", useSSL: true, topic: "pepper/commands"};
function fakePaho() {
    const instances = [];
    class Client {
        constructor(...args) { this.args = args; this.sent = []; this.subscriptions = []; this.closed = 0; instances.push(this); }
        connect(options) { this.options = options; }
        subscribe(topic, options) { this.subscriptions.push({topic, options}); }
        send(message) { this.sent.push(message); }
        disconnect() { this.closed++; }
    }
    class Message { constructor(payload) { this.payloadString = payload; } }
    return {Client, Message, instances};
}
function connectReady(adapter, paho) {
    adapter.connect();
    const client = paho.instances.at(-1);
    client.options.onSuccess();
    client.subscriptions[0].options.onSuccess();
    return client;
}
test("import/construction does not connect; subscribe waits for connection and commands wait for acknowledgement", () => {
    const paho = fakePaho();
    const adapter = new mqtt.Client(config, paho);
    assert.equal(paho.instances.length, 0);
    assert.equal(adapter.publish("surveillance_mode"), false);
    adapter.connect({username: "test-user", password: "test-password"});
    const client = paho.instances[0];
    assert.deepEqual(client.args.slice(0, 3), [config.host, 443, "/mqtt"]);
    assert.equal(client.options.cleanSession, true);
    assert.equal(client.options.useSSL, true);
    assert.equal(client.options.userName, "test-user");
    assert.equal(client.subscriptions.length, 0);
    client.options.onSuccess();
    assert.equal(client.subscriptions[0].topic, config.topic);
    assert.equal(adapter.publish("surveillance_mode"), false);
    client.subscriptions[0].options.onSuccess();
    assert.equal(adapter.publish("entrance_mode"), true);
    assert.equal(client.sent[0].payloadString, "entrance_mode");
    assert.equal(client.sent[0].destinationName, config.topic);
    assert.equal(client.sent[0].qos, 0);
    assert.equal(client.sent[0].retained, false);
});
test("connection and subscription failures disable publishing and permit explicit retry", () => {
    const paho = fakePaho();
    const adapter = new mqtt.Client(config, paho);
    adapter.connect();
    paho.instances[0].options.onFailure({errorMessage: "server detail"});
    assert.equal(adapter.state, "failed");
    assert.equal(adapter.publish("surveillance_mode"), false);
    adapter.connect();
    const second = paho.instances[1];
    second.options.onSuccess();
    second.subscriptions[0].options.onFailure();
    assert.equal(adapter.state, "failed");
    assert.equal(second.closed, 1);
    assert.equal(adapter.client, null);
});
test("disconnect invalidates pending success and subscription callbacks", () => {
    const paho = fakePaho();
    const adapter = new mqtt.Client(config, paho);
    adapter.connect();
    const first = paho.instances[0];
    adapter.disconnect();
    first.options.onSuccess();
    assert.equal(first.subscriptions.length, 0);
    assert.ok(first.closed >= 1);
    adapter.connect();
    const second = paho.instances[1];
    second.options.onSuccess();
    adapter.disconnect();
    second.subscriptions[0].options.onSuccess();
    assert.equal(adapter.state, "disconnected");
    assert.equal(adapter.publish("stop"), false);
});
test("message callbacks respect active connection/topic; connection loss does not reconnect", () => {
    const paho = fakePaho();
    const received = [];
    const adapter = new mqtt.Client(config, paho, undefined, value => received.push(value));
    const client = connectReady(adapter, paho);
    client.onMessageArrived({destinationName: "other/topic", payloadString: "ignored"});
    client.onMessageArrived({destinationName: config.topic, payloadString: "hello"});
    assert.deepEqual(received, ["hello"]);
    client.onConnectionLost();
    client.onMessageArrived({destinationName: config.topic, payloadString: "stale"});
    assert.deepEqual(received, ["hello"]);
    assert.equal(adapter.state, "disconnected");
    assert.equal(paho.instances.length, 1);
});
test("synchronous connect/subscribe/send errors leave no usable connection", () => {
    for (const operation of ["connect", "subscribe", "send"]) {
        const paho = fakePaho();
        paho.Client.prototype[operation] = function () { throw new Error("test failure"); };
        const adapter = new mqtt.Client(config, paho);
        adapter.connect();
        const client = paho.instances[0];
        if (operation !== "connect") client.options.onSuccess();
        if (operation === "send") {
            client.subscriptions[0].options.onSuccess();
            assert.equal(adapter.publish("surveillance_mode"), false);
        }
        assert.equal(adapter.state, "failed");
        assert.equal(adapter.client, null);
    }
});
test("configuration rejects credentials, invalid endpoints and wildcard command topics", () => {
    for (const invalid of [null, [], {...config, password: "not-configuration"}, {...config, host: "https://broker.example.invalid"}, {...config, port: 0}, {...config, port: 1.5}, {...config, path: "mqtt"}, {...config, useSSL: "false"}, {...config, topic: "pepper/#"}]) {
        assert.throws(() => mqtt.validateConfig(invalid));
    }
    const adapter = new mqtt.Client(config, fakePaho());
    assert.throws(() => adapter.connect({password: "test-only"}));
    assert.throws(() => adapter.publish("unexpected"));
    assert.throws(() => adapter.publish("start"));
});
function fakeDocument() {
    const nodes = new Map();
    function node(id) {
        if (!nodes.has(id)) nodes.set(id, {value: "", checked: false, disabled: false, textContent: "", files: [], dataset: {}, getAttribute(name) { return name === "data-command" ? this.dataset.command : null; }, events: {}, addEventListener(event, handler) { this.events[event] = handler; }});
        return nodes.get(id);
    }
    const buttons = ["entrance_mode", "stop"].map(command => { const button = node(command); button.dataset.command = command; return button; });
    node("broker-host").value = config.host;
    node("broker-port").value = "443";
    node("broker-path").value = "/mqtt";
    node("broker-tls").checked = true;
    node("command-topic").value = config.topic;
    return {getElementById: node, querySelectorAll: () => buttons, node, buttons};
}
test("page starts offline, clears entered credentials, renders broker text safely and clears on disconnect", () => {
    const document = fakeDocument();
    const paho = fakePaho();
    const controller = initPage(document, mqtt, paho);
    assert.equal(paho.instances.length, 0);
    assert.ok(document.buttons.every(button => button.disabled));
    document.node("broker-username").value = "test-user";
    document.node("broker-password").value = "test-password";
    document.node("connection-form").events.submit({preventDefault() {}});
    assert.equal(document.node("broker-username").value, "");
    assert.equal(document.node("broker-password").value, "");
    const client = paho.instances[0];
    client.options.onSuccess();
    client.subscriptions[0].options.onSuccess();
    client.onMessageArrived({destinationName: config.topic, payloadString: "<img src=x onerror=alert(1)>"});
    assert.equal(document.node("last-message").textContent, "<img src=x onerror=alert(1)>");
    assert.equal(document.node("last-message").innerHTML, undefined);
    document.buttons[0].events.click();
    assert.equal(client.sent.length, 1);
    controller.disconnect();
    assert.ok(document.buttons.every(button => button.disabled));
    assert.equal(document.node("last-message").textContent, "");
    assert.equal(document.node("command-status").textContent, "");
});
test("importing a local config never connects and rejects stored credentials", () => {
    const document = fakeDocument();
    const paho = fakePaho();
    class Reader { readAsText(file) { this.result = file.contents; this.onload(); } }
    initPage(document, mqtt, paho, Reader);
    const picker = document.node("config-file");
    picker.files = [{size: 200, contents: JSON.stringify({...config, topic: "another/commands"})}];
    picker.events.change();
    assert.equal(document.node("command-topic").value, "another/commands");
    assert.equal(paho.instances.length, 0);
    picker.files = [{size: 200, contents: JSON.stringify({...config, password: "do-not-store"})}];
    picker.events.change();
    assert.match(document.node("connection-status").textContent, /Invalid configuration/);
    assert.equal(paho.instances.length, 0);
});

test("page errors never display client details or entered passwords", () => {
    const document = fakeDocument();
    const sensitive = "fake-sensitive-value";
    const failing = {Client: function () { throw new Error(sensitive); }};
    initPage(document, failing, fakePaho());
    document.node("broker-password").value = sensitive;
    document.node("connection-form").events.submit({preventDefault() {}});
    assert.equal(document.node("connection-status").textContent.includes(sensitive), false);
    assert.match(document.node("connection-status").textContent, /Could not connect/);
});
