import ssl
from datetime import timedelta
from django.utils import timezone
from receiver.models import Data
import paho.mqtt.client as mqtt
import schedule
import time
from django.conf import settings

client = mqtt.Client(settings.MQTT_USER_PUB)

ALERT_WINDOW_MINUTES = 5
ALERT_MIN_POINTS = 30
ALERT_COOLDOWN_MINUTES = 2

_last_alert_sent_at = {}


def analyze_data():
    print("Calculando alertas...")

    now = timezone.now()
    window_start = now - timedelta(minutes=ALERT_WINDOW_MINUTES)
    window_start_hour = window_start.replace(minute=0, second=0, microsecond=0)
    data = Data.objects.filter(base_time__gte=window_start_hour) \
        .select_related('station', 'measurement') \
        .select_related('station__user', 'station__location') \
        .select_related('station__location__city', 'station__location__state',
                        'station__location__country') \
        .order_by('-base_time')

    grouped_data = {}
    for row in data:
        key = (row.station_id, row.measurement_id)
        if key not in grouped_data:
            grouped_data[key] = {
                'values': [],
                'measurement': row.measurement.name,
                'max_value': row.measurement.max_value,
                'min_value': row.measurement.min_value,
                'country': row.station.location.country.name,
                'state': row.station.location.state.name,
                'city': row.station.location.city.name,
                'user': row.station.user.username,
            }

        row_times = row.times or []
        row_values = row.values or []
        max_points = min(len(row_times), len(row_values))
        for index in range(max_points):
            sample_second = row_times[index]
            sample_value = row_values[index]

            if sample_value is None:
                continue

            sample_time = row.base_time + timedelta(seconds=float(sample_second))
            if sample_time < window_start:
                continue

            grouped_data[key]['values'].append(sample_value)

    alerts = 0
    reviewed = 0

    for key, item in grouped_data.items():
        station_id, measurement_id = key
        values = item['values']

        variable = item['measurement']
        max_value = item['max_value']
        min_value = item['min_value']

        if max_value is None and min_value is None:
            continue

        violations = 0
        for value in values:
            if max_value is not None and value > max_value:
                violations += 1
                continue
            if min_value is not None and value < min_value:
                violations += 1

        reviewed += 1
        if violations < ALERT_MIN_POINTS:
            continue

        last_sent_at = _last_alert_sent_at.get(key)
        if last_sent_at and now - last_sent_at < timedelta(minutes=ALERT_COOLDOWN_MINUTES):
            print(
                "[DEBUG] Skip station={} measurement={} variable={} reason=cooldown last_sent_at={} cooldown_minutes={}".format(
                    station_id,
                    measurement_id,
                    variable,
                    last_sent_at,
                    ALERT_COOLDOWN_MINUTES
                )
            )
            continue

        country = item['country']
        state = item['state']
        city = item['city']
        user = item['user']

        message = "ALERT {} min={} max={}".format(
            variable,
            min_value,
            max_value
        )
        topic = '{}/{}/{}/{}/in'.format(country, state, city, user)
        print(now, "Sending alert to {} {}".format(topic, variable))
        client.publish(topic, message)
        _last_alert_sent_at[key] = now
        alerts += 1

    print(reviewed, "dispositivos revisados")
    print(alerts, "alertas enviadas")


def on_connect(client, userdata, flags, rc):
    '''
    Función que se ejecuta cuando se conecta al bróker.
    '''
    print("Conectando al broker MQTT...", mqtt.connack_string(rc))


def on_disconnect(client: mqtt.Client, userdata, rc):
    '''
    Función que se ejecuta cuando se desconecta del broker.
    Intenta reconectar al bróker.
    '''
    print("Desconectado con mensaje:" + str(mqtt.connack_string(rc)))
    print("Reconectando...")
    client.reconnect()


def setup_mqtt():
    '''
    Configura el cliente MQTT para conectarse al broker.
    '''

    print("Iniciando cliente MQTT...", settings.MQTT_HOST, settings.MQTT_PORT)
    global client
    try:
        client = mqtt.Client(settings.MQTT_USER_PUB)
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect

        if settings.MQTT_USE_TLS:
            client.tls_set(ca_certs=settings.CA_CRT_PATH,
                           tls_version=ssl.PROTOCOL_TLSv1_2, cert_reqs=ssl.CERT_NONE)

        client.username_pw_set(settings.MQTT_USER_PUB,
                               settings.MQTT_PASSWORD_PUB)
        client.connect(settings.MQTT_HOST, settings.MQTT_PORT)

        client.loop_start()
    except Exception as e:
        print('Ocurrió un error al conectar con el bróker MQTT:', e)


def start_cron():
    '''
    Inicia el cron que se encarga de ejecutar la función analyze_data cada 5 minutos.
    '''
    print("Iniciando cron...")
    schedule.every(1).minutes.do(analyze_data)
    print("Servicio de control iniciado")
    while 1:
        schedule.run_pending()
        time.sleep(1)
