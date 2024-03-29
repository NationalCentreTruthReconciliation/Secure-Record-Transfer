# Generated by Django 3.2.11 on 2022-11-02 19:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('caais', '0009_preservationassessment_preservationassessmenttype'),
    ]

    operations = [
        migrations.AlterField(
            model_name='archivalunit',
            name='archival_unit',
            field=models.TextField(help_text='Record the reference code and/or title of the archival unit to which the accession belongs.'),
        ),
        migrations.RemoveField(
            model_name='metadata',
            name='status',
        ),
        migrations.AlterField(
            model_name='metadata',
            name='level_of_detail',
            field=models.CharField(
                choices=[('NS', 'Not Specified'), ('ML', 'Minimal'), ('PL', 'Partial'), ('FL', 'Full')], default='NS',
                help_text='Record the level of detail in accordance with a controlled vocabulary maintained by the repository.',
                max_length=2),
        ),
    ]
