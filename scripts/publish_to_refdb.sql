-- tabel bbga_kerncijfers
select	*
from	(
		select	concat_ws	(
							'|',
							measure,
							extract(year from temporaldimensionstartdate),
							case when spatialdimensiontype = 'Gemeente' and spatialdimensioncode = '0363' then 'STAD'
							else spatialdimensioncode
							end
							) as id
		,		extract(year from temporaldimensionstartdate) as jaar
		,		case when spatialdimensiontype = 'Gemeente' and spatialdimensioncode = '0363' then 'STAD'
				else spatialdimensioncode
				end as gebiedcode_15
		,		value as waarde
		,		measure as indicator_definitie_id
		from	publicatie_tabellen_publicationobservation
		) as foo
;



-- tabel bbga_indicatoren_definities

select	*
from	(
		select	extra_attr->>'BBGA_sort' as sort
		,		name as variabele
		,		cast(null as varchar) as begrotingsprogramma
		,		theme as thema
		,		label
		,		extra_attr->>'BBGA_label_kort' as label_kort
		,		definition as definitie
		,		source as bron
		,		extra_attr->>'BBGA_peildatum'as peildatum
		,		extra_attr->>'BBGA_verschijningsfrequentie' as verschijningsfrequentie
		,		extra_attr->>'BBGA_rekeneenheid' as rekeneenheid
		,		unit_symbol as symbool
		,		cast(null as varchar) as groep
		,		case
				when decimals = 0 then 'F8.'
				else 'F5.' || cast(decimals as varchar)
				end as format
		,		case
				when f.rule is not null then '1'
				end
				as berekende_variabelen
		,		extra_attr->>'BBGA_thema_kerncijfertabel' as thema_kerncijfertabel
		,		cast(null as varchar) as tussenkopje_kerncijfertabel
		,		extra_attr->>'BBGA_kleurenpalet' as kleurenpalet
		,		extra_attr->>'BBGA_legenda_code' as legenda_code
		,		extra_attr->>'BBGA_sd_minimum_bev_totaal' as sd_minimum_bev_totaal
		,		extra_attr->>'BBGA_sd_minimum_wvoor_bag' as sd_minimum_wvoor_bag
		,		theme_uk as topic_area
		,		label_uk as label_1
		,		definition_uk as definition
		,		extra_attr->>'BBGA_reference_date' as reference_date
		,		extra_attr->>'BBGA_frequency' as frequency
		from	public.publicatie_tabellen_publicationmeasure m
		left
		join	public.statistiek_hub_filter f on m.id = f.measure_id
		) as foo
where	sort is not null -- all active BBGA measures
;


-- tabel bbga_statistieken

select	*
from		(
			select	concat_ws	(
								'|',
								measure,
								extract(year from temporaldimensionstartdate)
								) as id
			,		extract(year from temporaldimensionstartdate) as jaar
			,		average as gemiddelde
			,		standarddeviation as standaardafwijking
			,		case
					when upper(source) = 'WIJK' then 'sdbc'
					when upper(source) = 'GGW-GEBIED' then 'sdgeb22'
					end
					as bron
			,		measure as indicator_definitie_id
			from	publicatie_tabellen_publicationstatistic
			) as foo
;