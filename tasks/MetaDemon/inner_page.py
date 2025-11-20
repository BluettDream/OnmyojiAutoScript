from tasks.GameUi.assets import GameUiAssets
from tasks.GameUi.page import Page, page_act_list, page_main, page_shikigami_records, page_reward, random_click, \
    page_failed, page_battle
from tasks.GlobalGame.assets import GlobalGameAssets
from tasks.MetaDemon.assets import MetaDemonAssets

# 活动列表页超鬼王活动
page_act_list_meta_demon = Page(MetaDemonAssets.I_CHECK_ACT_LIST_METADEMON_ACT)
page_act_list.link(button=MetaDemonAssets.L_GOTO_METADEMON_LIST, destination=page_act_list_meta_demon)
page_act_list_meta_demon.link(button=GlobalGameAssets.I_UI_BACK_YELLOW, destination=page_main)
# 超鬼王主界面
page_meta_demon = Page(MetaDemonAssets.I_MD_CHECK_MAIN_PAGE)
page_meta_demon.additional = [MetaDemonAssets.I_MD_GET_YESTERDAY_REWARD, MetaDemonAssets.I_MD_CLOSE_POPUP]
page_meta_demon.link(button=GlobalGameAssets.I_UI_BACK_YELLOW, destination=page_act_list_meta_demon)
page_act_list_meta_demon.link(button=GameUiAssets.I_ACT_LIST_GOTO_ACT, destination=page_meta_demon)
# 超鬼王boss界面
page_meta_demon_boss = Page(MetaDemonAssets.I_CHECK_BOSS_PAGE)
page_meta_demon_boss.additional = [MetaDemonAssets.I_MD_CLOSE_POPUP]
page_meta_demon_boss.link(button=GlobalGameAssets.I_UI_BACK_YELLOW, destination=page_meta_demon)
page_meta_demon.link(button=MetaDemonAssets.I_MD_CHECK_MAIN_PAGE, destination=page_meta_demon_boss)

# 更改战斗结算界面
page_reward.link(button=random_click(), destination=page_meta_demon_boss)
page_failed.link(button=random_click(), destination=page_meta_demon_boss)
