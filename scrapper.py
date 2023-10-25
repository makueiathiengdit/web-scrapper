"""
    Name        : Web Scrapper
    Author      : Awet Thon
    Date        : 29-05-2023
    Description : Module for scrapping basketball game data from website. 
"""


from bs4 import BeautifulSoup
import requests

import csv
import shutil  # for saving image data
from time import sleep
import os


class RosterScrapper:
    def __init__(self, url=None):
        self.url = url
        self.roster = []
        self.headers = {
            "Accept": "text/html, */*; q=0.01",
            "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "X-Requested-With": "XMLHttpRequest"
        }

    def get_roster(self, url=None):
        if url is None:
            raise ValueError("URL must be provided")

        res = requests.get(url, headers=self.headers)
        soup = None

        if res.status_code == 200:
            soup = BeautifulSoup(res.content, 'html.parser')
            roster_container = soup.find_all(
                'div', {'class': 'country_roster_team'})

            members = []
            if len(roster_container) > 1:
                members = roster_container[1].find_all(
                    'div', {'class': 'roster_member_container'})
            else:
                members = roster_container[0].find_all(
                    'div', {'class': 'roster_member_container'})

            for member in members:
                player_img = ""
                jersey_no = ""
                first_name = "",
                last_name = ""
                position = ""
                height = ""
                team = ""
                dob = ""
                competition = "FIBA World Cup 2023"

                player_img = member.find('img')['src']

                jersey_no = member.find("div", {'class': 'num'}).text.strip()
                first_name = member.find(
                    'div', {'class': 'firstname'}).text.strip()
                last_name = member.find(
                    'div', {'class': 'lastname'}).text.strip()
                position = member.find(
                    'div', {'class': 'position'}).text.strip()
                height = member.find('div', {'class': 'height'}).text.strip()
                team = member.find('div', {'class': 'team'}).text.strip()
                dob = member.find('div', {'class': 'birth'}).text.strip()

                player = {
                    'jersey_number': jersey_no,
                    'first_name': first_name,
                    'last_name': last_name,
                    'position': position,
                    'height': height,
                    'team': team,
                    'dob': dob,
                    'competition': competition,
                    'player_img': player_img,
                }

                self.roster.append(player)

     # recieves a dict or list of dicts

    def to_csv(self, data=None, filename=None, header=True):
        if filename is None:
            raise ValueError("Filename must be provided.")
        if data is None:
            raise ValueError("Data to be saved must be provided.")

        headers = []
        if header:
            if isinstance(data, list):
                headers = data[0].keys()
            elif isinstance(data, dict):
                headers = data.keys()
            else:
                raise TypeError('data must be a dict or list of dicts')

        print(f'saving data to {filename}.......', end='')
        with open(filename, 'a') as fh:
            writer = csv.DictWriter(fh, fieldnames=headers)
            if header:
                writer.writeheader()

            if isinstance(data, list):
                writer.writerows(data)
            else:
                writer.writerow(data)
        fh.close()
        print('done')


class WebScrapper:
    first = True

    def __init__(self):
        self.name = 'South Sudan Basketball Web Scraper'
        self.soup = None
        self.html = None
        self.game = {}
        self.final_score = None
        self.game_url = None
        self.ajax_urls = {}
        self.comparison_data = None
        self.default_value = "Unknown"
        self.headers = {
            "Accept": "text/html, */*; q=0.01",
            "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "X-Requested-With": "XMLHttpRequest"
        }
        self.allowed_tabs = ['preview', 'play_by_play', 'boxscore',
                             'videos', 'shot_chart', 'team_comparison']

        self.data = None
        self.cookies = None
        print('*'*25)
        print("Scrapper initialized")
        print("*"*25)

    def __str__(self):
        return f"{self.name}"

    def init(self, url=None):
        if not url:
            raise ValueError("url must be provided")
        self.game_url = url
        print('fetching data...', end='')
        result = requests.get(url, self.headers)
        self.soup = None
        print('done')

        print('making soup...', end='')
        self.soup = BeautifulSoup(result.content, 'html.parser')
        print('done')

        # extra data urls
        for tab in self.allowed_tabs:
            try:
                url = self.get_ajax_url(target_tab=tab)
                self.ajax_urls[tab] = url
            except Exception:
                print(f"Error finding ajax link for tab:  {tab}")

    # get comparison stats like fast break points, bench points, points from turnovers etc
    def get_team_comparison_stats(self, soup, team):

        if soup is None:
            raise ValueError("Soup must be provided")
        if team is None:
            raise ValueError("Team must be specified")

        team = team.upper()

        stats = {'points_from_turnover': "Unknown",
                 'second_chance_points': "Unknown",
                 'fast_break_points': "Unknown",
                 'points_in_the_paint': "Unknown",
                 'points_from_the_bench': "Unknown"
                 }
        try:
            divs = soup.find('li', {'class': 'comparison'}).find_all('div')
            if divs:
                for div in divs:
                    label = div.find(
                        'span', {'class': 'compare-label'}).text.strip()
                    val = div.find(
                        'span', {'class': 'team-' + team}).text.strip()
                    label = label.split(' ')
                    label = "_".join(label).lower()
                    stats[label] = val
        except Exception as e:
            print("error finding comparison stats")
            print(e)

        return stats

    # get lead stats like biggest scoring run, time leading, biggest lead etc.
    def get_team_lead_stats(self, soup=None, team=None):
        if soup is None:
            raise ValueError("Soup cannot be none")
        if team == "" or team is None:
            raise ValueError("Team must be specified")

        team = team.upper()
        lead_stats = {
            'biggest_lead': "Unknown",
            'biggest_scoring_run': "Unknown",
            'times_leading': "Unknown"
        }

        try:
            lead_stats_list = soup.find(
                'ul', {'class': 'lead-stats-list'}).find_all('li')
            skip_labels = ['Lead changes', 'Times tied']

            if lead_stats_list:
                for lead_stat in lead_stats_list:
                    label = lead_stat.find(
                        'span', {'class': 'lead-label'}).text.strip()

                    if label in skip_labels:
                        continue

                    label = label.split(' ')
                    label = "_".join(label).lower()
                    val = lead_stat.find(
                        'span', {'class': 'team-' + team}).text.strip()
                    lead_stats[label] = val
        except Exception as e:
            print("error finding lead stats")
            print(e)
        return lead_stats

    def get_game_in_brief(self, soup=None):

        # preview tab contains information about game date, time, arena etc
        preview_tab_tab = self.ajax_request(url=self.ajax_urls['preview'])

        sleep(1)
        # contains team comparison stats like like points in the paint, fast break points, lead stats etc
        compare_tab = self.ajax_request(url=self.ajax_urls['team_comparison'])

        preview_soup = BeautifulSoup(preview_tab_tab, 'html.parser')
        compare_soup = BeautifulSoup(compare_tab, 'html.parser')

        self.comparison_data = compare_soup

        teams = ['A', 'B']
        games = []
        for team in teams:
            game = {}

            final_score = self.get_team_final_score(team=team, soup=self.soup)

            team_name = self.get_team_name(team=team)
            opp_name = ''
            if team == 'A':
                opp_name = self.get_team_name(team='B')
                opp_score = self.get_team_final_score(team='B', soup=self.soup)
            else:
                opp_name = self.get_team_name(team='A')
                opp_score = self.get_team_final_score(team='A', soup=self.soup)

            top_performer = self.get_top_performer(team=team)

            result = 'W' if final_score > opp_score else 'L'
            # get images of top perfromers
            img = self.soup.find(
                'div', {'class': 'performer-content'}).find('div', {'class': 'team-' + team}).find('img')

            """
                    # save image as top performer name .png

                    # top_performer_img_name = top_performer.replace(
                    #     ' ', '_').lower() + '.png'

                    # try:
                    #     print("downloading top performers images....", end="")
                    #     self.download_img(imgs['src'], top_performer_img_name)

                    # except Exception as e:
                    #     print("Error downloading images")
            """

            lead_stats = self.get_team_comparison_stats(
                compare_soup, team)
            compare_stats = self.get_team_lead_stats(compare_soup, team)

            #  add game meta data
            game['date'] = self.get_game_date(preview_soup)
            game['time'] = self.get_game_time(preview_soup)
            game['arena'] = self.get_game_arena(preview_soup)
            game['city_or_country'] = self.get_host_country(preview_soup)

            game['phase'] = self.get_game_phase()
            game['group'] = self.get_game_group()
            game['tournament'] = self.get_tournament()
            game['team'] = team_name
            game['opponent'] = opp_name
            game['final_score'] = final_score
            game['result'] = result
            game['top_performer'] = top_performer
            game['top_performer_img'] = img['src']

            quarterly_scores = self.get_quarterly_scores(team=team)

            for quarter, score in quarterly_scores:
                game[quarter] = score

            # add comparison and lead stats
            for key, val in lead_stats.items():
                game[key] = val
            for key, val in compare_stats.items():
                game[key] = val

            games.append(game)
        return games

    def download_img(self, url, img_name):
        try:
            print('\nfetching image......', end='')
            res = requests.get(url, stream=True)
            if res.status_code == 200:
                print('done')
                print(f'saving image {img_name}', end='')
                with open(img_name, 'wb') as f:
                    shutil.copyfileobj(res.raw, f)
                print('......done')
            else:
                print(f'error downloading image {img_name}')
                print("Error code: ", res.status_code)

        except Exception as e:
            print('error downloading image')
            print(e)

    def get_team_final_score(self, soup=None, team=None):

        if team is None:
            raise ValueError("Team must be specified")
        if soup is None:
            soup = self.soup

        final_score = "Unknown"
        team = team.upper()
        try:
            final_score = soup.find('div', {
                                    'class': 'final-score'}).find('span', {'class': 'score-' + team}).text.strip()
        except Exception as e:
            print(f"error finding final score for team {team}")
            print(e)
        return final_score

    def get_quarterly_scores(self, soup=None, team=None):
        if team is None:
            raise ValueError("Team must be specified")

        if soup is None:
            soup = self.soup

        scores = {
            'Q1': None,
            'Q2': None,
            'Q3': None,
            'Q4': None,
        }
        try:
            scores_lis = soup.find(
                'ul', {'class': 'period-list'}).find_all("li", {'class': 'period-item'})
            for li in scores_lis:
                quarter = li.find(
                    'span', {'class': 'period-name'}).text.strip()
                score = li.find(
                    'span', {'class': 'score-' + team}).text.strip()
                scores[quarter] = score

        except Exception as e:
            print("error finding quarterly scores")
            print(e)

        return scores

    def get_top_performer(self, soup=None, team=None):
        if soup is None:
            soup = self.soup
        if team is None:
            raise ValueError("Expected a team name but got none")
        top_performer = "Unknown"
        team = team.upper()

        try:
            top_performer = soup.find(
                'div', {'class': 'athlete-' + team})\
                .find('span', {'class': 'name'}).text.strip()
        except:
            print("Can't find top performer")
        return top_performer

    def get_game_date(self, soup):
        date = "Unknown"
        try:
            date = soup.find('div', {'class': 'date_infos'}).find(
                'div', {'class': 'date'}).text.strip()
        except Exception as e:
            print("Error, can't find game date")
            print(e)

        return date

    def get_game_time(self, soup):
        time = "Unknown"
        try:
            time = soup.find('div', {'class': 'date_infos'}).find(
                'div', {'class': 'time'}).text.strip()
            timezone = soup.find('span', {'class': 'timezone'}).text.strip()
            time = time + ' ' + timezone
        except Exception as e:
            print("error finding game time")
            print(e)

        return time

    def get_host_country(self, soup):
        country = "Unknown"

        try:
            country = soup.find('div', {'class': 'date_infos'}).find(
                'span', {'class': 'country_name'}).text.strip()
        except Exception as e:
            print("error can't find host country")
            print(e)

        return country

    def get_game_arena(self, soup):
        arena = "Unknown"
        try:
            arena = soup.find('div', {'class': 'location'}).text.strip()
        except Exception as e:
            print("error. can't find game arena")
            print(e)

        return arena

    def get_game_group(self, soup=None):
        group = "Unknown"
        if soup is None:
            soup = self.soup
        try:
            group = soup.find('span', {'class': 'group'}).text.strip()
        except Exception as e:
            print("error, can't find game group")
            print(e)

        return group

    def get_tournament(self, url=None):
        name = "FIBA-"
        if url is None:
            url = self.game_url
        try:
            parts = url.split("/")[3:6]
            name += "-".join(parts)
        except:
            print("unable to get tournament name")
        return name.lower()

    def get_game_phase(self, soup=None):
        phase = "Unknown"
        if soup is None:
            soup = self.soup
        try:
            phase = soup.find('span', {'class': 'phase'}).text.strip()
        except:
            print("error, can't find game phase")

        return phase

    def get_team_name(self, soup=None, tag='div', team=None):
        name = "Unknown"
        if team is None:
            raise ValueError("Please specify team (A or B)")

        team = team.upper()
        try:
            if soup is None:
                soup = self.soup
            name = soup.find(tag, {'class': 'team-' + team}).find(
                'span', {'class': 'team-name'}).text.strip()
        except Exception as e:
            print("error, can't find team name")
            print(e)

        return name

    def get_game_play_by_play(self, soup=None, team=None):
        if team is None:
            raise ValueError("team must be specified")

        if soup is None:
            soup = self.soup

        opponent = ""
        if team == 'A':
            opponent = self.get_team_name(team="B")
        else:
            opponent = self.get_team_name(team="A")
        plays = []

        try:
            # find all plays belong to team
            all_actions = soup.find_all('li', {'class': 'x--team-'+team})
            for action in all_actions:

                # technical fouls are counted as rebs for coaches,
                athlete_image = "unknown"
                if action.find('span', {'class': 'athlete-name'}) == None:
                    athlete_name = 'Coach'
                    athlete_image = action.find(
                        'div', {'class': 'action-scores'}).find('img', {'class': 'nat-flag'})['src']
                else:
                    athlete_name = action.find(
                        'span', {'class': 'athlete-name'}).text.strip()
                    athlete_image = action.find(
                        'div', {'class': 'athlete-info'}).find('img')['src']

                quarter = action.find('span', {'class': 'period'}).text.strip()
                time = action.find('span', {'class': 'time'}).text.strip()

                description = action.find(
                    'span', {'class': 'action-description'}).text.strip()

                scores = action.find(
                    'div', {'class': 'score-info'}).find_all('span')
                team_score = scores[0].text.strip()
                opp_score = scores[1].text.strip()

                plays.append({'quarter': quarter,
                              'time': time,
                              'athlete_name': athlete_name,
                              'description': description,
                              'opponent': opponent,
                              'team_score': team_score,  # home team
                              'opp_score': opp_score,
                              'athlete_image': athlete_image})
        except Exception as e:
            print("Error finding play by play data")
            print(e)
        return plays

    def get_boxscore(self, soup=None, team=None):
        boxscore = None
        try:
            print('getting boxscore for team ' + team.upper(), end="")
            team = 'box-score_team-' + team.upper()
            boxscore = soup.find('section', {'class': team})
            print('...done')
        except Exception as e:
            print("...error")
            print(e)
        return boxscore

    def get_ajax_url(self, target_tab=None):
        if target_tab is None:
            raise ValueError(
                "Target tab must be specified (boxsocre, preview, team comparision, play by play etc)")
        data_ajax_url = None

        if target_tab not in self.allowed_tabs:
            raise ValueError(f"Target tab must be one of {self.allowed_tabs}")

        try:
            target_element = self.soup.find(
                'li', {'data-tab-content': target_tab})
            if target_element:
                data_ajax_url = target_element.get('data-ajax-url')
        except Exception as e:
            print(f"Error finding data ajax url for {target_tab}")
        return data_ajax_url

    def ajax_request(self, url=None, headers=None, cookies=None):
        if url is None:
            raise ValueError("URL cannot be empty")

        response = None
        try:
            print('Fetching data...', end='')
            BASE_URL = 'https://www.fiba.basketball'
            if headers is None:
                headers = self.headers
            if cookies is None:
                cookies = self.cookies

            if BASE_URL not in url:
                url = BASE_URL + url
            response = requests.get(
                url, headers=headers, cookies=cookies)
            print('done')

        except Exception as e:
            print("error")
            print(e)

        return response.content if response else None

    # recieves a dict or list of dicts
    def to_csv(self, data=None, filename=None, header=True):
        if filename is None:
            raise ValueError("Filename must be provided.")
        if data is None:
            raise ValueError("Data to be saved must be provided.")

        headers = []
        if header:
            if isinstance(data, list):
                headers = data[0].keys()
            elif isinstance(data, dict):
                headers = data.keys()
            else:
                raise TypeError('data must be a dict or list of dicts')

        print(f'saving data to {filename}.......', end='')
        with open(filename, 'a') as fh:
            writer = csv.DictWriter(fh, fieldnames=headers)
            if header:
                writer.writeheader()

            if isinstance(data, list):
                writer.writerows(data)
            else:
                writer.writerow(data)
        fh.close()
        print('done')

    def to_html(self, data=None, filename=None):
        if filename is None:
            raise ValueError("Filename must be specified")
        if data is None:
            raise ValueError("Data to save must be specified")

        filename = filename.lower()
        print(f"saving data to {filename}...", end="")
        with open(filename, 'w') as fh:
            fh.write(str(data))
        print("done")


if __name__ == '__main__':

    with open('games-links.csv', 'r') as f:
        csv_data = csv.DictReader(f)
        BASE_URL = "https://www.fiba.basketball"

        first = True
        i = 0
        raw_data_path = "final/data/raw/"

        if not os.path.exists(raw_data_path):
            os.makedirs(raw_data_path)

        for d in csv_data:
            i += 1

            url = ""
            if BASE_URL not in d['url']:
                url = BASE_URL + d['url']
            else:
                url = d['url']

            print(f"Iteration ===========: {i}")
            print(f"scrapping ===========: {url}")

            scrapper = WebScrapper()

            scrapper.init(url)

            tabs = ['preview', 'play_by_play', 'boxscore',
                    'videos', 'shot_chart', 'team_comparison']

            # extra data urls
            ajax_urls = {}
            for tab in tabs:
                url = scrapper.get_ajax_url(target_tab=tab)
                ajax_urls[tab] = url

            game_in_brief = scrapper.get_game_in_brief()

            # make request to get boxscore data for both teams
            data = scrapper.ajax_request(url=ajax_urls['boxscore'])

            team_A_name = "team_A"
            team_B_name = "team_B"

            try:
                team_A_name = scrapper.get_team_name('A')
                team_B_name = scrapper.get_team_name('B')
            except:
                pass

            # get each boxscore
            try:
                boxscore_team_A = scrapper.get_boxscore(
                    team='A', soup=BeautifulSoup(data))
                boxscore_team_B = scrapper.get_boxscore(
                    team='B', soup=BeautifulSoup(data))
            except:
                print("Unable to get boxscore data")

            # ------------------- save data -----------------
            # date is prefixed to file name
            date_prefix = game_in_brief[0]['date'].split(" ")[1:]
            date_prefix = "_".join(date_prefix)

            # game in brief
            scrapper.to_csv(data=game_in_brief,
                            filename="all_games_in_brief.csv", header=first)
            first = False
            # save boxscores
            if boxscore_team_A:
                scrapper.to_html(data=boxscore_team_A,
                                 filename=os.path.join(raw_data_path, date_prefix + team_A_name + '_boxscore.html'))
                scrapper.to_html(data=boxscore_team_B,
                                 filename=os.path.join(raw_data_path, date_prefix + team_B_name + '_boxscore.html'))
            # team comparision
            if scrapper.comparison_data:

                scrapper.to_html(data=scrapper.comparison_data, filename=os.path.join(
                    raw_data_path, date_prefix + team_A_name + "_" + team_B_name + '_team_comparison.html'))

            # get play by play data
            sleep(1)
            print("Getting play by play data...", end="")
            try:
                play_by_play_raw_data = scrapper.ajax_request(
                    url=ajax_urls['play_by_play'])
                play_by_play_soup = BeautifulSoup(
                    play_by_play_raw_data, 'html.parser')

                play_by_play_team_A = scrapper.get_game_play_by_play(
                    soup=play_by_play_soup, team="A")

                play_by_play_team_B = scrapper.get_game_play_by_play(
                    soup=play_by_play_soup, team="B")
                print("done")
            except:
                print("Print unable to get play by play data")

            if len(play_by_play_team_A) > 0:

                scrapper.to_csv(data=play_by_play_team_A,
                                filename=os.path.join(raw_data_path, date_prefix + team_A_name + "_pbp.csv"))
                scrapper.to_csv(data=play_by_play_team_B,
                                filename=os.path.join(raw_data_path, date_prefix + team_B_name + "_pbp.csv"))

            print("Sleeping for one second....", end='')
            sleep(1)
            print('done')
