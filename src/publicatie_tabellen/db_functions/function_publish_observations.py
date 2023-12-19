function_publish_observations = """
				create or replace function public.publicatie_tabellen_publish_observations
				----------------------------------------------------------------------
				-- GOAL: function to fill table with observations, ready to publish --
				----------------------------------------------------------------------
				(
					p_measure varchar default null
				)
					returns void
				as
				$$

				declare

					p_record record;

				begin

				--
				-- loop through measures to improve performance
				--
					
				for p_record in 

					select	distinct
							m.name as measure
					from 	public.statistiek_hub_measure m
					join	public.statistiek_hub_observation o on m.id = o.measure_id -- select only measures with observations
					order
					by 		1

					loop

					--
					-- fill supplied observations
					--

					insert into public.publication_observations
					(
					spatialdimensiontype,
					spatialdimensiondate,
					spatialdimensioncode,
					spatialdimensionname,
					temporaldimensiontype,
					temporaldimensionstartdate,
					temporaldimensionenddate,
					measure,
					value
					)
					select	spatialdimensiontype
					,		spatialdimensiondate
					,		spatialdimensioncode
					,		spatialdimensionname
					,		temporaldimensiontype
					,		temporaldimensionstartdate
					,		temporaldimensionenddate
					,		measure
					,		round_observation(measure_id, coalesce(apply_filter(measure_id, temporaldimension_id, spatialdimension_id), value))
					from	(
							select	st.name as spatialdimensiontype
							,		s.source_date as spatialdimensiondate
							,		s.code as spatialdimensioncode
							,		s.name as spatialdimensionname
							,		tt.name as temporaldimensiontype
							,		t.startdate as temporaldimensionstartdate
							,		t.enddate as temporaldimensionenddate
							,		m.name as measure
							,		o.value
							,		o.measure_id -- required to apply filter
							,		o.temporaldimension_id -- required to apply filter
							,		o.spatialdimension_id -- required to apply filter
							from	public.observation o
							join	public.statistiek_hub_measure m on o.measure_id = m.id
							join	public.statistiek_hub_spatialdimension s on o.spatialdimension_id = s.id
							join	public.referentie_tabellen_spatialdimensiontype st on s.type_id = st.id
							join	public.statistiek_hub_temporaldimension t on o.temporaldimension_id = t.id
							join	public.referentie_tabellen_temporaldimensiontype tt on t.type_id = tt.id
							) as foo
					where	1=1
					and 	foo.measure = p_record.measure
					and		not exists	( 
										-- no duplicates
										select	null
										from	public.publication_observations x
										where	foo.spatialdimensiontype = x.spatialdimensiontype
										and		foo.spatialdimensiondate = x.spatialdimensiondate
										and		foo.spatialdimensioncode = x.spatialdimensioncode
										and		foo.temporaldimensiontype = x.temporaldimensiontype
										and		foo.temporaldimensionstartdate = x.temporaldimensionstartdate 
										and		foo.measure = x.measure
										)
					;



					--
					-- fill calculated observations
					--
					
					insert into public.publication_observations
					(
					spatialdimensiontype,
					spatialdimensiondate,
					spatialdimensioncode,
					spatialdimensionname,
					temporaldimensiontype,
					temporaldimensionstartdate,
					temporaldimensionenddate,
					measure,
					value
					)
					select	spatialdimensiontype
					,		spatialdimensiondate
					,		spatialdimensioncode
					,		spatialdimensionname
					,		temporaldimensiontype
					,		temporaldimensionstartdate
					,		temporaldimensionenddate
					,		measure
					,		round_observation(measure_id, coalesce(apply_filter(measure_id, temporaldimension_id, spatialdimension_id), value))
					from	(
							select	st.name as spatialdimensiontype
							,		s.source_date as spatialdimensiondate
							,		s.code as spatialdimensioncode
							,		s.name as spatialdimensionname
							,		tt.name as temporaldimensiontype
							,		t.startdate as temporaldimensionstartdate
							,		t.enddate as temporaldimensionenddate
							,		m.name as measure
							,		o.value
							,		o.measure_id -- required to apply filter
							,		o.temporaldimension_id -- required to apply filter
							,		o.spatialdimension_id -- required to apply filter
							from	(
									select	x.value
									,		x.measure_id
									,		x.spatialdimension_id
									,		x.temporaldimension_id
									from	(
											select	(public.calculate_observation(name)).*
											from	statistiek_hub_measure
											where	nullif(calculation, '') is not null
											order
											by		3, 5, 4
											) as x
									) as o
							join	public.statistiek_hub_measure m on o.measure_id = m.id
							join	public.statistiek_hub_spatialdimension s on o.spatialdimension_id = s.id
							join	public.referentie_tabellen_spatialdimensiontype st on s.type_id = st.id
							join	public.statistiek_hub_temporaldimension t on o.temporaldimension_id = t.id
							join	public.referentie_tabellen_temporaldimensiontype tt on t.type_id = tt.id
							where	1=1
							and 	m.name = p_record.measure
							and		not exists	( 
												-- supplied observation cannot be overruled by calculated observation
												select	null
												from	public.statistiek_hub_observation x
												where	o.measure_id = x.measure_id
												and		o.spatialdimension_id = x.spatialdimension_id
												and		o.temporaldimension_id = x.temporaldimension_id
												)
							and		not exists	( 
												-- no duplicates
												select	null
												from	public.publicatie_tabellen_publication_observation x
												where	st.name = x.spatialdimensiontype
												and		s.source_date = x.spatialdimensiondate
												and		s.code = x.spatialdimensioncode
												and		tt.name = x.temporaldimensiontype
												and		t.startdate = x.temporaldimensionstartdate 
												and		m.name = x.measure
												)
							) as foo
							;



					--
					-- fill missing spatial dimension / temporal dimension with null value
					--
						
					insert into public.publication_observations
					(
					spatialdimensiontype,
					spatialdimensiondate,
					spatialdimensioncode,
					spatialdimensionname,
					temporaldimensiontype,
					temporaldimensionstartdate,
					temporaldimensionenddate,
					measure,
					value
					)
					with
					all_observations as	(
										select	spatialdimensiontype 
										,		spatialdimensiondate 
										,		spatialdimensioncode 
										,		spatialdimensionname 
										,		temporaldimensiontype 
										,		temporaldimensionstartdate 
										,		temporaldimensionenddate 
										,		measure 
										,		coalesce(value, 999) as value -- tric in case supplied or calculated value is null to avoid second null value to be added
										from	publicatie_tabellen_publication_observation
										where	1=1
										and 	measure = p_record.measure
										),
					select_observations as	(
											select	distinct
													a.measure
											,		sd.type as spatialdimensiontype
											,		sd.source_date as spatialdimensiondate
											,		sd.code as spatialdimensioncode
											,		sd.name as spatialdimensionname
											,		a.temporaldimensiontype
											,		a.temporaldimensionstartdate
											,		a.temporaldimensionenddate
											from 	all_observations a
											right
											join 	(
													select	d.*
													,		t.name as type
													from	statistiek_hub_spatialdimension d
													join	referentie_tabellen_spatialdimensiontype t on d.type_id = t.id
													where	lower(t.name) not in ('land', 'provincie', 'waterschap', 'gemeente') -- these types not
													) sd on	a.spatialdimensiontype = sd.type
														and	a.spatialdimensiondate = sd.source_date
											),
					--missings in de data
					missings as (			select	distinct
													s.spatialdimensiontype
											, 		s.spatialdimensiondate
											, 		s.spatialdimensioncode
											, 		s.temporaldimensiontype
											, 		s.temporaldimensionstartdate
											, 		s.measure  
											from 	all_observations a
											right
											join 	select_observations s on  a.spatialdimensiontype = s.spatialdimensiontype
																		and a.spatialdimensiondate = s.spatialdimensiondate 
																		and a.spatialdimensioncode = s.spatialdimensioncode 
																		and a.temporaldimensiontype = s.temporaldimensiontype
																		and a.temporaldimensionstartdate = s.temporaldimensionstartdate 
																		and a.measure = s.measure
											where 	a.value is null 
											)
					--
					-- fill missing spatial dimensions with null-values
					--
					select	s.spatialdimensiontype
					,		s.spatialdimensiondate
					,		s.spatialdimensioncode
					,		s.spatialdimensionname
					,		s.temporaldimensiontype
					,		s.temporaldimensionstartdate
					,		s.temporaldimensionenddate
					,		s.measure
					,		cast(null as float)
					from 	select_observations s
					join 	missings m	on  s.spatialdimensiontype = m.spatialdimensiontype 
										and s.spatialdimensiondate = m.spatialdimensiondate
										and s.spatialdimensioncode = m.spatialdimensioncode
										and s.temporaldimensiontype = m.temporaldimensiontype
										and s.temporaldimensionstartdate = m.temporaldimensionstartdate
										and s.measure = m.measure
					where	1=1
					and		not exists	( 
										-- no duplicates
										select	null
										from	public.publicatie_tabellen_publication_observation x
										where	s.spatialdimensiontype = x.spatialdimensiontype
										and		s.spatialdimensiondate = x.spatialdimensiondate
										and		s.spatialdimensioncode = x.spatialdimensioncode
										and		s.temporaldimensiontype = x.temporaldimensiontype
										and		s.temporaldimensionstartdate = x.temporaldimensionstartdate 
										and		s.measure = x.measure
										)
					;
						
				end loop;

				end;

				$$
				language plpgsql
				;
            """
