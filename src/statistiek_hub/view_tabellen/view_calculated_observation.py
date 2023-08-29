vw_calculated_observation = {
    "query": (
        """
                create or replace view public.vw_calculated_observation
                as
                with
                observation as  (
                                select  max(id) as max_id
                                from    public.observation
                                )
                select	(select max_id from observation) + row_number() over() as id -- TODO make unique and persist observation id
                ,		foo.created_at
                ,		foo.updated_at
                ,		foo.value
                ,		foo.measure_id
                ,		foo.spatialdimension_id
                ,		foo.temporaldimension_id
                from	(
                        select	(public.calculate_observation(name)).*
                        from	measure
                        where	nullif(calculation, '') is not null
                        order
                        by		3, 5, 4
                        ) as foo
                ;
            """
    ),
    "reverse": (
        """
                drop view if exists public.calculated_observation cascade;
            """
    ),
}
