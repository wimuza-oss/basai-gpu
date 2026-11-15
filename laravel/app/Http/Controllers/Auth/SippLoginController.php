<?php

declare(strict_types=1);

namespace App\Http\Controllers\Auth;

use App\Exceptions\SippAuthenticationException;
use App\Http\Controllers\Controller;
use App\Http\Requests\Auth\SippLoginRequest;
use App\Services\Auth\SippAuthenticationService;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\View\View;

final class SippLoginController extends Controller
{
    public function __construct(
        private readonly SippAuthenticationService $authentication,
    ) {
    }

    public function create(Request $request): View|RedirectResponse
    {
        if ($request->session()->has('basai.auth.userid')) {
            return redirect()->route('basai.test');
        }

        return view('auth.basai-login');
    }

    public function store(SippLoginRequest $request): RedirectResponse
    {
        try {
            $user = $this->authentication->authenticate(
                $request->string('username')->toString(),
                (string) $request->input('password'),
            );
        } catch (SippAuthenticationException) {
            return back()
                ->withInput($request->safe()->only('username'))
                ->withErrors([
                    'username' => 'Layanan autentikasi SIPP sedang tidak tersedia.',
                ]);
        }

        if ($user === null) {
            return back()
                ->withInput($request->safe()->only('username'))
                ->withErrors([
                    'username' => 'Nama pengguna atau kata sandi tidak sesuai, atau akun tidak memiliki akses BAS-AI.',
                ]);
        }

        $request->session()->regenerate();

        $request->session()->put('basai.auth', [
            'userid' => $user->userid,
            'username' => $user->username,
            'fullname' => $user->fullname,
            'admin_basai' => $user->adminBasai,
        ]);

        return redirect()->intended(route('basai.test'));
    }

    public function destroy(Request $request): RedirectResponse
    {
        $request->session()->forget('basai.auth');
        $request->session()->invalidate();
        $request->session()->regenerateToken();

        return redirect()->route('basai.login');
    }
}
