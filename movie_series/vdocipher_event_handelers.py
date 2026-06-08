import json

from rest_framework.response import Response
from .vdocipher_client import VdocipherClient

from .models import (
    Movie, Genre, Series,
    Season, Episode
)


client = VdocipherClient()


def create_or_update_movie(video_info):
    video_id = video_info['id']
    description = video_info['description']
    tags = video_info['tags']
    payload = {'file_uuid': video_id}

    if (dsc := description.strip()).isdigit():
        if len(dsc) >= 4:
            payload['release_year'] = int(dsc)

    if (yr_dsc := dsc.split('\n\n', maxsplit=2)).__len__() == 2:
        yr, dsc_new = yr_dsc
        if len(yr) >= 4:
            payload['release_year'] = yr
        payload['description'] = dsc_new
    else:
        payload['description'] = dsc

    payload['title'] = video_info['title'].rsplit('.', maxsplit=2)[0]


    print("DEBUG >>> << ", video_info['poster'])

    if video_info.get('poster'):
        payload['posters_url'] = [video_info.get('poster')]
    else:
        payload['posters_url'] = [
            poster['posterUrl']
            for poster in video_info['posters']
        ]

    genres = Genre.get_or_create_genres_safe(tags)
    # payload['genres'] = genres
    movie, _created = Movie.objects.update_or_create(
        title=payload['title'],
        defaults=payload,
        create_defaults=payload
    )
    movie.genres.set(genres)
    return Response({
        "msg": "video record added."
    })


def create_or_update_series_episode(video_info, folder_tree):
    video_id = video_info['id']
    description = video_info['description']
    tags = video_info['tags']
    payload = {'file_uuid': video_id}

    series_name, season_name = folder_tree[-2], folder_tree[-3]

    if (dsc := description.strip()).isdigit():
        if len(dsc) >= 4:
            payload['release_year'] = int(dsc)

    if (yr_dsc := dsc.split('\n\n', maxsplit=2)).__len__() == 2:
        yr, dsc_new = yr_dsc
        if len(yr) >= 4:
            payload['release_year'] = yr
        payload['description'] = dsc_new
    else:
        payload['description'] = dsc

    payload['title'] = video_info['title'].rsplit('.', maxsplit=2)[0]

    genres = Genre.get_or_create_genres_safe(tags)
    # payload['genres'] = genres

    series, _created = Series.objects.update_or_create(
        name=series_name
    )
    series.genres.set(genres)

    season, _created = Season.objects.update_or_create(
        series=series,
        season_name=season_name
    )
    episode, _created = Episode.objects.update_or_create(
        season=season,
        title=payload['title'],
        defaults={'file_uuid': video_id},
        create_defaults={'file_uuid': video_id}
    )
    series.posters_url = [
        poster['posterUrl']
        for poster in video_info['posters']
    ]

    series.save()
    return Response({
        "msg": "video record added."
    })


def handle_video_ready(payload):
    video_id = payload['id']
    tags = payload['tags']
    folder_tree = [pth['name'] for pth in payload['folderPath']]

    # if year and year.isdigit()

    if len(folder_tree) == 0 or (
            folder_tree[0] == 'series' and len(folder_tree) != 3
            ) or (folder_tree[0] == 'movies' and len(folder_tree) != 1):
        return Response({
            "message": "a video should be in one of the following path:\n"
                       "movies/<single: video_file> or,\n"
                       " series/<list: series_name>/<list: season_name>/"
                       " <list:video_file>"
        }, 400)

    video_info, _err = client.get_video_detail(video_id)
    if _err:
        return Response({"err": _err}, 400)

    if len(folder_tree) == 1:
        return create_or_update_movie(video_info)
    else:
        return create_or_update_series_episode(video_info, folder_tree)


def handle_video_update(payload):
    video_id = payload['videoId']
    folder_tree = [pth['name'] for pth in payload['folderPath']]

    if len(folder_tree) == 0 or (
            folder_tree[0] == 'series' and len(folder_tree) != 3
            ) or (folder_tree[0] == 'movies' and len(folder_tree) != 1):
        return Response({
            "message": "a video should be in one of the following path:\n"
                       "movies/<single: video_file> or,\n"
                       " series/<list: series_name>/<list: season_name>/"
                       " <list:video_file>"
        }, 400)

    video_info, _err = client.get_video_detail(video_id)

    if _err:
        return Response({"err": _err}, 400)

    if len(folder_tree) == 1:
        return create_or_update_movie(video_info)
    else:
        return create_or_update_series_episode(video_info, folder_tree)


def handle_video_error(payload):
    video_id = payload['id']
    pass


def handle_video_delete(payload):
    video_ids = payload['videoIds']

    Movie.objects.filter(file_uuid__in=video_ids).delete()
    Episode.objects.filter(file_uuid__in=video_ids).delete()
    return Response()


def handle_poster_uploaded(payload):
    video_id = payload['videoId']
    folder_tree = [pth['name'] for pth in payload['folderPath']]

    # if year and year.isdigit()

    if len(folder_tree) == 0 or (
            folder_tree[0] == 'series' and len(folder_tree) != 3
            ) or (folder_tree[0] == 'movies' and len(folder_tree) != 1):
        return Response({
            "message": "a video should be in one of the following path:\n"
                       "movies/<single: video_file> or,\n"
                       " series/<list: series_name>/<list: season_name>/"
                       " <list:video_file>"
        }, 400)

    video_info, _err = client.get_video_detail(video_id)
    print("VIDINFO ", len(folder_tree))
    print(print(json.dumps(video_info, indent=2)))

    return Response()
    if _err:
        return Response({"err": _err}, 400)

    if len(folder_tree) == 1:
        return create_or_update_movie(video_info)
    else:
        return create_or_update_series_episode(video_info, folder_tree)
    pass


def handle_caption_uploaded(payload):
    pass


VDOCIPHER_EVENT_HANDLERS = {
    'video:ready': handle_video_ready,
    'video:updated': handle_video_update,
    'video:error': handle_video_error,
    'video:deleted': handle_video_delete,
    'poster:uploaded': handle_poster_uploaded,
    'caption:uploaded': handle_caption_uploaded,
}