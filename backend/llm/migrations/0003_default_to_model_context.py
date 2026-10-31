from django.db import migrations, models


def use_model_context(apps, schema_editor):
    AppSettings = apps.get_model("llm", "AppSettings")
    AppSettings.objects.filter(num_ctx=8192).update(num_ctx=0)


class Migration(migrations.Migration):

    dependencies = [
        ("llm", "0002_remove_appsettings_ollama_base_url"),
    ]

    operations = [
        migrations.RunPython(use_model_context, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="appsettings",
            name="num_ctx",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
