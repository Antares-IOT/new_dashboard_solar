# 📚 Contoh Query untuk Semua Endpoint API

Dokumentasi lengkap contoh query natural language yang bisa digunakan di chatbot untuk mengakses semua endpoint API.

---

## 🔹 Device Endpoints

### 1. Total Device Count
**Endpoint:** `GET /devices/count`

**Contoh Query:**
```
berapa jumlah device?
berapa banyak perangkat?
total device
jumlah device online
ada berapa device?
```

**Response:**
```
Total device: 12
```

---

### 2. List Semua Device
**Endpoint:** `GET /devices`

**Contoh Query:**
```
tampilkan semua device
lihat semua perangkat
list device
daftar device
semua device
```

**Response:**
```
Ditemukan 12 data:

1. IMEI: 860137071625429, Serial: tes sensor
2. IMEI: 860137071526460, Serial: TAKU 240260-0
...
```

---

### 3. Device Info by IMEI
**Endpoint:** `GET /device-info/{imei}`

**Contoh Query:**
```
info device 860137071625429
serial number 860137071625429
```

**Response:**
```
Ditemukan 1 data:

1. IMEI: 860137071625429, Serial: tes sensor
```

---

### 4. Search Device
**Endpoint:** `GET /devices` (dengan filtering)

**Contoh Query:**
```
cari device 1234
tampilkan device TAKU
lihat device sensor
cari imei 8601
device mengandung '240'
```

**Response:**
```
Ditemukan 3 data:

1. IMEI: 860137071625429, Serial: tes sensor
2. IMEI: 123456789012345, Serial: device test
3. IMEI: 860137071240260, Serial: TAKU 240260-0
```

---

## 🔹 Registration Data Endpoints

### 5. Data Satu IMEI
**Endpoint:** `GET /registration/{imei}`

**Contoh Query:**
```
tampilkan data 860137071625429
data 860137071625429
860137071625429
imei 860137071625429
```

**Response:**
```
Ditemukan 150 data. Berikut 10 data pertama:

1. IMEI: 860137071625429, Type: GPS, Time: 2024-01-15 10:30:00, Battery: 85%, Location: (-6.123, 106.456)
2. IMEI: 860137071625429, Type: Heartbeat, Time: 2024-01-15 10:25:00, Battery: 85%
...
```

---

### 6. Data IMEI dengan Date Range
**Endpoint:** `POST /registration/{imei}/date-range`

**Contoh Query:**
```
data 860137071625429 dari 2024-01-01 sampai 2024-01-31
860137071625429 tanggal 2024-01-01 hingga 2024-01-31
tampilkan data 860137071625429 dari 2024-01-01 00:00:00 sampai 2024-01-31 23:59:59
data 860137071625429 mulai 2024-01-01 ke 2024-01-31
```

**Response:**
```
Ditemukan 45 data:

1. IMEI: 860137071625429, Type: GPS, Time: 2024-01-15 10:30:00, Battery: 85%
2. IMEI: 860137071625429, Type: Heartbeat, Time: 2024-01-15 10:25:00, Battery: 85%
...
```

---

## 🔹 GPS & Location Endpoints

### 7. GPS Terbaru
**Endpoint:** `GET /gps/{imei}/latest`

**Contoh Query:**
```
lokasi terakhir 860137071625429
gps terbaru 860137071625429
dimana posisi device 860137071625429
lokasi 860137071625429
posisi terbaru 860137071625429
koordinat terakhir 860137071625429
```

**Response:**
```
Ditemukan 1 data:

1. IMEI: 860137071625429, Type: GPS, Time: 2024-01-28 15:30:00, Battery: 85%, Location: (-6.123456, 106.789012)
```

---

### 8. GPS dengan Date Range
**Endpoint:** `GET /registration/{imei}/gps`

**Contoh Query:**
```
lokasi 860137071625429 dari 2024-01-01 sampai 2024-01-31
gps 860137071625429 tanggal 2024-01-01 hingga 2024-01-31
posisi 860137071625429 dari 2024-01-01 ke 2024-01-31
koordinat 860137071625429 mulai 2024-01-01 sampai 2024-01-31
```

**Response:**
```
Ditemukan 120 data. Berikut 10 data pertama:

1. IMEI: 860137071625429, Type: GPS, Time: 2024-01-15 10:30:00, Battery: 85%, Location: (-6.123456, 106.789012)
2. IMEI: 860137071625429, Type: GPS, Time: 2024-01-15 10:20:00, Battery: 84%, Location: (-6.123789, 106.789345)
...
```

---

## 🔹 Heartbeat & Battery Endpoints

### 9. Heartbeat Terbaru
**Endpoint:** `GET /heartbeat/{imei}/latest`

**Contoh Query:**
```
status battery 860137071625429
heartbeat terbaru 860137071625429
berapa battery device 860137071625429
voltage 860137071625429
baterai 860137071625429
tegangan 860137071625429
```

**Response:**
```
Ditemukan 1 data:

1. IMEI: 860137071625429, Type: Heartbeat, Time: 2024-01-28 15:30:00, Battery: 85%
```

---

## 🔹 Beacon Endpoints

### 10. Semua Lokasi Beacon
**Endpoint:** `GET /beacon/locations`

**Contoh Query:**
```
tampilkan semua beacon
list beacon
daftar beacon
lokasi beacon
beacon terdaftar
semua beacon location
```

**Response:**
```
Ditemukan 5 data:

1. major: 1234, minor: 5678, location_name: Gedung A, beacon_name: Beacon 1
2. major: 1234, minor: 5679, location_name: Gedung B, beacon_name: Beacon 2
...
```

---

## 🔹 Activity Endpoints

### 11. Activity Satu Device
**Endpoint:** `GET /device-activity/{imei}`

**Contoh Query:**
```
activity 860137071625429
aktivitas device 860137071625429
last activity 860137071625429
aktivitas terakhir 860137071625429
container activity 860137071625429
```

**Response:**
```
Ditemukan 1 data:

1. imei: 860137071625429, serial_number: tes sensor, last_activity: Container A
```

---

### 12. Activity Semua Device
**Endpoint:** `GET /all-device-activities`

**Contoh Query:**
```
tampilkan semua activity
list activity device
daftar aktivitas
semua activity
aktivitas semua device
```

**Response:**
```
Ditemukan 12 data:

1. imei: 860137071625429, serial_number: tes sensor, last_activity: Container A
2. imei: 860137071526460, serial_number: TAKU 240260-0, last_activity: Container B
...
```

---

## 🔹 Geofence Endpoints

### 13. Semua Geofence
**Endpoint:** `GET /api/geofence`

**Contoh Query:**
```
tampilkan semua geofence
list geofence
daftar area
geofence terdaftar
semua area geofence
```

**Response:**
```
Ditemukan 3 data:

1. id: 1, name: Area Pabrik, description: Area pabrik utama
2. id: 2, name: Area Gudang, description: Area gudang penyimpanan
...
```

---

## 🔹 Solar Tracker Endpoints

### 14. Semua Device Solar Tracker
**Endpoint:** `GET /solar-tracker/devices`

**Contoh Query:**
```
tampilkan semua solar tracker
list solar device
daftar panel surya
semua solar tracker
device solar
```

**Response:**
```
Ditemukan 5 data:

1. IMEI: 123456789012345, Serial: Solar Panel 1
2. IMEI: 123456789012346, Serial: Solar Panel 2
...
```

---

## 📊 Kombinasi Query

### Query dengan Multiple Conditions

**GPS + Date Range:**
```
lokasi 860137071625429 dari 2024-01-01 sampai 2024-01-31
```

**Data + Date Range:**
```
data 860137071625429 dari 2024-01-01 00:00:00 sampai 2024-01-31 23:59:59
```

**Search dengan Keyword:**
```
cari device yang mengandung 'TAKU'
```

---

## 🎯 Tips Penggunaan

### 1. Format Tanggal
Sistem mendukung berbagai format tanggal:
- `2024-01-01` (akan otomatis jadi 00:00:00 untuk start, 23:59:59 untuk end)
- `2024-01-01 00:00:00`
- `2024-01-01T00:00:00`

### 2. Kata Kunci Tanggal
Gunakan kata kunci berikut untuk date range:
- `dari ... sampai ...`
- `tanggal ... hingga ...`
- `mulai ... ke ...`
- `dari ... until ...`

### 3. IMEI
- IMEI harus 15 digit angka
- Bisa langsung ketik IMEI tanpa kata kunci
- Contoh: `860137071625429`

### 4. Keyword Search
- Bisa search partial IMEI atau serial number
- Case insensitive
- Contoh: `cari device 8601` akan match semua IMEI yang mengandung "8601"

### 5. Latest/Terbaru
Gunakan kata kunci berikut untuk data terbaru:
- `terbaru`
- `terakhir`
- `latest`
- `last`

---

## 🔍 Pattern Detection

Sistem mendeteksi intent berdasarkan keyword:

| Intent | Keywords |
|--------|----------|
| Device Count | berapa, jumlah, total, count |
| Device List | tampilkan, lihat, list, daftar, semua |
| GPS | gps, lokasi, location, posisi, koordinat, latitude, longitude |
| Heartbeat | heartbeat, battery, baterai, voltage, tegangan |
| Beacon | beacon, major, minor |
| Activity | activity, aktivitas, container |
| Geofence | geofence, area |
| Solar | solar, panel surya, tracker solar |

---

## ⚠️ Error Handling

Jika query tidak terdeteksi atau ada error:

**IMEI tidak ditemukan:**
```
Tidak ada data untuk IMEI 860137071625429
```

**Date range tidak ada data:**
```
Tidak ada data untuk IMEI 860137071625429 pada rentang tanggal tersebut
```

**Keyword tidak match:**
```
Tidak ada device yang cocok dengan keyword 'xyz'
```

**Error sistem:**
```
Maaf, terjadi kesalahan saat mengambil data.
```

---

## 💡 Contoh Skenario Penggunaan

### Skenario 1: Monitoring Device
```
1. "berapa jumlah device?" → Cek total device
2. "tampilkan semua device" → Lihat list device
3. "data 860137071625429" → Lihat detail satu device
4. "lokasi terakhir 860137071625429" → Cek posisi terbaru
5. "battery 860137071625429" → Cek status battery
```

### Skenario 2: Analisis Historical
```
1. "data 860137071625429 dari 2024-01-01 sampai 2024-01-31" → Data 1 bulan
2. "gps 860137071625429 dari 2024-01-01 sampai 2024-01-31" → Tracking lokasi
```

### Skenario 3: Troubleshooting
```
1. "cari device TAKU" → Cari device spesifik
2. "activity 860137071625429" → Cek last activity
3. "heartbeat 860137071625429" → Cek status device
```

### Skenario 4: Management
```
1. "tampilkan semua beacon" → Lihat beacon locations
2. "list geofence" → Lihat area terdaftar
3. "semua solar tracker" → Lihat solar devices
4. "semua activity" → Monitor semua device activity
```

---

## 📝 Testing Checklist

Gunakan checklist ini untuk testing:

- [ ] Device count query
- [ ] Device list query
- [ ] Device search by keyword
- [ ] Data by IMEI
- [ ] Data by IMEI + date range
- [ ] Latest GPS
- [ ] GPS by date range
- [ ] Latest heartbeat
- [ ] Beacon locations
- [ ] Device activity
- [ ] All activities
- [ ] Geofences
- [ ] Solar tracker devices
- [ ] AI fallback (pertanyaan umum)

---

## 🔋 Filter Berdasarkan Baterai

### 15. Filter Device dengan Kondisi Baterai
**Endpoint:** Multiple (menggunakan `/devices`, `/solar-tracker/devices`, `/registration/all`, `/solar-tracker/data`)

**Fitur:**
- Hanya menampilkan device AKTIF
- Support semua operator: <, >, <=, >=, =
- Support device type spesifik (BLE/Solar) atau semua
- Data baterai terbaru dari setiap device

**Contoh Query:**

#### A. Filter Baterai Kurang Dari (<)
```
tampilkan device dengan battery < 20
device dengan baterai kurang dari 20
device dengan baterai di bawah 20
device dengan baterai dibawah 20
```

#### B. Filter Baterai Lebih Dari (>)
```
tampilkan device dengan battery > 80
device dengan baterai lebih dari 80
device dengan baterai di atas 80
device dengan baterai diatas 80
```

#### C. Filter Baterai Kurang Dari atau Sama Dengan (<=)
```
tampilkan device dengan battery <= 50
device dengan baterai <= 50
```

#### D. Filter Baterai Lebih Dari atau Sama Dengan (>=)
```
tampilkan device dengan battery >= 80
device dengan baterai >= 80
```

#### E. Filter Baterai Sama Dengan (=) - Exact Match
```
tampilkan device dengan battery = 100
device dengan baterai sama dengan 100
device dengan battery 80
device dengan baterai 80%
device dengan battery 80 persen
```

#### F. Filter dengan Device Type Spesifik
```
tampilkan device BLE dengan battery < 20
device bluetooth dengan baterai kurang dari 20
tampilkan device solar dengan battery > 80
device tracker dengan baterai lebih dari 80
```

**Response Format (Tidak Spesifik):**
```json
{
  "grouped": true,
  "total": 5,
  "battery_filter": {
    "operator": "<",
    "value": 20
  },
  "summary": {
    "ble_count": 3,
    "solar_count": 2
  },
  "groups": {
    "Device BLE": [
      {
        "imei": "869100076975711",
        "serial_number": "TAKU 256017-0",
        "device_type": "BLE",
        "persentase_baterai": 19,
        "voltage": 3.28,
        "timestamp": "2025-11-14 19:19:02"
      }
    ],
    "Device Solar Tracker": [...]
  }
}
```

**Response Format (Spesifik BLE/Solar):**
```json
{
  "device_type": "BLE",
  "count": 3,
  "battery_filter": {
    "operator": "<",
    "value": 20
  },
  "devices": [...]
}
```

---

## 📅 Filter Device dengan Date Range

### 16. Tampilkan Device Aktif dalam Rentang Tanggal
**Endpoint:** Multiple (menggunakan `/devices`, `/solar-tracker/devices`, `/registration/all`, `/solar-tracker/data`)

**Fitur:**
- Hanya menampilkan device AKTIF
- Filter berdasarkan timestamp aktivitas terakhir
- Support device type spesifik atau semua
- Menampilkan summary count per kategori

**Contoh Query:**

#### A. Semua Device (Tidak Spesifik)
```
tampilkan device dari 2025-08-04 sampai 2025-10-22
device dari 2025-08-04 hingga 2025-10-22
lihat device tanggal 2025-08-04 ke 2025-10-22
```

#### B. Device BLE Spesifik
```
tampilkan device BLE dari 2025-08-04 sampai 2025-10-22
device bluetooth dari 2025-08-04 hingga 2025-10-22
```

#### C. Device Solar Spesifik
```
tampilkan device solar dari 2025-08-04 sampai 2025-10-22
device tracker dari 2025-08-04 hingga 2025-10-22
```

**Response Format:**
```json
{
  "grouped": true,
  "total": 16,
  "date_range": {
    "start": "2025-08-04 00:00:00",
    "end": "2025-10-22 23:59:59"
  },
  "summary": {
    "ble_count": 12,
    "solar_count": 4
  },
  "groups": {
    "Device BLE": [...],
    "Device Solar Tracker": [...]
  }
}
```

---

## 🎯 Kombinasi Query Advanced

### 17. Query dengan Multiple Conditions

**Contoh Kombinasi:**

#### A. Device Count dengan Type
```
berapa jumlah device BLE?
total device solar tracker
```

#### B. Device List dengan Type
```
tampilkan semua device BLE
list device solar tracker
```

#### C. GPS dengan Date Range
```
lokasi 869100076975711 dari 2024-01-01 sampai 2024-01-31
gps device dari 2024-01-01 hingga 2024-01-31
```

#### D. Search dengan Keyword
```
cari device TAKU
tampilkan device mengandung '240'
```

---

## 📊 Semua Operator yang Didukung

### Operator Baterai

| Operator | Contoh Query | Deskripsi |
|----------|--------------|-----------|
| **<** | `battery < 20` | Kurang dari |
| **>** | `battery > 80` | Lebih dari |
| **<=** | `battery <= 50` | Kurang dari atau sama dengan |
| **>=** | `battery >= 80` | Lebih dari atau sama dengan |
| **=** | `battery = 100` atau `battery 100` | Sama dengan (exact match) |

### Kata Kunci Alternatif

| Operator | Kata Kunci Indonesia |
|----------|---------------------|
| **<** | kurang dari, di bawah, dibawah |
| **>** | lebih dari, di atas, diatas |
| **=** | sama dengan, [angka saja], [angka]%, [angka] persen |

---

## 🔍 Pattern Detection Extended

Sistem mendeteksi intent berdasarkan keyword:

| Intent | Keywords | Device Type Support |
|--------|----------|-------------------|
| Device Count | berapa, jumlah, total, count | ✅ all/ble/solar |
| Device List | tampilkan, lihat, list, daftar, semua | ✅ all/ble/solar |
| Battery Filter | battery, baterai + operator | ✅ all/ble/solar |
| Date Range Filter | dari...sampai, tanggal...hingga | ✅ all/ble/solar |
| GPS | gps, lokasi, location, posisi, koordinat | ✅ all/ble/solar |
| Heartbeat | heartbeat, battery, baterai, voltage | ✅ BLE only |
| Beacon | beacon, major, minor | ✅ BLE only |
| Activity | activity, aktivitas, container | ✅ all/ble/solar |
| Geofence | geofence, area | ✅ N/A |
| Solar | solar, panel surya, tracker solar | ✅ Solar only |

---

## ⚡ Fitur Baru

### 1. **Pattern First + AI Fallback**
Sistem menggunakan pattern matching cepat terlebih dahulu, jika tidak match baru menggunakan AI untuk deteksi device type.

### 2. **Device Type Detection**
Otomatis mendeteksi apakah user meminta:
- Semua device (BLE + Solar)
- Hanya BLE
- Hanya Solar Tracker

### 3. **Active Device Only**
Semua query sekarang hanya menampilkan device AKTIF:
- Filter baterai: hanya device aktif
- GPS queries: validasi IMEI aktif
- Heartbeat queries: validasi IMEI aktif
- Activity queries: validasi IMEI aktif
- Device list: hanya device aktif

### 4. **Latest Data**
Sistem selalu mengambil data TERBARU untuk setiap device:
- GPS terbaru
- Heartbeat terbaru
- Baterai terbaru
- Activity terbaru

### 5. **Natural Language Support**
Query bisa menggunakan bahasa natural tanpa simbol:
```
battery 80        → sama dengan battery = 80
baterai 80%       → sama dengan battery = 80
battery 80 persen → sama dengan battery = 80
```

---

## 💡 Tips Penggunaan Extended

### 1. Format Tanggal
Sistem mendukung berbagai format tanggal:
- `2024-01-01` (akan otomatis jadi 00:00:00 untuk start, 23:59:59 untuk end)
- `2024-01-01 00:00:00`
- `2024-01-01T00:00:00`

### 2. Kata Kunci Tanggal
Gunakan kata kunci berikut untuk date range:
- `dari ... sampai ...`
- `tanggal ... hingga ...`
- `mulai ... ke ...`
- `dari ... until ...`

### 3. IMEI
- IMEI harus 15 digit angka
- Bisa langsung ketik IMEI tanpa kata kunci
- Contoh: `869100076975711`
- Sistem akan validasi apakah IMEI adalah device aktif

### 4. Keyword Search
- Bisa search partial IMEI atau serial number
- Case insensitive
- Contoh: `cari device 8601` akan match semua IMEI yang mengandung "8601"

### 5. Latest/Terbaru
Gunakan kata kunci berikut untuk data terbaru:
- `terbaru`
- `terakhir`
- `latest`
- `last`

### 6. Battery Filter
- Gunakan operator untuk kondisi spesifik
- Tanpa operator = exact match
- Support natural language (kurang dari, lebih dari, dll)

### 7. Device Type
- Tidak spesifik = tampilkan semua (BLE + Solar)
- Sebutkan "BLE" atau "bluetooth" = hanya BLE
- Sebutkan "solar" atau "tracker" = hanya Solar

---

## 🔍 Pattern Detection Priority

Sistem menggunakan prioritas berikut:

1. **Battery Filter** (Highest Priority)
   - Pattern dengan operator eksplisit (<, >, <=, >=, =)
   - Pattern tanpa operator (exact match)

2. **IMEI Detection**
   - 15 digit angka
   - Validasi device aktif

3. **Date Range Detection**
   - Pattern "dari...sampai"
   - Pattern "tanggal...hingga"

4. **Device Type Detection**
   - Pattern matching: ble, bluetooth, solar, tracker
   - AI fallback jika tidak ada pattern jelas

5. **Query Type Detection**
   - Device count, list, GPS, heartbeat, activity, dll

---

## ⚠️ Error Handling Extended

Jika query tidak terdeteksi atau ada error:

**IMEI tidak aktif:**
```
Device dengan IMEI 860137071625429 tidak aktif atau tidak ditemukan
```

**Date range tidak ada data:**
```
Tidak ada device yang aktif dari 2025-08-04 00:00:00 sampai 2025-10-22 23:59:59
```

**Battery filter tidak ada hasil:**
```
Tidak ada device aktif dengan battery < 20%
```

**Keyword tidak match:**
```
Tidak ada device yang cocok dengan keyword 'xyz'
```

**Error sistem:**
```
Maaf, terjadi kesalahan saat mengambil data.
```

---

## 💡 Contoh Skenario Penggunaan Extended

### Skenario 1: Monitoring Device dengan Battery Low
```
1. "berapa jumlah device?" → Cek total device
2. "tampilkan device dengan battery < 20" → Lihat device battery rendah
3. "tampilkan device BLE dengan battery < 20" → Fokus ke BLE saja
4. "lokasi terakhir 869100076975711" → Cek posisi device spesifik
```

### Skenario 2: Analisis Historical dengan Date Range
```
1. "tampilkan device dari 2025-08-04 sampai 2025-10-22" → Device aktif dalam periode
2. "gps device dari 2025-08-04 sampai 2025-10-22" → Tracking lokasi periode tersebut
3. "tampilkan device BLE dari 2025-08-04 sampai 2025-10-22" → Fokus BLE saja
```

### Skenario 3: Monitoring Battery Status
```
1. "tampilkan device dengan battery 100" → Device fully charged
2. "device dengan battery > 80" → Device siap operasi
3. "device solar dengan battery < 20" → Solar tracker perlu charging
```

### Skenario 4: Troubleshooting Device Aktif
```
1. "cari device TAKU" → Cari device spesifik
2. "activity 869100076975711" → Cek last activity
3. "heartbeat 869100076975711" → Cek status device
4. "lokasi terakhir 869100076975711" → Cek posisi terbaru
```

### Skenario 5: Management & Reporting
```
1. "berapa jumlah device BLE?" → Count BLE devices
2. "berapa jumlah device solar?" → Count Solar devices
3. "tampilkan device dengan battery <= 50" → Device perlu perhatian
4. "device dari 2025-11-01 sampai 2025-11-30" → Report bulanan
```

---

## 📝 Testing Checklist Extended

Gunakan checklist ini untuk testing:

**Basic Queries:**
- [ ] Device count query (all/ble/solar)
- [ ] Device list query (all/ble/solar)
- [ ] Device search by keyword
- [ ] Data by IMEI
- [ ] Data by IMEI + date range

**GPS Queries:**
- [ ] Latest GPS (validasi IMEI aktif)
- [ ] GPS by date range (validasi IMEI aktif)
- [ ] GPS all devices by date range (filter IMEI aktif)

**Heartbeat & Battery:**
- [ ] Latest heartbeat (validasi IMEI aktif)
- [ ] Battery filter < (all/ble/solar)
- [ ] Battery filter > (all/ble/solar)
- [ ] Battery filter <= (all/ble/solar)
- [ ] Battery filter >= (all/ble/solar)
- [ ] Battery filter = (all/ble/solar)
- [ ] Battery filter tanpa operator (exact match)

**Activity:**
- [ ] Device activity (validasi IMEI aktif)
- [ ] All activities

**Date Range:**
- [ ] Device list by date range (all/ble/solar)
- [ ] GPS by date range (all/ble/solar)

**Other Queries:**
- [ ] Beacon locations
- [ ] Geofences
- [ ] Solar tracker devices
- [ ] AI fallback (pertanyaan umum)

---

## 🚀 Performance Optimization

### Efficient API Calls
Sistem menggunakan strategi efisien:
- **3-4 API calls** untuk filter baterai (vs 14+ jika per device)
- **Cross-reference** antara device aktif dan data terbaru
- **Caching** data device aktif dalam satu request

### Data Freshness
- Selalu ambil data **terbaru** per device
- Filter berdasarkan **timestamp** terbaru
- Validasi **device aktif** sebelum query

---

**Last Updated:** 2025-12-01
**Version:** 3.0
**New Features:**
- ✅ Battery filter dengan semua operator
- ✅ Device type detection (all/ble/solar)
- ✅ Active device only validation
- ✅ Latest data per device
- ✅ Date range filter untuk device list
- ✅ Natural language support untuk battery filter
- ✅ Pattern first + AI fallback