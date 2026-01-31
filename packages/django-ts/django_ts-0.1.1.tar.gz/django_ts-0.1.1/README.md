# django-ts

Generate TypeScript constants and enums from Django models. No more copy-pasting values between backend and frontend.

## Why?

You've got Django models with constants:

```python
class Order(models.Model):
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_SHIPPED = "shipped"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_SHIPPED, "Shipped"),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
```

And you need the same values in TypeScript. You could copy them manually, forget to update one side, ship a bug, debug for an hour, then remember why you hate manual syncing.

Or just run:

```bash
python manage.py synctypes
```

## What you get

**constants.ts**
```typescript
export const Order = {
  STATUS_CONFIRMED: "confirmed",
  STATUS_PENDING: "pending",
  STATUS_SHIPPED: "shipped",
} as const
```

**enums.ts**
```typescript
export enum OrderStatusEnum {
  STATUS_PENDING = "pending", // Pending
  STATUS_CONFIRMED = "confirmed", // Confirmed
  STATUS_SHIPPED = "shipped", // Shipped
}
```

**index.ts**
```typescript
export * from "./constants";
export * from "./enums";
```

## Requirements

- Python 3.10+
- Django 4.0+

## Installation

```bash
pip install django-ts
```

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "django_ts_constants",
]
```

## Usage

```bash
# Generate to ./frontend/constants (default)
python manage.py synctypes

# Custom output directory
python manage.py synctypes --output ./frontend/src/generated

# Check mode - exits 1 if files are outdated (for CI)
python manage.py synctypes --check

# Dry run - see what would change without writing
python manage.py synctypes --dry-run
```

## What gets exported

The command scans your project's Django apps and extracts:

- **Uppercase constants** with underscores (`STATUS_PENDING = "pending"`)
  - Strings, integers, floats
- **Choice tuples** (`STATUS_CHOICES = [(value, label), ...]`)
  - Become TypeScript enums with labels as comments

Third-party packages are ignored. Only your project's apps are scanned.

## CI integration

```yaml
# GitHub Actions
- name: Check TypeScript constants are in sync
  run: python manage.py synctypes --check
```

If someone updates a Django constant but forgets to regenerate the TypeScript files, CI fails. No more "works on my machine" surprises.

## Development

```bash
git clone https://github.com/regiscamimura/django-ts 
cd django-ts

# Setup
uv venv && uv pip install -e ".[dev]"

# Test
pytest

# Lint
ruff check . && ruff format --check .
```

## License

MIT

---

Built by [Regis Camimura](https://github.com/regiscamimura)
