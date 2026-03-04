import httpx
import re
from typing import Optional, Dict, List, Any
from datetime import datetime

class SmartQueryHandler:
    """
    Handler pintar untuk memproses query natural language
    dan menerjemahkannya ke API calls yang sesuai
    """
    
    def __init__(self, base_url: str = "http://36.92.47.218:14523"):
        self.base_url = base_url
    
    async def _detect_device_type_with_ai(self, text: str) -> Optional[str]:
        """
        Gunakan AI untuk mendeteksi jenis device yang diminta user
        Returns: 'all', 'ble', 'solar', atau None
        """
        from .load_ai import ask_ai
        
        prompt = f"""Analisis pertanyaan ini dan tentukan jenis device yang dimaksud:

KATEGORI:
- all: semua device (BLE dan Solar Tracker)
- ble: hanya device BLE
- solar: hanya device Solar Tracker
- none: tidak jelas atau tidak relevan

PERTANYAAN: "{text}"

ATURAN:
- Jika user menyebut "BLE" atau "bluetooth" → jawab: ble
- Jika user menyebut "solar" atau "tracker" → jawab: solar
- Jika user tidak spesifik jenis device → jawab: all
- Jika pertanyaan tidak tentang device → jawab: none

Jawab HANYA dengan: all, ble, solar, atau none"""

        try:
            response = ask_ai(prompt).strip().lower()
            print(f"[AI Device Type] Detected: {response}")
            
            # Validasi response
            if response in ['all', 'ble', 'solar']:
                return response
            return None
        except Exception as e:
            print(f"[AI Device Type] Error: {e}")
            return None
    
    async def handle(self, user_text: str) -> Any:
        """
        Main handler untuk memproses query user
        
        Args:
            user_text: Input text dari user
            
        Returns:
            Data hasil query atau pesan error
        """
        text = user_text.lower()
        
        print(f"[SmartQueryHandler] Processing: {user_text}")
        
        # 1. Deteksi query untuk total device count (Pattern First + AI fallback)
        if self._is_device_count_query(text):
            # Layer 1: Quick pattern matching (cepat & akurat)
            if any(kw in text for kw in ['ble', 'bluetooth']):
                device_type = 'ble'
                print(f"[SmartQueryHandler] Pattern detected: BLE")
            elif any(kw in text for kw in ['solar', 'tracker']):
                device_type = 'solar'
                print(f"[SmartQueryHandler] Pattern detected: Solar")
            else:
                # Layer 2: Gunakan AI jika tidak ada pattern jelas
                device_type = await self._detect_device_type_with_ai(user_text)
                if device_type is None or device_type not in ['ble', 'solar', 'all']:
                    device_type = 'all'  # Default ke semua device
                print(f"[SmartQueryHandler] AI detected: {device_type}")
            
            print(f"[SmartQueryHandler] Device count query for type: {device_type}")
            return await self._get_device_count(device_type)
        
        # 2. Deteksi query untuk battery filter (advanced)
        battery_filter = self._extract_battery_filter(text)
        if battery_filter:
            return await self._filter_by_battery(battery_filter)
        
        # 3. PRIORITY: Deteksi IMEI dulu sebelum device list query
        imei = self._extract_imei(text)
        if imei:
            # Check if this is a device info query (not GPS/heartbeat specific)
            if not self._is_gps_query(text) and not self._is_heartbeat_query(text):
                print(f"[SmartQueryHandler] IMEI detected: {imei}, getting device with full details")
                return await self._get_single_device_with_details(imei)
        
        # 4. Deteksi query untuk device list (Pattern First + AI fallback)
        if self._is_device_list_query(text):
            # Check if there's a date range in the query
            date_range = self._extract_date_range(text)
            
            # Layer 1: Quick pattern matching (cepat & akurat)
            if any(kw in text for kw in ['ble', 'bluetooth']):
                device_type = 'ble'
                print(f"[SmartQueryHandler] Pattern detected: BLE")
            elif any(kw in text for kw in ['solar', 'tracker']):
                device_type = 'solar'
                print(f"[SmartQueryHandler] Pattern detected: Solar")
            else:
                # Layer 2: Gunakan AI jika tidak ada pattern jelas
                device_type = await self._detect_device_type_with_ai(user_text)
                if device_type is None or device_type not in ['ble', 'solar', 'all']:
                    device_type = 'all'  # Default ke semua device
                print(f"[SmartQueryHandler] AI detected: {device_type}")
            
            # If date range is specified, filter by date range
            if date_range:
                print(f"[SmartQueryHandler] Device list query with date range for type: {device_type}")
                return await self._get_device_list_by_date_range(device_type, date_range)
            
            print(f"[SmartQueryHandler] Device list query for type: {device_type}")
            return await self._get_device_list(device_type)
        
        # 5. Deteksi query untuk GPS/location
        if self._is_gps_query(text):
            imei = self._extract_imei(text)
            date_range = self._extract_date_range(text)
            
            if imei:
                # Query untuk 1 device spesifik
                if "terbaru" in text or "terakhir" in text or "latest" in text:
                    return await self._get_latest_gps(imei)
                if date_range:
                    return await self._get_gps_by_date_range(imei, date_range)
                return await self._get_latest_gps(imei)
            elif date_range:
                # Query untuk semua device dengan date range (tidak ada IMEI spesifik)
                # Deteksi device type
                if any(kw in text for kw in ['ble', 'bluetooth']):
                    device_type = 'ble'
                elif any(kw in text for kw in ['solar', 'tracker']):
                    device_type = 'solar'
                else:
                    device_type = 'all'  # Default ke semua device
                
                print(f"[SmartQueryHandler] GPS date range query for device type: {device_type}")
                return await self._get_all_gps_by_date_range(date_range, device_type)
        
        # 6. Deteksi query untuk heartbeat/battery
        if self._is_heartbeat_query(text):
            imei = self._extract_imei(text)
            if imei:
                return await self._get_latest_heartbeat(imei)
        
        # 7. Deteksi query untuk beacon
        if self._is_beacon_query(text):
            return await self._get_beacon_locations()
        
        # 8. Deteksi query untuk activity
        if self._is_activity_query(text):
            imei = self._extract_imei(text)
            if imei:
                return await self._get_device_activity(imei)
            return await self._get_all_activities()
        
        # 9. Deteksi query untuk geofence
        if self._is_geofence_query(text):
            return await self._get_geofences()
        
        # 10. Deteksi query untuk solar tracker (dengan advanced filtering)
        if self._is_solar_query(text):
            imei = self._extract_imei(text)
            keyword = self._extract_search_keyword(text)
            if imei or keyword:
                return await self._search_solar_devices(imei, keyword)
            return await self._get_solar_devices()
        
        # 11. Deteksi query untuk mencari device dengan keyword
        if any(kw in text for kw in ["cari", "tampilkan", "lihat", "device", "imei"]):
            keyword = self._extract_search_keyword(text)
            if keyword:
                return await self._search_devices(keyword)
        
        # Jika tidak ada yang cocok, return None
        return None
    
    def _is_device_count_query(self, text: str) -> bool:
        """Deteksi query untuk total device"""
        patterns = [
            r'berapa\s+(banyak|jumlah)?\s*(device|perangkat)',
            r'total\s+(device|perangkat)',
            r'jumlah\s+(device|perangkat)',
            r'(device|perangkat)\s+online',
            r'count\s+(device|perangkat)'
        ]
        return any(re.search(pattern, text) for pattern in patterns)
    
    def _is_device_list_query(self, text: str) -> bool:
        """Deteksi query untuk list semua device"""
        patterns = [
            r'(tampilkan|lihat|list)\s+(semua|all)?\s*(device|perangkat)',
            r'(semua|all)\s+(device|perangkat)',
            r'daftar\s+(device|perangkat)'
        ]
        return any(re.search(pattern, text) for pattern in patterns)
    
    def _extract_imei(self, text: str) -> Optional[str]:
        """
        Extract IMEI dari text
        IMEI biasanya 15 digit angka
        """
        # Pattern untuk IMEI (15 digit)
        imei_pattern = r'\b\d{15}\b'
        match = re.search(imei_pattern, text)
        if match:
            return match.group(0)
        
        # Pattern alternatif: "imei 123456789012345" atau "imei: 123456789012345"
        alt_pattern = r'imei[:\s]+(\d{15})'
        match = re.search(alt_pattern, text)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_search_keyword(self, text: str) -> Optional[str]:
        """
        Extract keyword untuk pencarian
        Contoh: "cari device 1234" -> "1234"
        """
        # Pattern: "cari/tampilkan/lihat device/imei [keyword]"
        patterns = [
            r'(?:cari|tampilkan|lihat)\s+(?:device|imei|perangkat)\s+["\']?([^"\']+)["\']?',
            r'(?:device|imei)\s+(?:mengandung|dengan)\s+["\']?([^"\']+)["\']?',
            r'(?:device|imei)\s+["\']([^"\']+)["\']'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                keyword = match.group(1).strip()
                # Jangan return jika keyword adalah IMEI lengkap (sudah dihandle di _extract_imei)
                if len(keyword) != 15 or not keyword.isdigit():
                    return keyword
        
        return None
    
    def _extract_date_range(self, text: str) -> Optional[Dict[str, str]]:
        """
        Extract date range dari text
        Format yang didukung:
        - "dari 2024-01-01 sampai 2024-01-31"
        - "tanggal 2024-01-01 hingga 2024-01-31"
        - "dari 2024-01-01 00:00:00 sampai 2024-01-31 23:59:59"
        """
        # Pattern untuk date range
        patterns = [
            r'(?:dari|tanggal|mulai)\s+(\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2}:\d{2})?)\s+(?:sampai|hingga|ke|until)\s+(\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2}:\d{2})?)',
            r'(\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2}:\d{2})?)\s+(?:sampai|hingga|to)\s+(\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2}:\d{2})?)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                start_date = match.group(1).strip()
                end_date = match.group(2).strip()
                
                # Add default time if not specified
                if len(start_date) == 10:  # Only date, no time
                    start_date += " 00:00:00"
                if len(end_date) == 10:
                    end_date += " 23:59:59"
                
                return {
                    "start_date": start_date,
                    "end_date": end_date
                }
        
        return None
    
    async def _get_device_count(self, device_type: str = 'all') -> Any:
        """
        Get device count berdasarkan type
        
        Args:
            device_type: 'all', 'ble', atau 'solar'
            
        Returns:
            Integer count atau dict dengan breakdown
        """
        try:
            async with httpx.AsyncClient() as client:
                if device_type == 'all':
                    # Get total semua device
                    res = await client.get(f"{self.base_url}/devices/count", timeout=30.0)
                    data = res.json()
                    total = data.get('total_devices', 0)
                    
                    # Get breakdown per type untuk informasi lengkap
                    devices_res = await client.get(f"{self.base_url}/devices", timeout=30.0)
                    devices_data = devices_res.json()
                    all_devices = devices_data.get('devices', [])
                    
                    solar_res = await client.get(f"{self.base_url}/solar-tracker/devices", timeout=30.0)
                    solar_data = solar_res.json()
                    solar_devices = solar_data.get('devices', [])
                    
                    ble_count = len(all_devices)
                    solar_count = len(solar_devices)
                    
                    print(f"[SmartQueryHandler] Total devices: {total} (BLE: {ble_count}, Solar: {solar_count})")
                    
                    return {
                        'total': total,
                        'ble': ble_count,
                        'solar': solar_count,
                        'breakdown': True
                    }
                    
                elif device_type == 'ble':
                    # Get hanya BLE devices
                    res = await client.get(f"{self.base_url}/devices", timeout=30.0)
                    data = res.json()
                    devices = data.get('devices', [])
                    count = len(devices)
                    print(f"[SmartQueryHandler] BLE device count: {count}")
                    return count
                    
                elif device_type == 'solar':
                    # Get hanya Solar Tracker devices
                    res = await client.get(f"{self.base_url}/solar-tracker/devices", timeout=30.0)
                    data = res.json()
                    devices = data.get('devices', [])
                    count = len(devices)
                    print(f"[SmartQueryHandler] Solar device count: {count}")
                    return count
                    
                else:
                    return "Tipe device tidak valid."
                    
        except Exception as e:
            print(f"[SmartQueryHandler] Error getting device count: {e}")
            return "Maaf, terjadi kesalahan saat mengambil jumlah device."
    
    async def _get_device_list(self, device_type: str = 'all') -> Any:
        """
        Get device list berdasarkan type dengan data lengkap
        
        Args:
            device_type: 'all', 'ble', atau 'solar'
            
        Returns:
            List of devices dengan data lengkap atau dict dengan grouping
        """
        try:
            async with httpx.AsyncClient() as client:
                if device_type == 'all':
                    # Get semua device (BLE + Solar) dengan data lengkap
                    ble_devices = await self._get_ble_devices_with_details(client)
                    solar_devices = await self._get_solar_devices_with_details(client)
                    
                    total = len(ble_devices) + len(solar_devices)
                    print(f"[SmartQueryHandler] Found {total} devices with details (BLE: {len(ble_devices)}, Solar: {len(solar_devices)})")
                    
                    # Return grouped format
                    return {
                        'grouped': True,
                        'total': total,
                        'groups': {
                            'Device BLE': ble_devices,
                            'Device Solar Tracker': solar_devices
                        }
                    }
                    
                elif device_type == 'ble':
                    # Get hanya BLE devices dengan data lengkap
                    devices = await self._get_ble_devices_with_details(client)
                    print(f"[SmartQueryHandler] Found {len(devices)} BLE devices with details")
                    return devices
                    
                elif device_type == 'solar':
                    # Get hanya Solar Tracker devices dengan data lengkap
                    devices = await self._get_solar_devices_with_details(client)
                    print(f"[SmartQueryHandler] Found {len(devices)} Solar devices with details")
                    return devices
                    
                else:
                    return "Tipe device tidak valid."
                    
        except Exception as e:
            print(f"[SmartQueryHandler] Error getting device list: {e}")
            return "Maaf, terjadi kesalahan saat mengambil daftar device."
    
    async def _get_device_list_by_date_range(self, device_type: str, date_range: Dict[str, str]) -> Any:
        """
        Get device list berdasarkan type dan filter berdasarkan date range
        Filter berdasarkan timestamp aktivitas terakhir (GPS/heartbeat/data terakhir)
        
        Args:
            device_type: 'all', 'ble', atau 'solar'
            date_range: Dictionary dengan 'start_date' dan 'end_date'
            
        Returns:
            List of devices yang aktif dalam date range atau dict dengan grouping
        """
        try:
            from datetime import datetime
            
            # Parse date range
            start_dt = datetime.strptime(date_range['start_date'], '%Y-%m-%d %H:%M:%S')
            end_dt = datetime.strptime(date_range['end_date'], '%Y-%m-%d %H:%M:%S')
            
            print(f"[SmartQueryHandler] Filtering devices from {start_dt} to {end_dt}")
            
            async with httpx.AsyncClient() as client:
                filtered_ble = []
                filtered_solar = []
                
                if device_type in ['all', 'ble']:
                    # Get BLE devices dengan details
                    ble_devices = await self._get_ble_devices_with_details(client)
                    
                    # Filter berdasarkan timestamp terakhir
                    for device in ble_devices:
                        # Cek timestamp dari GPS, heartbeat, atau beacon (ambil yang terbaru)
                        timestamps = []
                        
                        if device.get('gps_timestamp'):
                            timestamps.append(device['gps_timestamp'])
                        if device.get('heartbeat_timestamp'):
                            timestamps.append(device['heartbeat_timestamp'])
                        if device.get('beacon_timestamp'):
                            timestamps.append(device['beacon_timestamp'])
                        
                        if timestamps:
                            # Ambil timestamp terbaru
                            latest_timestamp = max(timestamps)
                            try:
                                device_dt = datetime.strptime(latest_timestamp, '%Y-%m-%d %H:%M:%S')
                                # Check if device was active in date range
                                if start_dt <= device_dt <= end_dt:
                                    filtered_ble.append(device)
                            except ValueError:
                                # Skip jika format timestamp tidak valid
                                continue
                
                if device_type in ['all', 'solar']:
                    # Get Solar devices dengan details
                    solar_devices = await self._get_solar_devices_with_details(client)
                    
                    # Filter berdasarkan timestamp
                    for device in solar_devices:
                        if device.get('timestamp'):
                            try:
                                device_dt = datetime.strptime(device['timestamp'], '%Y-%m-%d %H:%M:%S')
                                # Check if device was active in date range
                                if start_dt <= device_dt <= end_dt:
                                    filtered_solar.append(device)
                            except ValueError:
                                # Skip jika format timestamp tidak valid
                                continue
                
                # Return results
                total = len(filtered_ble) + len(filtered_solar)
                
                if total == 0:
                    return f"Tidak ada device yang aktif dari {date_range['start_date']} sampai {date_range['end_date']}"
                
                print(f"[SmartQueryHandler] Found {total} devices in date range (BLE: {len(filtered_ble)}, Solar: {len(filtered_solar)})")
                
                if device_type == 'all':
                    # Return grouped format dengan informasi jumlah per kategori
                    result = {
                        'grouped': True,
                        'total': total,
                        'date_range': {
                            'start': date_range['start_date'],
                            'end': date_range['end_date']
                        },
                        'summary': {
                            'ble_count': len(filtered_ble),
                            'solar_count': len(filtered_solar)
                        },
                        'groups': {}
                    }
                    if filtered_ble:
                        result['groups']['Device BLE'] = filtered_ble
                    if filtered_solar:
                        result['groups']['Device Solar Tracker'] = filtered_solar
                    return result
                elif device_type == 'ble':
                    # Return dengan informasi jumlah
                    return {
                        'device_type': 'BLE',
                        'count': len(filtered_ble),
                        'date_range': {
                            'start': date_range['start_date'],
                            'end': date_range['end_date']
                        },
                        'devices': filtered_ble
                    }
                elif device_type == 'solar':
                    # Return dengan informasi jumlah
                    return {
                        'device_type': 'Solar Tracker',
                        'count': len(filtered_solar),
                        'date_range': {
                            'start': date_range['start_date'],
                            'end': date_range['end_date']
                        },
                        'devices': filtered_solar
                    }
                    
        except Exception as e:
            print(f"[SmartQueryHandler] Error getting device list by date range: {e}")
            import traceback
            traceback.print_exc()
            return "Maaf, terjadi kesalahan saat memfilter device berdasarkan tanggal."
    
    async def _get_ble_devices_with_details(self, client: httpx.AsyncClient) -> List[Dict]:
        """
        Get BLE devices dengan data lengkap (activity, latest data, dll)
        Menggabungkan data dari multiple API
        """
        try:
            # 1. Get list BLE devices
            devices_res = await client.get(f"{self.base_url}/devices", timeout=30.0)
            devices = devices_res.json().get('devices', [])
            
            # 2. Get all activities
            activities_res = await client.get(f"{self.base_url}/all-device-activities", timeout=30.0)
            activities_data = activities_res.json().get('devices', [])
            activities_map = {item['imei']: item for item in activities_data}
            
            # 3. Get all registration data untuk latest info
            reg_res = await client.get(f"{self.base_url}/registration/all", timeout=30.0)
            all_reg_data = reg_res.json().get('data', [])
            
            # Group registration data by IMEI dan ambil yang terbaru
            latest_data_map = {}
            for item in all_reg_data:
                imei = item.get('payload_id_1')
                if imei not in latest_data_map:
                    latest_data_map[imei] = {
                        'gps': None,
                        'heartbeat': None,
                        'beacon': None,
                        'alarm': None
                    }
                
                payload_type = item.get('payload_id_2')
                timestamp = item.get('timestamp', '')
                
                if payload_type == 'GPS':
                    if latest_data_map[imei]['gps'] is None or timestamp > latest_data_map[imei]['gps'].get('timestamp', ''):
                        latest_data_map[imei]['gps'] = item
                elif payload_type == 'Heartbeat':
                    if latest_data_map[imei]['heartbeat'] is None or timestamp > latest_data_map[imei]['heartbeat'].get('timestamp', ''):
                        latest_data_map[imei]['heartbeat'] = item
                elif payload_type == 'Beacon':
                    if latest_data_map[imei]['beacon'] is None or timestamp > latest_data_map[imei]['beacon'].get('timestamp', ''):
                        latest_data_map[imei]['beacon'] = item
                elif payload_type == 'Alarm':
                    if latest_data_map[imei]['alarm'] is None or timestamp > latest_data_map[imei]['alarm'].get('timestamp', ''):
                        latest_data_map[imei]['alarm'] = item
            
            # 4. Combine all data
            enriched_devices = []
            for device in devices:
                imei = device['imei']
                
                # Determine last update timestamp from ALL payload types
                all_timestamps = []
                if imei in latest_data_map:
                    latest = latest_data_map[imei]
                    if latest['gps']:
                        all_timestamps.append(latest['gps'].get('timestamp', ''))
                    if latest['heartbeat']:
                        all_timestamps.append(latest['heartbeat'].get('timestamp', ''))
                    if latest['beacon']:
                        all_timestamps.append(latest['beacon'].get('timestamp', ''))
                    if latest['alarm']:
                        all_timestamps.append(latest['alarm'].get('timestamp', ''))
                
                last_update = max(all_timestamps) if all_timestamps else None
                
                enriched = {
                    'imei': imei,
                    'serial_number': device.get('serial_number'),
                    'device_type': 'BLE',
                    'last_activity': activities_map.get(imei, {}).get('last_activity', 'No Activity'),
                    'last_update': last_update,  # Timestamp terbaru dari semua payload
                }
                
                # Add latest data
                if imei in latest_data_map:
                    latest = latest_data_map[imei]
                    
                    # GPS data
                    if latest['gps']:
                        enriched['latitude'] = latest['gps'].get('latitude')
                        enriched['longitude'] = latest['gps'].get('longitude')
                        enriched['gps_timestamp'] = latest['gps'].get('timestamp')
                    
                    # Heartbeat data
                    if latest['heartbeat']:
                        enriched['battery'] = latest['heartbeat'].get('persentase_baterai')
                        enriched['voltage'] = latest['heartbeat'].get('voltage')
                        enriched['heartbeat_timestamp'] = latest['heartbeat'].get('timestamp')
                    
                    # Beacon data
                    if latest['beacon']:
                        enriched['beacon_data'] = latest['beacon'].get('parsed_data')
                        enriched['beacon_timestamp'] = latest['beacon'].get('timestamp')
                    
                    # Alarm data
                    if latest['alarm']:
                        enriched['alarm'] = latest['alarm'].get('alarm')
                        enriched['alarm_timestamp'] = latest['alarm'].get('timestamp')
                
                enriched_devices.append(enriched)
            
            return enriched_devices
            
        except Exception as e:
            print(f"[SmartQueryHandler] Error getting BLE devices with details: {e}")
            return []
    
    async def _get_solar_devices_with_details(self, client: httpx.AsyncClient) -> List[Dict]:
        """
        Get Solar Tracker devices dengan data lengkap
        Menggabungkan data dari multiple API
        """
        try:
            # 1. Get list Solar devices
            devices_res = await client.get(f"{self.base_url}/solar-tracker/devices", timeout=30.0)
            devices = devices_res.json().get('devices', [])
            
            # 2. Get all solar tracker data
            data_res = await client.get(f"{self.base_url}/solar-tracker/data", timeout=30.0)
            all_data = data_res.json().get('data', [])
            
            # Group by IMEI dan ambil yang terbaru
            latest_data_map = {}
            for item in all_data:
                imei = item.get('payload_id_1')
                timestamp = item.get('timestamp', '')
                
                if imei not in latest_data_map or timestamp > latest_data_map[imei].get('timestamp', ''):
                    latest_data_map[imei] = item
            
            # 3. Combine data
            enriched_devices = []
            for device in devices:
                imei = device['imei']
                enriched = {
                    'imei': imei,
                    'serial_number': device.get('serial_number', imei),
                    'device_type': 'Solar Tracker',
                }
                
                # Add latest data
                if imei in latest_data_map:
                    latest = latest_data_map[imei]
                    enriched['latitude'] = latest.get('latitude')
                    enriched['longitude'] = latest.get('longitude')
                    enriched['battery'] = latest.get('persentase_baterai')
                    enriched['speed_kmh'] = latest.get('speed_kmh')
                    enriched['g_sensor_status'] = latest.get('g_sensor_status')
                    enriched['alarm'] = latest.get('alarm')
                    enriched['timestamp'] = latest.get('timestamp')
                
                enriched_devices.append(enriched)
            
            return enriched_devices
            
        except Exception as e:
            print(f"[SmartQueryHandler] Error getting Solar devices with details: {e}")
            return []
    
    async def _get_single_device_with_details(self, imei: str) -> Dict:
        """
        Get single device dengan data lengkap berdasarkan IMEI
        Menampilkan:
        1. Data terbaru absolut (timestamp paling baru dari semua tipe)
        2. Data terbaru per kategori (GPS, Heartbeat, Beacon, Alarm)
        """
        try:
            async with httpx.AsyncClient() as client:
                # 1. Check if device exists in BLE or Solar (active devices only)
                # Try BLE first
                devices_res = await client.get(f"{self.base_url}/devices", timeout=30.0)
                ble_devices = devices_res.json().get('devices', [])
                device_info = next((d for d in ble_devices if d['imei'] == imei), None)
                
                if device_info:
                    # It's a BLE device - get ALL data
                    print(f"[SmartQueryHandler] Found active BLE device {imei}, fetching all latest data")
                    
                    # Get activity
                    activity_res = await client.get(f"{self.base_url}/device-activity/{imei}", timeout=30.0)
                    activity = activity_res.json().get('last_activity', 'No Activity') if activity_res.status_code == 200 else 'No Activity'
                    
                    # Get ALL registration data to find the latest
                    reg_res = await client.get(f"{self.base_url}/registration/all", timeout=30.0)
                    all_reg_data = reg_res.json().get('data', []) if reg_res.status_code == 200 else []
                    
                    # Filter only for this IMEI
                    device_reg_data = [item for item in all_reg_data if item.get('payload_id_1') == imei]
                    
                    if not device_reg_data:
                        return {
                            'imei': imei,
                            'serial_number': device_info.get('serial_number'),
                            'device_type': 'BLE',
                            'last_activity': activity,
                            'message': 'Tidak ada data registrasi untuk device ini'
                        }
                    
                    # Find absolute latest data (regardless of type)
                    absolute_latest = max(device_reg_data, key=lambda x: x.get('timestamp', ''))
                    
                    # Get latest per category
                    latest_gps = None
                    latest_heartbeat = None
                    latest_beacon = None
                    latest_alarm = None
                    
                    for item in device_reg_data:
                        payload_type = item.get('payload_id_2')
                        timestamp = item.get('timestamp', '')
                        
                        if payload_type == 'GPS':
                            if latest_gps is None or timestamp > latest_gps.get('timestamp', ''):
                                latest_gps = item
                        elif payload_type == 'Heartbeat':
                            if latest_heartbeat is None or timestamp > latest_heartbeat.get('timestamp', ''):
                                latest_heartbeat = item
                        elif payload_type == 'Beacon':
                            if latest_beacon is None or timestamp > latest_beacon.get('timestamp', ''):
                                latest_beacon = item
                        elif payload_type == 'Alarm':
                            if latest_alarm is None or timestamp > latest_alarm.get('timestamp', ''):
                                latest_alarm = item
                    
                    # Build response with both absolute latest and per-category latest
                    result = {
                        'imei': imei,
                        'serial_number': device_info.get('serial_number'),
                        'device_type': 'BLE',
                        'last_activity': activity,
                        'absolute_latest': {
                            'type': absolute_latest.get('payload_id_2'),
                            'timestamp': absolute_latest.get('timestamp'),
                            'data': absolute_latest
                        },
                        'latest_per_category': {}
                    }
                    
                    # Add latest per category
                    if latest_gps:
                        result['latest_per_category']['GPS'] = latest_gps
                    if latest_heartbeat:
                        result['latest_per_category']['Heartbeat'] = latest_heartbeat
                    if latest_beacon:
                        result['latest_per_category']['Beacon'] = latest_beacon
                    if latest_alarm:
                        result['latest_per_category']['Alarm'] = latest_alarm
                    
                    print(f"[SmartQueryHandler] Returning comprehensive data for {imei}")
                    print(f"  - Absolute latest: {absolute_latest.get('payload_id_2')} at {absolute_latest.get('timestamp')}")
                    print(f"  - Categories found: {list(result['latest_per_category'].keys())}")
                    
                    return result
                
                # Try Solar Tracker
                solar_res = await client.get(f"{self.base_url}/solar-tracker/devices", timeout=30.0)
                solar_devices = solar_res.json().get('devices', [])
                device_info = next((d for d in solar_devices if d['imei'] == imei), None)
                
                if device_info:
                    # It's a Solar device - get latest data
                    print(f"[SmartQueryHandler] Found active Solar device {imei}, fetching latest data")
                    
                    # Get ALL solar tracker data to find the latest
                    data_res = await client.get(f"{self.base_url}/solar-tracker/data", timeout=30.0)
                    all_data = data_res.json().get('data', [])
                    
                    # Find latest data for this IMEI
                    device_data = [d for d in all_data if d.get('payload_id_1') == imei]
                    latest_data = max(device_data, key=lambda x: x.get('timestamp', ''), default=None) if device_data else None
                    
                    # Build response (Solar only has one data stream)
                    result = {
                        'imei': imei,
                        'serial_number': device_info.get('serial_number', imei),
                        'device_type': 'Solar Tracker',
                    }
                    
                    if latest_data:
                        result['absolute_latest'] = {
                            'type': 'Solar Tracker Data',
                            'timestamp': latest_data.get('timestamp'),
                            'data': latest_data
                        }
                        result['latest_per_category'] = {
                            'Solar': latest_data
                        }
                        
                        print(f"[SmartQueryHandler] Returning latest data for active device {imei}, timestamp: {latest_data.get('timestamp')}")
                    else:
                        result['message'] = 'Tidak ada data untuk device ini'
                    
                    return result
                
                # Device not found in active devices
                return f"Device dengan IMEI {imei} tidak ditemukan atau tidak aktif"
                
        except Exception as e:
            print(f"[SmartQueryHandler] Error getting single device with details: {e}")
            import traceback
            traceback.print_exc()
            return f"Maaf, terjadi kesalahan saat mengambil data untuk IMEI {imei}."
    
    async def _get_registration_by_imei(self, imei: str) -> List[Dict]:
        """Get registration data by IMEI"""
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(f"{self.base_url}/registration/{imei}", timeout=30.0)
                if res.status_code == 404:
                    return f"Tidak ada data untuk IMEI {imei}"
                data = res.json()
                registration_data = data.get('data', [])
                print(f"[SmartQueryHandler] Found {len(registration_data)} records for IMEI {imei}")
                return registration_data
        except Exception as e:
            print(f"[SmartQueryHandler] Error getting registration data: {e}")
            return f"Maaf, terjadi kesalahan saat mengambil data untuk IMEI {imei}."
    
    async def _get_registration_by_date_range(self, imei: str, date_range: Dict[str, str]) -> List[Dict]:
        """Get registration data by IMEI and date range"""
        try:
            async with httpx.AsyncClient() as client:
                # Use POST with form data
                form_data = {
                    "start_date": date_range["start_date"],
                    "end_date": date_range["end_date"]
                }
                res = await client.post(
                    f"{self.base_url}/registration/{imei}/date-range",
                    data=form_data,
                    timeout=30.0
                )
                if res.status_code == 404:
                    return f"Tidak ada data untuk IMEI {imei} pada rentang tanggal tersebut"
                data = res.json()
                registration_data = data.get('data', [])
                meta = data.get('meta', {})
                print(f"[SmartQueryHandler] Found {len(registration_data)} records for IMEI {imei} from {meta.get('start_date')} to {meta.get('end_date')}")
                return registration_data
        except Exception as e:
            print(f"[SmartQueryHandler] Error getting registration data by date range: {e}")
            return f"Maaf, terjadi kesalahan saat mengambil data untuk IMEI {imei} dengan rentang tanggal."
    
    async def _search_devices(self, keyword: str) -> List[Dict]:
        """Search devices by keyword (partial IMEI or serial number)"""
        try:
            # Get all devices first
            devices = await self._get_device_list()
            if isinstance(devices, str):  # Error message
                return devices
            
            # Filter devices by keyword
            keyword_lower = keyword.lower()
            filtered = [
                device for device in devices
                if keyword_lower in str(device.get('imei', '')).lower() or
                   keyword_lower in str(device.get('serial_number', '')).lower()
            ]
            
            print(f"[SmartQueryHandler] Found {len(filtered)} devices matching '{keyword}'")
            
            if not filtered:
                return f"Tidak ada device yang cocok dengan keyword '{keyword}'"
            
            return filtered
        except Exception as e:
            print(f"[SmartQueryHandler] Error searching devices: {e}")
            return f"Maaf, terjadi kesalahan saat mencari device dengan keyword '{keyword}'."
    
    def _is_gps_query(self, text: str) -> bool:
        """Deteksi query untuk GPS/lokasi"""
        patterns = [
            r'(gps|lokasi|location|posisi|koordinat)',
            r'dimana\s+(posisi|lokasi)',
            r'(latitude|longitude)'
        ]
        return any(re.search(pattern, text) for pattern in patterns)
    
    def _is_heartbeat_query(self, text: str) -> bool:
        """Deteksi query untuk heartbeat/battery"""
        patterns = [
            r'(heartbeat|battery|baterai|voltage|tegangan)',
            r'berapa\s+(battery|baterai)',
            r'status\s+(battery|baterai)'
        ]
        return any(re.search(pattern, text) for pattern in patterns)
    
    def _is_beacon_query(self, text: str) -> bool:
        """Deteksi query untuk beacon"""
        patterns = [
            r'beacon',
            r'major\s+(dan|&)?\s*minor'
        ]
        return any(re.search(pattern, text) for pattern in patterns)
    
    def _is_activity_query(self, text: str) -> bool:
        """Deteksi query untuk activity"""
        patterns = [
            r'activity|aktivitas',
            r'(last|terakhir)\s+(activity|aktivitas)',
            r'container'
        ]
        return any(re.search(pattern, text) for pattern in patterns)
    
    def _is_geofence_query(self, text: str) -> bool:
        """Deteksi query untuk geofence"""
        patterns = [
            r'geofence',
            r'area\s+(terdaftar|registered)',
            r'(daftar|list)\s+area'
        ]
        return any(re.search(pattern, text) for pattern in patterns)
    
    def _is_solar_query(self, text: str) -> bool:
        """Deteksi query untuk solar tracker"""
        patterns = [
            r'solar',
            r'panel\s+surya',
            r'tracker\s+solar'
        ]
        return any(re.search(pattern, text) for pattern in patterns)
    
    async def _get_latest_gps(self, imei: str) -> Dict:
        """
        Get latest GPS data by IMEI
        Hanya untuk device AKTIF
        """
        try:
            async with httpx.AsyncClient() as client:
                # 1. Validasi apakah IMEI adalah device aktif
                devices_res = await client.get(f"{self.base_url}/devices", timeout=30.0)
                ble_devices = devices_res.json().get('devices', [])
                ble_imeis = {d['imei'] for d in ble_devices}
                
                solar_res = await client.get(f"{self.base_url}/solar-tracker/devices", timeout=30.0)
                solar_devices = solar_res.json().get('devices', [])
                solar_imeis = {d['imei'] for d in solar_devices}
                
                # Check if IMEI is active
                if imei not in ble_imeis and imei not in solar_imeis:
                    return f"Device dengan IMEI {imei} tidak aktif atau tidak ditemukan"
                
                # 2. Get latest GPS data
                res = await client.get(f"{self.base_url}/gps/{imei}/latest", timeout=30.0)
                if res.status_code == 404:
                    return f"Tidak ada data GPS untuk IMEI {imei}"
                data = res.json()
                gps_data = data.get('data', {})
                print(f"[SmartQueryHandler] Found latest GPS for active device {imei}")
                return [gps_data] if gps_data else f"Tidak ada data GPS untuk IMEI {imei}"
        except Exception as e:
            print(f"[SmartQueryHandler] Error getting latest GPS: {e}")
            return f"Maaf, terjadi kesalahan saat mengambil data GPS untuk IMEI {imei}."
    
    async def _get_gps_by_date_range(self, imei: str, date_range: Dict[str, str]) -> List[Dict]:
        """
        Get GPS data by IMEI and date range
        Hanya untuk device AKTIF
        """
        try:
            async with httpx.AsyncClient() as client:
                # 1. Validasi apakah IMEI adalah device aktif
                devices_res = await client.get(f"{self.base_url}/devices", timeout=30.0)
                ble_devices = devices_res.json().get('devices', [])
                ble_imeis = {d['imei'] for d in ble_devices}
                
                solar_res = await client.get(f"{self.base_url}/solar-tracker/devices", timeout=30.0)
                solar_devices = solar_res.json().get('devices', [])
                solar_imeis = {d['imei'] for d in solar_devices}
                
                # Check if IMEI is active
                if imei not in ble_imeis and imei not in solar_imeis:
                    return f"Device dengan IMEI {imei} tidak aktif atau tidak ditemukan"
                
                # 2. Get GPS data by date range
                params = {
                    "start_date": date_range["start_date"],
                    "end_date": date_range["end_date"]
                }
                res = await client.get(
                    f"{self.base_url}/registration/{imei}/gps",
                    params=params,
                    timeout=30.0
                )
                if res.status_code == 404:
                    return f"Tidak ada data GPS untuk IMEI {imei} pada rentang tanggal tersebut"
                data = res.json()
                gps_data = data.get('data', [])
                meta = data.get('meta', {})
                print(f"[SmartQueryHandler] Found {len(gps_data)} GPS records for active device {imei}")
                return gps_data
        except Exception as e:
            print(f"[SmartQueryHandler] Error getting GPS data by date range: {e}")
            return f"Maaf, terjadi kesalahan saat mengambil data GPS untuk IMEI {imei}."
    async def _get_all_gps_by_date_range(self, date_range: Dict[str, str], device_type: str = 'all') -> Any:
        """
        Get GPS data untuk semua device AKTIF berdasarkan date range dan device type
        
        Args:
            date_range: Dictionary dengan 'start_date' dan 'end_date'
            device_type: 'all', 'ble', atau 'solar'
            
        Returns:
            List of GPS data atau dict dengan grouping (hanya device aktif)
        """
        try:
            async with httpx.AsyncClient() as client:
                gps_data = []
                
                if device_type in ['all', 'ble']:
                    # 1. Get active BLE devices
                    devices_res = await client.get(f"{self.base_url}/devices", timeout=30.0)
                    active_ble_devices = devices_res.json().get('devices', [])
                    active_ble_imeis = {d['imei'] for d in active_ble_devices}
                    
                    print(f"[SmartQueryHandler] Found {len(active_ble_imeis)} active BLE devices")
                    
                    # 2. Get GPS data untuk BLE devices
                    params = {
                        "start_date": date_range["start_date"],
                        "end_date": date_range["end_date"]
                    }
                    res = await client.get(
                        f"{self.base_url}/registration/gps",
                        params=params,
                        timeout=30.0
                    )
                    if res.status_code == 200:
                        all_ble_gps = res.json().get('data', [])
                        # 3. Filter hanya IMEI device aktif
                        ble_gps = [
                            item for item in all_ble_gps
                            if item.get('payload_id_1') in active_ble_imeis
                        ]
                        gps_data.extend(ble_gps)
                        print(f"[SmartQueryHandler] Filtered to {len(ble_gps)} GPS records from active BLE devices")
                
                if device_type in ['all', 'solar']:
                    # 1. Get active Solar devices
                    solar_devices_res = await client.get(f"{self.base_url}/solar-tracker/devices", timeout=30.0)
                    active_solar_devices = solar_devices_res.json().get('devices', [])
                    active_solar_imeis = {d['imei'] for d in active_solar_devices}
                    
                    print(f"[SmartQueryHandler] Found {len(active_solar_imeis)} active Solar devices")
                    
                    # 2. Get GPS data untuk Solar Tracker devices
                    params = {
                        "start_date": date_range["start_date"],
                        "end_date": date_range["end_date"]
                    }
                    res = await client.get(
                        f"{self.base_url}/solar-tracker/gps",
                        params=params,
                        timeout=30.0
                    )
                    if res.status_code == 200:
                        all_solar_gps = res.json().get('data', [])
                        # 3. Filter hanya IMEI device aktif
                        solar_gps = [
                            item for item in all_solar_gps
                            if item.get('payload_id_1') in active_solar_imeis
                        ]
                        gps_data.extend(solar_gps)
                        print(f"[SmartQueryHandler] Filtered to {len(solar_gps)} GPS records from active Solar devices")
                
                if not gps_data:
                    return f"Tidak ada data GPS dari device aktif untuk rentang tanggal {date_range['start_date']} sampai {date_range['end_date']}"
                
                print(f"[SmartQueryHandler] Found {len(gps_data)} GPS records from active devices for date range")
                return gps_data
                
        except Exception as e:
            print(f"[SmartQueryHandler] Error getting GPS data by date range: {e}")
            return f"Maaf, terjadi kesalahan saat mengambil data GPS untuk rentang tanggal tersebut."
    
    
    async def _get_latest_heartbeat(self, imei: str) -> Dict:
        """
        Get latest heartbeat data by IMEI
        Hanya untuk device AKTIF
        """
        try:
            async with httpx.AsyncClient() as client:
                # 1. Validasi apakah IMEI adalah device aktif (hanya BLE yang punya heartbeat)
                devices_res = await client.get(f"{self.base_url}/devices", timeout=30.0)
                ble_devices = devices_res.json().get('devices', [])
                ble_imeis = {d['imei'] for d in ble_devices}
                
                # Check if IMEI is active BLE device
                if imei not in ble_imeis:
                    return f"Device dengan IMEI {imei} tidak aktif atau bukan device BLE"
                
                # 2. Get latest heartbeat data
                res = await client.get(f"{self.base_url}/heartbeat/{imei}/latest", timeout=30.0)
                if res.status_code == 404:
                    return f"Tidak ada data heartbeat untuk IMEI {imei}"
                data = res.json()
                heartbeat_data = data.get('data', {})
                print(f"[SmartQueryHandler] Found latest heartbeat for active device {imei}")
                return [heartbeat_data] if heartbeat_data else f"Tidak ada data heartbeat untuk IMEI {imei}"
        except Exception as e:
            print(f"[SmartQueryHandler] Error getting latest heartbeat: {e}")
            return f"Maaf, terjadi kesalahan saat mengambil data heartbeat untuk IMEI {imei}."
    
    async def _get_beacon_locations(self) -> List[Dict]:
        """Get all beacon locations"""
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(f"{self.base_url}/beacon/locations", timeout=30.0)
                data = res.json()
                beacon_data = data.get('data', [])
                print(f"[SmartQueryHandler] Found {len(beacon_data)} beacon locations")
                return beacon_data
        except Exception as e:
            print(f"[SmartQueryHandler] Error getting beacon locations: {e}")
            return "Maaf, terjadi kesalahan saat mengambil data beacon."
    
    async def _get_device_activity(self, imei: str) -> Dict:
        """
        Get activity for a single device
        Hanya untuk device AKTIF
        """
        try:
            async with httpx.AsyncClient() as client:
                # 1. Validasi apakah IMEI adalah device aktif
                devices_res = await client.get(f"{self.base_url}/devices", timeout=30.0)
                ble_devices = devices_res.json().get('devices', [])
                ble_imeis = {d['imei'] for d in ble_devices}
                
                solar_res = await client.get(f"{self.base_url}/solar-tracker/devices", timeout=30.0)
                solar_devices = solar_res.json().get('devices', [])
                solar_imeis = {d['imei'] for d in solar_devices}
                
                # Check if IMEI is active
                if imei not in ble_imeis and imei not in solar_imeis:
                    return f"Device dengan IMEI {imei} tidak aktif atau tidak ditemukan"
                
                # 2. Get device activity
                res = await client.get(f"{self.base_url}/device-activity/{imei}", timeout=30.0)
                if res.status_code == 404:
                    return f"Device dengan IMEI {imei} tidak ditemukan"
                data = res.json()
                print(f"[SmartQueryHandler] Found activity for active device {imei}")
                return [data]
        except Exception as e:
            print(f"[SmartQueryHandler] Error getting device activity: {e}")
            return f"Maaf, terjadi kesalahan saat mengambil activity untuk IMEI {imei}."
    
    async def _get_all_activities(self) -> List[Dict]:
        """Get activities for all devices"""
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(f"{self.base_url}/all-device-activities", timeout=30.0)
                data = res.json()
                activities = data.get('devices', [])
                print(f"[SmartQueryHandler] Found {len(activities)} device activities")
                return activities
        except Exception as e:
            print(f"[SmartQueryHandler] Error getting all activities: {e}")
            return "Maaf, terjadi kesalahan saat mengambil data activity."
    
    async def _get_geofences(self) -> List[Dict]:
        """Get all geofences"""
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(f"{self.base_url}/api/geofence", timeout=30.0)
                # Response bisa langsung list atau dict dengan key 'data'
                if isinstance(res.json(), list):
                    geofences = res.json()
                else:
                    geofences = res.json().get('data', [])
                print(f"[SmartQueryHandler] Found {len(geofences)} geofences")
                return geofences
        except Exception as e:
            print(f"[SmartQueryHandler] Error getting geofences: {e}")
            return "Maaf, terjadi kesalahan saat mengambil data geofence."
    
    async def _get_solar_devices(self) -> List[Dict]:
        """Get all solar tracker devices"""
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(f"{self.base_url}/solar-tracker/devices", timeout=30.0)
                data = res.json()
                devices = data.get('devices', [])
                print(f"[SmartQueryHandler] Found {len(devices)} solar tracker devices")
                return devices
        except Exception as e:
            print(f"[SmartQueryHandler] Error getting solar devices: {e}")
            return "Maaf, terjadi kesalahan saat mengambil data solar tracker."
    
    def _extract_battery_filter(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract battery filter dari text
        Contoh:
        - "battery < 20" → operator: <, value: 20
        - "baterai di bawah 20%" → operator: <, value: 20
        - "battery 80" → operator: =, value: 80 (exact match)
        - "baterai 80%" → operator: =, value: 80 (exact match)
        
        Juga deteksi device type (ble/solar/all)
        """
        # Pattern dengan operator eksplisit (prioritas tinggi)
        patterns_with_operator = [
            (r'(battery|baterai)\s*(<|kurang dari|di bawah|dibawah)\s*(\d+)', '<'),
            (r'(battery|baterai)\s*(>|lebih dari|di atas|diatas)\s*(\d+)', '>'),
            (r'(battery|baterai)\s*(<=)\s*(\d+)', '<='),
            (r'(battery|baterai)\s*(>=)\s*(\d+)', '>='),
            (r'(battery|baterai)\s*(=|sama dengan)\s*(\d+)', '='),
        ]
        
        # Cek pattern dengan operator dulu
        for pattern, operator in patterns_with_operator:
            match = re.search(pattern, text)
            if match:
                value = int(match.group(3))
                
                # Deteksi device type dari query
                device_type = 'all'  # Default
                if any(kw in text for kw in ['ble', 'bluetooth']):
                    device_type = 'ble'
                elif any(kw in text for kw in ['solar', 'tracker']):
                    device_type = 'solar'
                
                return {
                    'operator': operator,
                    'value': value,
                    'device_type': device_type
                }
        
        # Pattern tanpa operator (exact match) - prioritas rendah
        # Contoh: "battery 80", "baterai 80%", "battery 80 persen"
        pattern_exact = r'(battery|baterai)\s+(\d+)\s*(%|persen)?'
        match = re.search(pattern_exact, text)
        if match:
            value = int(match.group(2))
            
            # Deteksi device type dari query
            device_type = 'all'  # Default
            if any(kw in text for kw in ['ble', 'bluetooth']):
                device_type = 'ble'
            elif any(kw in text for kw in ['solar', 'tracker']):
                device_type = 'solar'
            
            print(f"[SmartQueryHandler] Detected exact match battery filter: {value}%")
            
            return {
                'operator': '=',
                'value': value,
                'device_type': device_type
            }
        
        return None
    
    async def _filter_by_battery(self, battery_filter: Dict[str, Any]) -> Dict:
        """
        Filter devices by battery level across all device types
        Hanya menampilkan device AKTIF yang memenuhi kondisi baterai
        
        Args:
            battery_filter: Dict dengan 'operator' dan 'value'
            
        Returns:
            Grouped data by device type atau data spesifik per type
        """
        try:
            operator = battery_filter['operator']
            value = battery_filter['value']
            
            print(f"[SmartQueryHandler] Filtering by battery {operator} {value}%")
            
            # Deteksi device type dari query user
            device_type = battery_filter.get('device_type', 'all')
            
            ble_devices = []
            solar_devices = []
            
            async with httpx.AsyncClient() as client:
                # 1. Ambil list device AKTIF
                if device_type in ['all', 'ble']:
                    # Get active BLE devices
                    devices_res = await client.get(f"{self.base_url}/devices", timeout=30.0)
                    active_ble_devices = devices_res.json().get('devices', [])
                    active_ble_imeis = {d['imei'] for d in active_ble_devices}
                    
                    print(f"[SmartQueryHandler] Found {len(active_ble_imeis)} active BLE devices")
                    
                    # 2. Get all registration data
                    reg_res = await client.get(f"{self.base_url}/registration/all", timeout=30.0)
                    all_reg_data = reg_res.json().get('data', [])
                    
                    # 3. Filter hanya untuk IMEI device aktif dan Heartbeat data
                    heartbeat_data = {}
                    for item in all_reg_data:
                        imei = item.get('payload_id_1')
                        # Filter: Hanya IMEI yang ada di active devices
                        if imei in active_ble_imeis and item.get('payload_id_2') == 'Heartbeat':
                            battery = item.get('persentase_baterai')
                            if battery is not None:
                                # Ambil data terbaru per IMEI
                                if imei not in heartbeat_data or item.get('timestamp', '') > heartbeat_data[imei].get('timestamp', ''):
                                    heartbeat_data[imei] = item
                    
                    # 4. Apply battery filter
                    for imei, data in heartbeat_data.items():
                        battery = data.get('persentase_baterai')
                        if self._check_battery_condition(battery, operator, value):
                            # Enrich dengan info device
                            device_info = next((d for d in active_ble_devices if d['imei'] == imei), {})
                            enriched = {
                                'imei': imei,
                                'serial_number': device_info.get('serial_number', imei),
                                'device_type': 'BLE',
                                'persentase_baterai': battery,
                                'voltage': data.get('voltage'),
                                'timestamp': data.get('timestamp')
                            }
                            ble_devices.append(enriched)
                
                if device_type in ['all', 'solar']:
                    # Get active Solar Tracker devices
                    solar_devices_res = await client.get(f"{self.base_url}/solar-tracker/devices", timeout=30.0)
                    active_solar_devices = solar_devices_res.json().get('devices', [])
                    active_solar_imeis = {d['imei'] for d in active_solar_devices}
                    
                    print(f"[SmartQueryHandler] Found {len(active_solar_imeis)} active Solar devices")
                    
                    # Get all solar tracker data
                    solar_data_res = await client.get(f"{self.base_url}/solar-tracker/data", timeout=30.0)
                    all_solar_data = solar_data_res.json().get('data', [])
                    
                    # Filter hanya untuk IMEI device aktif
                    latest_solar_data = {}
                    for item in all_solar_data:
                        imei = item.get('payload_id_1')
                        # Filter: Hanya IMEI yang ada di active devices
                        if imei in active_solar_imeis:
                            battery = item.get('persentase_baterai')
                            if battery is not None:
                                # Ambil data terbaru per IMEI
                                if imei not in latest_solar_data or item.get('timestamp', '') > latest_solar_data[imei].get('timestamp', ''):
                                    latest_solar_data[imei] = item
                    
                    # Apply battery filter
                    for imei, data in latest_solar_data.items():
                        battery = data.get('persentase_baterai')
                        if self._check_battery_condition(battery, operator, value):
                            # Enrich dengan info device
                            device_info = next((d for d in active_solar_devices if d['imei'] == imei), {})
                            enriched = {
                                'imei': imei,
                                'serial_number': device_info.get('serial_number', imei),
                                'device_type': 'Solar Tracker',
                                'persentase_baterai': battery,
                                'speed_kmh': data.get('speed_kmh'),
                                'g_sensor_status': data.get('g_sensor_status'),
                                'latitude': data.get('latitude'),
                                'longitude': data.get('longitude'),
                                'timestamp': data.get('timestamp')
                            }
                            solar_devices.append(enriched)
            
            # Return results based on device_type
            total = len(ble_devices) + len(solar_devices)
            
            if total == 0:
                return f"Tidak ada device aktif dengan battery {operator} {value}%"
            
            print(f"[SmartQueryHandler] Found {len(ble_devices)} BLE and {len(solar_devices)} Solar devices with battery {operator} {value}%")
            
            # Format response based on device_type
            if device_type == 'all':
                # Return grouped format
                result = {
                    'grouped': True,
                    'total': total,
                    'battery_filter': {
                        'operator': operator,
                        'value': value
                    },
                    'summary': {
                        'ble_count': len(ble_devices),
                        'solar_count': len(solar_devices)
                    },
                    'groups': {}
                }
                if ble_devices:
                    result['groups']['Device BLE'] = ble_devices
                if solar_devices:
                    result['groups']['Device Solar Tracker'] = solar_devices
                return result
                
            elif device_type == 'ble':
                # Return hanya BLE
                return {
                    'device_type': 'BLE',
                    'count': len(ble_devices),
                    'battery_filter': {
                        'operator': operator,
                        'value': value
                    },
                    'devices': ble_devices
                }
                
            elif device_type == 'solar':
                # Return hanya Solar
                return {
                    'device_type': 'Solar Tracker',
                    'count': len(solar_devices),
                    'battery_filter': {
                        'operator': operator,
                        'value': value
                    },
                    'devices': solar_devices
                }
            
        except Exception as e:
            print(f"[SmartQueryHandler] Error filtering by battery: {e}")
            import traceback
            traceback.print_exc()
            return "Maaf, terjadi kesalahan saat memfilter device berdasarkan battery."
    
    def _check_battery_condition(self, battery: float, operator: str, value: float) -> bool:
        """Check if battery meets the condition"""
        if operator == '<':
            return battery < value
        elif operator == '>':
            return battery > value
        elif operator == '<=':
            return battery <= value
        elif operator == '>=':
            return battery >= value
        elif operator == '=':
            return battery == value
        return False
    
    async def _search_solar_devices(self, imei: Optional[str], keyword: Optional[str]) -> List[Dict]:
        """
        Search solar tracker devices by IMEI or keyword
        """
        try:
            # Get all solar devices
            async with httpx.AsyncClient() as client:
                res = await client.get(f"{self.base_url}/solar-tracker/devices", timeout=30.0)
                data = res.json()
                devices = data.get('devices', [])
            
            # Filter by IMEI if provided
            if imei:
                filtered = [d for d in devices if d.get('imei') == imei]
                if filtered:
                    print(f"[SmartQueryHandler] Found solar device with IMEI {imei}")
                    return filtered
                return f"Tidak ada solar tracker dengan IMEI {imei}"
            
            # Filter by keyword if provided
            if keyword:
                keyword_lower = keyword.lower()
                filtered = [
                    d for d in devices
                    if keyword_lower in str(d.get('imei', '')).lower() or
                       keyword_lower in str(d.get('serial_number', '')).lower()
                ]
                
                if filtered:
                    print(f"[SmartQueryHandler] Found {len(filtered)} solar devices matching '{keyword}'")
                    return filtered
                return f"Tidak ada solar tracker yang cocok dengan keyword '{keyword}'"
            
            return devices
            
        except Exception as e:
            print(f"[SmartQueryHandler] Error searching solar devices: {e}")
            return "Maaf, terjadi kesalahan saat mencari solar tracker."
