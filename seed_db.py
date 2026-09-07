from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from app.firebase_db import db

print("Очистка старых данных Firestore...")
for col in ['stations', 'trains', 'schedules', 'users']:
    for doc in db.collection(col).stream():
        doc.reference.delete()

print("1. Загрузка вокзалов и станций...")
stations_data = [
    {"name": "Екатеринбург-Пассажирский", "city": "Екатеринбург", "code": "EKB"},
    {"name": "Москва Казанская", "city": "Москва", "code": "MSK_KAZ"},
    {"name": "Москва Ярославская", "city": "Москва", "code": "MSK_YAR"},
    {"name": "Санкт-Петербург-Главный", "city": "Санкт-Петербург", "code": "SPB"},
    {"name": "Тюмень", "city": "Тюмень", "code": "TYU"},
    {"name": "Пермь-2", "city": "Пермь", "code": "PRM"},
    {"name": "Казань-Пассажирская", "city": "Казань", "code": "KZN"},
    {"name": "Челябинск-Главный", "city": "Челябинск", "code": "CHEL"}
]

stations = {}
for data in stations_data:
    ref = db.collection('stations').add(data)
    stations[data['code']] = {**data, 'id': ref[1].id}

print("2. Загрузка парка поездов...")
trains_data = [
    {"number": "7081", "name": "«Ласточка-Премиум»", "train_type": "Скоростной экспресс («Ласточка»)"},
    {"number": "7085", "name": "«Ласточка»", "train_type": "Скоростной экспресс («Ласточка»)"},
    {"number": "802Е", "name": "«Ласточка-Юг»", "train_type": "Скоростной экспресс («Ласточка»)"},
    {"number": "015Е", "name": "Премиум «Урал»", "train_type": "Скорый фирменный"},
    {"number": "072Е", "name": "«Демидовский экспресс»", "train_type": "Скорый фирменный"},
    {"number": "059Е", "name": "«Тюмень»", "train_type": "Скорый фирменный"},
    {"number": "002Э", "name": "«Россия»", "train_type": "Скорый фирменный"},
    {"number": "136М", "name": "Пассажирский", "train_type": "Пассажирский"},
    {"number": "377Г", "name": "Пассажирский", "train_type": "Пассажирский"},
    {"number": "146У", "name": "Пассажирский", "train_type": "Пассажирский"}
]

trains = {}
for data in trains_data:
    ref = db.collection('trains').add(data)
    trains[data['number']] = {**data, 'id': ref[1].id}

print("3. Формирование насыщенной сетки расписания...")
now = datetime.now()
base_day = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

schedule_list = [
    # --- Екатеринбург -> Тюмень (3 рейса: скоростной, фирменный, пассажирский) ---
    {
        "train": trains["7081"], "dep_st": stations["EKB"], "arr_st": stations["TYU"],
        "dep_time": base_day.replace(hour=6, minute=45), "arr_time": base_day.replace(hour=11, minute=20),
        "platform": "1", "price": 1250.00, "status": "По расписанию",
        "stops": [{"station_name": "Камышлов", "arrival_time": base_day.replace(hour=8, minute=50).isoformat(), "departure_time": base_day.replace(hour=8, minute=55).isoformat(), "stop_duration_minutes": 5}]
    },
    {
        "train": trains["015Е"], "dep_st": stations["EKB"], "arr_st": stations["TYU"],
        "dep_time": base_day.replace(hour=12, minute=15), "arr_time": base_day.replace(hour=17, minute=30),
        "platform": "2", "price": 2100.00, "status": "По расписанию",
        "stops": [{"station_name": "Богданович", "arrival_time": base_day.replace(hour=13, minute=40).isoformat(), "departure_time": base_day.replace(hour=13, minute=45).isoformat(), "stop_duration_minutes": 5}]
    },
    {
        "train": trains["136М"], "dep_st": stations["EKB"], "arr_st": stations["TYU"],
        "dep_time": base_day.replace(hour=19, minute=0), "arr_time": base_day.replace(hour=23, minute=55),
        "platform": "3", "price": 890.00, "status": "По расписанию", "stops": []
    },

    # --- Тюмень -> Екатеринбург (обратное направление) ---
    {
        "train": trains["7085"], "dep_st": stations["TYU"], "arr_st": stations["EKB"],
        "dep_time": base_day.replace(hour=7, minute=10), "arr_time": base_day.replace(hour=11, minute=50),
        "platform": "1", "price": 1250.00, "status": "По расписанию", "stops": []
    },
    {
        "train": trains["059Е"], "dep_st": stations["TYU"], "arr_st": stations["EKB"],
        "dep_time": base_day.replace(hour=14, minute=30), "arr_time": base_day.replace(hour=19, minute=40),
        "platform": "2", "price": 1950.00, "status": "По расписанию", "stops": []
    },
    {
        "train": trains["136М"], "dep_st": stations["TYU"], "arr_st": stations["EKB"],
        "dep_time": base_day.replace(hour=20, minute=15), "arr_time": base_day.replace(hour=23, minute=59) + timedelta(hours=1, minutes=30),
        "platform": "1", "price": 890.00, "status": "По расписанию", "stops": []
    },

    # --- Екатеринбург -> Москва (3 рейса: фирменный, скорый, пассажирский) ---
    {
        "train": trains["015Е"], "dep_st": stations["EKB"], "arr_st": stations["MSK_KAZ"],
        "dep_time": base_day.replace(hour=8, minute=30), "arr_time": base_day.replace(hour=10, minute=0) + timedelta(days=1),
        "platform": "2", "price": 4300.00, "status": "По расписанию",
        "stops": [{"station_name": "Казань-Пассажирская", "arrival_time": (base_day + timedelta(hours=14)).isoformat(), "departure_time": (base_day + timedelta(hours=14, minutes=20)).isoformat(), "stop_duration_minutes": 20}]
    },
    {
        "train": trains["072Е"], "dep_st": stations["EKB"], "arr_st": stations["MSK_YAR"],
        "dep_time": base_day.replace(hour=15, minute=40), "arr_time": base_day.replace(hour=17, minute=50) + timedelta(days=1),
        "platform": "3", "price": 3850.00, "status": "По расписанию",
        "stops": [{"station_name": "Пермь-2", "arrival_time": (base_day + timedelta(hours=5)).isoformat(), "departure_time": (base_day + timedelta(hours=5, minutes=15)).isoformat(), "stop_duration_minutes": 15}]
    },
    {
        "train": trains["136М"], "dep_st": stations["EKB"], "arr_st": stations["MSK_KAZ"],
        "dep_time": base_day.replace(hour=22, minute=10), "arr_time": base_day.replace(hour=4, minute=30) + timedelta(days=2),
        "platform": "1", "price": 2750.00, "status": "Задерживается", "stops": []
    },

    # --- Москва -> Екатеринбург (обратное направление) ---
    {
        "train": trains["015Е"], "dep_st": stations["MSK_KAZ"], "arr_st": stations["EKB"],
        "dep_time": base_day.replace(hour=16, minute=50), "arr_time": base_day.replace(hour=18, minute=40) + timedelta(days=1),
        "platform": "1", "price": 4300.00, "status": "По расписанию", "stops": []
    },
    {
        "train": trains["072Е"], "dep_st": stations["MSK_YAR"], "arr_st": stations["EKB"],
        "dep_time": base_day.replace(hour=20, minute=25), "arr_time": base_day.replace(hour=22, minute=15) + timedelta(days=1),
        "platform": "2", "price": 3850.00, "status": "По расписанию", "stops": []
    },

    # --- Екатеринбург -> Пермь (3 рейса: скоростной, фирменный, пассажирский) ---
    {
        "train": trains["7085"], "dep_st": stations["EKB"], "arr_st": stations["PRM"],
        "dep_time": base_day.replace(hour=7, minute=20), "arr_time": base_day.replace(hour=12, minute=15),
        "platform": "1", "price": 1150.00, "status": "По расписанию",
        "stops": [{"station_name": "Кунгур", "arrival_time": base_day.replace(hour=10, minute=45).isoformat(), "departure_time": base_day.replace(hour=10, minute=50).isoformat(), "stop_duration_minutes": 5}]
    },
    {
        "train": trains["072Е"], "dep_st": stations["EKB"], "arr_st": stations["PRM"],
        "dep_time": base_day.replace(hour=17, minute=45), "arr_time": base_day.replace(hour=23, minute=10),
        "platform": "3", "price": 1780.00, "status": "По расписанию", "stops": []
    },
    {
        "train": trains["377Г"], "dep_st": stations["EKB"], "arr_st": stations["PRM"],
        "dep_time": base_day.replace(hour=23, minute=30), "arr_time": base_day.replace(hour=6, minute=10) + timedelta(days=1),
        "platform": "2", "price": 920.00, "status": "По расписанию", "stops": []
    },

    # --- Пермь -> Екатеринбург (обратное направление) ---
    {
        "train": trains["7085"], "dep_st": stations["PRM"], "arr_st": stations["EKB"],
        "dep_time": base_day.replace(hour=6, minute=40), "arr_time": base_day.replace(hour=11, minute=35),
        "platform": "1", "price": 1150.00, "status": "По расписанию", "stops": []
    },
    {
        "train": trains["072Е"], "dep_st": stations["PRM"], "arr_st": stations["EKB"],
        "dep_time": base_day.replace(hour=15, minute=30), "arr_time": base_day.replace(hour=21, minute=5),
        "platform": "2", "price": 1780.00, "status": "По расписанию", "stops": []
    },

    # --- Екатеринбург -> Челябинск (3 рейса: скоростной утренний, вечерний и пассажирский) ---
    {
        "train": trains["802Е"], "dep_st": stations["EKB"], "arr_st": stations["CHEL"],
        "dep_time": base_day.replace(hour=8, minute=10), "arr_time": base_day.replace(hour=11, minute=40),
        "platform": "1", "price": 880.00, "status": "По расписанию", "stops": []
    },
    {
        "train": trains["802Е"], "dep_st": stations["EKB"], "arr_st": stations["CHEL"],
        "dep_time": base_day.replace(hour=18, minute=30), "arr_time": base_day.replace(hour=22, minute=5),
        "platform": "2", "price": 880.00, "status": "По расписанию", "stops": []
    },
    {
        "train": trains["146У"], "dep_st": stations["EKB"], "arr_st": stations["CHEL"],
        "dep_time": base_day.replace(hour=13, minute=15), "arr_time": base_day.replace(hour=18, minute=5),
        "platform": "4", "price": 640.00, "status": "По расписанию", "stops": []
    },

    # --- Челябинск -> Екатеринбург ---
    {
        "train": trains["802Е"], "dep_st": stations["CHEL"], "arr_st": stations["EKB"],
        "dep_time": base_day.replace(hour=7, minute=0), "arr_time": base_day.replace(hour=10, minute=35),
        "platform": "1", "price": 880.00, "status": "По расписанию", "stops": []
    },
    {
        "train": trains["146У"], "dep_st": stations["CHEL"], "arr_st": stations["EKB"],
        "dep_time": base_day.replace(hour=19, minute=20), "arr_time": base_day.replace(hour=23, minute=55),
        "platform": "3", "price": 640.00, "status": "По расписанию", "stops": []
    },

    # --- Екатеринбург -> Санкт-Петербург ---
    {
        "train": trains["072Е"], "dep_st": stations["EKB"], "arr_st": stations["SPB"],
        "dep_time": base_day.replace(hour=14, minute=20), "arr_time": base_day.replace(hour=21, minute=15) + timedelta(days=1),
        "platform": "3", "price": 4950.00, "status": "По расписанию", "stops": []
    },
    {
        "train": trains["146У"], "dep_st": stations["EKB"], "arr_st": stations["SPB"],
        "dep_time": base_day.replace(hour=21, minute=40), "arr_time": base_day.replace(hour=7, minute=10) + timedelta(days=2),
        "platform": "2", "price": 3450.00, "status": "По расписанию", "stops": []
    },

    # --- Екатеринбург -> Казань ---
    {
        "train": trains["015Е"], "dep_st": stations["EKB"], "arr_st": stations["KZN"],
        "dep_time": base_day.replace(hour=9, minute=15), "arr_time": base_day.replace(hour=22, minute=50),
        "platform": "1", "price": 2850.00, "status": "По расписанию", "stops": []
    },
    {
        "train": trains["377Г"], "dep_st": stations["EKB"], "arr_st": stations["KZN"],
        "dep_time": base_day.replace(hour=16, minute=45), "arr_time": base_day.replace(hour=8, minute=25) + timedelta(days=1),
        "platform": "3", "price": 1720.00, "status": "По расписанию", "stops": []
    }
]

for s in schedule_list:
    db.collection('schedules').add({
        "train_id": s["train"]["id"],
        "train": s["train"],
        "departure_station_id": s["dep_st"]["id"],
        "departure_station": s["dep_st"],
        "arrival_station_id": s["arr_st"]["id"],
        "arrival_station": s["arr_st"],
        "departure_time": s["dep_time"].isoformat(),
        "arrival_time": s["arr_time"].isoformat(),
        "platform": s["platform"],
        "status": s["status"],
        "base_price": s["price"],
        "stops": s["stops"]
    })

print("4. Создание учетной записи администратора...")
db.collection('users').add({
    "username": "admin",
    "password_hash": generate_password_hash("admin123"),
    "role": "admin"
})

print("УСПЕХ: Вся база пересобрана! Добавлено 23 регулярных рейса по всем ключевым направлениям.")
