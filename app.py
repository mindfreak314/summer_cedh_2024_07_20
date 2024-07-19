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


########################################################################################################################
# maual R1 losses
r1_loss = [
    # "",
]
loss_matches = []
for player in r1_loss:
    match_log_element = {}
    match_log_element["match_players"] = [player]
    match_log_element["match_result"] = "loss"
    match_log_element["round"] = 1
    match_log_element["pod"] = 0
    loss_matches.append(match_log_element)
match_logs = loss_matches + match_logs
########################################################################################################################

# @st.cache_data
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


try:
    top4_df = pd.read_excel("control_sheet.ods", engine="odf", sheet_name="top 4")
    if 'Result' in top4_df.columns:
        top4_df = top4_df.style.applymap(color_result, subset=['Result']).format(f).hide(axis="index")
    else:
        top4_df = top4_df.style.hide(axis="index")
    with st.expander("Top 4"):
        st.markdown(top4_df.to_html(), unsafe_allow_html=True)
except:
    pass

try:
    top16_df = pd.read_excel("control_sheet.ods", engine="odf", sheet_name="top 16")
    if 'Result' in top16_df.columns:
        top16_df = top16_df.style.applymap(color_result, subset=['Result']).format(f).hide(axis="index")
    else:
        top16_df = top16_df.style.hide(axis="index")
    with st.expander("Top 16"):
        st.markdown(top16_df.to_html(), unsafe_allow_html=True)
except:
    pass


with st.expander("Standing"):
    control_sheet_standing = control_sheet.copy().reset_index()
    if search_player:
        control_sheet_standing = control_sheet_standing[control_sheet_standing.Player.str.lower().str.contains(search_player.lower())]
    # control_sheet_standing.drop(["dropped", "n_3P_pods"], axis = 1, inplace=True)
    # control_sheet_standing = control_sheet_standing[["Rank", "Player", "Points", "Regular points", "win", "loss", "draw"]]
    control_sheet_standing = control_sheet_standing[["Rank", "Player", "Points", "win", "loss", "draw", "bye"]]
    control_sheet_standing[["win", "loss", "draw", "bye"]] = control_sheet_standing[["win", "loss", "draw", "bye"]].astype(int)
    # control_sheet_standing["Points"] = control_sheet_standing["Points"].astype(int)
    st.markdown(control_sheet_standing.style.format(f).hide(axis="index").to_html(), unsafe_allow_html=True)



replace_round_strings = {
    6: "Top 16",
    7: "Top 4",
}

round_strings = [x+1 for x in reversed(range(current_round))]

new_round_strings = []
for ele in round_strings:
    if ele in replace_round_strings.keys():
        print("sjdbfgsohdgbsludfebsoihfb", ele)
        new_round_strings.append(replace_round_strings[ele])
    else:
        new_round_strings.append(ele)

round_strings = new_round_strings

display_round = st.radio("Round selection", round_strings, horizontal = True)




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