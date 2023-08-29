function_calculate_observation = """
                create or replace function public.calculate_observation
                ------------------------------------------------------------------------
                -- GOAL: function to return observation values of calculated measures --
                ------------------------------------------------------------------------
                (
                    p_measure	varchar
                )
                    returns setof observation -- returns query result
--                    returns text -- returns query statement
                as
                $$

                declare

                    p_measure_id		bigint;
                    p_calculation		varchar[];
                    p_date_calculation	varchar[];
                    p_total				integer;
                    p_number			integer default 0;
                    p_bracket_number	integer default 0;
                    p_divide			boolean default false;
                    i					varchar;
                    j					varchar;
                    p_stmt				text;
                    p_stmt_select		text default '';
                    p_stmt_with			text default '';
                    p_stmt_join			text default '';
                    p_stmt_value		text default '';
                    p_stmt_order		text default '';

                begin

                    -----------------------------------
                    -- select id of supplied measure --
                    -----------------------------------

                    select	id into p_measure_id
                    from	measure
                    where	name = p_measure
                    ;


                    ---------------------------------------------------------------------------
                    -- select calculation of supplied measure and split on spaces into array --
                    ---------------------------------------------------------------------------

                    select	regexp_split_to_array(calculation, '\s+') into  p_calculation
                    from	measure
                    where	name = p_measure
                    ;


                    -------------------------------------------------------------------------------
                    -- total number of measures in calculation; each measure should start with $ --
                    -------------------------------------------------------------------------------

                    select	count(*) into p_total
                    from	(
                            select	unnest(p_calculation) as rij
                            ) as foo
                    where 	rij like '$%'
                    ;


                    ---------------------------------------------------------------------------------
                    -- loop through calculation elements; only if calculation contains any measure --
                    ---------------------------------------------------------------------------------

                    if p_total > 0 then

                        foreach i in array p_calculation loop -- start loop calculation

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
                                                        select	o.spatialdimension_id
                                                        , 		o.temporaldimension_id
                                                        , 		o.value
                                                        from	observation o
                                                        join	measure m on o.measure_id = m.id
                                                        join	spatialdimension s on o.spatialdimension_id = s.id
                                                        join	temporaldimension t on o.temporaldimension_id = t.id
                                                        where	1=1
														and		m.name =
                                                '
														;


								---------------------------------------------------------------
								-- loop through measure elements to detect date restrictions --
								---------------------------------------------------------------

                                if i like '$[%' then

                                	p_stmt_with := 	p_stmt_with || ' case ';

	                                select regexp_split_to_array(replace(i, '$', ''), '[|]') into  p_date_calculation; -- split measure into array

	                                foreach j in array p_date_calculation loop -- start building measure condition

		                                if j like '[%' then -- date restriction

	                                	p_stmt_with := 	p_stmt_with || ' when extract(year from t.startdate) ' || replace(replace(replace(j, '[', 'between '), '-', ' and '), ']', '') || ' then ';

	                                	else

	                                	p_stmt_with := 	p_stmt_with || '''' || j || '''';

	                                	end if;

	                                end loop;

	                                p_stmt_with := 	p_stmt_with || ' end ';

                                else

                                	p_stmt_with := 	p_stmt_with || '''' || right(i, length(i) - 1) || ''''; -- measure without date restrictions

                                end if;


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

                            	------------------------------------------------------
                            	-- contruct nullif-syntax to prevent ´divided by 0' --
                            	------------------------------------------------------

								elsif i = '/' then

                                	p_divide := true; -- divide started
                                	p_stmt_value := p_stmt_value || i || 'nullif';

                                elsif p_divide = true and i = '(' then

                                	p_bracket_number := p_bracket_number + 1; -- count opening brackets
                                	p_stmt_value := p_stmt_value || i;

                                elsif p_divide = true and i = ')' then

                                	p_bracket_number := p_bracket_number - 1; -- count closing brackets

                                	if p_bracket_number = 0 then

                                		p_stmt_value := p_stmt_value || ',0' || i;
                                		p_divide := false; -- divide ended

                                	else

                                		p_stmt_value := p_stmt_value || i;

                                	end if;

                                else

                                	p_stmt_value := p_stmt_value || i;

                            end if; -- end measure

                        end loop; -- end loop calculation


                        --------------------------------------
                        -- construct 'select' sql-statement --
                        --------------------------------------

                        p_stmt_select :=	'
                                            select	now() as created_at
                                            ,       now() as update_at
                                            ,       row_number() over () as local_id
                                            ,       ' || p_stmt_value || ' as value
                                            ,		cast(' || p_measure_id || ' as bigint) as measure_id
                                            ,		var1.spatialdimension_id
                                            ,		var1.temporaldimension_id
                                            from	var1
                                            '
                                            ;


                        --------------------------------------
                        -- construct 'order by' sql-statement --
                        --------------------------------------

                        p_stmt_order :=	'
                                        order by 2, 4, 3
                                        '
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
                       return query execute p_stmt; -- returns query result
--                       return p_stmt; -- returns query statement
                    end if;

                end;
                $$
                language plpgsql
                ;
            """
