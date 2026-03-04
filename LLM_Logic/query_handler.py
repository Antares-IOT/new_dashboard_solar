import httpx
import re
from typing import Optional, Dict, List, Any

class QueryHandler:
    """
    Handler untuk memproses query dan filter data dari API
    Reusable untuk berbagai endpoint API
    """
    
    def __init__(self, api_url: str, keyword_filters: dict = None, field_filters: dict = None):
        """
        Args:
            api_url: URL endpoint API yang akan diquery
            keyword_filters: Dictionary untuk filter berdasarkan keyword
            field_filters: Dictionary untuk filter berdasarkan field numerik
        """
        self.api_url = api_url
        self.keyword_filters = keyword_filters or {}
        self.field_filters = field_filters or {}

    def detect_keyword_filters(self, text: str) -> Dict[str, Any]:
        """
        Deteksi filter berdasarkan keyword dalam text
        
        Args:
            text: Input text dari user
            
        Returns:
            Dictionary berisi field dan value yang terdeteksi
        """
        text = text.lower()
        applied = {}

        for field, mapping in self.keyword_filters.items():
            for value, keywords in mapping.items():
                if any(kw in text for kw in keywords):
                    applied[field] = value

        return applied

    def detect_expression_filters(self, text: str) -> List[tuple]:
        """
        Deteksi filter numerik (>, <, >=, <=, =)
        
        Args:
            text: Input text dari user
            
        Returns:
            List of tuples berisi (field, operator, value)
        """
        expr_filters = []
        patterns = [
            (r"(\w+)\s*>=\s*(\d+)", ">="),
            (r"(\w+)\s*<=\s*(\d+)", "<="),
            (r"(\w+)\s*>\s*(\d+)", ">"),
            (r"(\w+)\s*<\s*(\d+)", "<"),
            (r"(\w+)\s*=\s*(\d+)", "=")
        ]

        for pattern, operator in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                expr_filters.append((match[0], operator, int(match[1])))

        return expr_filters

    def detect_text_search(self, text: str) -> Optional[tuple]:
        """
        Deteksi pencarian text dalam field tertentu
        
        Args:
            text: Input text dari user
            
        Returns:
            Tuple (field, keyword) atau None
        """
        # Pattern untuk mencari: "field mengandung 'keyword'" atau "field 'keyword'"
        patterns = [
            r'(\w+)(?:\s+mengandung|\s+dengan)?\s*["\']([^"\']+)["\']',
            r'cari\s+(\w+)\s+["\']([^"\']+)["\']'
        ]
        
        for pattern in patterns:
            m = re.search(pattern, text.lower())
            if m:
                return (m.group(1), m.group(2).lower())
        
        return None

    async def fetch_data(self) -> Any:
        """
        Fetch data dari API endpoint
        
        Returns:
            Data dari API (biasanya list atau dict)
        """
        async with httpx.AsyncClient() as client:
            res = await client.get(self.api_url, timeout=30.0)
            data = res.json()
            
            # Handle jika response berisi key 'data' atau 'devices'
            if isinstance(data, dict):
                if 'data' in data:
                    return data['data']
                elif 'devices' in data:
                    return data['devices']
            
            return data

    def apply_filters(
        self, 
        data: List[Dict], 
        keyword_results: Dict, 
        expr_filters: List[tuple], 
        text_search: Optional[tuple]
    ) -> List[Dict]:
        """
        Apply semua filter ke data
        
        Args:
            data: List of dictionaries (data dari API)
            keyword_results: Hasil deteksi keyword filter
            expr_filters: Hasil deteksi expression filter
            text_search: Hasil deteksi text search
            
        Returns:
            Filtered data
        """
        filtered = data

        # Apply keyword filters
        for field, val in keyword_results.items():
            filtered = [item for item in filtered if item.get(field) == val]

        # Apply numeric expression filters
        for field, operator, value in expr_filters:
            if operator == ">":
                filtered = [x for x in filtered if x.get(field, 0) > value]
            elif operator == "<":
                filtered = [x for x in filtered if x.get(field, 0) < value]
            elif operator == ">=":
                filtered = [x for x in filtered if x.get(field, 0) >= value]
            elif operator == "<=":
                filtered = [x for x in filtered if x.get(field, 0) <= value]
            elif operator == "=":
                filtered = [x for x in filtered if x.get(field, 0) == value]

        # Apply text search filter
        if text_search:
            field, keyword = text_search
            filtered = [
                x for x in filtered
                if keyword in str(x.get(field, "")).lower()
            ]

        return filtered

    async def handle(self, user_text: str) -> Any:
        """
        Main handler untuk memproses query user
        
        Args:
            user_text: Input text dari user
            
        Returns:
            Filtered data atau pesan error
        """
        text = user_text.lower()

        # Deteksi semua jenis filter
        keyword_results = self.detect_keyword_filters(text)
        expr_filters = self.detect_expression_filters(text)
        text_search = self.detect_text_search(text)

        print(">> Keyword Filters:", keyword_results)
        print(">> Numeric Filters:", expr_filters)
        print(">> Text Search:", text_search)

        # Fetch data dari API
        try:
            data = await self.fetch_data()
        except Exception as e:
            print(f"Error fetching data: {e}")
            return "Maaf, terjadi kesalahan saat mengambil data."

        # Apply filters
        final = self.apply_filters(data, keyword_results, expr_filters, text_search)

        if not final:
            return "Tidak ada data yang cocok dengan permintaan Anda."

        return final