#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <SimpleKalmanFilter.h>

// Copy secrets.example.h to ignored secrets.h and configure this device locally.
#include "secrets.h"



#define STATE_PUBLISH_TIME 5000

WiFiClient espClient;
PubSubClient client(MQTT_HOST, MQTT_PORT, NULL, espClient);
SimpleKalmanFilter simpleKalmanFilter(2, 2, 0.01);

const long SERIAL_REFRESH_TIME = 500;
long refresh_time;
long state_sent_time;

void setup() {
	Serial.begin(9600);
	connectWifi();
}

void loop() {
	float real_value = analogRead(A0);
	float estimated_value = simpleKalmanFilter.updateEstimate(real_value);

	Serial.println(estimated_value);

	if (millis() > refresh_time) {
		if (!client.connected()) {
			reconnectMqtt();
		}
		client.loop();

		char buffer[100];
		snprintf(buffer, 100, "{\"ldr\": %.1f}", estimated_value);
		client.publish(MQTT_TOPIC, buffer, false);

		refresh_time = millis() + SERIAL_REFRESH_TIME;
	}

	delay(30);
}

void connectWifi() {
	delay(10);
	Serial.println();
	Serial.print("Connecting to ");
	Serial.println(WIFI_SSID);
	WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

	while (WiFi.status() != WL_CONNECTED) {
		delay(500);
		Serial.print(".");
	}

	Serial.println("");
	Serial.println("WiFi connected");
	Serial.println("IP address: ");
	Serial.println(WiFi.localIP());
}

void reconnectMqtt() {
	while (!client.connected()) {
		Serial.print("Attempting MQTT connection...");

		if (client.connect(MQTT_CLIENT_ID, MQTT_USERNAME, MQTT_PASSWORD)) {
			Serial.println("connected");
			client.publish(MQTT_TOPIC, "{\"scan_state\": 1}", false);
			state_sent_time = millis() + STATE_PUBLISH_TIME;
		} else {
			Serial.print("failed, rc=");
			Serial.print(client.state());
			Serial.print(" wifi=");
			Serial.print(WiFi.status());
			Serial.println(" try again in 5 seconds");
			delay(5000);
		}
	}
}