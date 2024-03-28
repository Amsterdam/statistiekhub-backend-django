function_publish_measures = """
create or replace function public.publicatie_tabellen_publish_measures
				------------------------------------------------------------------
				-- GOAL: function to fill table with measures, ready to publish --
				------------------------------------------------------------------
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

					select distinct name as measure from public.statistiek_hub_measure order by 1

					loop

					--
					-- fill supplied measures
					--

					insert into public.publicatie_tabellen_publicationmeasure
					(
					name,
					label,
					label_uk,
					definition,
					definition_uk,
					description,
					source,
					theme,
					theme_uk,
					unit,
					unit_code,
					unit_symbol,
					decimals,
					sensitive,
					parent,
					extra_attr,
					deprecated,
					deprecated_date,
					deprecated_reason
					)
					select	*
					from	(
							select	nullif(m.name, '') as name
							,		nullif(m.label, '') as label
							,		nullif(m.label_uk, '') as label_uk
							,		nullif(m.definition, '') as definition
							,		nullif(m.definition_uk, '') as definition_uk
							,		nullif(m.description, '') as description
							,		nullif(m.source, '') as source
							,		nullif(t.name, '') as theme
							,		nullif(t.name_uk, '') as theme_uk
							,		nullif(u.name, '') as unit
							,		nullif(u.code, '') as unit_code
							,		nullif(u.symbol, '') as unit_symbol
							,		m.decimals
							,		m.sensitive
							,		nullif(p.name, '') as parent
							,       m.extra_attr
							,		m.deprecated
							,		m.deprecated_date
							,		nullif(m.deprecated_reason, '') as deprecated_reason
							from	public.statistiek_hub_measure m
							join	public.referentie_tabellen_theme t on m.theme_id = t.id
							join	public.referentie_tabellen_unit u on m.unit_id = u.id
							left
							join	public.statistiek_hub_measure p on p.id = m.parent_id
							) as foo
					where	1=1
					and 	foo.name = p_record.measure
					and		not exists	( 
										-- no duplicates
										select	null
										from	public.publicatie_tabellen_publicationmeasure x
										where	foo.name = x.name
										)
					;
						
				end loop;

				end;

				$$
				language plpgsql
				;
            """
