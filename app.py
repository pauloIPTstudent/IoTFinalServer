import os
import ssl
from flask import Flask, render_template_string
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt

# Configurações Oficiais do seu Broker HiveMQ Cloud
MQTT_BROKER = "752c1a993df64a28b80430f7f0948d2f.s1.eu.hivemq.cloud" 
MQTT_PORT = 8883  # Porta segura obrigatória para instâncias Cloud do HiveMQ
MQTT_USER = "KinectV"
MQTT_PASS = "Qwe12345"
MQTT_TOPIC = "status"

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# HTML integrado em String para manter a facilidade de ficheiro único
HTML_PAGE = """
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel de Monitorização - Quedas</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; background-color: #f5f6fa; padding: 50px; }
        .card { background: white; padding: 30px; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); display: inline-block; min-width: 320px; }
        #status-box { font-size: 24px; font-weight: bold; margin-top: 20px; padding: 20px; border-radius: 10px; transition: all 0.3s ease; }
        .seguro { background-color: #D4EDDA; color: #155724; border: 2px solid #c3e6cb; }
        .possivel-queda { background-color: #FFF3CD; color: #856404; border: 2px solid #ffeeba; animation: blink 1s infinite; }
        @keyframes blink { 50% { opacity: 0.5; } }
    </style>
</head>
<body>
    <div class="card">
        <h2>Estado do Utilizador</h2>
        <div id="status-box" class="seguro">✅ Movimento Normal Seguro</div>
    </div>

    <script>
        var socket = io();

        // Escuta o evento em tempo real via WebSockets sem bloquear a página
        socket.on('atualizar_status', function(data) {
            var box = document.getElementById('status-box');
            if (data.id === '9') {
                box.innerText = "🚨 POSSÍVEL QUEDA DETETADA!";
                box.className = "possivel-queda";
            } else if (data.id === '0') {
                box.innerText = "✅ Movimento Normal Seguro";
                box.className = "seguro";
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

# --- CONFIGURAÇÃO DO CLIENTE MQTT COM TLS SEGURO ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"🚀 Servidor Flask conectado com SUCESSO ao HiveMQ Cloud!")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"❌ Erro na ligação ao HiveMQ Cloud. Código de retorno: {rc}")

def on_message(client, userdata, msg):
    payload = msg.payload.decode('utf-8')
    print(f"📥 Dados recebidos no tópico '{msg.topic}': {payload}")
    
    # Encaminha o evento diretamente para o frontend
    socketio.emit('atualizar_status', {'id': payload})

# Inicialização e parametrização do protocolo seguro
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# 1. Configura as credenciais de utilizador da plataforma
mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)

# 2. Ativa a camada TLS necessária para a porta 8883
mqtt_client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2)
mqtt_client.tls_insecure_set(False)

try:
    print(f"A estabelecer ligação segura a {MQTT_BROKER}...")
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()  # Mantém a escuta ativa em background paralela ao Flask
except Exception as e:
    print(f"Falha crítica na ligação MQTT: {e}")

if __name__ == '__main__':
    # Inicializa a aplicação local na porta 5000
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)