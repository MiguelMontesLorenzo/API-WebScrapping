import requests
from bs4 import BeautifulSoup

import numpy as np
import pandas as pd

import os
import plotly.express as px
from xhtml2pdf import pisa


import json




season = 2023


API_key = None




def extract():

    global season
    global API_key


    #GET THE MOST LIKELY TO WIN TEAMS ACCORDING TO BETTING HOUSES
    ##################################################################
    #SCRAP INFO USING BEAUTIFULSOUP
    ###############################
    r = requests.get('https://www.sportytrader.es/pronosticos/baloncesto/usa/nba-306/')
    soup = BeautifulSoup(r.text, "lxml")

    #get all div's
    # divs = soup.find_all('div')
    div_class = 'prose max-w-none mx-auto mt-10 px-box'.replace(' ','.')
    divs = soup.find_all('div', {'class': 'prose max-w-none mx-auto mt-10 px-box'})

    #find the div containing the ranking
    def find_ul_tag(divs):
        for div in divs:
            # print(type(div))
            # input(div)
            uls = div.find_all('ul')
            if len(uls) > 0:
                return div.ul

    #obtain all th info from the ranking
    def return_all_li(ul):
        lst = list()
        li_tags = ul.find_all('li')
        for li in li_tags:
            lst.append(li.text)
        return lst

    l = return_all_li(find_ul_tag(divs))


    sep = ', cuota de'   #añadir la cadena de texto que separa el nombre del equipo y el valor de la cuota 
    lst = { string.split(sep)[0].strip(): float(string.split(sep)[1]) for string in return_all_li(find_ul_tag(divs)) }



    print(lst)
    ####################################################################






    #GET OTHER DATA FROM THE SPORTS.IO API
    ##################################################################
    

    # DEFINE CREDENTIALS TO ACCESS THE API
    # API_key = '55cd35925fd2478b8926718647ab1be4'
    # params = {"query": f"{API_key}"}
    # headers = {"Ocp-Apim-Subscription-Key": f"{API_key}"}

    # DEFINE CREDENTIALS TO ACCESS THE API
    params = {"query": f"{API_key}"}
    headers = {"Ocp-Apim-Subscription-Key": f"{API_key}"}


    # OBTAIN EVERY TEAM ID AN ABBREVIATION
    URL = 'https://api.sportsdata.io/v3/nba/scores/json/teams'
    API_response = requests.get(url = URL, headers = headers)
    all_active_team_info = API_response.json()



    # print(json.dumps(all_active_team_info))





    nba_teams = [   'Atlanta Hawks', 'Boston Celtics', 'Brooklyn Nets', 'Charlotte Hornets', 'Chicago Bulls', 'Cleveland Cavaliers',
                    'Dallas Mavericks', 'Denver Nuggets', 'Detroit Pistons', 'Golden State Warriors', 'Houston Rockets', 'Indiana Pacers',
                    'Los Angeles Clippers', 'Los Angeles Lakers', 'Memphis Grizzlies', 'Miami Heat', 'Milwaukee Bucks', 'Minnesota Timberwolves',
                    'New Orleans Pelicans', 'New York Knicks', 'Oklahoma City Thunder', 'Orlando Magic', 'Philadelphia 76ers', 'Phoenix Suns',
                    'Portland Trail Blazers', 'Sacramento Kings', 'San Antonio Spurs', 'Toronto Raptors', 'Utah Jazz', 'Washington Wizards']



    # GET THE ABREVIATIONS OF EACH TEAM:
    dict_of_nba_teams = dict()
    for team_info in all_active_team_info:
        # input(team_info)
        team_name = None
        city = team_info['Name'].lower()
        for team in nba_teams:
            if city in team.lower():
                team_name = team

        dict_of_nba_teams[team_info['TeamID']] = {'abbreviation': team_info['Key'], 'name': team_name, 'games': dict(), 'players': None}








    # GET GAMES INFO BY TEAM:
    for team_id, team_info in dict_of_nba_teams.items():
        season = '2023'
        number_of_games = 'all'

        URL = f'https://api.sportsdata.io/v3/nba/scores/json/TeamGameStatsBySeason/{season}/{team_id}/{number_of_games}'
        API_response = requests.get(url = URL, headers = headers)
        team_games_info = API_response.json()


        for game in team_games_info:

            if type(game) == dict():
                win = bool(game['Wins'])
                free_throws_made = game['FreeThrowsMade']
                two_pointers_made = game['TwoPointersMade']
                three_pointers_made = game['ThreePointersMade']

                two_pointers_points = np.round(2*two_pointers_made, 2)
                three_pointers_points = np.round(3*three_pointers_made, 2)

                total_points_made = np.round(free_throws_made + two_pointers_points + three_pointers_points, 2)
                opponent_id = game['OpponentID']

                dict_of_nba_teams[team_id]['games'][opponent_id] = {'win': win, 'one': free_throws_made, 'two': two_pointers_points, 'three': three_pointers_points ,'total_points': total_points_made, 'opponent_points': None}


    for team_id, team_info in dict_of_nba_teams.items():
        for opponent_id, opponent_info in dict_of_nba_teams.items():

            if opponent_id in team_info['games']:
                team_info['games'][opponent_id]['opponent_points'] = opponent_info['games'][team_id]['total_points']




    finish = False

    while not finish:

        print('Select one NBA team:')
        for team_id, team_info in dict_of_nba_teams.items():
            print('  ' + str(team_id) + ' - ' + team_info['name'])

        try:
            selection = int(input('Enter de team ID: '))
        except:
            selection = None

        if selection in dict_of_nba_teams:
            selected_team_id = selection
            finish = True
            print(f'Equipo seleccionado: {dict_of_nba_teams[selected_team_id]["name"]}')
        else:
            print('ERROR, valor incorrecto')





    # GET PLAYERS INFO BY TEAM:
    team_players_stats = dict()


    team_abbreviation = dict_of_nba_teams[selected_team_id]['abbreviation']
    URL = f'https://api.sportsdata.io/v3/nba/scores/json/Players/{team_abbreviation}'
    API_response = requests.get(url = URL, headers = headers)
    team_players_info = API_response.json()

    # For each player in the team
    for player_pre_info in team_players_info:
        team_players_stats[player_pre_info['PlayerID']] = {'name': player_pre_info['FirstName'] + ' ' + player_pre_info['LastName'], 'jersey': player_pre_info['Jersey']}

    
    # Obtain scored poins and minutes played throughout the hole season
    for player_id, player_info in team_players_stats.items():

        number_of_games = 'all'

        team_abbreviation = dict_of_nba_teams[selected_team_id]['abbreviation']
        URL = f'https://api.sportsdata.io/v3/nba/stats/json/PlayerGameStatsBySeason/{season}/{player_id}/{number_of_games}'
        API_response = requests.get(url = URL, headers = headers)
        player_info = API_response.json()


        team_players_stats[player_id]['ratio'] = list()
        total_minutes = 0
        total_points = 0

        games_played = 0

        # For each game played by the player add the minutes and the scored points
        for game in player_info:
            free_throws_made = game['FreeThrowsMade']
            two_pointers_made = game['TwoPointersMade']
            three_pointers_made = game['ThreePointersMade']

            minutes = game['Minutes']
            seconds = game['Seconds']

            two_pointers_points = np.round(2*two_pointers_made, 4)
            three_pointers_points = np.round(3*three_pointers_made, 4)

            game_points_made = np.round(free_throws_made + two_pointers_points + three_pointers_points, 4)
            game_minutes = minutes + (seconds/60)


            if not game_minutes == 0:
                total_minutes += game_minutes
                total_points += game_points_made
                games_played += 1


        # Obtain the ratio points/minute for each player
        try:
            team_players_stats[player_id]['ratio'] = total_points/total_minutes if not total_minutes == 0 else 0
        except:
            pass


    dict_of_nba_teams[selected_team_id]['players'] = team_players_stats


    return dict_of_nba_teams, selected_team_id





def transform(dict_of_nba_teams, selected_team_id):

    # OBTAIN DATAFRAME FOR FIGURE 1
    dic_for_df1 = {'opponent name': list(), '1': list(), '2': list(), '3': list(), 'total points': list(), 'opponent points': list()}

    for opponent_id, game in dict_of_nba_teams[selected_team_id]['games'].items():

        dic_for_df1['opponent name'].append(dict_of_nba_teams[opponent_id]['name'])
        dic_for_df1['1'].append(np.round(game['one'], 2))
        dic_for_df1['2'].append(np.round(2*game['two'], 2))
        dic_for_df1['3'].append(np.round(3*game['three'], 2))
        dic_for_df1['total points'].append(np.round(game['total_points']))
        dic_for_df1['opponent points'].append(np.round(game['opponent_points'], 2))

    df_for_figure_1 = pd.DataFrame.from_dict(data=dic_for_df1)



    # OBTAIN DATAFRAME FOR FIGURE 2
    dic_for_df2 = {'opponent name': list(), 'wins': list()}
    wins = 0

    for opponent_id, game in dict_of_nba_teams[selected_team_id]['games'].items():

        wins = wins + 1 if game['win'] else wins
        dic_for_df2['opponent name'].append(dict_of_nba_teams[opponent_id]['name'])
        dic_for_df2['wins'].append(wins)

    df_for_figure_2 = pd.DataFrame.from_dict(data = dic_for_df2)



    # OBTAIN DATAFRAME FOR FIGURE 3
    dic_for_df3 = {'player name': list(), 'points per game': list()}

    for player_info in dict_of_nba_teams[selected_team_id]['players'].values():


        dic_for_df3['player name'].append(player_info['name'])
        dic_for_df3['points per game'].append(player_info['ratio'])

    df_for_figure_3 = pd.DataFrame.from_dict(data = dic_for_df3)
    df_for_figure_3.sort_values(by='points per game', ascending=False, inplace=True)
    df_for_figure_3 = df_for_figure_3.head(10)
    print(df_for_figure_3)


    return df_for_figure_1, df_for_figure_2, df_for_figure_3





def load(df1, df2, df3, dict_of_nba_teams, selected_team_id):



    # CREATE FIGURE 1: POINTS FOR AND AGAINST
    print(df1)
    fig1a = px.bar(  data_frame=df1,
                    x='opponent name',
                    y='total points',
                    title='Orders by pizza size',
                    color_discrete_map = {'total points': '#29E542'},#='#29E542',
                    text_auto=True #añadir etiquetas sobre las barras
                    )
                
    fig1a.update_layout(title_text='POINTS SCORED BY GAME', #título
                        uniformtext_minsize=10, #tamaño del texto
                        autosize=False, width=1200, height=600) #tamaño gráfico


    fig1b = px.bar( data_frame=df1,
                    x='opponent name',
                    y='opponent points',
                    title='Orders by pizza size',
                    color_discrete_map = {'opponent points': '#D6453E'},#='#29E542',
                    # fill='#D6453E',
                    text_auto=True #añadir etiquetas sobre las barras
                    )
                
    fig1b.update_layout(title_text='OPPONENT POINTS BY GAME', #título
                        uniformtext_minsize=10, #tamaño del texto
                        autosize=False, width=1200, height=600) #tamaño gráfico


    # CREATE FIGURE 2: VICTORIES EVOLUTION
    print(df2)
    fig2 = px.area( data_frame=df2,
                    x='opponent name', 
                    y=df2.columns,
                    color_discrete_map = {'wins': '#00BDFF'}
                    )
    fig2.update_layout( title_text='VICTORIES EVOLUTION',
                        uniformtext_minsize=10,
                        autosize=False,width=1200, height=600)

    # CREATE FIGURE 3
    print(df3)
    fig3 = px.bar(  data_frame=df3,
                    x='player name',
                    y='points per game',
                    color_discrete_map = {'total points': '#29E542'},
                    # color='#29E542',
                    text_auto=True #añadir etiquetas sobre las barras
                    )
                
    fig3.update_layout(title_text='POINTS/MINUTE PER PLAYER', #título
                        uniformtext_minsize=10, #tamaño del texto
                        autosize=False, width=1200, height=600) #tamaño gráfico




    def report_block_template(graph_url):
        graph_block = (
            '<a>' # Open the interactive graph when you click on the image
                f'<img style="height: 400px;" src="{graph_url}">'
            '</a><hr>')

        return graph_block


    # Convertion function
    def convert_html_to_pdf(source_html, output_filename):
        # open output file for writing (truncated binary)
        result_file = open(output_filename, 'w+b')

        # convert HTML to PDF
        pisa_status = pisa.CreatePDF(
                src=source_html,            # the HTML to convert
                dest=result_file)           # file handle to recieve result

        # close output file
        result_file.close()

        # return True on success and False on errors
        return pisa_status.err


    figs = [fig1a, fig1b, fig2, fig3]

    # crear directorio
    if not os.path.exists('plotly_figures_jpg'):
        os.mkdir('plotly_figures_jpg')

    # guardar imágenes
    for i, fig in enumerate(figs):
        fig.write_image(f"plotly_figures_jpg/fig{i+1}.jpg")


    static_report = ''

    #Store image paths from images I want to incluede in the report
    graphs = [f'plotly_figures_jpg/fig{i+1}.jpg' for i,fig in enumerate(figs)]
    for graph_url in graphs:

        static_block = report_block_template(graph_url)
        static_report += static_block


    # Obtain win probability
    next_opponent = 'tal'
    # next_opponent = dict_of_nba_teams[next_opponent_id]['name']
    win_probability = 0.5


    title = (
        '<h1>'
            f'TEAM: {dict_of_nba_teams[selected_team_id]["name"]}'
        '</h1>'
        '<h2>'
            f'NEXT OPPONENT: {next_opponent}      - win probabity: {win_probability}'
        '</h2><hr>\n'
            )

    static_report = title + static_report
    print(convert_html_to_pdf(static_report, 'report.pdf'))



if __name__ == '__main__':

    nba_teams_data, selected_team_id = extract()
    df1, df2, df3 = transform(nba_teams_data, selected_team_id)
    load(df1, df2, df3, nba_teams_data, selected_team_id)