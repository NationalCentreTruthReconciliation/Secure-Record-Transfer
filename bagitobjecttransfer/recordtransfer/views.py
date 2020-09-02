""" Views
"""

import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views.generic import TemplateView
from formtools.wizard.views import SessionWizardView

from recordtransfer.appsettings import BAG_STORAGE_FOLDER, REPORT_FOLDER
from recordtransfer.bagger import create_bag
from recordtransfer.reporter import write_report
from recordtransfer.metadatagenerator import HtmlDocument, BagitTags
from recordtransfer.models import UploadedFile, UploadSession, Bag


LOGGER = logging.getLogger(__name__)


class Index(TemplateView):
    template_name = 'recordtransfer/home.html'


class TransferSent(TemplateView):
    template_name = 'recordtransfer/transfersent.html'


class FormPreparation(TemplateView):
    template_name = 'recordtransfer/formpreparation.html'


class UserProfile(TemplateView):
    template_name = 'recordtransfer/profile.html'


class TransferFormWizard(SessionWizardView):
    ''' A form for collecting user metadata and uploading files '''

    TEMPLATES = {
        "sourceinfo": {
            "templateref": "recordtransfer/standardform.html",
            "formtitle": "Source Information",
        },
        "contactinfo": {
            "templateref": "recordtransfer/standardform.html",
            "formtitle": "Contact Information",
        },
        "recorddescription": {
            "templateref": "recordtransfer/standardform.html",
            "formtitle": "Record Description",
        },
        "rights": {
            "templateref": "recordtransfer/formsetform.html",
            "formtitle": "Record Rights",
        },
        "otheridentifiers": {
            "templateref": "recordtransfer/formsetform.html",
            "formtitle": "Other Identifiers",
            "infomessage": (
                "This step is optional, if you do not have any other IDs associated with the "
                "records, go to the next step"
            )
        },
        "uploadfiles": {
            "templateref": "recordtransfer/dropzoneform.html",
            "formtitle": "Upload Files",
        },
    }

    def get_template_names(self):
        step_name = self.steps.current
        return [self.TEMPLATES[step_name]["templateref"]]

    def get_context_data(self, form, **kwargs):
        ''' Send extra data variables to form templates '''
        context = super(TransferFormWizard, self).get_context_data(form, **kwargs)
        step_name = self.steps.current
        context.update({'form_title': self.TEMPLATES[step_name]['formtitle']})
        if 'infomessage' in self.TEMPLATES[step_name]:
            context.update({'info_message': self.TEMPLATES[step_name]['infomessage']})
        return context

    def done(self, form_list, **kwargs):
        ''' Retrieves all of the form data, and writes the user's uploaded files and their metadata
        to a new Bag. If the Bag generation succeeds, a human-readable report is written with all of
        the metadata and the location of the bag.
        '''
        data = self.get_all_cleaned_data()
        with ThreadPoolExecutor() as executor:
            tag_generator = BagitTags(data)
            tags = tag_generator.generate()
            LOGGER.info('Starting bag creation in the background')
            future = executor.submit(create_bag, BAG_STORAGE_FOLDER, data['session_token'], tags,
                                     None, True)
            bagging_result = future.result()
            if bagging_result['bag_created']:
                bag_location = bagging_result['bag_location']
                parsed_date = datetime.strptime(bagging_result['time_created'], r'%Y%m%d_%H%M%S')
                bagging_date = parsed_date.strftime(r'%Y-%m-%d %H:%M:%S')
                data['storage_location'] = bag_location
                data['creation_time'] = bagging_date
                doc_generator = HtmlDocument(data)
                html_document = doc_generator.generate()
                LOGGER.info('Starting report generation in the background')
                future = executor.submit(write_report, REPORT_FOLDER, html_document, 'html', None)
                report_result = future.result()
                report_location = report_result['report_location']
                report_created = report_result['report_created']
                if report_created:
                    LOGGER.info('Generated HTML document')
                else:
                    LOGGER.info('HTML document generation failed')

                # Create object to be viewed in admin app
                new_bag = Bag(bagging_date=bagging_date, bag_location=bag_location,
                              user=self.request.user)
                if report_created:
                    new_bag.report_location = report_location
                else:
                    new_bag.report_location = 'Report could not be created'
                new_bag.save()
            else:
                LOGGER.warning('Could not generate HTML document since bag creation failed')

        return HttpResponseRedirect(reverse('recordtransfer:transfersent'))


def uploadfiles(request):
    """ Upload one or more files to the server, and return a token representing the file upload
    session. If a token is passed in the request header using the Upload-Session-Token header, the
    uploaded files will be added to the corresponding session, meaning this endpoint can be hit
    multiple times for a large batch upload of files.
    """
    if not request.method == 'POST':
        return JsonResponse({'error': 'Files can only be uploaded using POST.'}, status=500)
    if not request.FILES:
        return JsonResponse({'upload_session_token': ''}, status=200)

    try:
        headers = request.headers
        if not 'Upload-Session-Token' in headers or not headers['Upload-Session-Token']:
            session = UploadSession.new_session()
            session.save()
        else:
            session = UploadSession.objects.filter(token=headers['Upload-Session-Token']).first()
            if session is None:
                session = UploadSession.new_session()
                session.save()

        for _, temp_file in request.FILES.dict().items():
            new_file = UploadedFile(name=temp_file.name, path=temp_file.path,
                old_copy_removed=False, session=session)
            new_file.save()

        return JsonResponse({'upload_session_token': session.token}, status=200)

    except Exception as exc:
        LOGGER.error('Uncaught exception in upload_file: %s' % str(exc))
        return JsonResponse({'error': f'Uncaught Exception:\n{str(exc)}'}, status=500)
