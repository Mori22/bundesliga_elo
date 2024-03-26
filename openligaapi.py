# %% imports

from re import S
import httpx
import pandas as pd
from io import StringIO


# %% define class


class OpenLigaDB:

    def __init__(self, ligaID: str = "bl1") -> None:
        self.openLigaDBApiUrl = "https://api.openligadb.de"
        self.ligaID: str = ligaID

    def get_matchday_result_data(self, season: int, matchday: int) -> str:
        request_url: str = (
            self.openLigaDBApiUrl
            + "/getmatchdata/"
            + self.ligaID
            + f"/{season}/{matchday}"
        )
        response: httpx.Response = httpx.get(request_url)

        data: str = response.text

        return data

    def get_matchday_result_dataframe(self, season: int, matchday: int) -> pd.DataFrame:
        matchday_data: str = self.get_matchday_result_data(
            season=season, matchday=matchday
        )
        matchday_df: pd.DataFrame = pd.read_json(StringIO(matchday_data))
        return matchday_df

    def get_season_result_data(self, season: int) -> str:
        request_url: str = (
            self.openLigaDBApiUrl + "/getmatchdata/" + self.ligaID + f"/{season}"
        )
        response: httpx.Response = httpx.get(request_url)

        data: str = response.text

        return data

    def get_season_result_dataframe(self, season: int) -> pd.DataFrame:
        season_data: str = self.get_season_result_data(season=season)
        season_df: pd.DataFrame = pd.read_json(StringIO(season_data))
        return season_df

    def get_season_teams_data(self, season: int) -> str:
        request_url: str = (
            self.openLigaDBApiUrl + "/getavailableteams/" + self.ligaID + f"/{season}"
        )
        response: httpx.Response = httpx.get(request_url)

        data: str = response.text

        return data

    def get_season_teams_dataframe(self, season: int) -> pd.DataFrame:
        season_teams_data: str = self.get_season_teams_data(season=season)
        season_teams_df: pd.DataFrame = pd.read_json(StringIO(season_teams_data))
        return season_teams_df

    def get_teams_dataframe(self, start_season: int, end_season: int) -> pd.DataFrame:
        teams_df: pd.DataFrame = self.get_season_teams_dataframe(season=start_season)
        for season in range(start_season + 1, end_season + 1):
            temp_df: pd.DataFrame = self.get_season_teams_dataframe(season=season)
            teams_df = pd.concat([teams_df, temp_df]).drop_duplicates()
        return teams_df

    def get_result_dataframe(self, start_season: int, end_season: int) -> pd.DataFrame:
        result_df: pd.DataFrame = self.get_season_result_dataframe(season=start_season)
        for season in range(start_season + 1, end_season + 1):
            temp_df: pd.DataFrame = self.get_season_result_dataframe(season=season)
            result_df: pd.DataFrame = pd.concat([result_df, temp_df])
        return result_df


# %% testarea

if __name__ == "__main__":
    openligadb = OpenLigaDB(ligaID="bl1")
    # openligadb.get_matchday_result_data(season=2022, matchday=1)
    # print(openligadb.get_matchday_result_dataframe(season=2022, matchday=1))

    # matchday_result = openligadb.get_matchday_result_dataframe(season=2022, matchday=1)

    # season_result = openligadb.get_season_result_dataframe(season=2022)

    # team_data = openligadb.get_season_teams_dataframe(season=2002)
    # print(team_data)
    test_teams = openligadb.get_teams_dataframe(start_season=2002, end_season=2022)
    print(test_teams)
