from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re

from app.engine import OcrLine


FIELDS = (
    'nik', 'nama', 'tempat_lahir', 'tanggal_lahir', 'jenis_kelamin', 'alamat',
    'rt_rw', 'kelurahan_desa', 'kecamatan', 'agama', 'status_perkawinan',
    'pekerjaan', 'kewarganegaraan', 'berlaku_hingga',
)
DATE = r'(\d{1,2}[-./]\d{1,2}[-./](?:19|20)\d{2})'
LABELS: list[tuple[str, re.Pattern[str]]] = [
    ('nik', re.compile(r'^(?:N[I1L]K)\b', re.I)),
    ('nama', re.compile(r'^NAMA\b', re.I)),
    ('birth', re.compile(r'^TEMPAT\s*[/|I.,-]?\s*T(?:GL|GI|6L|ANGGAL)\.?\s*LAHIR\b', re.I)),
    ('jenis_kelamin', re.compile(r'^JENIS\s+KELAMIN\b', re.I)),
    ('alamat', re.compile(r'^ALAMAT\b', re.I)),
    ('rt_rw', re.compile(r'^RT\s*[/|I-]\s*RW\b', re.I)),
    ('kelurahan_desa', re.compile(r'^(?:KEL\.?\s*[/|I-]\s*DESA|KELURAHAN\s*[/|I-]\s*DESA|KELURAHAN)\b', re.I)),
    ('kecamatan', re.compile(r'^KECAMATAN\b', re.I)),
    ('agama', re.compile(r'^AGAMA\b', re.I)),
    ('status_perkawinan', re.compile(r'^STATUS\s+PERKAWINAN\b', re.I)),
    ('pekerjaan', re.compile(r'^PEKERJAAN\b', re.I)),
    ('kewarganegaraan', re.compile(r'^KEWARGANEGARAAN\b', re.I)),
    ('berlaku_hingga', re.compile(r'^BERLAKU\s+HINGGA\b', re.I)),
]


@dataclass(frozen=True)
class ParseResult:
    fields: dict[str, str]
    confidences: dict[str, float]


def _date_valid(value: str) -> str | None:
    normalized = value.replace('/', '-').replace('.', '-')
    try:
        return datetime.strptime(normalized, '%d-%m-%Y').strftime('%d-%m-%Y')
    except ValueError:
        return None


def _normalize_field(key: str, value: str) -> str | None:
    value = re.sub(r'\s+', ' ', value).strip(' :|-;')
    if not value:
        return None
    upper = value.upper()
    if key == 'nik':
        digits = re.sub(r'[^0-9]', '', value)
        return digits if len(digits) == 16 else None
    if key == 'jenis_kelamin':
        if 'PEREMPUAN' in upper:
            return 'PEREMPUAN'
        if re.search(r'LAKI\s*[- ]?\s*LAKI', upper):
            return 'LAKI-LAKI'
        return None
    if key == 'rt_rw':
        match = re.search(r'(\d{1,3})\s*[/|I-]\s*(\d{1,3})', value)
        return f'{match[1]}/{match[2]}' if match else None
    if key in ('agama', 'kewarganegaraan', 'status_perkawinan'):
        choices = {
            'agama': ('ISLAM', 'KRISTEN', 'KATOLIK', 'HINDU', 'BUDDHA', 'KONGHUCU'),
            'kewarganegaraan': ('WNI', 'WNA'),
            'status_perkawinan': ('BELUM KAWIN', 'CERAI HIDUP', 'CERAI MATI', 'KAWIN'),
        }[key]
        for choice in choices:
            if re.search(r'\b' + re.escape(choice) + r'\b', upper):
                return choice
        return None
    if key in ('tanggal_lahir', 'berlaku_hingga'):
        if key == 'berlaku_hingga' and 'SEUMUR HIDUP' in upper:
            return 'SEUMUR HIDUP'
        match = re.search(DATE, value)
        return _date_valid(match.group(1)) if match else None
    if key == 'alamat':
        value = re.sub(r'^\d+\s+(?=(?:JL\.?|JALAN)\b)', '', value, flags=re.I)
        value = re.sub(r'\s+-\s+[A-Z]\d{0,2}\s*$', '', value, flags=re.I)
    if key == 'pekerjaan':
        value = re.sub(r'\s+[0-9]{1,2}$', '', value)
    return value.strip() if value.strip() else None


def _parse_birth(value: str) -> dict[str, str]:
    # Jangan tebak tanggal lahir menggunakan tanggal lain (berlaku hingga/cetak).
    match = re.search(DATE, value)
    if not match:
        return {}
    city = value[:match.start()].strip(' ,:;|-')
    date = _date_valid(match.group(1))
    result = {}
    if city and not re.search(r'\d{3,}', city):
        result['tempat_lahir'] = city
    if date:
        result['tanggal_lahir'] = date
    return result


def parse_ktp(lines: list[OcrLine]) -> ParseResult:
    result: dict[str, str] = {}
    scores: dict[str, float] = {}
    for i, line in enumerate(lines):
        text = line.text.replace('：', ':').strip()
        for key, pattern in LABELS:
            match = pattern.match(text)
            if not match:
                continue
            value = text[match.end():].lstrip(' :|-;')
            # Paddle sering mengeluarkan label dan value dalam kotak berbeda/baris berikutnya.
            if not value and key != 'birth' and i + 1 < len(lines) and not any(p.match(lines[i+1].text.strip()) for _, p in LABELS):
                value = lines[i+1].text.strip()
            if key == 'birth':
                if not re.search(DATE, value):
                    continuation = []
                    for followup in lines[i+1:i+3]:
                        if any(p.match(followup.text.strip()) for _, p in LABELS):
                            break
                        continuation.append(followup.text.strip())
                    value = ' '.join([value, *continuation]).strip()
                for birth_key, birth_value in _parse_birth(value).items():
                    if birth_key not in result or line.confidence > scores[birth_key]:
                        result[birth_key] = birth_value
                        scores[birth_key] = line.confidence
                break
            parsed = _normalize_field(key, value)
            if parsed is not None and (key not in result or line.confidence > scores[key]):
                result[key] = parsed
                scores[key] = line.confidence
            break
    # NIK tanpa label boleh dipakai hanya bila 16 digit kontinu dan tanpa koreksi karakter.
    if 'nik' not in result:
        for line in lines:
            match = re.search(r'(?<!\d)(\d{16})(?!\d)', line.text)
            if match:
                result['nik'] = match.group(1)
                scores['nik'] = line.confidence * .8
                break
    return ParseResult(result, scores)
