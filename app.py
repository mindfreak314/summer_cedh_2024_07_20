import streamlit as st
import pandas as pd
import utils

st.set_page_config(page_title="Summer cEDH @ Countdown", page_icon = "👑",  layout="wide")

st.title("Summer cEDH @ Countdown")

ranking_method = utils.hareruya_permutations_with_draw_and_byes

current_round = utils.get_finished_round()

control_sheet = utils.get_control_sheet()
oppo_dict = utils.get_oppo_dict(control_sheet)
match_logs = utils.get_match_logs(control_sheet)
# standings_after_rounds = utils.get_standings_after_rounds(control_sheet, match_logs, method=ranking_method)

@st.cache_data
def prep_control_sheet(control_sheet):
    control_sheet = utils.add_wld(control_sheet, match_logs)
    control_sheet = utils.add_standing(control_sheet, match_logs, method=ranking_method)

    return control_sheet

control_sheet = prep_control_sheet(control_sheet)

search_player = st.text_input('Search player...', '', )


def color_result(result):
    color_map = {
        "win": "green",
        "loss": "red",
        "draw": "yellow", 
        "BYE": "white"
    }
    color = color_map[result]
    return f'color: {color}'

f = {
'Points before':'{:.2f}',
'Points after':'{:.2f}',
'Points':'{:.2f}',
}


# with st.expander("Standing"):
#     control_sheet_standing = control_sheet.copy().reset_index()
#     if search_player:
#         control_sheet_standing = control_sheet_standing[control_sheet_standing.Player.str.lower().str.contains(search_player.lower())]
#     # control_sheet_standing.drop(["dropped", "n_3P_pods"], axis = 1, inplace=True)
#     # control_sheet_standing = control_sheet_standing[["Rank", "Player", "Points", "Regular points", "win", "loss", "draw"]]
#     control_sheet_standing = control_sheet_standing[["Rank", "Player", "Points",]]
#     # control_sheet_standing["Points"] = control_sheet_standing["Points"].astype(int)
#     st.markdown(control_sheet_standing.style.format(f).hide(axis="index").to_html(), unsafe_allow_html=True)




display_round = st.radio("Round selection", [x+1 for x in reversed(range(current_round))], horizontal =True )

if current_round > 0:

    round_df = pd.read_excel("control_sheet.ods", engine="odf", sheet_name=f"round {display_round}")
    if search_player:
        round_df = round_df[round_df.Player.str.lower().str.contains(search_player.lower())]

    if 'Result' in round_df.columns:
        # merge with poitns before and after
        round_df = (
            round_df
            # .merge(standings_after_rounds[display_round-1].rename({"Points":"Points before"}, axis = 1).reset_index(),  on="Player")
            # .merge(standings_after_rounds[display_round].rename({"Points":"Points after"}, axis = 1).reset_index(),  on="Player")
            )
        
        # round_df[["Points before", "Points after"]] = round_df[["Points before", "Points after"]].astype(int)
        # round_df[["Points before", "Points after"]] = round_df[["Points before", "Points after"]].round(decimals=2)
        round_df = round_df.style.applymap(color_result, subset=['Result']).format(f).hide(axis="index")
    else:
        round_df = round_df.style.hide(axis="index")

    st.markdown(round_df.to_html(), unsafe_allow_html=True)