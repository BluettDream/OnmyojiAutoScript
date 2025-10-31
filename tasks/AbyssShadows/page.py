from tasks.AbyssShadows.assets import AbyssShadowsAssets
from tasks.GameUi.assets import GameUiAssets
from tasks.GameUi.game_ui import GameUi
from tasks.GameUi.page import Page, page_guild

page_guild_shenshe = Page(AbyssShadowsAssets.I_CHECK_SHENSHE)
page_guild.link(button=AbyssShadowsAssets.I_RYOU_SHENSHE, destination=page_guild_shenshe)
page_guild_shenshe.link(button=GameUiAssets.I_BACK_Y, destination=page_guild)

page_abyss = Page(AbyssShadowsAssets.I_CHECK_ABYSS)
page_guild_shenshe.link(button=AbyssShadowsAssets.L_SHENSHE_TO_ABYSS, destination=page_abyss)
page_abyss.link(button=GameUiAssets.I_BACK_BLUE, destination=page_guild_shenshe)
