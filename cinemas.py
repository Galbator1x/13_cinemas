import requests
import re

from bs4 import BeautifulSoup

MOVIES_COUNT = 10
AFISHA_SCHEDULE_URL = 'http://www.afisha.ru/msk/schedule_cinema/'


def fetch_afisha_page():
    return requests.get(AFISHA_SCHEDULE_URL).text


def parse_afisha_list(raw_html, min_cinemas_count):
    soup = BeautifulSoup(raw_html, 'html.parser')
    movies = soup.find_all('h3', class_='usetags')
    movie_titles = [movie.find('a').text for movie in movies]
    cinemas = soup.find(id='schedule').find_all('tbody')
    cinemas_count = [len(cinema.find_all('tr')) for cinema in cinemas]

    movies_dict = {}
    for movie_title, cinemas_count in zip(movie_titles, cinemas_count):
        if cinemas_count < min_cinemas_count:
            continue
        movies_dict[movie_title] = fetch_movie_info(movie_title)
        movies_dict[movie_title]['cinemas_count'] = cinemas_count
    return movies_dict


def fetch_movie_info(movie_title):
    url = 'https://www.kinopoisk.ru/index.php'
    payload = {'kp_query': movie_title, 'first': 'yes'}
    movie_html = requests.get(url, params=payload).text
    soup = BeautifulSoup(movie_html, 'html.parser')
    try:
        movie_rating = float(soup.find('span', class_='rating_ball').text)
        movie_votes = soup.find('span', class_='ratingCount').text
        movie_votes = ''.join(re.findall(r'\d+', movie_votes))
    except AttributeError:
        movie_rating, movie_votes = 0, 0
    return {'rating': movie_rating, 'votes': movie_votes}


def output_movies_to_console(movies):
    for movie_title, movie_info in sorted(movies.items(),
                                          key=lambda movie:
                                          movie[1]['rating'],
                                          reverse=True)[:MOVIES_COUNT]:
        print('{} [rating: {}, votes: {}]'.format(movie_title,
                                                  movie_info['rating'],
                                                  movie_info['votes']))


if __name__ == '__main__':
    movies = parse_afisha_list(fetch_afisha_page(),
                               int(input(
                                   'Enter the minimum number of cinemas for the film: ')))
    output_movies_to_console(movies)
