<!doctype html>
<html lang="id">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Masuk BAS-AI</title>
    <style>
        * { box-sizing: border-box; }
        body {
            margin: 0;
            min-height: 100vh;
            display: grid;
            place-items: center;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: #f5f6f8;
            color: #111827;
        }
        .card {
            width: min(420px, calc(100% - 32px));
            background: #fff;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            padding: 28px;
            box-shadow: 0 12px 30px rgba(0, 0, 0, .07);
        }
        h1 { margin: 0 0 6px; font-size: 24px; }
        .subtitle { margin: 0 0 24px; color: #6b7280; }
        label { display: block; margin: 14px 0 6px; font-weight: 600; }
        input {
            width: 100%;
            border: 1px solid #d1d5db;
            border-radius: 10px;
            padding: 11px 12px;
            font: inherit;
        }
        input:focus { outline: 2px solid #111827; outline-offset: 1px; }
        button {
            width: 100%;
            margin-top: 20px;
            border: 0;
            border-radius: 10px;
            padding: 12px 16px;
            font: inherit;
            font-weight: 700;
            cursor: pointer;
            background: #111827;
            color: #fff;
        }
        .error {
            margin: 16px 0 0;
            padding: 10px 12px;
            border-radius: 10px;
            background: #fef2f2;
            color: #991b1b;
            font-size: 14px;
        }
        .note { margin-top: 18px; color: #6b7280; font-size: 13px; }
    </style>
</head>
<body>
<main class="card">
    <h1>BAS-AI</h1>
    <p class="subtitle">Masuk menggunakan akun SIPP.</p>

    @if ($errors->any())
        <div class="error">{{ $errors->first() }}</div>
    @endif

    <form method="POST" action="{{ route('basai.login.store') }}" autocomplete="on">
        @csrf

        <label for="username">Nama pengguna</label>
        <input
            id="username"
            name="username"
            type="text"
            maxlength="30"
            value="{{ old('username') }}"
            autocomplete="username"
            required
            autofocus
        >

        <label for="password">Kata sandi</label>
        <input
            id="password"
            name="password"
            type="password"
            maxlength="255"
            autocomplete="current-password"
            required
        >

        <button type="submit">Masuk</button>
    </form>

    <p class="note">
        Akses tersedia untuk Super Administrator, Panitera/Wakil Panitera,
        Panitera Muda, dan Panitera Pengganti.
    </p>
</main>
</body>
</html>
