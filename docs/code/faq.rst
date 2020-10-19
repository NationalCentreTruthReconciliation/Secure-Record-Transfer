FAQ
===

**Q: How can I modify the HTML report used to generate HTML CAAIS reports?**

- The HTML report template can be found at
  :code:`recordtransfer/templates/recordtransfer/report/metadata_report.html`

**Q: How can I modify the HTML Emails sent to users and archivists?**

- The HTML email templates can be found at :code:`recordtransfer/templates/recordtransfer/email`

**Q: Why do you use a custom** :code:`FileUploadHandler` ?

- This is because the user may hit the file upload endpoint multiple times depending on how large
  their transfer is. With the default :code:`TemporaryFileUploadHandler`, Django disposes of the
  temporary file after the view function returns, and we need the file to stick around longer so
  that we can copy it into a bag after the user's transfer finishes. This is done in a background
  task to minimize application slow down, and it was simplest to have all the files uploaded and on
  disk before they are copied to a Bag folder.
