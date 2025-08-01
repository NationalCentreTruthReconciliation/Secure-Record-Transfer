The Submission Form
===================

The Submission Form serves as the heart of the public-facing application, where metadata about
records can be provided by donors and files can be uploaded for transfer to the institution.

A submission can be initiated by clicking on either "Submit" on the navigation bar or the "Submit
Your Records" button on the homepage. This will take the donor to the submission form.

.. image:: images/access_submission_form.webp
    :alt: How to access the submission form


Form Overview
#############

The Submission Form is divided into multiple steps to simplify the submission process. At the bottom of each step, there are three navigation buttons: **Next Step**, **Previous Step**, and **Save**. You can click **Next Step** to proceed to the next step, **Previous Step** to go back, and **Save** to save your progress and return to the form later.

.. image:: images/form_navigation.webp
    :alt: Navigation buttons on the submission form

For every step of the Submission Form, the data entered is saved so the donor can navigate back and
forward in the form without losing their data. This includes file uploads in
:ref:`Step 8: Upload Files`, which are saved on the server upon selection.


On the left side of the page, a progress bar visually indicates which step of the submission process the donor is currently on. This helps the donor track their progress as they move through the form.

.. image:: images/submission_form_progress_bar.webp
    :alt: Progress Bar on the submission form

Throughout the form, grey information icons (i) exist next to many fields. Helpful tooltips with
additional guidance on how to complete each field are displayed when the mouse hovers over these
icons.

.. image:: images/mouse_over_help_icon.webp
    :alt: Help icons on the submission form

Fields marked with a red asterisk (*) are required. These fields must be completed before
proceeding to the next step of the form. The rest of the fields are optional.

Certain fields are validated after the **Next Step** button is clicked. If any required fields have
been missed or invalid data has been entered, error messages will be shown on top of each relevant
field. These errors prevent the donor from proceeding to the next step until they are corrected.

.. image:: images/form_error.webp
    :alt: Error message on the submission form



Step 1: Legal Agreement
#######################

To fill out the form, the legal agreement must first be accepted. This agreement outlines the legal
terms and conditions that the donor must agree to before continuing with the rest of the form.

.. image:: images/submission_step_1.webp
    :alt: Step 1 of the submission form


Step 2: Contact information
###########################

This step gathers contact information from the donor.

.. image:: images/submission_step_2.webp
    :alt: Step 2 of the submission form

If you wish to avoid entering your contact details repeatedly across multiple submissions, you may add this information to your profile on the :ref:`Contact Information Tab` of the Profile page. Once saved in your profile, these fields will be automatically populated each time you start a new submission.

.. image:: images/submission_step_2_prefilled.webp
    :alt: Step 2 of the submission form prefilled

During the submission process, when you complete the Contact Information step, you will also be prompted with an option to "Save and Continue." Choosing this will save your contact information to your profile, so it can be auto-filled for future submissions.

If you prefer not to save your contact information at this time, you can simply click "Continue without saving." You will still have the option to add or update your contact information later through your profile page. Additionally, the next time you make a submission, you will be prompted again to save your contact information if it is not already stored in your profile.


.. image:: images/submission_step_2_save_modal.webp
    :alt: Step 2 of the submission form save modal


Step 3: Record Source information
#################################

Here, the donor inputs information about who is submitting the records. If the donor is submitting
records themselves, they can leave the default "No" selected for the "Submitting on behalf of an
organization/another person" field and simply click **Next Step**.

.. image:: images/submission_step_3_not_on_behalf.webp
    :alt: Step 3 of the submission form, not submitting on behalf of another person or organization

If the donor is submitting the records on behalf of another person or an institution, they can
select "Yes" for that field instead. This will reveal additional fields where they can provide
information about the organization or person they are submitting the records for. CAAIS includes
fields for adding notes about the source. If the donor feels inclined
to include this information, they can do so in the relevant optional fields.

.. image:: images/submission_step_3_on_behalf.webp
    :alt: Step 3 of the submission form, submitting on behalf of another person or organization

If the relevant source role or source type is not present in the dropdown, the donor can select
"Other" for either field and a text box will appear where they can enter their own source type or
role.

.. image:: images/submission_step_3_other_source.webp
    :alt: Step 3 of the submission form, selecting "Other" for source type or role

More information about the source types and roles in this step can be found on :ref:`Adding Source
Types` and :ref:`Adding Source Roles` respectively.

Step 4: Record Description
##########################

In this step, the donor is asked for a very brief description of their transfer/records. They must
enter four pieces of information:

- A title
- The start and end date of the records

    *   If the records span only a single date, the donor can select just one date
    *   They can select "Date is approximated" if the date is not exact, or if they are not sure of
        the exact date

- The languages of the records
- A brief description of what the records contain


Donors can optionally provide information about who has had custody or ownership of the records in the past before the current submission in the **Custodial History** field.

.. image:: images/submission_step_4.webp
    :alt: Step 4 of the submission form

By default, a date widget is used to select the start and end dates. To allow donors to enter dates
manually, the date widget can be disabled by modifying :ref:`USE_DATE_WIDGETS`.


Step 5: Record Rights and Restrictions
######################################

This optional step allows the donor to enter any rights applying to their records. Unlike previous sections, donors can skip this step if they're unsure about the rights status of their materials.

If donors wish to provide rights information, they can select one or more types of rights from the dropdown menu. If the appropriate type isn't listed, they can select "Other" and specify their own type. The **+ More** button allows adding multiple rights (useful when different rights apply to different records), and the **- Remove** button can remove entries.

If the donor is unsure about which right(s) apply to their records, they can click the link in the Overview section at the top of the form. This will open a description for each type of right in a new tab.
More information about the rights in this step can be found on :ref:`Adding Rights Types`.

.. image:: images/submission_step_5.webp
    :alt: Step 5 of the submission form


Once you associate a right with the submission, you can also add Notes for that specific right to provide additional context or clarification about how it applies to your records.

.. image:: images/submission_step_5_notes.webp
    :alt: Step 5 of the submission form notes


Step 6: Identifiers
###################

If the donor has other identifiers that apply to their records, such as an ISBN, or a barcode
number, they can put those here. They are not required to enter any here, so can skip to the next
step if needed.

Similar to the Rights form, donors can add or remove identifiers as needed.

.. image:: images/submission_step_6.webp
    :alt: Step 6 of the submission form


Step 7: Assign Submission to Group
##################################

If the donor is splitting their submission out into multiple batches, or if they just want to
associate their submission with a group of other submissions they have or will make, they can do so
here. They can select previous groups from the dropdown, or create a new one by clicking on the
**Add New Group** button.

.. image:: images/submission_step_7.webp
    :alt: Step 7 of the submission form

If you are not sure about the purpose of creating these groups, you can click on the link provided at the bottom of the form saying "Why would I want to make a group?" This will take you to a FAQ section that explains the benefits and use cases for grouping submissions.

.. image:: images/submission_step_7_faq_help.webp
    :alt: Step 7 of the submission form FAQ help


Clicking on the **Add New Group** button will open a modal where the donor can enter a name and
description for the group. Clicking **Create** will create a new group and auto-select it in the **Assigned group** dropdown.

Groups can also be accessed later from the :ref:`Submission Groups` table on the user profile page.

.. image:: images/submission_step_7_add_group.webp
    :alt: Step 7 of the submission form, adding a new group


Step 8: Upload Files
####################

This is where the donor can add files to their submission. They must include at least one file to
make a submission. They can add files to the file drop zone by clicking on "browse files" or by
dragging and dropping files into it. Only accepted file formats can be uploaded.

Users can open the dropdown button labeled "Accepted File Formats" to see which file types are supported for upload.

.. image:: images/submission_step_8_accepted_file_types.webp
    :alt: Step 8 of the submission form accepted file types

Any additional notes that did not fit in the previous steps can be added in the "Other Notes"
field.

.. image:: images/submission_step_8.webp
    :alt: Step 8 of the submission form

A preview of an uploaded file can be seen by clicking on its file icon. The donor can also remove
uploaded files by clicking on the (x) icon.

At the bottom of this section, there is also an indicator showing how many megabytes (MB) of files the donor can still upload. This helps donors keep track of their remaining upload limit as they add or remove files.

.. image:: images/submission_step_8_uploaded_file.webp
    :alt: Step 8 of the submission form, an uploaded file


Step 9: Review
##############

On this step, the donor can review all the information they have entered in the previous steps. If
they need to make any changes, they can click on the **Go to step** button next to the step they
want to edit. This will take them back to that step.

.. image:: images/submission_step_9.webp
    :alt: Step 9 of the submission form


After making any necessary changes, the donor can click on the **Review** button to go back to the review step.

When the donor goes back to a previous step, the **Save** button remains available. This allows the donor to save their updated progress at any point, reopen the form later, return to the review step, and submit when ready.

.. image:: images/submission_step_9_return_to_review.webp
    :alt: Step 9 of the submission form, returning to the review step

If the donor is satisfied with the information they have entered, they can click on the **Submit**
button to submit their records.


After Submission
################

After successfully submitting the form, the donor is redirected directed to a thank you page
confirming their submission. The system then automatically:

1. Sends notification emails to all staff users who have opted to receive bag updates
2. Sends a confirmation email to the donor with details of their submission

.. image:: images/submission_thank_you.webp
    :alt: Thank you page after submitting the form