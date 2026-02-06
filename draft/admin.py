from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .models import Player, Team, Comment

# インポート・エクスポートのルール設定
class PlayerResource(resources.ModelResource):
    class Meta:
        model = Player
        # CSVの列名とモデルのフィールド名を一致させる
        fields = ('id', 'name', 'category', 'position', 'team', 'bats_throws', 'height', 'weight', 'introduction', 'scout_comment')

@admin.register(Player)
class PlayerAdmin(ImportExportModelAdmin):
    resource_class = PlayerResource
    list_display = ('name', 'category', 'position', 'team')  # 一覧で見やすく

admin.site.register(Team)
admin.site.register(Comment)