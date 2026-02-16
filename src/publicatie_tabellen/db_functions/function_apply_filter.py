function_apply_filter = r"""
create or replace function public.apply_filter
                ----------------------------------------------------------------------------------
                -- GOAL: function to return observation values after applying (privacy) filters --
                ----------------------------------------------------------------------------------
                (
                    p_measure_id			bigint,
                    p_filter_rule			varchar,
                    p_replacement_value		float,
                    p_years                 int[] default null
                )
                    returns setof statistiek_hub_observation -- returns query result
                    -- returns text -- returns query statement
                as
                $$

                declare

                    p_measure           varchar;
                    p_rule				varchar[];
                    p_total				integer;
                    p_value_new			float;

					i					varchar;
                    p_number			integer default 0;
                    p_bracket_number	integer default 0;

                    p_stmt				text;
                    p_stmt_select		text default '';
                    p_stmt_with			text default '';
                    p_stmt_join			text default '';
                    p_stmt_value		text default '';
                    p_stmt_order		text default '';

                begin

                    --------------------------------------
                    -- get measure name from measure_id --
                    --------------------------------------

                    select  name into p_measure
                    from    statistiek_hub_measure
                    where   id = p_measure_id;


                    -------------------------------------
                    -- split rule on spaces into array --
                    -------------------------------------

                    select	regexp_split_to_array(p_filter_rule, '\s+') into p_rule;
                   

                    --------------------------------------------------------------------------
                    -- total number of measures in filter; each measure should start with $ --
                    --------------------------------------------------------------------------

                    select	count(*) into p_total
                    from	(
                            select	unnest(p_rule) as rij
                            ) as foo
                    where 	rij like '$%'
                    ;


                    if p_total > 0 then

                    
                        ------------------------------------------------
                        -- start 'with' statement with supplied years --
                        ------------------------------------------------

                        p_stmt_with :=
                        '
                        with base as (
                            select  o.measure_id,
                                    o.spatialdimension_id,
                                    o.temporaldimension_id,
                                    t.year,
                                    o.value
                            from (
                                    select a.measure_id, a.spatialdimension_id, a.temporaldimension_id, a.value
                                    from statistiek_hub_observation a
                                    union all
                                    select b.measure_id, b.spatialdimension_id, b.temporaldimension_id, b.value
                                    from statistiek_hub_observationcalculated b
                                    join statistiek_hub_temporaldimension c on b.temporaldimension_id = c.id
                                    where ($1 is null OR c.year = any($1))
                            ) o
                            join statistiek_hub_measure m on o.measure_id = m.id
                            join statistiek_hub_spatialdimension s on o.spatialdimension_id = s.id
                            join statistiek_hub_temporaldimension t on o.temporaldimension_id = t.id
                        )
                        ';

                        -----------------------------------------------------
                        -- continue 'with' statement with supplied measure --
                        -----------------------------------------------------

                        p_stmt_with := p_stmt_with || ',
                            var0 as (
                                select b.*
                                from base b
                                join statistiek_hub_measure m on b.measure_id = m.id
                                where m.name = $2
                            )
                            ';

                                                                            
                        -------------------------------------------------------------------
                        -- loop through rule elements; only if rule contains any measure --
                        -------------------------------------------------------------------

                        foreach i in array p_rule loop -- start loop rule

                            if i like '$%' then -- start measure

                                p_number := p_number + 1;


                                -----------------------------------------------------------------
                                -- construct 'with' sql-statements for each individual measure --
                                -----------------------------------------------------------------

                                p_stmt_with := p_stmt_with || ',
                                var' || p_number || ' as (
                                    select b.*
                                    from base b
                                    join statistiek_hub_measure m on b.measure_id = m.id
                                    where m.name = ''' || right(i, length(i) - 1) || '''
                                )
                                ';


                                -----------------------------------------------------------------
                                -- construct 'join' sql-statements for each individual measure --
                                -----------------------------------------------------------------

                                p_stmt_join := 	p_stmt_join || 'join	var' || p_number ||
                                                ' on var' || p_number || '.spatialdimension_id = var' || p_number -1 || '.spatialdimension_id and var' ||
                                                p_number || '.year = var' || p_number -1 || '.year '
                                                ;


                                -----------------------------------------------------------------------------
                                -- construct 'calculated value' sql-statements for each individual measure --
                                -----------------------------------------------------------------------------

                                p_stmt_value := p_stmt_value || 'cast(var' || p_number || '.value as float)';


                           -------------------------------------------------------
                           -- detect first and last brackets for case-statement --
                           -------------------------------------------------------

                           elsif i = '(' then

		                       	if p_bracket_number = 0 then
		                          	p_stmt_value := p_stmt_value || 'case when ' || i;
		                        end if;

		                        p_bracket_number := p_bracket_number + 1; -- count opening brackets

	                       elsif  i = ')' then

		                        p_bracket_number := p_bracket_number - 1; -- count closing brackets

		                       	if p_bracket_number = 0 then
		                          	p_stmt_value := p_stmt_value || i || ' then ' || coalesce(p_replacement_value::varchar, 'null') || ' else cast(var0.value as float) end';
		                        end if;


                           --------------------------------
                           -- add spaces to 'or' / 'and' --
                           --------------------------------

		                    elsif upper(i) in ('OR', 'AND') then

		                    	p_stmt_value := p_stmt_value || ' ' || i || ' ';

                           else

	                           p_stmt_value := p_stmt_value || i;

                           end if; -- end measure

                        end loop; -- end loop rule


                        --------------------------------------
                        -- construct 'select' sql-statement --
                        --------------------------------------

                        p_stmt_select :=	'
                                            select	now() as created_at
                                            ,       now() as update_at
                                            ,       cast(row_number() over () as bigint) as local_id
                                            ,       ' || p_stmt_value || ' as value
                                            ,		$3::bigint as measure_id
                                            ,		var0.spatialdimension_id
                                            ,		var0.temporaldimension_id
                                            from	var0
                                            '
                                            ;

                                           
                        --------------------------------------
                        -- construct 'order by' sql-statement --
                        --------------------------------------

                        p_stmt_order :=	'order by 2, 4, 3'
                                        ;
                                           

                        -------------------------------------------------------------------------
                        -- combine all separate sql-statements to construct full sql-statement --
                        -------------------------------------------------------------------------

                        p_stmt := p_stmt_with || p_stmt_select || p_stmt_join || p_stmt_order || ';';

                    end if;

                    -------------------------
                    -- return query result --
                    -------------------------

                    if length(p_stmt) > 0 then
                    return query execute p_stmt
                        using p_years, p_measure, p_measure_id;
                    end if;

                end;
                $$
                language plpgsql
                ;
            """
