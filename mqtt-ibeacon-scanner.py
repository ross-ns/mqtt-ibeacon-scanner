#!/usr/bin/env python3

import os
import configparser
import paho.mqtt.client as mqtt
from bluetooth.ble import BeaconService
import time

# Get application file name without extension
app_file_name = os.path.splitext(os.path.basename(__file__))[0]
# Get config file name based on application file name
config_file = os.getenv('config_file', app_file_name + '.conf')

# Read the config file
config = configparser.ConfigParser()
config.read(config_file)

# Assign variables from config file
uuid = config.get("ibeacon", "uuid")
scan_wait = config.getint("ibeacon", "scan_wait")
consider_away = config.getint("ibeacon", "consider_away")
mqtt_certfile = config.get("mqtt", "mqtt_certfile")
mqtt_selfsignedcert = config.getboolean("mqtt", "mqtt_selfsignedcert")
mqtt_username = config.get("mqtt", "mqtt_username")
mqtt_password = config.get("mqtt", "mqtt_password")
mqtt_topic = config.get("mqtt", "mqtt_topic")
mqtt_payload_on = config.getint("mqtt", "mqtt_payload_on")
mqtt_payload_off = config.getint("mqtt", "mqtt_payload_off")
mqtt_retain = config.getboolean("mqtt", "mqtt_retain")
mqtt_qos = config.getint("mqtt", "mqtt_qos")
mqtt_host = config.get("mqtt", "mqtt_host")
mqtt_port = config.getint("mqtt", "mqtt_port")
mqtt_ttl = config.getint("mqtt", "mqtt_ttl")

# Assign some variables
topic_pub = mqtt_topic + "/" + uuid             # Combines the topic and device UUID
published_on = False
published_off = False
last_seen = 0

# Create the MQTT client
mqtt_client = mqtt.Client("lods")
mqtt_client.tls_set(mqtt_certfile)
mqtt_client.tls_insecure_set(mqtt_selfsignedcert)
mqtt_client.username_pw_set(mqtt_username, mqtt_password)


# Scan for beacons function
def beacon_scan():
    service = BeaconService()
    return service.scan(2)


# Check if our beacon was found
def check_for_beacon(device_list=[]):
    for key in device_list.keys():
        if uuid in device_list[key]:
            return True
        else:
            return False


# Connect to the broker and publish the topic, message and payload, then gracefully disconnect
def mqtt_message_publish():
    mqtt_client.connect(mqtt_host, mqtt_port, mqtt_ttl)
    mqtt_client.publish(topic_pub, mqtt_payload, mqtt_qos, mqtt_retain)
    mqtt_client.disconnect()


while True:
    if check_for_beacon(beacon_scan()):
        if published_on:
            time.sleep(scan_wait)
        else:
            mqtt_payload = mqtt_payload_on
            mqtt_message_publish()
            published_on = True
            published_off = False
            last_seen = 0
            time.sleep(scan_wait)
    else:
        if published_off:
            time.sleep(scan_wait)
        elif last_seen < consider_away:
            last_seen += 1
            time.sleep(scan_wait)
        else:
            mqtt_payload = mqtt_payload_off
            mqtt_message_publish()
            published_off = True
            published_on = False
            time.sleep(scan_wait)
