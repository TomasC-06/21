import socket
import json
import threading
import servidor
from servidor.maquina.motor_jogo import MotorJogo

class Maquina:
    def __init__(self):
        self.s = socket.socket()
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind(('', servidor.PORT))
        self.motor = MotorJogo()
        self.clients = []

    def receive_exact(self, connection, n_bytes):
        # Utiliza o ciclo while para que continue a ler as informações que vêm do socket até ter o n_bytes exigidos do protocolo
        data = bytearray()
        while len(data) < n_bytes:
            chunk = connection.recv(n_bytes - len(data))
            if not chunk:
                raise ConnectionError("Ligação encerrada durante a receção de dados")
            data.extend(chunk)
        return bytes(data)

    def receive_int(self, connection, n_bytes):
        data = self.receive_exact(connection, n_bytes)
        return int.from_bytes(data, byteorder='big', signed=True)

    def send_int(self, connection, value, n_bytes):
        connection.sendall(value.to_bytes(n_bytes, byteorder="big", signed=True))

    def send_object(self, connection, obj):
        data = json.dumps(obj).encode('utf-8')
        size = len(data)
        self.send_int(connection, size, servidor.INT_SIZE)
        connection.sendall(data)

    def receive_object(self, connection):
        size = self.receive_int(connection, servidor.INT_SIZE)
        data = self.receive_exact(connection, size)
        return json.loads(data.decode('utf-8'))

    def handle_client(self, conn, player_id):
        # Função principal de cada Thread
        print(f"Jogador {player_id+1} pronto.")
        self.send_object(conn, self.motor.get_state_for_player(player_id))
        
        keep_running = True
        while keep_running:
            try:

                if self.motor.game_over:
                    break
                # Pede informação ao cliente
                request = self.receive_object(conn)
                action = request.get("action")
                
                result = self.motor.play_action(player_id, action)
                self.broadcast_state()
                # 1. Verifica se o jogo já terminou
                if self.motor.game_over:
                    print(f"Jogo terminou (Score: {self.motor.score}). A encerrar ligação do P{player_id + 1}...")
                    keep_running = False

                # 2. Verifica se a ronda acabou
                if result["round_finished"]:
                    print(f"Fim de ronda detetado na thread do P{player_id + 1}")
                    print(self.motor.msg)

                    self.motor.reset_round()
                    print("Ronda reiniciada. Enviando novo estado...")
                    self.broadcast_state()
            except (ConnectionError, BrokenPipeError, EOFError):
                keep_running = False

            except Exception as e:
                print(f"Erro com Jogador {player_id+1}: {e}")
                keep_running = False



    def broadcast_state(self):
        # para todas os clientes, manda o estado do jogo
        for i, conn in enumerate(self.clients):
            try:
                self.send_object(conn, self.motor.get_state_for_player(i))
            except:
                pass

    def execute(self):
        self.s.listen(2)
        print(f"À espera de 2 jogadores na porta {servidor.PORT}...")
        
        # Aceita P1 e P2
        conn1, addr1 = self.s.accept()
        print("Jogador 1 conectou-se:", addr1)
        self.clients.append(conn1)

        conn2, addr2 = self.s.accept()
        print("Jogador 2 conectou-se:", addr2)
        self.clients.append(conn2)

        print("Ambos os jogadores conectados. A iniciar jogo...")

        # Inicia uma thread para cada jogador para escutar ações ao mesmo tempo
        t1 = threading.Thread(target=self.handle_client, args=(conn1, 0))
        t2 = threading.Thread(target=self.handle_client, args=(conn2, 1))
        
        t1.start()
        t2.start()
        
        t1.join()
        t2.join()
        self.s.close()