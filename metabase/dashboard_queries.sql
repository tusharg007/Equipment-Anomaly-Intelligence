-- Overall manufacturing KPIs
select
    round(avg(defect_flag)::numeric, 4) as defect_rate,
    round(avg(defect_probability)::numeric, 4) as avg_predicted_defect_probability,
    sum(defect_count) as total_defect_count
from quality_checks;

-- Defect rate by machine
select
    machine_id,
    line_id,
    round(avg(defect_flag)::numeric, 4) as defect_rate,
    sum(defect_count) as defect_count
from quality_checks
group by 1, 2
order by defect_rate desc;

-- Defect rate by production line
select
    line_id,
    round(avg(defect_flag)::numeric, 4) as defect_rate,
    sum(defect_count) as defect_count
from quality_checks
group by 1
order by defect_rate desc;

-- Downtime by machine
select
    machine_id,
    line_id,
    sum(downtime_minutes) as downtime_minutes
from downtime_events
group by 1, 2
order by downtime_minutes desc;

-- High-risk machines
select
    machine_id,
    line_id,
    downtime_risk_score,
    risk_band,
    maintenance_priority_recommendation
from downtime_risk_scores
order by downtime_risk_score desc;

-- Anomaly trend by day
select
    cast(timestamp as date) as metric_day,
    round(avg(anomaly_signal)::numeric, 3) as avg_anomaly_signal,
    sum(case when anomaly_signal > 2.5 then 1 else 0 end) as elevated_anomaly_windows
from model_features
group by 1
order by 1;

-- OEE by production line
select
    line_id,
    avg(oee_score) as avg_oee_score,
    avg(availability_rate) as availability_rate,
    avg(performance_rate) as performance_rate,
    avg(quality_rate) as quality_rate
from analytics.mart_oee_dashboard
group by 1
order by avg_oee_score desc;

-- Cycle time drift by machine
select
    machine_id,
    line_id,
    round(avg(cycle_time_drift)::numeric, 3) as avg_cycle_time_drift
from model_features
group by 1, 2
order by avg_cycle_time_drift desc;

-- Maintenance priority list
select
    machine_id,
    line_id,
    downtime_risk_score,
    risk_band,
    maintenance_priority_recommendation
from downtime_risk_scores
order by
    case risk_band when 'High' then 1 when 'Medium' then 2 else 3 end,
    downtime_risk_score desc;

-- Top defect drivers
select
    feature,
    importance
from feature_importance
order by importance desc
limit 10;
