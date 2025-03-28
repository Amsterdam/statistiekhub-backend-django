from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('publicatie_tabellen', '0004_db_function_apply_filter'),
    ]


    operations = [
        migrations.RunSQL(
            """
            CREATE OR REPLACE FUNCTION log_table_changes()
            RETURNS TRIGGER AS $$
            BEGIN
                INSERT INTO changes_log (table_name, changed_at)
                VALUES (TG_TABLE_NAME, NOW())
                ON CONFLICT (table_name)
                DO UPDATE SET changed_at = EXCLUDED.changed_at;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """
        , ('DROP FUNCTION IF EXISTS public.log_table_changes;')
        ),
        migrations.RunSQL(
            """
            DO $$ DECLARE r RECORD;
            BEGIN
                FOR r IN SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND (table_name LIKE 'statistiek_hub_%' OR table_name LIKE 'referentie_tabellen_%') 
                LOOP
                        EXECUTE format('CREATE TRIGGER table_changes_trigger AFTER INSERT OR UPDATE OR DELETE ON %I FOR EACH STATEMENT EXECUTE FUNCTION log_table_changes()', r.table_name);
                END LOOP;
            END $$;
            """
        ,
            """
            DO $$ 
            DECLARE r RECORD;
            BEGIN
                FOR r IN SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND (table_name LIKE 'statistiek_hub_%' OR table_name LIKE 'referentie_tabellen_%') 
                LOOP
                    EXECUTE format('DROP TRIGGER IF EXISTS table_changes_trigger ON %I', r.table_name);
                END LOOP;
            END $$;
            """
        ),
        migrations.RunSQL(
            """
            CREATE TABLE IF NOT EXISTS changes_log (
                id SERIAL PRIMARY KEY,
                table_name TEXT,
                changed_at TIMESTAMP,
                CONSTRAINT unique_table_operation UNIQUE (table_name)
            );
            """
        , ('DROP TABLE IF EXISTS public.changes_log;')
        ),
    ]