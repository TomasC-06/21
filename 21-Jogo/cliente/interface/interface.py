import socket
import json
import cliente

class Interface:
    def __init__(self):
        self.connection = socket.socket()
        self.connection.connect((cliente.SERVER_ADDRESS, cliente.PORT))

    def receive_exact(self, connection, n_bytes):
        data = bytearray()
        while len(data) < n_bytes:
            chunk = connection.recv(n_bytes - len(data))
            if not chunk:
                raise ConnectionError("Ligação encerrada durante a receção de dados")
            data.extend(chunk)
        return bytes(data)

    def send_int(self, connect, value, n_bytes):
        connect.sendall(value.to_bytes(n_bytes, byteorder="big", signed=True))

    def receive_int(self, connect, n_bytes):
        data = self.receive_exact(connect, n_bytes)
        return int.from_bytes(data, byteorder='big', signed=True)

    def send_object(self, connection, obj):
        data = json.dumps(obj).encode('utf-8')
        size = len(data)
        self.send_int(connection, size, cliente.INT_SIZE)
        connection.sendall(data)

    def receive_object(self, connection):
        size = self.receive_int(connection, cliente.INT_SIZE)
        data = self.receive_exact(connection, size)
        return json.loads(data.decode('utf-8'))

    def execute(self):
        print("Conectado ao servidor! À espera que o jogo comece...")
        
        while True:
            try:
                # 1. Recebe estado atual
                estado = self.receive_object(self.connection)
                
                print("\n" + "="*30)
                print(f"MENSAGEM: {estado['msg']}")
                print(f"SCORE GLOBAL: {estado['score']}")
                print(f"A TUA MÃO: {estado['my_hand']} (Soma: {sum(estado['my_hand'])})")
                print(f"CARTAS VISÍVEIS DO ADVERSÁRIO: {estado['opp_visible']}")
                print(f"O teu estado de stand: {estado['my_stand']} | Adversário: {estado['opp_stand']}")
                print("="*30)

                if estado.get('game_over'):
                    print("\n" + "#" * 30)
                    print(f"VITÓRIA FINAL: {estado['msg']}")
                    print("#" * 30)
                    break

                if estado['round_over']:
                    print("Ronda acabou. A aguardar o reinício automático...")
                    continue

                # 2. Verifica de quem é a vez
                if estado['is_my_turn']:
                    acao = input("-> É A TUA VEZ! O que queres fazer? (hit / stand): ").strip().lower()
                    while acao not in ["hit", "stand"]:
                        acao = input("Ação inválida. Escolhe 'hit' ou 'stand': ").strip().lower()
                    
                    self.send_object(self.connection, {"action": acao})
                else:
                    # Se não for a sua vez, o código passa aqui e volta ao início do while, 
                    # bloqueando no 'receive_object' à espera que o servidor envie o próximo estado
                    print("-> A aguardar a jogada do adversário...")
                    
            except Exception as e:
                print(f"Conexão perdida ou erro: {e}")
                break