# Generated by Django 3.2.20 on 2023-09-27 19:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('caais', '0011_auto_20230907_1214'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='acquisitionmethod',
            options={'verbose_name': 'Acquisition method', 'verbose_name_plural': 'Acquisition methods'},
        ),
        migrations.AlterModelOptions(
            name='appraisaltype',
            options={'verbose_name': 'Appraisal type', 'verbose_name_plural': 'Appraisal types'},
        ),
        migrations.AlterModelOptions(
            name='archivalunit',
            options={'verbose_name': 'Archival unit', 'verbose_name_plural': 'Archival units'},
        ),
        migrations.AlterModelOptions(
            name='associateddocumentation',
            options={'verbose_name': 'Associated document', 'verbose_name_plural': 'Associated documentation'},
        ),
        migrations.AlterModelOptions(
            name='associateddocumentationtype',
            options={'verbose_name': 'Associated documentation type', 'verbose_name_plural': 'Associated documentation types'},
        ),
        migrations.AlterModelOptions(
            name='creationorrevisiontype',
            options={'verbose_name': 'Date of creation or revision type', 'verbose_name_plural': 'Date of creation or revision types'},
        ),
        migrations.AlterModelOptions(
            name='dateofcreationorrevision',
            options={'verbose_name': 'Date of creation or revision', 'verbose_name_plural': 'Dates of creation or revision'},
        ),
        migrations.AlterModelOptions(
            name='dispositionauthority',
            options={'verbose_name': 'Disposition authority', 'verbose_name_plural': 'Disposition authorities'},
        ),
        migrations.AlterModelOptions(
            name='eventtype',
            options={'verbose_name': 'Event type', 'verbose_name_plural': 'Event types'},
        ),
        migrations.AlterModelOptions(
            name='extentstatement',
            options={'verbose_name': 'Extent statement', 'verbose_name_plural': 'Extent statements'},
        ),
        migrations.AlterModelOptions(
            name='generalnote',
            options={'verbose_name': 'General note', 'verbose_name_plural': 'General notes'},
        ),
        migrations.AlterModelOptions(
            name='metadata',
            options={'verbose_name': 'CAAIS metadata', 'verbose_name_plural': 'CAAIS metadata'},
        ),
        migrations.AlterModelOptions(
            name='preliminarycustodialhistory',
            options={'verbose_name': 'Preliminary custodial history', 'verbose_name_plural': 'Preliminary custodial histories'},
        ),
        migrations.AlterModelOptions(
            name='preliminaryscopeandcontent',
            options={'verbose_name': 'Preliminary scope and content', 'verbose_name_plural': 'Preliminary scope and content'},
        ),
        migrations.AlterModelOptions(
            name='preservationrequirements',
            options={'verbose_name': 'Preservation requirement', 'verbose_name_plural': 'Preservation requirements'},
        ),
        migrations.AlterModelOptions(
            name='preservationrequirementstype',
            options={'verbose_name': 'Preservation requirements type', 'verbose_name_plural': 'Preservation requirements types'},
        ),
        migrations.AlterModelOptions(
            name='rights',
            options={'verbose_name': 'Rights statement', 'verbose_name_plural': 'Rights'},
        ),
        migrations.AlterModelOptions(
            name='rightstype',
            options={'verbose_name': 'Type of rights', 'verbose_name_plural': 'Rights types'},
        ),
        migrations.AlterModelOptions(
            name='sourceconfidentiality',
            options={'verbose_name': 'Source confidentiality', 'verbose_name_plural': 'Source confidentialities'},
        ),
        migrations.AlterModelOptions(
            name='sourceofmaterial',
            options={'verbose_name': 'Source of material', 'verbose_name_plural': 'Sources of material'},
        ),
        migrations.AlterModelOptions(
            name='sourcerole',
            options={'verbose_name': 'Source role', 'verbose_name_plural': 'Source roles'},
        ),
        migrations.AlterModelOptions(
            name='sourcetype',
            options={'verbose_name': 'Source type', 'verbose_name_plural': 'Source types'},
        ),
        migrations.AlterModelOptions(
            name='storagelocation',
            options={'verbose_name': 'Storage location', 'verbose_name_plural': 'Storage locations'},
        ),
        migrations.AlterField(
            model_name='acquisitionmethod',
            name='name',
            field=models.CharField(help_text='Record the acquisition method in accordance with a controlled vocabulary [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 1.5]', max_length=128, unique=True),
        ),
        migrations.AlterField(
            model_name='appraisal',
            name='appraisal_note',
            field=models.TextField(blank=True, default='', help_text='Record any other information relevant to describing the appraisal activities. [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 4.4.3]'),
        ),
        migrations.AlterField(
            model_name='appraisal',
            name='appraisal_value',
            field=models.TextField(blank=True, default='', help_text='Where the accession process includes appraisal activities, record the appraisal statement value. [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 4.4.2]'),
        ),
        migrations.AlterField(
            model_name='appraisaltype',
            name='name',
            field=models.CharField(help_text='Record the appraisal type in accordance with a controlled vocabulary maintained by the repository [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 4.4.1]', max_length=128, unique=True),
        ),
        migrations.AlterField(
            model_name='archivalunit',
            name='archival_unit',
            field=models.TextField(help_text='Record the reference code and/or title of the archival unit to which the accession belongs [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 1.4]'),
        ),
        migrations.AlterField(
            model_name='associateddocumentation',
            name='associated_documentation_note',
            field=models.TextField(blank=True, default='', help_text='Record any other information relevant to describing documentation associated to the accessioned material [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 4.5.3]'),
        ),
        migrations.AlterField(
            model_name='associateddocumentation',
            name='associated_documentation_title',
            field=models.TextField(blank=True, default='', help_text='Record the title of the associated documentation [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 4.5.2]'),
        ),
        migrations.AlterField(
            model_name='associateddocumentationtype',
            name='name',
            field=models.CharField(help_text='Where the accession process generates associated documents, record the associated documentation type in accordance with a controlled vocabulary maintained by the repository. [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 4.5.1]', max_length=128, unique=True),
        ),
        migrations.AlterField(
            model_name='carriertype',
            name='name',
            field=models.CharField(help_text='Record the physical format of an object that supports or carries archival materials using a controlled vocabulary maintained by the repository [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 3.2.4]', max_length=128, unique=True),
        ),
        migrations.AlterField(
            model_name='contenttype',
            name='name',
            field=models.CharField(help_text='Record the type of material contained in the units measured, i.e., the genre of the material [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 3.2.3]', max_length=128, unique=True),
        ),
        migrations.AlterField(
            model_name='creationorrevisiontype',
            name='name',
            field=models.CharField(help_text='Record the action type in accordance with a controlled vocabulary maintained by the repository. [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 7.2.1]', max_length=128, unique=True),
        ),
        migrations.AlterField(
            model_name='dateofcreationorrevision',
            name='creation_or_revision_agent',
            field=models.CharField(blank=True, default='', help_text='Record the name of the staff member who performed the action (creation or revision) on the accession record [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 7.2.3]', max_length=256),
        ),
        migrations.AlterField(
            model_name='dateofcreationorrevision',
            name='creation_or_revision_date',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='dateofcreationorrevision',
            name='creation_or_revision_note',
            field=models.TextField(blank=True, default='', help_text='Record any information summarizing actions applied to the accession record. [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 7.2.4]'),
        ),
        migrations.AlterField(
            model_name='dispositionauthority',
            name='disposition_authority',
            field=models.TextField(help_text='Record information about any legal instruments that apply to the accessioned material. Legal instruments include statutes, records schedules or disposition authorities, and donor agreements [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 1.6]'),
        ),
        migrations.AlterField(
            model_name='event',
            name='event_agent',
            field=models.CharField(blank=True, default='', help_text='Record the name of the staff member or application responsible for the event [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 5.1.3]', max_length=256),
        ),
        migrations.AlterField(
            model_name='event',
            name='event_note',
            field=models.TextField(blank=True, default='', help_text='Record any other information relevant to describing the event. [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 5.1.4]'),
        ),
        migrations.AlterField(
            model_name='eventtype',
            name='name',
            field=models.CharField(help_text='Record the event type in accordance with a controlled vocabulary maintained by the repository [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 5.1.1]', max_length=128, unique=True),
        ),
        migrations.AlterField(
            model_name='extentstatement',
            name='content_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='extent_statements', to='caais.contenttype'),
        ),
        migrations.AlterField(
            model_name='extentstatement',
            name='extent_note',
            field=models.TextField(blank=True, default='', help_text='Record additional information related to the number and type of units received, retained, or removed not otherwise recorded [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 3.2.5]'),
        ),
        migrations.AlterField(
            model_name='extentstatement',
            name='extent_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='extent_statements', to='caais.extenttype'),
        ),
        migrations.AlterField(
            model_name='extentstatement',
            name='quantity_and_unit_of_measure',
            field=models.TextField(blank=True, default='', help_text='Record the number and unit of measure expressing the quantity of the extent (e.g., 5 files, totalling 2.5MB) [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 3.2.2]'),
        ),
        migrations.AlterField(
            model_name='extenttype',
            name='name',
            field=models.CharField(help_text='Record the extent statement type in accordance with a controlled vocabulary maintained by the repository [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 3.2.1]', max_length=128, unique=True),
        ),
        migrations.AlterField(
            model_name='generalnote',
            name='general_note',
            field=models.TextField(help_text='Record any other information relevant to the accession record or accessioning process [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 6.1]'),
        ),
        migrations.AlterField(
            model_name='identifier',
            name='identifier_note',
            field=models.TextField(blank=True, default='', help_text='Record any additional information that clarifies the purpose, use or generation of the identifier. [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 1.2.3]'),
        ),
        migrations.AlterField(
            model_name='identifier',
            name='identifier_type',
            field=models.CharField(blank=True, default='', help_text='Record the identifier type in accordance with a controlled vocabulary maintained by the repository [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 1.2.1]', max_length=128),
        ),
        migrations.AlterField(
            model_name='identifier',
            name='identifier_value',
            field=models.CharField(help_text='Record the other identifier value as received or generated by the repository [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 1.2.2]', max_length=128),
        ),
        migrations.AlterField(
            model_name='languageofmaterial',
            name='language_of_material',
            field=models.TextField(help_text='Record, at a minimum, the language that is predominantly found in the accessioned material [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 3.4]'),
        ),
        migrations.AlterField(
            model_name='metadata',
            name='accession_title',
            field=models.CharField(blank=True, default='', help_text='Supply an accession title in accordance with the repository\'s descriptive standard, typically consisting of the creator\'s name(s) and the type of material [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 1.3]', max_length=512),
        ),
        migrations.AlterField(
            model_name='metadata',
            name='date_of_materials',
            field=models.CharField(blank=True, default='', help_text='Provide a preliminary estimate of the date range or explicitly indicate if not it has yet been determined [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 3.1]', max_length=512),
        ),
        migrations.AlterField(
            model_name='metadata',
            name='language_of_accession_record',
            field=models.CharField(blank=True, default='en', help_text='Record the language(s) and script(s) used to create the accession record. [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 7.3]', max_length=256),
        ),
        migrations.AlterField(
            model_name='metadata',
            name='repository',
            field=models.CharField(blank=True, default='', help_text='Give the authorized form(s) of the name of the institution in accordance with the repository\'s naming standard [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 1.1]', max_length=512),
        ),
        migrations.AlterField(
            model_name='metadata',
            name='rules_or_conventions',
            field=models.CharField(blank=True, default='', help_text='Record information about the standards, rules or conventions that were followed when creating or maintaining the accession record. [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 7.1]', max_length=256),
        ),
        migrations.AlterField(
            model_name='preliminarycustodialhistory',
            name='preliminary_custodial_history',
            field=models.TextField(help_text='Provide relevant custodial history information in accordance with the repository\'s descriptive standard. Record the successive transfers of ownership, responsibility and/or custody of the accessioned material prior to its transfer to the repository [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 2.2]'),
        ),
        migrations.AlterField(
            model_name='preliminaryscopeandcontent',
            name='preliminary_scope_and_content',
            field=models.TextField(help_text='Record a preliminary description that may include: functions and activities that resulted in the material\'s generation, dates, the geographic area to which the material pertains, subject matter, arrangement, classification, and documentary forms [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 3.3]'),
        ),
        migrations.AlterField(
            model_name='preservationrequirements',
            name='preservation_requirements_note',
            field=models.TextField(blank=True, default='', help_text='Record any other information relevant to the long-term preservation of the material [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 4.3.3]'),
        ),
        migrations.AlterField(
            model_name='preservationrequirements',
            name='preservation_requirements_value',
            field=models.TextField(blank=True, default='', help_text='Record information about the assessment of the material with respect to its physical condition, dependencies, processing or access [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 4.3.2]'),
        ),
        migrations.AlterField(
            model_name='preservationrequirementstype',
            name='name',
            field=models.CharField(help_text='Record the type of preservation requirement in accordance with a controlled vocabulary maintained by the repository. [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 4.3.1]', max_length=128, unique=True),
        ),
        migrations.AlterField(
            model_name='rights',
            name='rights_note',
            field=models.TextField(blank=True, default='', help_text='Record any other information relevant to describing the rights statement [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 4.2.3]'),
        ),
        migrations.AlterField(
            model_name='rights',
            name='rights_value',
            field=models.TextField(blank=True, default='', help_text='Record the nature and duration of the permission granted or restriction imposed. Specify where the condition applies only to part of the accession [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 4.2.2]'),
        ),
        migrations.AlterField(
            model_name='rightstype',
            name='name',
            field=models.CharField(help_text='Record the rights statement type in accordance with a controlled vocabulary maintained by the repository [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 4.2.1]', max_length=128, unique=True),
        ),
        migrations.AlterField(
            model_name='sourceconfidentiality',
            name='name',
            field=models.CharField(help_text='Record source statements or source information that is for internal use only by the repository. Repositories should develop a controlled vocabulary with terms that can be translated into clear rules for handling source information [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 2.1.6]', max_length=128, unique=True),
        ),
        migrations.AlterField(
            model_name='sourceofmaterial',
            name='source_name',
            field=models.CharField(blank=True, default='', help_text='Record the source name in accordance with the repository\'s descriptive standard [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 2.1.2]', max_length=256),
        ),
        migrations.AlterField(
            model_name='sourceofmaterial',
            name='source_note',
            field=models.TextField(blank=True, default='', help_text='Record any other information about the source of the accessioned materials. If the source performed the role for only a specific period of time (e.g. was a custodian for several years), record the dates in this element [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 2.1.5]'),
        ),
        migrations.AlterField(
            model_name='sourcerole',
            name='name',
            field=models.CharField(help_text='Record the source role (when known) in accordance with a controlled vocabulary maintained by the repository [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 2.1.4]', max_length=128, unique=True),
        ),
        migrations.AlterField(
            model_name='sourcetype',
            name='name',
            field=models.CharField(help_text='Record the source in accordance with a controlled vocabulary maintained by the repository [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 2.1.1]', max_length=128, unique=True),
        ),
        migrations.AlterField(
            model_name='status',
            name='name',
            field=models.CharField(help_text='Record the current position of the material with respect to the repository\'s workflows and business processes using a controlled vocabulary [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 1.7]', max_length=128, unique=True),
        ),
        migrations.AlterField(
            model_name='storagelocation',
            name='storage_location',
            field=models.TextField(help_text='Record the physical and/or digital location(s) within the repository in which the accessioned material is stored [<a href="https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf" target="_blank">CAAIS</a> 4.1]'),
        ),
    ]
