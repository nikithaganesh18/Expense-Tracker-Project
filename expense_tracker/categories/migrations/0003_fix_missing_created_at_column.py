from django.db import migrations


def add_missing_created_at(apps, schema_editor):
    table_name = "categories_category"

    with schema_editor.connection.cursor() as cursor:
        columns = []

        if schema_editor.connection.vendor == "sqlite":
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
        else:
            description = schema_editor.connection.introspection.get_table_description(cursor, table_name)
            columns = [col.name for col in description]

        if "created_at" not in columns:
            if schema_editor.connection.vendor == "sqlite":
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN created_at datetime")
                cursor.execute(
                    f"UPDATE {table_name} "
                    f"SET created_at = CURRENT_TIMESTAMP "
                    f"WHERE created_at IS NULL"
                )
            else:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN created_at timestamp NULL")
                cursor.execute(
                    f"UPDATE {table_name} "
                    f"SET created_at = CURRENT_TIMESTAMP "
                    f"WHERE created_at IS NULL"
                )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("categories", "0002_alter_category_user"),
    ]

    operations = [
        migrations.RunPython(add_missing_created_at, reverse_code=noop),
    ]