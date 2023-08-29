vw_publish_observation = {
    "query": (
        """
                    create or replace view public.vw_publish_observation
                    as
                    select	id
                    ,		sd_type as ruimtelijke_dimensie_type
                    ,		sd_date as ruimtelijke_dimensie_datum
                    ,		sd_code as ruimtelijke_dimensie_code
                    ,		sd_name as ruimtelijke_dimensie_naam
                    ,		td_type as temporele_dimensie_type
                    ,		startdate as begindatum
                    ,		enddate as einddatum
                    ,		measure as indicator
                    ,		round_observation(measure_id, coalesce(apply_filter(measure_id, temporaldimension_id, spatialdimension_id), value)) as waarde -- apply filter-rule to value and round
                    from	(
		                    select	o.id
		                    ,		st.name as sd_type
		                    ,		s.source_date as sd_date
		                    ,		s.code as sd_code
		                    ,		s.name as sd_name
		                    ,		tt.name as td_type
		                    ,		t.startdate
		                    ,		t.enddate
		                    ,		m.name as measure
		                    ,		o.value
		                    ,		o.measure_id -- to apply filter
		                    ,		o.temporaldimension_id -- to apply filter
		                    ,		o.spatialdimension_id -- to apply filter
		                    from	public.observation o
		                    join	public.measure m on o.measure_id = m.id
		                    join	public.spatialdimension s on o.spatialdimension_id = s.id
		                    join	public.spatialdimensiontype st on s.type_id = st.id
		                    join	public.temporaldimension t on o.temporaldimension_id = t.id
		                    join	public.temporaldimensiontype tt on t.type_id = tt.id
		                    where	1=1
		                    --
		                    union all
		                    --
		                    -- calculated observation
		                    --
		                    select	o.id
		                    ,		st.name as sd_type
		                    ,		s.source_date as sd_date
		                    ,		s.code as sd_code
		                    ,		s.name as sd_name
		                    ,		tt.name as td_type
		                    ,		t.startdate
		                    ,		t.enddate
		                    ,		m.name as measure
		                    ,		o.value
		                    ,		o.measure_id -- to apply filter
		                    ,		o.temporaldimension_id -- to apply filter
		                    ,		o.spatialdimension_id -- to apply filter
		                    from	public.vw_calculated_observation o
		                    join	public.measure m on o.measure_id = m.id
		                    join	public.spatialdimension s on o.spatialdimension_id = s.id
		                    join	public.spatialdimensiontype st on s.type_id = st.id
		                    join	public.temporaldimension t on o.temporaldimension_id = t.id
		                    join	public.temporaldimensiontype tt on t.type_id = tt.id
		                    where	not exists	( -- supplied observation cannot be overruled by calculated observation
		                    					select	null
		                    					from	public.observation x
		                    					where	o.measure_id = x.measure_id
		                    					and		o.spatialdimension_id = x.spatialdimension_id
		                    					and		o.temporaldimension_id = x.temporaldimension_id
		                    					)
		                    ) as foo
                            ;
            """
    ),
    "reverse": (
        """
                drop view if exists public.vw_publish_observation;
            """
    ),
}
