import logging
import dateutil.parser

from red_cards.api import XLEApi, ApiError
from red_cards.models import Event, EventEnroll


def update_events_data(date_txt=''):
    existing_uuids = set(Event.objects.values_list('uuid', flat=True))
    print(XLEApi().get_timetable(date_txt))
    try:
        for event in XLEApi().get_timetable('2019-07-01'):
            uuid = event.get('event_uuid', '')
            activity_uuid = event.get('activity_uuid', '')
            title = event.get('title', '')
            capacity = event.get('capacity', '')
            place = event.get('place', '')
            place_uuid = place.get('uuid', '')
            place_title = place.get('title', '')
            type = event.get('type', '')
            type_uuid = type.get('uuid', '')
            type_title = type.get('title', '')
            start_dt = dateutil.parser.parse(event.get('start_dt'))
            end_dt = dateutil.parser.parse(event.get('end_dt'))
            e, e_created = Event.objects.update_or_create(uuid=uuid,
                                                          defaults={'activity_uuid': activity_uuid, 'title': title,
                                                                    'capacity': capacity, 'place_uuid': place_uuid,
                                                                    'place_title': place_title, 'type_uuid': type_uuid,
                                                                    'type_title': type_title, 'start_dt': start_dt,
                                                                    'end_dt': end_dt})
    except ApiError:
        return False
    except Exception:
        logging.exception('Failed to get timetable')


def update_enrolls_data(event_uuid):
    try:
        for enroll in XLEApi().get_enrolls(event_uuid):
            print(enroll)
            unti_id = enroll.get('unti_id', '')
            created_dt = dateutil.parser.parse(enroll.get('create_dt', ''))
            e, e_created = EventEnroll.objects.update_or_create(event_uuid=event_uuid, unti_id=unti_id,
                                                                defaults={'created_dt': created_dt})
    except ApiError:
        return False
    except Exception:
        logging.exception('Failed to get enrolls')
