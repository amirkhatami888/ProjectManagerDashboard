from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("creator_subproject", "0009_restore_subproject_history_id_autoincrement"),
    ]

    operations = [
        migrations.RenameField(
            model_name="subproject",
            old_name="sub_project_type",
            new_name="project_stage",
        ),
        migrations.AlterField(
            model_name="subproject",
            name="project_stage",
            field=models.CharField(
                choices=[
                    ("فاز مطالعاتی", "فاز مطالعاتی"),
                    ("طراحی نقشه های فاز 1و2", "طراحی نقشه های فاز 1و2"),
                    ("برگزاری مناقصه", "برگزاری مناقصه"),
                    ("انعقاد قرار داد و تحویل زمین", "انعقاد قرار داد و تحویل زمین"),
                    ("تجهیزات کارگاهی", "تجهیزات کارگاهی"),
                    ("گودبرداری", "گودبرداری"),
                    ("فونداسیون", "فونداسیون"),
                    ("اسکلت", "اسکلت"),
                    ("سفت کاری", "سفت کاری"),
                    ("نما", "نما"),
                    ("اجرای تاسیسات", "اجرای تاسیسات"),
                    ("نازک کاری", "نازک کاری"),
                    ("اجرای نصبیات برقی و مکانیکی", "اجرای نصبیات برقی و مکانیکی"),
                    ("محوطه سازی", "محوطه سازی"),
                    ("دیوارکشی", "دیوارکشی"),
                    ("محوطه سازی و دیوار کشی", "محوطه سازی و دیوار کشی"),
                ],
                max_length=100,
                verbose_name="مرحله جاری پروژه",
            ),
        ),
    ]
