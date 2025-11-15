# Best Dressed - AI Agent Instructions

## Project Overview
Best Dressed is a Django-based fashion social platform where users create and share outfits, manage personal wardrobes, browse clothing catalogs, and receive AI-powered outfit recommendations. The project uses OpenAI's API for personalized fashion advice.

## Architecture

### App Structure (Django Multi-App)
- **best_dressed_app**: Core wardrobe/outfit/recommendation features
- **users**: Authentication, registration (django-registration), password management
- **forum**: Community threads and posts for fashion discussions
- **api**: eBay marketplace integration for catalog items and GDPR-compliant user data deletion

### Key Models & Relationships
- `User` (Django built-in) ← OneToOne → `UserProfile` (bio, style_preferences, favorite_colors)
- `User` ← ForeignKey → `WardrobeItem` (personal wardrobe, optional link to catalog `Item`)
- `User` ← ForeignKey → `Outfit` (ManyToMany to `WardrobeItem` via `OutfitItem`)
- `Item`: Catalog items (shared pool, can be added by users or from eBay API)
- `Thread`/`Post`: Forum with nested posts, owner-based edit/delete permissions

### Data Flow Patterns
1. **Catalog → Wardrobe**: Users browse `Item` catalog → "Save to Wardrobe" creates `WardrobeItem` with `catalog_item` FK
2. **Wardrobe → Outfits**: Select multiple `WardrobeItem`s → create `Outfit` with ManyToMany relationship
3. **AI Recommendations**: Fetch user's wardrobe items + `UserProfile` → send to OpenAI API → stream results via AJAX

## Development Workflows

### Environment Setup
```powershell
# Install dependencies
pip install -r requirements.txt

# Database migrations (run after model changes)
python manage.py makemigrations
python manage.py makemigrations best_dressed_app  # Specific app if needed
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Testing Strategy
```powershell
# Run all tests with coverage
coverage run manage.py test

# Show coverage report
coverage report

# Run specific app tests
python manage.py test best_dressed_app
python manage.py test users
```

Tests use Django's `TestCase` with `Client` for view testing. See `best_dressed_app/test_dashboard_wardrobe_outfits.py` for comprehensive examples (1367 lines covering CRUD operations, authentication flows, form validation).

### CI/CD
- **GitHub Actions**: `.github/workflows/pytests.yml` runs on every push/PR
- **Linting**: Pylint runs on `best_dressed/` and `best_dressed_app/` (failures don't block CI: `|| true`)
- **Deployment**: Azure App Service via `.github/workflows/main_bestdressed.yml`

## Project-Specific Conventions

### Environment-Based Configuration (`best_dressed/settings.py`)
```python
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'DEV')  # DEV or PROD
if ENVIRONMENT == 'PROD':
    DEBUG = False
    SECRET_KEY = env_vars.get('SECRET_KEY')  # Required in prod
    DATABASES['default']['NAME'] = '/home/site/wwwroot/db.sqlite3'  # Azure persistence
else:
    DEBUG = True  # Hardcoded dev secret key
```
- **Prod requirements**: `SECRET_KEY`, `ALLOWED_HOSTS`, `SENDGRID_API_KEY` env vars
- **Static files**: WhiteNoise for prod serving; collected to `staticfiles/`

### Authentication Patterns
- Use `@login_required` decorator for protected views (redirects to `/accounts/login/`)
- Django-registration handles activation emails (7-day expiry: `ACCOUNT_ACTIVATION_DAYS = 7`)
- Custom views in `users/views.py` extend Django's auth views (e.g., `UserLoginView`, `UserPasswordResetView`)

### Form Handling Convention
```python
# Pattern used across views.py files
if request.method == "POST":
    form = MyForm(request.POST, instance=obj)  # instance= for edits
    if form.is_valid():
        new_obj = form.save(commit=False)
        new_obj.user = request.user  # Always set FK relationships
        new_obj.save()
        messages.success(request, "Success message")
        return redirect('view_name')
else:
    form = MyForm(instance=obj)  # GET: populate form
```
Always use Django messages framework for user feedback (`messages.success`, `messages.error`).

### AI Integration (`best_dressed_app/recommendation.py`)
```python
# OpenAI setup pattern
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
response = client.chat.completions.create(model="gpt-4", messages=[...])
```
- Recommendations view uses threading for non-blocking generation: `threading.Thread(target=generate_recommendations, ...)`
- AJAX endpoint (`generate_recommendations_ajax`) returns JsonResponse with streaming setup

### Template Architecture
- Base template: `templates/base.html` (all pages extend this)
- Shared components: `header.html`, `footer.html`, `bootstrap_js.html`
- App-specific templates in `templates/forum/`, `templates/registration/`, `templates/django_registration/`
- Custom template tags: `best_dressed_app/templatetags/wardrobe_extras.py` (e.g., `get_item` filter for dict access)

### URL Namespace Pattern
```python
# Main URLs include app URLs with namespace
path('forum/', include('forum.urls'))  # forum.urls defines 'thread_detail', etc.
path('', include('api.urls'))  # API at root for eBay webhooks

# Reverse in views
redirect('thread_detail', thread_id=thread.id)
```

## Critical Integration Points

### eBay API (`api/views.py`)
- **Webhook**: `POST /auth/ebay_market_delete/` handles GDPR account deletion
  - Challenge-response verification (SHA256 hash)
  - Signature validation using cryptography library + eBay public key
  - Requires `EBAY_VERIFICATION_TOKEN` and `EBAY_BASE64_AUTHORIZATION_TOKEN` env vars
- Uses `@csrf_exempt` for external webhooks

### Static Files (Production)
```python
# settings.py
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_URL = 'static/'
```
Run `python manage.py collectstatic` before deployment.

### Database Notes
- SQLite for both dev and prod (Azure: persisted at `/home/site/wwwroot/`)
- Use `select_related()`/`prefetch_related()` for FK/M2M optimization (see `forum/views.py`)
- Models use `related_name` for reverse lookups (e.g., `user.wardrobe_items.all()`)

## Common Patterns

### Ownership Checks
```python
# Pattern for edit/delete permissions
if not (request.user == obj.user or request.user.is_staff):
    messages.error(request, "Permission denied")
    return redirect('some_view')
```

### Model Auto-Fields
```python
# Item model auto-generates short_description from description in save()
def save(self, *args, **kwargs):
    if self.description:
        self.short_description = self.description[:72] + "..." if len(self.description) > 75 else self.description
    super().save(*args, **kwargs)
```

### AJAX Views
```python
# Return JsonResponse for async requests
return JsonResponse({'status': 'success', 'data': ...})
```

## Debugging Tips
- Check `db.sqlite3` exists and has correct path (prod vs dev)
- Verify migrations applied: `python manage.py showmigrations`
- For static file issues, ensure `collectstatic` ran and check `STATIC_ROOT`
- OpenAI errors: confirm `OPENAI_API_KEY` env var set
- Forum permission errors: check `request.user == obj.user or request.user.is_staff` patterns

## Building a New Feature
1. **Clarify Requirements**: Understand the feature scope and user stories. This may include questions being asked to the user before proceeding.
2. **Build tests first**: Write unit and integration tests covering the new feature.
3. **Plan the Feature**: Define models, views, templates, and URLs needed.
4. **Create/Update Models**: Add new models or fields in `models.py`, run migrations.
5. **Develop Views**: Implement view functions or class-based views in `views.py`, following existing patterns.
6. **Design Templates**: Create or modify HTML templates in the appropriate `templates/` directory.
7. **Set Up URLs**: Add URL patterns in the app's `urls.py` and include them in the main `urls.py`.
8. **Test the Feature**: Run the tests created in step 2 to ensure the feature works as expected.