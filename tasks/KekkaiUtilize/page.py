from tasks.Component.ReplaceShikigami.assets import ReplaceShikigamiAssets
from tasks.GameUi.page import Page, page_guild, random_click
from tasks.GlobalGame.assets import GlobalGameAssets
from tasks.KekkaiUtilize.assets import KekkaiUtilizeAssets

# 阴阳寮结界页面
page_guild_realm = Page(KekkaiUtilizeAssets.I_REALM_SHIN)
page_guild_realm.link(button=GlobalGameAssets.I_UI_BACK_YELLOW, destination=page_guild)
page_guild.link(button=KekkaiUtilizeAssets.I_GUILD_REALM, destination=page_guild_realm)
# 结界育成页面
page_guild_realm_growth = Page(ReplaceShikigamiAssets.I_RS_RECORDS_SHIKI)
page_guild_realm.link(button=KekkaiUtilizeAssets.I_SHI_GROWN, destination=page_guild_realm_growth)
page_guild_realm_growth.link(button=GlobalGameAssets.I_UI_BACK_BLUE, destination=page_guild_realm)
# 蹭卡页面
page_guild_realm_utilize = Page(KekkaiUtilizeAssets.I_U_ENTER_REALM)
page_guild_realm_utilize.link(button=random_click, destination=page_guild_realm_growth)
page_guild_realm_growth.link(button=KekkaiUtilizeAssets.I_UTILIZE_ADD, destination=page_guild_realm_utilize)
