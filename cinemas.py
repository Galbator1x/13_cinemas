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

    cinemas = soup.find(id='schedule')
    cinemas = cinemas.find_all('tbody')
    cinemas_count = [len(cinema.find_all('tr')) for cinema in cinemas]

    movies_dict = {}
    for movie_title, cinemas_count in zip(movie_titles, cinemas_count):
        if cinemas_count < min_cinemas_count:
            continue
        movies_dict[movie_title] = fetch_movie_info(movie_title)
        movies_dict[movie_title]['cinemas_count'] = cinemas_count

    return movies_dict


def fetch_movie_info(movie_title):
    req_movies = requests.get('http://api.kinopoisk.cf/searchFilms?keyword={}'.
                              format(movie_title)).json()
    if req_movies['pagesCount'] == 0:
        return {'rating': 0, 'votes': 0}

    # looking for the right film in response of kinopoisk
    movie_title_set = set(re.findall(r'\w+|\d+', movie_title.lower()))
    for movie_info in req_movies['searchFilms']:
        title_on_kinopoisk_set = set(re.findall(r'\w+|\d+',
                                                movie_info['nameRU'].lower()))
        if movie_title_set == title_on_kinopoisk_set:
            movie_rating, movie_votes = parse_rating_and_votes(movie_info)
            return {'rating': movie_rating,
                    'votes': movie_votes}


def parse_rating_and_votes(movie_info):
    try:
        rating, votes = movie_info['rating'].split(' ', maxsplit=1)
        movie_rating = float(rating)
        movie_votes = votes[1:-1]  # remove redundant parentheses
    except (KeyError, ValueError):
        # if rating and votes does not exists
        movie_rating, movie_votes = 0, 0
    return movie_rating, movie_votes


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
                               int(input('Enter the minimum number of cinemas for the film: ')))
    output_movies_to_console(movies)
