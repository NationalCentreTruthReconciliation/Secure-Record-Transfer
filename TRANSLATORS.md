# 🌍 TRANSLATORS.md

Welcome! This guide is for anyone helping translate this project into other languages.

Whether you're translating UI text or contributing localized content, this document explains how and where to make your changes.

---

## 📝 How Translations Work

We use **Django's built-in internationalization (i18n)** framework to handle translations in both Python and JavaScript files.

All translatable strings are extracted into `.po` files and compiled into `.mo` files, which Django uses at runtime.

---

## 📂 Translation File Locations

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

## 🛠️ Extracting Strings

To extract translatable strings after making changes:

```bash
# For Python and templates
python manage.py makemessages -l hi

# For JavaScript
python manage.py makemessages -d djangojs -l hi
```

Replace `hi` with the target language code (e.g., `fr`, `es`, etc.).

---

## 🌐 Compiling Translations

After editing `.po` files, compile them so Django can use the updated translations:

```bash
python manage.py compilemessages
```

---

## 🐍 Python Translations (`gettext_lazy`)

In Python files, we use `gettext_lazy` (commonly aliased as `_`) to mark strings for translation.

We do this because we don’t want these strings to be translated immediately when the code is loaded. Instead, we want the translation to happen **later, when the page is being rendered** — for example, when displaying a model field label or a form error message.

This is important because the user’s language preference might not be known at import time (i.e., when the Python code is first loaded), but will be available at render time. Using `gettext_lazy` ensures that the correct translation is applied based on the active language at that moment.

## 💬 JavaScript Translations (`djangojs.po`)

We use `JavaScriptCatalog` to make translations available to frontend code.

You don’t need to worry about the setup — just translate the `djangojs.po` file as you would with `django.po`.

### Behind the scenes:
- `JavaScriptCatalog.as_view()` is set up in `urls.py`
- `{% javascript_catalog %}` is included in templates to load translations
- Strings in JS files are marked using `gettext()` or `_()` just like in Python

---

## ✅ Translating Strings

You can edit `.po` files manually, or use a GUI editor like:

- [Poedit](https://poedit.net/)
- [Lokalise](https://lokalise.com/)
- [Weblate](https://weblate.org/)

Make sure to save your changes and recompile (`compilemessages`) after editing.

---

## 🔍 Tips for Translators

- Be consistent with terminology
- Preserve placeholders like `{count}`, `{size}`, or `%s`
- Use the context (`msgctxt`) if provided
- Don’t translate code, only the user-facing text

---

## ❓ Need Help?

If you're unsure about a string or how to test your translations:

- Check the original usage in code/templates
- Ask in the project discussion or issues
- Look for comments in the `.po` file for extra context

---

Happy translating! 🎉

Let us know if you have suggestions for improving this guide.
