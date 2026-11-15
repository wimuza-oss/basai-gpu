# D5H — Protect BAS-AI Test Route

## Goal

Protect both existing `/basai/test` routes with the BAS-AI SIPP session and show
the authenticated SIPP identity plus a POST-only logout control.

## Route integration

Use the middleware class directly; no global alias is required.

For both existing named routes:

- `basai.test.show`
- `basai.test.transcribe`

append:

```php
->middleware(\App\Http\Middleware\RequireBasaiAuthentication::class)
```

Do not change their controller, HTTP method, route URI, or names.

## View integration

In the existing Blade rendered by `BasaiTestController::show`, add:

```blade
@include('auth.basai-userbar')
```

inside the page container near the top of the page.

## Security properties

- No password or SIPP password hash is stored in the session.
- Missing/malformed BAS-AI session redirects to `basai.login` and retains intended URL.
- Logout is POST-only and protected by Laravel CSRF.
- The existing STT controller/service pipeline remains unchanged.
