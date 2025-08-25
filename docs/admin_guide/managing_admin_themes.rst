Managing Admin Interface Themes
=================================

The Secure Record Transfer application provides customizable themes for the admin interface. This allows administrators to customize the appearance of the admin interface to match organizational branding or improve usability.

.. contents:: Table of Contents
   :local:
   :depth: 2

.. note::
    Only superusers can access and manage admin interface themes. Regular admin users will not see the Theme Admin.

Changing the Theme
------------------

To change the currently active theme:

1. Log into the admin interface as a superuser
2. Navigate to **Admin Interface** → **Themes**

    .. image:: /images/admin_themes_navigation.png
       :alt: Admin themes navigation

3. You will see a list of available themes

   .. image:: /images/admin_themes_list.png
      :alt: List of available admin themes

4. Check the **Active** checkbox on your desired theme to enable it

.. note::
   Only one theme can be active at a time. Activating a new theme will automatically deactivate the previously active theme.

The changes will take effect immediately after saving.

Adding a New Theme
------------------

To create a new custom theme:

1. Navigate to **Admin Interface** → **Themes** in the admin
2. Click the **Add Theme** button

   .. image:: /images/add_new_theme_button.png
      :alt: Add new theme button

3. Make your desired changes to any of the theme settings (see :ref:`theme-form-sections` below)
4. Click **Save** to create the theme

Modifying an Existing Theme
---------------------------

To modify an existing theme:

1. Navigate to **Admin Interface** → **Themes** in the admin
2. Click on the theme you want to modify from the list

   .. image:: /images/edit_existing_theme.png
      :alt: Editing an existing theme

3. Make your desired changes to any of the theme settings (see :ref:`theme-form-sections` above for detailed descriptions)
4. Click **Save** to apply your modifications

.. _theme-form-sections:

Theme Form Sections and Settings
---------------------------------

The admin interface theme form is organized into several sections, each controlling different aspects of the admin interface appearance and behavior.

Basic Settings
~~~~~~~~~~~~~~

**Name**
   A descriptive name for the theme (e.g., "NCTR", "Dark Theme", "Custom Brand")

**Active**
   Checkbox to activate this theme. Only one theme can be active at a time.

Language Chooser
~~~~~~~~~~~~~~~~

.. note::
    Only languages which are set in the application settings will be available. This setting is not configurable.

**Active**
    Checkbox to enable/disable the language selection dropdown in the navigation bar.

**Control**
    Dropdown selection for the type of language selector:

    - ``Default Select`` - Standard dropdown
    - ``Minimal Select`` - More discreet dropdown

    .. image:: /images/admin_theme_language_chooser_select_type.png
         :alt: Admin theme language chooser select type

**Display**
   How language options are displayed:

   - ``code`` - Show language codes (e.g., "en", "fr")
   - ``name`` - Show language names (e.g., "English", "French")

Logo (not supported)
~~~~~~~~~~~~~~~~~~~~

.. note::
    Custom logos are not currently supported. The NCTR logo is used by default in the application.

**Logo**
    Upload field for a logo image file

**Max Width**
   Maximum width in pixels for the logo (e.g., 400)

**Max Height**
   Maximum height in pixels for the logo (e.g., 40)

**Color**
    Hex color code for the logo tint/overlay

**Visible**
   Checkbox to show/hide the logo

Favicon (not supported)
~~~~~~~~~~~~~~~~~~~~~~~

.. note::
    Custom favicons are not currently supported. The NCTR favicon is used by default in the application.

**Favicon**
   Upload field for a custom favicon (.ico file)

Title
~~~~~

**Title**
    The text displayed in the admin interface header

**Color**
    Hex color code for the title text

**Visible**
    Checkbox to show/hide the title in the header

    .. image:: /images/admin_theme_title_section.png
        :alt: Admin theme title section configuration

Header
~~~~~~

Controls the appearance of the admin interface header/ navigation bar.

**Background Color**
    Hex color code for the header background

**Text Color**
    Hex color code for header text

**Link Color**
    Hex color code for links in the header

**Link Hover Color**
    Hex color code for header links on hover

    .. image:: /images/admin_theme_header_section.png
        :alt: Admin theme header section configuratio

Breadcrumbs/Module Styling
~~~~~~~~~~~~~~~~~~~~~~~~~~

Controls the appearance of the breadcrumbs, app modules and fieldset headings.

.. image:: /images/admin_theme_breadcrumbs_example.png
    :alt: Example of breadcrumbs styling in admin interface

.. image:: /images/admin_theme_app_modules_example.png
    :alt: Example of app modules styling in admin interface

.. image:: /images/admin_theme_fieldset_headings_example.png
    :alt: Example of fieldset headings styling in admin interface

**Background Color**
   Hex color code for module box backgrounds

**Background Selected Color**
   Hex color code for selected/active module backgrounds

**Text Color**
   Hex color code for module text

**Link Color**
   Hex color code for module links

**Link Selected Color**
   Hex color code for selected module links

**Link Hover Color**
   Hex color code for module links on hover

**Rounded Corners**
   Checkbox to enable/disable rounded corners on module boxes

Generic Links
~~~~~~~~~~~~~

**Link Color**
    Hex color code for general links throughout the admin

**Link Hover Color**
    Hex color code for general links on hover

**Link Active Color**
    Hex color code for active/clicked links

.. image:: /images/admin_theme_generic_links_example_1.png
     :alt: Example of generic links styling in admin interface

.. image:: /images/admin_theme_generic_links_example_2.png
     :alt: Another example of generic links styling in admin interface

Save Button
~~~~~~~~~~~

**Button Background Color**
    Hex color code for save button backgrounds

**Button Background Hover Color**
    Hex color code for save buttons on hover

**Button Text Color**
    Hex color code for save button text

.. image:: /images/admin_theme_save_button_section.png
     :alt: Admin theme save button section configuration

Delete Button
~~~~~~~~~~~~~

**Button Background Color**
    Hex color code for delete button backgrounds

**Button Background Hover Color**
    Hex color code for delete buttons on hover

**Button Text Color**
    Hex color code for delete button text

.. image:: /images/admin_theme_delete_button_section.png
      :alt: Admin theme delete button section configuration

Navigation Bar
~~~~~~~~~~~~~~

**Foldable apps**
   Checkbox to allow collapsing/expanding app sections

.. image:: /images/admin_theme_navigation_bar_section.png
   :alt: Admin theme collapsable app sections

Related Objects Modal
~~~~~~~~~~~~~~~~~~~~~

**Active**
    Checkbox to enable/disable modal popups for related object editing.

.. figure:: /images/admin_theme_related_modal_example.png
    :alt: Example of related object modal popup in admin interface

    When related modal is enabled, editing objects opens in a modal popup.

.. figure:: /images/admin_theme_related_modal_disabled_example.png
    :alt: Example of related object editing in new window when modal is disabled

    When related modal is disabled, editing objects opens in a new window.

**Background Color**
   Hex color code for the modal background overlay

**Background Opacity**
   Decimal value for background transparency

**Rounded Corners**
   Checkbox to enable rounded corners on modal windows

**Close Button Visible**
   Checkbox to show/hide the close button on modals

Form Controls
~~~~~~~~~~~~~

**Sticky Submit**
    When enabled, form submit buttons (e.g., "Save", "Delete") will stick to the bottom of the screen when scrolling.

    .. image:: /images/admin_theme_sticky_submit_example.png
        :alt: Example of sticky submit buttons in admin interface

**Sticky Pagination**
    When enabled, pagination controls will stick to the bottom of the screen when scrolling.

    .. image:: /images/admin_theme_sticky_pagination_example.png
        :alt: Example of sticky pagination controls in admin interface

List Filter
~~~~~~~~~~~

**Highlight**
    Checkbox to enable highlighting of active filters

    .. image:: /images/admin_theme_list_filter_highlight_example.png
        :alt: Example of highlighted active filters in admin interface

**Dropdown**
    Checkbox to use dropdown style for filters instead of default links

    .. image:: /images/admin_theme_list_filter_dropdown_example.png
        :alt: Example of dropdown style filters in admin interface

**Sticky**
    Checkbox to make filters stick to the top when scrolling

    .. image:: /images/admin_theme_list_filter_sticky_example.png
        :alt: Example of sticky filters in admin interface

**Removal Links**
    Checkbox to show "x" links for removing individual filters

    .. image:: /images/admin_theme_list_filter_removal_links_example.png
        :alt: Example of filter removal links in admin interface

Change Form
~~~~~~~~~~~

**Fieldsets as tabs**
   Checkbox to display form fieldsets as tabs instead of sections

**Inlines as tabs**
   Checkbox to display inline forms as tabs

Recent Actions
~~~~~~~~~~~~~~

**Visible**
   Checkbox to show/hide the recent actions sidebar on the admin home page

   .. image:: /images/admin_theme_recent_actions_example.png
       :alt: Example of recent actions sidebar in admin interface
