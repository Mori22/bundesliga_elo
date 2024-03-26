from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List

import pandas as pd
import matplotlib.pyplot as plt

from openligaapi import OpenLigaDB


@dataclass
class BuLiTeam:
    id: int
    name: str
    short_name: str
    elo: int = field(default=1000)
    highest_elo: int = field(default=1000)
    elo_history: Dict[datetime, int] = field(default_factory=dict)

    def update_elo(self, new_elo: int, matchdate: datetime) -> None:
        if new_elo > self.highest_elo:
            self.highest_elo = new_elo
        self.elo = new_elo
        self.elo_history[matchdate] = new_elo


# %% define elo calculation class


@dataclass
class BuLiElo:
    match_data: pd.DataFrame = None
    teams: Dict[int, BuLiTeam] = field(default_factory=dict)
    openligadb: OpenLigaDB = OpenLigaDB(ligaID="bl1")
    start_season: int = field(default=2002)
    end_season: int = field(default=2022)

    def __post_init__(self) -> None:
        self.match_data = self.openligadb.get_result_dataframe(
            start_season=self.start_season, end_season=self.end_season
        )

    def create_team(self, team_id, team_name, team_short_name) -> None:
        temp_team = BuLiTeam(id=team_id, name=team_name, short_name=team_short_name)
        self.teams[team_id] = temp_team

    def create_all_teams(self):
        teams_dataframes: pd.DataFrame = self.openligadb.get_teams_dataframe(
            start_season=self.start_season, end_season=self.end_season
        )
        for team_tuple in teams_dataframes.itertuples():
            self.create_team(
                team_id=team_tuple.teamId,
                team_name=team_tuple.teamName,
                team_short_name=team_tuple.shortName,
            )

    def update_elo(
        self,
        team_1: BuLiTeam,
        team_2: BuLiTeam,
        result_team_1: float,
        result_team_2: float,
        matchdate: datetime,
    ):
        current_elo_rating_team_1: int = team_1.elo
        current_elo_rating_team_2: int = team_2.elo
        new_elo_rating_team_1: int = self.calculate_elo_update(
            team_rating=current_elo_rating_team_1,
            opponent_rating=current_elo_rating_team_2,
            result=result_team_1,
        )
        new_elo_rating_team_2: int = self.calculate_elo_update(
            team_rating=current_elo_rating_team_2,
            opponent_rating=current_elo_rating_team_1,
            result=result_team_2,
        )
        team_1.update_elo(new_elo=new_elo_rating_team_1, matchdate=matchdate)
        team_2.update_elo(new_elo=new_elo_rating_team_2, matchdate=matchdate)

    def calculate_elo_update(
        self, team_rating: int, opponent_rating: int, result: float, k_factor: int = 32
    ) -> int:
        """
        Calculates the updated Elo rating for a team after a match.

        Args:
            team_rating (int): Current Elo rating of the team.
            opponent_rating (int): Elo rating of the opponent.
            result (float): Result of the match (1 for win, 0.5 for draw, 0 for loss).
            k_factor (int, optional): K-factor for Elo rating system. Defaults to 32.

        Returns:
            int: Updated Elo rating for the player.
        """
        expected_score: float = 1 / (1 + 10 ** ((opponent_rating - team_rating) / 400))
        actual_score: float = result
        rating_change: float = k_factor * (actual_score - expected_score)
        new_rating: float = team_rating + rating_change
        return int(new_rating)

    def get_result_objects(self, match_result):
        goals_team_1 = match_result["pointsTeam1"]
        goals_team_2 = match_result["pointsTeam2"]
        if goals_team_1 > goals_team_2:
            result_team_1 = 1
            result_team_2 = 0
        elif goals_team_1 == goals_team_2:
            result_team_1 = 0.5
            result_team_2 = 0.5
        else:
            result_team_1 = 0
            result_team_2 = 1
        return result_team_1, result_team_2

    def evaluate_match(self, match_data):
        team_id_1 = match_data.team1["teamId"]
        team_id_2 = match_data.team2["teamId"]
        match_result = match_data.matchResults[0]
        team_1: BuLiTeam = self.teams[team_id_1]
        team_2: BuLiTeam = self.teams[team_id_2]
        result_team_1, result_team_2 = self.get_result_objects(
            match_result=match_result
        )
        matchdate: datetime = datetime.strptime(
            match_data.matchDateTime, "%Y-%m-%dT%H:%M:%S"
        )
        self.update_elo(
            team_1=team_1,
            team_2=team_2,
            result_team_1=result_team_1,
            result_team_2=result_team_2,
            matchdate=matchdate,
        )

    def evaluate_all_matches(self):
        for match in self.match_data.itertuples():
            self.evaluate_match(match_data=match)

    def get_elo_table(self) -> pd.DataFrame:
        team_names = []
        team_current_elo = []
        team_highest_elo = []

        for team in self.teams.values():
            team_names.append(team.name)
            team_current_elo.append(team.elo)
            team_highest_elo.append(team.highest_elo)

        team_elo_df = pd.DataFrame(
            data={
                "Verein": team_names,
                "Aktuelles ELO": team_current_elo,
                "Maximales ELO": team_highest_elo,
            }
        )
        return team_elo_df

    def plot_elo_history(self, team_id: int) -> None:
        """
        Plots the Elo history for a specific team.

        Args:
            team_id (int): ID of the team.

        Returns:
            None
        """
        if team_id not in self.teams:
            print(f"Team with ID {team_id} not found.")
            return

        team = self.teams[team_id]
        match_dates = list(team.elo_history.keys())
        elo_ratings = list(team.elo_history.values())

        plt.figure(figsize=(10, 6))
        plt.plot(match_dates, elo_ratings, marker="o", linestyle="-", color="b")
        plt.title(f"Elo History for {team.name}")
        plt.xlabel("Match Date")
        plt.ylabel("Elo Rating")
        plt.grid(True)
        plt.show()

    def plot_all_teams_elo_history(self) -> None:
        """
        Plots the Elo history for all teams in the same graph.

        Returns:
            None
        """
        plt.figure(figsize=(12, 8))
        line_styles = ["-", "--", "-.", ":"]
        color_cycle = plt.cm.tab20.colors  # Use distinct colors from the tab20 colormap
        for i, (team_id, team) in enumerate(self.teams.items()):
            match_dates = list(team.elo_history.keys())
            elo_ratings = list(team.elo_history.values())
            plt.plot(
                match_dates,
                elo_ratings,
                label=team.name,
                linestyle=line_styles[i % len(line_styles)],
                color=color_cycle[i % len(color_cycle)],
            )

        plt.title("Elo History for Bundesliga Teams")
        plt.xlabel("Match Date")
        plt.ylabel("Elo Rating")
        plt.grid(True)
        plt.legend(
            loc="center left", bbox_to_anchor=(1, 0.5)
        )  # Legend outside the plot
        plt.show()

    def plot_selected_teams_elo_history(self, team_ids: List[int]) -> None:
        """
        Plots the Elo history for specific teams based on provided team IDs.

        Args:
            team_ids (List[int]): List of team IDs to plot.

        Returns:
            None
        """
        plt.figure(figsize=(12, 8))
        line_styles = ["-", "--", "-.", ":"]
        color_cycle = plt.cm.tab20.colors

        for i, team_id in enumerate(team_ids):
            if team_id not in self.teams:
                print(f"Team with ID {team_id} not found.")
                continue

            team = self.teams[team_id]
            match_dates = list(team.elo_history.keys())
            elo_ratings = list(team.elo_history.values())
            plt.plot(
                match_dates,
                elo_ratings,
                label=team.name,
                linestyle=line_styles[i % len(line_styles)],
                color=color_cycle[i % len(color_cycle)],
            )

        plt.title("Elo History for Selected Bundesliga Teams")
        plt.xlabel("Match Date")
        plt.ylabel("Elo Rating")
        plt.grid(True)
        plt.legend(
            loc="center left", bbox_to_anchor=(1, 0.5)
        )  # Legend outside the plot
        plt.tight_layout()
        plt.show()


# %% test area
if __name__ == "__main__":
    # test_team = BuLiTeam(id=1, name="Eintracht Frankfurt", short_name="SGE")
    # print(test_team)
    # test_team.update_elo(999)
    # print(test_team)
    test_elo = BuLiElo(start_season=2004)
    # test_elo.create_team(
    #     team_id=1, team_name="Eintracht Frankfurt", team_short_name="SGE"
    # )
    # test_elo.create_team(
    #     team_id=2, team_name="Borussia Dortmund", team_short_name="BVB"
    # )
    # print(test_elo)
    test_elo.create_all_teams()

    # print(test_elo.match_data)

    # print(
    #     test_elo.calculate_elo_update(team_rating=1000, opponent_rating=1000, result=1)
    # )
    # test_data = test_elo.match_data.head(3)

    # for match in test_data.itertuples():
    #     team_id_1 = match.team1["teamId"]
    #     team_id_2 = match.team2["teamId"]
    #     match_result = match.matchResults[0]

    # result_team_1, result_team_2 = test_elo.get_result_objects(
    #     match_result=match_result
    # )

    # test_elo.evaluate_match(match)

    test_elo.evaluate_all_matches()

    test_elo.plot_all_teams_elo_history()

    test_elo.plot_selected_teams_elo_history(team_ids=[6, 7, 91, 40, 9, 100, 129])


# %%
