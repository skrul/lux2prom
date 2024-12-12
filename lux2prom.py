import random
import sys
import paho.mqtt.client as paho
import json
import traceback
from prometheus_client import start_http_server, Gauge
import os


# Get environment variables with defaults
MQTT_HOST = os.getenv('MQTT_HOST', None)
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
MQTT_USERNAME = os.getenv('MQTT_USERNAME', None)
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', None)
DONGLE = os.getenv('DONGLE', None)
PROMETHEUS_PORT = int(os.getenv('PROMETHEUS_PORT', '8000'))

from prometheus_client import Gauge, Counter, Histogram, Summary
from metrics import METRICS

# Create a mapping of metric types to Prometheus metric classes
METRIC_TYPE_MAP = {
    "gauge": Gauge,
    "counter": Counter,
    "histogram": Histogram,
    "summary": Summary
}

# Build PROM_METRICS dictionary
PROM_METRICS = {}
for metric in METRICS:
    prom_class = METRIC_TYPE_MAP[metric["type"]]
    metric_id = metric["id"].lower()
    PROM_METRICS[metric_id] = prom_class(
        name=metric_id,
        documentation='',
        unit=metric.get("unit", ""),
        namespace='lux',
        labelnames=['dongle']
    )

def on_message(client, userdata, msg):
    try:
        sent = []
        payload = json.loads(msg.payload.decode())
        
        # Iterate through all keys in the payload
        for key, value in payload["payload"].items():
            # Convert key to lowercase to match PROM_METRICS keys
            metric_key = key.lower()
            if metric_key in PROM_METRICS:
                try:
                    # Convert value to float and set the metric
                    metric_value = float(value)
                    PROM_METRICS[metric_key].labels(dongle=DONGLE).set(metric_value)
                    sent.append({metric_key: metric_value})
                except (ValueError, TypeError) as e:
                    print(f"Failed to convert value for metric {key}: {e}")
        print(f"Sent metrics: {json.dumps(sent)}")
    except json.JSONDecodeError:
        print(f"Failed to decode JSON payload: {msg.payload.decode()}")
    except (KeyError, ValueError) as e:
        print(f"Failed to process payload: {e}")


def run():
    # Print configuration settings
    print("\nCurrent Configuration:")
    print(f"MQTT Host: {MQTT_HOST}")
    print(f"MQTT Port: {MQTT_PORT}")
    print(f"MQTT Username: {MQTT_USERNAME}")
    print(f"MQTT Password: {'*' * len(MQTT_PASSWORD)}")  # Masked for security
    print(f"Dongle: {DONGLE}")
    print(f"Prometheus Port: {PROMETHEUS_PORT}\n")

    # Start Prometheus HTTP server
    start_http_server(PROMETHEUS_PORT)
    print("Prometheus metrics server started on port 8000")

    client = paho.Client(
        client_id=f"python-mqtt-{random.randint(0, 1000)}",
        callback_api_version=paho.CallbackAPIVersion.VERSION2,
    )
    client.on_message = on_message

    if MQTT_USERNAME is not None:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    if client.connect(MQTT_HOST, MQTT_PORT, 60) != 0:
        print("Couldn't connect to the mqtt broker")
        sys.exit(1)

    client.subscribe(f"{DONGLE}/inputbank1")
    client.on_message = on_message

    try:
        print("Press CTRL+C to exit...")
        client.loop_forever()
    except Exception:
        print(traceback.format_exc())
    finally:
        print("Disconnecting from the MQTT broker")
        client.disconnect()

if __name__ == "__main__":
    run()
