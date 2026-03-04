from fastapi import FastAPI, HTTPException, Form
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
import db_connection as db
import requests
from LLM_Logic.load_ai import ask_ai
from LLM_Logic.query_router import handle_query

app = FastAPI(title="Device Registration API")

GOOGLE_MAPS_API_KEY = "AIzaSyAdidNhffYHTMN60gs6oiXcqpyrmE8vpf0"  # Ganti dengan API key Anda

class Device(BaseModel):
    imei: str
    serial_number: str

class ChatMessage(BaseModel):
    message: str
    timestamp: str

_device_cache = {}
_last_cache_update = None
_cache_duration = timedelta(minutes=5)

def get_cached_devices():
    global _device_cache, _last_cache_update
    now = datetime.now()
    
    if _last_cache_update is None or (now - _last_cache_update) > _cache_duration:
        devices = db.get_all_devices()
        _device_cache = {device['imei']: device['serial_number'] for device in devices}
        _last_cache_update = now
    
    return _device_cache

@app.post("/ask")
async def ask(message: ChatMessage):
    """
    Endpoint chatbot yang menggabungkan query handler dan AI
    """
    user_input = message.message
    
    print(f"[API /ask] Received message: {user_input}")
    
    # Coba handle dengan query handler dulu
    query_response = await handle_query(user_input)
    
    if query_response is not None:
        print(f"[API /ask] Query handler returned: {type(query_response)}")
        
        # Jika ada hasil dari query handler, format response
        if isinstance(query_response, int):
            # Response adalah angka (device count)
            return {"response": f"Total device: {query_response}"}
        
        elif isinstance(query_response, dict) and 'breakdown' in query_response:
            # Format untuk device count dengan breakdown
            total = query_response.get('total', 0)
            ble = query_response.get('ble', 0)
            solar = query_response.get('solar', 0)
            
            response_text = f"Total device: {total}\n"
            response_text += f"- Device BLE: {ble}\n"
            response_text += f"- Device Solar Tracker: {solar}"
            
            return {"response": response_text}
        
        elif isinstance(query_response, dict) and 'absolute_latest' in query_response:
            # Format untuk single device dengan absolute latest + per category
            summary = f"IMEI: {query_response.get('imei')}\n"
            summary += f"Serial: {query_response.get('serial_number', 'N/A')}\n"
            
            if query_response.get('last_activity'):
                summary += f"Activity: {query_response.get('last_activity')}\n"
            
            summary += "\n=== DATA TERBARU (OVERALL) ===\n"
            abs_latest = query_response['absolute_latest']
            summary += f"Type: {abs_latest['type']}\n"
            summary += f"Timestamp: {abs_latest['timestamp']}\n"
            
            # Show relevant fields from absolute latest
            data = abs_latest['data']
            if data.get('alarm'):
                summary += f"Alarm: {data.get('alarm')}\n"
            if data.get('latitude') and data.get('longitude'):
                summary += f"Location: ({data.get('latitude')}, {data.get('longitude')})\n"
            if data.get('persentase_baterai') is not None:
                summary += f"Battery: {data.get('persentase_baterai')}%\n"
            if data.get('voltage'):
                summary += f"Voltage: {data.get('voltage')}V\n"
            
            # Show per-category latest data
            if query_response.get('latest_per_category'):
                summary += "\n=== DATA TERBARU PER KATEGORI ===\n"
                
                for category, cat_data in query_response['latest_per_category'].items():
                    summary += f"\n{category}:\n"
                    summary += f"  Timestamp: {cat_data.get('timestamp')}\n"
                    
                    if category == 'GPS':
                        if cat_data.get('latitude') and cat_data.get('longitude'):
                            summary += f"  Location: ({cat_data.get('latitude')}, {cat_data.get('longitude')})\n"
                    
                    elif category == 'Heartbeat':
                        if cat_data.get('persentase_baterai') is not None:
                            summary += f"  Battery: {cat_data.get('persentase_baterai')}%\n"
                        if cat_data.get('voltage'):
                            summary += f"  Voltage: {cat_data.get('voltage')}V\n"
                    
                    elif category == 'Beacon':
                        if cat_data.get('parsed_data'):
                            summary += f"  Data: {cat_data.get('parsed_data')}\n"
                    
                    elif category == 'Alarm':
                        if cat_data.get('alarm'):
                            summary += f"  Alarm: {cat_data.get('alarm')}\n"
                    
                    elif category == 'Solar':
                        if cat_data.get('persentase_baterai') is not None:
                            summary += f"  Battery: {cat_data.get('persentase_baterai')}%\n"
                        if cat_data.get('speed_kmh') is not None:
                            summary += f"  Speed: {cat_data.get('speed_kmh')} km/h\n"
                        if cat_data.get('g_sensor_status') is not None:
                            status = "Vibrate" if cat_data.get('g_sensor_status') == 1 else "Static"
                            summary += f"  G-Sensor: {status}\n"
            
            return {"response": summary.strip()}
        
        elif isinstance(query_response, list):
            # Format list data menjadi text yang readable
            if len(query_response) == 0:
                return {"response": "Tidak ada data yang ditemukan."}
            
            # Tampilkan SEMUA data tanpa batasan
            summary = f"Ditemukan {len(query_response)} data:\n\n"
            for i, item in enumerate(query_response, 1):
                summary += f"{i}. {format_item(item)}\n"
            
            return {"response": summary}
        
        elif isinstance(query_response, dict) and 'grouped' in query_response:
            summary = f"Ditemukan {query_response.get('total', 0)} data:\n\n"
            
            for group_name, items in query_response.get('groups', {}).items():
                if items:
                    summary += f"=== {group_name} ===\n"
                    for i, item in enumerate(items, 1):
                        summary += f"{i}. {format_item(item)}\n"
                    summary += "\n"

            return {"response": summary.strip()}  # <-- multiline aman

        
        elif isinstance(query_response, str):
            return {"response": query_response}
        
        else:
            return {"response": str(query_response)}
    
    print(f"[API /ask] Forwarding to AI")
    response = ask_ai(user_input)
    return {"response": response}

def format_item(item: dict) -> str:
    """Format dictionary menjadi output multiline yang rapi"""

    # Helper untuk rapikan key:value
    def multiline_output(data: dict):
        lines = []
        for key, value in data.items():
            if value is not None:
                key_clean = key.replace("_", " ").lower()
                lines.append(f"  {key_clean}: {value}")
        return "\n" + "\n".join(lines)

    # ==========================
    # FORMAT DEVICE BLE & SOLAR
    # ==========================
    if 'imei' in item and 'device_type' in item:
        data = {
            "imei": item.get("imei"),
            "serial": item.get("serial_number", "N/A"),
            "activity": item.get("last_activity"),
            "location": f"({item.get('latitude')}, {item.get('longitude')})"
                if item.get('latitude') and item.get('longitude') else None,
            "battery": f"{item.get('battery')}%" if item.get('battery') is not None else None,
            "voltage": f"{item.get('voltage')}V" if item.get('voltage') else None,
            "speed": f"{item.get('speed_kmh')} km/h" if item.get('speed_kmh') is not None else None,
            "g sensor": "Vibrate" if item.get('g_sensor_status') == 1
                else "Static" if item.get('g_sensor_status') is not None else None,
            "last update": item.get('timestamp')
                or item.get('gps_timestamp')
                or item.get('heartbeat_timestamp')
        }

        return multiline_output(data)

    # ==========================
    # FORMAT FALLBACK DEVICE SIMPLE
    # ==========================
    elif 'imei' in item:
        data = {
            "imei": item.get("imei"),
            "serial": item.get("serial_number", "N/A")
        }
        return multiline_output(data)

    # ==========================
    # FORMAT DATA REGISTRASI
    # ==========================
    elif 'payload_id_1' in item:
        data = {
            "imei": item.get("payload_id_1"),
            "type": item.get("payload_id_2", "N/A"),
            "time": item.get("timestamp", "N/A"),
            "battery": f"{item.get('persentase_baterai')}%" if item.get("persentase_baterai") else None,
            "location": f"({item.get('latitude')}, {item.get('longitude')})"
                if item.get('latitude') and item.get('longitude') else None
        }
        return multiline_output(data)

    # ==========================
    # FORMAT GENERIC (5 ITEM SAJA)
    # ==========================
    else:
        trimmed = {}
        count = 0
        for k, v in item.items():
            if v is not None and v != "":
                trimmed[k] = v
                count += 1
            if count >= 5:
                break

        return multiline_output(trimmed)


@app.get("/device-info/{imei}")
async def get_device_info(imei: str):
    """Get device serial number from cache"""
    devices = get_cached_devices()
    return {"serial_number": devices.get(imei)}

@app.get("/registration/all")
async def get_all_registrations():
    data = db.get_all_registration_data()
    if data is None:
        raise HTTPException(status_code=500, detail="Failed to fetch registration data")
    return {"data": data}

@app.get("/devices")
async def get_devices():
    devices = db.get_all_devices()
    return {"devices": devices, "total": len(devices)}

@app.post("/devices")
async def add_device(device: Device):
    success = db.insert_device_data(device.imei, device.serial_number)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to insert device")
    return {"message": "Device added successfully"}

@app.get("/devices/count")
async def get_devices_count():
    count = db.get_device_count()
    return {"total_devices": count}

@app.get("/registration/{imei}")
async def get_registration_by_imei(imei: str):
    data = db.get_registration_data_by_imei(imei)
    if data is None:
        raise HTTPException(status_code=404, detail="Data not found")
    
    processed_data = []
    for row in data:
        if row['payload_id_2'] == 'Beacon':
            major, minor = db.parse_beacon_data(row['parsed_data'])
            row['major'] = major
            row['minor'] = minor
        processed_data.append(row)
    
    return {"data": processed_data}

@app.post("/registration/{imei}/date-range")
async def get_registration_by_date_range(
    imei: str,
    start_date: str = Form(...),
    end_date: str = Form(...)
):
    """
    Get registration data by IMEI and date range using form data
    Date format: YYYY-MM-DD HH:MM:SS or YYYY-MM-DDTHH:MM:SS
    """
    try:
        # Parse date strings to datetime objects
        # Support both formats: "YYYY-MM-DD HH:MM:SS" and "YYYY-MM-DDTHH:MM:SS"
        start_dt = datetime.strptime(start_date.replace('T', ' '), '%Y-%m-%d %H:%M:%S')
        end_dt = datetime.strptime(end_date.replace('T', ' '), '%Y-%m-%d %H:%M:%S')
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format. Use 'YYYY-MM-DD HH:MM:SS' or 'YYYY-MM-DDTHH:MM:SS'. Error: {str(e)}"
        )
    
    # Validasi tanggal
    if end_dt < start_dt:
        raise HTTPException(
            status_code=400,
            detail="Invalid date range: end_date cannot be earlier than start_date"
        )
    
    data = db.get_registration_data_by_date_range(imei, start_dt, end_dt)
    if data is None:
        raise HTTPException(status_code=404, detail="Data not found")
    
    return {
        "data": data,
        "meta": {
            "start_date": start_dt.strftime('%Y-%m-%d %H:%M:%S'),
            "end_date": end_dt.strftime('%Y-%m-%d %H:%M:%S'),
            "total_records": len(data) if data else 0
        }
    }

@app.get("/registration/{imei}/gps")
async def get_gps_data_range(
    imei: str,
    start_date: datetime,
    end_date: datetime
):
    if end_date < start_date:
        raise HTTPException(
            status_code=400, 
            detail="Invalid date range: end_date cannot be earlier than start_date"
        )
    
    data = db.get_gps_data_by_date_range(imei, start_date, end_date)
    if data is None:
        raise HTTPException(status_code=404, detail="GPS data not found")
    return {
        "data": data,
        "meta": {
            "start_date": start_date.strftime('%Y-%m-%d %H:%M:%S'),
            "end_date": end_date.strftime('%Y-%m-%d %H:%M:%S'),
            "total_records": len(data) if data else 0
        }
    }

@app.get("/registration/{imei}/non-gps")
async def get_non_gps_data_range(
    imei: str,
    start_date: datetime,
    end_date: datetime
):
    if end_date < start_date:
        raise HTTPException(
            status_code=400, 
            detail="Invalid date range: end_date cannot be earlier than start_date"
        )
    
    data = db.get_non_gps_data_by_date_range(imei, start_date, end_date)
    if data is None:
        raise HTTPException(status_code=404, detail="Non-GPS data not found")
    return {
        "data": data,
        "meta": {
            "start_date": start_date.strftime('%Y-%m-%d %H:%M:%S'),
            "end_date": end_date.strftime('%Y-%m-%d %H:%M:%S'),
            "total_records": len(data) if data else 0
        }
    }

@app.get("/gps/{imei}/latest")
async def get_latest_gps(imei: str):
    data = db.get_latest_gps_data(imei)
    if data is None:
        raise HTTPException(status_code=404, detail="GPS data not found")
    return {"data": data}

@app.get("/heartbeat/{imei}/latest")
async def get_latest_heartbeat(imei: str):
    data = db.get_latest_heartbeat(imei)
    if data is None:
        raise HTTPException(status_code=404, detail="Heartbeat data not found")
    return {
        "data": data,
        "meta": {
            "timestamp": data.get('timestamp'),
            "voltage": data.get('voltage'),
            "battery_percentage": data.get('persentase_baterai')
        }
    }

@app.get("/service-tanto")
async def get_service_tanto():
    """Get all service tanto data"""
    data = db.get_service_tanto_data()
    if data is None:
        raise HTTPException(status_code=500, detail="Failed to fetch service tanto data")
    return {
        "data": data,
        "total": len(data),
        "fields": {
            "id": "Record ID",
            "id_container": "Container ID",
            "last_activity": "Last Activity",
            "date": "Date",
            "created_time": "Created Time"
        },
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

@app.get("/devices-with-activity")
async def get_devices_with_activity():
    """Get all devices with their latest container activity"""
    devices = db.get_all_devices_with_activity()
    return {
        "devices": devices,
        "total": len(devices),
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

@app.get("/device-activity/{imei}")
async def get_device_activity(imei: str):
    """Get activity for a single device"""
    device = db.get_device_by_imei(imei)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    
    activity = db.get_container_activity(device['serial_number'])
    return {
        "imei": imei,
        "serial_number": device['serial_number'],
        "last_activity": activity or "No Activity"
    }

@app.get("/all-device-activities")
async def get_all_device_activities():
    """Get activities for all devices"""
    data = db.get_all_devices_activities()
    return {
        "devices": data,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

@app.post("/api/geofence")
async def create_geofence(geofence: dict):
    """Create a new geofence area"""
    try:
        success = db.save_geofence(
            name=geofence['name'],
            coordinates=geofence['coordinates'],
            description=geofence.get('description')
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save geofence")
        
        return {"message": "Geofence saved successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving geofence: {str(e)}")

@app.get("/api/geofence")
async def get_geofences():
    data = db.get_all_geofences()
    if data is None:
        raise HTTPException(status_code=500, detail="Failed to fetch geofences")
    return data

@app.get("/reverse-geocode")
async def get_address(lat: float, lng: float):
    """Get location name (geofence or street address) for coordinates"""
    try:
        # First check if point is in any geofence
        geofence_name = db.check_point_in_geofence(lat, lng)
        if (geofence_name):
            return {
                "street_name": geofence_name,
                "full_address": f"Inside {geofence_name} Area"
            }
        
        # If not in geofence, get street address from Google Maps
        url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={GOOGLE_MAPS_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if data["status"] == "OK":
            address_components = data["results"][0]["address_components"]
            street_name = None
            city = None
            
            # Extract street name and city
            for component in address_components:
                if "route" in component["types"]:
                    street_name = component["long_name"]
                if "administrative_area_level_2" in component["types"]:
                    city = component["long_name"]
            
            # If no specific street found, use formatted address
            if not street_name:
                street_name = data["results"][0]["formatted_address"].split(',')[0]
            
            location_text = f"{street_name}"
            if city:
                location_text += f", {city}"
            
            return {
                "street_name": location_text,
                "full_address": data["results"][0]["formatted_address"]
            }
        else:
            return {"error": "No results found"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Geocoding error: {str(e)}")

@app.get("/beacon/registration")
async def get_beacon_registrations(
    imei: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get beacon registration data with optional IMEI and date filters"""
    try:
        data = db.get_beacon_registration_data(imei, start_date, end_date)
        if data is None:
            raise HTTPException(status_code=500, detail="Failed to fetch beacon registration data")
        
        processed_data = []
        for row in data:
            major, minor = db.parse_beacon_data(row['parsed_data'])
            row['major'] = major
            row['minor'] = minor
            processed_data.append(row)
        
        return {
            "status": "success",
            "data": processed_data,
            "count": len(processed_data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/beacon/locations")
async def get_beacon_locations():
    """Get all beacon location data"""
    try:
        data = db.get_all_beacon_locations()
        if data is None:
            raise HTTPException(status_code=500, detail="Failed to fetch beacon locations")
        
        return {
            "status": "success",
            "data": data,
            "count": len(data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/beacon/location/{major}/{minor}")
async def get_beacon_location_by_id(
    major: str,
    minor: str
):
    """Get beacon location by major and minor IDs"""
    try:
        data = db.get_beacon_location_by_id(major, minor)
        if data is None:
            return {
                "status": "error",
                "message": "Beacon location not found"
            }
        
        return {
            "status": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/solar-tracker/devices")
async def get_solar_tracker_devices_list():
    """Get all devices from the solar tracker system."""
    devices = db.get_solar_tracker_devices()
    if devices is None:
        raise HTTPException(status_code=500, detail="Failed to fetch solar tracker devices")
    return {"devices": devices, "total": len(devices)}


@app.get("/solar-tracker/data")
async def get_solar_tracker_data_api(
    imei: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """
    Get combined solar tracker data with optional filters for IMEI and date range.
    Date format: YYYY-MM-DDTHH:MM:SS (e.g., 2023-01-01T00:00:00)
    """
    if start_date and not end_date:
        # Set end_date ke waktu sekarang jika hanya start_date yang diberikan
        end_date = datetime.now()

    data = db.get_solar_tracker_data(imei=imei, start_date=start_date, end_date=end_date)
    
    if data is None:
        raise HTTPException(status_code=500, detail="Failed to fetch solar tracker data")
    
    return {"data": data, "count": len(data)}

@app.get("/solar-tracker/{imei}/latest-gps")
async def get_solar_tracker_latest_gps(imei: str):
    """Get latest GPS data from solar tracker device by IMEI."""
    data = db.get_solar_tracker_latest_gps(imei)
    if data is None:
        raise HTTPException(status_code=404, detail=f"No GPS data found for solar tracker IMEI: {imei}")
    
    return {
        "imei": imei,
        "data": data,
        "timestamp": data.get('timestamp')
    }

@app.get("/solar-tracker/{imei}/latest")
async def get_solar_tracker_latest_data(imei: str):
    """Get latest data from solar tracker device by IMEI (all data types)."""
    data = db.get_solar_tracker_latest_data(imei)
    if data is None:
        raise HTTPException(status_code=404, detail=f"No data found for solar tracker IMEI: {imei}")
    
    return {
        "imei": imei,
        "data": data,
        "timestamp": data.get('timestamp')
    }

@app.get("/solar-tracker/{imei}")
async def get_solar_tracker_all_data_by_imei(imei: str):
    """Get all data from solar tracker device by IMEI."""
    data = db.get_solar_tracker_data(imei=imei)
    if data is None:
        raise HTTPException(status_code=500, detail="Failed to fetch solar tracker data")
    
    if not data:
        raise HTTPException(status_code=404, detail=f"No data found for solar tracker IMEI: {imei}")
    
    return {
        "imei": imei,
        "data": data,
        "count": len(data)
    }

@app.post("/devices/create")
async def create_device_from_form(
    device_type: str = Form(...),
    imei: str = Form(...),
    serial_number: Optional[str] = Form(None)
):
    """Creates a device from the web form submission."""
    if device_type == 'solar':
        success, message = db.insert_solar_device(imei)
        if not success:
            raise HTTPException(status_code=409 if "exists" in message else 500, detail=message)
        return {"status": "success", "message": message}

    elif device_type == 'tracker':
        if not serial_number:
            raise HTTPException(status_code=400, detail="Serial Number is required for a tracker device.")
        success = db.insert_device_data(imei, serial_number)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to insert tracker device.")
        return {"status": "success", "message": f"Tracker Device {imei} added successfully."}
    
    raise HTTPException(status_code=400, detail="Invalid device type specified.")

@app.delete("/api/geofence/{geofence_id}")
async def delete_geofence(geofence_id: int):
    """Delete a geofence by its ID."""
    success = db.delete_geofence(geofence_id)
    if not success:
        raise HTTPException(
            status_code=404, 
            detail=f"Failed to delete geofence with ID {geofence_id}. It may not exist."
        )
    return {"message": "Geofence deleted successfully."}