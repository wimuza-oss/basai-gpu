<?php

declare(strict_types=1);

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\View;
use Symfony\Component\HttpFoundation\Response;

final class RequireBasaiAuthentication
{
    public function handle(Request $request, Closure $next): Response|RedirectResponse
    {
        $auth = $request->session()->get('basai.auth');

        if (! is_array($auth)
            || ! isset($auth['userid'], $auth['username'], $auth['fullname'])
            || ! is_numeric($auth['userid'])
            || trim((string) $auth['username']) === ''
            || trim((string) $auth['fullname']) === '') {
            $request->session()->forget('basai.auth');

            return redirect()->guest(route('basai.login'));
        }

        $normalized = [
            'userid' => (int) $auth['userid'],
            'username' => (string) $auth['username'],
            'fullname' => (string) $auth['fullname'],
            'admin_basai' => (bool) ($auth['admin_basai'] ?? false),
        ];

        $request->attributes->set('basai.auth', $normalized);
        View::share('basaiAuth', $normalized);

        return $next($request);
    }
}
