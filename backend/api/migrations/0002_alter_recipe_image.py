# Generated by Django 5.1.1 on 2024-09-07 18:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='images/', verbose_name='Ссылка на картинку на сайте'),
        ),
    ]
