from django.db import migrations


class Migration(migrations.Migration):
    """
    Restore the auto-generated primary key on the live financialdocument table.

    The Django model uses the app's default BigAutoField, but the deployed
    MySQL table had an id column without AUTO_INCREMENT. New financial documents then
    failed with MySQL error 1364.
    """

    dependencies = [
        ("creator_subproject", "0011_subproject_has_tax_insurance_increase_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE `creator_subproject_financialdocument` "
                "MODIFY `id` BIGINT NOT NULL AUTO_INCREMENT"
            ),
            reverse_sql=(
                "ALTER TABLE `creator_subproject_financialdocument` "
                "MODIFY `id` BIGINT NOT NULL"
            ),
        ),
    ]