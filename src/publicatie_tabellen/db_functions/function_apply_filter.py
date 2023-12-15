function_apply_filter = """
                create or replace function public.apply_filter
                ----------------------------------------------------------------------------------
                -- GOAL: function to return observation values after applying (privacy) filters --
                ----------------------------------------------------------------------------------
                (
                    p_measure_id			bigint,
                    p_temporaldimension_id	bigint,
                    p_spatialdimension_id	bigint
                )
                    returns float
                    --returns text -- returns query statement
                as
                $$

                declare

                    p_rule				varchar[];
                    p_total				integer;
	                p_replacement_value	float;
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

                    --------------------------------------------------------------------
                    -- select rule of supplied measure and split on spaces into array --
                    --------------------------------------------------------------------

                    select	regexp_split_to_array(rule, '\s+') into p_rule
                    from	statistiek_hub_filter
                    where	measure_id = p_measure_id
                    ;

                    --------------------------------------------------
                    -- select replacement value of supplied measure --
                    --------------------------------------------------

                    select	value_new into p_replacement_value
                    from	statistiek_hub_filter
                    where	measure_id = p_measure_id
                    ;


                    --------------------------------------------------------------------------
                    -- total number of measures in filter; each measure should start with $ --
                    --------------------------------------------------------------------------

                    select	count(*) into p_total
                    from	(
                            select	unnest(p_rule) as rij
                            ) as foo
                    where 	rij like '$%'
                    ;


                    -------------------------------------------------------------------
                    -- loop through rule elements; only if rule contains any measure --
                    -------------------------------------------------------------------

                    if p_total > 0 then

                        foreach i in array p_rule loop -- start loop rule

                            if i like '$%' then -- start measure

                                p_number := p_number + 1;


                                -----------------------------------------------------------------
                                -- construct 'with' sql-statements for each individual measure --
                                -----------------------------------------------------------------

                                if p_number = 1 then

                                    p_stmt_with := 'with ';

                                end if;

                                if p_number > 1 then

                                    p_stmt_with := p_stmt_with || ', ';

                                end if;

                                p_stmt_with := 	p_stmt_with || 'var' || p_number ||
                                                ' as	(
                                                        select	o.value
														,		o.temporaldimension_id
														,		o.spatialdimension_id
                                                        from	statistiek_hub_observation o
														join	statistiek_hub_measure m on o.measure_id = m.id
                                                        where	1=1
														and		o.spatialdimension_id = ' || p_spatialdimension_id || '
														and		o.temporaldimension_id = ' || p_temporaldimension_id || '
														and		m.name = ''' || right(i, length(i) - 1) || '''
                                                '
														;

                                p_stmt_with := 	p_stmt_with || ') '; -- close with-statement


                                -----------------------------------------------------------------
                                -- construct 'join' sql-statements for each individual measure --
                                -----------------------------------------------------------------

                                if p_number > 1 then

                                    p_stmt_join := 	p_stmt_join || 'join	var' || p_number ||
                                                    ' on var' || p_number || '.spatialdimension_id = var' || p_number -1 || '.spatialdimension_id and var' ||
                                                    p_number || '.temporaldimension_id = var' || p_number -1 || '.temporaldimension_id '
                                                    ;

                                end if;


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
		                          	p_stmt_value := p_stmt_value || i || ' then ' || p_replacement_value || ' else null end';
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
                                            select	' || p_stmt_value || ' as value_new
                                            from	var1
                                            '
                                            ;


                        -------------------------------------------------------------------------
                        -- combine all separate sql-statements to construct full sql-statement --
                        -------------------------------------------------------------------------

                        p_stmt := p_stmt_with || p_stmt_select || p_stmt_join || ';';

                    end if;

                    -------------------------
                    -- return query result --
                    -------------------------

                    if length(p_stmt) > 0 then
                     execute p_stmt into p_value_new; -- execute dynamic sql-statement
  					 return p_value_new;
                     --return p_stmt; -- returns query statement
                    else
                     return cast(null as float);
                    end if;

                end;
                $$
                language plpgsql
                ;
            """
