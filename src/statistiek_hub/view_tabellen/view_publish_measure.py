vw_publish_measure = {
    "query": (
        """
                    create or replace view public.vw_publish_measure
                    as
                    select	m.id
                    ,		m.name
                    ,		m.label
                    ,		m.label_uk
                    ,		m.definition
                    ,		m.definition_uk
                    ,		m.description
                    ,		m.calculation
                    ,		m.source
                    ,		t.name as theme
                    ,		u.name as unit
                    ,		u.symbol as symbol
                    ,		m.decimals
                    ,		d.name as dimension
                    ,		d.code as dimension_code
                    ,		d.description as dimension_description
                    ,		m.extra_attr
                    ,		p.name as parent
                    ,		o.username as owner
                    from	public.measure m
                    join	public.theme t on m.theme_id = t.id
                    join	public.unit u on m.unit_id = u.id
                    join	public.auth_user o on m.owner_id = o.id
                    left
                    join	public.dimension d on m.dimension_id = d.id
                    left
                    join	public.measure p on m.parent_id = p.id
                    order
                    by      2
                    ;
            """
    ),
    "reverse": (
        """
                drop view if exists public.vw_publish_measure;
            """
    ),
}
