"""Forms specific to the recordtransfer admin site"""

from django import forms
from django.utils.html import format_html
from django.utils.translation import gettext

from recordtransfer.models import (
    Submission,
)


class RecordTransferModelForm(forms.ModelForm):
    """Adds disabled_fields to forms.ModelForm"""

    disabled_fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = getattr(self, "instance", None)
        if instance and instance.pk and self.disabled_fields:
            # Disable fields
            for field in self.disabled_fields:
                if field in self.fields:
                    self.fields[field].disabled = True


class SubmissionModelForm(RecordTransferModelForm):
    """Form for editing Submissions."""

    class Meta:
        model = Submission
        fields = (
            "metadata",
            "user",
            "upload_session",
            "part_of_group",
            "uuid",
        )

    disabled_fields = ["metadata", "upload_session", "user", "part_of_group", "uuid"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if hasattr(self, "instance") and self.instance.metadata:
            # TODO: This makes the tiny link by the Metadata title in the Submission form.
            self.fields["metadata"].help_text = " | ".join(
                [
                    format_html('<a href="{}">{}</a>', url, gettext(text))
                    for url, text in [
                        (self.instance.get_admin_metadata_change_url(), "View or Change Metadata"),
                    ]
                ]
            )
        self.fields["metadata"].widget.can_add_related = False
