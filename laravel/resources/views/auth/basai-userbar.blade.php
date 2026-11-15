@php
    /** @var array{userid:int,username:string,fullname:string,admin_basai:bool}|null $basaiAuth */
    $basaiAuth = $basaiAuth ?? session('basai.auth');
@endphp

@if (is_array($basaiAuth))
    <div class="basai-userbar" role="region" aria-label="Identitas pengguna BAS-AI">
        <div class="basai-userbar__identity">
            <strong>{{ $basaiAuth['fullname'] ?? $basaiAuth['username'] ?? 'Pengguna BAS-AI' }}</strong>
            <span>
                {{ $basaiAuth['username'] ?? '' }}
                @if (!empty($basaiAuth['admin_basai']))
                    · Administrator BAS-AI
                @endif
            </span>
        </div>

        <form method="POST" action="{{ route('basai.logout') }}">
            @csrf
            <button type="submit" class="basai-userbar__logout">Logout</button>
        </form>
    </div>

    <style>
        .basai-userbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            margin: 0 0 20px;
            padding: 12px 14px;
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            background: #fff;
        }

        .basai-userbar__identity {
            display: grid;
            gap: 2px;
        }

        .basai-userbar__identity span {
            color: #6b7280;
            font-size: 13px;
        }

        .basai-userbar__logout {
            border: 1px solid #d1d5db;
            border-radius: 8px;
            padding: 8px 12px;
            background: #fff;
            color: #111827;
            font: inherit;
            font-weight: 600;
            cursor: pointer;
        }
    </style>
@endif
