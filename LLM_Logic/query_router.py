from .query_handler import QueryHandler
from .smart_query_handler import SmartQueryHandler

# Handler pintar untuk query device dan registration
smart_handler = SmartQueryHandler(base_url="http://36.92.47.218:14523")

# Handler untuk registration data (fallback untuk query kompleks)
registration_handler = QueryHandler(
    api_url="http://36.92.47.218:14523/registration/all",
    keyword_filters={
        "payload_id_2": {
            "GPS": ["gps", "lokasi", "location"],
            "Beacon": ["beacon"],
            "Heartbeat": ["heartbeat", "status"]
        }
    },
    field_filters={
        "persentase_baterai": ["> 20", "<= 50", ">= 80"]
    }
)

# Handler untuk solar tracker
solar_handler = QueryHandler(
    api_url="http://36.92.47.218:14523/solar-tracker/data",
    keyword_filters={
        "g_sensor_status": {
            0: ["static", "diam", "tidak bergerak"],
            1: ["vibrate", "bergetar", "bergerak"]
        }
    },
    field_filters={
        "speed_kmh": ["> 0", "<= 50", ">= 10"],
        "persentase_baterai": ["> 20", "<= 50"]
    }
)

async def handle_query(user_input: str):
    """
    Router untuk menentukan handler mana yang digunakan
    berdasarkan keyword dalam input user
    
    Priority:
    1. SmartQueryHandler - untuk query device, IMEI, count, list
    2. SolarHandler - untuk query solar tracker
    3. RegistrationHandler - untuk query registration dengan filter kompleks
    4. None - diteruskan ke AI
    """
    text = user_input.lower()
    
    print(f"[QueryRouter] Processing query: {user_input}")
    
    # Priority 1: Coba SmartQueryHandler untuk query device/IMEI/count
    if any(kw in text for kw in ["device", "perangkat", "imei", "serial", "berapa", "jumlah", "total", "cari", "tampilkan", "lihat", "daftar", "list"]):
        result = await smart_handler.handle(user_input)
        if result is not None:
            print(f"[QueryRouter] SmartQueryHandler handled the query")
            return result
    
    # Priority 2: Solar tracker queries
    if any(kw in text for kw in ["solar", "tracker solar", "panel"]):
        print(f"[QueryRouter] Using SolarHandler")
        return await solar_handler.handle(user_input)
    
    # Priority 3: Registration queries dengan filter kompleks
    if any(kw in text for kw in ["registration", "gps", "beacon", "heartbeat"]) and any(op in text for op in [">", "<", ">=", "<=", "="]):
        print(f"[QueryRouter] Using RegistrationHandler")
        return await registration_handler.handle(user_input)
    
    # Jika tidak match, return None (akan diteruskan ke AI)
    print(f"[QueryRouter] No handler matched, forwarding to AI")
    return None