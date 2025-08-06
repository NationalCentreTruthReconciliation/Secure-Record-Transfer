# TRANSLATORS.md

Welcome! This guide is for anyone helping translate this project into other languages.

Whether you're translating UI text or contributing localized content, this document explains how and where to make your changes.

---

## How Translations Work

We use **Django's built-in internationalization (i18n)** framework to handle translations in both Python and JavaScript files.

All translatable strings are extracted into `.po` files and compiled into `.mo` files, which Django uses at runtime.

---

## Translation File Locations

- **Python & Templates:**
  Translations are stored in `locale/<language_code>/LC_MESSAGES/django.po`.

- **JavaScript files:**
  Translations go into `locale/<language_code>/LC_MESSAGES/djangojs.po`.

  Example:
  ```
  locale/
    hi/
      LC_MESSAGES/
        django.po       # Python/template strings
        djangojs.po     # JavaScript strings
  ```

---

## Extracting Strings

To extract translatable strings after making changes:

```bash
# For Python and templates
python manage.py makemessages -l hi

# For JavaScript
python manage.py makemessages -d djangojs -l hi

# Extract for all configured languages at once
python manage.py makemessages -a

# Extract JavaScript strings for all languages
python manage.py makemessages -d djangojs -a
```

Replace `hi` with the target language code (e.g., `fr`, `es`, etc.).

**Useful flags:**
- `-a, --all`: Extract strings for all configured languages
- `-d, --domain`: Specify domain (default: `django`, use `djangojs` for JavaScript)
- `-l, --locale`: Specify a particular language code
- `--help`: See all available options and flags

For a complete list of options, run:
```bash
python manage.py makemessages --help
```

---

## Compiling Translations

After editing `.po` files, compile them so Django can use the updated translations:

```bash
python manage.py compilemessages
```

---

## Python Translations (`gettext_lazy`)

In Python files, we use `gettext_lazy` (commonly aliased as `_`) to mark strings for translation.

We do this because we don’t want these strings to be translated immediately when the code is loaded. Instead, we want the translation to happen **later, when the page is being rendered** — for example, when displaying a model field label or a form error message.

This is important because the user’s language preference might not be known at import time (i.e., when the Python code is first loaded), but will be available at render time. Using `gettext_lazy` ensures that the correct translation is applied based on the active language at that moment.

## JavaScript Translations (`djangojs.po`)

We use `JavaScriptCatalog` to make translations available to frontend code.

You don’t need to worry about the setup — just translate the `djangojs.po` file as you would with `django.po`.

### Behind the scenes:
- `JavaScriptCatalog.as_view()` is set up in `urls.py`
- `{% javascript_catalog %}` is included in templates to load translations
- Strings in JS files are marked using `gettext()` or `_()`

---

## Complete Translation Workflow

Here's the step-by-step process for translating:

1. **Extract new strings**: `python manage.py makemessages -l hi`
2. **Edit the `.po` file** with your translations (using Poedit or text editor)
3. **Compile translations**: `python manage.py compilemessages`
4. **Test your changes** by switching language in the app
5. **Submit your translation updates** via pull request

---

## Testing Your Translations

After compiling your translations, you'll want to verify they work correctly:

### Switching Languages
- Look for a language selector in the app interface located in the header of the website

### Verification Checklist
- [ ] Text appears in your target language
- [ ] Placeholders are filled with actual values
- [ ] Text fits properly in the UI (not cut off)
- [ ] Special characters display correctly

### Troubleshooting
If translations don't appear:
1. Check you ran `compilemessages` after editing `.po` files
2. Restart the development server: `python manage.py runserver`
3. Clear your browser cache
4. Verify the `.mo` files were created in the locale directory

---

## Understanding Placeholders

Placeholders are variables that get filled with actual data. **Never translate the placeholder names**, only the surrounding text.

### Common Placeholder Types:

```po
# Named placeholders (recommended style)
msgid "File %(filename)s is too large (%(size)s MB)"
msgstr "फ़ाइल %(filename)s बहुत बड़ी है (%(size)s MB)"

# Simple placeholders
msgid "Welcome, %s!"
msgstr "स्वागत है, %s!"
```

### Key Rules:
- **Keep placeholder names exactly the same**: `%(filename)s` stays `%(filename)s`
- **You can reorder them** for your language's grammar: `"%(count)d files by %(user)s"` → `"%(user)s द्वारा %(count)d फ़ाइलें"`
- **Don't change the format specifiers**: `%s`, `%d`, `.2f` must stay exactly as written

---

## Translating Strings

You can edit `.po` files manually, or use a GUI editor like:

- [Poedit](https://poedit.net/)
- [Lokalise](https://lokalise.com/)
- [Weblate](https://weblate.org/)

Make sure to save your changes and recompile (`compilemessages`) after editing.

---

## Need Help?

If you're unsure about a string or how to test your translations:

- Check the original usage in code/templates
- Ask in the project discussion or issues
- Look for comments in the `.po` file for extra context

---

Happy translating!

Let us know if you have suggestions for improving this guide.
