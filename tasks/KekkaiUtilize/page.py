from tasks.GameUi.page import Page, page_guild
from tasks.GlobalGame.assets import GlobalGameAssets
from tasks.KekkaiUtilize.assets import KekkaiUtilizeAssets

page_guild_realm = Page(KekkaiUtilizeAssets.I_REALM_SHIN)
page_guild_realm.link(button=GlobalGameAssets.I_UI_BACK_BLUE, destination=page_guild)
page_guild.link(button=KekkaiUtilizeAssets.I_GUILD_REALM, destination=page_guild_realm)
