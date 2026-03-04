from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from typing import Optional
import db_connection as db
from math import ceil
import api
from datetime import datetime, timedelta
import os
import pandas as pd
import requests
from io import BytesIO

GOOGLE_MAPS_API_KEY = api.GOOGLE_MAPS_API_KEY

def reverse_geocode(lat, lng, cache: dict) -> str:
    """Convert lat/lng to street name using Google Maps API with cache."""
    # Round to 4 decimal places for cache key (~11m accuracy)
    cache_key = (round(lat, 4), round(lng, 4))
    if cache_key in cache:
        return cache[cache_key]
    
    try:
        # Check geofence first
        geofence_name = db.check_point_in_geofence(lat, lng)
        if geofence_name:
            cache[cache_key] = geofence_name
            return geofence_name
        
        url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={GOOGLE_MAPS_API_KEY}"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if data.get("status") == "OK":
            address_components = data["results"][0]["address_components"]
            street_name = None
            city = None
            
            for component in address_components:
                if "route" in component["types"]:
                    street_name = component["long_name"]
                if "administrative_area_level_2" in component["types"]:
                    city = component["long_name"]
            
            if not street_name:
                street_name = data["results"][0]["formatted_address"].split(',')[0]
            
            location_text = street_name
            if city:
                location_text += f", {city}"
            
            cache[cache_key] = location_text
            return location_text
    except Exception as e:
        print(f"Reverse geocode error for ({lat}, {lng}): {e}")
    
    cache[cache_key] = f"({lat}, {lng})"
    return f"({lat}, {lng})"

app = api.app


# Ensure static directory exists
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# Create a basic favicon if it doesn't exist
favicon_path = os.path.join(static_dir, "favicon.ico")
if not os.path.exists(favicon_path):
    # Create minimal 16x16 favicon
    from PIL import Image
    img = Image.new('RGB', (16, 16), color='blue')
    img.save(favicon_path, 'ICO')

# Mount static files with proper configuration
app.mount("/static", StaticFiles(directory=static_dir), name="static")

templates = Jinja2Templates(directory="templates")
templates.env.globals.update(min=min)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Redirect root to dashboard"""
    return templates.TemplateResponse("redirect.html", {
        "request": request,
        "url": "/dashboard"
    })

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request, 
    page: int = 1,
    imei: str = None,
    start_date: str = None,
    end_date: str = None
):
    devices = db.get_all_devices()
    device_status = None
    data = None

    # Get default last update data
    default_device_data = []
    if not imei and not start_date and not end_date:
        for device in devices:
            device_imei = device['imei']
            last_data = db.get_latest_data_by_imei(device_imei)
            if last_data:
                default_device_data.append(last_data)
        data = default_device_data
    else:
        # Handle filtered data
        if imei:
            # Get device status if specific device selected
            last_data = db.get_latest_data_by_imei(imei)
            heartbeat = db.get_latest_heartbeat(imei)
            
            if last_data and heartbeat:
                device_status = {
                    'voltage': heartbeat.get('voltage'),
                    'persentase_baterai': heartbeat.get('persentase_baterai'),
                    'timestamp': last_data.get('timestamp'),
                    'is_online': (datetime.now() - datetime.strptime(last_data['timestamp'], '%Y-%m-%d %H:%M:%S')).total_seconds() < 86400  # 24 hours
                }
            
            # Get filtered data by date range if specified
            if start_date and end_date:
                try:
                    start_dt = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
                    end_dt = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')
                    data = db.get_registration_data_by_date_range(imei, start_dt, end_dt)
                except ValueError:
                    data = db.get_registration_data_by_imei(imei)
            else:
                data = db.get_registration_data_by_imei(imei)
        else:
            # Get all data with optional date filter
            if start_date and end_date:
                try:
                    start_dt = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
                    end_dt = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')
                    data = db.get_all_registration_data_by_date_range(start_dt, end_dt)
                except ValueError:
                    data = db.get_all_registration_data()
            else:
                data = db.get_all_registration_data()

    if data:
        # Pagination logic
        ITEMS_PER_PAGE = 10
        total_items = len(data)
        total_pages = ceil(total_items / ITEMS_PER_PAGE)
        start_idx = (page - 1) * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        current_data = data[start_idx:end_idx]
        
        # Process beacon data for each row
        for item in current_data:
            if item['payload_id_2'] == 'Beacon':
                try:
                    # Parse beacon data to get major/minor
                    major, minor = db.parse_beacon_data(item['parsed_data'])
                    if major and minor:
                        # Get beacon location data
                        location = db.get_beacon_location_by_id(major, minor)
                        if location:
                            item['location_name'] = location['location_name']
                            item['beacon_name'] = location['beacon_name']
                        item['major'] = major
                        item['minor'] = minor
                except Exception as e:
                    print(f"Error processing beacon data: {str(e)}")
        
        return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "data": current_data,
            "page": page,
            "total_pages": total_pages,
            "total_items": total_items,
            "devices": devices,
            "selected_imei": imei or "",
            "start_date": start_date or "",
            "end_date": end_date or "",
            "now": datetime.now().strftime('%Y-%m-%dT%H:%M'),
            "device_status": device_status,
            "device_type": "tracker"  # Add this line to identify regular tracker
        }
    )
    
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "message": "No data found"
        }
    )

# In main.py, replace the existing solar_dashboard function

@app.get("/solar-dashboard", response_class=HTMLResponse)
async def solar_dashboard(
    request: Request,
    page: int = 1,
    imei: str = None,
    start_date: str = None,
    end_date: str = None
):
    devices = db.get_solar_tracker_devices()
    device_status = None
    data = []
    message = None

    # This logic is now cleaner and handles all cases
    if imei:
        # --- LOGIC FOR A SINGLE FILTERED DEVICE ---
        data = db.get_solar_tracker_data(imei=imei, start_date=start_date, end_date=end_date)
        if not data:
            # If a device is selected but has no data, set a specific message
            message = f"No data available for device {imei}."
        
        # Get the status card info from the latest data point, if it exists
        last_data_point = db.get_solar_tracker_data(imei=imei, limit=1)
        if last_data_point:
            first_record = last_data_point[0]
            timestamp = first_record.get('timestamp')
            is_online = False
            if timestamp and isinstance(timestamp, str) and timestamp != 'No data yet':
                try:
                    is_online = (datetime.now() - datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')).total_seconds() < 86400
                except ValueError:
                    is_online = False
            
            device_status = {
                'voltage': first_record.get('voltage'),
                'persentase_baterai': first_record.get('persentase_baterai'),
                'timestamp': timestamp,
                'is_online': is_online
            }

    else:
        # --- LOGIC FOR "ALL DEVICES" VIEW ---
        all_devices_data = []
        source_data = db.get_solar_tracker_data(start_date=start_date, end_date=end_date) if (start_date and end_date) else db.get_solar_tracker_data()
        
        # Create a dictionary of data found
        data_map = {item['payload_id_1']: item for item in source_data}

        for device in devices:
            device_imei = device['imei']
            if device_imei in data_map:
                all_devices_data.append(data_map[device_imei])
            else:
                # If a device has no data, create a placeholder
                all_devices_data.append({
                    'payload_id_1': device_imei, 'timestamp': 'No data yet',
                    'latitude': None, 'longitude': None, 'persentase_baterai': None,
                    'g_sensor_status': None, 'speed_kmh': None, 'alarm': None
                })
        data = all_devices_data

    # --- PAGINATION & DISPLAY LOGIC ---
    total_items = len(data) if data else 0
    ITEMS_PER_PAGE = 10
    total_pages = ceil(total_items / ITEMS_PER_PAGE)
    start_idx = (page - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    current_data = data[start_idx:end_idx] if data else []

    for item in current_data:
        g_status = item.get('g_sensor_status')
        item['g_sensor_display'] = "Vibrate" if g_status == 1 else "Static" if g_status == 0 else "-"

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "data": current_data,
            "page": page,
            "total_pages": total_pages,
            "total_items": total_items,
            "devices": devices,
            "selected_imei": imei or "",
            "start_date": start_date or "",
            "end_date": end_date or "",
            "now": datetime.now().strftime('%Y-%m-%dT%H:%M'),
            "device_status": device_status,
            "device_type": "solar",
            "message": message  # Pass the message to the template
        }
    )

@app.get("/insert", response_class=HTMLResponse)
async def insert_page(request: Request):
    """Render insert device page"""
    return templates.TemplateResponse("insert.html", {
        "request": request,
        "message": None
    })

@app.post("/insert", response_class=HTMLResponse)
async def insert_device(
    request: Request,
    device_type: str = Form(...),
    imei: str = Form(...),
    serial_number: Optional[str] = Form(None)
):
    """Handle device insertion for both tracker and solar tracker types."""

    if device_type == 'solar':
        success, message = db.insert_solar_device(imei)
        
        if success:
            return RedirectResponse(url="/solar-dashboard", status_code=303)
        else:
            return templates.TemplateResponse("insert.html", {
                "request": request,
                "message": message
            })

    elif device_type == 'tracker':
        if not serial_number:
            return templates.TemplateResponse("insert.html", {
                "request": request,
                "message": "Serial Number is required for a Tracker Device."
            })
            
        success = db.insert_device_data(imei, serial_number)
        
        if success:
            return RedirectResponse(url="/dashboard", status_code=303)
        else:
            message = f"Failed to insert Tracker Device. The IMEI '{imei}' may already exist."
            return templates.TemplateResponse("insert.html", {
                "request": request,
                "message": message
            })
    
    return templates.TemplateResponse("insert.html", {
        "request": request,
        "message": "Invalid device type selected. Please try again."
    })

@app.get("/export-excel")
async def export_excel(
    imei: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Export table data to Excel"""
    try:
        # Get data based on filters
        if imei:
            if start_date and end_date:
                try:
                    start_dt = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
                    end_dt = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')
                    data = db.get_registration_data_by_date_range(imei, start_dt, end_dt)
                except ValueError:
                    data = db.get_registration_data_by_imei(imei)
            else:
                data = db.get_registration_data_by_imei(imei)
        else:
            if start_date and end_date:
                try:
                    start_dt = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
                    end_dt = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')
                    data = db.get_all_registration_data_by_date_range(start_dt, end_dt)
                except ValueError:
                    data = db.get_all_registration_data()
            else:
                data = db.get_all_registration_data()

        if not data:
            raise HTTPException(status_code=404, detail="No data found to export")

        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Get device info and activities
        devices_info = {device['imei']: device['serial_number'] for device in db.get_all_devices()}
        device_activities = {device['imei']: device['last_activity'] for device in db.get_all_devices_activities()}
        
        # Add serial number and activity columns
        df['serial_number'] = df['payload_id_1'].map(devices_info)
        df['activity'] = df['payload_id_1'].map(device_activities)
        
        # Add Location column (reverse geocode lat/lng to street name)
        geocode_cache = {}
        def build_tracker_location(row):
            lat = row.get('latitude')
            lng = row.get('longitude')
            if pd.notna(lat) and pd.notna(lng) and lat != 0 and lng != 0:
                return reverse_geocode(float(lat), float(lng), geocode_cache)
            return '-'
        
        df['location'] = df.apply(build_tracker_location, axis=1)
        
        # Reorder and rename columns
        columns_order = [
            'payload_id_1', 'serial_number', 'payload_id_2', 'timestamp',
            'latitude', 'longitude', 'location', 'voltage', 'persentase_baterai',
            'activity', 'alarm', 'parsed_data'
        ]
        
        column_names = {
            'payload_id_1': 'IMEI',
            'serial_number': 'Serial Number',
            'payload_id_2': 'Type',
            'timestamp': 'Timestamp',
            'latitude': 'Latitude',
            'longitude': 'Longitude',
            'location': 'Location',
            'voltage': 'Voltage',
            'persentase_baterai': 'Battery (%)',
            'activity': 'Last Activity',
            'alarm': 'Alarm',
            'parsed_data': 'Raw Data'
        }

        # Select and rename columns
        df = df.reindex(columns=[col for col in columns_order if col in df.columns])
        df = df.rename(columns=column_names)

        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Device Data', index=False)

        # Reset buffer position
        output.seek(0)
        
        # Generate filename with filter info
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"device_data_{imei or 'all'}"
        if start_date and end_date:
            filename += f"_{start_date.split('T')[0]}_{end_date.split('T')[0]}"
        filename += f"_{timestamp}.xlsx"
        
        # Fix the Content-Disposition header and set Content-Length so browsers treat it as a downloadable file
        output.seek(0)
        file_bytes = output.getvalue()
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Length': str(len(file_bytes))
        }

        # Return as StreamingResponse (seeked to start)
        output.seek(0)
        return StreamingResponse(
            output,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers=headers
        )
        
    except Exception as e:
        print(f"Export error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# Add these new routes for solar tracker
@app.get("/solar-export-excel")
async def solar_export_excel(
    imei: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Export solar tracker data to Excel"""
    try:
        if imei:
            if start_date and end_date:
                try:
                    start_dt = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
                    end_dt = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')
                    data = db.get_solar_tracker_data(imei=imei, start_date=start_dt, end_date=end_dt)
                except ValueError:
                    data = db.get_solar_tracker_data(imei=imei)
            else:
                data = db.get_solar_tracker_data(imei=imei)
        else:
            if start_date and end_date:
                try:
                    start_dt = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
                    end_dt = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')
                    data = db.get_solar_tracker_data(start_date=start_dt, end_date=end_dt)
                except ValueError:
                    data = db.get_solar_tracker_data()
            else:
                data = db.get_solar_tracker_data()

        if not data:
            raise HTTPException(status_code=404, detail="No solar tracker data found to export")

        # Convert to DataFrame
        df = pd.DataFrame(data)

        # Add Location column (reverse geocode lat/lng to street name)
        geocode_cache = {}
        def build_location(row):
            lat = row.get('latitude')
            lng = row.get('longitude')
            if pd.notna(lat) and pd.notna(lng) and lat != 0 and lng != 0:
                return reverse_geocode(float(lat), float(lng), geocode_cache)
            return '-'
        
        df['location'] = df.apply(build_location, axis=1)
        
        # Reorder and rename columns
        columns_order = [
            'payload_id_1', 'payload_id_2', 'timestamp',
            'latitude', 'longitude', 'location', 'persentase_baterai',
            'speed_kmh', 'last_activity', 'alarm', 'g_sensor_status',
            'is_charging'
        ]
        
        column_names = {
            'payload_id_1': 'IMEI',
            'payload_id_2': 'Type',
            'timestamp': 'Timestamp',
            'latitude': 'Latitude',
            'longitude': 'Longitude',
            'location': 'Location',
            'persentase_baterai': 'Battery (%)',
            'speed_kmh': 'Speed (km/h)',
            'last_activity': 'Last Activity',
            'alarm': 'Alarm',
            'g_sensor_status': 'G-Sensor Status',
            'is_charging': 'Status Charging'
        }

        # Select and rename columns
        # 1. Pilih kolom yang mau dipakai
        df = df.reindex(columns=[col for col in columns_order if col in df.columns])
        # DEBUG dulu lihat isi asli (nanti hapus)
        print("ISI is_charging:", df['is_charging'].unique())

        # Mapping nilai SEBELUM rename
        df['is_charging'] = df['is_charging'].map({
            True: 'charging',
            False: 'uncharging',
            1: 'charging',
            0: 'uncharging',
            '1': 'charging',
            '0': 'uncharging'
        })

        # 3. rename nama kolom untuk tampilan
        df = df.rename(columns=column_names)
        # Convert is_charging 1/0 to text
        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Solar Tracker Data', index=False)

        # Reset buffer position
        output.seek(0)
        
        # Generate filename with filter info
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"solar_tracker_data_{imei or 'all'}"
        if start_date and end_date:
            filename += f"_{start_date.split('T')[0]}_{end_date.split('T')[0]}"
        filename += f"_{timestamp}.xlsx"
        
        # Fix the Content-Disposition header and set Content-Length so browsers treat it as a downloadable file
        output.seek(0)
        file_bytes = output.getvalue()
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Length': str(len(file_bytes))
        }

        output.seek(0)
        return StreamingResponse(
            output,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers=headers
        )
        
    except Exception as e:
        print(f"Solar export error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Solar export failed: {str(e)}")

@app.get("/geofence", response_class=HTMLResponse)
async def geofence_page(request: Request):
    """Render geofence management page"""
    return templates.TemplateResponse("geofence.html", {
        "request": request,
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5023)