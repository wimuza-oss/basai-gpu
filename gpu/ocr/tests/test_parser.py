from app.engine import OcrLine, assemble_rows
from app.parser import parse_ktp


def test_noisy_synthetic_id_card_text():
    lines = [
        'PROVINSI DKI JAKARTA',
        'JAKARTA BARAT',
        'NIK : 3171234567890123',
        'Nama : MIRA SETIAWAN',
        'Tempat/Tgi Lahir : JAKARTA, 18-02-1986',
        'Jenis Kelamin : PEREMPUAN Gol Darah : B',
        'Alamat : 1 JL. PASTI CEPAT A7/66 - P1',
        'RT/RW : 007/008 aa',
        'Kel/Desa : PEGADUNGAN',
        'Kecamatan : KALIDERES',
        'Agama : ISLAM -h',
        'Status Perkawinan : KAWIN',
        'Pekerjaan : PEGAWAI SWASTA 2',
        'Kewarganegaraan : WNI JAKARTA BARAT',
        'Berlaku Hingga : -- : 22-02-2017 02-12-2012',
    ]
    result = parse_ktp([OcrLine(x, .94) for x in lines])
    assert result.fields == {
        'nik': '3171234567890123', 'nama': 'MIRA SETIAWAN',
        'tempat_lahir': 'JAKARTA', 'tanggal_lahir': '18-02-1986',
        'jenis_kelamin': 'PEREMPUAN', 'alamat': 'JL. PASTI CEPAT A7/66',
        'rt_rw': '007/008', 'kelurahan_desa': 'PEGADUNGAN',
        'kecamatan': 'KALIDERES', 'agama': 'ISLAM',
        'status_perkawinan': 'KAWIN', 'pekerjaan': 'PEGAWAI SWASTA',
        'kewarganegaraan': 'WNI', 'berlaku_hingga': '22-02-2017',
        'provinsi': 'DKI JAKARTA', 'kabupaten_kota': 'JAKARTA BARAT',
    }


def test_do_not_guess_birth_date_from_expiry():
    result = parse_ktp([OcrLine('Berlaku Hingga: 21-12-2027', .98)])
    assert result.fields == {'berlaku_hingga': '21-12-2027'}


def test_split_rows_into_horizontal_order():
    rows = assemble_rows([
        OcrLine('MIRA SETIAWAN', .91, (280, 100, 600, 125)),
        OcrLine('Nama', .97, (20, 100, 150, 124)),
        OcrLine('NIK', .99, (20, 50, 150, 75)),
        OcrLine('3171234567890123', .99, (280, 49, 600, 75)),
    ])
    assert [r.text for r in rows] == ['NIK 3171234567890123', 'Nama MIRA SETIAWAN']
    assert parse_ktp(rows).fields['nama'] == 'MIRA SETIAWAN'


def test_birth_label_split_across_three_lines():
    result = parse_ktp([
        OcrLine('Tempat/Tgl Lahir', .91),
        OcrLine('BANDUNG,', .91),
        OcrLine('19-07-1979', .93),
        OcrLine('Jenis Kelamin PEREMPUAN', .99),
    ])
    assert result.fields['tempat_lahir'] == 'BANDUNG'
    assert result.fields['tanggal_lahir'] == '19-07-1979'


def test_seven_priority_fields_can_be_extracted_from_separate_ocr_lines():
    # Data sintetis: foto/rekaman/PII asli tidak masuk ke repository.
    lines = [
        OcrLine('NIK: 1234567890123456', .98),
        OcrLine('Nama: SAKSI CONTOH', .97),
        OcrLine('Tempat/Tgl Lahir: BANDUNG, 12-05-1980', .96),
        OcrLine('Alamat: JL. CONTOH NO. 12', .95),
        OcrLine('Agama: ISLAM', .94),
        OcrLine('Pekerjaan: KARYAWAN SWASTA', .93),
    ]
    got = parse_ktp(lines).fields
    assert {key: got[key] for key in (
        'nik', 'nama', 'tempat_lahir', 'tanggal_lahir', 'alamat', 'agama', 'pekerjaan',
    )} == {
        'nik': '1234567890123456',
        'nama': 'SAKSI CONTOH',
        'tempat_lahir': 'BANDUNG',
        'tanggal_lahir': '12-05-1980',
        'alamat': 'JL. CONTOH NO. 12',
        'agama': 'ISLAM',
        'pekerjaan': 'KARYAWAN SWASTA',
    }


def test_regency_header_is_read_before_nik():
    lines = [
        OcrLine('PROVINSI JAWA BARAT', .98),
        OcrLine('KABUPATEN BANDUNG', .97),
        OcrLine('NIK: 1234567890123456', .99),
        OcrLine('Kel/Desa: CANGKUANG', .93),
        OcrLine('Kecamatan: SOREANG', .92),
    ]
    result = parse_ktp(lines)
    assert result.fields['provinsi'] == 'JAWA BARAT'
    assert result.fields['kabupaten_kota'] == 'KABUPATEN BANDUNG'
    assert result.fields['kelurahan_desa'] == 'CANGKUANG'
    assert result.fields['kecamatan'] == 'SOREANG'


def test_never_infer_city_from_signature_area_or_nationality():
    lines = [
        OcrLine('PROVINSI DKI JAKARTA', .95),
        OcrLine('NIK: 1234567890123456', .95),
        OcrLine('Kewarganegaraan WNI JAKARTA BARAT', .91),
        OcrLine('JAKARTA BARAT', .91),
    ]
    fields = parse_ktp(lines).fields
    assert fields['provinsi'] == 'DKI JAKARTA'
    assert 'kabupaten_kota' not in fields


def test_header_region_value_missing_stays_empty():
    result = parse_ktp([
        OcrLine('NIK: 1234567890123456', .94),
        OcrLine('Kabupaten Bandung', .94),
    ])
    assert 'kabupaten_kota' not in result.fields
    assert 'provinsi' not in result.fields
