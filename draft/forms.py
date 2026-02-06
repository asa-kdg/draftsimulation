from django import forms
from .models import Comment

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text', 'rank', 'velocity', 'command', 'breakingball', 'mechanics',
            'batcontroll', 'power', 'speed', 'defense', 'potential'] # 使う可能性のあるフィールドを全部並べる
        
        
        

    def __init__(self, *args, **kwargs):
        player = kwargs.pop('player', None)
        super().__init__(*args, **kwargs)

        # 対象のフィールドリスト
        rating_fields = [
            'velocity', 'command', 'breakingball', 'mechanics',
            'batcontroll', 'power', 'speed', 'defense', 'potential'
        ]

        # スライダーの設定を一括適用
        for field_name in rating_fields:
            if field_name in self.fields:
                self.fields[field_name].widget = forms.NumberInput(attrs={
                    'type': 'range', # これでスライダーになる
                    'step': '0.1',
                    'min': '1.0',
                    'max': '5.0',
                    'class': 'form-range', # Bootstrapなどを使う場合に便利
                })


        # 1. カテゴリごとのフィールドリストを定義
        pitcher_fields = ['velocity', 'command', 'breakingball', 'mechanics']
        batter_fields = ['batcontroll', 'power', 'speed', 'defense']

        # 2. 条件分岐で「不要な方」を消す
        if player:
            if player.position == 'P':
                # 投手なら、野手用の項目を消す
                self.remove_fields(batter_fields)
            else:
                # 投手以外なら、投手用の項目を消す
                self.remove_fields(pitcher_fields)

    def remove_fields(self, field_list):
        """リストにあるフィールドを安全に削除する補助関数"""
        for field_name in field_list:
            if field_name in self.fields:
                del self.fields[field_name]

            