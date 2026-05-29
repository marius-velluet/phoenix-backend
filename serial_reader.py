# serial_reader.py — Passerelle Série USB → MQTT
# Work packages 8.2.1 + 8.2.2 + 8.2.3

import serial
import serial.tools.list_ports
import paho.mqtt.client as mqtt
import json
import time
import argparse
import re

# ── CONFIGURATION ─────────────────────────────────────────────────────
MQTT_HOST  = "localhost"
MQTT_PORT  = 1883
MQTT_TOPIC = "phoenix/alerts"
BAUDRATE   = 115200

# ── CORRECTION JSON (clés sans guillemets) ────────────────────────────
def fix_json(raw: str) -> str:
    """Corrige le JSON sans guillemets autour des clés si nécessaire."""
    return re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', raw)

# ── DÉTECTION AUTOMATIQUE DU PORT ─────────────────────────────────────
def find_port():
    """Trouve automatiquement le port USB de la DFR1195."""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        # La DFR1195 apparaît généralement avec ces identifiants
        if any(kw in port.description for kw in ['USB', 'UART', 'CH340', 'CP210', 'ESP32']):
            print(f"✅ Carte détectée sur {port.device} : {port.description}")
            return port.device
    print("⚠️  Aucune carte détectée automatiquement.")
    print("   Ports disponibles :")
    for port in ports:
        print(f"   - {port.device} : {port.description}")
    return None

# ── PROGRAMME PRINCIPAL ───────────────────────────────────────────────
def main(port=None):
    # 1. Trouver le port série
    if not port:
        port = find_port()
    if not port:
        port = input("Entre le port manuellement (ex: COM3 ou /dev/ttyUSB0) : ").strip()

    # 2. Connexion MQTT
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = lambda c, u, f, rc: print(f"✅ Connecté au broker MQTT (code {rc})")
    client.connect(MQTT_HOST, MQTT_PORT)
    client.loop_start()

    print(f"\n🚀 Lecture du port série {port} à {BAUDRATE} bauds...")
    print(f"📡 Publication sur le topic MQTT : {MQTT_TOPIC}")
    print("   (Ctrl+C pour arrêter)\n")

    # 3. Lecture en boucle avec reconnexion automatique
    while True:
        try:
            with serial.Serial(port, BAUDRATE, timeout=2) as ser:
                print(f"🔌 Port série ouvert : {port}")
                while True:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if not line:
                        continue

                    print(f"📥 Reçu : {line}")

                    # Validation et correction JSON
                    try:
                        fixed = fix_json(line)
                        data  = json.loads(fixed)

                        # Ajout timestamp si absent
                        if 'timestamp' not in data:
                            data['timestamp'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

                        payload = json.dumps(data)
                        client.publish(MQTT_TOPIC, payload, qos=0)
                        print(f"📤 Publié sur MQTT : {payload}")

                    except json.JSONDecodeError as e:
                        print(f"⚠️  JSON invalide ignoré : {line} ({e})")

        except serial.SerialException as e:
            print(f"❌ Erreur port série : {e}")
            print("   Reconnexion dans 3 secondes...")
            time.sleep(3)
        except KeyboardInterrupt:
            print("\n🛑 Arrêt demandé.")
            client.loop_stop()
            client.disconnect()
            break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Passerelle Série → MQTT pour PHOENIX")
    parser.add_argument("--port", help="Port série (ex: COM3 ou /dev/ttyUSB0)", default=None)
    args = parser.parse_args()
    main(args.port)