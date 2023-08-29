function_round_observation = """
                create or replace function public.round_observation
                -----------------------------------------------------------------------------------------------
                -- GOAL: function to return rounded observation values based on specified amount of decimals --
                -----------------------------------------------------------------------------------------------
                (
                    p_measure_id	bigint,
                    p_input			float
                )
                    returns float
                as
                $$

                declare

                    p_decimals		integer;
                    p_output		numeric;

                begin

                    ---------------------------------------------------
                    -- select amount of decimals of supplied measure --
                    ---------------------------------------------------

                    select	decimals into p_decimals
                    from	measure
                    where	id = p_measure_id
                    ;


                    --------------------------
                    -- round supplied value --
                    --------------------------

                    select round(p_input::numeric, p_decimals) into p_output
                    ;

                return p_output;

                end;
                $$
                language plpgsql
                ;
            """
