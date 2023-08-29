vw_publish_product = {
    "query": (
        """
                    create or replace view public.vw_publish_product
                    as
                    select	t.id
                    ,		t.name
                    ,		t.version
                    ,		m.name as measure
                    from	public.topic t
                    join	public.topicset s on t.id = s.topic_id
                    join	public.measure m on s.measure_id = m.id
                    order
                    by		t.id
                    ;
            """
    ),
    "reverse": (
        """
                drop view if exists public.vw_publish_product;
            """
    ),
}
