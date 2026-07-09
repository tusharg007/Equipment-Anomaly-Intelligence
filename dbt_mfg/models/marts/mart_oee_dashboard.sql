with batches as (
    select * from {{ source('ops_raw', 'production_batches') }}
),
downtime as (
    select
        line_id,
        date_trunc('day', timestamp) as metric_day,
        sum(downtime_minutes) as downtime_minutes
    from {{ ref('stg_downtime_events') }}
    group by 1, 2
)
select
    batches.line_id,
    date_trunc('day', cast(batches.timestamp as timestamp)) as metric_day,
    sum(batches.planned_units) as planned_units,
    sum(batches.actual_units) as actual_units,
    sum(batches.good_units) as good_units,
    coalesce(max(downtime.downtime_minutes), 0) as downtime_minutes,
    round((1440 - coalesce(max(downtime.downtime_minutes), 0)) / 1440.0, 4) as availability_rate,
    round(sum(batches.actual_units) / nullif(sum(batches.planned_units), 0), 4) as performance_rate,
    round(sum(batches.good_units) / nullif(sum(batches.actual_units), 0), 4) as quality_rate,
    round(
        ((1440 - coalesce(max(downtime.downtime_minutes), 0)) / 1440.0)
        * (sum(batches.actual_units) / nullif(sum(batches.planned_units), 0))
        * (sum(batches.good_units) / nullif(sum(batches.actual_units), 0)),
        4
    ) as oee_score
from batches
left join downtime
    on batches.line_id = downtime.line_id
   and date_trunc('day', cast(batches.timestamp as timestamp)) = downtime.metric_day
group by 1, 2
