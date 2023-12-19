function_publish_statistics = """
				create or replace function public.publicatie_tabellen_publish_statistics
				---------------------------------------------------------------------------------------
				-- GOAL: function to fill table with average and standarddeviation, ready to publish --
				---------------------------------------------------------------------------------------
				(
				)
					returns void
				as
				$$

				declare


				begin

				insert into public.publicatie_tabellen_publication_statistics
				(
				spatialdimensiondate,
				temporaldimensiontype,
				temporaldimensionstartdate,
				measure,
				average,
				standarddeviation,
				source
				)
				with
				mta as	(
						select 'BEVMUTNL_P' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'BEVMUTTOT_P' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'BHBGWFOODWVO_1000INW' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'BHBGWNONFWVO_1000INW' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'BHBGWWVO_1000INW' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'BHHORECA_1000INW' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'BHHOTBED_1000INW' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'BHVESTAIRBNB_1000WON' as measure, cast(null as integer) as sd_minimum_bevolking, 1000 as sd_minimum_woningvoorraad union all
						select 'BHWINK_1000INW' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'BHWINKDG_1000INW' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'BHWP_1000INW' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'SK017_KWETS34' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'SK017_KWETS34_P' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'SK017_SES234' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'SK017_SES234_P' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'SK1826_KWETS34' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'SK1826_KWETS34_P' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'SK1826_SES234' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'SK1826_SES234_P' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'SK2765_KWETS34' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'SK2765_KWETS34_P' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'SK2765_SES234' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'SK2765_SES234_P' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'SK66PLUS_KWETS34' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'SK66PLUS_KWETS34_P' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'SK66PLUS_SES234' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'SK66PLUS_SES234_P' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'SKACTI' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'SKACTI_1000INW' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'SKKWETS0_P' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'SKKWETS12_P' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'SKKWETS34' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'SKKWETS34_P' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'SKSES_GEM' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'SKSES234' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'SKSES234_P' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'SKSES567' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'SKSES567_P' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'SKSES8910' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'SKSES8910_P' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'SRCULTUUR_1000INW' as measure, 500 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'SRSPORT_1000INW' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'VBRAND_1000WON' as measure, cast(null as integer) as sd_minimum_bevolking, 1000 as sd_minimum_woningvoorraad union all
						select 'WBEZET' as measure, cast(null as integer) as sd_minimum_bevolking, 500 as sd_minimum_woningvoorraad union all
						select 'WZGEZOND_1000INW' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad union all
						select 'WZWELZIJN_1000INW' as measure, 1000 as sd_minimum_bevolking, cast(null as integer) as sd_minimum_woningvoorraad
						),
				obs as	(
						select	o.value
						,		m.name as measure
						,		st.name as spatialdimensiontype
						,		s.source_date as spatialdimensiondate
						,		s.code as spatialdimensioncode
						,		tt.name as temporaldimensiontype
						,		t.startdate as temporaldimensionstartdate
						,		o.measure_id
						,		o.spatialdimension_id
						,		o.temporaldimension_id
						from	(
								select	value
								, 		measure_id
								, 		spatialdimension_id
								, 		temporaldimension_id
								from	public.observation
								union all
								-- calculated observations
								select	x.value
								,		x.measure_id
								,		x.spatialdimension_id
								,		x.temporaldimension_id
								from	(
										select	(public.calculate_observation(name)).*
										from	measure
										where	nullif(calculation, '') is not null
										order
										by		3, 5, 4
										) as x
								) o
						join	public.statistiek_hub_measure m on o.measure_id = m.id
						join	public.statistiek_hub_spatialdimension s on o.spatialdimension_id = s.id
						join	public.statistiek_hub_spatialdimensiontype st on s.type_id = st.id
						join	public.statistiek_hub_temporaldimension t on o.temporaldimension_id = t.id
						join	public.statistiek_hub_temporaldimensiontype tt on t.type_id = tt.id
						),
				gem as	(
						select	obs.*
						from 	obs
						join	mta on obs.measure = mta.measure
						where	obs.spatialdimensiontype = 'Gemeente'
						),
				min as	(
						select	obs.measure
						,		obs.spatialdimensiontype
						,		obs.spatialdimensiondate
						,		obs.spatialdimensioncode
						,		obs.temporaldimensiontype
						,		obs.temporaldimensionstartdate
						,		obs.measure_id
						,		obs.spatialdimension_id
						,		obs.temporaldimension_id
						,		case
								when	(
										bev.value < mta.sd_minimum_bevolking or
										won.value < mta.sd_minimum_woningvoorraad
										) then null
								else obs.value
								end as value
				--		,		bev.value as bev_value
				--		,		mta.sd_minimum_bevolking
				--		,		won.value as won_value
				--		,		mta.sd_minimum_woningvoorraad
						from 	obs
						join	(
								select	spatialdimension_id
								,		temporaldimension_id
								,		value
								from	obs
								where	upper(measure) = 'BEVTOTAAL'
								) as bev on obs.spatialdimension_id = bev.spatialdimension_id and obs.temporaldimension_id = bev.temporaldimension_id
						join	(
								select	spatialdimension_id
								,		temporaldimension_id
								,		value
								from	obs
								where	upper(measure) = 'WVOORRBAG'
								) as won on obs.spatialdimension_id = won.spatialdimension_id and obs.temporaldimension_id = won.temporaldimension_id
						join	mta on obs.measure = mta.measure -- selecteert automatisch alleen de betrokken measures 
						),
				sddev as	(
							select	coalesce(w.measure, g.measure) as measure
							,		coalesce(w.spatialdimensiontype, g.spatialdimensiontype) as spatialdimensiontype
							,		coalesce(w.spatialdimensiondate, g.spatialdimensiondate) as spatialdimensiondate
							,		coalesce(w.temporaldimensiontype, g.temporaldimensiontype) as temporaldimensiontype
							,		coalesce(w.temporaldimensionstartdate, g.temporaldimensionstartdate) as temporaldimensionstartdate
							,		coalesce(w.sd, g.sd) as sd
							,		coalesce(w.bron, g.bron) as bron
							from	(
									select	measure
									,		spatialdimensiontype
									,		spatialdimensiondate
									,		temporaldimensiontype
									,		temporaldimensionstartdate
									,		stddev(value) as sd
									,		'Wijk' as bron
									from	min
									where	value is not null
									and		spatialdimensiontype = 'Wijk'
									group
									by		measure
									,		spatialdimensiontype
									,		spatialdimensiondate
									,		temporaldimensiontype
									,		temporaldimensionstartdate
									) w
							full 
							outer
							join	(
									select	measure
									,		spatialdimensiontype
									,		spatialdimensiondate
									,		temporaldimensiontype
									,		temporaldimensionstartdate
									,		stddev(value) as sd
									,		'GGW-gebied' as bron
									from	min
									where	value is not null
									and		spatialdimensiontype = 'GGW-gebied'
									group
									by		measure
									,		spatialdimensiontype
									,		spatialdimensiondate
									,		temporaldimensiontype
									,		temporaldimensionstartdate
									) g on 	w.measure = g.measure  
										and w.spatialdimensiondate = g.spatialdimensiondate 
										and w.temporaldimensiontype = g.temporaldimensiontype 
										and w.temporaldimensionstartdate = g.temporaldimensionstartdate
							)
				select	g.spatialdimensiondate
				,		g.temporaldimensiontype
				,		g.temporaldimensionstartdate
				,		g.measure
				,		round(g.value::numeric, 3) as average
				,		round(s.sd::numeric, 3) as standarddeviation
				,		s.bron as standarddeviation_source
				from	gem g
				join	sddev s on 	s.measure = g.measure  
								and s.spatialdimensiondate = g.spatialdimensiondate 
								and s.temporaldimensiontype = g.temporaldimensiontype 
								and s.temporaldimensionstartdate = g.temporaldimensionstartdate 
				where	1=1
				and		not exists	( 
									-- no duplicates
									select	null
									from	public.publication_statistics x
									where	g.spatialdimensiondate = x.spatialdimensiondate
									and		g.temporaldimensiontype = x.temporaldimensiontype
									and		g.temporaldimensionstartdate = x.temporaldimensionstartdate 
									and		g.measure = x.measure
									)
				;

				end;

				$$
				language plpgsql
				;
            """
