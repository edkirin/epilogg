# Channels consumers

## OnLogEventConsumer

URL: `ws:/ws/on_log_event/`

### connect()

Params: none

### watch_client_app()

Params:

- cmd: `watch_client_app`
- client_app_id
- filter_level
- filter_category

### watch_facility()

Params:

- cmd: `watch_facility`
- facility_id
- filter_level
- filter_category

### watch_all()

Params:

- cmd: `watch_all`

