import pandas as pd
import itertools
import numpy as np
from collections import Counter
from random import shuffle
from tqdm import tqdm
from itertools import permutations

def init():
    control_sheet_general = pd.read_excel("control_sheet.ods", engine="odf", sheet_name="general").set_index("Player")
    n_active_players = len(control_sheet_general[control_sheet_general.dropped == 0])
    print(f"Active players {n_active_players}")

    print("Pod config (4P/Byes):")
    # print(f"{n_active_players//4} / {n_active_players-n_active_players//4 * 4}")
    print((n_active_players//4, n_active_players-n_active_players//4 * 4))
    pod_config = (n_active_players//4, n_active_players-n_active_players//4 * 4)
        


    # played rounds
    finished_rounds = get_finished_round()
    
    print("Finished rounds")
    print(f"--- {finished_rounds}")

    return pod_config

def get_finished_round():
    finished_rounds = 0
    for i in range(1,99):
        try:
            pd.read_excel("control_sheet.ods", engine="odf", sheet_name=f"round {i}")
            finished_rounds += 1
        except:
            return finished_rounds


def get_control_sheet():
    control_sheet_general = pd.read_excel("control_sheet.ods", engine="odf", sheet_name="general").set_index("Player")    
    return control_sheet_general

def get_oppo_dict(control_sheet_general):
    oppo_dict = {}
    finished_rounds = get_finished_round()
    for player in control_sheet_general.index.unique():
        oppo_dict[player] = []
    if finished_rounds > 0:
        for i in range(1,finished_rounds+1):
            round_df = pd.read_excel("control_sheet.ods", engine="odf", sheet_name=f"round {i}")

            for pod in round_df.Pod.unique():
                if pod == "BYE": continue
                pod_players = round_df[round_df.Pod == pod].Player.values
                for tuple in list(itertools.combinations(pod_players, r = 2)):
                    oppo_dict[tuple[0]].append(tuple[1])
                    oppo_dict[tuple[1]].append(tuple[0])
    return oppo_dict


def get_match_logs(control_sheet):
    match_logs = []
    finished_rounds = get_finished_round()
    if finished_rounds > 0:
        
        for i in range(1,finished_rounds+1):
            round_df = pd.read_excel("control_sheet.ods", engine="odf", sheet_name=f"round {i}")
            if "Result" not in round_df.columns: continue
            for pod_number in range(1, round_df[round_df.Pod != "BYE"].Pod.max()+1):
                match_log_element = {}
                pod_df = round_df[round_df.Pod == pod_number]
                match_players = []
                pod_winner = None
                for index, row in pod_df.iterrows():
                    state = row.Result
                    if state == "draw":
                        pod_winner = "draw"
                    elif state == "win":
                        pod_winner = row.Player
                    match_players.append(row.Player)
                match_log_element["match_players"] = match_players
                match_log_element["match_result"] = pod_winner
                match_log_element["round"] = i
                match_log_element["pod"] = pod_number
                match_logs.append(match_log_element)

            # each bye player is a separate "match"
            for index, row in round_df[round_df.Pod == "BYE"].iterrows(): 
                match_log_element = {}
                match_log_element["match_players"] = [row.Player]
                match_log_element["match_result"] = "bye"
                match_log_element["round"] = i
                match_log_element["pod"] = "bye"
                match_logs.append(match_log_element)

    return match_logs


#################################################################################################################################

def add_wld(control_sheet, match_logs):
    control_sheet["win"] = 0
    control_sheet["loss"] = 0
    control_sheet["draw"] = 0
    control_sheet["bye"] = 0

    if not match_logs:
        return control_sheet
    
    for match in match_logs:
        match_players = match["match_players"]
        match_result = match["match_result"]

        for player in match_players:
            if player == match_result:
                control_sheet.loc[player, "win"] += 1
            elif match_result == "draw":
                control_sheet.loc[player, "draw"] += 1
            elif match_result == "bye":
                control_sheet.loc[player, "bye"] += 1
            else:
                control_sheet.loc[player, "loss"] += 1

    return control_sheet



def add_standing(control_sheet, match_logs, method):
    """
    methods: hareruya, 
    """
    control_sheet = method(control_sheet, match_logs)
    return control_sheet

def get_standings_after_rounds(control_sheet, match_logs, method):
    if not match_logs:
        return None
    
    # get number of finished round from match logs
    max_round_number = 0
    for ele in match_logs:
        if ele["round"] > max_round_number: max_round_number = ele["round"]

    sheets = {}
    
    for round in range(1, max_round_number+1):
        print("round", round)
        match_logs_subset = []
        for ele in match_logs:
            if ele["round"] <= round: match_logs_subset.append(ele)
        control_sheet_temp = add_wld(control_sheet.copy(), match_logs_subset)
        control_sheet_temp = add_standing(control_sheet_temp, match_logs_subset, method=method)
        control_sheet_temp = control_sheet_temp[["Points"]]
        sheets[round] = control_sheet_temp

    # fill in round 0
    if sheets:
        sheets[0] = sheets[1].copy()
        sheets[0]["Points"] = 1000.
    
    
    return sheets

#################################

def hareruya_permutations_with_draw_and_byes(control_sheet, match_logs):
    control_sheet["Random"] = np.random.random(len(control_sheet))
    if not match_logs:
        control_sheet["Points"] = 1000
        
        control_sheet["Rank"] = (
            control_sheet[["Points", "Random"]]
            .apply(tuple,axis=1)
            .rank(method='dense',ascending=False)
            .astype(int)
            )
        control_sheet = control_sheet.sort_values("Rank")
        return control_sheet
    
    # get number of finished round from match logs
    max_round_number = 0
    for ele in match_logs:
        if ele["round"] > max_round_number: max_round_number = ele["round"]
    
    sheets = []

    round_permutations = list(permutations(np.arange(1, max_round_number+1)))
    for perm in tqdm(round_permutations):
        # print(perm)
        control_sheet_perm = control_sheet.copy()
        control_sheet_perm["Points"] = 1000
        match_log_perm = []
        for round in perm:
            for ele in match_logs:
                if ele["round"] == round: match_log_perm.append(ele)

        bye_players = []
        
        for match in match_log_perm:
            match_players = match["match_players"]
            match_result = match["match_result"]

            points_for_winner = 0

            for player in match_players:
                if player == match_result:
                    pass
                elif match_result == "bye":
                    bye_players.append(player)
                    pass
                else: # draw or loss
                    points_for_winner += control_sheet_perm.loc[player, "Points"]*0.07
                    control_sheet_perm.loc[player, "Points"] *= 0.93
            
            if match_result == "bye":
                continue
            elif match_result == "draw":
                for player in match_players:
                    control_sheet_perm.loc[player, "Points"] += points_for_winner/len(match_players)
            elif match_result == "loss":
                pass
            else:
                control_sheet_perm.loc[match_result, "Points"] += points_for_winner
        
        # account for byes , this accounts for byes on each single permutation. Probably also fine, but rules document says to do it other way
        # for player in bye_players:
        #     avg_point_move = (control_sheet_perm.loc[player, "Points"] - 1000) / (len(perm) - 1) # -1 because one of the rounds was the bye
        #     avg_point_move = np.max([0, avg_point_move])
        #     control_sheet_perm.loc[player, "Points"] += avg_point_move

        #     control_sheet_perm.loc[player, "avg_point_move"] = avg_point_move

        
        control_sheet_perm["Regular points"] = control_sheet_perm["win"]*5 + control_sheet_perm["draw"]
        sheets.append(control_sheet_perm)

    # combine
    control_sheet = pd.concat(sheets)
    control_sheet = control_sheet.groupby(control_sheet.index).mean()

    # account for byes
    control_sheet["points_before_bye"] = control_sheet["Points"].copy()
    control_sheet["avg_point_move"] = (control_sheet["points_before_bye"] - 1000) / (max_round_number - control_sheet["bye"]) # -1 because one of the rounds was the bye
    control_sheet["avg_point_move"] = control_sheet["avg_point_move"].clip(lower=0)
    control_sheet["Points"] = control_sheet["points_before_bye"] + control_sheet["avg_point_move"]*control_sheet["bye"]


    control_sheet["Rank"] = (
        control_sheet[["Points", "Random"]]
        .apply(tuple,axis=1)
        .rank(method='dense',ascending=False)
        .astype(int)
        )
    
    control_sheet = control_sheet.sort_values("Rank")
    return control_sheet#, sheets

def get_weighted_opp_win_percentage(control_sheet, oppo_dict):

    control_sheet["n_games"] = control_sheet["win"] + control_sheet["loss"] + control_sheet["draw"]
    control_sheet["WR"] = control_sheet["win"] / control_sheet["n_games"]

    control_sheet["weighted_oppo_WR"] = 0.0

    for player, oppo_list in oppo_dict.items():
        oppo_wins = 0
        oppo_games = 0
        for oppo in oppo_list:
            oppo_wins += control_sheet.loc[oppo, "win"]
            oppo_games += control_sheet.loc[oppo, "n_games"]

        if oppo_games > 0:
            control_sheet.loc[player, "weighted_oppo_WR"] = oppo_wins/oppo_games

    return control_sheet

def get_weighted_opp_win_percentage_with_draws(control_sheet, oppo_dict):

    control_sheet["n_games"] = control_sheet["win"] + control_sheet["loss"] + control_sheet["draw"]
    control_sheet["WR"] = control_sheet["win"] / control_sheet["n_games"]

    control_sheet["weighted_oppo_WR_with_draws"] = 0.0

    for player, oppo_list in oppo_dict.items():
        oppo_wins = 0
        oppo_games = 0
        for oppo in oppo_list:
            oppo_wins += control_sheet.loc[oppo, "win"] * 7
            oppo_wins += control_sheet.loc[oppo, "draw"]
            oppo_games += control_sheet.loc[oppo, "n_games"] * 7

        if oppo_games > 0:
            control_sheet.loc[player, "weighted_oppo_WR_with_draws"] = oppo_wins/oppo_games

    return control_sheet


##########################################################################################################
def get_random_pairings(control_sheet, pod_config):
    control_sheet_general_copy = control_sheet[control_sheet.dropped == 0]
    control_sheet_general_copy["rndm"] = np.random.random(len(control_sheet_general_copy))
    control_sheet_general_copy["seed"] = control_sheet_general_copy["rndm"] + 0.5*control_sheet_general_copy["n_3P_pods"]
    control_sheet_general_copy = control_sheet_general_copy.sort_values(["seed"], ascending=False)
    player_order = control_sheet_general_copy.index.values
    pods_4P = [player_order[x:x+4] for x in range(0, pod_config[0]*4, 4)]
    pods_3P = [player_order[x:x+3] for x in range(pod_config[0]*4, pod_config[0]*4+pod_config[1]*3, 3)]
    return pods_4P, pods_3P

def get_heuristic_pairing(control_sheet, pod_config, oppo_dict):
    """
    minimizes byes per player
    avoids rematches if possible
    """
    control_sheet_general_copy = control_sheet[control_sheet.dropped == 0]
    control_sheet_general_copy["rndm"] = np.random.random(len(control_sheet_general_copy))
    control_sheet_general_copy = control_sheet_general_copy.sort_values(["bye", "Points", "rndm"], ascending=False)
    player_order = control_sheet_general_copy.index.values
    players_4 = player_order[:pod_config[0]*4]
    players_byes = player_order[-pod_config[1]:]
    # place players_4
    matches_4 = [[] for _ in range(pod_config[0])]
    for player in players_4:
        pod_scores = [evaluate_pod(player, pod, oppo_dict, max_pod_size = 4) for pod in matches_4]
        index = pod_scores.index(max(pod_scores))
        matches_4[index].append(player)
        
    return matches_4, list(players_byes)

def evaluate_pod(player, pod, opponent_dict, max_pod_size = 4):
    if len(pod) == max_pod_size:
        return -np.inf
    already_player_counter = 0
    for other_player in pod:
        if other_player in opponent_dict[player]: already_player_counter += dict(Counter(opponent_dict[player]).items())[other_player]
    return -(already_player_counter**2)
    


def get_pairing_scores(
        oppo_dict,
        pods_4P,
        ):
    """
    this is the subjective part of what matters when pairing
    """
    
    # number of rematches
    rematch_counter = 0
    for pod in pods_4P:
        for tuple in list(itertools.combinations(pod, r = 2)):
            if tuple[0] in oppo_dict[tuple[1]]: rematch_counter += dict(Counter(oppo_dict[tuple[1]]).items())[tuple[0]]**2
    
    score = rematch_counter
    return score, rematch_counter

