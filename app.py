import os
from flask import Flask, render_template_string
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt

# Configurações do Broker (Mude para as credenciais do seu HiveMQ)
MQTT_BROKER = "seu-broker-do-hivemq.com" 
MQTT_PORT = 1883  # Porta padrão TCP para o backend se conectar (Nota: a 8884 de websockets é usada no frontend se necessário, mas o backend Python conecta nativamente por TCP)
MQTT_TOPIC = "status"

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# HTML embutido em String para manter tudo num único ficheiro
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
        .card { background: white; padding: 30px; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); display: inline-block; min-width: 300px; }
        #status-box { font-size: 24px; font-weight: bold; margin-top: 20px; padding: 15px; border-radius: 10px; transition: all 0.3s ease; }
        .seguro { background-color: #D4EDDA; color: #155724; }
        .possivel-queda { background-color: #FFF3CD; color: #856404; animation: blink 1s infinite; }
        @keyframes blink { 50% { opacity: 0.6; } }
    </style>
</head>
<body>
    <div class="card">
        <h2>Estado do Utilizador</h2>
        <div id="status-box" class="seguro">✅ Movimento Normal Seguro</div>
    </div>

    <script>
        var socket = io();

        // Escuta o evento enviado pelo servidor Flask em tempo real
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

# --- CONFIGURAÇÃO DO CLIENTE MQTT (PAHO) ---
def on_connect(client, userdata, flags, rc):
    print(f"Servidor Flask conectado ao HiveMQ com resultado: {rc}")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    payload = msg.payload.decode('utf-8')
    print(f"📥 Mensagem recebida no tópico {msg.topic}: {payload}")
    
    # Repassa a mensagem via WebSocket para o navegador instantaneamente
    socketio.emit('atualizar_status', {'id': payload})

# Inicializa o cliente MQTT em background
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# Se o seu HiveMQ exigir usuário e senha, descomente a linha abaixo:
# mqtt_client.username_pw_set("seu_usuario", "sua_senha")

try:
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start() # Roda o MQTT numa thread paralela para não travar o Flask
except Exception as e:
    print(f"Erro ao conectar ao Broker MQTT: {e}")

if __name__ == '__main__':
    # Roda o servidor Flask com suporte a WebSockets
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)