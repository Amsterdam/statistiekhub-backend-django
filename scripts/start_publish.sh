#!/bin/bash

echo " ================================ "
echo " DOEL: VULLEN PUBLICATIE TABELLEN "
echo " ================================ "



echo " -------------------- "
echo " instellen parameters "
echo " -------------------- "

export p_current_dir=$(dirname $0)
echo $p_current_dir


# laden van omgevingsvariabelen uit env-bestand
eval $(egrep "^[^#;]" $p_current_dir/../.dev.env | xargs -d'\n' -n1 | sed 's/^/export /')

export execute_sql="psql postgresql://$DB_NAME@localhost:$DB_PORT/$DB_USER"
export PGPASSWORD=$DB_PASS
export measure_list=$p_current_dir/measures.txt



echo " ---------------- "
echo " publish measures "
echo " ---------------- "

$execute_sql -f $p_current_dir/publish_measures.sql



echo " -------------------- "
echo " publish observations "
echo " -------------------- "

$execute_sql -c "truncate table publicatie_tabellen_publicationobservation" # empty table

$execute_sql -c "\copy (select distinct name as measure from public.statistiek_hub_measure order by 1) to STDOUT;" > $measure_list # list all measures

while read measure || [[ -n $measure ]]; do
echo $measure
$execute_sql -f $p_current_dir/publish_observations.sql -v p_measure="'$measure'"
done < $measure_list
rm $p_current_dir/measures.txt


echo " ------------------ "
echo " publish statistics "
echo " ------------------ "

$execute_sql -f $p_current_dir/publish_statistics.sql