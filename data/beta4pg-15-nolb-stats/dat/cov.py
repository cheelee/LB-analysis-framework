import numpy as np

obj_IDs = ["8589934592", "8589934593", "8589934594", "8589934595", "8589934596", "8589934597", "8589934598", "8589934599", "17179869184", "17179869185", "17179869186", "17179869187", "17179869188", "17179869189", "17179869190", "17179869191", "25769803776", "25769803777", "25769803778", "25769803779", "25769803780", "25769803781", "25769803782", "25769803783", "34359738368", "34359738369", "34359738370", "34359738371", "34359738372", "34359738373", "34359738374", "34359738375", "42949672960", "42949672961", "42949672962", "42949672963", "42949672964", "42949672965", "42949672966", "42949672967", "51539607552", "51539607553", "51539607554", "51539607555", "51539607556", "51539607557", "51539607558", "51539607559", "60129542144", "60129542145", "60129542146", "60129542147", "60129542148", "60129542149", "60129542150", "60129542151", "68719476736", "68719476737", "68719476738", "68719476739", "68719476740", "68719476741", "68719476742", "68719476743"]

m = {}
for o in obj_IDs:
    times = []
    with open("o-{}.dat".format(o), 'r') as f:
        for row in f:
            times.append(float(row.split(' ')[2].strip()))
    m[o] = times

w_sz = 10
c = {}
for o in obj_IDs:
    o_times = m[o]
    cov_times = []
    for t in range(len(o_times) - w_sz + 1):
        t_sample = o_times[t : t + w_sz]
        cov_times.append(np.std(t_sample) / np.mean(t_sample))
    c[o] = cov_times

n_t = len(c[obj_IDs[0]])
values = []
for t in range(n_t):
    cov_t = []
    for v in c.values():
        cov_t.append(v[t])
    print np.mean(cov_t)

