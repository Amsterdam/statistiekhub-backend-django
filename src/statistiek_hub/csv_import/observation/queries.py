create_table_as_query = "CREATE TABLE IF NOT EXISTS {tmp_table_name} AS TABLE {table_name} WITH NO DATA"

drop_table_query = "DROP TABLE IF EXISTS {table_name}"

copy_csv_query = "COPY {table_name} ({columns}) FROM STDIN WITH CSV"

insert_query = (
    "INSERT INTO {table_name} (value, measure_id, spatialdimension_id, temporaldimension_id, created_at, updated_at) "
    "SELECT tmp.value, tmp.measure_id, tmp.spatialdimension_id, tmp.temporaldimension_id,now() AS created_at, now() AS updated_at "  # noqa: E501
    "FROM {tmp_table_name} AS tmp "
    "WHERE NOT EXISTS ( "
    "SELECT org.* FROM {table_name} AS org "
    "WHERE org.measure_id = tmp.measure_id AND "
    "org.temporaldimension_id = tmp.temporaldimension_id AND "
    "org.spatialdimension_id = tmp.spatialdimension_id "
    ") "
    "AND tmp.value IS NOT NULL "
    "RETURNING *"
)

update_query = (
    "UPDATE {table_name} AS org "
    "SET value = tmp.value, updated_at = now() "
    "FROM {tmp_table_name} AS tmp "
    "WHERE org.measure_id = tmp.measure_id AND "
    "org.temporaldimension_id = tmp.temporaldimension_id AND "
    "org.spatialdimension_id = tmp.spatialdimension_id AND "
    "tmp.value IS NOT NULL AND "
    "org.value != tmp.value "
    "RETURNING org.id, org.value, org.measure_id, org.temporaldimension_id, org.spatialdimension_id"
)

delete_query = (
    "DELETE FROM {table_name} AS org "
    "USING {tmp_table_name} AS tmp "
    "WHERE org.measure_id = tmp.measure_id AND "
    "org.temporaldimension_id = tmp.temporaldimension_id AND "
    "org.spatialdimension_id = tmp.spatialdimension_id AND "
    "tmp.value IS NULL "
    "RETURNING org.id, org.value as original_value, tmp.value, org.measure_id, org.temporaldimension_id, org.spatialdimension_id"  # noqa: E501
)
