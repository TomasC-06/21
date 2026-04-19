import random
import threading

class MotorJogo:
    def __init__(self):
        self.lock = threading.Lock()
        self.score = 0
        self.reset_round()
        self.game_over = False

    def reset_round(self):
        self.deck = list(range(1, 12))
        random.shuffle(self.deck)
        
        self.hands = [[self.deck.pop(), self.deck.pop()], [self.deck.pop(), self.deck.pop()]]
        self.stands = [False, False]
        self.round_over = False
        self.current_turn = 0  # 0 para P1, 1 para P2. O Jogador 1 começa
        self.round_winner = None
        self.msg = "Nova ronda! Jogador 1 começa."

    def get_state_for_player(self, player_id):
        opp_id = 1 if player_id == 0 else 0
        with self.lock:
            opp_visible = self.hands[opp_id][1:]
            
            return {
                "score": self.score,
                "game_over": self.game_over,
                "my_hand": self.hands[player_id],
                "opp_visible": opp_visible,
                "my_stand": self.stands[player_id],
                "opp_stand": self.stands[opp_id],
                "round_over": self.round_over,
                "is_my_turn": self.current_turn == player_id,  # Diz ao cliente se é a vez dele
                "msg": self.msg
            }

    def play_action(self, player_id, action):
        with self.lock:
            if self.round_over:
                return {"accepted": False, "logs": [], "round_finished": False}

            #Ignora a jogada se não for a vez dele
            if player_id != self.current_turn:
                return {"accepted": False, "logs": [], "round_finished": False}

            logs = []
            if action == "hit" and not self.stands[player_id]:
                if len(self.deck) > 0:
                    carta = self.deck.pop()
                    self.hands[player_id].append(carta)
                    self.msg = f"Jogador {player_id+1} fez hit e tirou a carta {carta}."
                else:
                    self.msg = f"Jogador {player_id+1} fez hit, mas o baralho está vazio."
                logs.append(self.msg)
            elif action == "stand":
                self.stands[player_id] = True
                self.msg = f"Jogador {player_id+1} fez stand."
                logs.append(self.msg)
            else:
                self.msg = f"Ação ignorada do Jogador {player_id+1}: {action}."
                logs.append(self.msg)

            round_finished = self.check_round_end()


            if not self.round_over:
                opp_id = 1 if player_id == 0 else 0

                if not self.stands[opp_id]:
                    self.current_turn = opp_id

            return {
                "accepted": True,
                "logs": logs,
                "round_finished": round_finished,
            }

    def check_round_end(self):
        if self.stands[0] and self.stands[1]:
            self.round_over = True
            score_p1 = sum(self.hands[0])
            score_p2 = sum(self.hands[1])
            winner = "Empate"

            p1_bust = score_p1 > 21
            p2_bust = score_p2 > 21

            if p1_bust and p2_bust:
                if score_p1 < score_p2: self.score += 1
                elif score_p2 < score_p1:
                    self.score -= 1
                if score_p1 < score_p2:
                    winner = "Jogador 1"
                elif score_p2 < score_p1:
                    winner = "Jogador 2"
            elif p1_bust:
                self.score -= 1
                winner = "Jogador 2"
            elif p2_bust:
                self.score += 1
                winner = "Jogador 1"
            else:
                if score_p1 > score_p2: self.score += 1
                elif score_p2 > score_p1:
                    self.score -= 1

                if score_p1 > score_p2:
                    winner = "Jogador 1"
                elif score_p2 > score_p1:
                    winner = "Jogador 2"

            self.round_winner = winner


            if self.score >= 7:
                self.msg = f"JOGO TERMINADO! Jogador 1 venceu! Score Global:{self.score}"
                self.game_over = True
            elif self.score <= -7:
                self.msg = f"JOGO TERMINADO! Jogador 2 venceu! Score Global:{self.score}"
                self.game_over = True
            else:
                self.msg = (
                f"Ronda terminou! P1:{score_p1} | P2:{score_p2} "
                f"Vencedor: {winner}. Score global: {self.score}"
            )
                return True

        return False