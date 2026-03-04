# LLM Logic - Dokumentasi Sistem Query

## 📋 Daftar Isi
1. [Overview](#overview)
2. [Perubahan yang Dilakukan](#perubahan-yang-dilakukan)
3. [Struktur File](#struktur-file)
4. [Cara Kerja Sistem](#cara-kerja-sistem)
5. [Contoh Query](#contoh-query)
6. [API Endpoints](#api-endpoints)

---

## Overview

Sistem LLM Logic adalah sistem pemrosesan query natural language yang menggabungkan:
- **SmartQueryHandler**: Handler pintar untuk query device, IMEI, dan count
- **QueryHandler**: Handler untuk filtering data kompleks
- **AI Fallback**: Jika query tidak terdeteksi, diteruskan ke AI

---

## Perubahan yang Dilakukan

### 1. **API Endpoint `/registration/{imei}/date-range`**
- **Sebelum**: Menggunakan query parameters (GET)
- **Sekarang**: Menggunakan form data (POST)

```python
# Cara penggunaan baru:
POST /registration/{imei}/date-range
Form Data:
  - start_date: "2024-01-01 00:00:00" atau "2024-01-01T00:00:00"
  - end_date: "2024-01-31 23:59:59" atau "2024-01-31T23:59:59"
```

### 2. **SmartQueryHandler (Baru)**
File: `smart_query_handler.py`

Handler pintar yang dapat mendeteksi dan memproses:
- ✅ Query jumlah device: "berapa jumlah device?"
- ✅ Query list device: "tampilkan semua device"
- ✅ Query by IMEI: "tampilkan data 860137071625429"
- ✅ Query by IMEI + date range: "data 860137071625429 dari 2024-01-01 sampai 2024-01-31"
- ✅ Search device: "cari device 1234"

### 3. **Query Router (Diperbarui)**
File: `query_router.py`

Sistem routing dengan prioritas:
1. **SmartQueryHandler** - untuk query device/IMEI/count
2. **SolarHandler** - untuk query solar tracker
3. **RegistrationHandler** - untuk query dengan filter kompleks
4. **AI Fallback** - untuk pertanyaan umum

### 4. **API Response Formatting (Diperbaiki)**
File: `api.py`

- Menampilkan hingga 10 data (sebelumnya 5)
- Format response lebih informatif
- Support untuk response type: int, list, string
- Logging lebih detail untuk debugging

---

## Struktur File

```
LLM_Logic/
├── __init__.py                 # Python package marker
├── load_ai.py                  # Komunikasi dengan AI Gemma3:1b
├── query_handler.py            # Handler untuk filtering kompleks
├── smart_query_handler.py      # Handler pintar (BARU)
├── query_router.py             # Router untuk menentukan handler
└── README.md                   # Dokumentasi ini
```

---

## Cara Kerja Sistem

### Flow Diagram

```
User Input
    ↓
[Query Router]
    ↓
    ├─→ [SmartQueryHandler] ──→ Deteksi pattern & call API
    │   ├─ Device count?
    │   ├─ Device list?
    │   ├─ IMEI query?
    │   ├─ Date range?
    │   └─ Search keyword?
    │
    ├─→ [SolarHandler] ──→ Filter solar tracker data
    │
    ├─→ [RegistrationHandler] ──→ Filter registration data
    │
    └─→ [AI Fallback] ──→ Tanya ke Gemma3:1b
```

### SmartQueryHandler - Pattern Detection

#### 1. Device Count Query
**Pattern yang dideteksi:**
- "berapa banyak device"
- "berapa jumlah perangkat"
- "total device"
- "jumlah device online"

**API Call:** `GET /devices/count`

**Response:** Angka (integer)

#### 2. Device List Query
**Pattern yang dideteksi:**
- "tampilkan semua device"
- "lihat semua perangkat"
- "list device"
- "daftar device"

**API Call:** `GET /devices`

**Response:** List of devices dengan IMEI dan serial number

#### 3. IMEI Query
**Pattern yang dideteksi:**
- IMEI 15 digit: "860137071625429"
- "imei 860137071625429"
- "data 860137071625429"

**API Call:** `GET /registration/{imei}`

**Response:** List of registration data untuk IMEI tersebut

#### 4. IMEI + Date Range Query
**Pattern yang dideteksi:**
- "data 860137071625429 dari 2024-01-01 sampai 2024-01-31"
- "860137071625429 tanggal 2024-01-01 hingga 2024-01-31"

**API Call:** `POST /registration/{imei}/date-range`

**Response:** List of registration data dalam rentang tanggal

#### 5. Search Device Query
**Pattern yang dideteksi:**
- "cari device 1234"
- "tampilkan device 1234"
- "imei mengandung '1234'"

**API Call:** `GET /devices` + filtering

**Response:** List of devices yang cocok dengan keyword

---

## Contoh Query

### ✅ Query yang AKAN BERHASIL:

#### 1. Jumlah Device
```
User: "berapa jumlah device?"
Response: "Total device: 12"

User: "berapa banyak perangkat online?"
Response: "Total device: 12"
```

#### 2. List Semua Device
```
User: "tampilkan semua device"
Response: 
"Ditemukan 12 data:

1. IMEI: 860137071625429, Serial: tes sensor
2. IMEI: 860137071526460, Serial: TAKU 240260-0
..."
```

#### 3. Data Satu IMEI
```
User: "tampilkan data 860137071625429"
Response:
"Ditemukan 150 data. Berikut 10 data pertama:

1. IMEI: 860137071625429, Type: GPS, Time: 2024-01-15 10:30:00, Battery: 85%, Location: (-6.123, 106.456)
2. IMEI: 860137071625429, Type: Heartbeat, Time: 2024-01-15 10:25:00, Battery: 85%
..."
```

#### 4. Data IMEI dengan Rentang Tanggal
```
User: "data 860137071625429 dari 2024-01-01 00:00:00 sampai 2024-01-31 23:59:59"
Response:
"Ditemukan 45 data:

1. IMEI: 860137071625429, Type: GPS, Time: 2024-01-15 10:30:00, Battery: 85%
..."
```

#### 5. Cari Device dengan Keyword
```
User: "cari device 1234"
Response:
"Ditemukan 3 data:

1. IMEI: 860137071625429, Serial: tes sensor
2. IMEI: 123456789012345, Serial: device test
3. IMEI: 860910076975695, Serial: DEVICE 1234"
```

### ❌ Query yang TIDAK AKAN BERHASIL (akan diteruskan ke AI):

```
User: "apa itu IoT?"
Response: [Jawaban dari AI Gemma3:1b]

User: "bagaimana cara kerja GPS?"
Response: [Jawaban dari AI Gemma3:1b]
```

---

## API Endpoints

### 1. GET `/devices/count`
**Deskripsi:** Mendapatkan jumlah total device

**Response:**
```json
{
  "total_devices": 12
}
```

### 2. GET `/devices`
**Deskripsi:** Mendapatkan list semua device

**Response:**
```json
{
  "devices": [
    {
      "imei": "860137071625429",
      "serial_number": "tes sensor"
    },
    ...
  ],
  "total": 12
}
```

### 3. GET `/registration/{imei}`
**Deskripsi:** Mendapatkan semua data registration untuk satu IMEI

**Response:**
```json
{
  "data": [
    {
      "payload_id_1": "860137071625429",
      "payload_id_2": "GPS",
      "timestamp": "2024-01-15 10:30:00",
      "latitude": -6.123,
      "longitude": 106.456,
      "persentase_baterai": 85,
      ...
    },
    ...
  ]
}
```

### 4. POST `/registration/{imei}/date-range`
**Deskripsi:** Mendapatkan data registration untuk satu IMEI dalam rentang tanggal

**Form Data:**
- `start_date`: "2024-01-01 00:00:00" atau "2024-01-01T00:00:00"
- `end_date`: "2024-01-31 23:59:59" atau "2024-01-31T23:59:59"

**Response:**
```json
{
  "data": [...],
  "meta": {
    "start_date": "2024-01-01 00:00:00",
    "end_date": "2024-01-31 23:59:59",
    "total_records": 45
  }
}
```

### 5. GET `/device-info/{imei}`
**Deskripsi:** Mendapatkan serial number dari IMEI

**Response:**
```json
{
  "serial_number": "tes sensor"
}
```

---

## Debugging

### Logging
Semua handler memiliki logging untuk debugging:

```python
# Di console/terminal akan muncul:
[QueryRouter] Processing query: berapa jumlah device?
[QueryRouter] Using SmartQueryHandler
[SmartQueryHandler] Processing: berapa jumlah device?
[SmartQueryHandler] Device count: 12
[API /ask] Query handler returned: <class 'int'>
```

### Cara Melihat Log
1. Jalankan aplikasi: `python main.py`
2. Kirim query melalui chatbot
3. Lihat output di terminal/console

---

## Troubleshooting

### Problem: Query tidak terdeteksi
**Solusi:** 
- Periksa pattern di `SmartQueryHandler._is_device_count_query()` dll
- Tambahkan keyword baru jika perlu

### Problem: API endpoint error
**Solusi:**
- Periksa apakah endpoint API berjalan di `http://36.92.47.218:14523`
- Cek response format dari API

### Problem: Date range tidak bekerja
**Solusi:**
- Pastikan format tanggal: "YYYY-MM-DD HH:MM:SS" atau "YYYY-MM-DDTHH:MM:SS"
- Periksa apakah endpoint menggunakan POST dengan form data

---

## Pengembangan Lebih Lanjut

### Menambah Pattern Baru
Edit file `smart_query_handler.py`:

```python
def _is_new_query_type(self, text: str) -> bool:
    """Deteksi query type baru"""
    patterns = [
        r'pattern1',
        r'pattern2'
    ]
    return any(re.search(pattern, text) for pattern in patterns)
```

### Menambah Endpoint Baru
1. Tambahkan method di `SmartQueryHandler`
2. Update `handle()` method untuk memanggil method baru
3. Update `query_router.py` jika perlu

---

## Kontak & Support

Jika ada pertanyaan atau issue, silakan hubungi tim development.

**Last Updated:** 2024-01-28