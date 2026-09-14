from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort, Response
from datetime import datetime, date, timedelta
import random
from werkzeug.security import check_password_hash
from app.firebase_db import db

main_bp = Blueprint('main', __name__)

def parse_datetime(val):
    if isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(val)
    except Exception:
        return datetime.now()

def shift_schedule_dates(sch, target_date=None):
    if target_date is None:
        target_date = (datetime.now() + timedelta(days=1)).date()

    orig_dep = parse_datetime(sch.get('departure_time'))
    orig_arr = parse_datetime(sch.get('arrival_time'))
    duration = orig_arr - orig_dep

    new_dep = datetime.combine(target_date, orig_dep.time())
    new_arr = new_dep + duration

    sch['departure_time'] = new_dep
    sch['arrival_time'] = new_arr

    stops = sch.get('stops', [])
    for st in stops:
        if st.get('arrival_time'):
            orig_stop_arr = parse_datetime(st['arrival_time'])
            st['arrival_time'] = new_dep + (orig_stop_arr - orig_dep)
        if st.get('departure_time'):
            orig_stop_dep = parse_datetime(st['departure_time'])
            st['departure_time'] = new_dep + (orig_stop_dep - orig_dep)

    sch['stops'] = stops
    return sch, duration

def generate_train_carriages(schedule_id, train_type):
    rng = random.Random(str(schedule_id))
    carriages = []

    if 'Ласточка' in train_type:
        seats = []
        for i in range(1, 69):
            is_window = (i % 4 in [1, 0])
            seats.append({
                "number": i,
                "type": "У окна" if is_window else "У прохода",
                "available": rng.random() > 0.42
            })
        carriages.append({
            "id": "seating",
            "name": "Вагон 03 — Сидячий (2 класс)",
            "category": "seating",
            "seats": seats,
            "free": sum(1 for s in seats if s["available"]),
            "total": len(seats)
        })
    else:
        coupe_compartments = []
        for comp_idx in range(9):
            start = comp_idx * 4 + 1
            places = [
                {"number": start, "type": "Нижняя полка", "available": rng.random() > 0.5},
                {"number": start + 1, "type": "Верхняя полка", "available": rng.random() > 0.35},
                {"number": start + 2, "type": "Нижняя полка", "available": rng.random() > 0.55},
                {"number": start + 3, "type": "Верхняя полка", "available": rng.random() > 0.4}
            ]
            coupe_compartments.append({
                "number": comp_idx + 1,
                "places": places
            })

        coupe_all = [p for c in coupe_compartments for p in c["places"]]
        carriages.append({
            "id": "coupe",
            "name": "Вагон 05 — Купе (Спальный)",
            "category": "coupe",
            "compartments": coupe_compartments,
            "free": sum(1 for p in coupe_all if p["available"]),
            "total": len(coupe_all)
        })

        platz_compartments = []
        for comp_idx in range(9):
            start = comp_idx * 4 + 1
            main_places = [
                {"number": start, "type": "Нижняя полка", "available": rng.random() > 0.4},
                {"number": start + 1, "type": "Верхняя полка", "available": rng.random() > 0.3},
                {"number": start + 2, "type": "Нижняя полка", "available": rng.random() > 0.45},
                {"number": start + 3, "type": "Верхняя полка", "available": rng.random() > 0.35}
            ]
            side_num = 54 - (comp_idx * 2)
            side_places = [
                {"number": side_num - 1, "type": "Боковая нижняя", "available": rng.random() > 0.4},
                {"number": side_num, "type": "Боковая верхняя", "available": rng.random() > 0.3}
            ]
            platz_compartments.append({
                "number": comp_idx + 1,
                "main_places": main_places,
                "side_places": side_places
            })

        platz_all = [p for c in platz_compartments for p in (c["main_places"] + c["side_places"])]
        carriages.append({
            "id": "platzkart",
            "name": "Вагон 08 — Плацкарт (Спальный)",
            "category": "platzkart",
            "compartments": platz_compartments,
            "free": sum(1 for p in platz_all if p["available"]),
            "total": len(platz_all)
        })

    return carriages

@main_bp.route('/')
def index():
    stations_ref = db.collection('stations').stream()
    stations = []
    for doc in stations_ref:
        st = doc.to_dict()
        st['id'] = doc.id
        stations.append(st)
    
    stations.sort(key=lambda x: (x.get('city', ''), x.get('name', '')))
    tomorrow = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
    return render_template('index.html', stations=stations, tomorrow=tomorrow)

@main_bp.route('/search')
def search():
    dep_id = request.args.get('departure_id')
    arr_id = request.args.get('arrival_id')
    train_type = request.args.get('train_type')
    sort_by = request.args.get('sort_by', 'time')
    search_date_str = request.args.get('date')

    if search_date_str:
        try:
            target_date = datetime.strptime(search_date_str, '%Y-%m-%d').date()
        except Exception:
            target_date = (datetime.now() + timedelta(days=1)).date()
    else:
        target_date = (datetime.now() + timedelta(days=1)).date()

    schedules_ref = db.collection('schedules').stream()
    results = []
    
    for doc in schedules_ref:
        sch = doc.to_dict()
        sch['id'] = doc.id

        if dep_id and sch.get('departure_station_id') != dep_id:
            continue
        if arr_id and sch.get('arrival_station_id') != arr_id:
            continue
        if train_type and train_type != 'all':
            current_type = sch.get('train', {}).get('train_type', '')
            if train_type not in current_type:
                continue

        sch, duration = shift_schedule_dates(sch, target_date)
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60

        results.append({
            "item": sch,
            "duration": f"{hours} ч {minutes} мин",
            "duration_seconds": total_seconds,
            "price": float(sch.get('base_price', 0))
        })

    if sort_by == 'price':
        results.sort(key=lambda x: x['price'])
    elif sort_by == 'duration':
        results.sort(key=lambda x: x['duration_seconds'])
    else:
        results.sort(key=lambda x: x['item']['departure_time'])

    dep_station = db.collection('stations').document(dep_id).get().to_dict() if dep_id else None
    arr_station = db.collection('stations').document(arr_id).get().to_dict() if arr_id else None

    return render_template(
        'search_results.html',
        results=results,
        dep_station=dep_station,
        arr_station=arr_station,
        count=len(results),
        dep_id=dep_id,
        arr_id=arr_id,
        train_type=train_type,
        sort_by=sort_by
    )

@main_bp.route('/train/<schedule_id>')
def train_detail(schedule_id):
    doc = db.collection('schedules').document(schedule_id).get()
    if not doc.exists:
        abort(404)
    
    schedule = doc.to_dict()
    schedule['id'] = doc.id
    schedule, duration = shift_schedule_dates(schedule)

    total_seconds = int(duration.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60

    train_type = schedule.get('train', {}).get('train_type', '')
    carriages = generate_train_carriages(schedule_id, train_type)

    return render_template(
        'train_detail.html',
        schedule=schedule,
        stops=schedule.get('stops', []),
        duration=f"{hours} ч {minutes} мин",
        carriages=carriages
    )

@main_bp.route('/train/<schedule_id>/export-ics')
def export_ics(schedule_id):
    doc = db.collection('schedules').document(schedule_id).get()
    if not doc.exists:
        abort(404)
    
    sch = doc.to_dict()
    sch, _ = shift_schedule_dates(sch)
    dep_time = sch.get('departure_time')
    arr_time = sch.get('arrival_time')

    train_info = sch.get('train') or {}
    dep_station_info = sch.get('departure_station') or {}
    arr_station_info = sch.get('arrival_station') or {}

    train_num = train_info.get('number', '000')
    train_name = train_info.get('name', '')
    dep_st = dep_station_info.get('name', 'Вокзал отправления')
    arr_st = arr_station_info.get('name', 'Вокзал прибытия')
    platform = sch.get('platform', '1')
    status = sch.get('status', 'По расписанию')

    dt_start = dep_time.strftime('%Y%m%dT%H%M%S') if dep_time else ''
    dt_end = arr_time.strftime('%Y%m%dT%H%M%S') if arr_time else ''
    dt_now = datetime.now().strftime('%Y%m%dT%H%M%SZ')

    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//RZD-Info//Train Schedule System//RU",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:train-{schedule_id}-{dt_start}@rzd-info.ru",
        f"DTSTAMP:{dt_now}",
        f"DTSTART:{dt_start}",
        f"DTEND:{dt_end}",
        f"SUMMARY:Поезд {train_num} ({train_name}): {dep_st} - {arr_st}",
        f"DESCRIPTION:Справочная информация о рейсе. Платформа {platform}. Статус: {status}.",
        f"LOCATION:{dep_st}",
        "STATUS:CONFIRMED",
        "END:VEVENT",
        "END:VCALENDAR"
    ]
    ics_content = "\r\n".join(ics_lines)

    # Имя файла только в ASCII для предотвращения падения WSGI/Gunicorn с UnicodeEncodeError (502 Bad Gateway)
    safe_filename = f"train_schedule_{schedule_id[:8]}.ics"

    response = Response(
        ics_content.encode('utf-8'),
        mimetype="text/calendar; charset=utf-8"
    )
    response.headers["Content-Disposition"] = f'attachment; filename="{safe_filename}"'
    return response

@main_bp.route('/board')
def board():
    station_id = request.args.get('station_id')
    stations_ref = db.collection('stations').stream()
    stations = []
    for doc in stations_ref:
        st = doc.to_dict()
        st['id'] = doc.id
        stations.append(st)
    stations.sort(key=lambda x: x.get('city', ''))

    if not station_id and stations:
        station_id = stations[0]['id']

    selected_station = None
    if station_id:
        st_doc = db.collection('stations').document(station_id).get()
        if st_doc.exists:
            selected_station = st_doc.to_dict()
            selected_station['id'] = st_doc.id

    departures = []
    arrivals = []

    schedules_ref = db.collection('schedules').stream()
    for doc in schedules_ref:
        sch = doc.to_dict()
        sch['id'] = doc.id
        sch, _ = shift_schedule_dates(sch)

        if station_id and sch.get('departure_station_id') == station_id:
            departures.append(sch)
        if station_id and sch.get('arrival_station_id') == station_id:
            arrivals.append(sch)

    departures.sort(key=lambda x: x['departure_time'])
    arrivals.sort(key=lambda x: x['arrival_time'])

    return render_template('board.html', stations=stations, selected_station=selected_station, departures=departures, arrivals=arrivals)

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        users_ref = db.collection('users').where('username', '==', username).limit(1).stream()
        user_list = [u.to_dict() for u in users_ref]

        if user_list and check_password_hash(user_list[0]['password_hash'], password):
            session['user_id'] = username
            session['username'] = username
            flash('Авторизация выполнена успешно.', 'success')
            return redirect(url_for('main.admin'))
        else:
            flash('Неверный логин или пароль.', 'danger')

    return render_template('login.html')

@main_bp.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('main.index'))

@main_bp.route('/admin')
def admin():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    schedules = []
    for doc in db.collection('schedules').stream():
        sch = doc.to_dict()
        sch['id'] = doc.id
        sch, _ = shift_schedule_dates(sch)
        schedules.append(sch)

    schedules.sort(key=lambda x: x['departure_time'], reverse=True)

    stations = []
    for doc in db.collection('stations').stream():
        st = doc.to_dict()
        st['id'] = doc.id
        stations.append(st)

    trains = []
    for doc in db.collection('trains').stream():
        tr = doc.to_dict()
        tr['id'] = doc.id
        trains.append(tr)

    return render_template('admin.html', schedules=schedules, trains=trains, stations=stations)

@main_bp.route('/admin/schedule/add', methods=['POST'])
def add_schedule():
    if 'user_id' not in session:
        abort(403)

    try:
        train_id = request.form.get('train_id')
        dep_station_id = request.form.get('departure_station_id')
        arr_station_id = request.form.get('arrival_station_id')

        train_data = db.collection('trains').document(train_id).get().to_dict()
        dep_data = db.collection('stations').document(dep_station_id).get().to_dict()
        arr_data = db.collection('stations').document(arr_station_id).get().to_dict()

        new_schedule = {
            'train_id': train_id,
            'train': train_data,
            'departure_station_id': dep_station_id,
            'departure_station': dep_data,
            'arrival_station_id': arr_station_id,
            'arrival_station': arr_data,
            'departure_time': request.form.get('departure_time'),
            'arrival_time': request.form.get('arrival_time'),
            'platform': request.form.get('platform') or '1',
            'status': 'По расписанию',
            'base_price': float(request.form.get('base_price') or 1500),
            'stops': []
        }
        db.collection('schedules').add(new_schedule)
        flash('Новый рейс успешно добавлен в базу!', 'success')
    except Exception as e:
        flash(f'Ошибка добавления: {str(e)}', 'danger')

    return redirect(url_for('main.admin'))

@main_bp.route('/admin/schedule/<schedule_id>/status', methods=['POST'])
def update_status(schedule_id):
    if 'user_id' not in session:
        abort(403)

    db.collection('schedules').document(schedule_id).update({
        'status': request.form.get('status'),
        'platform': request.form.get('platform')
    })
    flash('Данные рейса обновлены.', 'success')
    return redirect(url_for('main.admin'))

@main_bp.route('/admin/schedule/<schedule_id>/delete', methods=['POST'])
def delete_schedule(schedule_id):
    if 'user_id' not in session:
        abort(403)

    db.collection('schedules').document(schedule_id).delete()
    flash('Рейс удален из базы данных.', 'warning')
    return redirect(url_for('main.admin'))
