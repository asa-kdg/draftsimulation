# draft/simulation.py
import random
from .models import Player, Team

class DraftManager:
    def __init__(self, session):
        self.session = session

    def resolve_lottery(self):
        """1巡目の抽選を行い、結果を返す"""
        current_bids = self.session.get("current_bids", {})
        draft_picks = self.session.get("draft_picks", {})
        team_ids = self.session.get("teams", [])

        player_to_teams = {}
        for t_id, p_id in current_bids.items():
            player_to_teams.setdefault(str(p_id), []).append(int(t_id))

        new_pending_ids = []
        messages = []

        for p_id, t_ids in player_to_teams.items():
            player = Player.objects.get(id=p_id)
            if len(t_ids) > 1:
                winner_id = random.choice(t_ids)
                for t_id in t_ids:
                    team_obj = Team.objects.get(id=t_id)
                    if t_id == winner_id:
                        draft_picks[str(t_id)].append(int(p_id))
                        messages.append(f"【当選】{team_obj.name}が{player.name}の交渉権獲得！")
                    else:
                        new_pending_ids.append(t_id)
                        messages.append(f"【外れ】{team_obj.name}は抽選に外れました。")
            else:
                t_id = t_ids[0]
                team_obj = Team.objects.get(id=t_id)
                draft_picks[str(t_id)].append(int(p_id))
                messages.append(f"【確定】{team_obj.name}が{player.name}を単独指名！")

        update_data = {
            "draft_picks": draft_picks,
            "pending_teams": new_pending_ids,
            "current_bids": {},
            "lottery_messages": messages,
        }

        # --- ここが重要：順序の制御 ---
        if not new_pending_ids:
            # 12チーム全員の1位が決まった瞬間
            update_data.update({
                "draft_phase": "waiver",
                "current_round": 2,
                "current_team_index": 0, # 再びリストの先頭（12位）から開始
                "direction": 1          # 12位 -> 1位へ向かって進む
            })
        else:
            # まだ決まっていないチームがある（外れ1位指名）
            update_data.update({
                "current_team_index": 0,
                "direction": 1
            })
            
        return update_data

    def get_next_state(self, idx, direction, current_round):
        """2巡目以降の蛇行指名（スネーク）制御"""
        team_ids = self.session.get("teams", [])
        finished_teams = self.session.get("finished_teams", [])
        
        if len(finished_teams) >= len(team_ids) or current_round > 12:
            return None

        # 指名可能なチームを探すループ
        for _ in range(len(team_ids) * 2): # 折り返しを考慮して多めに回す
            idx += direction

            # リストの右端（1位）を超えた場合
            if idx >= len(team_ids):
                current_round += 1
                direction = -1      # 折り返して 1位 -> 12位へ
                idx = len(team_ids) - 1
            # リストの左端（12位）を超えた場合
            elif idx < 0:
                current_round += 1
                direction = 1       # 折り返して 12位 -> 1位へ
                idx = 0

            if current_round > 12:
                return None

            # 指名終了していないチームが見つかったら即座に返す
            if team_ids[idx] not in finished_teams:
                return {
                    "current_team_index": idx,
                    "direction": direction,
                    "current_round": current_round
                }
        return None