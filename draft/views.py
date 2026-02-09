from django.shortcuts import render, get_object_or_404, redirect
from .models import Player, Team, Pick, Comment
from django.db.models import Q, Avg, Case, When, IntegerField, Value, CharField, FloatField
from .simulation import DraftManager
from .forms import CommentForm

# --- 1. 基本機能（一覧・詳細） ---

def index(request):
    q = request.GET.get('q', '')
    players = Player.objects.all()

    if q:
        # 1. 日本語の検索ワードをコードに変換するマップ
        pos_map = {
        '投手': 'P',
        '捕手': 'C',
        '内野手': 'IF',
        '外野手': 'OF',
        }
    
        pos_code = pos_map.get(q)

        # 2. クエリの組み立て
        # 名前か所属にキーワードが含まれているか
        query = Q(name__icontains=q) | Q(team__icontains=q)

        if pos_code:
            # 「外野手」と打たれたら、DBの「OF」を直接狙い撃ち
            query |= Q(position__iexact=pos_code)
        else:
            # それ以外（"P"や"捕手"以外の文字など）は部分一致で検索
            query |= Q(position__icontains=q)

        # 3. 最後に一回だけフィルターをかける（上書きしない！）
        players = players.filter(query)

    # 1. 表示したいカテゴリとポジションの順序を定義
    category_order = ['HS', 'UNIV', 'IND']
    position_order = ['P', 'C', 'IF', 'OF']

    # 2. 辞書を初期化（これ自体には順序がないが、ループで使う際に制御する）
    raw_data = {}
    for p in players:
        raw_data.setdefault(p.category, {})
        raw_data[p.category].setdefault(p.position, [])
        raw_data[p.category][p.position].append(p)

    # 3. 定義した順序に従って、整理されたリストを作成する
    grouped_list = []
    for cat in category_order:
        if cat in raw_data:
            cat_data = {'id': cat, 'positions': []}
            for pos in position_order:
                if pos in raw_data[cat]:
                    cat_data['positions'].append({
                        'id': pos,
                        'players': raw_data[cat][pos]
                    })
            grouped_list.append(cat_data)

    return render(request, 'draft/index.html', {
        'grouped_list': grouped_list
    })


def detail(request, pk):
    player = get_object_or_404(Player, pk=pk)
    all_comments = player.comments.all()

    # 投稿された全コメントの平均値を計算
    averages = all_comments.aggregate(
        avg_velocity=Avg('velocity'),
        avg_command=Avg('command'),
        avg_breakingball=Avg('breakingball'),
        avg_mechanics=Avg('mechanics'),
        avg_batcontroll=Avg('batcontroll'),
        avg_power=Avg('power'),
        avg_speed=Avg('speed'),
        avg_defense=Avg('defense'),
        avg_potential=Avg('potential'),
    )

    # --- 2. ランク（文字列）の平均計算 ---
    rank_map = {'S': 5, 'A': 4, 'B': 3, 'C': 2, 'D': 1}
    inv_rank_map = {v: k for k, v in rank_map.items()} # {5: 'S', 4: 'A', ...}
    
    avg_rank_display = "-" # コメントがない場合の初期値
    
    if all_comments.exists():
        # 全コメントのランクを数値に変換して合計を出す
        rank_values = [rank_map.get(c.rank, 0) for c in all_comments if c.rank in rank_map]
        if rank_values:
            avg_rank_num = sum(rank_values) / len(rank_values)
            # 四捨五入して、一番近いランク文字に戻す（例: 4.2 -> 4 -> 'A'）
            avg_rank_display = inv_rank_map.get(round(avg_rank_num), "-")
    
    if request.method == 'POST':
        form = CommentForm(request.POST, player=player)
        if form.is_valid():
            comment = form.save(commit=False) # まだ保存しない
            comment.player = player           # どの選手へのコメントか紐付け
            comment.save()                    # ここで保存
            return redirect('draft:detail', pk=pk)
    else:
        form = CommentForm(player=player)

    return render(request, 'draft/detail.html', {
        'player': player,
        'form': form, # テンプレートにフォームを渡す
        'averages':averages, #平均データをテンプレートへ
        'avg_rank': avg_rank_display, # 平均ランクを渡す
    })

# --- 2. シミュレーション制御（交通整理） ---

def simulation_start(request):
    """初期化して1巡目から開始"""
    request.session.flush()
    teams = list(Team.objects.order_by("-order"))
    t_ids = [t.id for t in teams]
    
    request.session.update({
        "teams": t_ids,
        "draft_picks": {str(tid): [] for tid in t_ids},
        "finished_teams": [],
        "draft_phase": "1st_round",
        "pending_teams": t_ids,
        "current_team_index": 0,
        "current_bids": {},
        "current_round": 1,
        "direction": 1,
        "lottery_messages": []
    })
    return redirect("draft:simulation_play")

def simulation_play(request):
    """指名画面の表示"""
    if "teams" not in request.session:
        return redirect("draft:simulation_start")

    phase = request.session.get("draft_phase")
    draft_picks = request.session.get("draft_picks", {})
    # すでに指名が確定している選手を除外（1巡目の入札中の選手は除外しない）
    picked_ids = [int(pid) for pids in draft_picks.values() for pid in pids]
    
    if phase == "1st_round":
        pending_ids = request.session.get("pending_teams", [])
        idx = request.session.get("current_team_index", 0)
        current_team = Team.objects.get(id=pending_ids[idx])
    else:
        team_ids = request.session["teams"]
        idx = request.session["current_team_index"]
        current_team = Team.objects.get(id=team_ids[idx])

    players = Player.objects.exclude(id__in=picked_ids).annotate(
        # ランクを数値に置換して平均を出す
        avg_rank_num=Avg(
            Case(
                When(comments__rank='S', then=Value(5.0)),
                When(comments__rank='A', then=Value(4.0)),
                When(comments__rank='B', then=Value(3.0)),
                When(comments__rank='C', then=Value(2.0)),
                When(comments__rank='D', then=Value(1.0)),
                output_field=FloatField(),
            )
        )
    ).annotate(
        # 平均値に基づいてランク文字を決める
        display_rank=Case(
            When(avg_rank_num__gte=4.5, then=Value('S')),
            When(avg_rank_num__gte=3.5, then=Value('A')),
            When(avg_rank_num__gte=2.5, then=Value('B')),
            When(avg_rank_num__gte=1.5, then=Value('C')),
            When(avg_rank_num__gt=0, then=Value('D')),
            default=Value('-'),
            output_field=CharField(),
        )
    ).order_by('-avg_rank_num', 'name') # 高い順

    # 画面右側の指名リスト作成
    teams_with_picks = []
    for tid in request.session["teams"]:
        team_obj = Team.objects.get(id=tid)
        p_ids = draft_picks.get(str(tid), [])
        ordered_players = [Player.objects.get(id=pid) for pid in p_ids]
        teams_with_picks.append({"name": team_obj.name, "first_color": team_obj.first_color, "second_color": team_obj.second_color, "picks": ordered_players})

    return render(request, "draft/simulation_play.html", {
        "team": current_team,
        "players": players,
        "teams": teams_with_picks,
        "round": request.session.get("current_round"),
        "lottery_messages": request.session.get("lottery_messages", [])
    })

def resolve_lottery(request):
    """マネージャーを呼んで抽選を実行"""
    manager = DraftManager(request.session)
    results = manager.resolve_lottery()
    for key, value in results.items():
        request.session[key] = value
    return redirect("draft:simulation_play")

def pick_player(request):
    """指名実行"""
    if request.method == "POST":
        player_id_raw = request.POST.get("player_id")
        if not player_id_raw:
            return redirect("draft:simulation_play")
            
        player_id = int(player_id_raw)
        phase = request.session.get("draft_phase")
        manager = DraftManager(request.session)

        if phase == "1st_round":
            pending_ids = request.session["pending_teams"]
            idx = request.session["current_team_index"]
            current_bids = request.session.get("current_bids", {})
            current_bids[str(pending_ids[idx])] = player_id
            request.session["current_bids"] = current_bids
            request.session["lottery_messages"] = []

            if len(current_bids) == len(pending_ids):
                return resolve_lottery(request)
            else:
                request.session["current_team_index"] = idx + request.session.get("direction", 1)
        else:
            draft_picks = request.session["draft_picks"]
            team_ids = request.session["teams"]
            idx = request.session["current_team_index"]
            draft_picks[str(team_ids[idx])].append(player_id)
            request.session["draft_picks"] = draft_picks
            
            next_state = manager.get_next_state(idx, request.session["direction"], request.session["current_round"])
            if next_state is None:
                return redirect("draft:simulation_result")
            request.session.update(next_state)

    return redirect("draft:simulation_play")

def skip_team(request):
    """指名終了（パス）"""
    if request.method == "POST":
        if request.session.get("draft_phase") == "1st_round":
            return redirect("draft:simulation_play")
            
        finished_teams = request.session.get("finished_teams", [])
        current_team_id = request.session["teams"][request.session["current_team_index"]]
        if current_team_id not in finished_teams:
            finished_teams.append(current_team_id)
            request.session["finished_teams"] = finished_teams
        
        manager = DraftManager(request.session)
        next_state = manager.get_next_state(request.session["current_team_index"], request.session["direction"], request.session["current_round"])
        
        if next_state is None:
            return redirect("draft:simulation_result")
        request.session.update(next_state)
        
    return redirect("draft:simulation_play")

def simulation_result(request):
    """結果画面の表示"""
    draft_picks = request.session.get("draft_picks", {})
    teams = Team.objects.order_by("order")
    result_data = []
    max_picks = 0
    for team_obj in teams:
        p_ids = draft_picks.get(str(team_obj.id), [])
        players = [Player.objects.get(id=pid) for pid in p_ids]
        result_data.append({"team": team_obj, "players": players})
        max_picks = max(max_picks, len(players))
    
    return render(request, "draft/simulation_result.html", {
        "result_data": result_data,
        "range_max": range(1, max_picks + 1)
    })