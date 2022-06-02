#!/usr/bin/env python
# coding: utf-8

from oar.kao.helpers import plot_slots_and_job
from oar.kao.simsim import JobSimu, ResourceSetSimu, SimSched
from oar.lib import config

# Set undefined config value to default one
DEFAULT_CONFIG = {
    "HIERARCHY_LABELS": "resource_id,network_address",
    "SCHEDULER_RESOURCE_ORDER": "resource_id ASC",
    "SCHEDULER_JOB_SECURITY_TIME": "60",
    "SCHEDULER_AVAILABLE_SUSPENDED_RESOURCE_TYPE": "default",
    "FAIRSHARING_ENABLED": "no",
    "SCHEDULER_FAIRSHARING_MAX_JOB_PER_USER": "30",
    "QUOTAS": "no",
}

config.setdefault_config(DEFAULT_CONFIG)

# config['LOG_FILE'] = ':stderr:'

nb_res = 32

#
# generate ResourceSet
#
hy_resource_id = [[(i, i)] for i in range(1, nb_res + 1)]
res_set = ResourceSetSimu(
    rid_i2o=range(nb_res + 1),
    rid_o2i=range(nb_res + 1),
    roid_itvs=[(1, nb_res)],
    hierarchy={"resource_id": hy_resource_id},
    available_upto={2147483600: [(1, nb_res)]},
)

#
# generate jobs
#

nb_jobs = 4
jobs = {}
submission_time_jids = []

for i in range(1, nb_jobs + 1):
    jobs[i] = JobSimu(
        id=i,
        state="Waiting",
        queue="test",
        start_time=0,
        walltime=0,
        types={},
        res_set=[],
        moldable_id=0,
        mld_res_rqts=[(i, 60, [([("resource_id", 15)], [(0, nb_res - 1)])])],
        run_time=20 * i,
        deps=[],
        key_cache={},
        ts=False,
        ph=0,
    )

    submission_time_jids.append((10, [i]))

# submission_time_jids= [(10, [1,2,3,4])]
# submission_time_jids= [(10, [1,2]), (10, [3])]


print(submission_time_jids)

simsched = SimSched(res_set, jobs, submission_time_jids)
simsched.run()

plt = simsched.platform

print("Number completed jobs:", len(plt.completed_jids))
print("Completed job ids:", plt.completed_jids)

print(jobs)

# for jid,job in iteritems(jobs):
#    jres_set = job.res_set
#    r_ids = [ res_set.rid_o2i[roid] for roid in itvs2ids(jres_set) ]
#    job.res_set = unordered_ids2itvs(r_ids)
#    print jid, job.state, job.start_time, job.walltime, job.res_set

last_completed_job = jobs[plt.completed_jids[-1]]
print(last_completed_job)
plot_slots_and_job(
    {}, jobs, nb_res, last_completed_job.start_time + last_completed_job.walltime
)
