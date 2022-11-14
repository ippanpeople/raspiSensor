import random
import time
import RPi.GPIO as GPIO
import board
import adafruit_dht
#import Adafruit_DHT
import mysql.connector                          # MySQL
from paho.mqtt import client as mqtt_client     # Mqtt

# GPIO 初期設定
GPIO.setwarnings(True)
GPIO.setmode(GPIO.BCM)

# 温湿度センサー初期設定
# SENSOR = Adafruit_DHT.DHT11
# SENSOR_PIN = 26
dhtDevice = adafruit_dht.DHT11(board.D26)

# MySQL DB の接続設定
Raspi_db = mysql.connector.connect(
    user = 'your_db_user',
    password = 'your_db_password',
    host = 'your_db_host',
    database = 'your_db_table',
    auth_plugin='mysql_native_password'
)

# Mqtt の接続設定
broker = 'your_mqtt_broker_ip_address'
port = 1883
topic = "your_topic"
client_id = f'python-mqtt-{random.randint(0, 1000)}'

# Mqtt の接続関数
def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)
    # Set Connecting Client ID
    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def destroy():
    dhtDevice.exit()
    GPIO.cleanup()


def main():
    # Mqtt brokerに接続
    client = connect_mqtt()

    while True:
        try:
            # humi, temp = Adafruit_DHT.read(SENSOR, SENSOR_PIN) 
            # if temp is not None and humi is not None:
            temp = dhtDevice.temperature
            humi = dhtDevice.humidity
            if temp is not None and humi is not None: 
                # publishメッセージ
                msg = '溫度={0:0.1f}度C 濕度={1:0.1f}%'.format(temp, humi)
                result = client.publish(topic, msg)
                print("Mqtt publish status : ", result[0])

                mycursor = Raspi_db.cursor()
                mycursor.execute("INSERT INTO dht11 ( DATE, TIME, TEMPERATURE, HUMIDITY ) VALUES ( current_date(), current_time(), %s, %s)", (temp, humi))
                Raspi_db.commit()

                mycursor.execute("SELECT * FROM dht11 ORDER BY DATE DESC, TIME DESC LIMIT 1")
        
                for x in mycursor:
                    print(x)
        except RuntimeError as error:
            print(error.args[0])
            time.sleep(5)
            continue
        except Exception as error:
            dhtDevice.exit()
            raise error
    
        time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        destroy()
