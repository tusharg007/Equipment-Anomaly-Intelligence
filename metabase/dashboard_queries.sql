-- Manufacturing overview KPIs
select
    count(distinct batch_id) as total_batches,
    round(avg(defect_flag)::numeric, 4) as defect_rate,
    sum(defect_count) as total_defects,
    coalesce((select sum(downtime_minutes) from downtime_events), 0) as total_downtime_minutes
from quality_checks;

-- Defect rate by line
select
    line_id,
    round(avg(defect_flag)::numeric, 4) as defect_rate,
    sum(defect_count) as defect_count
from quality_checks
group by 1
order by defect_rate desc;

-- Defect rate by machine
select
    machine_id,
    line_id,
    round(avg(defect_flag)::numeric, 4) as defect_rate,
    sum(defect_count) as defect_count
from quality_checks
group by 1, 2
order by defect_rate desc;

-- Defect trend over time
select
    cast(timestamp as date) as metric_day,
    round(avg(defect_flag)::numeric, 4) as defect_rate,
    sum(defect_count) as defect_count
from quality_checks
group by 1
order by 1;

-- Downtime by machine
select
    machine_id,
    line_id,
    sum(downtime_minutes) as downtime_minutes
from downtime_events
group by 1, 2
order by downtime_minutes desc;

-- OEE-style KPI by line
select
    line_id,
    avg(oee_score) as avg_oee_score,
    avg(availability_rate) as availability_rate,
    avg(performance_rate) as performance_rate,
    avg(quality_rate) as quality_rate
from analytics.mart_oee_dashboard
group by 1
order by avg_oee_score desc;

-- Anomaly trend by day
select
    cast(timestamp as date) as metric_day,
    avg(anomaly_score) as avg_anomaly_score,
    sum(anomaly_flag) as anomaly_count
from anomaly_scores
group by 1
order by 1;

-- Cycle time drift by machine
select
    machine_id,
    line_id,
    round(avg(cycle_time_drift)::numeric, 3) as avg_cycle_time_drift
from ml_training_dataset
group by 1, 2
order by avg_cycle_time_drift desc;

-- High-risk machines
select
    machine_id,
    line_id,
    downtime_risk_score,
    risk_band,
    top_risk_driver,
    maintenance_priority_recommendation
from downtime_risk_scores
order by downtime_risk_score desc;

-- Maintenance priority list
select
    machine_id,
    line_id,
    risk_band,
    maintenance_priority_recommendation,
    top_risk_driver
from maintenance_priority
order by
    case risk_band
        when 'Critical' then 1
        when 'High' then 2
        when 'Medium' then 3
        else 4
    end;

-- Top defect drivers / feature importance
select
    feature,
    importance
from feature_importance
order by importance desc
limit 10;
